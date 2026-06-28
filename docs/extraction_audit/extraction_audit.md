# Hansard Extraction Audit

## Purpose

This document is the reviewer-facing audit artifact for the Hansard PDF extraction stage used in the MERCon 2026 paper, "Trilingual Topic Modeling of Sri Lankan Parliamentary Debates."

The audit exists because reviewers asked for enough information to inspect, reproduce, and qualify the extraction step before downstream topic modeling. In particular, they asked for:

- the exact extraction prompt used;
- the exact model/version and access date;
- the input format used for Gemini;
- post-processing steps;
- representative success and failure cases;
- a small manually checked extraction-quality benchmark;
- clarification that this is a multimodal document extraction pipeline, not a purely non-OCR method.

The extraction stage is documented as a **multimodal document extraction pipeline**. Gemini is treated as a document understanding component that may perform OCR-like visual text recognition internally when processing PDFs or rendered page images. Its role in this pipeline is to recover reading order, segment speaker turns, suppress procedural noise, preserve multilingual/code-mixed speech text, and normalize speaker identifiers.

Raw Hansard PDFs may be large. If storage constraints apply, keep full raw PDFs outside Git and document their source URLs, checksums, page ranges, and download instructions instead of committing every raw document.

## Recovered Extraction Prompt

Status: recovered prompt found in `src/ingestion/prompt.md`.

The following prompt is copied from that source file. It should be treated as the recovered extraction prompt currently present in this repository. Authors should verify that this is the exact prompt used for every experiment before citing it as the production prompt in the camera-ready paper.

