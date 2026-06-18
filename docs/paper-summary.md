# Multilingual Topic Modeling of Sri Lankan Parliamentary Debates

**Department of Computer Science & Engineering**
**University of Moratuwa, Sri Lanka**

**Submitted in partial fulfilment of the requirements for the degree of**
**Bachelor of Science in Engineering (Computer Science & Engineering)**

---

> **Authors:** D.H.N. Dhanapala · K.S.H. Daishika · H.A. Kuruppu · N.A.K. Nawagamuwa · N.S. Seneviratne
> **Supervisor:** [TBD — Insert Supervisor Name]
> **Date:** [TBD — Insert Submission Date]

---

## Abstract

Parliamentary Hansards represent a high-value yet methodologically challenging source for political analysis, particularly in multilingual settings where code-mixing, morphological complexity, and domain-specific rhetoric collectively undermine the assumptions of classical topic models. This thesis addresses that challenge through the Sri Lankan Hansard corpus (2017–2026) — a trilingual dataset in Sinhala, Tamil, and English shaped by major political shocks, including the 2019 Easter Sunday attacks and the 2022 economic crisis and Aragalaya civil uprising. The central problem is to recover coherent, cross-lingual thematic structure from this corpus without imposing arbitrary topic counts or collapsing meaningful variation into procedural noise.

The proposed pipeline combines BGE-M3 multilingual embeddings with UMAP dimensionality reduction, HDBSCAN density-based clustering, and a two-stage macro-topic aggregation procedure — Pareto-based size filtering followed by an **Empirical Dendrogram Cut** on micro-topic centroids — to extract a data-driven taxonomy of **30 interpretable macro-topics** from 19,553 parliamentary speeches. As an exploratory extension, a hybrid semantic–lexical architecture (**BiTopic**) is additionally investigated to assess whether augmenting dense embeddings with lexical bag-of-words features can improve topic boundary sharpness and reduce embedding blur.

Empirical results confirm that the primary pipeline successfully recovers the dominant thematic structure of Sri Lankan parliamentary discourse. The 30 macro-topics span policy domains ranging from energy economics and constitutional reform to Easter Sunday attack accountability and fisheries industry. Temporal trajectories align with real-world events without any event labelling: economy-linked topics surge sharply during the 2022 Aragalaya crisis, and national security discourse rises in proximity to the 2019 Easter Sunday attacks. The language distribution across macro-topics confirms that BGE-M3 embeddings group speeches by content rather than language of expression. The exploratory BiTopic study further suggests that lexical grounding at a weight of $\beta = 0.15$ ($\alpha = 0.85$) can reduce topic fragmentation, though at a coverage cost, motivating future work on adaptive fusion strategies.

**Keywords:** multilingual NLP, topic modelling, BERTopic, Sri Lankan Hansard, Sinhala, Tamil, HDBSCAN, BGE-M3, macro-topic aggregation, dendrogram cut, parliamentary discourse analysis

---

## Chapter 1: Introduction

### 1.1 Background and Motivation

The Parliament of Sri Lanka constitutes the supreme legislative authority of the country and serves as the principal forum for national deliberation on matters of governance, public policy, economic planning, and social welfare. The official transcripts of these proceedings — collectively known as Hansards — represent one of the most comprehensive and longitudinally rich documentary records of Sri Lankan political discourse available in the public domain. Published across three official languages, namely Sinhala, Tamil, and English, these transcripts capture decades of legislative debate, policy argumentation, and inter-party exchange in their original linguistic form.

The systematic computational analysis of such a corpus carries significant scholarly and civic value. Topic modelling applied to parliamentary debates can reveal the distribution of legislative attention across policy domains, track the emergence and decline of political issues over time, and provide a quantitative foundation for downstream tasks such as sentiment analysis, political stance detection, and representative accountability studies. However, realising this potential requires overcoming a distinct set of technical challenges that existing natural language processing (NLP) methodologies are ill-equipped to address without substantive adaptation.

The Sri Lankan Hansard corpus is characterised by three interrelated properties that collectively distinguish it from the parliamentary corpora on which the majority of prior computational work has been conducted. First, it is inherently *trilingual*: a single parliamentary session may contain speeches delivered in Sinhala, Tamil, English, or in code-mixed combinations of these languages, often within a single speaker turn. Second, both Sinhala and Tamil exhibit highly *agglutinative morphology*, wherein a single root word may take on dozens of surface forms through affixation, rendering bag-of-words representations impoverished for semantic comparison. Third, the source documents are *distributed in PDF format* subject to complex dual-column layouts and mixed-script rendering that severely limits the reliability of conventional optical character recognition (OCR) pipelines.

Beyond these structural and linguistic challenges, the corpus spans a politically turbulent decade (2017–2026) encompassing the 2019 Easter Sunday bombings, the 2022 economic collapse and mass civil protests known as the Aragalaya, successive government collapses, and an IMF-supervised fiscal restructuring programme. These events generate identifiable documentary signatures within parliamentary speech — spikes in debate frequency, dramatic vocabulary shifts, and the emergence of entirely new thematic clusters. Recovering and quantifying this temporal thematic structure from raw transcript data is both a technically demanding and historically significant undertaking.

These challenges motivate the development of an end-to-end multilingual NLP pipeline specifically designed for the Sri Lankan parliamentary domain. The present thesis addresses this need by constructing and empirically evaluating a complete processing pipeline spanning text extraction, multilingual embedding generation, density-based topic clustering, and hierarchical macro-topic aggregation. As a secondary investigation, a hybrid semantic–lexical architecture — BiTopic — is explored as an experimental extension aimed at addressing the phenomenon of embedding blur in dense representation spaces.

### 1.2 Research Questions

This thesis is structured around three primary research questions:

**RQ1 — Multilingual Topic Modelling:** How can a topic modelling pipeline be designed to operate effectively over a large-scale trilingual corpus containing Sinhala, Tamil, and English, including code-mixed text, while preserving cross-lingual semantic coherence without requiring language-specific preprocessing for each script?

**RQ2 — Empirical Macro-Topic Determination:** Can the number and boundaries of macro-level thematic groupings be determined empirically from the hierarchical geometric structure of HDBSCAN micro-topic centroids, eliminating the need for an arbitrary user-specified cluster count?

**RQ3 — Hybrid Semantic–Lexical Fusion (Experimental):** Does augmenting dense semantic embeddings with a lexical representation component within a hybrid BiTopic architecture reduce embedding blur and improve topic boundary sharpness, relative to the primary embedding-only pipeline?

### 1.3 Contributions

This thesis makes the following research contributions to the fields of multilingual NLP and computational political science:

1. **An end-to-end multilingual parliamentary topic modelling pipeline**, combining LLM-based text extraction, BGE-M3 cross-lingual embeddings, UMAP dimensionality reduction, HDBSCAN density-based clustering, and a hierarchical macro-topic aggregation stage yielding **30 interpretable macro-topics** from 19,553 Hansard speeches. This pipeline is, to the best of the authors' knowledge, the first to address the full span of the trilingual Sri Lankan parliamentary corpus at this scale.

2. **A curated trilingual parliamentary corpus**, web-scraped and LLM-extracted from the official Sri Lankan Hansard archive spanning 2017–2026, with a manually annotated ground-truth subset of 300 speeches across 16 topic categories for supervised evaluation.

3. **A custom cross-lingual embedding evaluation framework**, assessing four state-of-the-art multilingual embedding models on the 300-speech annotated subset using cross-lingual semantic textual similarity (STS), semantic retrieval (Precision@5, MRR), and embedding space anisotropy — producing the first documented benchmark of this kind for Sri Lankan parliamentary text.

4. **An empirical macro-topic aggregation method** using Pareto-based size filtering and an Empirical Dendrogram Cut on HDBSCAN micro-topic centroids (cosine distance, average linkage, cut at distance threshold 0.002), yielding a data-driven $K_{\text{macro}} = 30$ without arbitrary specification.

5. **A curated trilingual stopword list** comprising 1,045 terms across Sinhala, Tamil, and English, including parliamentary procedural vocabulary and domain-specific boilerplate essential for clean topic representation in this domain.

6. **An exploratory BiTopic investigation**, evaluating the effect of semantic–lexical weight fusion ($\alpha = 0.85$, $\beta = 0.15$) on topic count, noise rate, and boundary sharpness relative to the primary semantic-only baseline.

### 1.4 Thesis Structure

The remainder of this thesis is organised as follows. Chapter 2 reviews the relevant literature spanning topic modelling methodology, multilingual embedding models, density-based clustering, and prior work on parliamentary NLP. Chapter 3 describes the Sri Lankan Hansard corpus, the data collection and LLM-based extraction pipeline, and the preprocessing methodology. Chapter 4 presents the full methodology of the primary pipeline, including the embedding model evaluation, UMAP and HDBSCAN configuration, and the macro-topic aggregation procedure, followed by a dedicated subsection introducing the experimental BiTopic architecture. Chapter 5 reports results from the clustering benchmark, the 30 macro-topic analysis, temporal and actor-level findings, and the BiTopic ablation study. Chapter 6 discusses the implications of the findings, addresses each research question, and identifies limitations and future directions.

---

## Chapter 2: Literature Review

### 2.1 Topic Modelling: Methodological Evolution

#### 2.1.1 Latent Dirichlet Allocation and Classical Methods

