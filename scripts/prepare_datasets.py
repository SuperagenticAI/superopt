#!/usr/bin/env python3
"""
Prepare Datasets for Evaluation

Converts task datasets between different formats (SuperOpt, GEPA, ACE)
and creates train/val splits.
"""

import argparse
import json
from pathlib import Path


def load_superopt_format_full(file_path: Path):
    """Load tasks in SuperOpt format (full dictionaries)."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("SuperOpt format expects a list of task dictionaries")

    return data


def convert_to_gepa_format(tasks):
    """Convert tasks to GEPA format and split into train/val sets."""
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


def convert_to_ace_format(tasks):
    """Convert tasks to ACE format (JSONL-ready dictionaries)."""
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


def save_tasks_to_file(tasks, file_path: Path, format: str = "json"):
    """Save tasks to a file in specified format."""
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


def main():
    parser = argparse.ArgumentParser(description="Prepare datasets for evaluation")
    parser.add_argument(
        "--input", type=str, required=True, help="Input task file (SuperOpt format)"
    )
    parser.add_argument(
        "--output-dir", type=str, required=True, help="Output directory for formatted datasets"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="all",
        choices=["all", "gepa", "ace", "superopt"],
        help="Output format(s)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return

    print(f"Loading tasks from {input_path}...")
    tasks = load_superopt_format_full(input_path)
    print(f"Loaded {len(tasks)} tasks")

    # Convert to different formats
    if args.format in ["all", "gepa"]:
        print("Converting to GEPA format...")
        trainset, valset = convert_to_gepa_format(tasks)

        train_path = output_dir / "gepa_train.json"
        val_path = output_dir / "gepa_val.json"

        with open(train_path, "w") as f:
            json.dump(trainset, f, indent=2)

        with open(val_path, "w") as f:
            json.dump(valset, f, indent=2)

        print(f"  Train: {len(trainset)} tasks -> {train_path}")
        print(f"  Val: {len(valset)} tasks -> {val_path}")

    if args.format in ["all", "ace"]:
        print("Converting to ACE format...")
        ace_tasks = convert_to_ace_format(tasks)

        # Split for ACE (train/val/test)
        split1 = len(ace_tasks) * 2 // 3
        split2 = len(ace_tasks) * 5 // 6

        train_tasks = ace_tasks[:split1]
        val_tasks = ace_tasks[split1:split2]
        test_tasks = ace_tasks[split2:]

        train_path = output_dir / "ace_train.jsonl"
        val_path = output_dir / "ace_val.jsonl"
        test_path = output_dir / "ace_test.jsonl"

        # Save as JSONL
        for path, task_list in [
            (train_path, train_tasks),
            (val_path, val_tasks),
            (test_path, test_tasks),
        ]:
            with open(path, "w") as f:
                for task in task_list:
                    f.write(json.dumps(task, ensure_ascii=False) + "\n")

        print(f"  Train: {len(train_tasks)} tasks -> {train_path}")
        print(f"  Val: {len(val_tasks)} tasks -> {val_path}")
        print(f"  Test: {len(test_tasks)} tasks -> {test_path}")

    if args.format in ["all", "superopt"]:
        print("Saving SuperOpt format...")
        output_path = output_dir / "superopt_tasks.json"
        save_tasks_to_file(tasks, output_path, format="json")
        print(f"  {len(tasks)} tasks -> {output_path}")

    print(f"\nDataset preparation complete! Output directory: {output_dir}")


if __name__ == "__main__":
    main()
