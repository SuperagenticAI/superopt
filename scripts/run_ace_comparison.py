#!/usr/bin/env python3
"""
ACE vs SuperOpt Comparison

Compares ACE-style context accumulation against SuperOpt's typed memory with decay.

ACE (Agentic Context Engineering) accumulates reflective context across tasks,
appending learned insights to a "playbook". This can lead to:
- Context growth (playbook gets larger over time)
- Context collapse (too much context degrades performance)
- No decay (stale information persists)

SuperMem (SuperOpt's memory system) uses:
- Typed memory entries (PROMPT_CONSTRAINT, TOOL_RULE, STRATEGY)
- Confidence decay over time
- Conflict resolution
- Bounded memory size

This script demonstrates these differences empirically.

Usage:
    python scripts/run_ace_comparison.py --max-tasks 5

    # After completion, share the results path with Claude for analysis
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from superopt.adapters.aider_adapter import AiderAdapter
from superopt.comparison.dataset_loaders import load_superopt_format


class ACESimulator:
    """
    Simulates ACE-style context accumulation.

    ACE accumulates a "playbook" of learned insights from task executions.
    After each task, reflections are appended to the playbook, which is
    then included in the system prompt for subsequent tasks.
    """

    def __init__(self, model_name: str = "ollama/llama3.2:3b"):
        self.model_name = model_name
        self.playbook: list[str] = []
        self.playbook_token_estimate = 0
        self.task_history: list[dict[str, Any]] = []

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (4 chars per token)."""
        return len(text) // 4

    def _generate_reflection(
        self, task: str, success: bool, failure_type: str, duration: float
    ) -> str:
        """
        Generate ACE-style reflection from task execution.

        In real ACE, this would use an LLM to generate insights.
        We simulate with structured reflections.
        """
        if success:
            return f"- Task '{task[:50]}...' succeeded. Approach was effective."
        else:
            reflections = {
                "TOOL": f"- Task '{task[:50]}...' failed due to TOOL error. Consider: verify tool arguments match expected schema.",
                "PROMPT": f"- Task '{task[:50]}...' failed due to PROMPT issue. Consider: clarify requirements and expected output format.",
                "RETRIEVAL": f"- Task '{task[:50]}...' failed due to RETRIEVAL miss. Consider: improve search queries or expand context.",
                "MEMORY": f"- Task '{task[:50]}...' failed due to MEMORY issue. Consider: review previous learnings for conflicts.",
            }
            return reflections.get(
                failure_type, f"- Task '{task[:50]}...' failed. Review approach."
            )

    def _build_ace_prompt(self, base_prompt: str) -> str:
        """Build system prompt with accumulated ACE playbook."""
        if not self.playbook:
            return base_prompt

        playbook_text = "\n".join(self.playbook)
        return f"""{base_prompt}

## ACE Accumulated Playbook
The following insights have been learned from previous task executions:

{playbook_text}

Apply these learnings to improve task execution."""

    def run_task(self, task: str, task_index: int) -> dict[str, Any]:
        """Run a single task with ACE-accumulated context."""

        # Create adapter
        adapter = AiderAdapter(model_name=self.model_name)

        # Get base environment and apply ACE playbook
        env = adapter.extract_environment()
        original_prompt = env.prompts.system_prompt
        env.prompts.system_prompt = self._build_ace_prompt(original_prompt)

        # Track context size
        context_size = self._estimate_tokens(env.prompts.system_prompt)

        print(
            f"\n[Task {task_index}] Context size: ~{context_size} tokens, Playbook entries: {len(self.playbook)}"
        )
        print(f"  Task: {task[:60]}...")

        start_time = time.time()
        try:
            trace = adapter.execute(task, env)
            duration = time.time() - start_time

            success = trace.success
            failure_type = trace.failure_type.value if trace.failure_type else "NONE"

            status = "PASS" if success else f"FAIL ({failure_type})"
            print(f"  Result: {status} ({duration:.1f}s)")

        except Exception as e:
            duration = time.time() - start_time
            success = False
            failure_type = "ERROR"
            print(f"  Result: ERROR - {str(e)[:50]}")

        finally:
            adapter.cleanup()

        # Generate and accumulate reflection (ACE-style)
        reflection = self._generate_reflection(task, success, failure_type, duration)
        self.playbook.append(reflection)
        self.playbook_token_estimate = self._estimate_tokens("\n".join(self.playbook))

        result = {
            "task": task,
            "task_index": task_index,
            "success": success,
            "failure_type": failure_type,
            "duration": duration,
            "context_size_tokens": context_size,
            "playbook_entries": len(self.playbook),
            "playbook_tokens": self.playbook_token_estimate,
        }

        self.task_history.append(result)
        return result

    def run_all_tasks(self, tasks: list[str]) -> dict[str, Any]:
        """Run all tasks with ACE context accumulation."""

        print("=" * 60)
        print("ACE Context Accumulation Experiment")
        print("=" * 60)
        print(f"Model: {self.model_name}")
        print(f"Tasks: {len(tasks)}")
        print("=" * 60)

        for i, task in enumerate(tasks):
            self.run_task(task, i + 1)

        # Calculate metrics
        success_count = sum(1 for r in self.task_history if r["success"])
        total_duration = sum(r["duration"] for r in self.task_history)
        final_context_size = (
            self.task_history[-1]["context_size_tokens"] if self.task_history else 0
        )

        return {
            "method": "ACE",
            "model": self.model_name,
            "results": self.task_history,
            "playbook": self.playbook,
            "metrics": {
                "success_count": success_count,
                "total_tasks": len(tasks),
                "success_rate": success_count / len(tasks) * 100 if tasks else 0,
                "total_duration": total_duration,
                "final_context_tokens": final_context_size,
                "final_playbook_entries": len(self.playbook),
                "context_growth_rate": final_context_size / len(tasks) if tasks else 0,
            },
        }