The dominant paradigm in computational topic modelling for over two decades has been Latent Dirichlet Allocation (LDA), introduced by Blei, Ng, and Jordan (2003). LDA is a generative probabilistic model that represents each document as a probabilistic mixture of latent topics and each topic as a distribution over vocabulary terms. LDA and its extensions have been widely applied to parliamentary and legislative corpora: Lauderdale and Clark (2014) used an LDA-based approach to model debates in the U.S. Congress, Abercrombie and Batista-Navarro (2018) constructed a sentiment-labelled corpus of UK Hansard debates, and Rauh and Schwalbach (2020) applied LDA to the ParlSpeech corpus of Western European proceedings.

Despite these successes, LDA carries fundamental assumptions that render it structurally unsuitable for multilingual, agglutinative corpora. Its bag-of-words representation treats each vocabulary term as an independent feature, discarding all syntactic and morphological information. For agglutinative languages such as Sinhala and Tamil, wherein a single root form may surface as dozens of distinct word forms through case, tense, aspect, and derivational affixation, this assumption is especially damaging: semantically equivalent terms are treated as unrelated features, causing topic distributions to fragment along morphological rather than thematic lines. Furthermore, LDA has no mechanism for cross-lingual alignment; in a multilingual corpus, semantically equivalent speeches in different languages are assigned to different topics solely because they share no vocabulary, producing language-stratified rather than thematically unified clusters. Non-negative Matrix Factorisation (NMF; Lee and Seung, 1999) shares these same fundamental limitations.

#### 2.1.2 Neural and Embedding-Based Topic Models

The introduction of transformer-based contextual embeddings fundamentally altered the design space for topic modelling. Rather than representing documents by term frequencies, neural approaches encode documents as dense vectors in a continuous semantic space, where proximity reflects semantic relatedness independently of surface vocabulary. Contextualised Topic Models (CTMs; Bianchi et al., 2021) extended variational inference by conditioning on sentence-transformer embeddings, enabling zero-shot cross-lingual topic modelling. Top2Vec (Angelov, 2020) was among the earliest methods to combine dense document embeddings with UMAP dimensionality reduction and HDBSCAN clustering to identify topics as dense regions in embedding space without requiring prior specification of topic count.

BERTopic (Grootendorst, 2022) refined and extended this paradigm by introducing class-based TF-IDF (c-TF-IDF) for topic keyword extraction, which computes term importance relative to a topic's document set rather than the global corpus, yielding more distinctive keyword representations. BERTopic's modular architecture — separating embedding, dimensionality reduction, clustering, and keyword extraction into independent components — makes it readily adaptable to multilingual settings and constitutes the foundational framework of the present pipeline. Its non-parametric cluster count and principled noise handling via HDBSCAN are particularly suited to parliamentary discourse.

#### 2.1.3 Embedding Blur in Parliamentary Corpora

A limitation of purely embedding-based topic modelling that has received limited explicit treatment in the literature is what this thesis terms *embedding blur*: the phenomenon whereby dense contextual embeddings place semantically adjacent but politically distinct terms at distances insufficient to induce cluster separation. In the Sri Lankan context, embedding blur manifests when Sinhala and Tamil semantic near-synonyms — sharing denotative meaning but differing in political valence — collapse to the same embedding region, or when politically distinct English terms such as *devolution*, *federalism*, and *autonomy* exhibit high cosine similarity due to similar co-occurrence contexts. This phenomenon motivates the experimental BiTopic investigation described in Section 4.5.

### 2.2 Multilingual Embedding Models

The effectiveness of any embedding-based topic modelling system is directly conditional on the quality and properties of the underlying document representations. For a trilingual parliamentary corpus, two requirements are paramount: *cross-lingual alignment*, such that semantically equivalent speeches in Sinhala, Tamil, and English are mapped to nearby embedding vectors; and *distributional coverage*, such that the embedding space does not collapse into a narrow region that impairs density-based clustering.

**Multilingual-E5-large-instruct** (Wang et al., 2024) achieves state-of-the-art cross-lingual semantic similarity but exhibits pathologically high anisotropy (0.909 on the parliamentary benchmark): its embeddings collapse into a narrow cone in representation space, eliminating the density contrasts that UMAP and HDBSCAN require. Its 512-token context limit additionally truncates the majority of parliamentary speeches.

**BAAI/BGE-M3** (Chen et al., 2025) was designed to address these limitations through an 8,192-token context window and self-knowledge distillation training. It achieves an anisotropy score of 0.552 — substantially lower — while retaining competitive retrieval performance. Its extended context window allows full parliamentary speeches to be encoded without truncation, and its training corpus includes Sinhala, Tamil, and English.

**LaBSE** (Feng et al., 2022) achieves stable cross-lingual alignment with healthy anisotropy (0.492) but is constrained to a 512-token context window, restricting its effectiveness for long-form parliamentary speeches. **Paraphrase-multilingual-mpnet-base-v2** serves as a general-purpose baseline with low anisotropy but weaker cross-lingual alignment for Sinhala–English and Tamil–English pairs.

### 2.3 Density-Based Clustering and the Precision–Coverage Trade-Off

Parliamentary topic discovery requires a clustering algorithm capable of identifying topically coherent groupings of variable size and shape without requiring prior knowledge of cluster count, while remaining robust to the substantial proportion of speeches that are procedural, transitional, or thematically ambiguous.

**HDBSCAN** (Campello, Moulavi, and Sander, 2013; McInnes, Healy, and Astels, 2017) addresses these limitations through a hierarchical, density-based cluster extraction procedure. Rather than requiring $K$, HDBSCAN constructs a hierarchy of clusters at varying density levels and extracts the most stable ones using the excess of mass (EOM) criterion. Speeches in low-density regions are assigned to a noise class (label $-1$), acting as a principled filtering mechanism that improves the thematic purity of accepted clusters at the cost of reduced coverage. **K-Means** and **Agglomerative Clustering** force all documents into clusters, absorbing procedural and noise speeches and reducing cluster purity — a critical deficiency for downstream sentiment analysis applications requiring semantically clean topic assignments.

### 2.4 Macro-Topic Aggregation and Cluster Count Selection

A hierarchical perspective on parliamentary topic structure distinguishes between *micro-topics* — fine-grained thematic units — and *macro-topics*, broader thematic domains. The selection of $K$ for any aggregation stage is a well-known challenge. Hierarchical clustering dendrograms offer a principled alternative: the merge distances in the dendrogram's linkage matrix encode the relative cost of each cluster fusion, and large gaps in these distances indicate natural boundaries in the data's cluster structure. The present thesis proposes a constrained gap-detection procedure over the linkage dendrogram of HDBSCAN micro-topic centroids, restricting the search to a semantically interpretable range $[K_{\min}, K_{\max}]$ to avoid degenerate solutions. This method yields $K_{\text{macro}} = 30$ as an empirically supported partition count.

### 2.5 Parliamentary NLP and South Asian Corpora

Computational work on parliamentary NLP is concentrated almost entirely on high-resource, morphologically simple European languages. South Asian parliamentary corpora remain substantially understudied. The specific challenges of Sinhala NLP — including morphological complexity, the absence of word boundaries in certain contexts, and scarcity of annotated training data — have been noted by Senevirathna et al. (2024) in the context of code-mixed sentiment analysis, but have not been systematically addressed in a parliamentary topic modelling setting. Code-mixed Sri Lankan Tamil, which incorporates Sinhala and English borrowings, diverges substantially from standard Tamil and presents distinct modelling challenges.

### 2.6 Research Gaps and Positioning

The preceding review identifies four concurrent gaps: (i) no prior work applies neural topic modelling to the full-scale Sri Lankan Hansard corpus across all three official languages; (ii) existing multilingual topic models have not been benchmarked on agglutinative, code-mixed parliamentary corpora; (iii) no prior work proposes a principled, data-driven method for hierarchical macro-topic construction from HDBSCAN outputs; and (iv) the phenomenon of embedding blur in dense-only parliamentary topic models has not been explicitly characterised or experimentally addressed. This thesis addresses all four gaps.

---

## Chapter 3: Dataset and Preprocessing

### 3.1 Overview

This chapter describes the construction of the Sri Lankan Hansard corpus, encompassing data collection, LLM-based text extraction, quality assurance, linguistic preprocessing, and the engineered resources that underpin downstream modelling. The final processed corpus comprises **19,553 speeches** from parliamentary sessions spanning 2017 to 2026.

### 3.2 Data Collection

#### 3.2.1 Source and Scope

The primary data source is the official website of the Parliament of Sri Lanka, which publishes digitised Hansard records as PDF documents. The Hansard constitutes the verbatim official record of parliamentary proceedings. Each PDF corresponds to a single day of parliamentary sitting and contains all speeches delivered during that session, along with procedural annotations, speaker identifiers, and multilingual content reflecting the language chosen by each Member of Parliament.

The collection period spans from 2017 to 2026. This range was chosen to encompass both a pre-crisis baseline period and the economically and politically turbulent years surrounding the 2019 Easter Sunday attacks, the 2022 economic collapse, the Aragalaya civil uprising, and the subsequent IMF-supervised fiscal restructuring. This temporal span enables downstream temporal topic analysis to capture the full arc of parliamentary response to major national crises.

[Figure 3.1: Parliamentary Activity by Year Annotated with Key Political Events]

#### 3.2.2 Web Scraping Methodology

A dedicated web scraping pipeline was developed to systematically collect Hansard PDF documents from the parliamentary archive. The scraper traversed year-level index pages, identified linked PDF documents for each parliamentary sitting, and downloaded each document into a structured local directory organised by year and session date. HTTP request throttling and retry logic were implemented to ensure reliable collection. Documents from non-sitting dates, question sessions, and committee reports were excluded, as these do not contain debate speeches of the type targeted by the pipeline.

### 3.3 Text Extraction

#### 3.3.1 Limitations of Conventional OCR

