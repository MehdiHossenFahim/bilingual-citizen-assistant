# API Reference — Bilingual Citizen Services AI Assistant

Base URL: `http://localhost:8000` (local) or your deployed URL.

Interactive docs: `GET /docs` (Swagger UI) | `GET /redoc` (ReDoc)

---

## Endpoints

### POST `/api/v1/chat`

Submit a bilingual query and receive a grounded answer with citations.

**Request body**

```json
{
  "query": "পাসপোর্ট করতে কী কী কাগজ লাগে?",
  "language": "auto",
  "session_id": "optional-session-uuid"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Question in Bangla, English, or Banglish (2–1000 chars) |
| `language` | string | No | `"bn"` \| `"en"` \| `"auto"` (default: `"auto"`) |
| `session_id` | string | No | Optional session ID for conversation continuity |

**Response — 200 OK**

```json
{
  "answer": "পাসপোর্ট নবায়নের জন্য প্রয়োজনীয় কাগজপত্র...",
  "language": "bn",
  "status": "answered",
  "citations": [
    {
      "source_id": "abc123def456",
      "title": "Bangladesh e-Passport Application Guide",
      "authority": "Department of Immigration and Passports (DIP)",
      "url": "https://www.dip.gov.bd/site/page/...",
      "page": 3,
      "section": "Required Documents",
      "excerpt": "NID is required for new passport applications...",
      "publication_date": "2024-01-01",
      "ingestion_date": null
    }
  ],
  "limitations": [
    "Fee information sourced from 2024-01-01 document — verify with DIP before applying."
  ],
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "latency_ms": 3210.5
}
```

**Status values**

| Value | Meaning |
|-------|---------|
| `answered` | Evidence found; grounded answer generated |
| `insufficient_evidence` | No reliable evidence; honest fallback returned |
| `clarification_needed` | Query too ambiguous to answer |
| `error` | Internal error; try again |

**Error responses**

```json
// 422 Unprocessable Entity (validation error)
{
  "detail": [{"loc": ["body", "query"], "msg": "min length 2", "type": "value_error"}]
}

// 503 Service Unavailable (workflow not ready)
{
  "detail": "RAG workflow not initialised. Check /ready for status."
}
```

---

### GET `/api/v1/sources/{source_id}`

Retrieve source metadata and excerpts for a cited document chunk.

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_id` | string | Chunk ID from a citation's `source_id` field |

**Response — 200 OK**

```json
{
  "source": {
    "source_id": "abc123def456",
    "title": "Passport Application Guide",
    "authority": "DIP",
    "url": "https://www.dip.gov.bd/",
    "category": "passport",
    "publication_date": "2024-01-01",
    "ingestion_date": "1729800000.0",
    "chunk_count": 8,
    "parsing_status": "ok"
  },
  "excerpts": [
    {
      "chunk_id": "abc123def456",
      "text": "NID is required for new passport applications...",
      "page": 3
    }
  ]
}
```

**Error responses**

| Code | Condition |
|------|-----------|
| 404 | `source_id` not found in the index |
| 503 | Dense index not available |

---

### GET `/health`

Liveness check — returns 200 if the application is running.

```json
{"status": "ok", "timestamp": "2024-10-24T15:59:00"}
```

---

### GET `/ready`

Readiness check — returns whether all dependencies are initialised.

```json
{
  "ready": true,
  "checks": {
    "bm25_index": "ok",
    "dense_index": "ok",
    "workflow": "ok"
  },
  "timestamp": "2024-10-24T15:59:00"
}
```

Use this endpoint in Docker health checks and deployment readiness probes.

---

### POST `/api/v1/feedback`

Submit optional answer feedback. Stores only a query hash (SHA-256), not the raw query.

**Request body**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "query_hash": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
  "rating": "helpful",
  "comment": "Accurate and easy to understand."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | Session identifier |
| `query_hash` | string | Yes | SHA-256 of the submitted query |
| `rating` | string | Yes | `"helpful"` \| `"not_helpful"` |
| `comment` | string | No | Optional free-text comment (max 500 chars) |

**Response — 200 OK**

```json
{"acknowledged": true, "message": "Thank you for your feedback."}
```

---

## Authentication

The current API does not require authentication. Apply an API gateway or reverse proxy for production rate limiting and access control.

API keys for Gemini and other services are loaded from environment variables and **never** returned in responses.

## Rate Limiting

Default: 20 requests per 60 seconds per IP (configurable in `.env`).
The rate limit applies to `/api/v1/chat` only.

## Error Format

All error responses follow a consistent format:

```json
{
  "error": "Human-readable error description",
  "details": [
    {"code": "VALIDATION_ERROR", "message": "Field too short", "field": "query"}
  ],
  "request_id": null
}
```

Stack traces, API keys, and internal prompts are **never** included in error responses.

