# Extraction Audit

This directory is the reviewer-facing mini-benchmark for the extraction claim.

The goal is to compare Gemini multimodal extraction against a Tesseract OCR baseline on the same fixed Hansard pages, using manually corrected reference text.

## Files

- `gemini_prompt.md`: canonical extraction prompt copied from the old repo.
- `samples/`: fixed source pages or source PDFs used for the audit.
- `gemini_outputs/`: Gemini markdown/text output for each sample.
- `tesseract_outputs/`: Tesseract OCR output for each sample.
- `reference_outputs/`: manually corrected text for each sample.
- `extraction_audit_results.csv`: output written by `src/evaluation/extraction_audit.py`.

## How To Add A Sample

1. Place the page PDF/image in `samples/`.
2. Use the same stem for each output file, for example `2025_01_10_p03.txt`.
3. Put the Gemini output in `gemini_outputs/2025_01_10_p03.txt`.
4. Put the Tesseract output in `tesseract_outputs/2025_01_10_p03.txt`.
5. Put the corrected reference in `reference_outputs/2025_01_10_p03.txt`.
6. Run:

```powershell
python src\evaluation\extraction_audit.py
```

The script reports word accuracy, speaker-boundary F1, and reading-order similarity.

## Current Status

The old repo did not contain recovered Gemini/Tesseract/reference audit outputs. This repo therefore includes the harness and a copied sample PDF, but does not claim audit scores until reference files are added.
