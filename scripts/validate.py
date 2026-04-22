#!/usr/bin/env python3
"""Validate all vocabulary CSVs and grammar YAMLs in the project."""

import csv
import sys
import yaml
from pathlib import Path

BASE = Path(__file__).parent.parent
VOCAB_DIR = BASE / "vocabulary"

CSV_REQUIRED_COLUMNS = {"spanish", "french", "category", "icon", "tags", "notes"}
GRAMMAR_REQUIRED_KEYS_SER_ESTAR = {"title", "tables"}
GRAMMAR_REQUIRED_KEYS_NUMBERS = {"title", "numbers"}
GRAMMAR_REQUIRED_KEYS_COLORS = {"title", "colors"}

errors = []
warnings = []


def check_csv(path: Path) -> None:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            errors.append(f"{path}: empty file or no header row")
            return
        columns = set(reader.fieldnames)
        missing = CSV_REQUIRED_COLUMNS - columns
        if missing:
            errors.append(f"{path}: missing columns: {sorted(missing)}")
            return
        for i, row in enumerate(reader, start=2):
            spanish = row.get("spanish", "").strip()
            french = row.get("french", "").strip()
            if spanish and not french:
                warnings.append(f"{path}:{i}: spanish='{spanish}' has no French translation")
            if french and not spanish:
                warnings.append(f"{path}:{i}: french='{french}' has no Spanish word")


def check_yaml(path: Path) -> None:
    with open(path, encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append(f"{path}: YAML parse error: {e}")
            return
    if data is None:
        errors.append(f"{path}: empty YAML file")
        return
    if not isinstance(data, dict):
        errors.append(f"{path}: expected a YAML mapping at the top level")
        return
    if "title" not in data:
        warnings.append(f"{path}: no 'title' key found")


def main() -> int:
    csv_files = sorted(VOCAB_DIR.glob("theme_*.csv")) + sorted(VOCAB_DIR.glob("reference_*.csv"))
    yaml_files = sorted((VOCAB_DIR / "grammar").glob("*.yaml"))

    if not csv_files:
        errors.append(f"No session or reference CSV files found in {VOCAB_DIR}")
    if not yaml_files:
        warnings.append(f"No grammar YAML files found in {VOCAB_DIR / 'grammar'}")

    for p in csv_files:
        check_csv(p)
    for p in yaml_files:
        check_yaml(p)

    for w in warnings:
        print(f"  WARNING  {w}")
    for e in errors:
        print(f"  ERROR    {e}")

    if errors:
        print(f"\n{len(errors)} error(s) found — fix before generating output.")
        return 1

    print(
        f"  OK  {len(csv_files)} CSV file(s) and {len(yaml_files)} YAML file(s) validated "
        f"({len(warnings)} warning(s))."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
