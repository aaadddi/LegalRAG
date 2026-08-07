"""
The single entry point the API layer calls: answer(query) -> full response
with the generated text, source chunks, and routing info (useful for
debugging/demoing why a given answer was retrieved the way it was).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.retrieval import retrieve
from core.generation import generate_answer


def answer(query: str) -> dict:
    retrieval_result = retrieve(query)
    chunks = retrieval_result["chunks"]

    response_text = generate_answer(query, chunks)

    return {
        "answer": response_text,
        "sources": [
            {
                "report_id": c["metadata"].get("report_id"),
                "date": c["metadata"].get("date"),
                "incident_type": c["metadata"].get("incident_type"),
                "excerpt": c["text"][:200],
            }
            for c in chunks
        ],
        "routing": {
            "people_detected": retrieval_result["intent"].people,
            "date_range_detected": [
                retrieval_result["intent"].date_start,
                retrieval_result["intent"].date_end,
            ],
            "sql_prefiltered_report_ids": retrieval_result["report_ids_filtered"],
        },
    }


if __name__ == "__main__":
    import json

    q = sys.argv[1] if len(sys.argv) > 1 else "What incidents involved David Chen?"
    result = answer(q)
    print(json.dumps(result, indent=2))