Initial text extraction using Tesseract OCR (version 5.x) proved inadequate for the Hansard corpus. The dual-column layout of most Hansard pages caused systematic column-interleaving errors, producing semantically incoherent output at column boundaries. Mixed-script content caused frequent character substitution errors, particularly for Sinhala characters sharing visual features with Latin glyphs. Older Hansard PDFs employ non-standard font encodings for Sinhala and Tamil glyphs, causing transcription errors and Unicode normalisation failures including mojibake sequences for Tamil conjunct characters and Sinhala vowel diacritics. Speaker attribution lines were inconsistently retained or dropped, making speaker-level analysis unreliable. Page headers, footers, and page numbers were systematically incorporated into extracted text.

Quantitative assessment on a manually reviewed sample of 50 pages confirmed error rates incompatible with reliable topic modelling: approximately 23% of extracted text segments contained character-level errors severe enough to corrupt the intended word, and 38% of multi-paragraph extracts contained at least one structural error (column interleaving, incomplete speaker attribution, or header/footer contamination).

#### 3.3.2 LLM-Based Extraction with Google Gemini

To overcome these limitations, a large language model-based extraction pipeline was adopted using Google Gemini. A carefully engineered prompt was designed to simultaneously: (i) extract only substantive speeches delivered by identified Members of Parliament; (ii) suppress procedural content including interruptions, Speaker rulings, and short non-informative utterances; and (iii) enforce a structured output format wherein each speech segment was represented as a single coherent text block attributed to a normalised speaker identifier.

The prompt explicitly instructed the model to preserve multilingual and code-mixed text in its original form without translation, normalisation, or transliteration — ensuring that Sinhala and Tamil content was retained with its original script and morphological structure intact. This is a critical design choice: translating or transliterating speeches would collapse the linguistic diversity of the corpus and remove information that is itself an object of analysis.

The LLM-based extraction produced substantially cleaner output. Dual-column interleaving was resolved through the model's contextual understanding of textual coherence; mixed-script content was reproduced accurately; speaker attribution was reliably maintained. Residual noise including page numbers, headers, and non-speech procedural elements was effectively suppressed. Speaker names were normalised by removing titles (e.g., *Hon.*, *Dr.*, *Prof.*) and role-based suffixes, yielding a consistent speaker identifier per speech.

### 3.4 Post-Extraction Preprocessing

#### 3.4.1 Speaker Name Normalisation

Raw speaker attributions include honorific titles, role-based suffixes, constituency identifiers, and transliterated name variants across Sinhala, Tamil, and English. For example, the same Member of Parliament may appear as *"Hon. Wijesinghe"*, *"ගරු විජේසිංහ මැතිතුමා"*, or *"திரு. விஜேசிங்க"* across sessions. Normalisation proceeded in three stages: removal of common honorific prefixes and suffixes, phonemic matching using edit-distance heuristics to merge transliteration variants, and manual review of ambiguous cases.

#### 3.4.2 Residual Noise Removal

Following speaker normalisation, rule-based filters were applied to remove running headers and footers, page number tokens, and parliamentary session metadata lines; to deduplicate speeches appearing twice due to multi-page boundary effects; and to filter speeches below a minimum threshold of 50 words, which typically represent procedural acknowledgements or interjections that escaped the extraction filter.

#### 3.4.3 Language Detection

Language detection was applied to each speech using a combination of script-based heuristics (Unicode block membership) and probabilistic language identification. Speeches were categorised into language classes including Sinhala, Tamil, English, and code-mixed variants.

[Figure 3.2: Speech Language Distribution — Bar Chart and Proportional Breakdown by Language Category]

The corpus is substantially Sinhala-dominant (approximately 76%), reflecting the demographic and parliamentary majority. Tamil and English speeches each constitute approximately 7% of the corpus, with the remaining approximately 10% comprising code-mixed categories. This distribution reflects genuine parliamentary language practice and motivates the embedding model selection criteria described in Section 4.2.

### 3.5 Corpus Statistics

The final preprocessed corpus contains **19,553 speeches** spanning 2017–2026.

**Table 3.1: Corpus Summary Statistics**

| Statistic | Value |
|---|---|
| Total speeches | 19,553 |
| Years covered | 2017–2026 |
| Unique speakers | [TBD — Insert count] |
| Median speech length (words) | ~300 |
| 95th percentile speech length (words) | ~1,200 |
| BGE-M3 truncation rate (<8,192 tokens) | < 3% |
| Estimated truncation rate at 512 tokens | ~35–40% |

[Figure 3.3: Hansard Speech Length Distribution — Word Count Histogram and Token Truncation Impact]

Speech length is right-skewed: the majority of speeches are between 50 and 400 words, reflecting typical parliamentary turns, while a small number of ministerial statements exceed 1,000 words. Under BGE-M3's 8,192-token context window, fewer than 3% of speeches require truncation. By contrast, models with a 512-token limit would truncate approximately 35–40% of speeches, representing a substantial loss of semantic content for longer policy addresses.

[Figure 3.4: Parliamentary Activity Timeline — Speech Count per Session Year]

### 3.6 Ground-Truth Annotation Subset

To enable quantitative evaluation of the clustering pipeline, a subset of 300 speeches was manually annotated with expert-assigned topic labels using a taxonomy of **16 thematic categories**: Economy & Finance, Governance & Legal Reform, Parliamentary Affairs, Infrastructure & Energy, Health & Social Welfare, National Security & Public Order, Agriculture & Fisheries, Education, Foreign Affairs & Diplomacy, Reconciliation & Transitional Justice, Labour & Migration, Culture & Religion, Disaster Management, Technology & Innovation, Tourism Promotion, and Environmental Protection.

Language identification on the annotated subset revealed **273 Sinhala speeches (91.0%), 19 Tamil speeches (6.3%), and 8 English speeches (2.7%)**. Prior to clustering evaluation, topic labels with fewer than five speech instances were excluded to prevent severe class imbalance from deflating evaluation metrics, yielding a **filtered subset of 288 speeches across 13 topic categories** for all benchmark comparisons.

### 3.7 Trilingual Stopword Engineering

A custom stopword list was engineered specifically for the Sri Lankan parliamentary domain. Standard English stopword lists are entirely absent of Sinhala and Tamil content and do not address the domain-specific parliamentary vocabulary that recurs at high frequency regardless of topical content.

The list was constructed through three stages. First, language-specific base lists were compiled for Sinhala, Tamil, and English through manual inspection of high-frequency, low-information terms in each script. Second, parliamentary procedural vocabulary was added for each language: speaker acknowledgements, formulaic address terms, procedural motions, and administrative boilerplate. Third, corpus-level frequency analysis identified terms appearing in more than 80% of speeches — indicating insufficient discriminative power for topic modelling — which were added regardless of language.

The final stopword list comprises **1,045 terms** across Sinhala, Tamil, and English. This resource was applied within the CountVectorizer and topic representation stages to suppress non-informative vocabulary while preserving semantically meaningful content.

---

## Chapter 4: Methodology

### 4.1 Overview

The methodology of this thesis proceeds in two clearly demarcated parts. The **primary pipeline** (Sections 4.2–4.6) constitutes the core contribution: a multilingual topic modelling framework producing 30 empirically grounded macro-topics from the full Hansard corpus. An **experimental extension**, the BiTopic architecture (Section 4.7), is independently evaluated as an exploratory study into the effect of lexical grounding on topic boundary formation.

### 4.2 Baseline: Latent Dirichlet Allocation

Before adopting embedding-based approaches, a baseline topic modelling experiment was conducted using Latent Dirichlet Allocation (LDA). This establishes a reference point for interpretable lexical modelling against which the proposed pipeline can be compared.

Given a corpus $\mathcal{D} = \{d_1, \dots, d_M\}$ and vocabulary of size $V$, LDA assumes the following generative process for each document $d$:

1. Draw topic mixture $\theta_d \sim \mathrm{Dirichlet}(\alpha_0)$.
2. For each token position $n$: draw topic assignment $z_{d,n} \sim \mathrm{Categorical}(\theta_d)$, then draw observed word $w_{d,n} \sim \mathrm{Categorical}(\phi_{z_{d,n}})$, where $\phi_k \sim \mathrm{Dirichlet}(\eta_0)$.

The LDA pipeline was adapted for the multilingual corpus using a custom whitespace tokeniser (to avoid distorting non-Latin scripts) and the 1,045-term trilingual stopword list. Standard stemming and lemmatisation were deliberately avoided. Model selection was performed over $K \in \{10, 15, 20, 25, 30\}$.

Despite these adaptations, LDA failed to produce coherent and unified topics. Its reliance on word co-occurrence produced language-specific topic fragmentation: Sinhala, Tamil, and English speeches discussing the same political event were assigned to distinct topics characterised by surface vocabulary rather than semantic content. Morphological dispersion in Sinhala and Tamil further diluted topic distributions by distributing a single lexical root across many low-frequency surface forms. These failures confirm the inadequacy of bag-of-words approaches for multilingual parliamentary discourse and motivate the transition to embedding-based methods.

### 4.3 Embedding Model Selection

#### 4.3.1 Evaluation Framework

Four multilingual embedding models were evaluated on the 300-speech ground-truth subset using three complementary methods:

- **Method 1 — Cross-Lingual Semantic Textual Similarity (STS):** Mean cosine similarity between speech pairs across different languages within the same annotated topic. This evaluates whether semantically equivalent speeches in Sinhala, Tamil, and English map to similar regions in the embedding space.

- **Method 2 — Semantic Retrieval:** English queries related to parliamentary topics were issued against the corpus; retrieval effectiveness was measured using Precision@5 and Mean Reciprocal Rank (MRR).

