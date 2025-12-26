"""
Model Configuration for Comparison Experiments

Provides unified model configuration for SuperOpt vs GEPA vs ACE comparisons.
Supports both local (Ollama) and cloud (OpenAI, Anthropic) models.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ModelProvider(Enum):
    """Supported model providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class ModelConfig:
    """
    Model configuration for comparison experiments.

    Ensures all methods (SuperOpt, GEPA, ACE) use the same models
    for fair comparison.
    """

    task_model: str
    reflection_model: str
    provider: ModelProvider
    api_base: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None

    def __post_init__(self):
        """Validate configuration."""
        if self.provider == ModelProvider.OLLAMA:
            if not self.api_base:
                # Default Ollama API base
                self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        elif self.provider == ModelProvider.OPENAI:
            # Only require API key if actually using OpenAI (not lazy-loaded configs)
            if not self.api_key:
                self.api_key = os.getenv("OPENAI_API_KEY")
            # Don't raise error here - let it fail at runtime if key is missing
        elif self.provider == ModelProvider.ANTHROPIC:
            if not self.api_key:
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
            # Don't raise error here - let it fail at runtime if key is missing

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_model": self.task_model,
            "reflection_model": self.reflection_model,
            "provider": self.provider.value,
            "api_base": self.api_base,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelConfig":
        """Create from dictionary."""
        return cls(
            task_model=data["task_model"],
            reflection_model=data["reflection_model"],
            provider=ModelProvider(data["provider"]),
            api_base=data.get("api_base"),
            api_key=data.get("api_key"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens"),
        )


# Predefined model configurations

# Local development models (Ollama)

# Large local models (recommended if available)
LOCAL_LARGE_CONFIG = ModelConfig(
    task_model="ollama/gpt-oss:20b",
    reflection_model="ollama/gpt-oss:120b",
    provider=ModelProvider.OLLAMA,
    temperature=0.7,
)

# Large local models (balanced - use 20b for both if 120b is too slow)
LOCAL_LARGE_BALANCED = ModelConfig(
    task_model="ollama/gpt-oss:20b",
    reflection_model="ollama/gpt-oss:20b",
    provider=ModelProvider.OLLAMA,
    temperature=0.7,
)

# Small local models (for lower-end hardware)
LOCAL_DEV_CONFIG = ModelConfig(
    task_model="ollama/qwen2.5:7b",
    reflection_model="ollama/qwen2.5:14b",
    provider=ModelProvider.OLLAMA,
    temperature=0.7,
)

LOCAL_DEV_CONFIG_SMALL = ModelConfig(
    task_model="ollama/qwen2.5:7b",
    reflection_model="ollama/qwen2.5:7b",  # Use same model if 14b not available
    provider=ModelProvider.OLLAMA,
    temperature=0.7,
)

LOCAL_DEV_CONFIG_LLAMA = ModelConfig(
    task_model="ollama/llama3.1:8b",
    reflection_model="ollama/llama3.1:8b",
    provider=ModelProvider.OLLAMA,
    temperature=0.7,
)

# Small 3B model config - for testing with weaker models
LOCAL_DEV_CONFIG_LLAMA_SMALL = ModelConfig(
    task_model="ollama/llama3.2:3b",
    reflection_model="ollama/llama3.2:3b",
    provider=ModelProvider.OLLAMA,
    temperature=0.7,
)

LOCAL_DEV_CONFIG_QWEN = ModelConfig(
    task_model="ollama/qwen3:8b",
    reflection_model="ollama/qwen3:8b",
    provider=ModelProvider.OLLAMA,
    temperature=0.7,
)


# Cloud development models (lazy initialization to avoid API key requirement at import)
def _create_cloud_dev_config():
    """Create cloud dev config (lazy to avoid API key requirement)."""
    return ModelConfig(
        task_model="openai/gpt-4o-mini",
        reflection_model="openai/gpt-4o",
        provider=ModelProvider.OPENAI,
        temperature=0.7,
    )


def _create_cloud_dev_config_anthropic():
    """Create Anthropic cloud dev config (lazy to avoid API key requirement)."""
    return ModelConfig(
        task_model="anthropic/claude-3-5-haiku-20241022",
        reflection_model="anthropic/claude-3-5-sonnet-20241022",
        provider=ModelProvider.ANTHROPIC,
        temperature=0.7,
    )


def _create_production_config():
    """Create production config (lazy to avoid API key requirement)."""
    return ModelConfig(
        task_model="openai/gpt-4o",
        reflection_model="openai/gpt-4o",
        provider=ModelProvider.OPENAI,
        temperature=0.7,
    )


# Lazy-loaded configs (created on first access)
_CLOUD_DEV_CONFIG = None
_CLOUD_DEV_CONFIG_ANTHROPIC = None
_PRODUCTION_CONFIG = None


def _get_cloud_dev_config():
    """Get or create cloud dev config."""
    global _CLOUD_DEV_CONFIG
    if _CLOUD_DEV_CONFIG is None:
        _CLOUD_DEV_CONFIG = _create_cloud_dev_config()
    return _CLOUD_DEV_CONFIG


def _get_cloud_dev_config_anthropic():
    """Get or create Anthropic cloud dev config."""
    global _CLOUD_DEV_CONFIG_ANTHROPIC
    if _CLOUD_DEV_CONFIG_ANTHROPIC is None:
        _CLOUD_DEV_CONFIG_ANTHROPIC = _create_cloud_dev_config_anthropic()
    return _CLOUD_DEV_CONFIG_ANTHROPIC


def _get_production_config():
    """Get or create production config."""
    global _PRODUCTION_CONFIG
    if _PRODUCTION_CONFIG is None:
        _PRODUCTION_CONFIG = _create_production_config()
    return _PRODUCTION_CONFIG


def get_model_config(config_name: str = "local_large") -> ModelConfig:
    """
    Get a predefined model configuration.

    Args:
        config_name: Name of configuration to use
            - "local_large": Large local models (gpt-oss:20b + 120b) [DEFAULT]
            - "local_large_balanced": Large local models (gpt-oss:20b for both)
            - "local_dev": Small local models (qwen2.5:7b + 14b)
            - "local_dev_small": Small local models (qwen2.5:7b only)
            - "local_dev_llama": Small local models (llama3.1:8b)
            - "local_dev_qwen": Small local models (qwen3:8b)
            - "cloud_dev": Cloud OpenAI models (gpt-4o-mini + gpt-4o)
            - "cloud_dev_anthropic": Cloud Anthropic models
            - "production": Production OpenAI models (gpt-4o)

    Returns:
        ModelConfig instance
    """
    configs = {
        "local_large": LOCAL_LARGE_CONFIG,
        "local_large_balanced": LOCAL_LARGE_BALANCED,
        "local_dev": LOCAL_DEV_CONFIG,
        "local_dev_small": LOCAL_DEV_CONFIG_SMALL,
        "local_dev_llama": LOCAL_DEV_CONFIG_LLAMA,
        "local_dev_llama_small": LOCAL_DEV_CONFIG_LLAMA_SMALL,
        "local_dev_qwen": LOCAL_DEV_CONFIG_QWEN,
        "cloud_dev": _get_cloud_dev_config(),
        "cloud_dev_anthropic": _get_cloud_dev_config_anthropic(),
        "production": _get_production_config(),
    }

    if config_name not in configs:
        raise ValueError(f"Unknown config name: {config_name}. Available: {list(configs.keys())}")

    return configs[config_name]


def create_llm_client(model_config: ModelConfig):
    """
    Create an LLM client from model configuration.

    Uses litellm for unified interface across providers.

    Args:
        model_config: Model configuration

    Returns:
        LLM client instance
    """
    try:
        import litellm
    except ImportError:
        raise ImportError(
            "litellm is required for LLM client creation. Install with: pip install litellm"
        )

    # Configure litellm based on provider
    if model_config.provider == ModelProvider.OLLAMA:
        # Ollama uses local API
        os.environ["OLLAMA_API_BASE"] = model_config.api_base or "http://localhost:11434"
    elif model_config.provider == ModelProvider.OPENAI:
        if model_config.api_key:
            os.environ["OPENAI_API_KEY"] = model_config.api_key
    elif model_config.provider == ModelProvider.ANTHROPIC:
        if model_config.api_key:
            os.environ["ANTHROPIC_API_KEY"] = model_config.api_key

    # Return litellm client wrapper
    class LLMClient:
        def __init__(self, config: ModelConfig):
            self.config = config
            self.litellm = litellm

        def generate(self, prompt: str, model: str | None = None, **kwargs) -> str:
            """Generate text using the specified model."""
            model_name = model or self.config.task_model
            response = self.litellm.completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )
            return response.choices[0].message.content

        def generate_reflection(self, prompt: str, **kwargs) -> str:
            """Generate reflection using reflection model."""
            return self.generate(
                prompt,
                model=self.config.reflection_model,
                **kwargs,
            )

    return LLMClient(model_config)