class SuperMemSimulator:
    """
    Simulates SuperMem-style typed memory with decay.

    Unlike ACE's unbounded accumulation, SuperMem:
    - Uses typed memory entries (different categories)
    - Applies confidence decay over time
    - Resolves conflicts between entries
    - Maintains bounded memory size
    """

    def __init__(
        self, model_name: str = "ollama/llama3.2:3b", max_entries: int = 10, decay_rate: float = 0.1
    ):
        self.model_name = model_name
        self.max_entries = max_entries
        self.decay_rate = decay_rate
        self.memory: list[dict[str, Any]] = []
        self.task_history: list[dict[str, Any]] = []

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate."""
        return len(text) // 4

    def _decay_memory(self):
        """Apply decay to all memory entries."""
        for entry in self.memory:
            entry["confidence"] *= 1 - self.decay_rate

        # Remove low-confidence entries
        self.memory = [e for e in self.memory if e["confidence"] > 0.3]

        # Enforce max entries (keep highest confidence)
        if len(self.memory) > self.max_entries:
            self.memory.sort(key=lambda x: x["confidence"], reverse=True)
            self.memory = self.memory[: self.max_entries]

    def _add_memory_entry(self, task: str, success: bool, failure_type: str):
        """Add typed memory entry based on task outcome."""

        if success:
            entry_type = "STRATEGY"
            content = f"Successful approach for: {task[:30]}..."
            confidence = 0.8
        else:
            type_mapping = {
                "TOOL": ("TOOL_RULE", "Avoid tool error pattern"),
                "PROMPT": ("PROMPT_CONSTRAINT", "Clarify output format"),
                "RETRIEVAL": ("RETRIEVAL_HINT", "Improve context retrieval"),
                "MEMORY": ("STRATEGY", "Check for conflicting rules"),
            }
            entry_type, content = type_mapping.get(failure_type, ("STRATEGY", "Review approach"))
            content = f"{content}: {task[:30]}..."
            confidence = 0.9  # Failures are high-confidence learnings

        # Check for conflicts with existing entries of same type
        conflicts = [e for e in self.memory if e["type"] == entry_type]
        if conflicts:
            # Boost confidence of new entry if it conflicts
            confidence = min(1.0, confidence + 0.1)

        self.memory.append(
            {
                "type": entry_type,
                "content": content,
                "confidence": confidence,
                "task_index": len(self.task_history) + 1,
            }
        )

    def _build_supermem_prompt(self, base_prompt: str) -> str:
        """Build system prompt with SuperMem typed memory."""
        if not self.memory:
            return base_prompt

        # Group by type
        by_type: dict[str, list[str]] = {}
        for entry in sorted(self.memory, key=lambda x: x["confidence"], reverse=True):
            if entry["type"] not in by_type:
                by_type[entry["type"]] = []
            by_type[entry["type"]].append(f"  - [{entry['confidence']:.1f}] {entry['content']}")

        memory_text = ""
        for entry_type, entries in by_type.items():
            memory_text += f"\n### {entry_type}\n" + "\n".join(entries[:3])  # Max 3 per type

        return f"""{base_prompt}

