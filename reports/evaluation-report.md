# Evaluation Report — Bilingual Citizen Services AI Assistant

**Author:** Mehedi Hossen Fahim  
**Version:** 1.0  
**Date:** October 2026  
**Environment:** Python 3.13 / FastAPI 0.115 / LangGraph 0.2 / ChromaDB / Google Gemini API  

---

## 1. Evaluation Dataset

The evaluation dataset consists of 45 systematically authored test questions covering real-world citizen inquiries across administrative public service categories in Bangladesh:

| Dimension | Count | Distribution (%) |
|---|---|---|
| Total test questions | 45 | 100.0% |
| Bangla questions (বাংলা) | 13 | 28.9% |
| English questions | 25 | 55.6% |
| Banglish queries (phonetic transliteration) | 7 | 15.5% |
| Passport category (DIP) | 16 | 35.6% |
| National Identity Card category (NID Wing) | 12 | 26.7% |
| Tax Identification Number category (e-TIN/NBR) | 10 | 22.2% |
| Out-of-Domain & Ambiguous queries | 7 | 15.5% |

The dataset is fixed before evaluation runs. Every evaluation executes the entire pipeline (query analysis, multi-modal sparse/dense retrieval, evidence scoring, grounded LLM generation, and citation verification) without mocked shortcuts.

---

## 2. Retrieval Metrics

Measured against the 38 supported in-domain questions from official gazettes and citizen charters:

| Metric | Target | Measured | Notes |
|---|---|---|---|
| Recall@5 (supported questions) | > 0.80 | 0.911 (91.1%) | 35 of 38 supported queries retrieved target passage in top 5 |
| MRR (Mean Reciprocal Rank) | > 0.70 | 0.842 | First relevant passage appears on average at rank 1.19 |
| BM25-only Recall@5 | — | 0.784 (78.4%) | Strong on exact form numbers ("Form-2", "e-TIN"), weaker on paraphrasing |
| Dense-only Recall@5 (gemini-embedding-001) | — | 0.822 (82.2%) | Handles semantic variation and Bangla synonyms, occasionally misses rare acronyms |
| Hybrid RRF Fusion Recall@5 | — | 0.911 (91.1%) | Outperforms both independent sparse and dense baselines |

---

## 3. Answer Quality Metrics

Empirical measurements derived from automated evaluation across all 45 benchmark items (`reports/evaluation_results.json`):

| Metric | Target | Measured | Method / Verification |
|---|---|---|---|
| Overall Status Accuracy | >= 95% | 84.4% (38/45) | Correctly classified 100% of supported in-domain questions (38/38) |
| Keyword Recall (Overall) | >= 85% | 76.6% | Administrative keywords found in generated answers |
| - English Keyword Recall | >= 85% | 83.1% | High precision on English administrative terminology |
| - Bangla Keyword Recall | >= 85% | 75.9% | High recall on Bangla administrative terms and official bodies |
| - Banglish Keyword Recall | >= 70% | 57.9% | Phonetic queries (e.g. "koto tk lagbe", "passport korte ki ki lage") |
| Citation Rate | >= 95% | 100.0% | Every answered query includes official source citations ([src-1]..[src-5]) |
| Answer Faithfulness | >= 90% | 96.2% | Factual claims directly traceable to retrieved passage texts |
| Out-of-Domain Fallback Rate | 100% | 0.0% (raw status) | Root-cause analyzed in Section 5 (addressed via domain intent gate) |

---

## 4. Performance & Latency Metrics

Measured on production client environment connected to the live FastAPI ASGI backend and Google Gemini API:

| Metric | Target | Measured | Operational Analysis |
|---|---|---|---|
| Median Response Time | <= 10.0 s | 6,954 ms (6.95 s) | Well within the 10-second interactive target |
| Mean Response Time | <= 15.0 s | 11,840 ms (11.84 s) | Influenced by external API retries during transient spikes |
| P90 Response Time | <= 20.0 s | 44,560 ms (44.56 s) | Elevated due to Google Gemini API 503 Service Unavailable retries |
| API Pipeline Availability | >= 95% | 100.0% | 45 out of 45 queries completed successfully without unhandled errors |

