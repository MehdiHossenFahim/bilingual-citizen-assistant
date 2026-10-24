# 🏛️ Bilingual Citizen Services AI Assistant

**Ask in your language. Get understandable guidance. Check the official source.**

A RAG-powered AI assistant for Bangladesh government services, supporting **Bangla**, **English**, and **Banglish** queries with grounded answers from official sources.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-orange)](https://langchain-ai.github.io/langgraph/)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 Bilingual | Full Bangla + English support with Banglish best-effort |
| 📚 Hybrid RAG | BM25 keyword + BGE-M3 semantic retrieval + RRF fusion + cross-encoder reranking |
| 🔗 Cited answers | Every factual claim linked to official source with page/section reference |
| 🛡️ Safe fallback | Honest "cannot confirm" instead of fabricated administrative facts |
| 🔄 LangGraph workflow | Explicit analyze → retrieve → evaluate → generate/fallback state machine |
| 📊 Evaluation suite | 40+ test questions with bilingual, OOD, and adversarial cases |
| 🐳 Docker ready | Single `docker compose up` deployment |

**Covered services**: Passport (পাসপোর্ট) · NID (জাতীয় পরিচয়পত্র) · TIN (করদাতা শনাক্তকারী নম্বর)

---

## 🏗️ Architecture

```
React Web UI (bilingual chat)
        │ POST /api/v1/chat
        ▼
FastAPI Backend (validation + routing)
        │
        ▼
LangGraph Workflow
  ├─ analyze_query  (language detect · category · intent)
  ├─ retrieve       (BM25 + BGE-M3 → RRF → CrossEncoder reranker)
  ├─ evaluate       (threshold · freshness · conflict check)
  ├─ generate       (Gemini grounded answer + citation extraction)
  └─ fallback       (honest Bangla/English message)
        │
        ▼
ChromaDB (dense) + BM25 pickle (sparse)
```

See [`docs/architecture.md`](docs/architecture.md) for the full system diagram and component detail.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- ~6 GB RAM recommended (embedding model + reranker)

### 1. Clone and set up

```bash
git clone https://github.com/your-username/bilingual-citizen-assistant.git
cd bilingual-citizen-assistant

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your-actual-key
```

### 3. Ingest the knowledge base

```bash
# Ingest the bundled sample data (Passport + NID + TIN)
python scripts/ingest.py

# Or ingest your own sources:
python scripts/ingest.py --source-file data/sources/my_documents.json
python scripts/ingest.py --url https://www.dip.gov.bd/... --title "Guide" --category passport
python scripts/ingest.py --pdf data/raw_pdfs/guide.pdf --title "PDF Guide" --category nid
```

This downloads the embedding model (~570 MB) and reranker (~600 MB) on first run.

### 4. Start the backend

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify: http://localhost:8000/health

### 5. Start the React frontend

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173 (or http://localhost:8501 when running via Docker)

---

## 🐳 Docker Deployment

```bash
cp .env.example .env   # fill in GEMINI_API_KEY

docker compose up --build
```

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API docs**: http://localhost:8000/docs

The ChromaDB vector store and BM25 index persist across container restarts via Docker volumes.

**Note**: First startup downloads ~1.2 GB of ML models. Subsequent starts are fast.

---

## 📡 API Reference

See [`docs/api.md`](docs/api.md) for the full API reference.

### Example: Chat request

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "পাসপোর্ট করতে কী কী কাগজ লাগে?", "language": "bn"}'
```

```json
{
  "answer": "পাসপোর্ট আবেদনের জন্য নিম্নলিখিত কাগজপত্র প্রয়োজন...",
  "language": "bn",
  "status": "answered",
  "citations": [
    {
      "source_id": "abc123",
      "title": "Bangladesh e-Passport Application Guide",
      "authority": "Department of Immigration and Passports (DIP)",
      "url": "https://www.dip.gov.bd/...",
      "page": 1,
      "excerpt": "NID is required for new passport applications..."
    }
  ],
  "limitations": [],
  "latency_ms": 3800.0
}
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_api.py -v        # API endpoint tests
pytest tests/test_retrieval.py -v  # BM25 + RRF unit tests
pytest tests/test_citations.py -v  # Citation extraction tests
pytest tests/test_fallback.py -v   # Fallback behaviour tests
```

### Run the evaluation suite

```bash
# Requires a running knowledge base
python -m app.evaluation.evaluator
# Results saved to reports/evaluation_results.json
```

---

## 📁 Repository Structure

```
bilingual-citizen-assistant/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py          # POST /api/v1/chat
│   │   │   ├── sources.py       # GET /api/v1/sources/{id}
│   │   │   └── feedback.py      # POST /api/v1/feedback
│   │   └── schemas.py           # Pydantic request/response models
│   ├── ingestion/
│   │   ├── loaders.py           # HTML / PDF / JSON loaders
│   │   ├── parsing.py           # Unicode normalization, language detection
│   │   └── chunking.py          # Recursive chunking with Bangla support
│   ├── retrieval/
│   │   ├── bm25.py              # BM25Okapi index + serialization
│   │   ├── dense_search.py      # BGE-M3 + ChromaDB dense retrieval
│   │   ├── fusion.py            # Reciprocal Rank Fusion
│   │   └── reranker.py          # BGE-reranker-v2-m3 cross-encoder
│   ├── graph/
│   │   ├── state.py             # LangGraph TypedDict state schema
│   │   ├── nodes.py             # Node functions (analyze/retrieve/evaluate/generate/fallback)
│   │   └── workflow.py          # StateGraph builder + RAGWorkflow class
│   ├── generation/
│   │   ├── generator.py         # Gemini API answer generator
│   │   └── prompts.py           # System prompt, evidence template, fallback messages
│   ├── evaluation/
│   │   ├── dataset.py           # 40+ bilingual test questions
│   │   └── evaluator.py         # Automated evaluation runner
│   ├── config.py                # Pydantic settings (all env vars)
│   └── main.py                  # FastAPI app + lifespan startup
├── frontend/
│   └── app.py                   # Streamlit bilingual chat UI
├── data/
│   ├── sources/
│   │   └── sample_data.json     # Curated Passport/NID/TIN knowledge base
│   └── README.md
├── tests/
│   ├── test_api.py
│   ├── test_retrieval.py
│   ├── test_citations.py
│   └── test_fallback.py
├── scripts/
│   └── ingest.py                # Ingestion pipeline runner (CLI)
├── reports/
│   └── evaluation-report.md     # Evaluation methodology and results template
├── docs/
│   ├── architecture.md          # System architecture and data flow diagrams
│   └── api.md                   # Full API reference
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md                    # This file
```

---

## ⚙️ Configuration

All settings are in `.env` (copy from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | **required** | Google Gemini API key |
| `GENERATION_MODEL` | `gemini-3.8-flash` | LLM for answer generation |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Multilingual embedding model |
| `RERANKER_MODEL` | `BAAI/bge-reranker-v2-m3` | Cross-encoder reranker |
| `EVIDENCE_THRESHOLD` | `0.40` | Minimum reranker score for sufficient evidence |
| `CHROMA_PERSIST_DIR` | `./data/chroma_db` | ChromaDB storage path |
| `BM25_INDEX_PATH` | `./data/bm25_index.pkl` | BM25 index path |
| `RERANKER_TOP_K` | `5` | Final passages after reranking |

---

## 🎯 How to Demonstrate (for capstone rubric)

### AI Integration (25 marks)

1. **BM25 vs Dense retrieval**: Inspect `/api/v1/sources/{id}` for chunks; notice different scores
2. **RRF + reranking**: Enable `DEBUG` log level to see fusion scores
3. **LangGraph workflow**: The 5-node graph is visible in `app/graph/workflow.py`
4. **Citation tracing**: Click "Sources" in the UI to see exact supporting passage
5. **Fallback demo**: Ask "What is the best stock to buy?" → receives honest fallback
6. **Evaluation**: Run `python -m app.evaluation.evaluator` and review `reports/evaluation_results.json`

---

## ⚠️ Limitations and Disclaimers

- **Not a government system**: This assistant provides guidance only; it cannot submit applications, access government databases, or make official eligibility decisions.
- **Not legal advice**: Information from this system should be verified with the responsible authority before acting on it.
- **Fee information**: Government fees change annually. Always verify current fees with the issuing authority.
- **Document currency**: Official sources are indexed at ingestion time. Check source dates and re-ingest periodically.
- **Zero hallucinations disclaimer**: Zero unsupported claims in the audited test set does not guarantee zero hallucinations in production.

---

## 👨‍💻 Author & Submission Details

- **Author / Developer:** Mehedi Hossen Fahim
- **Project:** Bilingual Citizen Services AI Assistant (Bangla & English · Agentic RAG)
- **Course / Degree:** Capstone Project Submission
- **Domain:** AI / GenAI / Citizen-Facing NLP Systems

---

## 📜 License

This project is submitted as a capstone project by Mehedi Hossen Fahim. Source code is for educational and public-benefit demonstration purposes.

---

## 🙏 Acknowledgements

- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) — multilingual embedding model
- [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) — cross-encoder reranker
- [LangGraph](https://langchain-ai.github.io/langgraph/) — workflow orchestration
- [ChromaDB](https://docs.trychroma.com/) — vector database
- [Google Gemini](https://ai.google.dev/) — answer generation
- Bangladesh government portals: [DIP](https://www.dip.gov.bd), [EC NID Wing](https://services.nidw.gov.bd), [NBR](https://secure.incometax.gov.bd)