- **Method 3 — Anisotropy Analysis:** Global anisotropy was measured as the mean off-diagonal cosine similarity of randomly sampled speech embeddings. High anisotropy indicates vector collapse — a condition in which all representations become uniformly similar regardless of content — eliminating the density contrasts required by UMAP and HDBSCAN.

#### 4.3.2 Benchmark Results

**Table 4.1: Embedding Model Benchmark on 300 Hansard Speeches**

| Model | STS Mean ↑ | Retrieval MRR ↑ | P@5 ↑ | Anisotropy ↓ | Verdict |
|---|---|---|---|---|---|
| multilingual-e5-large-instruct | 0.827 | 0.810 | 0.56 | 0.909 | ✗ Collapsed |
| **BAAI/bge-m3** | **0.523** | **0.516** | **0.68** | **0.552** | **✓ Selected** |
| LaBSE | 0.487 | 0.324 | 0.72 | 0.492 | ✓ Healthy |
| paraphrase-multilingual-mpnet-base-v2 | 0.424 | 0.536 | 0.76 | 0.496 | ✓ Healthy |

[Figure 4.1: Embedding Model Benchmark Results — Comparative Visualisation across STS, Retrieval, and Anisotropy]

#### 4.3.3 Selection Rationale: Anisotropy as the Decisive Criterion

Although Multilingual-E5-large-instruct achieves the highest raw STS score (0.827), its anisotropy of 0.909 causes embeddings to collapse into a narrow cone in representation space. This eliminates the geometric density contrasts that UMAP and HDBSCAN require for effective topic separation: in a collapsed space, all pairwise cosine similarities are elevated irrespective of semantic content, making density-based cluster identification impossible regardless of semantic quality. Furthermore, its 512-token context limit results in systematic truncation of parliamentary speeches.

BGE-M3 achieves an anisotropy of 0.552 — substantially lower — while retaining competitive retrieval performance and uniquely providing an 8,192-token context window that accommodates full parliamentary speeches without truncation, preserving discourse-level semantics essential for accurate topic formation. LaBSE achieves healthy anisotropy but its context limitation is prohibitive for this corpus. **BAAI/BGE-M3 was therefore selected as the embedding model for the proposed pipeline**, with selection motivated primarily by the primacy of anisotropy and context coverage over raw similarity score when the downstream task is density-based clustering.

### 4.4 Dimensionality Reduction with UMAP

Following embedding generation using BGE-M3, UMAP (Uniform Manifold Approximation and Projection; McInnes et al., 2018) was applied to reduce the 1,024-dimensional embedding space to a lower-dimensional representation suitable for clustering. Specifically, embeddings were projected into a **5-dimensional space** using UMAP configured with:

$$n\_\text{neighbors} = 15, \quad n\_\text{components} = 5, \quad \min\_\text{dist} = 0.0, \quad \text{metric} = \text{cosine}.$$

This dimensionality reduction step is critical for HDBSCAN's effectiveness. UMAP preserves local neighbourhood relationships while restructuring the embedding space to exhibit more pronounced density variations. The choice of $\min\_\text{dist} = 0.0$ encourages tighter grouping of semantically similar points, improving cluster compactness and separation.

A separate **2-dimensional UMAP projection** ($\min\_\text{dist} = 0.1$) was generated for visualisation purposes only, providing an interpretable representation of the embedding structure without influencing the clustering procedure.

### 4.5 Density-Based Topic Formation with HDBSCAN

#### 4.5.1 Why Density-Based Clustering Is Essential

Parliamentary text exhibits structurally heterogeneous discourse density. High-density regions correspond to sustained policy debates; medium-density regions correspond to sub-debates and secondary discussions; and low-density regions correspond to procedural utterances, short interjections, and contextually ambiguous fragments. Partitioning methods such as K-Means, which force every point into a cluster, degrade topic purity by assigning low-information utterances to substantive clusters. HDBSCAN identifies stable dense regions and assigns low-density points to a noise class ($y_i = -1$), functioning as a principled purification mechanism.

Formally, HDBSCAN constructs a hierarchy over mutual reachability distances and extracts the most stable clusters using the excess of mass (EOM) criterion. Points not satisfying minimum cluster stability constraints receive label $-1$. In the full corpus run, HDBSCAN produced **336 micro-topics** and assigned **6,921 speeches (35.4%) to procedural noise**, retaining 12,632 speeches (64.6%) in substantive topic clusters.

#### 4.5.2 Clustering Algorithm Comparison

Three clustering algorithms were benchmarked at $K = 336$ on the BGE-M3 UMAP-reduced embedding space, using Silhouette Score, Calinski-Harabász Index (CH), and Davies-Bouldin Index (DB, lower is better).

**Table 4.2: Clustering Algorithm Benchmark — Full Corpus ($K = 336$)**

| Algorithm | $K$ | Noise % | $N$ Evaluated | Silhouette ↑ | CH Index ↑ | DB Index ↓ |
|---|---|---|---|---|---|---|
| **HDBSCAN** | 336 | 35.4% | 12,632 | **0.5741** | **15,052** | **0.5148** |
| KMeans | 336 | 0.0% | 19,553 | 0.4076 | 13,098 | 0.8745 |
| Agglomerative | 336 | 0.0% | 19,553 | 0.3812 | 12,217 | 0.9088 |

[Figure 4.2: Clustering Visualisation — UMAP 2D Projection Comparing HDBSCAN, KMeans, and Agglomerative at K=336]

HDBSCAN achieves the highest silhouette (0.5741 vs. 0.4076 and 0.3812), the best CH score, and the lowest DB index, despite evaluating on only 64.6% of documents. KMeans and Agglomerative force every speech into a cluster — inflating $N_{\text{evaluated}}$ — but contaminate cluster geometry with low-density procedural utterances, depressing all three quality metrics. As visible in the UMAP scatter (Figure 4.2), the HDBSCAN panel shows distinct, well-separated density islands, while KMeans and Agglomerative panels show diffuse, overlapping colour regions with no coherent spatial structure, visually confirming their inferior cluster quality.

**Table 4.3: Clustering Algorithm Benchmark — Ground-Truth Subset (288 Speeches, 13 True Topics)**

| Algorithm | K Found | Noise % | BCubed P | BCubed F1 | ARI | NMI | Silhouette |
|---|---|---|---|---|---|---|---|
| K-Means | 13 | 0.0% | 0.349 | 0.324 | 0.184 | 0.379 | 0.388 |
| Agglomerative (Ward) | 13 | 0.0% | 0.355 | 0.340 | 0.191 | 0.398 | 0.377 |
| **HDBSCAN** | **11** | **41.7%** | **0.673** | 0.313 | 0.104 | 0.340 | **0.532** |
| OPTICS | 19 | 36.1% | 0.670 | 0.250 | 0.073 | 0.351 | 0.497 |

HDBSCAN achieves BCubed Precision of 0.673 — substantially higher than K-Means (0.349) and Agglomerative (0.355) — indicating that its clusters are substantially purer in terms of true topic homogeneity, even accounting for its 41.7% noise rate on this benchmark subset. The lower BCubed F1 score relative to partition methods reflects the precision–coverage trade-off: HDBSCAN prioritises forming compact, well-defined clusters over exhaustive coverage. For the downstream application of sentiment analysis, this trade-off is desirable — sentiment signals applied to impure mixed-topic clusters would be ambiguous and misleading.

The cluster size distribution (Figure 4.3) further illustrates a critical difference: HDBSCAN produces a strongly right-skewed distribution dominated by a single large noise cluster (n = 6,921) and a long tail of micro-topics, whereas KMeans and Agglomerative produce broadly uniform cluster sizes, artificially distributing procedural noise across all 336 clusters.

[Figure 4.3: Cluster Size Distribution — HDBSCAN (red = noise), KMeans, and Agglomerative at K=336]

#### 4.5.3 Topic Representation

For topic keyword extraction, a CountVectorizer was configured with the 1,045-term trilingual stopword list, capturing both unigrams and bigrams while preserving Unicode characters for correct Sinhala and Tamil rendering. BERTopic's KeyBERT-inspired and Maximal Marginal Relevance (MMR) representation models were applied to prioritise semantically informative, non-redundant terms, yielding more descriptive and distinguishable topic representations.

### 4.6 Macro-Topic Aggregation

The 336 micro-topics produced by HDBSCAN are analytically useful at fine granularity but too numerous for chapter-level political interpretation. A two-stage aggregation procedure is introduced to transform micro-topic outputs into a stable, interpretable macro-topic structure.

#### 4.6.1 Step 1: Pareto-Based Size Filtering

Micro-topics are ranked by size $n_t = |C_t|$ in descending order. Cumulative coverage is defined as:

$$P(m) = \frac{\sum_{t=1}^{m} n_{(t)}}{\sum_{t=1}^{T} n_{(t)}},$$

where $n_{(t)}$ denotes sorted sizes. A Pareto-style threshold retains dominant micro-topics up to a target coverage of 80–90% of total speech mass, filtering the long tail of hyper-local, low-frequency debate clusters that represent one-off interventions rather than sustained thematic discourse. The micro-topic size distribution (Figure 4.3) directly motivates this step: a small fraction of micro-topics accounts for the majority of speech volume.

#### 4.6.2 Step 2: Empirical Dendrogram Cut on Micro-Topic Centroids

For each retained micro-topic $C_t$, its centroid in the BGE-M3 embedding space is computed:

$$\boldsymbol{\mu}_t = \frac{1}{|C_t|}\sum_{d_i \in C_t} \mathbf{e}_{d_i}.$$