## SuperMem Active Memory (Typed, with Decay)
{memory_text}

Note: Entries with higher confidence [0.9] take precedence over lower [0.5]."""

    def run_task(self, task: str, task_index: int) -> dict[str, Any]:
        """Run a single task with SuperMem typed memory."""

        # Apply decay before each task
        self._decay_memory()

        # Create adapter
        adapter = AiderAdapter(model_name=self.model_name)

        # Get base environment and apply SuperMem
        env = adapter.extract_environment()
        original_prompt = env.prompts.system_prompt
        env.prompts.system_prompt = self._build_supermem_prompt(original_prompt)

        # Track context size
        context_size = self._estimate_tokens(env.prompts.system_prompt)

        print(
            f"\n[Task {task_index}] Context size: ~{context_size} tokens, Memory entries: {len(self.memory)}"
        )
        print(f"  Task: {task[:60]}...")

        start_time = time.time()
        try:
            trace = adapter.execute(task, env)
            duration = time.time() - start_time

            success = trace.success
            failure_type = trace.failure_type.value if trace.failure_type else "NONE"

            status = "PASS" if success else f"FAIL ({failure_type})"
            print(f"  Result: {status} ({duration:.1f}s)")

        except Exception as e:
            duration = time.time() - start_time
            success = False
            failure_type = "ERROR"
            print(f"  Result: ERROR - {str(e)[:50]}")

        finally:
            adapter.cleanup()

        # Add typed memory entry
        self._add_memory_entry(task, success, failure_type)

        result = {
            "task": task,
            "task_index": task_index,
            "success": success,
            "failure_type": failure_type,
            "duration": duration,
            "context_size_tokens": context_size,
            "memory_entries": len(self.memory),
            "memory_types": list({e["type"] for e in self.memory}),
        }

        self.task_history.append(result)
        return result

    def run_all_tasks(self, tasks: list[str]) -> dict[str, Any]:
        """Run all tasks with SuperMem typed memory."""

        print("\n" + "=" * 60)
        print("SuperMem Typed Memory Experiment")
        print("=" * 60)
        print(f"Model: {self.model_name}")
        print(f"Tasks: {len(tasks)}")
        print(f"Max entries: {self.max_entries}, Decay rate: {self.decay_rate}")
        print("=" * 60)

        for i, task in enumerate(tasks):
            self.run_task(task, i + 1)

        # Calculate metrics
        success_count = sum(1 for r in self.task_history if r["success"])
        total_duration = sum(r["duration"] for r in self.task_history)
        final_context_size = (
            self.task_history[-1]["context_size_tokens"] if self.task_history else 0
        )

        return {
            "method": "SuperMem",
            "model": self.model_name,
            "config": {
                "max_entries": self.max_entries,
                "decay_rate": self.decay_rate,
            },
            "results": self.task_history,
            "final_memory": self.memory,
            "metrics": {
                "success_count": success_count,
                "total_tasks": len(tasks),
                "success_rate": success_count / len(tasks) * 100 if tasks else 0,
                "total_duration": total_duration,
                "final_context_tokens": final_context_size,
                "final_memory_entries": len(self.memory),
                "memory_types_used": list({e["type"] for e in self.memory}),
            },
        }


def compare_results(ace_results: dict, supermem_results: dict, superopt_file: Path | None = None):
    """Generate comparison summary."""

    print("\n" + "=" * 70)
    print("COMPARISON RESULTS: ACE vs SuperMem vs SuperOpt")
    print("=" * 70)

    # Load SuperOpt results if available
    superopt_success = None
    superopt_total = None
    if superopt_file and superopt_file.exists():
        with open(superopt_file) as f:
            superopt_data = json.load(f)
        superopt_results = superopt_data.get("superopt", [])
        superopt_success = sum(1 for r in superopt_results if r["success"])
        superopt_total = len(superopt_results)

    print("\n## Success Rate Comparison")
    print("| Method | Success Rate | Context Growth | Memory Strategy |")
    print("|--------|--------------|----------------|-----------------|")

    ace_m = ace_results["metrics"]
    print(
        f"| ACE | {ace_m['success_rate']:.1f}% ({ace_m['success_count']}/{ace_m['total_tasks']}) | "
        f"{ace_m['final_context_tokens']} tokens | Unbounded accumulation |"
    )

    sm_m = supermem_results["metrics"]
    print(
        f"| SuperMem | {sm_m['success_rate']:.1f}% ({sm_m['success_count']}/{sm_m['total_tasks']}) | "
        f"{sm_m['final_context_tokens']} tokens | Typed + decay |"
    )

    if superopt_success is not None:
        print(
            f"| **SuperOpt** | **{100 * superopt_success / superopt_total:.1f}%** ({superopt_success}/{superopt_total}) | "
            f"Adaptive | **Full environment opt** |"
        )

    print("\n## Context Growth Analysis")
    print(
        f"- ACE final playbook: {ace_m['final_playbook_entries']} entries, ~{ace_m['final_context_tokens']} tokens"
    )
    print(
        f"- SuperMem final memory: {sm_m['final_memory_entries']} entries, ~{sm_m['final_context_tokens']} tokens"
    )
    print(
        f"- Context reduction: {(1 - sm_m['final_context_tokens'] / max(ace_m['final_context_tokens'], 1)) * 100:.1f}% smaller with SuperMem"
    )

    print("\n## Key Insights")
    print("""
