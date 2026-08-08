"""
Ingests every markdown report in data/ into both stores:
- SQLite: structured fields (date, people, type) for exact filtering
- Chroma: chunked + embedded narrative text for semantic search

Run:
    python ingest/ingest_pipeline.py           # only new report_ids (cheap)
    python ingest/ingest_pipeline.py --force   # re-embed everything

Runs automatically on backend container startup (see entrypoint.sh) so
dropping new files into data/ and redeploying is enough - no manual step.
Skips report_ids already in the store by default so restarts don't re-hit
the embedding API for reports that haven't changed.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest.parse_report import parse_report_file
from store.db import init_db, get_conn, upsert_report
from store.vector_store import add_report_chunks

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-parse, re-embed, and overwrite reports already in the store "
             "(default: skip report_ids already ingested).",
    )
    args = parser.parse_args()

    init_db()

    report_files = sorted(DATA_DIR.glob("*.md"))
    if not report_files:
        print(f"No .md files found in {DATA_DIR}")
        return

    reports = [parse_report_file(path) for path in report_files]

    if not args.force:
        with get_conn() as conn:
            existing_ids = {row["report_id"] for row in conn.execute("SELECT report_id FROM reports")}
        skipped = [r for r in reports if r["report_id"] in existing_ids]
        reports = [r for r in reports if r["report_id"] not in existing_ids]
        if skipped:
            print(f"Skipping {len(skipped)} already-ingested report(s) (use --force to re-embed).")

    if not reports:
        print("Nothing new to ingest.")
        return

    print(f"Ingesting {len(reports)} report(s)...")

    with get_conn() as conn:
        for report in reports:
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
            print(f"  Ingested {report['report_id']} ({Path(report['source_path']).name})")

    print("\nDone. Structured data in SQLite, embeddings in Chroma.")


if __name__ == "__main__":
    main()