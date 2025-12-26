#!/usr/bin/env python3
"""
Model Setup Script

Helps set up and verify model configurations for comparison experiments.
"""

import argparse
import subprocess
import sys


def check_ollama_installed() -> bool:
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_ollama():
    """Install Ollama."""
    print("Installing Ollama...")
    print("Please visit: https://ollama.com/download")
    print("Or run: curl -fsSL https://ollama.com/install.sh | sh")
    sys.exit(1)


def check_model_available(model_name: str) -> bool:
    """Check if a model is available in Ollama."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
        )
        return model_name in result.stdout
    except Exception:
        return False


def pull_model(model_name: str):
    """Pull a model from Ollama."""
    print(f"Pulling model: {model_name}")
    result = subprocess.run(
        ["ollama", "pull", model_name],
        text=True,
    )
    if result.returncode == 0:
        print(f"✓ Successfully pulled {model_name}")
    else:
        print(f"✗ Failed to pull {model_name}")
        return False
    return True


def setup_local_models():
    """Set up local Ollama models for development."""
    print("Setting up local models for development...")
    print()

    # Check Ollama installation
    if not check_ollama_installed():
        print("Ollama is not installed.")
        install_ollama()
        return

    print("✓ Ollama is installed")
    print()

    # Recommended models (prioritize large models if available)
    models = [
        {
            "name": "gpt-oss:20b",
            "description": "Task execution model (20B parameters) [RECOMMENDED]",
            "required": True,
        },
        {
            "name": "gpt-oss:120b",
            "description": "Reflection/optimization model (120B parameters) [RECOMMENDED]",
            "required": False,  # Can fall back to 20b if too slow
        },
        {
            "name": "qwen2.5:7b",
            "description": "Alternative task model (7B parameters) - for lower-end hardware",
            "required": False,
        },
        {
            "name": "qwen2.5:14b",
            "description": "Alternative reflection model (14B parameters) - for lower-end hardware",
            "required": False,
        },
    ]

    print("Recommended models:")
    for model in models:
        status = "✓" if check_model_available(model["name"]) else "✗"
        required = " (required)" if model["required"] else " (optional)"
        print(f"  {status} {model['name']:20} - {model['description']}{required}")
    print()

    # Pull missing models
    for model in models:
        if not check_model_available(model["name"]):
            if model["required"]:
                response = input(f"Pull {model['name']}? (y/n): ")
                if response.lower() == "y":
                    pull_model(model["name"])
            else:
                response = input(f"Pull optional model {model['name']}? (y/n): ")
                if response.lower() == "y":
                    pull_model(model["name"])

    print()
    print("Model setup complete!")
    print()
    print("Usage in code:")
    print("  from superopt.comparison.models import get_model_config")
    print("  config = get_model_config('local_dev')")


def test_model_config(config_name: str):
    """Test a model configuration."""
    print(f"Testing model configuration: {config_name}")

    try:
        from superopt.comparison.models import create_llm_client, get_model_config

        config = get_model_config(config_name)
        print(f"  Task model: {config.task_model}")
        print(f"  Reflection model: {config.reflection_model}")
        print(f"  Provider: {config.provider.value}")

        # Try to create client
        try:
            client = create_llm_client(config)
            print("  ✓ Client created successfully")

            # Test generation
            print("  Testing generation...")
            response = client.generate("Say 'Hello' if you can read this.")
            print(f"  ✓ Generation successful: {response[:50]}...")

        except Exception as e:
            print(f"  ✗ Client creation failed: {e}")
            print("  Make sure models are available and API keys are set.")

    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        print("  Install dependencies: pip install litellm")


def main():
    parser = argparse.ArgumentParser(description="Set up models for comparison experiments")
    parser.add_argument(
        "action",
        choices=["setup", "test"],
        help="Action to perform",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="local_dev",
        help="Model configuration to test (default: local_dev)",
    )

    args = parser.parse_args()

    if args.action == "setup":
        setup_local_models()
    elif args.action == "test":
        test_model_config(args.config)


if __name__ == "__main__":
    main()