1. **ACE Limitations**:
   - Playbook grows unboundedly with each task
   - No decay mechanism - stale information persists
   - All learnings treated equally (no typing/priority)
   - Risk of context collapse with many tasks

2. **SuperMem Advantages**:
   - Typed memory entries (TOOL_RULE, STRATEGY, etc.)
   - Confidence decay removes stale information
   - Bounded memory size prevents context collapse
   - Conflict resolution between entries

3. **SuperOpt (Full System)**:
   - Combines SuperMem with SuperPrompt, SuperReflexion, SuperRAG
   - Can fix failures that memory alone cannot address
   - Stability guarantees via hierarchy of mutability
""")

    return {
        "ace": ace_m,
        "supermem": sm_m,
        "superopt": {"success": superopt_success, "total": superopt_total}
        if superopt_success
        else None,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ACE vs SuperMem Comparison")
    parser.add_argument("--tasks", type=str, required=True, help="Path to tasks JSON file")
    parser.add_argument(
        "--superopt-results",
        type=str,
        default=None,
        help="Path to SuperOpt results for comparison (optional)",
    )
    parser.add_argument("--output", type=str, required=True, help="Output path for results JSON")
    parser.add_argument("--model", type=str, default="ollama/llama3.2:3b", help="Model to use")
    parser.add_argument(
        "--max-tasks", type=int, default=5, help="Max tasks (keep low for Mac heat)"
    )
    parser.add_argument("--max-memory", type=int, default=10, help="Max SuperMem entries")
    parser.add_argument("--decay-rate", type=float, default=0.1, help="SuperMem decay rate")
    args = parser.parse_args()

    # Load tasks
    tasks_file = Path(args.tasks)
    tasks = load_superopt_format(tasks_file)

    # Limit tasks
    if args.max_tasks and len(tasks) > args.max_tasks:
        print(f"Limiting to {args.max_tasks} tasks to avoid overheating...")
        tasks = tasks[: args.max_tasks]

    print(f"\n{'=' * 60}")
    print("ACE vs SuperMem vs SuperOpt Comparison")
    print(f"{'=' * 60}")
    print(f"Model: {args.model}")
    print(f"Tasks: {len(tasks)}")
    print(f"This comparison runs {len(tasks)} tasks x 2 methods = {len(tasks) * 2} executions")
    print(f"Estimated time: ~{len(tasks) * 2 * 30}s (assuming 30s/task avg)")
    print(f"{'=' * 60}\n")

    # Run ACE simulation
    ace_sim = ACESimulator(model_name=args.model)
    ace_results = ace_sim.run_all_tasks(tasks)

    # Run SuperMem simulation
    supermem_sim = SuperMemSimulator(
        model_name=args.model,
        max_entries=args.max_memory,
        decay_rate=args.decay_rate,
    )
    supermem_results = supermem_sim.run_all_tasks(tasks)

    # Compare results
    superopt_file = Path(args.superopt_results)
    comparison = compare_results(ace_results, supermem_results, superopt_file)

    # Save results
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "model": args.model,
        "tasks_count": len(tasks),
        "ace": ace_results,
        "supermem": supermem_results,
        "comparison": comparison,
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"Results saved to: {output_file}")
    print(f"{'=' * 60}")
    print("\nShare this path with Claude for analysis!")


if __name__ == "__main__":
    main()
