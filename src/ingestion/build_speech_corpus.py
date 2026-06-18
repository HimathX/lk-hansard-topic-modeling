import logging
import re
import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError:  # pragma: no cover - reported before execution
    pd = None

try:
    from thefuzz import fuzz, process
except ImportError:  # pragma: no cover - reported before execution
    fuzz = None
    process = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MARKDOWN_ROOT = ROOT / "data" / "extracted-markdown"
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "final_v14"
DEFAULT_REPORT_PATH = ROOT / "artifacts" / "final_v14" / "markdown_extraction_report.csv"


SPEAKER_BLOCK_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:\*\*)?(?:\[)?([^\]\n*:]+?)(?:\])?(?:\*\*)?\s*:\s*(.+?)"
    r"(?=(?:\n\s*(?:\*\*)?(?:\[)?[^\]\n*:]+?(?:\])?(?:\*\*)?\s*:)|$)",
    re.DOTALL,
)


def normalize_speakers(df, column_name="speaker", threshold=85):
    """
    Fuzzy matches speaker names. Sorts by length descending to ensure
    the longest (most formal, e.g. "Ranil Wickremesinghe") becomes the canonical name.
    """
    if fuzz is None or process is None:
        raise RuntimeError("Missing dependency: install thefuzz to normalize speaker names.")

    unique_speakers = sorted(
        [s for s in df[column_name].unique() if isinstance(s, str)],
        key=len,
        reverse=True,
    )
    canonical_mapping = {}
    processed = set()

    for speaker in unique_speakers:
        if speaker in processed:
            continue

        matches = process.extract(
            speaker, unique_speakers, scorer=fuzz.token_sort_ratio, limit=len(unique_speakers)
        )
        valid_matches = [m[0] for m in matches if m[1] >= threshold]

        for match in valid_matches:
            canonical_mapping[match] = speaker
            processed.add(match)

    df[column_name] = df[column_name].map(canonical_mapping).fillna(df[column_name])
    return df


def discover_valid_markdown_files(markdown_root: Path) -> list[Path]:
    if not markdown_root.exists():
        raise FileNotFoundError(f"Markdown root not found: {markdown_root}")

    all_md_files = sorted(markdown_root.rglob("*.md"))
    valid_files = []
    skipped_empty_flag = 0
    skipped_blank = 0

    for md_file in all_md_files:
        if md_file.stem.endswith("-empty"):
            skipped_empty_flag += 1
            continue

        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            skipped_blank += 1
            continue

        valid_files.append(md_file)

    log.info(
        "Discovered %d markdown file(s): %d valid, %d '-empty', %d blank",
        len(all_md_files),
        len(valid_files),
        skipped_empty_flag,
        skipped_blank,
    )
    return valid_files


def process_pipeline(raw_records, output_dir=None):
    """
    raw_records: List of dicts [{'date': '...', 'speaker': '...', 'text': '...'}]
    Outputs a single all_speakers.csv; no chunking.
    """
    if pd is None:
        raise RuntimeError("Missing dependency: install pandas to build the speech corpus.")

    output_root = Path(output_dir) if output_dir else Path.cwd()
    output_root.mkdir(parents=True, exist_ok=True)
    speeches_out = output_root / "all_speakers.csv"

    if not raw_records:
        pd.DataFrame(columns=["speech_id", "date", "speaker", "text"]).to_csv(
            speeches_out, index=False, encoding="utf-8-sig"
        )
        log.warning("No input records. Wrote empty all_speakers.csv")
        return

    df = pd.DataFrame(raw_records)

    # Normalize speaker names
    df = normalize_speakers(df, column_name="speaker", threshold=85)

    # Assign unique speech ID
    df["speech_id"] = [f"SP_{i:05d}" for i in range(len(df))]

    df = df[["speech_id", "date", "speaker", "text"]]
    df.to_csv(speeches_out, index=False, encoding="utf-8-sig")

    log.info("Pipeline V4 complete. Wrote %s (%d rows)", speeches_out, len(df))


def build_raw_records(md_files, min_words=50):
    if pd is None:
        raise RuntimeError("Missing dependency: install pandas to build the speech corpus.")

    records = []
    file_stats = []

    for md_path in md_files:
        log.info("Reading %s", md_path.name)
        text = md_path.read_text(encoding="utf-8")
        matches = SPEAKER_BLOCK_PATTERN.findall(text)
        log.info("  Found %d speaker segments", len(matches))
        date_str = md_path.stem.replace("_", "-")

        file_speech_count = 0
        for speaker, speech in matches:
            speaker = speaker.strip()
            speech = re.sub(r"\s+", " ", speech.strip())
            if not speech:
                continue

            if len(speech.split()) < min_words:
                continue

            records.append({"date": date_str, "speaker": speaker, "text": speech})
            file_speech_count += 1

        file_stats.append(
            {
                "file_path": str(md_path),
                "file_name": md_path.name,
                "speaker_segments_found": len(matches),
                "speech_records_extracted": file_speech_count,
            }
        )

    return records, pd.DataFrame(file_stats)


def parse_args():
    parser = argparse.ArgumentParser(description="Build all_speakers.csv from extracted Hansard markdown.")
    parser.add_argument("--markdown-root", type=Path, default=DEFAULT_MARKDOWN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--min-words", type=int, default=50)
    return parser.parse_args()


def main():
    args = parse_args()
    if pd is None:
        raise SystemExit("Missing dependency: install pandas, for example `pip install -r requirements.txt`.")
    if fuzz is None or process is None:
        raise SystemExit("Missing dependency: install thefuzz, for example `pip install -r requirements.txt`.")

    markdown_root = args.markdown_root

    md_files = discover_valid_markdown_files(markdown_root)
    if not md_files:
        log.warning("No valid markdown files found in: %s", markdown_root)
        process_pipeline([], output_dir=args.output_dir)
        return

    log.info("Found %d markdown file(s) in %s", len(md_files), markdown_root)
    raw_records, file_stats_df = build_raw_records(md_files, min_words=args.min_words)

    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    file_stats_df.to_csv(args.report_path, index=False, encoding="utf-8-sig")

    zero_speech_df = file_stats_df[file_stats_df["speech_records_extracted"] == 0]
    if zero_speech_df.empty:
        log.info("All markdown files produced at least 1 speech record.")
    else:
        log.warning(
            "Found %d markdown file(s) with 0 extracted speeches. Report: %s",
            len(zero_speech_df),
            args.report_path,
        )
        for file_name in zero_speech_df["file_name"].tolist():
            log.warning("  0 speeches: %s", file_name)

    log.info("Extracted %d total speaker record(s)", len(raw_records))
    process_pipeline(raw_records, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
