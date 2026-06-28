"""Audit macro-topic aggregation from saved micro-topic outputs.

This script is intentionally separate from the original modeling notebook
(`src/modeling/run_macro_topic_modeling.ipynb`). It recomputes reviewer-facing
audit tables and figures from available artifacts and verifies them against the
saved final output, so the camera-ready paper can describe the 336 -> 30
reduction with reproducible numbers.

Default behaviour mirrors the executable notebook exactly:

* retain micro-topics with at least ``--min-speeches`` (50) speeches;
* build one centroid per retained micro-topic over the saved UMAP-5D
  embeddings (probability-weighted if a probability column is present, else a
  plain mean -- the partition is identical either way, see ``--verify``);
* cut an average-linkage cosine dendrogram at the fixed ``--n-macro`` (30);
* KNN-rescue the small ("niche") micro-topics into the nearest macro-topic.

The largest merge-distance gap is reported as a *diagnostic* only. The 30-topic
solution is a fixed interpretability choice; its corresponding cut distance is
~0.002, which is what the paper reports as the "distance threshold".

Reproduction command (from the repository root):

    python scripts/audit_macro_topic_aggregation.py \
        --speech-topic-assignments artifacts/final_v14/v11_cluster_assignments.csv \
        --speech-embeddings artifacts/final_v14/umap5.npy \
        --macro-assignments artifacts/final_v14/macro_topic_assignments.csv \
        --output-dir docs/macro_topic_aggregation \
        --min-speeches 50 --n-macro 30 --niche-rescue-thresh 0.25 \
        --kmin 20 --kmax 40 --distance-threshold 0.002 --figures
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
    probability: float


def rel_to_root(path: Path) -> Path:
    try:
        return path.resolve().relative_to(ROOT)
    except ValueError:
        return path


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


def find_probability_column(rows: list[dict[str, str]]) -> str | None:
    for candidate in ("hdbscan_probability", "probability", "hdbscan_prob"):
        if candidate in rows[0]:
            return candidate
    return None


def load_assignments(
    path: Path, topic_column: str | None
) -> tuple[list[AssignmentRow], bool]:
    rows = read_csv_rows(path)
    column = find_topic_column(rows, topic_column)
    prob_column = find_probability_column(rows)
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
        prob = 1.0
        if prob_column:
            raw = row.get(prob_column, "")
            try:
                prob = float(raw) if raw != "" else 0.0
            except ValueError:
                prob = 0.0
        assignments.append(AssignmentRow(row["speech_id"], micro_topic, prob))
    if not assignments:
        raise ValueError("No valid speech-topic assignments found.")
    return assignments, prob_column is not None


def retained_topic_table(
    assignments: Iterable[AssignmentRow],
    min_speeches: int,
    mass_threshold: float | None,
    noise_label: int,
) -> tuple[list[dict[str, object]], dict[str, object], set[int]]:
    """Rank micro-topics by size and flag the retained (valid) set.

    Retention follows the notebook: a micro-topic is retained when its speech
    count is at least ``min_speeches``. The cumulative-mass column is reported
    for context; if ``mass_threshold`` is given it overrides the size rule and
    retains the smallest prefix reaching that cumulative mass instead.
    """
    counts = Counter(row.micro_topic for row in assignments if row.micro_topic != noise_label)
    total_non_noise = sum(counts.values())
    if total_non_noise == 0:
        raise ValueError("No non-noise speeches found after excluding noise label.")

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    retained: set[int] = set()
    if mass_threshold is None:
        retained = {topic for topic, count in counts.items() if count >= min_speeches}

    cumulative = 0
    table = []
    reached = False
    for micro_topic, speech_count in ranked:
        cumulative += speech_count
        cumulative_mass = cumulative / total_non_noise
        if mass_threshold is not None:
            if not reached:
                retained.add(micro_topic)
            if cumulative_mass >= mass_threshold:
                reached = True
        table.append(
            {
                "micro_topic_id": micro_topic,
                "speech_count": speech_count,
                "cumulative_count": cumulative,
                "cumulative_mass": f"{cumulative_mass:.8f}",
                "retained": str(micro_topic in retained).lower(),
            }
        )

    retained_speech_count = sum(counts[topic] for topic in retained)
    summary = {
        "retention_rule": (
            f"min_speeches>={min_speeches}" if mass_threshold is None
            else f"cumulative_mass>={mass_threshold}"
        ),
        "total_micro_topics_excluding_noise": len(counts),
        "total_substantive_clustered_speeches": total_non_noise,
        "retained_micro_topic_count": len(retained),
        "retained_speech_count": retained_speech_count,
        "retained_speech_mass": retained_speech_count / total_non_noise,
        "niche_micro_topic_count": len(counts) - len(retained),
        "niche_speech_count": total_non_noise - retained_speech_count,
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


def weighted_centroid(
    embeddings: np.ndarray, indices: list[int], probs: np.ndarray, use_probs: bool
) -> np.ndarray:
    block = embeddings[indices]
    if use_probs and probs.sum() > 0:
        return np.average(block, axis=0, weights=probs)
    return block.mean(axis=0)


def compute_centroids(
    assignments: list[AssignmentRow],
    embeddings: np.ndarray,
    topics: set[int],
    use_probs: bool,
) -> tuple[list[int], np.ndarray]:
    if len(assignments) != len(embeddings):
        raise ValueError(
            f"Assignment rows ({len(assignments)}) and embedding rows ({len(embeddings)}) differ."
        )
    topic_to_indices: dict[int, list[int]] = defaultdict(list)
    for idx, row in enumerate(assignments):
        if row.micro_topic in topics:
            topic_to_indices[row.micro_topic].append(idx)

    topic_ids = sorted(topic_to_indices)
    centroids = []
    for topic_id in topic_ids:
        indices = topic_to_indices[topic_id]
        probs = np.array([assignments[i].probability for i in indices])
        centroids.append(weighted_centroid(embeddings, indices, probs, use_probs))
    if not centroids:
        raise ValueError("No centroids could be computed for the requested topic set.")
    return topic_ids, np.asarray(centroids)


def hierarchy_with_scipy(centroids: np.ndarray) -> np.ndarray:
    from scipy.cluster.hierarchy import linkage
    from scipy.spatial.distance import pdist

    condensed = pdist(l2_normalize(centroids), metric="cosine")
    return linkage(condensed, method="average")


def gap_candidates(
    z: np.ndarray,
    n: int,
    kmin: int,
    kmax: int,
    n_macro: int,
    distance_threshold: float,
) -> tuple[list[dict[str, object]], int | None, int, float]:
    distances = z[:, 2]
    rows = []
    best_k = None
    best_gap = None
    threshold_k = int(n - np.sum(distances <= distance_threshold))

    # cut distance that yields exactly n_macro clusters
    cut_distance_n_macro = float(distances[n - n_macro - 1]) if 1 <= n_macro < n else float("nan")

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
                "is_paper_n_macro": str(k == n_macro).lower(),
                f"selected_by_threshold_{str(distance_threshold).replace('.', '_')}": str(
                    k == threshold_k
                ).lower(),
            }
        )
    for row in rows:
        row["selected_by_largest_gap"] = str(row["K"] == best_k).lower()
    return rows, best_k, threshold_k, cut_distance_n_macro


def labels_for_k(centroids: np.ndarray, k: int) -> np.ndarray:
    from sklearn.cluster import AgglomerativeClustering

    model = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
    return model.fit_predict(centroids)


def knn_rescue(
    niche_ids: list[int],
    niche_centroids: np.ndarray,
    macro_centroids: np.ndarray,
    threshold: float,
) -> tuple[dict[int, int], int, int]:
    from sklearn.metrics.pairwise import cosine_distances

    rescue_map: dict[int, int] = {}
    rescued = 0
    left = 0
    if len(niche_centroids) == 0:
        return rescue_map, rescued, left
    dist = cosine_distances(niche_centroids, macro_centroids)
    for i, micro_id in enumerate(niche_ids):
        nearest = int(dist[i].argmin())
        if dist[i, nearest] <= threshold:
            rescue_map[micro_id] = nearest
            rescued += 1
        else:
            rescue_map[micro_id] = -1  # stays niche
            left += 1
    return rescue_map, rescued, left


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


def verify_against_saved(
    topic_ids: list[int],
    labels: np.ndarray,
    assignments: list[AssignmentRow],
    macro_assignments_path: Path,
) -> dict[str, object] | None:
    """Compare the reproduced macro partition with the saved final output.

    Maps each retained micro-topic to its majority saved macro label and
    computes the adjusted Rand index between the reproduced and saved
    partitions over the retained micro-topics.
    """
    speech_to_macro = load_macro_labels(macro_assignments_path)
    if not speech_to_macro:
        return None
    from sklearn.metrics import adjusted_rand_score

    speeches_by_topic: dict[int, list[str]] = defaultdict(list)
    for row in assignments:
        speeches_by_topic[row.micro_topic].append(row.speech_id)

    saved_label = []
    for topic_id in topic_ids:
        counter = Counter(
            speech_to_macro.get(sid, "")
            for sid in speeches_by_topic[topic_id]
            if speech_to_macro.get(sid, "")
        )
        saved_label.append(counter.most_common(1)[0][0] if counter else "")

    saved_codes = {lab: i for i, lab in enumerate(sorted(set(saved_label)))}
    saved_arr = np.array([saved_codes[lab] for lab in saved_label])
    ari = adjusted_rand_score(saved_arr, labels)
    return {
        "saved_macro_topic_count": len([lab for lab in set(saved_label) if lab.startswith("Macro")]),
        "adjusted_rand_index_vs_saved": round(float(ari), 6),
        "exact_match": ari == 1.0,
    }


def mapping_rows(
    topic_ids: list[int],
    labels: np.ndarray,
    assignments: list[AssignmentRow],
    retained_rows: list[dict[str, object]],
    macro_assignments_path: Path,
    keywords_path: Path,
) -> list[dict[str, object]]:
    speech_to_macro = load_macro_labels(macro_assignments_path)
    keyword_lookup = load_keyword_labels(keywords_path)
    size_by_topic = {int(r["micro_topic_id"]): int(r["speech_count"]) for r in retained_rows}
    cumulative_by_topic = {int(r["micro_topic_id"]): r["cumulative_mass"] for r in retained_rows}
    speeches_by_topic: dict[int, list[str]] = defaultdict(list)
    for row in assignments:
        speeches_by_topic[row.micro_topic].append(row.speech_id)

    macro_size = Counter()
    for topic_id, label in zip(topic_ids, labels, strict=True):
        macro_size[int(label)] += size_by_topic[topic_id]

    rows = []
    for topic_id, label in zip(topic_ids, labels, strict=True):
        speech_ids = speeches_by_topic[topic_id]
        existing = Counter(
            speech_to_macro.get(sid, "") for sid in speech_ids if speech_to_macro.get(sid, "")
        )
        label_if_available = existing.most_common(1)[0][0] if existing else ""
        rows.append(
            {
                "micro_topic_id": topic_id,
                "macro_topic_id": int(label),
                "micro_topic_size": size_by_topic[topic_id],
                "macro_topic_size": macro_size[int(label)],
                "macro_label_if_available": label_if_available,
                "top_keywords_if_available": keyword_lookup.get(label_if_available, ""),
                "representative_speech_id": speech_ids[0] if speech_ids else "",
                "cumulative_mass": cumulative_by_topic.get(topic_id, ""),
            }
        )
    return rows


def write_parameters_yaml(path: Path, params: dict[str, object]) -> None:
    """Write a small, dependency-free YAML for the audit parameters."""
    def emit(value: object, indent: int) -> list[str]:
        pad = "  " * indent
        lines = []
        if isinstance(value, dict):
            for key, sub in value.items():
                if isinstance(sub, dict):
                    lines.append(f"{pad}{key}:")
                    lines.extend(emit(sub, indent + 1))
                else:
                    lines.append(f"{pad}{key}: {format_scalar(sub)}")
        return lines

    def format_scalar(value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return value
        return str(value)

    path.write_text("\n".join(emit(params, 0)) + "\n", encoding="utf-8")


def make_figures(
    z: np.ndarray,
    gap_rows: list[dict[str, object]],
    n_macro: int,
    cut_distance: float,
    distance_threshold: float,
    output_dir: Path,
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.cluster.hierarchy import dendrogram

    written: list[Path] = []

    # Figure 1: dendrogram of retained centroids with the K=n_macro cut line.
    # Top panel: full tree. Bottom panel: zoomed to the cut region so the
    # K=n_macro split is legible (most merges happen at small cosine distances).
    fig, (ax_full, ax_zoom) = plt.subplots(2, 1, figsize=(8.0, 7.0), dpi=150)
    for ax, zoom in ((ax_full, False), (ax_zoom, True)):
        dendrogram(z, no_labels=True, color_threshold=cut_distance, ax=ax)
        ax.axhline(
            cut_distance,
            color="#C1121F",
            linestyle="--",
            linewidth=1.2,
            label=f"cut for K={n_macro} (d={cut_distance:.4f})",
        )
        ax.set_ylabel("Cosine merge distance", fontsize=9)
        if zoom:
            zoom_top = float(z[-n_macro - 2, 2]) * 1.15 if len(z) > n_macro + 2 else cut_distance * 3
            ax.set_ylim(0, max(zoom_top, cut_distance * 2.5))
            ax.set_xlabel("Retained micro-topics", fontsize=9)
            ax.set_title(f"Zoom to cut region: d={cut_distance:.4f} produces K={n_macro}", fontsize=9)
        else:
            ax.set_title(
                "Average-linkage cosine dendrogram of retained micro-topic centroids",
                fontsize=10,
            )
            ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    path1 = output_dir / "dendrogram_with_cut.png"
    fig.savefig(path1, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    written.append(path1)

    # Figure 2: cut distance and merge-gap vs K, marking the paper K.
    ks = [int(r["K"]) for r in gap_rows]
    cut = [float(r["cut_distance"]) for r in gap_rows]
    gap = [float(r["merge_gap"]) for r in gap_rows]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.0, 6.0), dpi=150, sharex=True)
    ax1.plot(ks, cut, marker="o", markersize=3, color="#264653")
    ax1.axhline(distance_threshold, color="#C1121F", linestyle="--", linewidth=1.0,
                label=f"distance threshold {distance_threshold}")
    if n_macro in ks:
        ax1.axvline(n_macro, color="#2A9D8F", linestyle=":", linewidth=1.0,
                    label=f"paper K={n_macro}")
    ax1.set_ylabel("Cut distance", fontsize=9)
    ax1.set_title("Cut distance and adjacent merge-gap across candidate K", fontsize=10)
    ax1.legend(fontsize=8)
    ax2.bar(ks, gap, color="#457B9D", width=0.7)
    if n_macro in ks:
        ax2.axvline(n_macro, color="#2A9D8F", linestyle=":", linewidth=1.0)
    ax2.set_xlabel("Number of macro-topics K", fontsize=9)
    ax2.set_ylabel("Adjacent merge-gap", fontsize=9)
    fig.tight_layout()
    path2 = output_dir / "merge_gap_vs_k.png"
    fig.savefig(path2, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    written.append(path2)
    return written


def print_markdown_summary(
    summary: dict[str, object],
    best_k: int | None,
    threshold_k: int | None,
    cut_distance: float,
    verification: dict[str, object] | None,
) -> None:
    print("# Macro-Topic Aggregation Audit")
    print()
    print("| Field | Value |")
    print("| --- | ---: |")
    for key, value in summary.items():
        rendered = f"{value:.4f}" if isinstance(value, float) else str(value)
        print(f"| {key} | {rendered} |")
    print(f"| largest_gap_selected_k (diagnostic) | {best_k if best_k is not None else 'n/a'} |")
    print(f"| threshold_selected_k | {threshold_k if threshold_k is not None else 'n/a'} |")
    print(f"| cut_distance_for_paper_k | {cut_distance:.6f} |")
    if verification:
        for key, value in verification.items():
            print(f"| {key} | {value} |")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit macro-topic aggregation reproducibility.")
    parser.add_argument("--speech-topic-assignments", type=Path, default=DEFAULT_ASSIGNMENTS)
    parser.add_argument("--topic-column", default=None)
    parser.add_argument("--speech-embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--macro-assignments", type=Path, default=DEFAULT_MACRO_ASSIGNMENTS)
    parser.add_argument("--keywords", type=Path, default=DEFAULT_KEYWORDS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--min-speeches", type=int, default=50,
                        help="Notebook retention rule: keep micro-topics with >= this many speeches.")
    parser.add_argument("--mass-threshold", type=float, default=None,
                        help="Optional alternative: retain smallest prefix reaching this cumulative mass.")
    parser.add_argument("--n-macro", type=int, default=30, help="Fixed macro-topic count (paper value).")
    parser.add_argument("--niche-rescue-thresh", type=float, default=0.25)
    parser.add_argument("--kmin", type=int, default=20)
    parser.add_argument("--kmax", type=int, default=40)
    parser.add_argument("--distance-threshold", type=float, default=0.002)
    parser.add_argument("--noise-label", type=int, default=-1)
    parser.add_argument("--figures", action="store_true", help="Also render dendrogram and gap figures.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.speech_topic_assignments.exists():
        raise SystemExit(f"Missing assignment file: {args.speech_topic_assignments}")
    if not args.speech_embeddings.exists():
        raise SystemExit(f"Missing embeddings file: {args.speech_embeddings}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    assignments, has_probs = load_assignments(args.speech_topic_assignments, args.topic_column)
    non_noise = [r for r in assignments if r.micro_topic != args.noise_label]

    retained_rows_all, summary, retained = retained_topic_table(
        assignments, args.min_speeches, args.mass_threshold, args.noise_label
    )
    write_csv(
        args.output_dir / "retained_micro_topics.csv",
        retained_rows_all,
        ["micro_topic_id", "speech_count", "cumulative_count", "cumulative_mass", "retained"],
    )
    retained_rows = [r for r in retained_rows_all if str(r["retained"]).lower() == "true"]
    niche_ids = sorted(
        {r.micro_topic for r in non_noise} - retained - {args.noise_label}
    )

    embeddings = load_embeddings(args.speech_embeddings)
    use_probs = has_probs
    topic_ids, centroids = compute_centroids(assignments, embeddings, retained, use_probs)

    z = hierarchy_with_scipy(centroids)
    n = centroids.shape[0]
    gap_rows, best_k, threshold_k, cut_distance = gap_candidates(
        z, n, args.kmin, args.kmax, args.n_macro, args.distance_threshold
    )
    threshold_col = f"selected_by_threshold_{str(args.distance_threshold).replace('.', '_')}"
    write_csv(
        args.output_dir / "merge_gap_candidates.csv",
        gap_rows,
        ["K", "cut_distance", "next_merge_distance", "merge_gap",
         "selected_by_largest_gap", "is_paper_n_macro", threshold_col],
    )

    # Reproduce the fixed-K macro partition and map niche topics by KNN rescue.
    labels = labels_for_k(l2_normalize(centroids), args.n_macro)
    verification = verify_against_saved(topic_ids, labels, assignments, args.macro_assignments)

    macro_centroids = np.array(
        [l2_normalize(centroids)[labels == m].mean(axis=0) for m in range(args.n_macro)]
    )
    rescued_count = left_count = 0
    if niche_ids:
        _, niche_centroids = compute_centroids(assignments, embeddings, set(niche_ids), use_probs)
        _, rescued_count, left_count = knn_rescue(
            niche_ids, l2_normalize(niche_centroids), macro_centroids, args.niche_rescue_thresh
        )

    map_rows = mapping_rows(
        topic_ids, labels, assignments, retained_rows, args.macro_assignments, args.keywords
    )
    write_csv(
        args.output_dir / "macro_topic_mapping.csv",
        map_rows,
        ["micro_topic_id", "macro_topic_id", "micro_topic_size", "macro_topic_size",
         "macro_label_if_available", "top_keywords_if_available",
         "representative_speech_id", "cumulative_mass"],
    )

    params = {
        "macro_topic_aggregation": {
            "total_micro_topics_excluding_noise": summary["total_micro_topics_excluding_noise"],
            "noise_topic_label": args.noise_label,
            "total_substantive_clustered_speeches": summary["total_substantive_clustered_speeches"],
        },
        "retention": {
            "rule": summary["retention_rule"],
            "min_speeches": args.min_speeches,
            "retained_micro_topic_count": summary["retained_micro_topic_count"],
            "retained_speech_count": summary["retained_speech_count"],
            "retained_speech_mass": round(float(summary["retained_speech_mass"]), 6),
            "niche_micro_topic_count": summary["niche_micro_topic_count"],
            "niche_speech_count": summary["niche_speech_count"],
        },
        "centroids": {
            "source": str(rel_to_root(args.speech_embeddings)),
            "method": "probability_weighted" if use_probs else "mean (probabilities not in artifact)",
            "normalization": "L2",
        },
        "hierarchical_clustering": {
            "distance_metric": "cosine",
            "linkage": "average",
            "n_macro": args.n_macro,
            "cut_distance_for_n_macro": round(float(cut_distance), 6),
            "kmin": args.kmin,
            "kmax": args.kmax,
            "largest_gap_selected_k_diagnostic": best_k,
            "distance_threshold": args.distance_threshold,
            "k_at_distance_threshold": threshold_k,
        },
        "niche_rescue": {
            "threshold": args.niche_rescue_thresh,
            "rescued": rescued_count,
            "left_as_niche": left_count,
        },
        "validation": {
            "adjusted_rand_index_vs_saved": (
                verification["adjusted_rand_index_vs_saved"] if verification else "n/a"
            ),
            "reproduces_saved_partition": (
                bool(verification["exact_match"]) if verification else "n/a"
            ),
            "k_at_threshold_equals_n_macro": threshold_k == args.n_macro,
        },
    }
    write_parameters_yaml(args.output_dir / "parameters.yaml", params)

    figs: list[Path] = []
    if args.figures:
        figs = make_figures(
            z, gap_rows, args.n_macro, cut_distance, args.distance_threshold, args.output_dir
        )

    summary["niche_rescued"] = rescued_count
    summary["niche_left"] = left_count
    print_markdown_summary(summary, best_k, threshold_k, cut_distance, verification)
    if threshold_k == args.n_macro:
        print(f"\nOK: distance threshold {args.distance_threshold} reproduces K={args.n_macro}.")
    else:
        print(f"\nNOTE: distance threshold {args.distance_threshold} gives K={threshold_k}, "
              f"not {args.n_macro}.")
    if best_k != args.n_macro:
        print(f"NOTE: largest-gap diagnostic selects K={best_k}; the paper uses a fixed "
              f"K={args.n_macro} (its cut distance is {cut_distance:.6f}).")
    if figs:
        print("Figures written:")
        for fig in figs:
            print(f"  - {rel_to_root(fig)}")


if __name__ == "__main__":
    main()
