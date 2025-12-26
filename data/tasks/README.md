# Task Datasets

This directory contains task datasets for evaluating SuperOpt, GEPA, and ACE.

## Dataset Files

### `sample_tasks.json`
A small sample dataset (10 tasks) for quick testing. Contains a mix of:
- Format violation tasks
- Missing constraint tasks
- Ambiguous instruction tasks

**Usage:**
```bash
python scripts/evaluate_baseline.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/baseline.json
```

### `prompt_only_tasks.json`
Tasks designed to test prompt optimization (10 tasks). These tasks primarily fail due to:
- Format violations (wrong output format)
- Missing constraints (edge cases not handled)
- Ambiguous instructions (unclear requirements)

**Categories:**
- Format violations: Tasks requiring specific output formats (JSON strings, etc.)
- Missing constraints: Tasks requiring edge case handling
- Ambiguous instructions: Tasks with unclear requirements

### `multi_dimensional_tasks.json`
Tasks designed to test multi-dimensional optimization (10 tasks). These tasks fail due to:
- Tool errors (line number issues, syntax errors)
- Retrieval failures (missing code references)
- Mixed failures (combination of multiple failure types)

**Categories:**
- Tool errors: Tasks triggering tool schema violations
- Retrieval failures: Tasks requiring codebase search
- Mixed failures: Complex tasks with multiple failure modes

## Dataset Format

All datasets use SuperOpt format (JSON):

```json
[
    {
        "task_id": "task_001",
        "task_description": "Task description here",
        "expected_output": "Optional expected output",
        "category": "task_category",
        "difficulty": "easy|medium|hard",
        "metadata": {
            "failure_type": "prompt|tool|retrieval|mixed",
            "source": "synthetic|real"
        }
    }
]
```

## Converting Formats

Use `scripts/prepare_datasets.py` to convert between formats:

```bash
# Convert to all formats
python scripts/prepare_datasets.py \
    --input data/tasks/sample_tasks.json \
    --output-dir data/tasks/formatted \
    --format all

# Convert to specific format
python scripts/prepare_datasets.py \
    --input data/tasks/sample_tasks.json \
    --output-dir data/tasks/gepa_format \
    --format gepa
```

## Creating Your Own Datasets

1. **Start with sample format:**
   ```json
   [
       {
           "task_description": "Your task description here",
           "expected_output": "Optional expected output"
       }
   ]
   ```

2. **Add metadata** (optional but recommended):
   ```json
   {
       "task_id": "unique_id",
       "task_description": "...",
       "category": "format_violation|missing_constraints|tool_error|retrieval_failure|mixed",
       "difficulty": "easy|medium|hard",
       "metadata": {
           "failure_type": "prompt|tool|retrieval|mixed",
           "source": "synthetic|real"
       }
   }
   ```

3. **Validate format:**
   ```bash
   python -c "import json; json.load(open('data/tasks/your_tasks.json'))"
   ```

## Task Categories

### Prompt-Only Tasks
- **Format violations**: Tasks requiring specific output formats
- **Missing constraints**: Tasks requiring edge case handling
- **Ambiguous instructions**: Tasks with unclear requirements

### Multi-Dimensional Tasks
- **Tool errors**: Tasks triggering tool schema violations
- **Retrieval failures**: Tasks requiring codebase search
- **Mixed failures**: Complex tasks with multiple failure modes

### Long-Horizon Tasks (Future)
- **Multi-session tasks**: Tasks spanning multiple interactions
- **Evolving requirements**: Tasks with changing requirements
- **Context-dependent**: Tasks requiring previous context

## Usage Examples

### Quick Test (Sample Dataset)
```bash
python scripts/evaluate_baseline.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/sample_baseline.json
```

### Prompt Optimization Test
```bash
python scripts/evaluate_gepa.py \
    --tasks data/tasks/prompt_only_tasks.json \
    --output results/prompt_gepa.json
```

### Multi-Dimensional Test
```bash
python scripts/compare_all.py \
    --tasks data/tasks/multi_dimensional_tasks.json \
    --output results/multi_comparison.json
```

## Notes

- All datasets are in SuperOpt format (JSON)
- Use `prepare_datasets.py` to convert to GEPA/ACE formats
- Tasks should be executable by your agent adapter (Aider, Letta, Codex)
- Include expected failures in metadata for analysis

