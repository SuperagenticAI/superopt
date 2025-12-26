# Data Directory

This directory contains datasets and task files for evaluation experiments.

## Structure

```
data/
├── tasks/                    # Task datasets
│   ├── sample_tasks.json     # Small sample dataset (10 tasks)
│   ├── prompt_only_tasks.json  # Prompt optimization tasks (10 tasks)
│   ├── multi_dimensional_tasks.json  # Multi-dimensional tasks (10 tasks)
│   ├── formatted/           # Auto-generated formatted datasets
│   │   ├── gepa_train.json  # GEPA training set
│   │   ├── gepa_val.json    # GEPA validation set
│   │   ├── ace_train.jsonl  # ACE training set (JSONL)
│   │   ├── ace_val.jsonl    # ACE validation set (JSONL)
│   │   ├── ace_test.jsonl   # ACE test set (JSONL)
│   │   └── superopt_tasks.json  # SuperOpt format
│   └── README.md            # Task dataset documentation
└── README.md                # This file
```

## Quick Start

### Using Sample Dataset

```bash
# Run baseline evaluation
python scripts/evaluate_baseline.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/baseline.json

# Run GEPA evaluation
python scripts/evaluate_gepa.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/gepa.json

# Run comprehensive comparison
python scripts/compare_all.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/comparison.json
```

### Converting Dataset Formats

```bash
# Convert to all formats (GEPA, ACE, SuperOpt)
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

## Dataset Descriptions

### Sample Tasks (`sample_tasks.json`)
- **Size**: 10 tasks
- **Purpose**: Quick testing and validation
- **Types**: Mix of format violations, missing constraints, ambiguous instructions
- **Use case**: Initial testing of evaluation pipeline

### Prompt-Only Tasks (`prompt_only_tasks.json`)
- **Size**: 10 tasks
- **Purpose**: Test prompt optimization (SuperPrompt vs GEPA)
- **Categories**:
  - Format violations (4 tasks)
  - Missing constraints (3 tasks)
  - Ambiguous instructions (3 tasks)
- **Use case**: Compare SuperPrompt against GEPA on prompt-related failures

### Multi-Dimensional Tasks (`multi_dimensional_tasks.json`)
- **Size**: 10 tasks
- **Purpose**: Test multi-dimensional optimization
- **Categories**:
  - Tool errors (3 tasks)
  - Retrieval failures (3 tasks)
  - Mixed failures (4 tasks)
- **Use case**: Demonstrate SuperOpt's advantage over GEPA (can fix tool/retrieval issues)

## Task Format

All tasks use SuperOpt format (JSON):

```json
[
    {
        "task_description": "Task description here",
        "expected_output": "Optional expected output",
        "task_id": "unique_id",
        "category": "task_category",
        "difficulty": "easy|medium|hard",
        "metadata": {
            "failure_type": "prompt|tool|retrieval|mixed",
            "source": "synthetic|real"
        }
    }
]
```

## Creating Custom Datasets

1. Create a JSON file with task descriptions:
   ```json
   [
       {
           "task_description": "Your task here",
           "expected_output": "Optional"
       }
   ]
   ```

2. Validate format:
   ```bash
   python -c "import json; json.load(open('data/tasks/your_tasks.json'))"
   ```

3. Convert to other formats:
   ```bash
   python scripts/prepare_datasets.py \
       --input data/tasks/your_tasks.json \
       --output-dir data/tasks/your_formatted \
       --format all
   ```

## Notes

- All datasets are in SuperOpt format by default
- Use `prepare_datasets.py` to convert to GEPA/ACE formats
- Tasks should be executable by your agent adapter
- Include metadata for better analysis and categorization

