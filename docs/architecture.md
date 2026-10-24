# Architecture — Bilingual Citizen Services AI Assistant

## System Overview

```
                        ┌─────────────────────────────────────────┐
                        │           Streamlit Frontend             │
                        │   (Bangla / English / Banglish input)    │
                        └──────────────────┬──────────────────────┘
                                           │ POST /api/v1/chat
                        ┌──────────────────▼──────────────────────┐
                        │         FastAPI Backend (main.py)        │
                        │   Request validation · CORS · Routing    │
                        └──────────────────┬──────────────────────┘
                                           │
                        ┌──────────────────▼──────────────────────┐
                        │        LangGraph RAG Workflow            │
                        │                                          │
                        │  ┌────────────────────────────────────┐ │
                        │  │      analyze_query (Node 1)         │ │
                        │  │  Language detect · Category · Intent│ │
                        │  └───────────────┬────────────────────┘ │
                        │                  │                       │
                        │  ┌───────────────▼────────────────────┐ │
                        │  │       retrieve (Node 2)             │ │
                        │  │  BM25 ──┐                           │ │
                        │  │         ├── RRF Fusion ── Reranker  │ │
                        │  │  Dense ─┘                           │ │
                        │  └───────────────┬────────────────────┘ │
                        │                  │                       │
                        │  ┌───────────────▼────────────────────┐ │
                        │  │   evaluate_evidence (Node 3)        │ │
                        │  │  Score · Freshness · Conflicts      │ │
                        │  └────────┬──────────────┬────────────┘ │
                        │           │ sufficient    │ insufficient  │
                        │  ┌────────▼────────┐ ┌───▼────────────┐ │
                        │  │ generate_answer │ │   fallback     │ │
                        │  │  (Node 4a)      │ │   (Node 4b)    │ │
                        │  └────────┬────────┘ └───┬────────────┘ │
                        └──────────┬───────────────┬──────────────┘
                                   └───────┬────────┘
                        ┌──────────────────▼──────────────────────┐
                        │        JSON Response to User             │
                        │  answer · language · status · citations  │
                        └─────────────────────────────────────────┘
```

## Component Detail

### 1. Ingestion Pipeline

```
Official Sources (HTML / PDF / JSON)
           │
           ▼
    loaders.py ──── HTMLLoader / PDFLoader / JSONFAQLoader
           │
           ▼
    parsing.py ──── Unicode NFC normalization
                    Control char removal
                    Language detection
                    Page reference extraction
           │
           ▼
    chunking.py ─── Recursive character splitting (512 chars, 80 overlap)
                    Sentence-boundary aware (Bangla danda + English punctuation)
                    Chunk metadata: doc_id, title, url, page, language
           │
     ┌─────┴──────┐
     ▼            ▼
BM25Index    DenseIndex (ChromaDB + BGE-M3)
```

### 2. Query-Time Pipeline

| Step | Component | What happens |
|------|-----------|--------------|
| 1 | `analyze_query` | Detect language (bn/en/mixed), classify category and intent |
| 2 | `bm25.retrieve()` | BM25Okapi scores top-20 chunks by keyword match |
| 3 | `dense_search.retrieve()` | BGE-M3 embeds query; ChromaDB ANN search top-20 |
| 4 | `fusion.rrf()` | Reciprocal Rank Fusion merges both ranked lists |
| 5 | `reranker.rerank()` | BGE-reranker-v2-m3 cross-encoder re-scores top-N |
| 6 | `evaluate_evidence` | Score threshold check, freshness, conflict detection |
| 7a | `generate_answer` | Gemini generates grounded answer from passages |
| 7b | `fallback` | Honest "cannot confirm" message in correct language |

### 3. Hybrid Retrieval: Why Both BM25 and Dense?

| Query type | BM25 wins | Dense (BGE-M3) wins |
|---|---|---|
| Exact form numbers ("Form-1", "SRO 219") | ✅ | Partial |
| Administrative acronyms ("NID", "TIN", "DIP") | ✅ | ✅ |
| Semantic questions ("how to change my name") | Partial | ✅ |
| Bangla + English mixed queries | ✅ (tokenised) | ✅ (multilingual) |
| Paraphrases ("renew" vs "extend" vs "নবায়ন") | ❌ | ✅ |

RRF ensures both signals contribute without requiring score calibration between them.

### 4. Evidence Evaluation Logic

```python
sufficient = (top_reranker_score >= EVIDENCE_THRESHOLD)
# EVIDENCE_THRESHOLD default: 0.40
# Calibrate on validation dataset — do not treat 0.40 as universal truth
```

Additional checks:
- **Fee queries** without source dates → add limitation warning
- **Multiple source dates** → flag potential superseded content
- **No passages at all** → immediate fallback

### 5. AI Safety Measures

1. **Prompt injection guard**: Instructions embedded in source documents are treated as evidence content, not system commands
2. **Evidence-only generation**: System prompt requires every factual claim to be traceable to a retrieved passage
3. **No URL fabrication**: Only URLs from the metadata store are cited
4. **Fallback over hallucination**: Threshold triggers honest "cannot confirm" instead of guessing
5. **Citation extraction**: Only passages explicitly cited (or top-3) appear as citations

### 6. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Streamlit | 1.40.x |
| Backend | FastAPI + Uvicorn | 0.115.x |
| Workflow | LangGraph | 0.2.x |
| Sparse retrieval | rank-bm25 (BM25Okapi) | 0.2.x |
| Dense embeddings | BAAI/bge-m3 (FlagEmbedding) | 1.3.x |
| Reranking | BAAI/bge-reranker-v2-m3 | 1.3.x |
| Vector store | ChromaDB (persistent) | 0.5.x |
| LLM | Google Gemini (gemini-3.8-flash) | genai ≥2.30 |
| Evaluation | Ragas + custom dataset | 0.2.x |
| Containerisation | Docker + Compose | v3 |

## Data Flow Diagram

```
User query (Bangla/English/Banglish)
    │
    ▼
FastAPI validates input (Pydantic schema)
    │
    ▼
LangGraph: analyze_query
    ├── langdetect → 'bn' | 'en' | 'mixed'
    ├── regex patterns → category: passport|nid|tin|general
    └── regex patterns → intent: procedure|document|fee|general
    │
    ▼
LangGraph: retrieve
    ├── BM25 (rank_bm25) → 20 candidates (keyword match)
    ├── BGE-M3 + ChromaDB → 20 candidates (semantic match)
    ├── RRF fusion (k=60) → merged ranked list
    └── BGE-reranker-v2-m3 → top 5 passages + scores
    │
    ▼
LangGraph: evaluate_evidence
    ├── score[0] >= 0.40? → sufficient
    ├── fee intent + no date? → add limitation
    └── multiple dates? → add conflict warning
    │
    ├─── sufficient ──▶ generate_answer
    │                       ├── Build prompt with passages
    │                       ├── Gemini API (gemini-3.8-flash)
    │                       └── Extract [src-N] citations
    │
    └─── insufficient ──▶ fallback
                            └── Return FALLBACK_BANGLA or FALLBACK_ENGLISH
    │
    ▼
FastAPI serializes ChatResponse
    │
    ▼
Streamlit renders: answer + citations panel + limitations
```

