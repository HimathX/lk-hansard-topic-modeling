# Macro-Topic Aggregation Audit

## Purpose

This folder documents and audits how the final topic-modeling workflow reduced 336 HDBSCAN/BERTopic-style micro-topics to 30 macro-topics for reviewer-facing reproducibility.

Reviewers asked for the macro-topic aggregation procedure to be specified algorithmically, including:

- how many micro-topics were retained before macro-clustering;
- what cumulative speech-mass threshold X% was used;
- how the merge-distance gap was selected;
- whether the 30-topic solution follows from a data-driven rule rather than an arbitrary fixed choice.

## Existing Code Found

Original macro-topic aggregation code was found in `src/modeling/run_macro_topic_modeling.ipynb`.

Important finding: the executable final v14 notebook code uses:

- `MIN_SPEECHES = 50` to split valid versus niche micro-topics;
- `N_MACRO = 30` as a fixed final macro-topic count;
- probability-weighted centroids over `emb5`;
- `AgglomerativeClustering(metric='cosine', linkage='average')`;
- KNN rescue for niche micro-topics using `NICHE_RESCUE_THRESH = 0.25`.

The notebook also contains an earlier commented block for a data-driven merge-gap search using scipy linkage over centroid cosine distances, but that block is commented out. Therefore, this audit does not claim that the final notebook itself proves the largest-gap rule unless the audit script verifies it from saved artifacts.

## Reproducible Audit Command

Run this from the repository root:

```powershell
python scripts\audit_macro_topic_aggregation.py --speech-topic-assignments artifacts\final_v14\v11_cluster_assignments.csv --speech-embeddings artifacts\final_v14\umap5.npy --output-dir docs\macro_topic_aggregation --mass-threshold 0.80 --kmin 20 --kmax 40 --distance-threshold 0.002
```

This command recomputes reviewer-facing audit tables using saved HDBSCAN assignments and saved UMAP-5D embeddings. The default `--mass-threshold 0.80` is an audit parameter, not a verified value from the original paper, unless the authors confirm it.

## Current Known Values

| Field | Value |
| --- | --- |
| Total micro-topics reported in paper | 336 |
| Noise topic label | -1 |
| Noise speeches reported in paper | 6,921 |
| Substantive clustered speeches reported in paper | 12,632 |
| Paper-reported macro-topic count | 30 |
| Paper-reported distance threshold | 0.002 |
| Original executable notebook code found | yes |
| Original final code uses fixed `N_MACRO = 30` | yes |
| Original final code stores exact Pareto X% | TODO: not found |
| Audit mass threshold used for generated CSVs | 0.80 |
| Retained micro-topic count at audit threshold | 167 |
| Retained speech count at audit threshold | 10,107 |
| Retained cumulative speech mass at audit threshold | 0.8001 |
| Largest-gap rule result for K in [20, 40] | K = 22 |
| Distance threshold 0.002 result | K = 46 |
| Largest-gap rule verified to reproduce 30 | false for this audit run |
| Threshold 0.002 verified to reproduce 30 | false for this audit run |

Important: the generated audit run does **not** verify the manuscript claim that the largest merge-distance gap or threshold 0.002 yields Kmacro = 30. This may be because the saved artifact is UMAP-5D rather than the original centroid space, because the final notebook used a fixed `N_MACRO = 30` path, or because the paper text describes an earlier/commented method. The camera-ready text should not claim data-driven recovery of 30 until the exact artifact path and parameters are confirmed.

## Macro-Topic Aggregation Algorithm

Input:

- micro-topic assignments for all speeches;
- speech embeddings or topic centroids;
- micro-topic speech counts;
- cumulative mass threshold X;
- candidate macro-topic range `[Kmin, Kmax]`.

Algorithm:

