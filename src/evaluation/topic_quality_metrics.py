"""Topic quality metrics used for reviewer-facing evaluation tables."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import pandas as pd


TOKEN_PATTERN = re.compile(r"(?u)[a-zA-Z\u0D80-\u0DFF\u0B80-\u0BFF\u200D\u200C]{2,}")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(str(text).lower())


def load_keyword_topics(path: str | Path, section: str = "tfidf", top_n: int = 20) -> dict[str, list[str]]:
    """Load keyword JSONs shaped like {'count': {...}, 'tfidf': {...}} or {topic: words}."""
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if section in data and isinstance(data[section], dict):
        data = data[section]

    topics: dict[str, list[str]] = {}
    for topic_id, words in data.items():
        if isinstance(words, dict):
            words = list(words)
        cleaned = []
        for item in words:
            if isinstance(item, (list, tuple)):
                word = str(item[0])
            else:
                word = str(item)
            if word:
                cleaned.append(word)
        topics[str(topic_id)] = cleaned[:top_n]
    return topics


def topic_diversity(keyword_topics: dict[str, list[str]], top_n: int = 20) -> float:
    """Unique top words divided by total top words."""
    words = [word for topic_words in keyword_topics.values() for word in topic_words[:top_n]]
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def topic_mass(labels: Iterable[object], noise_label: str = "-1") -> dict[str, object]:
    """Return coverage/noise and per-topic mass statistics."""
    values = [str(label) for label in labels]
    counts = Counter(values)
    total = len(values)
    noise = counts.get(noise_label, 0)
    clustered = total - noise
    cluster_sizes = [count for label, count in counts.items() if label != noise_label]
    return {
        "n_items": total,
        "n_topics": len(cluster_sizes),
        "clustered_count": clustered,
        "noise_count": noise,
        "clustered_pct": clustered / total if total else 0.0,
        "noise_pct": noise / total if total else 0.0,
        "min_topic_size": min(cluster_sizes) if cluster_sizes else 0,
        "median_topic_size": float(pd.Series(cluster_sizes).median()) if cluster_sizes else 0.0,
        "max_topic_size": max(cluster_sizes) if cluster_sizes else 0,
    }


def cv_coherence(
    texts: Iterable[str],
    keyword_topics: dict[str, list[str]],
    top_n: int = 20,
    window_size: int = 20,
) -> float:
    """Approximate C_V coherence with sliding-window NPMI.

    This is intentionally dependency-light and deterministic. If exact Gensim
    `CoherenceModel(coherence='c_v')` is required for a paper run, use the same
    inputs with Gensim; this function provides a portable repo-level evaluator.
    """
    tokenized_docs = [tokenize(text) for text in texts]
    word_windows: Counter[str] = Counter()
    pair_windows: Counter[tuple[str, str]] = Counter()
    total_windows = 0

    vocabulary = {
        word
        for topic_words in keyword_topics.values()
        for word in topic_words[:top_n]
    }
    if not vocabulary:
        return 0.0

    for doc in tokenized_docs:
        if not doc:
            continue
        if len(doc) <= window_size:
            windows = [doc]
        else:
            windows = [doc[i : i + window_size] for i in range(0, len(doc) - window_size + 1)]
        for window in windows:
            present = sorted(set(window) & vocabulary)
            if not present:
                continue
            total_windows += 1
            for word in present:
                word_windows[word] += 1
            for i, left in enumerate(present):
                for right in present[i + 1 :]:
                    pair_windows[(left, right)] += 1

    if total_windows == 0:
        return 0.0

    topic_scores = []
    for topic_words in keyword_topics.values():
        words = [word for word in topic_words[:top_n] if word in word_windows]
        if len(words) < 2:
            continue
        pair_scores = []
        for i, left in enumerate(words):
            for right in words[i + 1 :]:
                pair_count = pair_windows.get(tuple(sorted((left, right))), 0)
                if pair_count == 0:
                    pair_scores.append(-1.0)
                    continue
                p_left = word_windows[left] / total_windows
                p_right = word_windows[right] / total_windows
                p_pair = pair_count / total_windows
                pmi = math.log(p_pair / (p_left * p_right))
                npmi = pmi / (-math.log(p_pair))
                pair_scores.append(npmi)
        if pair_scores:
            topic_scores.append(sum(pair_scores) / len(pair_scores))

    if not topic_scores:
        return 0.0
    return float(sum(topic_scores) / len(topic_scores))


def topic_quality_summary(
    texts: Iterable[str],
    labels: Iterable[object],
    keyword_topics: dict[str, list[str]],
    top_n: int = 20,
    noise_label: str = "-1",
) -> dict[str, float | int]:
    mass = topic_mass(labels, noise_label=noise_label)
    return {
        **mass,
        "topic_diversity": topic_diversity(keyword_topics, top_n=top_n),
        "cv_coherence": cv_coherence(texts, keyword_topics, top_n=top_n),
    }
