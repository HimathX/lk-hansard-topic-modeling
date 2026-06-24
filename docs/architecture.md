# Architecture

This repo is a flat research-code copy of the final Hanzards v14 workflow. There is no `hanzards/` package folder. Code is grouped by workflow stage under `src/`.

## Pipeline

1. `src/ingestion/hansard_download.py` downloads official Hansard PDFs into a local data tree.
2. `docs/extraction_audit/extraction_audit.md` documents the recovered Gemini multimodal extraction prompt used to produce markdown.
3. `src/ingestion/build_speech_corpus.py` parses extracted markdown into a speech-level CSV, filters speeches below 50 words, normalizes speakers, and writes corpus artifacts.
4. `src/modeling/generate_bge_m3_embeddings.ipynb` creates yearly BGE-M3 `.npy` embedding files.
5. `src/modeling/run_macro_topic_modeling.ipynb` runs the final v14 pipeline: UMAP, HDBSCAN, KMeans and Agglomerative baselines, keyword extraction, and 30 macro-topic aggregation.
6. `src/modeling/compare_bitopic_bertopic.ipynb` preserves the v13 BiTopic experiment as a comparison notebook.
7. `src/evaluation/run_evaluation.py` reproduces reviewer-facing clustering and topic-quality tables.
8. `src/publishing/publish_huggingface_dataset.py` merges final speech text and topic assignments for Hugging Face publication.

## Canonical Artifacts

The final v14 outputs live in `artifacts/final_v14/`.

Key files:

- `all_speakers.csv`: final speech corpus.
- `v11_cluster_assignments.csv`: HDBSCAN, KMeans, and Agglomerative assignments.
- `macro_topic_assignments.csv`: final 30 macro-topic assignment per speech plus procedural noise.
- `macro_topic_keywords.json`: macro-topic keyword lists.
- `v11_metrics.csv`: baseline clustering metrics.
- `*.png`, `*.pdf`, `*.npy`: final figures and cached projections.

## Evaluation Layer

`src/evaluation/` replaces the old local-only BCubed scripts with portable modules:

- `classification_metrics.py`: B-Cubed precision, recall, F1, purity, ARI, and NMI.
- `topic_quality_metrics.py`: dependency-light C_V-style coherence, topic diversity, and mass/coverage.
- `run_evaluation.py`: end-to-end table writer.
- `extraction_audit.py`: Gemini-vs-Tesseract mini-benchmark evaluator.

## Known Provenance Limits

The 300-speech gold sample includes adjudicated labels and rationales, but no recovered per-annotator sheets or IAA table. The extraction audit harness is present, but recovered Gemini/Tesseract/reference audit outputs were not found in the old repo.