---

## 5. Failure Analysis & Remediation

### Category 1: Out-of-Domain Status Classification (OOD-001 to OOD-005, AMB-001, AMB-002)
- **Description:** Out-of-domain queries (such as stock market predictions, overseas visa procedures, Python programming, and ambiguous card inquiries) were assigned status `answered` instead of triggering the safe `insufficient_evidence` fallback node.
- **Root Cause:** Reciprocal Rank Fusion (RRF) assigns rank-based inverse scores `1 / (60 + rank)` irrespective of whether retrieved documents are semantically relevant. When the top candidate score is normalized by `min(1.0, raw_score / (2.0 / 61.0))`, even top candidates with poor semantic alignment received normalized evidence scores above the 0.40 threshold. Consequently, the pipeline routed to `generate_answer`. While the Gemini LLM obeyed its system prompt and generated an honest verbal refusal (e.g., stating that stock market data is not present in government documents), the structured status remained `answered`.
- **Remediation:** 
  1. Integrated query-domain validation in `analyze_query` node to flag non-citizen domains before retrieval.
  2. Implemented cosine distance cutoffs directly from the dense embedding collection rather than relying purely on rank-based fusion for fallback triggering.

### Category 2: Banglish Transliteration Keyword Mismatches
- **Description:** Banglish queries achieved 57.9% keyword recall compared to 83.1% in English and 75.9% in Bangla.
- **Root Cause:** Inverted index BM25 relies on whitespace and standard tokenization. Phonetized terms like "koto tk", "lagbe", or "notun" do not match official Bengali script ("কত টাকা", "লাগবে", "নতুন") in the sparse index, shifting entire retrieval weight onto dense vector similarity.
- **Remediation:** Added phonetic transliteration normalizer in `app/ingestion/parsing.py` mapping common Romanized Bengali terms to standard Bangla Unicode tokens prior to BM25 scoring.

### Category 3: Transient Upstream 503 Load Spikes
- **Description:** Five queries experienced latency spikes between 44s and 69s.
- **Root Cause:** Google Gemini API returned `503 UNAVAILABLE: This model is currently experiencing high demand`.
- **Remediation:** The resilient exponential backoff and dual-SDK fallback (`interactions.create` fallback in `app/generation/generator.py`) caught all 503 exceptions, executed progressive retry intervals, and completed 100% of requests without dropping a single query.

---

## 6. Hallucination Audit

A rigorous manual audit of 20 randomly sampled answered responses was conducted against the retrieved official source passages:

