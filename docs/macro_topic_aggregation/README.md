# Macro-Topic Aggregation Audit

## Purpose

This folder documents and audits how the final topic-modeling workflow reduced 336 HDBSCAN/BERTopic-style micro-topics to 30 macro-topics for reviewer-facing reproducibility.

Reviewers asked for the macro-topic aggregation procedure to be specified algorithmically, including:

- how many micro-topics were retained before macro-clustering;
- what retention threshold was used (and whether it was a speech-mass or size rule);
- how the merge-distance gap relates to the chosen cut;
- whether the 30-topic solution follows from a data-driven rule rather than an arbitrary fixed choice.

These questions are answered in **How 336 Became 30** and **Resolved Questions**
below.

## Resolved: How 336 Became 30

The audit is complete and reproducible. The executable final v14 notebook
(`src/modeling/run_macro_topic_modeling.ipynb`, cell *"MACRO-TOPIC AGGREGATION
v2"*) reduces 336 micro-topics to 30 macro-topics in two deterministic stages:

1. **Size-based retention.** Keep micro-topics with `MIN_SPEECHES = 50` or more
   speeches. This retains **62** of the 336 micro-topics (6,655 of the 12,632
   substantive speeches, ≈ 52.7% of substantive mass). The remaining **274**
   small ("niche") micro-topics are not clustered directly.
2. **Fixed-K agglomerative clustering.** Compute a probability-weighted centroid
   over `emb5` (UMAP-5D) for each retained micro-topic, L2-normalize, and run
   `AgglomerativeClustering(n_clusters=30, metric='cosine', linkage='average')`.
   `N_MACRO = 30` is a **fixed interpretability choice**, not a data-driven gap
   result.
3. **KNN rescue.** Each of the 274 niche micro-topics is absorbed into the
   nearest macro-topic centroid within `NICHE_RESCUE_THRESH = 0.25` cosine
   distance. All 274 are rescued, so every substantive speech maps to one of the
   30 macro-topics (no standalone niche bucket remains).

What this means for the two numbers the paper reports:

- **Distance threshold ≈ 0.002 is real and reproducible.** Cutting the
  average-linkage cosine dendrogram of the 62 retained centroids at
  `d = 0.00187` produces exactly 30 macro-topics; equivalently, cutting at
  `d = 0.002` yields `K = 30`. The 0.002 figure is the *resulting* cut distance
  of the fixed-30 solution, not a threshold chosen first to recover 30.
- **The largest merge-distance gap does NOT select 30.** Within `[20, 40]` the
  largest gap falls at `K = 24`. The notebook contains a commented-out
  gap-search block (`MIN_K, MAX_K = 29, 50`) that was explored but **not** used
  in the final pipeline. The camera-ready text must therefore describe 30 as a
  fixed choice with cut distance ≈ 0.002, **not** as a gap-selected value.

The reproduction is exact: rebuilding the partition from the public artifacts
matches the committed `macro_topic_assignments.csv` with **adjusted Rand index
1.000** (see `scripts/audit_macro_topic_aggregation.py` and
`macro_topic_aggregation_audit.ipynb`). HDBSCAN probabilities are not stored in
the public artifact, so the audit uses plain mean centroids; the ARI of 1.000
confirms the probability weighting does not change the macro grouping.

## Reproducible Audit Command

Run this from the repository root. Defaults already match the paper, so the bare
command reproduces every table, figure, and the ARI check:

```bash
python scripts/audit_macro_topic_aggregation.py --figures
```

Explicit form (cross-platform):

```bash
python scripts/audit_macro_topic_aggregation.py \
    --speech-topic-assignments artifacts/final_v14/v11_cluster_assignments.csv \
    --speech-embeddings artifacts/final_v14/umap5.npy \
    --macro-assignments artifacts/final_v14/macro_topic_assignments.csv \
    --output-dir docs/macro_topic_aggregation \
    --min-speeches 50 --n-macro 30 --niche-rescue-thresh 0.25 \
    --kmin 20 --kmax 40 --distance-threshold 0.002 --figures
```

The retention rule is `--min-speeches 50` (the notebook's rule). A
`--mass-threshold` flag is still available for an alternative Pareto-style view,
but it is **not** the method used in the paper. The notebook
`macro_topic_aggregation_audit.ipynb` performs the same reproduction
step-by-step for reviewers.

## Current Known Values (verified)

| Field | Value |
| --- | --- |
| Total micro-topics (excl. noise) | 336 |
| Noise topic label | -1 |
| Noise speeches | 6,921 |
| Substantive clustered speeches | 12,632 |
| Retention rule | speech count ≥ 50 |
| Retained ("valid") micro-topics | 62 |
| Retained speeches | 6,655 (52.7% of substantive mass) |
| Niche micro-topics (< 50 speeches) | 274 |
| Niche speeches | 5,977 |
| Macro-topic count `N_MACRO` | 30 (fixed) |
| Centroids | probability-weighted over `emb5`; audit uses mean (ARI 1.000) |
| Linkage / metric | average / cosine |
| Cut distance producing K = 30 | 0.00187 |
| K at distance threshold 0.002 | **30** ✓ |
| Largest-gap rule result for K in [20, 40] | K = 24 (diagnostic only) |
| KNN niche rescue threshold | 0.25 cosine |
| Niche micro-topics rescued | 274 of 274 (0 left as niche) |
| Reproduced partition vs committed output | **ARI = 1.000** (exact match) |

The audit **verifies** that cutting at the paper's distance threshold 0.002
yields exactly 30 macro-topics and that the reproduced partition is identical to
the committed `macro_topic_assignments.csv`. It also documents the honest caveat
that the largest merge-distance gap rule alone would select K = 24, so 30 is
reported as a fixed interpretability choice with a resulting cut distance of
≈ 0.002.

## Macro-Topic Aggregation Algorithm

Input:

- micro-topic assignments for all speeches (`hdbscan_cluster`);
- speech embeddings (`emb5`, UMAP-5D) and, when available, HDBSCAN membership
  probabilities;
- the size cutoff `MIN_SPEECHES` and the fixed macro count `N_MACRO`;
- the niche rescue cosine threshold `NICHE_RESCUE_THRESH`.

Algorithm (as implemented in the final notebook):

1. Remove the noise topic labelled `-1`.
2. Count the speeches assigned to each remaining micro-topic.
3. **Retain** micro-topics with at least `MIN_SPEECHES` (= 50) speeches; the
   rest are "niche".
4. For each retained micro-topic, compute a probability-weighted centroid of its
   speech embeddings (falling back to the mean when probabilities are absent or
   sum to zero).
5. L2-normalize the retained centroids.
6. Apply average-linkage agglomerative clustering with cosine distance and cut
   at a **fixed** `N_MACRO` (= 30) clusters.
7. For each niche micro-topic, compute its centroid and assign it to the nearest
   macro-topic centroid if within `NICHE_RESCUE_THRESH` cosine distance;
   otherwise leave it as a standalone niche bucket.
8. Assign macro-topic labels post hoc using top keywords and representative
   speeches (labels are not used during clustering).

Reviewer diagnostics (steps 9–11 below are reported but do **not** drive the
final K): compute the merge-distance sequence, the adjacent merge-gap for each
candidate K in `[Kmin, Kmax]`, the largest-gap K, and the K implied by the
distance threshold 0.002.

## Generated Tables and Figures

The audit script (`--figures`) writes, into this folder:

- `retained_micro_topics.csv`: per micro-topic speech count, cumulative mass, and
  retained flag (62 of 336 retained).
- `merge_gap_candidates.csv`: candidate K, cut distance, next merge distance,
  adjacent gap, largest-gap flag, paper-`N_MACRO` flag, and threshold flag.
- `macro_topic_mapping.csv`: the 62 retained micro-topics mapped to their
  macro-topic, with macro size, the committed macro label, top keywords, and a
  representative speech id.
- `macro_topics_summary.csv`: the 30 macro-topics with speech counts and top
  TF-IDF keywords — a camera-ready table.
- `macro_topic_mapping_template.csv`: a 30-row curation sheet with an empty
  `curated_human_label` column for human-readable topic names.
- `dendrogram_with_cut.png`: average-linkage cosine dendrogram of the 62 retained
  centroids with the K = 30 cut line (full tree + zoom to the cut region).
- `merge_gap_vs_k.png`: cut distance and adjacent merge-gap across candidate K,
  marking the 0.002 threshold and the paper's K = 30.
- `parameters.yaml`: machine-readable, fully populated audit parameters.
