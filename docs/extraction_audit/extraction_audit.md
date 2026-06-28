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

## Extraction Prompt

```markdown
# Hansard Extraction Prompt

Role: You are an expert Data Extraction AI specialized in Sri Lankan Parliamentary Hansards and trilingual text recognition: Sinhala, Tamil, and English.

Task: I will provide pages from a dual-column parliamentary transcript. Extract only the substantive political speeches by Members of Parliament and convert them into clean, structured Markdown.

---

## Extraction Rules & Constraints

### 1. Output Format

Every extracted speech MUST follow this exact format — one speech per paragraph, with no line breaks inside a speech:

**[Speaker Full Name]:** [Complete text of the speech as a single paragraph.]

---

### 2. MPs Only — Drop All Procedural Turns

Do NOT extract anything spoken by the presiding officer or procedural roles. Specifically, drop ALL utterances from:

- The Speaker / කථානායකතුමා / Hon. Speaker
- The Deputy Chairperson of Committees / නියෝජ්‍ය කාරක සභා සභාපතිතුමිය
- The Presiding Member / මූලාසනාරූඬ / Hon. Presiding Member
- Any unnamed role label used instead of a personal name, such as “ගරු ඇමතිතුමා”, “Hon. Minister”, or “ගරු මන්ත්‍රීතුමා”

Only extract speeches where the speaker is identified by their personal name.

---

### 3. Substantive Speech Filter

Do NOT extract short procedural noise. Drop any utterance that is:

- Fewer than about 50 words
- A procedural instruction, such as “Order!”, “ඔව්”, “කරුණාකර ඉඳගන්න”, or “ප්‍රශ්නය අහන්න”
- A time notification, such as “ඔබතුමාට විනාඩි 5ක කාලයක් ලැබී ඇත”
- An address preamble only, such as “ගරු කථානායකතුමනි,” with no substantive content

Only extract full arguments, policy positions, questions, and responses that form a real speech.

---

### 4. Merge Interrupted Speeches

If the same MP’s speech is interrupted by a procedural interjection from the Chair and then continues, treat it as ONE speech and merge the text.

Do not create separate entries for the same speaker’s continuous argument.

---

### 5. Speaker Name Normalisation

Use only the MP’s clean personal name. Remove role suffixes, address phrases, and ministry titles in parentheses.

Correct examples:

- **ගරු රවී කරුණානායක මහතා:**
- **ගරු (ආචාර්ය) හරිනි අමරසූරිය:**

Incorrect examples:

- **ගරු රවී කරුණානායක මන්ත්‍රීතුමා, ඔබතුමාගේ දෙවැනි ප්‍රශ්නය:**
- **ගරු (ආචාර්ය) හරිනි අමරසූරිය (අග්‍රාමාත්‍ය සහ අධ්‍යාපන...):**

---

### 6. Visual Reading Only

Do not rely on the PDF’s embedded text layer. It may contain legacy font corruption.

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
- Section titles, such as “ORAL ANSWERS TO QUESTIONS”
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
| Model name | Gemini Pro |
| Model version | 3.1 |
| API or interface | Gemini web interface |
| Access date start | 2026-03-20 |
| Access date end | 2026-06-12 |
| Study period note | Dates and interface details were confirmed by the authors after repository recovery. The checked-in extracted markdown corpus spans 786 files dated `2017-01-09` through `2026-02-19`. |
| Source documents | Sri Lankan Parliamentary Hansard PDFs from `https://www.parliament.lk/en/business-of-parliament/hansards` |
| Input given to model | Raw PDFs |
| Page granularity | One document in batches |
| Languages | Sinhala, Tamil, English, code-mixed |
| Layout features | dual-column layout; mixed-script text; speaker labels; procedural text; page headers and footers |
| Output unit | speech turn |
| Output format | `**[Speaker Full Name]:** [speech text]` |

Known limitations to report:

- Gemini may internally rely on OCR-like visual text recognition when processing PDF pages.
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

Recovered notes for authors:

- No additional executable manual-validation script was recovered in this repository snapshot.
- The authors confirmed that they manually corrected speaker names, removed bad outputs, and retried failed pages outside the checked-in repository scripts.
- `docs/paper-summary.md` narrates extra cleanup steps such as header/footer stripping, page-number removal, and duplicate removal across page boundaries, but those steps are not present in the checked-in `src/ingestion/build_speech_corpus.py`. Treat them as narrative-only unless the original script or execution logs are restored.
- The recovered prompt still documents the extraction behavior as visual reading only, so the pipeline should be described as multimodal raw-PDF ingestion with visually grounded extraction rather than plain text-layer parsing.

## Representative Success Case Templates

The examples below were visually checked against rendered sample PDF pages on June 28, 2026. They should be treated as a seed benchmark, not as a substitute for the larger camera-ready sample recommended later in this document.

### Success Case 1: Sinhala substantive speech

Source:

- Hansard document: `data/samples/2025_01_10.pdf`
- Page number: printed Hansard page `546` on the rendered spread `545-546`
- Language: Sinhala
- Input type: rendered PDF page image from the source Hansard PDF