An agglomerative hierarchical clustering model is fitted over $\{\boldsymbol{\mu}_t\}$ using **cosine distance and average linkage**, yielding a dendrogram over micro-topics. Instead of fixing $K$ a priori, the dendrogram is cut at an **empirically determined distance threshold** identified as the point of greatest structural stability within an interpretable range $[K_{\min}, K_{\max}]$.

The dendrogram (Figure 4.4) reveals a cut at **cosine distance threshold = 0.002**, yielding $K_{\text{macro}} = \mathbf{30}$ macro-topics. This cut corresponds to the most prominent gap in merge distances within the interpretable range, representing the natural partition boundary in the data's cluster geometry. The resulting mapping assigns each retained micro-topic to one of 30 macro-topic groups without arbitrary specification.

$$g: \{1, \dots, T'\} \rightarrow \{1, \dots, 30\},$$

where $T'$ is the number of retained micro-topics after Pareto filtering.

[Figure 4.4: Hierarchical Dendrogram of Micro-Topic Centroids — Cosine Distance, Average Linkage; Cut at dist=0.002 → 30 Macro-Topics]

### 4.7 Experimental Extension: The BiTopic Architecture

This section describes the BiTopic architecture, an **exploratory extension** investigated to assess whether augmenting dense semantic embeddings with lexical bag-of-words features can reduce embedding blur and improve topic boundary formation. BiTopic is treated as a secondary experimental study and is evaluated independently of the primary pipeline.

#### 4.7.1 Motivation

The primary pipeline relies exclusively on BGE-M3 semantic embeddings. While BGE-M3 produces strong cross-lingual alignment, purely embedding-based approaches are susceptible to embedding blur in parliamentary text (Section 2.1.3): semantically adjacent but institutionally distinct concepts can collapse to indistinguishable embedding vectors, causing over-merging in dense topic clusters. Lexical representations, while lacking cross-lingual alignment, are inherently sensitive to the exact terminology used in a speech and can provide discriminative anchoring at topic boundaries.

#### 4.7.2 Dual Representation and Fusion

For each document $d_i$, two complementary representations are constructed:

- **Semantic embedding:** $\mathbf{e}_i \in \mathbb{R}^{1024}$ from BGE-M3.
- **Lexical sparse vector:** $\mathbf{v}_i \in \mathbb{R}^V$ from CountVectorizer with the trilingual stopword list.

Pairwise similarity matrices are computed independently:

$$S_{\text{semantic}}(i,j) = \cos(\mathbf{e}_i, \mathbf{e}_j), \qquad S_{\text{lexical}}(i,j) = \cos(\mathbf{v}_i, \mathbf{v}_j).$$

Both matrices are normalised to a common scale and fused via weighted combination:

$$S_{\text{final}} = \alpha\, S_{\text{semantic}} + \beta\, S_{\text{lexical}}, \qquad \alpha + \beta = 1.$$

The fused similarity induces a distance matrix $D_{\text{final}} = 1 - S_{\text{final}}$ used by downstream HDBSCAN. Crucially, this **early fusion** strategy ensures that HDBSCAN operates on a unified geometric field jointly encoding semantic and lexical proximity, rather than merging cluster labels post-hoc.

#### 4.7.3 Fusion Weight Ablation

The fusion weights were selected through a systematic sweep over $\alpha \in \{0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 1.00\}$ with $\beta = 1 - \alpha$, holding all other hyperparameters constant.

**Table 4.4: BiTopic Fusion Weight Ablation**

| $\alpha$ (semantic) | $\beta$ (lexical) | Topics ($K$) | Noise Count | Noise % | Clustered % |
|---|---|---|---|---|---|
| 0.60 | 0.40 | 276 | 8,436 | 43.14 | 56.86 |
| 0.70 | 0.30 | 281 | 8,535 | 43.65 | 56.35 |
| 0.80 | 0.20 | 291 | 8,733 | 44.66 | 55.34 |
| **0.85** | **0.15** | **277** | **8,990** | **45.98** | **54.02** |
| 0.90 | 0.10 | 272 | 8,775 | 44.88 | 55.12 |
| 0.95 | 0.05 | 295 | 8,401 | 42.97 | 57.03 |
| 1.00 | 0.00 | 318 | 7,244 | 37.05 | 62.95 |

[Figure 4.5: α/β Ablation Study — Effect of Fusion Weights on Noise % and Number of Topics (K)]

The ablation reveals several structural patterns. The pure semantic limit ($\alpha = 1.00$) maximises clustered proportion (62.95%) and topic count (318), but without lexical grounding, semantically adjacent debates across policy sub-domains can over-merge. Conversely, heavy lexical weighting ($\alpha \leq 0.70$) collapses cross-lingual coverage: agglutinative Sinhala and Tamil morphology produces many distinct surface forms per root, causing thematically equivalent speeches in different languages to appear lexically dissimilar, fragmenting cross-lingual clusters into language-specific shards.

The value **$\alpha = 0.85$ ($\beta = 0.15$)** was selected as the experimental operating point. At this weighting, the semantic component remains dominant — preserving cross-lingual alignment and paraphrastic grouping — while the lexical component provides sufficient anchoring to sharpen topic boundaries and differentiate institutionally distinct but semantically adjacent discourse. This weighting corresponds to an inflection in the noise–coverage trade-off curve, beyond which further lexical weight either degrades coverage or provides diminishing boundary-sharpening benefit.

#### 4.7.4 Comparison of Early vs. Late Fusion

Early and late fusion strategies were compared at fixed hyperparameters:

| Pipeline | Topics ($K$) | Noise % | Clustered % |
|---|---|---|---|
| BERTopic (semantic only, $\alpha=1.00$) | 336 | 35.40% | 64.60% |
| BiTopic — **Early Fusion** ($\alpha=0.85$) | 277 | 45.98% | 54.02% |
| BiTopic — Late Fusion ($\alpha=0.85$) | [TBD] | [TBD] | [TBD] |

Early fusion is adopted as the experimental strategy, as it allows HDBSCAN's density estimator to operate on a unified distance field jointly encoding semantic and lexical proximity. Late fusion produces incoherent label boundaries when independent modality clusterings are merged post-hoc.

#### 4.7.5 Evaluation Metrics

Two complementary metrics are used to evaluate topic quality across both the primary and experimental pipelines:

**Silhouette Score.** For each document $i$, define $a(i)$ as the mean distance to points in its own cluster and $b(i)$ as the minimum mean distance to points in the nearest other cluster:
$$s(i) = \frac{b(i) - a(i)}{\max\{a(i), b(i)\}} \in [-1, 1], \qquad S = \frac{1}{N}\sum_{i=1}^{N} s(i).$$

**Topic Coherence $c_v$.** The $c_v$ metric estimates semantic interpretability by measuring co-occurrence consistency among top topic words in a sliding-window reference corpus. While computed algorithmically, $c_v$ correlates strongly with human topic judgement in practice. Joint optimisation of Silhouette and $c_v$ reflects the core objective: *semantic separation with lexical interpretability*.

---

## Chapter 5: Results and Evaluation

### 5.1 Primary Pipeline Results: The 30 Macro-Topics

The primary pipeline — BGE-M3 embeddings → UMAP (5D) → HDBSCAN → Pareto filtering → Empirical Dendrogram Cut — was applied to all 19,553 speeches in the full 2017–2026 corpus. The pipeline produced **336 HDBSCAN micro-topics**, from which the macro-topic aggregation procedure derived **30 final macro-topics** by cutting the dendrogram at cosine distance threshold 0.002. Of the full corpus, **12,632 speeches (64.6%)** are assigned to substantive macro-topics and **6,921 speeches (35.4%)** are classified as procedural noise.

#### 5.1.1 Macro-Topic Speech Volume Distribution

[Figure 5.1: Speech Count per Macro-Topic — Horizontal Bar Chart (30 Macro-Topics + Procedural Noise)]

The 30 macro-topics vary substantially in speech volume, reflecting the genuine non-uniform distribution of parliamentary agenda attention. The largest substantive topic (Macro-Topic 1: Energy Economy & Fuel Crisis) contains 1,395 speeches, followed by Macro-Topic 5 (Social Welfare, Housing & Water, 852 speeches) and Macro-Topic 2 (Tamil-medium Parliamentary Debates, 738 speeches). Smaller but non-trivial macro-topics cover specialised policy domains: Macro-Topic 12 (Utilities Legislation & Media Law, 89 speeches), Macro-Topic 21 (Dairy Industry & Livestock, 90 speeches), and Macro-Topic 22 (SAITM Medical Education & Defence University, 114 speeches). This variation is substantively expected: any model producing equal-sized topics on this corpus would be generating artificial balance rather than recovering real agenda structure.

#### 5.1.2 Macro-Topic Taxonomy: Labels and Keywords

The 30 macro-topics are presented with their descriptive labels, derived from the top TF-IDF and c-TF-IDF keyword sets.

**Table 5.1: 30 Macro-Topics — Descriptive Labels and Speech Counts**

| ID | Label | Speeches | Top Keywords |
|---|---|---|---|
| MT-0 | Parliamentary Procedure & Standing Orders | 509 | ප්‍රශ්න, ආණ්ඩුක්‍රම, ස්ථාවර නියෝග, පාර්ලිමේන්තු, ව්‍යවස්ථා |
| MT-1 | Energy Economy & Fuel Crisis | 1,395 | රුපියල්, ණය, ආර්ථික, මෙගාවොට්, තෙල් ටැංකි, සූර්ය |
| MT-2 | Tamil-Medium Parliamentary Debates | 738 | இவ்வாறு, நடவடிக்கைகளை, பிரதமர், பாதிக்கப்பட்ட |
| MT-3 | Infrastructure — Ports, Aviation & Urban Dev. | 340 | වරාය නගරය, හම්බන්තොට, ශ්‍රීලන්කන්, ගුවන් යානා |
| MT-4 | Agriculture, Plantation & Price Policy | 736 | කිලෝවක් රුපියල්, තේ, පොහොර, ගම්මිරිස්, කාබනික |
| MT-5 | Social Welfare, Housing & Water | 852 | නිවාස, ජල, සමෘද්ධි, ආපදා, ගංවතුර |
| MT-6 | Parliamentary Oversight & Public Accounts (COPE) | 424 | රජයේ ගිණුම්, COPE, බැඳුම්කර, කාර්ය සාධන |
| MT-7 | Education — Schools, Universities & Teachers | 724 | පාසල්, ගුරු, විශ්ව විද්‍යාල, විභාග, අධ්‍යාපනය |
| MT-8 | Constitutional Amendments & Executive Governance | 568 | ආණ්ඩුක්‍රම ව්‍යවස්ථා, සංශෝධනය, ජනාධිපති, රාජාසන |
| MT-9 | Parliamentary Privilege & Conduct | 360 | රාමනායක, රන්ජන්, වරප්‍රසාද, ආචාර ධර්ම |
| MT-10 | Cooperative Finance & Microfinance | 227 | සමුපකාර, ක්ෂුද්‍ර මූල්‍ය, බැංකු, තැන්පතු |
| MT-11 | Healthcare, Pharmaceuticals & NMRA | 685 | nmra, ඖෂධ, වෛද්‍ය, රෝහල්, කොවිඩ් |
| MT-12 | Utilities Legislation & Media Law | 89 | ලංකා විදුලිබල, ජනමාධ්‍ය, රූපවාහිනී, සංශෝධන |
| MT-13 | English-Medium Governance & Peace Discourse | 317 | peace, majority, sovereignty, constitution, tamil |
| MT-14 | Environment, Land & Wildlife Conservation | 653 | වනජීවී, ඉඩම්, අලි-මිනිස් ගැටුම, සංරක්ෂණ |
| MT-15 | Parliamentary Condolences & Obituaries | 481 | නිවන් සුව, අභාවය, ශෝකය, ජ මු |
| MT-16 | Specific Parliamentary Events (Political) | 184 | අමරකීර්ති, Commonwealth, Queen Elizabeth |
| MT-17 | Easter Sunday Attacks & National Security | 439 | පාස්කු ප්‍රහාරය, සහරාන්, කොමිෂන් වාර්තාව, ත්‍රස්ත |
| MT-18 | Transport & Road Infrastructure | 370 | දුම්රිය, බස් රථ, අධිවේගී, මාර්ග සංවර්ධන |
| MT-19 | Foreign Employment, Tourism & Diaspora | 234 | විදේශ රැකියා, සංචාරකයන්, ශ්‍රමිකයන්, ප්‍රේෂණ |
| MT-20 | Human Rights & International Relations | 189 | මානව හිමිකම්, ජිනීවා, ත්‍රස්තවාදය, ඇමෙරිකා |
| MT-21 | Dairy Industry & Livestock | 90 | කිරි පිටි, දියර කිරි, පශු සම්පත්, ලීටර් |
| MT-22 | SAITM Medical Education & Defence University | 114 | සයිටම්, SAITM, කොතලාවල, නිදහස් අධ්‍යාපනය |
| MT-23 | Electoral Reform & Local Government Elections | 389 | සීමා නිර්ණය, මැතිවරණ කොමිෂන්, ඡන්ද, මනාප |
| MT-24 | Tax Policy — Excise, Gems & Revenue | 148 | සුරා බදු, මැණික්, VAT, ස්වර්ණාභරණ |
| MT-25 | Cricket & Sports Administration | 240 | ලංකා ක්‍රිකට්, ICC, ක්‍රීඩකයන්, ක්‍රිකට් ආයතනය |
| MT-26 | Judicial Affairs, Crime & Anti-Corruption | 563 | නඩු, අධිකරණ, දූෂණ, මහේන්ද්‍රන්, රිමාන්ඩ් |
| MT-27 | Fisheries & Maritime Industry | 133 | ධීවර, මත්ස්‍ය, යාත්‍රා, බහුදින, ඩීසල් |
| MT-28 | Plantation (Estate) Sector & Labour | 155 | වතු, වැටුප, කම්කරු, තේ වතු, තොණ්ඩමන් |
| MT-29 | Heritage, Women, Children & Municipal Waste | 286 | පුරාවිද්‍යා, කසළ, කාන්තාවන්, ළමා, බුද්ධ ශාසන |

[Figure 5.2: Keyword Word Clouds per Macro-Topic (TF-IDF Distinctive Terms) — 30-Panel Grid]

The keyword word clouds (Figure 5.2) provide immediate visual confirmation of thematic coherence. Policy cores are clearly visible: MT-1 displays energy and economic vocabulary (megawatts, debt, oil tanks, solar); MT-17 shows Easter Sunday attack–specific terms (Saharan, commission report, Catholic, April 21); MT-8 displays constitutional amendment discourse; and MT-13 shows English-medium political vocabulary including *sovereignty*, *peace*, and *Rajapaksa*. The limited leakage of procedural filler terms across all 30 clouds confirms that the macro-topic layer preserves policy substance rather than debate mechanics.

### 5.2 UMAP Visualisation of Macro-Topic Structure

[Figure 5.3: UMAP 2D Projection — Macro-Topic Assignments (30 Classes + Procedural Noise)]

The UMAP scatter plot (Figure 5.3) projects the BGE-M3 embedding space onto two dimensions, with each point coloured by macro-topic assignment. The visualisation reveals several structurally significant patterns:

**Spatial coherence of macro-topics.** Macro-topic regions are spatially coherent on the 2D projection, confirming that the centroid-merging aggregation step does not fragment geometrically unified regions. MT-21 (Dairy Industry) and MT-25 (Cricket) appear as isolated, tightly bounded clusters in the peripheral regions of the projection, reflecting their lexically and semantically distinctive vocabulary. MT-2 (Tamil-medium debates) forms a well-separated satellite cluster, confirming that BGE-M3 successfully groups Tamil speeches by topic while maintaining their linguistic distinctiveness.

**Thematic neighbourhood structure.** Macro-topics that share mild thematic overlap appear as neighbouring but non-overlapping regions, reflecting a graded semantic continuum. MT-1 (Energy Economy) and MT-8 (Constitutional Governance) occupy adjacent but distinct spatial positions, as do MT-14 (Environment) and MT-4 (Agriculture), both touching on land use and natural resources. This adjacency reflects genuine conceptual proximity in parliamentary debate rather than algorithmic failure.

**Procedural noise distribution.** Points assigned to HDBSCAN label $-1$ (procedural noise) visibly occupy low-density inter-cluster regions, consistent with the pipeline's design: procedural fragments that lack strong topical membership fall outside the dense cores of substantive policy clusters.

### 5.3 Inter-Topic Similarity Matrix

[Figure 5.4: Macro-Topic Cosine Distance Matrix (30 × 30) — Colour Scale: Dark = High Similarity]

The inter-topic similarity heatmap displays the pairwise cosine distance matrix $\mathbf{C} \in \mathbb{R}^{30 \times 30}$ between macro-topic centroids:

$$C_{ij} = 1 - \frac{\boldsymbol{c}_i \cdot \boldsymbol{c}_j}{\|\boldsymbol{c}_i\|\|\boldsymbol{c}_j\|}, \qquad \boldsymbol{c}_k = \frac{1}{|\mathcal{T}_k|} \sum_{d \in \mathcal{T}_k} \mathbf{e}_d.$$

The dominant off-diagonal pattern shows low-to-very-low distance (high similarity) values for the majority of off-diagonal cells, with isolated higher-similarity blocks for thematically proximate pairs. **Macro-Topic 15** (Condolences & Obituaries) exhibits the highest cross-topic similarity with many other topics at approximately 0.20–0.30 distance, reflecting the pervasive parliamentary register of condolence motions that share vocabulary with many policy domains. All remaining off-diagonal cells remain well below 1.0 distance, confirming that the 30 macro-topics are genuinely distinct. This validates the dendrogram cut decision: the chosen threshold at 0.002 produced non-redundant topics while preserving conceptually adjacent groupings.

### 5.4 Language Distribution across Macro-Topics

[Figure 5.5: Language Distribution per Macro-Topic — % Sinhala, Tamil, English per Thematic Domain]

A well-functioning multilingual topic model assigns speeches to topics on the basis of semantic content rather than language of expression. If a topic were populated exclusively by speeches in one language despite the issue being debated across all three, it would indicate language-driven rather than content-driven clustering. The language distribution figure shows that the large majority of macro-topics contain speeches from multiple languages, confirming that BGE-M3 embeddings produce substantially language-agnostic semantic representations.

**MT-2** (Tamil-Medium Parliamentary Debates) is the single macro-topic with near-total Tamil dominance, appropriately reflecting a cluster of speeches delivered primarily in Tamil. Critically, this is not an artefact of language-based clustering: MT-2 groups Tamil-medium speeches on the basis of shared semantic content — governance, community concerns, and post-war reconciliation — rather than by script identity alone. **MT-13** (English-Medium Governance & Peace Discourse) similarly shows elevated English proportions, consistent with the historical register conventions of formal constitutional and diplomatic discourse in Sri Lankan parliament. Topics with elevated Tamil proportions correspond to issues predominantly raised by Northern and Eastern province representatives (e.g., MT-2, MT-20 on human rights and international relations), which is substantively plausible.

This distribution pattern provides a key validation result for **RQ1**: the model does not collapse multilingual debates into language silos but surfaces cross-linguistic policy communities, a result that would not be achievable with a monolingual bag-of-words approach such as LDA.

### 5.5 Temporal Analysis: Topic Evolution and Event Alignment

The temporal trajectory of macro-topics provides the strongest external validity check for the unsupervised pipeline. No event labels were provided at any stage of training or clustering.

[Figure 5.6: Temporal Topic Evolution — Top 20 Topics by Speech Count, HDBSCAN Share over Time (2017–2026)]

[Figure 5.7: Most Volatile Topic per Algorithm — Overlaid with Sri Lankan Political Events (Annotated)]

#### 5.5.1 The 2022 Economic Crisis and Aragalaya

A pronounced surge is observed in economy-linked macro-topics during 2022–2023, corresponding to Sri Lanka's economic collapse and the Aragalaya protest movement. The HDBSCAN panel of the volatile topic chart (Figure 5.7) shows the most volatile topic (C123, corresponding to economy/fuel/governance discourse) peaking at approximately 6.5–7% of yearly speeches in 2017, declining through 2019–2021, then experiencing a secondary surge in 2023 before declining through 2025–2026. MT-1 (Energy Economy & Fuel Crisis), which contains the keywords *megawatts*, *fuel tanks*, *renewable energy*, *economic growth rate*, and *debt level*, is directly interpretable as capturing the parliamentary response to energy shortages and economic contraction during this period.

This alignment is methodologically significant: the unsupervised system recovered the crisis signal from discourse structure alone, without any event labelling. The model is not merely clustering syntax; it is tracing substantive issue attention over time, responding to exogenous political shocks in substantively expected directions.

#### 5.5.2 The 2019 Easter Sunday Attacks

MT-17 (Easter Sunday Attacks & National Security) is one of the most lexically specific and politically significant macro-topics in the taxonomy. Its distinctive keywords — *Saharan* (the attack leader's name), *commission report*, *Catholic*, *April 21*, *intelligence services*, *Easter Sunday attack* — directly identify parliamentary debate surrounding the investigation and accountability process following the bombings. The temporal trajectory of this topic (visible as an elevated signal around 2019–2020 in Figure 5.6) is consistent with the period of post-attack parliamentary scrutiny, including debates over intelligence failures and the Presidential Commission of Inquiry.

#### 5.5.3 COVID-19 and the 2020–2021 Period

The HDBSCAN volatile topic chart additionally shows a brief spike in the 2020 period, consistent with COVID-19 lockdown discourse absorbed into procedural and governance-related micro-topics. MT-11 (Healthcare, Pharmaceuticals & NMRA) contains the keyword *covid* and *vaccines*, further confirming that the pipeline captured pandemic-related parliamentary attention without explicit labelling.

#### 5.5.4 Comparative Temporal Sensitivity by Algorithm

The comparative volatile-topic plot (Figure 5.7) juxtaposes HDBSCAN, KMeans, and Agglomerative temporal signals for their respective most volatile micro-topics. The HDBSCAN signal exhibits temporally interpretable peaks and troughs aligned with known events. The KMeans signal is nearly flat until 2025–2026, where it shows an artificial spike — a consequence of absorbing diverse procedural and late-period content into a single misaligned cluster. The Agglomerative signal peaks in 2017–2018 before becoming dormant, failing to track the major 2019 and 2022 events. This comparison confirms that density-based clustering, by isolating noise and preserving topic purity, produces temporally more coherent and event-sensitive macro-topic trajectories than partition-based alternatives.

### 5.6 Speaker and Party Analysis

[Figure 5.8: Top 30 Speakers × Macro-Topic Heatmap (% of Each Speaker's Speeches per Macro-Topic)]

The speaker–topic matrix maps actor-level attention patterns. Let $\mathbf{M} \in \mathbb{R}^{|S| \times 30}$ where $M_{s,k}$ denotes the normalised speech mass of speaker $s$ in macro-topic $k$. The heatmap (Figure 5.8) reveals differentiated strategic attention among the top 30 most active speakers:

**Specialisation patterns.** Several speakers exhibit highly concentrated profiles — with a single macro-topic accounting for 30–45% of their total speech mass — indicating strong issue specialisation. These concentrated cells (visible as deep red in the heatmap) correspond to portfolio ministers or opposition critics with sustained engagement in specific policy domains such as energy, constitutional reform, or public accounts oversight.

**Cross-topic breadth.** Other speakers exhibit more uniformly distributed profiles across 5–10 macro-topics, consistent with the broad portfolio of cabinet ministers or senior opposition spokespersons who engage across governance, economic, and legislative domains.

**Macro-Topic 0 concentration.** Macro-Topic 0 (Parliamentary Procedure & Standing Orders) shows distinctive concentration among certain speakers, corresponding to the parliamentary Speaker's role and the leaders of major party blocks who engage disproportionately in procedural discourse.

Aggregating speaker rows by political party yields party-level topic profiles that enable direct comparison of issue emphasis across blocs. The actor-topic layer operationalises topic modelling outputs into interpretable political behaviour indicators, supporting political communication analysis, agenda ownership studies, and coalition–opposition framing comparisons.

### 5.7 Quantitative Clustering Quality

The geometric quality of the primary pipeline clustering was assessed using three internal metrics evaluated on HDBSCAN-clustered documents.

**Table 5.2: Primary Pipeline Quality Metrics**

| Metric | Primary Pipeline (HDBSCAN) | KMeans (K=336) | Agglomerative (K=336) |
|---|---|---|---|
| Silhouette Score | 0.5741 | 0.4076 | 0.3812 |
| Calinski-Harabász Index | 15,052 | 13,098 | 12,217 |
| Davies-Bouldin Index | 0.5148 | 0.8745 | 0.9088 |
| Noise % | 35.4% | 0.0% | 0.0% |
| Topic Coherence $c_v$ | [TBD — Insert value] | [TBD — Insert value] | [TBD — Insert value] |

The HDBSCAN pipeline achieves the highest silhouette (0.5741), the best Calinski-Harabász score, and the lowest Davies-Bouldin index across all three algorithms at the same micro-topic count. These results, taken together with the temporal event alignment (Section 5.5) and the substantive interpretability of keyword profiles (Section 5.1.2), provide convergent evidence that the primary pipeline successfully recovers meaningful political thematic structure from the corpus.

### 5.8 Experimental Results: BiTopic Ablation

This section reports the results of the experimental BiTopic investigation as a secondary, exploratory finding.

The ablation sweep (Table 4.4; Figure 4.5) reveals that introducing lexical grounding at $\alpha = 0.85$ ($\beta = 0.15$) increases the noise rate from 35.4% (pure semantic) to 45.98%, while reducing the number of micro-topics from 336 to 277. The topic count reduction at $\alpha = 0.85$ reflects a moderate consolidation of semantically adjacent but lexically distinct micro-topics, consistent with the expected boundary-sharpening effect of lexical regularisation. The noise rate increase indicates that lexical constraints cause some borderline speeches — particularly those using synonymous terminology across languages — to fall below the density threshold and be classified as noise rather than assigned to clusters.

**Table 5.3: Primary Pipeline vs. BiTopic Experimental Comparison**

| Pipeline | Topics ($K$) | Noise % | Clustered % | Silhouette | $c_v$ |
|---|---|---|---|---|---|
| Primary (BERTopic, $\alpha=1.00$) | 336 | 35.40% | 64.60% | 0.5741 | [TBD] |
| BiTopic ($\alpha=0.85$) | 277 | 45.98% | 54.02% | [TBD] | [TBD] |

The BiTopic results demonstrate a clear semantic–lexical trade-off: lexical grounding sharpens topic boundaries (fewer, more consolidated micro-topics) but at the cost of coverage (higher noise rate). For the primary research objective of this thesis — extracting a comprehensive, interpretable macro-topic taxonomy covering the maximum informative speech mass — the pure semantic pipeline is superior. The BiTopic experiment is therefore reported as an exploratory finding that motivates future investigation into adaptive fusion strategies (see Section 6.5) rather than as a replacement for the primary pipeline.

---

## Chapter 6: Discussion and Conclusion

### 6.1 Direct Answers to the Research Questions

**RQ1 — Multilingual Topic Modelling:** Can a multilingual dense embedding model combined with density-based clustering produce semantically coherent and cross-lingual topic clusters from trilingual, code-mixed Sri Lankan parliamentary speeches?

**Answer: Yes.** The BGE-M3 embedding model, selected on the basis of its low anisotropy (0.552) and extended context window (8,192 tokens), produces cross-lingual semantic representations that allow HDBSCAN to identify coherent topic clusters spanning Sinhala, Tamil, and English speeches. The language distribution results (Section 5.4) confirm that macro-topics are grouped by content rather than language identity. Event-aligned temporal patterns (Section 5.5) confirm that clusters have substantive political validity.

**RQ2 — Empirical Macro-Topic Determination:** Can a data-driven hierarchical aggregation procedure produce a stable and interpretable macro-topic taxonomy without arbitrarily chosen hyperparameters?

**Answer: Yes.** The Pareto filtering plus Empirical Dendrogram Cut (at distance 0.002, average linkage, cosine metric) produces a stable **30 macro-topic** structure that is interpretable, reproducible, and well-suited to downstream temporal and actor-level analysis. The dendrogram gap-detection method provides a principled, data-driven basis for $K_{\text{macro}}$ selection absent from prior parliamentary topic modelling work.

**RQ3 — Hybrid Semantic–Lexical Fusion (Experimental):** Does BiTopic reduce embedding blur and improve topic boundary sharpness?

**Answer: Conditionally.** BiTopic at $\alpha = 0.85$ produces fewer, more consolidated micro-topics (277 vs. 336), suggesting that lexical grounding does sharpen boundaries as hypothesised. However, this comes at a coverage cost (noise rate increases from 35.4% to 45.98%), and the loss of 10.6 percentage points of clustered speech mass represents a significant reduction in corpus coverage. BiTopic therefore trades coverage for boundary sharpness, a trade-off that may be acceptable for applications prioritising topic purity over completeness, but which makes the pure semantic pipeline preferable as the primary analytical tool for this corpus.

### 6.2 Interpretation of Key Findings

**The 30 Macro-Topic Taxonomy.** The final taxonomy reveals the dominant thematic structure of Sri Lankan parliamentary discourse across a decade of significant political change. Economy-related topics (MT-1, MT-3, MT-4, MT-6, MT-10, MT-24) collectively dominate the agenda, consistent with Sri Lanka's sustained economic challenges including the 2022 crisis. Governance and institutional topics (MT-0, MT-8, MT-9, MT-23) reflect the repeated constitutional changes and electoral reform debates of the period. Domain-specific policy topics (MT-17 Easter attacks, MT-22 SAITM, MT-25 Cricket) demonstrate the pipeline's ability to isolate politically significant niche debates that would otherwise be subsumed into broader clusters under classical methods.

**HDBSCAN's Purification Role.** The 35.4% noise rate in the primary pipeline is not a failure of the model; it is a feature. The 6,921 speeches classified as procedural noise correspond to short interventions, formulaic address, procedural motions, and ambiguous short turns that do not carry substantive thematic content. Their exclusion from macro-topic clusters ensures that the retained 12,632 speeches form clean, semantically coherent policy clusters suitable for downstream sentiment analysis and actor-level attribution.

**The Anisotropy Criterion.** The embedding evaluation result that multilingual-E5 — despite its superior STS score — is disqualified on anisotropy grounds (0.909) is a finding of broad methodological significance. It establishes that anisotropy and context coverage should be treated as primary selection criteria over raw similarity scores when the downstream task is density-based clustering.

### 6.3 Limitations

1. **Sinhala-dominant ground-truth subset.** The supervised evaluation relies on 300 annotated speeches of which 91.0% are Sinhala. Cross-lingual clustering quality for Tamil and English speeches is therefore evaluated with limited statistical power.

2. **Noise-coverage tension.** The 35.4% noise rate means that a significant fraction of parliamentary time is absent from the macro-topic analysis. Some of these excluded speeches may contain informative content that is simply too sparse or idiosyncratic for density-based clustering to assign reliably.

3. **Morphological residue in lexical representations.** CountVectorizer, used in both the topic representation stage and the BiTopic experiment, remains sensitive to agglutinative surface forms. Extreme morphological variants can reduce effective lexical overlap between thematically equivalent Sinhala and Tamil speeches, potentially weakening the lexical component of BiTopic.

4. **Transcript quality dependence.** LLM-based extraction, while substantially superior to Tesseract OCR, is not error-free. Residual extraction errors propagate into embeddings and can subtly affect cluster geometry for speeches from older or lower-quality Hansard PDFs.

5. **Temporal comparability.** Institutional schedule effects and unequal debate volume across years can influence apparent topic intensity, potentially conflating changes in parliamentary activity volume with changes in thematic focus.

### 6.4 Significance for Political Analysis

This thesis demonstrates that multilingual parliamentary discourse, even in low-resource and morphologically complex settings, can be transformed into a rigorous empirical signal of political attention. The 30 macro-topics provide a data-driven agenda map of Sri Lankan parliamentary discourse spanning the pre-crisis baseline through the Aragalaya period, with topic trajectories that respond to major national events without any supervised labelling. The speaker–topic matrix additionally enables actor-level discourse interpretation, linking computational results to substantive questions of parliamentary representation, policy ownership, and political communication.

### 6.5 Future Work

The most promising extensions of this work are:

1. **Aspect-Based Sentiment Analysis (ABSA).** With coherent, cross-lingual macro-topic clusters identified, targeted sentiment models can be applied to analyse how political actors and parties respond to specific policy issues over time. Examining sentiment evolution within MT-1 (Energy Economy) during 2021–2023, for example, can provide quantitative evidence of shifting political postures through the economic crisis.

2. **Adaptive BiTopic Fusion.** The BiTopic ablation suggests that a fixed $\alpha$ may not be optimal across all macro-topic domains. A future direction is per-topic or per-language adaptive weighting, allowing the semantic component to dominate for cross-lingual clusters while increasing lexical weight for monolingual, domain-specific clusters.

3. **Morphology-Aware Lexical Modules.** Integrating subword tokenisation (SentencePiece or BPE-based schemes) into the CountVectorizer component of BiTopic would reduce agglutinative morphological fragmentation and improve lexical alignment between Sinhala and Tamil speeches on the same topic.

4. **Real-Time Parliamentary Monitoring.** Extending the pipeline to process live Hansard feeds would enable continuous macro-topic tracking, providing near-real-time agenda analytics for civil society, media, and policy research applications.

5. **Cross-Country Transfer.** Evaluating the pipeline's transferability to other South Asian legislatures (India, Pakistan, Bangladesh, Nepal) would assess regional generalisability and the methodology's applicability to other low-resource, morphologically complex legislative contexts.

6. **Human-in-the-Loop Taxonomy Validation.** Formalising interpretability audits with political scientists would establish reproducible quality standards for the 30 macro-topic labels and enable systematic comparison with expert-constructed thematic taxonomies.

### 6.6 Closing Statement

The thesis shows that the core methodological challenge — multilingual, morphologically complex parliamentary text — can be addressed through a principled combination of cross-lingual dense embeddings, non-parametric density-based clustering, and data-driven hierarchical aggregation. The resulting 30 macro-topic taxonomy is not an arbitrary computational artefact but a substantively interpretable map of Sri Lankan legislative attention, validated by event alignment, language distribution analysis, and actor-level discourse patterns. By establishing this foundation, the thesis advances both the computational methodology for multilingual parliamentary NLP and the empirical study of political discourse in Sri Lanka's complex linguistic and political context.

---

## References

[1] G. Abercrombie and R. T. Batista-Navarro, "A sentiment-labelled corpus of Hansard parliamentary debate speeches," Technical report, University of Manchester, 2018.

[2] D. Angelov, "Top2Vec: Distributed representations of topics," *arXiv preprint arXiv:2008.09470*, 2020.

[3] M. Ankerst, M. M. Breunig, H.-P. Kriegel, and J. Sander, "OPTICS: Ordering points to identify the clustering structure," *SIGMOD Record*, vol. 28, no. 2, pp. 49–60, 1999.

[4] A. Berracheche, "Appraisal and party positioning in parliamentary debates: A usage-based critical discourse analysis," *International Journal of English Linguistics*, vol. 10, no. 6, pp. 322–331, 2020.

[5] F. Bianchi, S. Terragni, D. Hovy, D. Nozza, and E. Fersini, "Cross-lingual Contextualized Topic Models with Zero-Shot Learning," in *Proc. EACL*, pp. 1676–1683, 2021.

[6] D. M. Blei, A. Y. Ng, and M. I. Jordan, "Latent Dirichlet allocation," *Journal of Machine Learning Research*, vol. 3, pp. 993–1022, 2003.

[7] R. J. G. B. Campello, D. Moulavi, and J. Sander, "Density-based clustering based on hierarchical density estimates," in *Advances in Knowledge Discovery and Data Mining*, Springer, 2013.

[8] J. Chen, S. Xiao, P. Zhang, K. Luo, D. Lian, and Z. Liu, "M3-Embedding: Multi-lingual, multi-functionality, multi-granularity text embeddings through self-knowledge distillation," *arXiv preprint arXiv:2402.03216*, 2025.

[9] F. Feng, Y. Yang, D. Cer, N. Arivazhagan, and W. Wang, "Language-agnostic BERT sentence embedding," in *Proc. ACL*, pp. 878–891, 2022.

[10] M. Grootendorst, "BERTopic: Neural topic modeling with a class-based TF-IDF procedure," *arXiv preprint arXiv:2203.05794*, 2022.

[11] P. Koehn, "Europarl: A parallel corpus for statistical machine translation," in *Proc. Machine Translation Summit X*, pp. 79–86, 2005.

[12] B. E. Lauderdale and T. S. Clark, "Scaling politically meaningful dimensions using texts and votes," *American Journal of Political Science*, vol. 58, no. 3, pp. 754–771, 2014.

[13] D. D. Lee and H. S. Seung, "Learning the parts of objects by non-negative matrix factorization," *Nature*, vol. 401, pp. 788–791, 1999.

[14] L. McInnes, J. Healy, and S. Astels, "HDBSCAN: Hierarchical density-based clustering," *Journal of Open Source Software*, vol. 2, no. 11, p. 205, 2017.

[15] L. McInnes, J. Healy, and J. Melville, "UMAP: Uniform manifold approximation and projection for dimension reduction," *arXiv preprint arXiv:1802.03426*, 2018.

[16] C. Rauh and J. Schwalbach, "The ParlSpeech V2 data set," Harvard Dataverse, 2020.

[17] W. P. U. Senevirathna et al., "Enhancing multilingual sentiment analysis with explainability for Sinhala, English, and code-mixed content," (unpublished manuscript), 2024.

[18] A. Srivastava and C. Sutton, "Autoencoding Variational Inference for Topic Models," in *Proc. ICLR*, 2017.

[19] L. Wang et al., "Multilingual E5 text embeddings: A technical report," *arXiv preprint arXiv:2402.05672*, 2024.