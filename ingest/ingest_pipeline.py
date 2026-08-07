"""
Ingests every markdown report in data/ into both stores:
- SQLite: structured fields (date, people, type) for exact filtering
- Chroma: chunked + embedded narrative text for semantic search

Run:
    python ingest/ingest_pipeline.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest.parse_report import parse_report_file
from store.db import init_db, get_conn, upsert_report
from store.vector_store import add_report_chunks

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main():
    init_db()

    report_files = sorted(DATA_DIR.glob("*.md"))
    if not report_files:
        print(f"No .md files found in {DATA_DIR}")
        return

    print(f"Found {len(report_files)} report(s). Ingesting...")

    with get_conn() as conn:
        for path in report_files:
            report = parse_report_file(path)

            # 1. Structured store
            upsert_report(conn, report)

            # 2. Vector store - chunk + embed the narrative, tag with metadata
            #    Chroma metadata values must be str/int/float/bool, so join the
            #    people list into a comma-separated string for filtering.
            add_report_chunks(
                report_id=report["report_id"],
                narrative=report["narrative"],
                metadata={
                    "date": report["date"],
                    "incident_type": report["incident_type"],
                    "location": report["location"],
                    "people": ", ".join(report["people_involved"]),
                },
            )
            print(f"  Ingested {report['report_id']} ({path.name})")

    print("\nDone. Structured data in SQLite, embeddings in Chroma.")


if __name__ == "__main__":
    main()