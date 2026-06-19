# LK Hansard Topic Modeling

The canonical pipeline is:

1. Extract speech-level corpus from Gemini markdown.
2. Generate BGE-M3 embeddings.
3. Run the v14 micro-topic and 30 macro-topic modeling workflow.
4. Evaluate, publish, and report reviewer-facing artifacts.

## Layout

- `src/ingestion/`: corpus building and Hansard download utilities.
- `src/modeling/`: final notebooks for embeddings, v14 macro-topics, and BiTopic comparison.
- `src/evaluation/`: portable metrics and extraction audit scripts.
- `src/publishing/`: Hugging Face dataset publishing helper.
- `data/evaluation/`: 300-row gold sample, evaluable subset, taxonomy, and annotation notes.
- `data/extraction_audit/`: Gemini prompt plus mini-benchmark scaffold.
- `artifacts/final_v14/`: copied final v14 outputs.
- `dashboard/`: copied final dashboard.
- `docs/`: architecture, data contracts, reproduction notes, and paper summary.

## Datasets

This repo contains both the full speech corpus outputs and the smaller evaluation datasets used to validate topic quality.

- `artifacts/final_v14/all_speakers.csv`: the main speech-level corpus built from extracted Hansard markdown.
- `data/evaluation/ground_truth_300.csv`: 300-row labeled evaluation sample used for reviewer-facing clustering checks.
- `data/evaluation/ground_truth_evaluable_273.csv`: evaluable subset after excluding rows that could not be matched cleanly to the current corpus.
- `data/evaluation/label_taxonomy.json`: consolidated topic taxonomy and provenance for the gold labels.

The evaluation dataset in `data/evaluation/` is the cleaned successor to the old materials from `D:\projects\Hanzards\src\BCubed-precision`, especially `gold_standard_eval_sample.csv` and `topics_reasoning.json`. The old local-only BCubed scripts were replaced here by portable modules under `src/evaluation/`.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python src\evaluation\run_evaluation.py
python src\evaluation\extraction_audit.py
python src\publishing\publish_huggingface_dataset.py --dry-run
```

See `docs/reproduce.md` for the full reproduction sequence and expected artifacts.