```markdown
# Hansard Extraction Prompt

Role: You are an expert Data Extraction AI specialized in Sri Lankan Parliamentary Hansards and trilingual text recognition: Sinhala, Tamil, and English.

Task: I will provide pages from a dual-column parliamentary transcript. Extract only the substantive political speeches by Members of Parliament and convert them into clean, structured Markdown.

---

## Extraction Rules & Constraints

### 1. Output Format

Every extracted speech MUST follow this exact format â€” one speech per paragraph, with no line breaks inside a speech:

**[Speaker Full Name]:** [Complete text of the speech as a single paragraph.]

---

### 2. MPs Only â€” Drop All Procedural Turns

Do NOT extract anything spoken by the presiding officer or procedural roles. Specifically, drop ALL utterances from:

- The Speaker / à¶šà¶®à·à¶±à·à¶ºà¶šà¶­à·”à¶¸à· / Hon. Speaker
- The Deputy Chairperson of Committees / à¶±à·’à¶ºà·à¶¢à·Šâ€à¶º à¶šà·à¶»à¶š à·ƒà¶·à· à·ƒà¶·à·à¶´à¶­à·’à¶­à·”à¶¸à·’à¶º
- The Presiding Member / à¶¸à·–à¶½à·à·ƒà¶±à·à¶»à·–à¶¬ / Hon. Presiding Member
- Any unnamed role label used instead of a personal name, such as â€œà¶œà¶»à·” à¶‡à¶¸à¶­à·’à¶­à·”à¶¸à·â€, â€œHon. Ministerâ€, or â€œà¶œà¶»à·” à¶¸à¶±à·Šà¶­à·Šâ€à¶»à·“à¶­à·”à¶¸à·â€

Only extract speeches where the speaker is identified by their personal name.

---

### 3. Substantive Speech Filter

Do NOT extract short procedural noise. Drop any utterance that is:

- Fewer than about 50 words
- A procedural instruction, such as â€œOrder!â€, â€œà¶”à·€à·Šâ€, â€œà¶šà¶»à·”à¶«à·à¶šà¶» à¶‰à¶³à¶œà¶±à·Šà¶±â€, or â€œà¶´à·Šâ€à¶»à·à·Šà¶±à¶º à¶…à·„à¶±à·Šà¶±â€
- A time notification, such as â€œà¶”à¶¶à¶­à·”à¶¸à·à¶§ à·€à·’à¶±à·à¶©à·’ 5à¶š à¶šà·à¶½à¶ºà¶šà·Š à¶½à·à¶¶à·“ à¶‡à¶­â€
- An address preamble only, such as â€œà¶œà¶»à·” à¶šà¶®à·à¶±à·à¶ºà¶šà¶­à·”à¶¸à¶±à·’,â€ with no substantive content

Only extract full arguments, policy positions, questions, and responses that form a real speech.

---

### 4. Merge Interrupted Speeches

If the same MPâ€™s speech is interrupted by a procedural interjection from the Chair and then continues, treat it as ONE speech and merge the text.

Do not create separate entries for the same speakerâ€™s continuous argument.

---

### 5. Speaker Name Normalisation

Use only the MPâ€™s clean personal name. Remove role suffixes, address phrases, and ministry titles in parentheses.

Correct examples:

- **à¶œà¶»à·” à¶»à·€à·“ à¶šà¶»à·”à¶«à·à¶±à·à¶ºà¶š à¶¸à·„à¶­à·:**
- **à¶œà¶»à·” (à¶†à¶ à·à¶»à·Šà¶º) à·„à¶»à·’à¶±à·’ à¶…à¶¸à¶»à·ƒà·–à¶»à·’à¶º:**

Incorrect examples:

- **à¶œà¶»à·” à¶»à·€à·“ à¶šà¶»à·”à¶«à·à¶±à·à¶ºà¶š à¶¸à¶±à·Šà¶­à·Šâ€à¶»à·“à¶­à·”à¶¸à·, à¶”à¶¶à¶­à·”à¶¸à·à¶œà·š à¶¯à·™à·€à·à¶±à·’ à¶´à·Šâ€à¶»à·à·Šà¶±à¶º:**
- **à¶œà¶»à·” (à¶†à¶ à·à¶»à·Šà¶º) à·„à¶»à·’à¶±à·’ à¶…à¶¸à¶»à·ƒà·–à¶»à·’à¶º (à¶…à¶œà·Šâ€à¶»à·à¶¸à·à¶­à·Šâ€à¶º à·ƒà·„ à¶…à¶°à·Šâ€à¶ºà·à¶´à¶±...):**

---

### 6. Visual Reading Only

Do not rely on the PDFâ€™s embedded text layer. It may contain legacy font corruption.

Read ONLY visually. Transcribe exactly as it appears in Sinhala, Tamil, or English. Do not translate.

---

### 7. Dual-Column Layout

Read the left column completely from top to bottom, then the right column from top to bottom.

Do not bleed text across the column margin.

---

### 8. Noise Removal

Completely ignore:

- Page headers
- Footers
- Page numbers
- Section titles, such as â€œORAL ANSWERS TO QUESTIONSâ€
- Timestamps
- Vote tallies

---

## Final Output

Provide ONLY the clean Markdown.

Do not include introductory remarks, commentary, explanations, or notes.
```

## Model And Input Metadata

| Field | Value |
| --- | --- |
| Provider | Google |
| Model name | TODO: insert exact Gemini model name |
| Model version | TODO: insert exact model/version string if available |
| API or interface | TODO: Gemini API / AI Studio / Vertex AI / other |
| Access date start | TODO: YYYY-MM-DD |
| Access date end | TODO: YYYY-MM-DD |
| Study period note | The manuscript states that Gemini was adopted at study initiation around February 2026; replace with exact access dates where available. |
| Source documents | Sri Lankan Parliamentary Hansard PDFs |
| Input given to model | TODO: raw PDFs / rendered page images / extracted text / page screenshots |
| Page granularity | TODO: per page / per document / per batch |
| Languages | Sinhala, Tamil, English, code-mixed |
| Layout features | dual-column layout; mixed-script text; speaker labels; procedural text; page headers and footers |
| Output unit | speech turn |
| Output format | `**[Speaker Full Name]:** [speech text]` |
| Translation applied | false |
| Transliteration applied | false |
| Language normalization applied | false |