Expected extraction behavior:

- Speaker correctly identified.
- Procedural text removed.
- Sinhala text preserved without translation.

Verified excerpt from extracted output:

```markdown
**ගරු බිමල් රත්නායක මහතා:** ගරු කථානායකතුමනි, ප්‍රථමයෙන්ම, හිටපු පාර්ලිමේන්තු මන්ත්‍රී ගරු කුමාර වෙල්ගම මන්ත්‍රීතුමාගේ අභාවය පිළිබඳ ශෝක යෝජනාවයි මා ඉදිරිපත් කරන්න බලාපොරොත්තු වන්නේ. ඔබතුමාගේ ආරාධනයෙන් එතුමාගේ පවුලේ ඥාතීන් අද දින පැමිණ සිටින බව දැනුම් දී තිබෙනවා.
```

Manual note: The speaker label, opening sentence, and memorial context align visually with the right-hand printed page `546`; no header/footer or bilingual contents-page text leaked into the extracted paragraph.

### Success Case 2: Tamil or English substantive speech

Source:

- Hansard document: `data/samples/2024_04_02.pdf`
- Page number: printed Hansard pages `241-242`
- Language: English
- Input type: rendered PDF page image from the source Hansard PDF

Expected extraction behavior:

- Speaker correctly identified.
- Speech boundary preserved.
- Original language preserved without translation or transliteration.

Verified excerpt from extracted output:

```markdown
**රවුෆ් හකීම්:** Hon. Deputy Speaker, we are discussing the Banking (Amendment) Bill that had been brought in order to regulate important areas of the banking business in this country, particularly at a time when we are faced with a serious debt crisis and are in the process of restructuring our international debt.
```

Manual note: The English paragraph on the rendered spread matches the extracted markdown opening exactly enough for reviewer inspection, including the bill name and the debt-restructuring context.

### Success Case 3: Code-mixed speech

Source:

- Hansard document: `data/samples/2024_04_02.pdf`
- Page number: printed Hansard pages `183-184`
- Language: code-mixed or mixed-script
- Input type: rendered PDF page image from the source Hansard PDF

Expected extraction behavior:

- Code-mixed text preserved as written.
- Speaker turn remains one coherent paragraph.
- Procedural interruptions removed or excluded.

Verified excerpt from extracted output:

```markdown
**චරිත හේරත්:** ගරු කථානායකතුමනි, මේ අවස්ථාව වන විට අපට මාධ්‍ය මඟින් දැනගන්න ලැබිලා තිබෙනවා, ඇමෙරිකාවේ ඉඳලා නැව්ගත වෙලා තිබෙන Maersk කියන කොම්පැනියට අයත් "Dali" නමැති නෞකාව hazardous waste වර්ගයේ wastes ගණනාවක් රැගෙන ලංකාවට ගමන් කරමින් තිබෙනවා කියලා.
```

Manual note: The spread preserves a Sinhala paragraph with embedded English ship and hazard terms (`Maersk`, `Dali`, `hazardous waste`) without translation or normalization, which is exactly the code-mixed behavior the audit needs to show.

## Candidate Failure Categories To Check

These are candidate failure categories to inspect manually. Do not claim they occurred in the benchmark until verified rows are added to the CSV.

### Failure Case 1: Dual-column reading-order confusion

Source:

- Hansard document: `data/samples/2024_04_02.pdf`
- Page number: printed Hansard pages `183-184`
- Language: code-mixed Sinhala-English

Observed issue: No confirmed failure in the checked excerpt, but this spread is the strongest local stress test for reading-order failure because one long code-mixed turn runs across both printed pages and sits beside other dense dual-column content.

Likely cause: dense dual-column layout or page transition.

Impact on downstream topic modeling: text from unrelated turns may be combined, weakening embedding/topic quality.

Mitigation: manually flag page in benchmark; compare Gemini output with page image/reference text.

### Failure Case 2: Speaker attribution error

Source:

- Hansard document: `data/samples/2025_01_10.pdf`
- Page number: printed Hansard pages `545-546`
- Language: Sinhala memorial debate

Observed issue: No confirmed failure in the checked excerpt, but this spread contains multiple role labels and memorial transitions in close proximity, making it a good attribution-check page for manual review.

Likely cause: ambiguous speaker label, role title, or label split across lines.

Impact on downstream topic modeling: speaker-level analysis and actor-topic heatmaps may be affected.

Mitigation: verify speaker labels against source page and correct gold benchmark fields.

### Failure Case 3: Procedural text retained or adjacent speeches merged

Source:

- Hansard document: `data/samples/2024_04_02.pdf`
- Page number: printed Hansard pages `185-186`
- Language: code-mixed Sinhala-English

Observed issue: No confirmed failure in the checked excerpt, but this spread alternates Charitha Herath, Sajith Premadasa, and Janaka Wakkumbura across two printed pages, so it is the best local sample for probing adjacent-speech merge or procedural carry-over errors.

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



Run:

```powershell
python scripts\evaluate_extraction_audit.py docs\extraction_audit\extraction_audit_manual_benchmark_template.csv
```
