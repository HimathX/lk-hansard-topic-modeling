"""Audit macro-topic aggregation from saved micro-topic outputs.

This script is intentionally separate from the original modeling notebook. It
recomputes reviewer-facing audit tables from available artifacts and clearly
reports when an input needed for centroid clustering is missing.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSIGNMENTS = ROOT / "artifacts" / "final_v14" / "v11_cluster_assignments.csv"
DEFAULT_EMBEDDINGS = ROOT / "artifacts" / "final_v14" / "umap5.npy"
DEFAULT_MACRO_ASSIGNMENTS = ROOT / "artifacts" / "final_v14" / "macro_topic_assignments.csv"
DEFAULT_KEYWORDS = ROOT / "artifacts" / "final_v14" / "macro_topic_keywords.json"
DEFAULT_OUT = ROOT / "docs" / "macro_topic_aggregation"


@dataclass(frozen=True)
class AssignmentRow:
    speech_id: str
    micro_topic: int


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def find_topic_column(rows: list[dict[str, str]], preferred: str | None) -> str:
    if not rows:
        raise ValueError("Assignment CSV has no rows.")
    if preferred and preferred in rows[0]:
        return preferred
    for candidate in ("hdbscan_cluster", "topic", "topic_id", "micro_topic", "micro_topic_id"):
        if candidate in rows[0]:
            return candidate
    raise ValueError(
        "Could not find a micro-topic column. Pass --topic-column, e.g. hdbscan_cluster."
    )


def load_assignments(path: Path, topic_column: str | None, noise_label: int) -> list[AssignmentRow]:
    rows = read_csv_rows(path)
    column = find_topic_column(rows, topic_column)
    if "speech_id" not in rows[0]:
        raise ValueError("Assignment CSV must contain speech_id.")

    assignments = []
    for row in rows:
        value = row.get(column, "")
        if value == "":
            continue
        try:
            micro_topic = int(float(value))
        except ValueError as exc:
            raise ValueError(f"Non-numeric topic value {value!r} in column {column}.") from exc
        assignments.append(AssignmentRow(row["speech_id"], micro_topic))
    if not assignments:
        raise ValueError("No valid speech-topic assignments found.")
    return assignments


def retained_topic_table(
    assignments: Iterable[AssignmentRow],
    mass_threshold: float,
    noise_label: int,
) -> tuple[list[dict[str, object]], dict[str, object], set[int]]:
    counts = Counter(row.micro_topic for row in assignments if row.micro_topic != noise_label)
    total_non_noise = sum(counts.values())
    if total_non_noise == 0:
        raise ValueError("No non-noise speeches found after excluding noise label.")

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    cumulative = 0
    retained: set[int] = set()
    table = []
    reached = False
    for micro_topic, speech_count in ranked:
        cumulative += speech_count
        if not reached:
            retained.add(micro_topic)
        cumulative_mass = cumulative / total_non_noise
        table.append(
            {
                "micro_topic_id": micro_topic,
                "speech_count": speech_count,
                "cumulative_count": cumulative,
                "cumulative_mass": f"{cumulative_mass:.8f}",
                "retained": str(micro_topic in retained).lower(),
            }
        )
        if cumulative_mass >= mass_threshold:
            reached = True

    retained_speech_count = sum(counts[topic] for topic in retained)
    summary = {
        "total_micro_topics_excluding_noise": len(counts),
        "total_substantive_clustered_speeches": total_non_noise,
        "retained_micro_topic_count": len(retained),
        "retained_speech_count": retained_speech_count,
        "retained_speech_mass": retained_speech_count / total_non_noise,
        "excluded_tail_micro_topic_count": len(counts) - len(retained),
        "excluded_tail_speech_count": total_non_noise - retained_speech_count,
    }
    return table, summary, retained


def load_embeddings(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        return np.load(path)
    if path.suffix.lower() == ".csv":
        return np.loadtxt(path, delimiter=",")
    raise ValueError("Embeddings must be .npy or numeric .csv.")


def l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def compute_centroids(
    assignments: list[AssignmentRow],
    embeddings: np.ndarray,
    retained_topics: set[int],
    noise_label: int,
) -> tuple[list[int], np.ndarray]:
    if len(assignments) != len(embeddings):
        raise ValueError(
            f"Assignment rows ({len(assignments)}) and embedding rows ({len(embeddings)}) differ."
        )

    topic_to_indices: dict[int, list[int]] = defaultdict(list)
    for idx, row in enumerate(assignments):
        if row.micro_topic != noise_label and row.micro_topic in retained_topics:
            topic_to_indices[row.micro_topic].append(idx)

    topic_ids = sorted(topic_to_indices)
    centroids = []
    for topic_id in topic_ids:
        centroids.append(embeddings[topic_to_indices[topic_id]].mean(axis=0))
    if not centroids:
        raise ValueError("No retained centroids could be computed.")
    return topic_ids, l2_normalize(np.asarray(centroids))


def hierarchy_with_scipy(centroids: np.ndarray) -> np.ndarray:
    from scipy.cluster.hierarchy import linkage
    from scipy.spatial.distance import pdist

    condensed = pdist(centroids, metric="cosine")
    return linkage(condensed, method="average")


def labels_for_k(centroids: np.ndarray, k: int) -> np.ndarray:
    try:
        from scipy.cluster.hierarchy import fcluster

        z = hierarchy_with_scipy(centroids)
        return fcluster(z, t=k, criterion="maxclust") - 1
    except Exception:
        from sklearn.cluster import AgglomerativeClustering

        model = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
        return model.fit_predict(centroids)


def gap_candidates(
    centroids: np.ndarray,
    kmin: int,
    kmax: int,
    distance_threshold: float,
) -> tuple[list[dict[str, object]], int | None, int]:
    z = hierarchy_with_scipy(centroids)
    n = centroids.shape[0]
    distances = z[:, 2]

    rows = []
    best_k = None
    best_gap = None
    threshold_k = int(n - np.sum(distances <= distance_threshold))

    for k in range(kmin, kmax + 1):
        if k < 1 or k >= n:
            continue
        cut_idx = n - k - 1
        next_idx = n - k
        if cut_idx < 0 or next_idx >= len(distances):
            continue
        cut_distance = float(distances[cut_idx])
        next_merge_distance = float(distances[next_idx])
        gap = next_merge_distance - cut_distance
        if best_gap is None or gap > best_gap:
            best_gap = gap
            best_k = k
        rows.append(
            {
                "K": k,
                "cut_distance": f"{cut_distance:.10f}",
                "next_merge_distance": f"{next_merge_distance:.10f}",
                "merge_gap": f"{gap:.10f}",
                "selected_by_largest_gap": "false",
                f"selected_by_threshold_{str(distance_threshold).replace('.', '_')}": str(k == threshold_k).lower(),
            }
        )

    for row in rows:
        row["selected_by_largest_gap"] = str(row["K"] == best_k).lower()
    return rows, best_k, threshold_k


def load_macro_labels(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows = read_csv_rows(path)
    return {row["speech_id"]: row.get("macro_topic", "") for row in rows if "speech_id" in row}


def load_keyword_labels(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    section = data.get("tfidf", data if isinstance(data, dict) else {})
    labels = {}
    for macro_label, words in section.items():
        clean_words = []
        for item in words[:8]:
            if isinstance(item, list):
                clean_words.append(str(item[0]))
            else:
                clean_words.append(str(item))
        labels[str(macro_label)] = "; ".join(clean_words)
    return labels


def mapping_rows(
    topic_ids: list[int],
    labels: np.ndarray,
    assignments: list[AssignmentRow],
    retained_summary_rows: list[dict[str, object]],
    macro_assignments_path: Path,
    keywords_path: Path,
) -> list[dict[str, object]]:
    speech_to_macro = load_macro_labels(macro_assignments_path)
    keyword_lookup = load_keyword_labels(keywords_path)
    size_by_topic = {
        int(row["micro_topic_id"]): int(row["speech_count"])
        for row in retained_summary_rows
        if str(row["retained"]).lower() == "true"
    }
    cumulative_by_topic = {
        int(row["micro_topic_id"]): row["cumulative_mass"]
        for row in retained_summary_rows
        if str(row["retained"]).lower() == "true"
    }
    speech_ids_by_topic: dict[int, list[str]] = defaultdict(list)
    for row in assignments:
        if row.micro_topic in size_by_topic:
            speech_ids_by_topic[row.micro_topic].append(row.speech_id)

    macro_size = Counter()
    for topic_id, label in zip(topic_ids, labels, strict=True):
        macro_size[int(label)] += size_by_topic[topic_id]
    rows = []
    for topic_id, label in zip(topic_ids, labels, strict=True):
        speech_ids = speech_ids_by_topic[topic_id]
        existing_labels = Counter(
            speech_to_macro.get(speech_id, "")
            for speech_id in speech_ids
            if speech_to_macro.get(speech_id, "")
        )
        label_if_available = existing_labels.most_common(1)[0][0] if existing_labels else ""
        top_keywords = keyword_lookup.get(label_if_available, "")
        rows.append(
            {
                "micro_topic_id": topic_id,
                "macro_topic_id": int(label),
                "micro_topic_size": size_by_topic[topic_id],
                "macro_topic_size": macro_size[int(label)],
                "macro_label_if_available": label_if_available,
                "top_keywords_if_available": top_keywords,
                "representative_speech_id": speech_ids[0] if speech_ids else "",
                "cumulative_mass": cumulative_by_topic.get(topic_id, ""),
            }
        )
    return rows


def print_markdown_summary(summary: dict[str, object], best_k: int | None, threshold_k: int | None) -> None:
    print("# Macro-Topic Aggregation Audit")
    print()
    print("| Field | Value |")
    print("| --- | ---: |")
    for key, value in summary.items():
        if isinstance(value, float):
            rendered = f"{value:.4f}"
        else:
            rendered = str(value)
        print(f"| {key} | {rendered} |")
    print(f"| largest_gap_selected_k | {best_k if best_k is not None else 'n/a'} |")
    print(f"| threshold_selected_k | {threshold_k if threshold_k is not None else 'n/a'} |")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit macro-topic aggregation reproducibility.")
    parser.add_argument("--topic-info", type=Path, default=None, help="Optional BERTopic topic_info CSV.")
    parser.add_argument("--speech-topic-assignments", type=Path, default=DEFAULT_ASSIGNMENTS)
    parser.add_argument("--topic-column", default=None)
    parser.add_argument("--speech-embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--topic-embeddings", type=Path, default=None)
    parser.add_argument("--macro-assignments", type=Path, default=DEFAULT_MACRO_ASSIGNMENTS)
    parser.add_argument("--keywords", type=Path, default=DEFAULT_KEYWORDS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--mass-threshold", type=float, default=0.80)
    parser.add_argument("--kmin", type=int, default=20)
    parser.add_argument("--kmax", type=int, default=40)
    parser.add_argument("--distance-threshold", type=float, default=0.002)
    parser.add_argument("--noise-label", type=int, default=-1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.speech_topic_assignments.exists():
        raise SystemExit(f"Missing assignment file: {args.speech_topic_assignments}")
    if not args.speech_embeddings.exists() and not (args.topic_embeddings and args.topic_embeddings.exists()):
        raise SystemExit(
            "Missing embeddings. Provide --speech-embeddings or --topic-embeddings."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    assignments = load_assignments(args.speech_topic_assignments, args.topic_column, args.noise_label)
    retained_rows, summary, retained = retained_topic_table(
        assignments, args.mass_threshold, args.noise_label
    )
    write_csv(
        args.output_dir / "retained_micro_topics.csv",
        retained_rows,
        ["micro_topic_id", "speech_count", "cumulative_count", "cumulative_mass", "retained"],
    )

    if args.topic_embeddings and args.topic_embeddings.exists():
        raise SystemExit("Topic-level embeddings are not implemented yet; use --speech-embeddings.")

    embeddings = load_embeddings(args.speech_embeddings)
    topic_ids, centroids = compute_centroids(assignments, embeddings, retained, args.noise_label)
    gap_rows, best_k, threshold_k = gap_candidates(
        centroids, args.kmin, args.kmax, args.distance_threshold
    )
    threshold_col = f"selected_by_threshold_{str(args.distance_threshold).replace('.', '_')}"
    write_csv(
        args.output_dir / "merge_gap_candidates.csv",
        gap_rows,
        ["K", "cut_distance", "next_merge_distance", "merge_gap", "selected_by_largest_gap", threshold_col],
    )

    chosen_k = threshold_k if threshold_k >= 1 else best_k
    if chosen_k is None:
        raise SystemExit("Could not choose a macro-topic K from the hierarchy.")
    labels = labels_for_k(centroids, chosen_k)
    map_rows = mapping_rows(
        topic_ids,
        labels,
        assignments,
        retained_rows,
        args.macro_assignments,
        args.keywords,
    )
    write_csv(
        args.output_dir / "macro_topic_mapping.csv",
        map_rows,
        [
            "micro_topic_id",
            "macro_topic_id",
            "micro_topic_size",
            "macro_topic_size",
            "macro_label_if_available",
            "top_keywords_if_available",
            "representative_speech_id",
            "cumulative_mass",
        ],
    )

    print_markdown_summary(summary, best_k, threshold_k)
    if best_k != 30:
        print()
        print(f"WARNING: largest-gap rule selected K={best_k}, not K=30.")
    if threshold_k != 30:
        print()
        print(f"WARNING: distance threshold {args.distance_threshold} produced K={threshold_k}, not K=30.")


if __name__ == "__main__":
    main()