Known limitations to report:

- Gemini may internally rely on OCR-like visual text recognition when processing PDF pages.
- Dense dual-column pages may cause occasional reading-order errors.
- Short procedural turns may be merged with substantive speeches.
- Speaker labels may be incomplete or inconsistent in noisy pages.

## Post-Processing Pipeline

Actual post-processing code is in `src/ingestion/build_speech_corpus.py`.

| Step | Purpose | Script/File | Notes |
| --- | --- | --- | --- |
| Markdown discovery | Find extracted Gemini markdown inputs | `src/ingestion/build_speech_corpus.py` | Reads `data/extracted-markdown` by default and skips `*-empty.md` and blank files. |
| Speaker segment parsing | Split markdown into speaker/text turns | `SPEAKER_BLOCK_PATTERN` in `src/ingestion/build_speech_corpus.py` | Expects speaker labels followed by a colon; supports optional Markdown bolding/brackets. |
| Speech text cleanup | Collapse whitespace and discard empty speech text | `build_raw_records()` | Preserves original language/script content after whitespace normalization. |
| 50-word filtering | Remove short turns likely to be procedural/noise | `build_raw_records(min_words=50)` | Default minimum is 50 words. |
| Speaker normalization | Merge near-duplicate speaker names | `normalize_speakers()` | Uses `thefuzz.token_sort_ratio` with threshold 85. |
| ID assignment | Create stable speech IDs for the built corpus | `process_pipeline()` | Emits `SP_00000`, `SP_00001`, etc. |
| Output writing | Produce corpus and report artifacts | `process_pipeline()` and `main()` | Writes `artifacts/final_v14/all_speakers.csv` and `artifacts/final_v14/markdown_extraction_report.csv` by default. |

Reproduction command:

```powershell
python src\ingestion\build_speech_corpus.py --markdown-root data\extracted-markdown --output-dir artifacts\final_v14 --report-path artifacts\final_v14\markdown_extraction_report.csv --min-words 50
```

Current TODOs for authors:

- TODO: confirm whether any duplicate-removal occurred before or after this script.
- TODO: confirm whether additional manual validation rules were applied outside this repository.
- TODO: confirm exact Gemini input format and batching/page granularity.

## Representative Success Case Templates

Do not cite these as completed examples until the TODO fields are replaced with manually verified samples.

### Success Case 1: Sinhala substantive speech

Source:

- Hansard document: TODO
- Page number: TODO
- Language: Sinhala
- Input type: TODO

Expected extraction behavior:

- Speaker correctly identified.
- Procedural text removed.
- Sinhala text preserved without translation.

Extracted output:

```markdown
TODO: insert verified extracted speech
```

Manual note: TODO

### Success Case 2: Tamil or English substantive speech

Source:

- Hansard document: TODO
- Page number: TODO
- Language: TODO: Tamil / English
- Input type: TODO

Expected extraction behavior:

- Speaker correctly identified.
- Speech boundary preserved.
- Original language preserved without translation or transliteration.

Extracted output:

```markdown
TODO: insert verified extracted speech
```

Manual note: TODO

### Success Case 3: Code-mixed speech

Source:

- Hansard document: TODO
- Page number: TODO
- Language: code-mixed or mixed-script
- Input type: TODO

Expected extraction behavior:

- Code-mixed text preserved as written.
- Speaker turn remains one coherent paragraph.
- Procedural interruptions removed or excluded.

Extracted output:

```markdown
TODO: insert verified extracted speech
```

Manual note: TODO

## Candidate Failure Categories To Check

These are candidate failure categories to inspect manually. Do not claim they occurred in the benchmark until verified rows are added to the CSV.

### Failure Case 1: Dual-column reading-order confusion

Source:

- Hansard document: TODO
- Page number: TODO
- Language: TODO

Observed issue: TODO

