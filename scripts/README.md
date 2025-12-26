# Scripts

Evaluation and comparison scripts for SuperOpt experiments.

## Experiment Scripts (Paper Results)

These scripts were used to generate the results in the paper:

### `run_gepa_comparison.py`
Compares GEPA prompt optimization against SuperOpt.

```bash
python scripts/run_gepa_comparison.py \
    --tasks data/tasks/challenging_tasks.json \
    --superopt-results results/challenging_eval/superopt_3b.json \
    --output results/challenging_eval/gepa_comparison.json \
    --model ollama/llama3.2:3b \
    --max-tasks 5
```

### `run_ace_comparison.py`
Compares ACE context accumulation against SuperOpt's typed memory.

```bash
python scripts/run_ace_comparison.py --max-tasks 5
```

### `run_superrag_comparison.py`
Demonstrates SuperRAG's retrieval parameter optimization vs GEPA.

```bash
pip install -e ".[lancedb]"
python scripts/run_superrag_comparison.py
```

## Evaluation Scripts

### `evaluate_baseline.py`
Run baseline evaluation (no optimization).

```bash
python scripts/evaluate_baseline.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/baseline.json
```

### `evaluate_superopt.py`
Run SuperOpt full environment optimization.

```bash
python scripts/evaluate_superopt.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/superopt.json
```

### `compare_all.py`
Run all methods (baseline, GEPA, ACE, SuperOpt) for comparison.

```bash
python scripts/compare_all.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/comparison.json
```

### `analyze_results.py`
Generate paper-ready analysis tables from results.

```bash
python scripts/analyze_results.py --results-dir results/challenging_eval
```

## Setup Scripts

### `setup_models.py`
Setup and verify Ollama models for local inference.

```bash
python scripts/setup_models.py --check
python scripts/setup_models.py --pull llama3.2:3b
```

### `setup_lancedb.py`
Setup LanceDB vector store for RAG experiments.

```bash
python scripts/setup_lancedb.py --codebase /path/to/code --db-path ./lancedb_store
```

### `prepare_datasets.py`
Convert datasets between formats (SuperOpt, GEPA, ACE).

```bash
python scripts/prepare_datasets.py \
    --input data/tasks/sample_tasks.json \
    --output-dir data/tasks/formatted \
    --format all
```

## Testing

### `test_aider_adapter.py`
Test the Aider adapter integration.

```bash
python scripts/test_aider_adapter.py --model ollama/llama3.2:3b
```

## Results Directory

Pre-computed experimental results are available in `results/`:

```
results/
├── challenging_eval/     # Main paper experiments
│   ├── superopt_3b.json  # SuperOpt results
│   ├── gepa_comparison.json
│   ├── ace_comparison.json
│   ├── superrag_comparison.json
│   └── analysis.md
├── comprehensive_eval/   # Extended evaluation
└── safe_eval/           # Resource-constrained runs
```

## Model Configuration

Scripts use Ollama by default. Set `OLLAMA_API_BASE` for custom endpoint:

```bash
export OLLAMA_API_BASE=http://localhost:11434
```

For OpenAI-compatible APIs:

```bash
python scripts/evaluate_superopt.py \
    --model-config openai \
    --api-base https://api.openai.com/v1
```
