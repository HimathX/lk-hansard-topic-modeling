# Annotation Guidelines

This file documents the recovered gold-label protocol for the 300-speech evaluation sample.

## Current Provenance

- Source files copied from the old repo:
  - `gold_standard_eval_sample_source.csv`
  - `topics_reasoning_source.json`
- Reconstructed canonical file:
  - `ground_truth_300.csv`

The recovered artifacts contain one adjudicated label and one rationale per speech. They do not contain per-annotator ballots, annotator IDs, or a machine-readable inter-annotator agreement table.

## Annotator Count

Recovered source metadata does not specify the number of annotators. Treat `ground_truth_300.csv` as the adjudicated gold file unless project notes outside this repo identify the individual annotators.

## Label Taxonomy

The label space contains 16 categories and is stored in `label_taxonomy.json`.

Annotators assign exactly one primary policy label per speech:

- Agriculture & Fisheries
- Culture & Religion
- Disaster Management
- Economy & Finance
- Education
- Environmental Protection
- Foreign Affairs
- Governance & Legal Reform
- Health & Social Welfare
- Infrastructure & Energy
- Labor & Migration
- National Security & Public Order
- Parliamentary Affairs
- Reconciliation & Justice
- Technology Innovation
- Tourism Promotion

## Labeling Instructions

1. Read the full speech text, not only the first sentence.
2. Choose the dominant policy or procedural issue discussed by the speaker.
3. Prefer substantive policy labels over `Parliamentary Affairs` unless the speech is primarily about procedure, standing orders, petitions, agenda control, or parliamentary conduct.
4. If a speech contains multiple issues, assign the label that best explains the speaker's main claim or request.
5. Record a short rationale that cites the specific issue, policy domain, or event driving the label.

## Adjudication

The copied source artifacts expose only the final label and rationale. If multiple annotators were used, the adjudication trail was not recovered from `D:\projects\Hanzards`.

## Inter-Annotator Agreement

Inter-annotator agreement cannot be recomputed from the recovered files because individual annotation sheets are not present. If those sheets are later recovered, add Cohen's kappa, Fleiss' kappa, or Krippendorff's alpha here and keep the adjudicated labels in `ground_truth_300.csv`.

## Validation Notes

The canonical evaluation file preserves all 300 annotated rows. Some rows may not align cleanly to the current processed corpus in `artifacts/final_v14/all_speakers.csv`, but this repository treats `ground_truth_300.csv` as the single source of truth for the recovered gold annotations.
