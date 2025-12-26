# Changelog

All notable changes to SuperOpt will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-25

### Added

- **Core Framework**
  - `SuperOpt` main optimizer class with `step()` and `optimize_episode()` methods
  - `AgenticEnvironment` representing the optimization target Φ = {P, T, R, M}
  - `ExecutionTrace` for capturing agent-environment interactions
  - `NaturalLanguageGradient` for structured environment updates

- **Optimization Components**
  - `SuperController` for failure diagnosis and routing
  - `SuperPrompt` for evolutionary prompt optimization (GEPA-based)
  - `SuperReflexion` for tool schema repair
  - `SuperRAG` for retrieval configuration optimization
  - `SuperMem` for typed memory with decay and conflict resolution

- **Stability System**
  - `MutabilityHierarchy` enforcing stability ordering
  - Validation constraints preventing optimization oscillation

- **Adapters**
  - `AiderAdapter` for Aider coding agent integration
  - `LettaAdapter` for Letta memory agent integration
  - `CodexAdapter` for OpenAI Codex integration
  - Base `AgentAdapter` interface for custom integrations

- **Comparison Framework**
  - GEPA comparison for prompt-only optimization baseline
  - ACE comparison for context accumulation baseline
  - Comprehensive evaluation metrics and analysis

- **RAG Integration**
  - LanceDB vector store integration
  - Support for vector, FTS, and hybrid search modes
  - Configurable retrieval parameters

- **Evaluation**
  - Task datasets for benchmarking
  - Evaluation scripts for reproducible experiments
  - Results analysis and visualization

### Documentation

- Comprehensive README with usage examples
- Architecture documentation
- API reference in docstrings
- Contributing guidelines
