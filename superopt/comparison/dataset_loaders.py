"""
Dataset Loaders for Comparison Experiments

Provides utilities to load and convert datasets between different formats:
- GEPA format (JSON with input/answer)
- ACE format (JSONL)
- SuperOpt format (JSON with task_description)
"""

import json
from pathlib import Path
from typing import Any


def load_gepa_format(dataset_dir: Path) -> tuple[list[dict], list[dict]]:
    """
    Load tasks in GEPA format (trainset/valset).

    Expected structure:
        dataset_dir/
            train.json  # List of {"input": "...", "answer": "..."}
            val.json    # List of {"input": "...", "answer": "..."}

    Args:
        dataset_dir: Directory containing train.json and val.json

    Returns:
        Tuple of (trainset, valset) as lists of dictionaries
    """
    train_path = dataset_dir / "train.json"
    val_path = dataset_dir / "val.json"

    if not train_path.exists():
        raise FileNotFoundError(f"Training file not found: {train_path}")
    if not val_path.exists():
        raise FileNotFoundError(f"Validation file not found: {val_path}")

    with open(train_path, encoding="utf-8") as f:
        trainset = json.load(f)

    with open(val_path, encoding="utf-8") as f:
        valset = json.load(f)

    # Validate format
    if not isinstance(trainset, list) or not isinstance(valset, list):
        raise ValueError("GEPA format expects lists of dictionaries")

    return trainset, valset


def load_ace_format(file_path: Path) -> list[dict[str, Any]]:
    """
    Load tasks in ACE format (JSONL - one JSON object per line).

    Expected format:
        {"input": "...", "output": "..."}
        {"input": "...", "output": "..."}
        ...

    Args:
        file_path: Path to JSONL file

    Returns:
        List of task dictionaries
    """
    if not file_path.exists():
        raise FileNotFoundError(f"ACE format file not found: {file_path}")

    tasks = []
    with open(file_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            try:
                task = json.loads(line)
                tasks.append(task)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num} of {file_path}: {e}")

    return tasks


def load_superopt_format(file_path: Path) -> list[str]:
    """
    Load tasks in SuperOpt format.

    Expected format:
        [
            {"task_description": "...", "expected_output": "...", ...},
            ...
        ]

    Args:
        file_path: Path to JSON file

    Returns:
        List of task description strings
    """
    if not file_path.exists():
        raise FileNotFoundError(f"SuperOpt format file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("SuperOpt format expects a list of task dictionaries")

    tasks = []
    for item in data:
        if isinstance(item, dict):
            task_desc = item.get("task_description", "")
            if task_desc:
                tasks.append(task_desc)
        elif isinstance(item, str):
            tasks.append(item)

    return tasks


def load_superopt_format_full(file_path: Path) -> list[dict[str, Any]]:
    """
    Load tasks in SuperOpt format (full dictionaries).

    Args:
        file_path: Path to JSON file

    Returns:
        List of full task dictionaries
    """
    if not file_path.exists():
        raise FileNotFoundError(f"SuperOpt format file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("SuperOpt format expects a list of task dictionaries")

    return data


def convert_to_gepa_format(tasks: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Convert tasks to GEPA format and split into train/val sets.

    GEPA expects: [{"input": "...", "answer": "..."}]

    Args:
        tasks: List of task dictionaries with "task_description" key

    Returns:
        Tuple of (trainset, valset) in GEPA format
    """
    gepa_tasks = []

    for task in tasks:
        if isinstance(task, dict):
            task_desc = task.get("task_description", task.get("input", ""))
            expected_output = task.get("expected_output", task.get("answer", ""))
        elif isinstance(task, str):
            task_desc = task
            expected_output = ""
        else:
            continue

        gepa_tasks.append(
            {
                "input": task_desc,
                "answer": expected_output,
            }
        )

    # Split into train/val (2/3 train, 1/3 val)
    split_idx = len(gepa_tasks) * 2 // 3
    trainset = gepa_tasks[:split_idx]
    valset = gepa_tasks[split_idx:]

    return trainset, valset


def convert_to_ace_format(tasks: list[dict]) -> list[dict]:
    """
    Convert tasks to ACE format (JSONL-ready dictionaries).

    ACE expects: {"input": "...", "output": "..."}

    Args:
        tasks: List of task dictionaries

    Returns:
        List of ACE-formatted task dictionaries
    """
    ace_tasks = []

    for task in tasks:
        if isinstance(task, dict):
            task_input = task.get("task_description", task.get("input", ""))
            task_output = task.get("expected_output", task.get("output", ""))
        elif isinstance(task, str):
            task_input = task
            task_output = ""
        else:
            continue

        ace_tasks.append(
            {
                "input": task_input,
                "output": task_output,
            }
        )

    return ace_tasks


def convert_to_superopt_format(tasks: list[dict]) -> list[dict[str, Any]]:
    """
    Convert tasks to SuperOpt format.

    SuperOpt expects: [{"task_description": "...", "expected_output": "...", ...}]

    Args:
        tasks: List of task dictionaries in various formats

    Returns:
        List of SuperOpt-formatted task dictionaries
    """
    superopt_tasks = []

    for task in tasks:
        if isinstance(task, dict):
            # Preserve existing structure, ensure task_description exists
            formatted_task = task.copy()
            if "task_description" not in formatted_task:
                formatted_task["task_description"] = formatted_task.get(
                    "input", formatted_task.get("task", "")
                )
            superopt_tasks.append(formatted_task)
        elif isinstance(task, str):
            superopt_tasks.append(
                {
                    "task_description": task,
                    "expected_output": "",
                }
            )

    return superopt_tasks


def load_tasks_from_file(file_path: Path, format: str | None = None) -> list[Any]:
    """
    Auto-detect and load tasks from a file.

    Args:
        file_path: Path to task file
        format: Optional format hint ("gepa", "ace", "superopt", "jsonl", "json")

    Returns:
        List of tasks (format depends on file type)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Task file not found: {file_path}")

    # Auto-detect format if not specified
    if format is None:
        if file_path.suffix == ".jsonl":
            format = "ace"
        elif file_path.suffix == ".json":
            # Try to detect by reading first line
            with open(file_path, encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("{") and first_line.endswith("}"):
                    format = "ace"  # JSONL format
                else:
                    format = "superopt"  # JSON array format

    if format == "ace" or format == "jsonl":
        return load_ace_format(file_path)
    elif format == "superopt" or format == "json":
        return load_superopt_format_full(file_path)
    else:
        raise ValueError(f"Unknown format: {format}")


def save_tasks_to_file(tasks: list[Any], file_path: Path, format: str = "json"):
    """
    Save tasks to a file in specified format.

    Args:
        tasks: List of tasks to save
        file_path: Output file path
        format: Format to save as ("json", "jsonl", "gepa")
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "jsonl" or format == "ace":
        # Save as JSONL (one JSON object per line)
        with open(file_path, "w", encoding="utf-8") as f:
            for task in tasks:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")

    elif format == "json" or format == "superopt":
        # Save as JSON array
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    elif format == "gepa":
        # Save as GEPA format (split into train/val)
        trainset, valset = convert_to_gepa_format(tasks)

        train_path = file_path.parent / "train.json"
        val_path = file_path.parent / "val.json"

        with open(train_path, "w", encoding="utf-8") as f:
            json.dump(trainset, f, indent=2, ensure_ascii=False)

        with open(val_path, "w", encoding="utf-8") as f:
            json.dump(valset, f, indent=2, ensure_ascii=False)

    else:
        raise ValueError(f"Unknown format: {format}")
