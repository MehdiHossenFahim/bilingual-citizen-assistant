"""
scripts/ingest.py — Ingestion pipeline runner.

Usage:
    python scripts/ingest.py --source-file data/sources/sample_data.json
    python scripts/ingest.py --url https://www.dip.gov.bd/site/page/... --title "Passport Guide" --category passport
    python scripts/ingest.py --pdf data/raw_pdfs/passport-guide.pdf --title "MRP Guide" --category passport

Run after setting up your .env file.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("ingest")


def load_settings():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    from app.config import get_settings
    return get_settings()


def run_ingestion(docs, settings):
    from app.ingestion.chunking import DocumentChunker
    from app.retrieval.bm25 import BM25Index
    from app.retrieval.dense_search import DenseIndex

    chunker = DocumentChunker()
    all_chunks = []

    logger.info("Chunking %d documents…", len(docs))
    for doc in docs:
        if doc.parsing_status != "ok":
            logger.warning("Skipping failed doc: %s (%s)", doc.title, doc.parsing_notes)
            continue
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)

    logger.info("Total chunks: %d", len(all_chunks))

    if not all_chunks:
        logger.error("No chunks to index. Check your source documents.")
        sys.exit(1)

    # --- BM25 ---
    logger.info("Building BM25 index…")
    bm25 = BM25Index(settings.bm25_index_path)
    bm25.load()  # Load existing to merge
    bm25.add_chunks(all_chunks)
    bm25.save()
    logger.info("BM25 index saved: %d chunks", bm25.chunk_count)

    # --- Dense ---
    logger.info("Building dense index (this may download models)…")
    dense = DenseIndex(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
        embedding_model_name=settings.embedding_model,
    )
    dense.add_chunks(all_chunks)
    logger.info("Dense index ready: %d vectors", dense.vector_count)

    logger.info("[OK] Ingestion complete.")
    return len(all_chunks)


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into the knowledge base")
    parser.add_argument("--source-file", type=str, help="Path to JSON FAQ/knowledge file")
    parser.add_argument("--url", type=str, help="URL to fetch and index")
    parser.add_argument("--pdf", type=str, help="Path to local PDF file")
    parser.add_argument("--title", type=str, default="Untitled Document")
    parser.add_argument("--category", type=str, default="general",
                        choices=["passport", "nid", "tin", "general"])
    parser.add_argument("--authority", type=str, default=None)
    parser.add_argument("--publication-date", type=str, default=None)
    args = parser.parse_args()

    settings = load_settings()
    docs = []

    if args.source_file:
        from app.ingestion.loaders import JSONFAQLoader
        loader = JSONFAQLoader()
        docs = loader.load_file(args.source_file)
        logger.info("Loaded %d documents from %s", len(docs), args.source_file)

    elif args.url:
        from app.ingestion.loaders import HTMLLoader
        loader = HTMLLoader()
        doc = loader.load(
            url=args.url,
            title=args.title,
            authority=args.authority,
            category=args.category,
            publication_date=args.publication_date,
        )
        docs = [doc]
        logger.info("Loaded HTML page: %s", args.title)

    elif args.pdf:
        from app.ingestion.loaders import PDFLoader
        loader = PDFLoader()
        doc = loader.load(
            file_path=args.pdf,
            title=args.title,
            authority=args.authority,
            category=args.category,
            publication_date=args.publication_date,
        )
        docs = [doc]
        logger.info("Loaded PDF: %s", args.pdf)

    else:
        # Default: load the sample data bundled with the project
        default_path = Path(__file__).parent.parent / "data" / "sources" / "sample_data.json"
        if default_path.exists():
            from app.ingestion.loaders import JSONFAQLoader
            loader = JSONFAQLoader()
            docs = loader.load_file(default_path)
            logger.info("Loaded %d docs from default sample data.", len(docs))
        else:
            logger.error("No source specified and no sample data found at %s", default_path)
            sys.exit(1)

    total = run_ingestion(docs, settings)
    print(f"\n[OK] Successfully indexed {total} chunks into the knowledge base.")


if __name__ == "__main__":
    main()

