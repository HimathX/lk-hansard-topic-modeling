# Reproduction Guide

These commands assume Windows PowerShell from the repo root.

## Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 1. Build Speech Corpus

Use this step only when extracted Gemini markdown exists under `data/extracted-markdown/`.

```powershell
python src\ingestion\build_speech_corpus.py --min-words 50
```

Expected output:

- `artifacts/final_v14/all_speakers.csv`
- `artifacts/final_v14/markdown_extraction_report.csv`

## 2. Generate Embeddings

Open and run:

```text
src/modeling/generate_bge_m3_embeddings.ipynb
```

Expected output:

- `embeddings/<year>.npy`

## 3. Run Final Topic Modeling

Open and run:

```text
src/modeling/run_macro_topic_modeling.ipynb
```

Expected final outputs:

- `artifacts/final_v14/v11_cluster_assignments.csv`
- `artifacts/final_v14/macro_topic_assignments.csv`
- `artifacts/final_v14/macro_topic_keywords.json`
- v14 figures and UMAP cache files

The final v14 configuration uses 50-word speech filtering and 30 macro-topics.

## 4. Run Evaluation

```powershell
python src\evaluation\run_evaluation.py
```

Expected output:

- `artifacts/evaluation/table_iii_metrics.csv`
- `artifacts/evaluation/topic_quality_metrics.csv`
- `artifacts/evaluation/evaluation_summary.md`

## 5. Run Extraction Audit

Add matched files to `data/extraction_audit/reference_outputs/`, `gemini_outputs/`, and `tesseract_outputs/`, then run:

```powershell
python src\evaluation\extraction_audit.py
```

Expected output:

- `data/extraction_audit/extraction_audit_results.csv`

## 6. Publish Dataset Dry Run

```powershell
python src\publishing\publish_huggingface_dataset.py --dry-run
```

To push, set `HF_TOKEN` in `.env` or the environment and pass `--repo-id`.
