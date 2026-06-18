"""Portable clustering/classification metrics for topic-model evaluation."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

import numpy as np

try:
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
except ImportError:  # pragma: no cover - reported at runtime by run_evaluation.py
    adjusted_rand_score = None
    normalized_mutual_info_score = None


@dataclass(frozen=True)
class ClassificationMetrics:
    n_items: int
    n_true_labels: int
    n_pred_labels: int
    purity: float
    bcubed_precision: float
    bcubed_recall: float
    bcubed_f1: float
    ari: float | None
    nmi: float | None


def _as_list(values: Iterable[object]) -> list[str]:
    return [str(value) for value in values]


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def purity_score(true_labels: Iterable[object], pred_labels: Iterable[object]) -> float:
    """Return mass-weighted cluster purity."""
    true = _as_list(true_labels)
    pred = _as_list(pred_labels)
    if len(true) != len(pred):
        raise ValueError("true_labels and pred_labels must have the same length")
    if not true:
        return 0.0

    clusters: dict[str, Counter[str]] = defaultdict(Counter)
    for true_label, pred_label in zip(true, pred, strict=True):
        clusters[pred_label][true_label] += 1

    correct = sum(max(counts.values()) for counts in clusters.values() if counts)
    return correct / len(true)


def bcubed_scores(true_labels: Iterable[object], pred_labels: Iterable[object]) -> tuple[float, float, float]:
    """Return B-Cubed precision, recall, and F1.

    For each item, precision is the share of its predicted cluster with the
    same gold label; recall is the share of its gold class captured by its
    predicted cluster. The corpus score is the item-level mean.
    """
    true = _as_list(true_labels)
    pred = _as_list(pred_labels)
    if len(true) != len(pred):
        raise ValueError("true_labels and pred_labels must have the same length")
    if not true:
        return 0.0, 0.0, 0.0

    pred_counts = Counter(pred)
    true_counts = Counter(true)
    pair_counts = Counter(zip(true, pred, strict=True))

    precisions = []
    recalls = []
    for true_label, pred_label in zip(true, pred, strict=True):
        overlap = pair_counts[(true_label, pred_label)]
        precisions.append(overlap / pred_counts[pred_label])
        recalls.append(overlap / true_counts[true_label])

    precision = float(np.mean(precisions))
    recall = float(np.mean(recalls))
    return precision, recall, _f1(precision, recall)


def evaluate_classification(true_labels: Iterable[object], pred_labels: Iterable[object]) -> ClassificationMetrics:
    """Compute all reviewer-facing external validity metrics."""
    true = _as_list(true_labels)
    pred = _as_list(pred_labels)
    if len(true) != len(pred):
        raise ValueError("true_labels and pred_labels must have the same length")

    precision, recall, f1 = bcubed_scores(true, pred)
    ari = adjusted_rand_score(true, pred) if adjusted_rand_score is not None and true else None
    nmi = normalized_mutual_info_score(true, pred) if normalized_mutual_info_score is not None and true else None

    return ClassificationMetrics(
        n_items=len(true),
        n_true_labels=len(set(true)),
        n_pred_labels=len(set(pred)),
        purity=purity_score(true, pred),
        bcubed_precision=precision,
        bcubed_recall=recall,
        bcubed_f1=f1,
        ari=None if ari is None else float(ari),
        nmi=None if nmi is None else float(nmi),
    )
