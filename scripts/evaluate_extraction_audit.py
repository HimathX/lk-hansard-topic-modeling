"""Evaluate the manual Hansard extraction audit CSV.

The script intentionally uses only the Python standard library so reviewers can
run it without installing the full modeling stack.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "docs" / "extraction_audit" / "extraction_audit_manual_benchmark_template.csv"

METRICS = [
    ("speaker_correct", "Speaker Accuracy"),
    ("boundary_correct", "Boundary Accuracy"),
    ("layout_order_correct", "Layout Order Accuracy"),
    ("language_preserved", "Language Preservation Accuracy"),
    ("procedural_noise_removed", "Procedural Noise Removal Accuracy"),
]

TRUE_VALUES = {"true", "t", "yes", "y", "1", "correct"}
FALSE_VALUES = {"false", "f", "no", "n", "0", "incorrect"}
TODO_VALUES = {"", "todo", "todo:", "tbd", "na", "n/a", "unknown"}


def parse_bool(value: object) -> bool | None:
    normalized = str(value or "").strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    if normalized in TODO_VALUES or normalized.startswith("todo"):
        return None
    return None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def summarize(rows: Iterable[dict[str, str]]) -> dict[str, tuple[int, int]]:
    counts: dict[str, list[int]] = {field: [0, 0] for field, _ in METRICS}
    for row in rows:
        for field, _ in METRICS:
            value = parse_bool(row.get(field))
            if value is None:
                continue
            counts[field][1] += 1
            if value:
                counts[field][0] += 1
    return {field: (correct, total) for field, (correct, total) in counts.items()}


def format_rate(correct: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{correct / total:.2%}"


def print_summary(title: str, summary: dict[str, tuple[int, int]]) -> None:
    print(f"\n## {title}\n")
    print("| Metric | Score | Checked Rows |")
    print("| --- | ---: | ---: |")
    for field, label in METRICS:
        correct, total = summary[field]
        print(f"| {label} | {format_rate(correct, total)} | {total} |")


def group_by_language(rows: Iterable[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        language = str(row.get("language_category") or "").strip()
        if not language or language.lower().startswith("todo"):
            continue
        has_completed_metric = any(parse_bool(row.get(field)) is not None for field, _ in METRICS)
        if not has_completed_metric:
            continue
        grouped[language].append(row)
    return dict(grouped)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate manual extraction audit annotations.")
    parser.add_argument("csv_path", nargs="?", type=Path, default=DEFAULT_CSV)
    args = parser.parse_args()

    rows = read_rows(args.csv_path)

    print("# Extraction Audit Summary")
    print(f"\nInput: `{args.csv_path}`")
    print(f"Rows loaded: {len(rows)}")

    overall = summarize(rows)
    print_summary("Overall", overall)

    groups = group_by_language(rows)
    if groups:
        print("\n## By Language Category\n")
        for language, language_rows in sorted(groups.items()):
            print_summary(language, summarize(language_rows))

    if all(total == 0 for _, total in overall.values()):
        print("\nNo completed boolean metric cells were found. Replace TODO values with true/false annotations to compute scores.")


if __name__ == "__main__":
    main()
