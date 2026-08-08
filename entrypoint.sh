#!/bin/sh
set -e

# Auto-ingest any report markdown in data/ not yet in the store. Runs on
# every container start (cheap after the first run - see
# ingest/ingest_pipeline.py, which skips already-ingested report_ids), so
# data/ and store_data/ being host-mounted at *runtime* (docker-compose.yml)
# rather than baked in at build time is a non-issue: this catches it here
# instead. Ingestion failure (e.g. GOOGLE_API_KEY missing) shouldn't take
# the whole API down, so it's non-fatal.
python ingest/ingest_pipeline.py || echo "Warning: ingestion step failed, continuing with existing store data" >&2

exec uvicorn api.main:app --host 0.0.0.0 --port 8000
