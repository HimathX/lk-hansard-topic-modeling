# LK Hansard Topic Modeling

Trilingual topic modeling workflow for Sri Lankan parliamentary Hansards, including corpus extraction, multilingual embedding generation, topic modeling, evaluation, and reviewer-facing audit artifacts.

## Project Links

- Hugging Face dataset: <https://huggingface.co/datasets/himath-nimpura/sl-parliamentary-hansard-17-26>
- Dashboard: <https://hansards.vercel.app/>

## Project Team

### Student Authors

- D.H.N. Dhanapala
- K.S.H. Daishika
- H.A. Kuruppu
- N.A.K. Nawagamuwa
- N.S. Seneviratne

### Supervisors

- Dr. Nisansa de Silva
- Dr. Sandareka Wickramanayake

### Senior Advisors

- P. Narasinghe
- S. Weerasekara

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
- `docs/extraction_audit/`: consolidated Gemini extraction audit and benchmark instructions.
- `artifacts/final_v14/`: copied final v14 outputs.
- `dashboard/`: copied final dashboard.
- `docs/`: architecture, data contracts, reproduction notes, paper summary, and extraction audit notes.

## Datasets

The primary public dataset for this project is hosted on Hugging Face:

- <https://huggingface.co/datasets/himath-nimpura/sl-parliamentary-hansard-17-26>

This repository keeps the workflow, reviewer-facing evaluation assets, and supporting artifacts used to reproduce the analysis around that dataset.

- `data/evaluation/ground_truth_300.csv`: 300-row labeled evaluation sample used for reviewer-facing clustering checks.
- `data/evaluation/ground_truth_evaluable_273.csv`: evaluable subset after excluding rows that could not be matched cleanly to the current corpus.
- `data/evaluation/label_taxonomy.json`: consolidated topic taxonomy and provenance for the gold labels.
- `artifacts/final_v14/all_speakers.csv`: local copied corpus artifact retained for reproducibility of the final v14 workflow.

The evaluation data in `data/evaluation/` is the cleaned successor to the old materials from `D:\projects\Hanzards\src\BCubed-precision`, especially `gold_standard_eval_sample.csv` and `topics_reasoning.json`. The old local-only BCubed scripts were replaced here by portable modules under `src/evaluation/`.

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
