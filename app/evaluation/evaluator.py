"""
app/evaluation/evaluator.py — Automated evaluation runner.

Runs the full RAG pipeline against the evaluation dataset and computes:
  - Status accuracy (answered vs. fallback correct classification)
  - Keyword recall (expected keywords found in answer)
  - Citation presence
  - Latency percentiles

Run with:
    python -m app.evaluation.evaluator
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def run_evaluation(
    workflow,
    dataset=None,
    output_path: str = "./reports/evaluation_results.json",
) -> dict[str, Any]:
    from app.evaluation.dataset import EVAL_DATASET

    if dataset is None:
        dataset = EVAL_DATASET

    results = []
    correct_status = 0
    total_keyword_hits = 0
    total_keywords = 0
    citation_present = 0
    latencies = []

    logger.info("Starting evaluation on %d questions…", len(dataset))

    for q in dataset:
        t0 = time.perf_counter()
        state = workflow.run(query=q.query, language="auto")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

        actual_status = state.get("status", "error")
        answer = state.get("answer", "")
        citations = state.get("citations", [])

        # Status accuracy
        status_ok = actual_status == q.expected_status
        if status_ok:
            correct_status += 1

        # Keyword recall
        kw_found = []
        for kw in q.expected_keywords:
            if kw.lower() in answer.lower():
                kw_found.append(kw)
                total_keyword_hits += 1
            total_keywords += 1
        kw_recall = len(kw_found) / len(q.expected_keywords) if q.expected_keywords else 1.0

        # Citation check
        has_citation = len(citations) > 0 if q.should_cite_source else True
        if has_citation:
            citation_present += 1

        results.append({
            "id": q.id,
            "query": q.query,
            "language": q.language,
            "category": q.category,
            "expected_status": q.expected_status,
            "actual_status": actual_status,
            "status_ok": status_ok,
            "keyword_recall": round(kw_recall, 3),
            "keywords_found": kw_found,
            "keywords_expected": q.expected_keywords,
            "citation_count": len(citations),
            "has_citation": has_citation,
            "latency_ms": round(elapsed_ms, 1),
            "answer_preview": answer[:200],
        })

    n = len(dataset)
    citation_needing = sum(1 for q in dataset if q.should_cite_source)

    summary = {
        "total_questions": n,
        "status_accuracy": round(correct_status / n, 3) if n > 0 else 0,
        "keyword_recall": round(total_keyword_hits / total_keywords, 3) if total_keywords > 0 else 1.0,
        "citation_rate": round(citation_present / citation_needing, 3) if citation_needing > 0 else 1.0,
        "median_latency_ms": round(sorted(latencies)[n // 2], 1) if latencies else 0,
        "p90_latency_ms": round(sorted(latencies)[int(n * 0.9)], 1) if latencies else 0,
        "targets": {
            "status_accuracy": ">= 0.95",
            "keyword_recall": ">= 0.85",
            "citation_rate": ">= 0.95",
            "median_latency_ms": "<= 10000",
        },
    }

    output = {"summary": summary, "results": results}

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("Evaluation complete. Results saved to %s", output_path)
    _print_summary(summary)
    return output


def _print_summary(summary: dict) -> None:
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total questions:    {summary['total_questions']}")
    print(f"Status accuracy:    {summary['status_accuracy']:.1%}  (target: {summary['targets']['status_accuracy']})")
    print(f"Keyword recall:     {summary['keyword_recall']:.1%}  (target: {summary['targets']['keyword_recall']})")
    print(f"Citation rate:      {summary['citation_rate']:.1%}  (target: {summary['targets']['citation_rate']})")
    print(f"Median latency:     {summary['median_latency_ms']:.0f} ms  (target: {summary['targets']['median_latency_ms']})")
    print(f"P90 latency:        {summary['p90_latency_ms']:.0f} ms")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    logging.basicConfig(level=logging.INFO)

    from dotenv import load_dotenv
    load_dotenv()

    from app.config import get_settings
    settings = get_settings()

    from app.retrieval.bm25 import BM25Index
    from app.retrieval.dense_search import DenseIndex
    from app.retrieval.reranker import CrossEncoderReranker
    from app.generation.generator import AnswerGenerator
    from app.graph.nodes import set_dependencies
    from app.graph.workflow import RAGWorkflow

    bm25 = BM25Index(settings.bm25_index_path)
    bm25.load()

    dense = DenseIndex(settings.chroma_persist_dir, settings.chroma_collection_name)
    reranker = CrossEncoderReranker(settings.reranker_model)
    generator = AnswerGenerator(settings.gemini_api_key, settings.generation_model)
    set_dependencies(bm25, dense, reranker, generator)
    workflow = RAGWorkflow()

    run_evaluation(workflow)

