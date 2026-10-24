# Data Directory

This directory contains the knowledge base for the Bilingual Citizen Services AI Assistant.

## Structure

```
data/
├── sources/
│   └── sample_data.json   ← Curated official Bangladesh government service data
├── chroma_db/             ← ChromaDB vector store (created at runtime, gitignored)
├── bm25_index.pkl         ← BM25 sparse index (created at runtime, gitignored)
├── metadata.db            ← SQLite metadata store (created at runtime, gitignored)
└── feedback.jsonl         ← User feedback log (created at runtime, gitignored)
```

## Adding Sources

### Via JSON file (recommended for batch ingestion)

Create a JSON file following the schema in `sources/sample_data.json`:

```json
[
  {
    "id": "unique-id",
    "title": "Document Title",
    "content": "Full document text...",
    "source_url": "https://official.gov.bd/url",
    "authority": "Ministry / Department Name",
    "category": "passport | nid | tin | general",
    "publication_date": "YYYY-MM-DD"
  }
]
```

Then run:
```bash
python scripts/ingest.py --source-file data/sources/my_documents.json
```

### Via URL (HTML scraping)

```bash
python scripts/ingest.py \
  --url https://www.dip.gov.bd/site/page/... \
  --title "Passport Application Guide" \
  --category passport \
  --authority "DIP" \
  --publication-date 2024-01-01
```

### Via local PDF

```bash
python scripts/ingest.py \
  --pdf data/raw_pdfs/passport-guide.pdf \
  --title "MRP Passport Guide" \
  --category passport \
  --authority "Department of Immigration and Passports"
```

## Source Quality Guidelines

1. **Only use official Bangladesh government sources** as authoritative evidence.
2. **Track publication/effective dates** — mark time-sensitive content.
3. **Verify URLs** resolve correctly before indexing.
4. **Minimum 100 knowledge records** across Passport, NID, and TIN services.
5. **Retain ingestion logs** to trace every indexed chunk.

## Privacy

- Do **not** store raw user queries or personally identifiable information.
- `feedback.jsonl` stores only query hashes (SHA-256), not raw queries.
- Logs and indexes should not contain citizen NID numbers or passport numbers.