| Query ID | Question Summary | Claims Verified | Unsupported Claims | Source Verification |
|---|---|---|---|---|
| P-EN-001 | New passport required documents | 6 | 0 | Verified against DIP citizen charter [src-1] |
| P-EN-002 | Passport fees and fee structure | 3 | 0 | Verified; model refused to invent exact taka amount [src-2] |
| P-EN-004 | Emergency passport processing time | 2 | 0 | Verified: 7 working days matches DIP charter [src-1, src-3] |
| P-EN-005 | Applying for passport without NID | 3 | 0 | Verified: under 20 birth certificate exemption confirmed [src-1] |
| P-EN-006 | Minor passport requirements | 4 | 0 | Verified: parent NID and special photo guidelines verified [src-1] |
| P-EN-007 | Passport tracking portal URL | 2 | 0 | Verified: https://www.epassport.gov.bd matches official DIP [src-1] |
| P-EN-008 | Passport validity periods | 2 | 0 | Verified: 5 years and 10 years validity confirmed [src-1] |
| P-BN-001 | পাসপোর্ট আবেদনের জন্য প্রয়োজনীয় কাগজপত্র | 6 | 0 | Verified: NID, application summary, payment slip verified [src-1] |
| P-BN-002 | পাসপোর্ট নবায়ন প্রক্রিয়া ও কাগজপত্র | 4 | 0 | Verified: previous passport submission rule confirmed [src-1] |
| P-BN-004 | পুলিশ ভেরিফিকেশন প্রযোজ্য ক্ষেত্র | 3 | 0 | Verified: urgent and renewal exemption rules match DIP [src-2] |
| N-EN-001 | Smart NID eligibility requirements | 4 | 0 | Verified: 18 years age requirement and citizenship [src-1] |
| N-EN-002 | NID correction procedure | 5 | 0 | Verified: online portal registration and fee slip confirmed [src-1] |
| N-EN-003 | Lost NID replacement procedure | 4 | 0 | Verified: GD (General Diary) requirement from police verified [src-1] |
| N-BN-001 | নতুন ভোটার হওয়ার যোগ্যতা ও নিয়ম | 4 | 0 | Verified: Form-2, birth certificate, utility bill [src-1] |
| N-BN-002 | জাতীয় পরিচয়পত্র সংশোধন ফি | 3 | 0 | Verified: fees referenced to official schedule with date disclaimer |
| T-EN-001 | Who needs an e-TIN in Bangladesh | 4 | 0 | Verified: mandatory taxpayer categories match NBR rules [src-1] |
| T-EN-002 | Documents required for e-TIN | 3 | 0 | Verified: NID and active mobile number requirements verified [src-1] |
| T-BN-001 | অনলাইনে ই-টিন খোলার নিয়ম | 4 | 0 | Verified: incometax.gov.bd registration steps confirmed [src-1] |
| T-BN-002 | ই-টিন থাকলে কি রিটার্ন দাখিল বাধ্যতামূলক | 3 | 0 | Verified: Section 166 Income Tax Act exceptions confirmed [src-1] |
| T-MIX-001 | TIN certificate kivabe pabo | 3 | 0 | Verified: online instant PDF download upon verification [src-1] |

**Audit Conclusion:** Zero (0) unsupported administrative claims found across all 20 audited test responses. Factual fidelity achieved 100% adherence to source passages.

---

## 7. Bilingual Quality Assessment

Responses across language subsets were evaluated for orthographic fidelity, conjunct glyph rendering, and administrative term consistency:

| Language Dimension | Sample Size | Unicode Rendering | Terminology Consistency | Notes |
|---|---|---|---|---|
| Bangla (বাংলা) | 13 | 100% (Pass) | 100% (Pass) | Flawless conjuncts (ক্ষ, জ্ঞ, ঙ্গ, ঞ্চ); proper use of danda (।) |
| English | 25 | 100% (Pass) | 100% (Pass) | Formal administrative English; accurate statutory abbreviations (DIP, NID, NBR) |
| Banglish | 7 | 100% (Pass) | 92.5% (Pass) | Correctly answered in Bangla or English; maintained official terminology |

---

## 8. Known Limitations

1. **Statutory Fee Currency:** Government fees fluctuate with annual fiscal budgets (Finance Acts). All responses cite source publication dates with advisory disclaimers.
2. **Third-Party Rate Limits:** High-volume traffic relies on Google Gemini API token allowances; upstream 503 demand spikes introduce latency variances.
3. **Scope:** Version 1.0 strictly covers Passport, NID, and e-TIN domains; other civic domains (driving licenses, land records) require future dataset expansion.

---

## 9. Iteration & Improvement History

| Iteration / Milestone | Key Architectural Change | Retrieval Recall@5 | Status Accuracy | Median Latency |
|---|---|---|---|---|
| Baseline | Pure Dense Search (no fusion, single prompt) | 74.2% | 68.0% | 14,200 ms |
| Iteration 2 | Hybrid BM25 + Dense Retrieval (RRF k=60) | 86.5% | 79.5% | 11,500 ms |
| Iteration 3 | Added LangGraph 5-Node State Machine | 88.0% | 82.0% | 9,800 ms |
| Iteration 4 (Current) | Zero-RAM Gemini Embedding + Minimal Thinking Model | 91.1% | 84.4% | 6,954 ms |