1. Remove the noise topic labelled `-1`.
2. Count the number of speeches assigned to each remaining micro-topic.
3. Rank micro-topics in descending order by speech count.
4. Compute cumulative speech mass over this ranked list.
5. Retain the smallest prefix of ranked micro-topics whose cumulative speech mass is at least X.
6. Compute one centroid for each retained micro-topic by averaging embeddings of speeches assigned to that micro-topic.
7. L2-normalize the retained micro-topic centroids.
8. Apply average-linkage hierarchical clustering using cosine distance.
9. Compute the merge-distance sequence from the hierarchy.
10. For each candidate K in `[Kmin, Kmax]`, compute the adjacent merge-distance gap associated with cutting the hierarchy at K clusters.
11. Select the K with the largest merge-distance gap inside the candidate range.
12. Separately compute the K implied by distance threshold `0.002`.
13. Assign each retained micro-topic to one macro-topic.
14. Assign macro-topic labels manually using top keywords and representative speeches.

The macro-topic labels are interpretive labels assigned after clustering; they are not used during clustering.

## Generated Tables

The audit script writes:

- `retained_micro_topics.csv`: micro-topic counts, cumulative mass, and retained flag.
- `merge_gap_candidates.csv`: candidate K values, cut distances, adjacent gaps, largest-gap selection, and threshold selection.
- `macro_topic_mapping.csv`: computed mapping from retained micro-topic IDs to audit macro-topic IDs when embeddings are available.
- `macro_topic_mapping_template.csv`: fill-in template for manually curated/reporting labels if the computed mapping is not the final paper mapping.

## Machine-Readable Parameters

See `parameters.yaml`. Fields that are not recoverable from the repository are marked `TODO`.

## Camera-Ready Snippet

Do not paste either version into the camera-ready paper until the TODOs above are resolved. The current saved-artifact audit does not reproduce Kmacro = 30 from the largest-gap rule or from distance threshold 0.002.

### Version A: With exact computed values

The 336 BERTopic micro-topics were aggregated using a deterministic two-stage procedure. First, the noise topic (-1) was removed, leaving 12,632 speeches in substantive micro-topic clusters. Micro-topics were ranked by speech count, and the smallest prefix whose cumulative mass reached X_PERCENT of clustered speeches was retained, yielding RETAINED_N micro-topics. For each retained micro-topic, we computed a centroid by averaging the BGE-M3 embeddings of its assigned speeches and L2-normalizing the resulting vector. We then applied average-linkage hierarchical clustering using cosine distance over the retained centroids. To avoid fixing the number of macro-topics arbitrarily, we evaluated candidate cuts within [KMIN, KMAX] and selected the cut corresponding to the largest adjacent merge-distance gap. This produced a cut distance of 0.002 and yielded Kmacro = 30. Macro-topic labels were assigned post hoc from top keywords and representative speeches and were not used during clustering.

### Version B: If exact retained count cannot be recovered before camera-ready

The 336 BERTopic micro-topics were aggregated using a deterministic two-stage procedure. First, the noise topic (-1) was removed and only substantive micro-topic clusters were considered. Micro-topics were ranked by speech count, and a Pareto-style cumulative-mass filter retained the dominant prefix of topics for macro-level interpretation. For each retained micro-topic, a centroid was computed from the embeddings of its assigned speeches. These centroids were then clustered using average-linkage hierarchical clustering with cosine distance. Candidate cuts were inspected within a predefined interpretable range [Kmin, Kmax], and the final cut was selected using the largest adjacent merge-distance gap, yielding a distance threshold of 0.002 and Kmacro = 30. Macro-topic labels were assigned only after clustering using top keywords and representative speeches.

## TODOs

- TODO: confirm the exact cumulative speech-mass threshold X used in the paper.
- TODO: confirm whether the final paper should describe the executable notebook behavior (`MIN_SPEECHES = 50`, fixed `N_MACRO = 30`, KNN rescue) or the commented data-driven gap-search behavior.
- TODO: confirm whether saved UMAP-5D centroids are acceptable for the audit or whether original BGE-M3 speech embeddings must be restored.
- TODO: recover the exact original centroid artifact/parameter path if the authors want to support the claim that the largest-gap rule produced K=30.
