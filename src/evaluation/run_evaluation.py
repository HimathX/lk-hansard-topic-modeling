"""Run reviewer-facing evaluation tables for the Hansard topic models."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from classification_metrics import evaluate_classification
from topic_quality_metrics import load_keyword_topics, topic_quality_summary


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GROUND_TRUTH = ROOT / "data" / "evaluation" / "ground_truth_300.csv"
DEFAULT_CLUSTERS = ROOT / "artifacts" / "final_v14" / "v11_cluster_assignments.csv"
DEFAULT_MACROS = ROOT / "artifacts" / "final_v14" / "macro_topic_assignments.csv"
DEFAULT_SPEECHES = ROOT / "artifacts" / "final_v14" / "all_speakers.csv"
DEFAULT_KEYWORDS = ROOT / "artifacts" / "final_v14" / "macro_topic_keywords.json"
DEFAULT_OUT = ROOT / "artifacts" / "evaluation"


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_eval_frame(args: argparse.Namespace) -> pd.DataFrame:
    gt = pd.read_csv(args.ground_truth)
    gt = gt[gt["is_evaluable"].astype(str).str.lower() == "true"].copy()

    clusters = pd.read_csv(args.clusters)
    df = gt.merge(clusters, on="speech_id", how="inner", suffixes=("", "_cluster"))

    if args.macros.exists():
        macros = pd.read_csv(args.macros)
        df = df.merge(macros, on="speech_id", how="left")
    return df


def run_classification_metrics(df: pd.DataFrame) -> list[dict[str, object]]:
    prediction_columns = [
        ("HDBSCAN micro-topics", "hdbscan_cluster"),
        ("KMeans micro-topics", "kmeans_cluster"),
        ("Agglomerative micro-topics", "agglomerative_cluster"),
        ("Macro-topics", "macro_topic"),
    ]
    rows = []
    for model_name, column in prediction_columns:
        if column not in df.columns:
            continue
        subset = df.dropna(subset=["label", column]).copy()
        if subset.empty:
            continue
        metrics = evaluate_classification(subset["label"], subset[column])
        rows.append({"model": model_name, "prediction_column": column, **asdict(metrics)})
    return rows


def run_topic_quality(args: argparse.Namespace) -> list[dict[str, object]]:
    speeches = pd.read_csv(args.speeches, usecols=["speech_id", "text"])
    labels = pd.read_csv(args.macros) if args.macros.exists() else None
    if labels is None:
        return []
    df = speeches.merge(labels, on="speech_id", how="inner")
    keywords = load_keyword_topics(args.keywords, section=args.keyword_section, top_n=args.top_n)
    summary = topic_quality_summary(
        texts=df["text"].fillna(""),
        labels=df["macro_topic"],
        keyword_topics=keywords,
        top_n=args.top_n,
        noise_label="Procedural Noise",
    )
    return [{"model": "Macro-topics", "keyword_file": str(args.keywords), **summary}]


def write_summary(path: Path, class_rows: list[dict[str, object]], quality_rows: list[dict[str, object]], df: pd.DataFrame) -> None:
    def fmt(value: object) -> str:
        return "n/a" if value is None else f"{float(value):.4f}"

    lines = [
        "# Evaluation Summary",
        "",
        f"Evaluable ground-truth rows: {len(df)}",
        "",
        "## External Validity",
    ]
    for row in class_rows:
        lines.append(
            f"- {row['model']}: B-Cubed F1={fmt(row['bcubed_f1'])}, "
            f"Purity={fmt(row['purity'])}, ARI={fmt(row['ari'])}, NMI={fmt(row['nmi'])}"
        )
    lines.extend(["", "## Topic Quality"])
    for row in quality_rows:
        lines.append(
            f"- {row['model']}: C_V~={row['cv_coherence']:.4f}, "
            f"Topic diversity={row['topic_diversity']:.4f}, "
            f"Clustered={row['clustered_pct']:.2%}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run topic-model evaluation tables.")
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GROUND_TRUTH)
    parser.add_argument("--clusters", type=Path, default=DEFAULT_CLUSTERS)
    parser.add_argument("--macros", type=Path, default=DEFAULT_MACROS)
    parser.add_argument("--speeches", type=Path, default=DEFAULT_SPEECHES)
    parser.add_argument("--keywords", type=Path, default=DEFAULT_KEYWORDS)
    parser.add_argument("--keyword-section", default="tfidf")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    df = load_eval_frame(args)
    class_rows = run_classification_metrics(df)
    quality_rows = run_topic_quality(args)

    _write_rows(args.out_dir / "table_iii_metrics.csv", class_rows)
    _write_rows(args.out_dir / "topic_quality_metrics.csv", quality_rows)
    write_summary(args.out_dir / "evaluation_summary.md", class_rows, quality_rows, df)
    print(f"Wrote evaluation outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
