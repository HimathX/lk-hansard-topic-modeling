"""Publish the processed Sri Lankan Hansard dataset to Hugging Face.

Usage:
    python src/publishing/publish_huggingface_dataset.py --dry-run
    python src/publishing/publish_huggingface_dataset.py --repo-id owner/dataset-name
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from datasets import Dataset, DatasetDict
from dotenv import load_dotenv
from huggingface_hub import login


ROOT = Path(__file__).resolve().parents[2]
SPEECHES_CSV = ROOT / "artifacts" / "final_v14" / "all_speakers.csv"
CLUSTER_CSV = ROOT / "artifacts" / "final_v14" / "v11_cluster_assignments.csv"
MACRO_CSV = ROOT / "artifacts" / "final_v14" / "macro_topic_assignments.csv"
DEFAULT_REPO_ID = "himath-nimpura/sl-parliamentary-hansard-17-26"

load_dotenv(ROOT / ".env")


def build_dataset_frame(
    speeches_csv: Path = SPEECHES_CSV,
    cluster_csv: Path = CLUSTER_CSV,
    macro_csv: Path = MACRO_CSV,
) -> pd.DataFrame:
    """Merge speech text, micro-topic labels, and macro-topic labels."""
    print("Loading speeches...")
    speeches = pd.read_csv(speeches_csv, encoding="utf-8-sig")
    speeches.columns = speeches.columns.str.lstrip("\ufeff")

    if "year" not in speeches.columns:
        speeches["date"] = pd.to_datetime(speeches["date"], errors="coerce")
        speeches["year"] = speeches["date"].dt.year.astype("Int16")

    speeches = speeches[["speech_id", "date", "speaker", "text", "year"]].copy()
    speeches["date"] = speeches["date"].astype(str)
    speeches["year"] = speeches["year"].astype("Int64")
    print(f"  {len(speeches):,} speeches loaded.")

    print("Loading cluster assignments...")
    clusters = pd.read_csv(cluster_csv)
    clusters = clusters[["speech_id", "hdbscan_cluster"]].copy()
    clusters.rename(columns={"hdbscan_cluster": "micro_topic_cluster"}, inplace=True)
    clusters["micro_topic_cluster"] = pd.to_numeric(
        clusters["micro_topic_cluster"], errors="coerce"
    ).astype("Int64")
    print(f"  {len(clusters):,} cluster rows loaded.")

    if macro_csv.exists():
        print("Loading macro topic assignments...")
        macro = pd.read_csv(macro_csv)[["speech_id", "macro_topic"]]
        print(f"  {len(macro):,} macro topic rows loaded.")
    else:
        macro = None
        print("  macro_topic_assignments.csv not found; skipping macro_topic column.")

    df = speeches.merge(clusters, on="speech_id", how="left")
    if macro is not None:
        df = df.merge(macro, on="speech_id", how="left")

    print(f"\nFinal dataset: {len(df):,} rows, {list(df.columns)} columns")
    print(df.dtypes)
    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish the processed Hansard dataset.")
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument("--speeches-csv", type=Path, default=SPEECHES_CSV)
    parser.add_argument("--cluster-csv", type=Path, default=CLUSTER_CSV)
    parser.add_argument("--macro-csv", type=Path, default=MACRO_CSV)
    parser.add_argument("--dry-run", action="store_true", help="Build the dataset frame without pushing.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = build_dataset_frame(args.speeches_csv, args.cluster_csv, args.macro_csv)
    if args.dry_run:
        print("Dry run complete; not pushing to Hugging Face.")
        return

    token = os.environ.get("HF_TOKEN")
    if not token:
        raise EnvironmentError("Could not find HF_TOKEN. Save it in .env or the environment.")
    login(token)

    print("Converting to Hugging Face Dataset...")
    dataset_dict = DatasetDict({"train": Dataset.from_pandas(df, preserve_index=False)})

    print(f"\nPushing to {args.repo_id} ...")
    dataset_dict.push_to_hub(args.repo_id)
    print(f"\nDone: https://huggingface.co/datasets/{args.repo_id}")


if __name__ == "__main__":
    main()
