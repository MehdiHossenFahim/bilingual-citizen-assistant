# Evaluation Report — Bilingual Citizen Services AI Assistant

**Version:** 1.0  
**Date:** October 2026  
**Status:** Template — fill with actual measured results after running evaluation

---

## 1. Evaluation Dataset

| Dimension | Count |
|-----------|-------|
| Total questions | 42 (expandable to 100+) |
| Bangla questions | 14 |
| English questions | 16 |
| Banglish questions | 8 |
| Out-of-domain (must fallback) | 5 |
| Ambiguous queries | 2 |
| Passport category | 16 |
| NID category | 12 |
| TIN category | 10 |
| General/OOD | 7 |

The dataset is fixed before tuning. After any change to prompts, embeddings, thresholds, or models, the same dataset is re-evaluated.

---

## 2. Retrieval Metrics

Run `python -m app.evaluation.evaluator` and fill in results below.

| Metric | Target | Measured | Notes |
|--------|--------|---------|-------|
| Recall@5 (supported questions) | > 0.80 | ___ | Fraction of questions with at least one correct passage in top 5 |
| MRR (Mean Reciprocal Rank) | > 0.70 | ___ | Measures average rank of first correct passage |
| BM25-only Recall@5 | — | ___ | Baseline comparison |
| Dense-only Recall@5 | — | ___ | Baseline comparison |
| RRF+Reranker Recall@5 | — | ___ | Should exceed both baselines |

---

## 3. Answer Quality Metrics

| Metric | Target | Measured | Method |
|--------|--------|---------|--------|
| Status accuracy | ≥ 95% | ___ | Correct answered/fallback classification |
| Keyword recall | ≥ 85% | ___ | Expected admin terms found in answer |
| Citation rate | ≥ 95% | ___ | Valid source cited in answered responses |
| Fallback rate on OOD | 100% | ___ | All out-of-domain questions return fallback |
| Answer faithfulness | ≥ 90% | ___ | Claims traceable to retrieved passages |

---

## 4. Performance Metrics

Measured on: [hardware], [hosting tier], [model provider]

| Metric | Target | Measured |
|--------|--------|---------|
| Median response time | ≤ 10 s | ___ |
| P90 response time | ≤ 20 s | ___ |
| API availability (test run) | ≥ 95% | ___ |

---

## 5. Failure Analysis

### Category: Retrieval failures

Document: [failure description]
Root cause: [e.g., Bangla OCR quality, chunking too large]
Fix applied: [e.g., smaller chunk size, additional sources]

### Category: Generation failures

Document: [failure description]
Root cause: [e.g., threshold too low, conflicting sources]
Fix applied: [e.g., threshold calibration, date filtering]

### Category: Fallback failures (answered when should have fallen back)

Document: [failure description]

---

## 6. Hallucination Audit

**Methodology**: Manually review 20 randomly selected answered responses.  
For each response, check that every factual administrative claim appears in the cited source passage.

| Response ID | Claims verified | Unsupported claims | Notes |
|-------------|----------------|-------------------|-------|
| (fill after review) | | | |

**Target**: Zero unsupported administrative claims in the audited set.

---

## 7. Bilingual Quality Assessment

Sample responses in each language category were reviewed for:
- Correct Bangla Unicode rendering
- Preservation of form numbers and government abbreviations
- Consistent terminology across Bangla and English responses

| Language | Sample size | Rendering OK | Terminology OK |
|----------|-------------|-------------|----------------|
| Bangla | ___ | ___ | ___ |
| English | ___ | ___ | ___ |
| Banglish | ___ | ___ | ___ |

---

## 8. Known Limitations

1. **Fee data currency**: Fee schedules change with annual budgets. The system adds a caveat for fee information but cannot automatically verify whether a source is current.
2. **Bangla PDF quality**: Some official documents have poor OCR quality; text extraction may miss characters.
3. **Banglish normalisation**: Banglish queries (transliterated Bangla) rely on tokenisation; semantic retrieval quality may be lower than pure Bangla or English.
4. **Scope**: Only Passport, NID, and TIN services are covered in v1.0.
5. **Hallucination disclaimer**: Zero hallucinations on the audited test set does not guarantee zero hallucinations in production.

---

## 9. Improvement History

| Date | Change | Retrieval Recall@5 | Status Accuracy |
|------|--------|-------------------|-----------------|
| Baseline | Initial system | ___ | ___ |
| After threshold tuning | Evidence threshold adjusted | ___ | ___ |
| After reranker addition | CrossEncoder reranker enabled | ___ | ___ |

