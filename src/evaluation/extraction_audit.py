"""Compare Gemini, Tesseract, and reference extraction outputs on sample pages."""

from __future__ import annotations

import argparse
import csv
import re
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT_DIR = ROOT / "data" / "extraction_audit"
SPEAKER_PATTERN = re.compile(r"\*\*[^:\n]+:\*\*|^\s*[^:\n]{2,120}:", re.MULTILINE)
WORD_PATTERN = re.compile(r"(?u)[\w\u0D80-\u0DFF\u0B80-\u0BFF\u200D\u200C]+")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def word_accuracy(candidate: str, reference: str) -> float:
    cand_words = WORD_PATTERN.findall(normalize_text(candidate))
    ref_words = WORD_PATTERN.findall(normalize_text(reference))
    if not ref_words:
        return 0.0
    matcher = SequenceMatcher(None, ref_words, cand_words)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    return matched / len(ref_words)


def speaker_boundary_f1(candidate: str, reference: str) -> float:
    cand = set(match.group(0).strip() for match in SPEAKER_PATTERN.finditer(candidate))
    ref = set(match.group(0).strip() for match in SPEAKER_PATTERN.finditer(reference))
    if not cand and not ref:
        return 1.0
    if not cand or not ref:
        return 0.0
    tp = len(cand & ref)
    precision = tp / len(cand)
    recall = tp / len(ref)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def layout_similarity(candidate: str, reference: str) -> float:
    return SequenceMatcher(None, normalize_text(reference), normalize_text(candidate)).ratio()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def audit(audit_dir: Path) -> list[dict[str, object]]:
    rows = []
    reference_dir = audit_dir / "reference_outputs"
    gemini_dir = audit_dir / "gemini_outputs"
    tesseract_dir = audit_dir / "tesseract_outputs"

    for ref_path in sorted(reference_dir.glob("*.txt")) + sorted(reference_dir.glob("*.md")):
        sample_id = ref_path.stem
        reference = read_text(ref_path)
        for system_name, system_dir in [("gemini", gemini_dir), ("tesseract", tesseract_dir)]:
            candidate_path = system_dir / ref_path.name
            candidate = read_text(candidate_path)
            rows.append(
                {
                    "sample_id": sample_id,
                    "system": system_name,
                    "candidate_file": str(candidate_path.relative_to(audit_dir)),
                    "reference_file": str(ref_path.relative_to(audit_dir)),
                    "word_accuracy": word_accuracy(candidate, reference),
                    "speaker_boundary_f1": speaker_boundary_f1(candidate, reference),
                    "layout_order_similarity": layout_similarity(candidate, reference),
                    "missing_candidate": not candidate_path.exists(),
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Gemini-vs-Tesseract extraction audit.")
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_AUDIT_DIR / "extraction_audit_results.csv")
    args = parser.parse_args()

    rows = audit(args.audit_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "sample_id",
            "system",
            "candidate_file",
            "reference_file",
            "word_accuracy",
            "speaker_boundary_f1",
            "layout_order_similarity",
            "missing_candidate",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} audit row(s) to {args.output}")


if __name__ == "__main__":
    main()
