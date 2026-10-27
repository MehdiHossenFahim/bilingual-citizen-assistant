# Architecture — Bilingual Citizen Services AI Assistant

**Author / Developer:** Mehedi Hossen Fahim  
**Repository:** [https://github.com/MehdiHossenFahim/bilingual-citizen-assistant](https://github.com/MehdiHossenFahim/bilingual-citizen-assistant)

---

## 1. System Overview

The Bilingual Citizen Services AI Assistant is a decoupled, modern cloud-native system designed for high reliability, zero hallucinations, and low latency across Bengali (বাংলা) and English queries.

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Client (Vercel)"]
        UI["React 18 + Vite Web App<br/>(Bilingual Interface, Citation Cards, Diagnostic Modal)"]
    end

    subgraph EdgeRouting["Edge & Reverse Proxy"]
        Proxy["Vercel Edge Rewrites<br/>(/api/*, /health, /ready)"]
    end

    subgraph BackendLayer["Backend Core (Render Cloud)"]
        API["FastAPI 0.115 Engine<br/>(Non-blocking Lifespan, CORS, Pydantic)"]
        
        subgraph LangGraphEngine["LangGraph State Machine (5-Node Graph)"]
            N1["1. analyze_query<br/>(Language Detection, Category & Intent Classification)"]
            N2["2. retrieve<br/>(Parallel BM25 Sparse + Dense ChromaDB)"]
            N3{"3. evaluate_evidence<br/>(Normalized Score >= 0.40 & Freshness Check)"}
            N4A["4a. generate_answer<br/>(Gemini Flash Grounded Inference with Citations)"]
            N4B["4b. fallback<br/>(Honest Multilingual Safe Refusal)"]
        end
    end

    subgraph StorageLayer["Knowledge Base & Storage"]
        BM25[("BM25 Inverted Index<br/>(data/bm25_index.pkl)")]
        Chroma[("ChromaDB Vector Store<br/>(data/chroma_db/ - Vectors)")]
        DocStore[("Document Metadata Store<br/>(Authorities, URLs, Excerpts)")]
    end

    UI -->|"POST /api/v1/chat"| Proxy
    Proxy -->|"Secure TLS Proxy"| API
    API --> N1
    N1 --> N2
    N2 <-->|"Tokenized Sparse Search"| BM25
    N2 <-->|"Cosine Similarity Vector Search"| Chroma
    N2 --> N3
    N3 -->|"Sufficient Evidence (>= 0.40)"| N4A
    N3 -->|"Insufficient Evidence (< 0.40)"| N4B
    N4A -->|"Response with [src-X] Citations"| API
    N4B -->|"Safe Refusal Notice"| API
    API -->|"JSON Response"| UI
```

---

## 2. Component Detail

### 1. Ingestion Pipeline

Official administrative manuals, FAQs, citizen charters, and circulars are pre-processed into dual-engine indices:

```mermaid
flowchart LR
    subgraph RawSources["Official Sources"]
        HTML["Official Government Portals<br/>(dip.gov.bd, nidw.gov.bd, nbr.gov.bd)"]
        PDF["Citizen Charters & Forms<br/>(PDFs)"]
        JSON["Structured FAQs<br/>(JSON/JSONL)"]
    end

    subgraph Preprocessing["Parsing & Chunking"]
        Loaders["loaders.py<br/>(HTMLLoader, PDFLoader, JSONLoader)"]
        Parser["parsing.py<br/>(NFKC Unicode Normalization, Danda Delimiters)"]
        Chunker["chunking.py<br/>(512 Chars / 80 Overlap, Sentence-Aware)"]
    end

    subgraph StorageEngines["Dual-Engine Storage"]
        BM25Gen["BM25 Index Builder"]
        DenseGen["Dense Embedder (Gemini / BGE-M3)"]
        BM25File[("data/bm25_index.pkl")]
        ChromaDB[("data/chroma_db/")]
    end

    RawSources --> Loaders
    Loaders --> Parser
    Parser --> Chunker
    Chunker --> BM25Gen
    Chunker --> DenseGen
    BM25Gen --> BM25File
    DenseGen --> ChromaDB
```

1. **Loaders (`app/ingestion/loaders.py`):** Ingests raw content from structured JSON files, live government URLs, and downloadable PDF circulars.
2. **Parsing (`app/ingestion/parsing.py`):** Applies Unicode NFKC normalization, strips non-printable control characters, and standardizes Bengali punctuation (such as the sentence-ending danda `।`).
3. **Chunking (`app/ingestion/chunking.py`):** Uses recursive splitting respecting linguistic sentence boundaries with 512 characters and 80-character overlap.
4. **Dual Indexing:**
   - **Sparse Index:** Precomputes BM25Okapi inverted term frequencies serialized to `data/bm25_index.pkl`.
   - **Dense Index:** Generates high-dimensional semantic embeddings (using zero-RAM `gemini-embedding-001` in production or `BAAI/bge-m3` locally) saved to ChromaDB.

---

### 2. Query-Time Execution Pipeline

```mermaid
flowchart TD
    UserQuery["User Input (Bangla / English / Banglish)"] --> N1["1. analyze_query Node"]
    
    subgraph MultiModalRetrieval["2. Parallel Retrieval"]
        N1 -->|"Sparse Query"| BM25Search["BM25 Lexical Search (Top-20)"]
        N1 -->|"Dense Query"| ChromaSearch["ChromaDB Semantic Search (Top-20)"]
    end

    BM25Search --> Fusion["3. Reciprocal Rank Fusion (RRF)<br/>RRF(d) = Σ 1 / (60 + rank)"]
    ChromaSearch --> Fusion

    Fusion --> Normalization["4. Normalization & Rerank<br/>Scale confidence to [0.0, 1.0]"]
    Normalization --> EvalGate{"5. evaluate_evidence Node<br/>Top Score >= 0.40?"}

    EvalGate -->|"Sufficient Evidence"| GroundedGen["6a. generate_answer Node<br/>Grounded Gemini Flash Generation"]
    EvalGate -->|"Insufficient Evidence"| FallbackNode["6b. fallback Node<br/>Honest refusal with government source link"]

    GroundedGen --> CitationParse["7. Citation Parsing & Deduplication<br/>Map [src-X] to Title, Authority & URL"]
    CitationParse --> FinalResponse["FastAPI JSON Response"]
    FallbackNode --> FinalResponse
```

| Step | Component | Responsibilities |
|---|---|---|
| 1 | `analyze_query` | Detects language (`bn`, `en`, `mixed`), identifies domain (Passport, NID, e-TIN), and classifies intent. |
| 2 | `bm25.retrieve()` | BM25Okapi scores top-20 chunks based on exact term matches. |
| 3 | `dense_search.retrieve()` | Vector search queries top-20 nearest semantic neighbors via cosine similarity. |
| 4 | `fusion.rrf()` | Merges both candidate lists using Reciprocal Rank Fusion ($k=60$). |
| 5 | `reranker.rerank()` | Normalizes candidate scores to $[0.0, 1.0]$. |
| 6 | `evaluate_evidence` | Evaluates evidence sufficiency against threshold ($0.40$), checks currency, and detects conflicting source dates. |
| 7a | `generate_answer` | Generates grounded answer using Google Gemini Flash, inserting verifiable citations. |
| 7b | `fallback` | Returns honest, courteous failure response in the user's language without hallucination. |

---

### 3. Why Hybrid Retrieval (BM25 + Dense)?

| Query Characteristic | BM25 Sparse | Dense Semantic | Hybrid RRF Benefit |
|---|---|---|---|
| **Exact form numbers** ("Form-1", "SRO 219") | High Precision | Low Precision | Catches exact administrative codes |
| **Official acronyms** ("NID", "TIN", "DIP", "MRP") | Direct Token Match | Semantic Embedding | Guarantees exact government acronym matching |
| **Colloquial questions** ("পাসপোর্ট বানাতে কী লাগবে?") | Partial Match | High Recall | Understands semantic intent regardless of phrasing |
| **Cross-lingual queries** ("how to apply for Smart NID") | English only | Cross-lingual embedding | Bridges English queries with Bengali regulations |
| **Morphological variations** ("নবায়ন", "রিনিউ", "renew") | Stemming dependent | Semantic association | Handles informal synonyms cleanly |

---

### 4. Technology Stack & Specifications

| Tier | Component | Technology | Role |
|---|---|---|---|
| **Frontend** | User Interface | React 18.3 + Vite 5.4 | Single Page Application with citation cards & health diagnostics |
| **Hosting (Client)** | Web Hosting & Proxy | Vercel | Edge routing, asset CDN, and serverless reverse proxy |
| **Backend** | API Engine | FastAPI 0.115 + Uvicorn | Asynchronous request processing, CORS, and OpenAPI docs |
| **Hosting (Server)** | Application Server | Render (Linux Container) | Dockerized backend with non-blocking lifecycle management |
| **Orchestrator** | RAG State Machine | LangGraph 0.2 | Deterministic conditional workflow state machine |
| **Sparse Engine** | Lexical Index | `rank-bm25` (BM25Okapi) | Inverted keyword index with Bengali tokenization |
| **Dense Engine** | Vector Database | ChromaDB 0.5+ | Persistent local vector store |
| **Embeddings** | Semantic Vectors | Gemini Cloud Embeddings / BGE-M3 | Zero-RAM cloud embeddings (`gemini-embedding-001`) |
| **Generative LLM** | Answer Generator | Google Gemini Flash | Grounded inference with strict citation extraction |
| **Evaluation** | Quality Benchmark | Custom bilingual evaluation suite | 40+ audited test cases across accuracy, citations, and fallback |
