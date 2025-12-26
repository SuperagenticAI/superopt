"""
ACE Comparison Adapter

Integrates ACE for context accumulation to compare against SuperOpt.

This adapter provides a bridge between SuperOpt's comparison framework and ACE.
Assumes ACE is installed as a package (pip install ace-context).
"""

from superopt.comparison.ace_data_processor import AgentDataProcessor
from superopt.comparison.models import ModelConfig
from superopt.core.environment import AgenticEnvironment


class ACEComparison:
    """
    Adapter for comparing SuperOpt against ACE.

    ACE accumulates reflective context, so this adapter:
    1. Uses ACE to accumulate context across tasks
    2. Runs tasks with ACE-accumulated context
    3. Compares against SuperOpt (which uses typed memory with decay)
    """

    def __init__(
        self,
        agent_adapter=None,
        model_config: ModelConfig | None = None,
        api_base: str | None = None,
    ):
        """
        Initialize ACE comparison adapter.

        Args:
            agent_adapter: Agent adapter for executing tasks (optional, for evaluation)
            model_config: Model configuration (optional)
            api_base: API base URL for models (optional, for Ollama)
        """
        self.agent_adapter = agent_adapter
        self.model_config = model_config
        self.api_base = api_base
        self.accumulated_context: str | None = None
        self.ace_system = None

    def _initialize_ace_system(self):
        """Initialize ACE system with model configuration."""
        if self.ace_system is not None:
            return

        try:
            from ace import ACE
            from utils import initialize_clients  # noqa: F401
        except ImportError as e:
            raise ImportError(
                f"ACE not found. Install with: pip install ace-context. Original error: {e}"
            )

        # Determine API provider and models
        import os

        if self.model_config:
            # Map ModelConfig provider to ACE's api_provider
            provider_map = {
                "ollama": "openai",  # Ollama uses OpenAI-compatible API
                "openai": "openai",
                "anthropic": "openai",  # Fallback, ACE doesn't support Anthropic directly
            }
            api_provider = provider_map.get(self.model_config.provider.value, "openai")

            # Extract model names (remove provider prefix if present)
            task_model = self.model_config.task_model
            reflection_model = self.model_config.reflection_model

            # Remove "ollama/" prefix if present
            if task_model.startswith("ollama/"):
                task_model = task_model[7:]
            if reflection_model.startswith("ollama/"):
                reflection_model = reflection_model[7:]

            # Set API base for Ollama (use provided api_base or from model_config)
            if self.model_config.provider.value == "ollama":
                api_base = self.api_base or self.model_config.api_base
                if api_base:
                    os.environ["OPENAI_API_BASE"] = api_base
                elif "OPENAI_API_BASE" not in os.environ:
                    # Set default Ollama API base if not already set
                    os.environ["OPENAI_API_BASE"] = "http://localhost:11434"
        else:
            # Default configuration (fallback to OpenAI if no config provided)
            api_provider = "openai"
            task_model = "gpt-4o-mini"
            reflection_model = "gpt-4o"

        # Set API base for OpenAI-compatible providers if provided
        if self.api_base and api_provider == "openai" and "OPENAI_API_BASE" not in os.environ:
            os.environ["OPENAI_API_BASE"] = self.api_base

        # Initialize ACE system
        self.ace_system = ACE(
            api_provider=api_provider,
            generator_model=task_model,
            reflector_model=reflection_model,
            curator_model=reflection_model,
            max_tokens=4096,
            use_bulletpoint_analyzer=False,
        )

    def accumulate_context(
        self,
        tasks: list[str],
        num_epochs: int = 1,
        max_num_rounds: int = 3,
        curator_frequency: int = 1,
    ) -> str:
        """
        Accumulate context using ACE.

        Args:
            tasks: List of task descriptions
            num_epochs: Number of training epochs (default: 1)
            max_num_rounds: Max reflection rounds (default: 3)
            curator_frequency: Run curator every N steps (default: 1)

        Returns:
            Accumulated context/playbook
        """
        try:
            # Initialize ACE system if not already done
            self._initialize_ace_system()

            if not self.ace_system:
                # Fallback if ACE initialization failed
                self.accumulated_context = ""
                return self.accumulated_context

            # Create data processor for agent tasks
            data_processor = AgentDataProcessor(task_name="superopt_comparison")

            # Convert tasks to ACE format
            ace_tasks = []
            for task in tasks:
                ace_tasks.append(
                    {
                        "input": task,
                        "output": "",  # No ground truth for agent tasks
                    }
                )

            # Process task data
            processed_tasks = data_processor.process_task_data(ace_tasks)

            # Split into train/val sets (ACE expects both)
            split_idx = len(processed_tasks) * 2 // 3
            train_samples = processed_tasks[:split_idx]
            val_samples = processed_tasks[split_idx:]

            # Configure ACE run
            config = {
                "num_epochs": num_epochs,
                "max_num_rounds": max_num_rounds,
                "curator_frequency": curator_frequency,
                "eval_steps": len(train_samples),  # Evaluate at end
                "save_steps": len(train_samples),  # Save at end
                "playbook_token_budget": 80000,
                "task_name": "superopt_comparison",
                "json_mode": False,
                "no_ground_truth": True,  # No ground truth for agent tasks
                "save_dir": "./results/ace",
                "test_workers": 1,
                "use_bulletpoint_analyzer": False,
            }

            # Run ACE accumulation in offline mode
            _result = self.ace_system.run(
                mode="offline",
                train_samples=train_samples,
                val_samples=val_samples,
                data_processor=data_processor,
                config=config,
            )

            # Extract best playbook
            self.accumulated_context = self.ace_system.best_playbook or self.ace_system.playbook

            return self.accumulated_context

        except Exception as e:
            # Fallback on error - return empty context
            import warnings

            warnings.warn(
                f"ACE accumulation failed: {e}. Using empty context.",
                UserWarning,
            )
            self.accumulated_context = ""
            return self.accumulated_context

    def apply_context(
        self,
        environment: AgenticEnvironment,
        context: str | None = None,
    ) -> AgenticEnvironment:
        """
        Apply ACE-accumulated context to environment.

        Args:
            environment: Base environment
            context: ACE-accumulated context (optional, uses accumulated_context if not provided)

        Returns:
            Environment with ACE context applied
        """
        # Use provided context or accumulated context
        if context is None:
            context = self.accumulated_context or ""

        # Create new environment (don't mutate original)
        from dataclasses import replace

        # Append ACE playbook to system prompt
        new_system_prompt = environment.prompts.system_prompt
        if context:
            new_system_prompt += "\n\n## ACE Accumulated Playbook\n\n" + context

        new_prompts = replace(environment.prompts, system_prompt=new_system_prompt)

        new_env = replace(
            environment,
            prompts=new_prompts,
        )

        return new_env

    def get_context(self) -> str:
        """Get accumulated context."""
        return self.accumulated_context or ""