Likely cause: dense dual-column layout or page transition.

Impact on downstream topic modeling: text from unrelated turns may be combined, weakening embedding/topic quality.

Mitigation: manually flag page in benchmark; compare Gemini output with page image/reference text.

### Failure Case 2: Speaker attribution error

Source:

- Hansard document: TODO
- Page number: TODO
- Language: TODO

Observed issue: TODO

Likely cause: ambiguous speaker label, role title, or label split across lines.

Impact on downstream topic modeling: speaker-level analysis and actor-topic heatmaps may be affected.

Mitigation: verify speaker labels against source page and correct gold benchmark fields.

### Failure Case 3: Procedural text retained or adjacent speeches merged

Source:

- Hansard document: TODO
- Page number: TODO
- Language: TODO

Observed issue: TODO

Likely cause: short procedural interjection, interrupted speech, or role label confused with MP name.

Impact on downstream topic modeling: procedural noise can dilute substantive topics or join unrelated policy statements.

Mitigation: mark `procedural_noise_removed=false` or `boundary_correct=false` in the benchmark.

Other candidate categories:

- Tamil/Sinhala mixed-script recognition issue.
- Page header/footer retained as speech.
- Table-only content incorrectly extracted.

## Manual Benchmark Instructions

Use `docs/extraction_audit/extraction_audit_manual_benchmark_template.csv` to record a small manually checked sample.

Recommended camera-ready sample:

- 10 Sinhala pages
- 5 Tamil pages
- 5 English pages
- 5 code-mixed or mixed-script pages

Minimum fallback sample if time is short:

- 3 Sinhala pages
- 2 Tamil pages
- 2 English/code-mixed pages

Annotation unit: one extracted speech turn, plus page-level layout checks where needed.

Field definitions:

- `speaker_correct`: true if the extracted speaker matches the source page speaker for the checked speech.
- `boundary_correct`: true if the extracted speech starts and ends at the correct turn boundaries.
- `layout_order_correct`: true if the extracted text follows the source reading order.
- `language_preserved`: true if there is no translation, transliteration, or major script corruption.
- `procedural_noise_removed`: true if procedural-only content is absent from the extracted speech.

Error categories:

- `dual_column_order`
- `speaker_attribution`
- `procedural_retained`
- `adjacent_speeches_merged`
- `speech_split`
- `mixed_script_recognition`
- `header_footer_retained`
- `table_content_extracted`
- `other`

Simple metrics:

- Speaker Accuracy = correct speaker attributions / checked speeches
- Boundary Accuracy = correctly segmented speeches / checked speeches
- Layout Order Accuracy = speeches with correct reading order / checked pages or speeches
- Language Preservation Accuracy = speeches with no translation, transliteration, or major script corruption / checked speeches
- Procedural Noise Error Rate = speeches incorrectly containing procedural-only content / checked speeches

The evaluator reports "Procedural Noise Removal Accuracy" as the share of checked rows where `procedural_noise_removed=true`.

Run:

```powershell
python scripts\evaluate_extraction_audit.py docs\extraction_audit\extraction_audit_manual_benchmark_template.csv
```

## Camera-Ready Paper Snippet

The Hansard extraction stage was implemented as a multimodal document extraction pipeline rather than a purely non-OCR method. Gemini was used as a document understanding component for layout-aware text recovery, speaker-turn segmentation, procedural-noise filtering, and preservation of Sinhala, Tamil, English, and code-mixed speech content. No translation, transliteration, or language normalization was applied. For auditability, we release the extraction prompt, model metadata, input-format description, post-processing steps, representative success and failure cases, and a manually checked extraction benchmark template in the accompanying repository.

On a manually checked sample of TODO pages / TODO speeches, we evaluated speaker attribution, speech-boundary segmentation, layout-order preservation, language preservation, and procedural-noise removal. The most common observed errors were TODO. These results are reported to contextualize downstream topic-modeling quality rather than to claim perfect extraction.
