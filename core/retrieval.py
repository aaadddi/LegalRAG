"""
Hybrid retrieval logic:
- If the query names a person or date range, filter SQLite first to get
  the relevant report_ids, then restrict the vector search to just those
  (via a Chroma metadata $in filter).
- If the SQL filter alone is precise and narrow, we can also just return
  those reports directly without needing semantic search.
- If no filters were detected, run plain semantic search over everything.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.query_router import QueryIntent, parse_query
from store.db import get_conn, find_reports_by_person, find_reports_by_date_range
from store.vector_store import semantic_search

MAX_CHUNKS = 6


def _sql_filtered_report_ids(intent: QueryIntent) -> set[str]:
    person_ids: set[str] | None = None
    date_ids: set[str] | None = None

    with get_conn() as conn:
        if intent.people:
            person_ids = set()
            for person in intent.people:
                for report in find_reports_by_person(conn, person):
                    person_ids.add(report["report_id"])

        if intent.date_start and intent.date_end:
            date_ids = {
                report["report_id"]
                for report in find_reports_by_date_range(conn, intent.date_start, intent.date_end)
            }

    # Both filters present -> intersect (person AND in that date range).
    if person_ids is not None and date_ids is not None:
        return person_ids & date_ids
    # Only one filter present -> use it directly.
    return person_ids if person_ids is not None else (date_ids or set())


def retrieve(query: str) -> dict:
    """Returns {"chunks": [...], "report_ids_filtered": [...], "intent": QueryIntent}"""
    intent = parse_query(query)

    report_ids = _sql_filtered_report_ids(intent) if intent.has_filters else set()

    where_filter = None
    if report_ids:
        where_filter = {"report_id": {"$in": list(report_ids)}}

    results = semantic_search(query, n_results=MAX_CHUNKS, where=where_filter)

    chunks = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for doc, meta in zip(docs, metas):
        chunks.append({"text": doc, "metadata": meta})

    return {
        "chunks": chunks,
        "report_ids_filtered": sorted(report_ids),
        "intent": intent,
    }