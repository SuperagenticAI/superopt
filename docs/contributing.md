# Contributing to SuperOpt

Thank you for your interest in contributing to SuperOpt! This document provides guidelines and instructions for contributing.

## Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SuperagenticAI/superopt.git
   cd superopt
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Using pip
   pip install -e ".[dev]"

   # Or using uv
   uv sync --all-extras
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Style

We use the following tools to maintain code quality:

- **Ruff** for linting and import sorting
- **Black** for code formatting
- **MyPy** for type checking

Run all checks:
```bash
# Linting
ruff check .

# Formatting
black .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=superopt --cov-report=html

# Run specific test file
pytest tests/comparison/test_gepa_adapter.py -v
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run manually:
```bash
pre-commit run --all-files
```

## Making Contributions

### Reporting Issues

- Search existing issues before creating a new one
- Use the issue templates when available
- Include reproduction steps for bugs
- Provide system information (Python version, OS, etc.)

### Pull Requests

1. **Fork and branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, concise commit messages
   - Add tests for new functionality
   - Update documentation as needed

3. **Run checks locally**
   ```bash
   ruff check .
   black --check .
   pytest
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

### Commit Messages

Follow conventional commit format:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Example:
```
feat: add support for custom retrieval strategies in SuperRAG

- Implement pluggable retrieval strategy interface
- Add hybrid search strategy combining vector and FTS
- Update documentation with examples
```

## Project Structure

```
superopt/
├── superopt/           # Main package
│   ├── core/           # Core abstractions (environment, trace, nlg)
│   ├── adapters/       # Agent framework integrations
│   ├── comparison/     # Comparison with baselines (GEPA, ACE)
│   ├── rag/            # RAG optimization components
│   └── *.py            # Optimizer modules
├── tests/              # Test suite
├── scripts/            # Evaluation scripts
├── examples/           # Usage examples
└── data/               # Task datasets
```

## Areas for Contribution

We welcome contributions in these areas:

- **New Adapters**: Integrations with other agent frameworks
- **Optimization Strategies**: Novel approaches for environment optimization
- **Benchmarks**: New evaluation tasks and datasets
- **Documentation**: Tutorials, examples, API documentation
- **Bug Fixes**: Issue resolution and stability improvements

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

- Open a [GitHub Discussion](https://github.com/SuperagenticAI/superopt/discussions)
- Email: team@super-agentic.ai

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
