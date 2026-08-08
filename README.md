# Legal Incident RAG

A "chat with your docs" RAG app specialized for legal/HR incident reports:
hybrid retrieval (structured SQL filters + semantic vector search), person
profiling, and cited answers. Built with Gemini + Chroma + FastAPI + Next.js.

## How it works

Incident reports are markdown files with YAML frontmatter (date, location,
incident type, people involved). Each report is stored two ways:

- **SQLite** (`store/incidents.db`) — structured fields, for exact filtering
  (e.g. "incidents involving David Chen in March").
- **Chroma** (`store/chroma_db/`) — the narrative text, chunked and embedded,
  for semantic search.

When a question comes in, `core/query_router.py` uses spaCy NER to detect
people and date ranges mentioned in the query. `core/retrieval.py` uses those
to SQL-prefilter candidate reports, then runs semantic search over that
subset in Chroma. `core/generation.py` calls Gemini to produce a cited answer
from the retrieved chunks. `core/rag_engine.py` ties this together as the
single entry point the API calls.

## Project structure

```
data/     raw incident reports (markdown, with YAML frontmatter)
ingest/   synthetic data generation, parsing, chunking, embedding
store/    SQLite (structured fields) + Chroma (vector embeddings)
core/     query routing, hybrid retrieval, answer generation
api/      FastAPI backend
ui/       Next.js frontend
```

## Setup

### Backend

1. Create a virtualenv and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate       # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. Get a Gemini API key from https://aistudio.google.com -> "Get API key",
   then create a `.env` file in the project root:
   ```
   GOOGLE_API_KEY=your-key-here
   EMBEDDING_MODEL=gemini-embedding-001
   CHROMA_PATH=store/chroma_db
   COLLECTION_NAME=incidents
   ```

3. Generate a synthetic dataset (or drop your own markdown reports into
   `data/`, matching the frontmatter format in `data/sample_report_0001.md`):
   ```
   python ingest/generate_synthetic_data.py --count 40
   ```

4. Ingest the reports into SQLite + Chroma:
   ```
   python ingest/ingest_pipeline.py
   ```

5. Run the API:
   ```
   uvicorn api.main:app --reload
   ```
   The backend listens on `http://127.0.0.1:8000`. Check `GET /health` to
   confirm it's up.

### Frontend

```
cd ui
npm install
npm run dev
```

By default the UI talks to `http://127.0.0.1:8000`. To point it elsewhere,
set `NEXT_PUBLIC_API_URL` in `ui/.env.local`. Open http://localhost:3000.

## API endpoints

| Method | Path                   | Description                              |
|--------|------------------------|-------------------------------------------|
| POST   | `/query`                | Ask a question, get a cited answer       |
| GET    | `/profile/{person_name}`| All incidents involving a person, date-sorted |
| GET    | `/reports`               | List/filter reports by date range        |
| POST   | `/reports`               | Create a report                          |
| GET    | `/reports/{report_id}`   | Fetch a single report                    |
| PUT    | `/reports/{report_id}`   | Update a report                          |
| DELETE | `/reports/{report_id}`   | Delete a report                          |
| GET    | `/health`                | Liveness check                           |

## Docker

`docker-compose.yml` runs the backend, the frontend, and an nginx reverse
proxy together, with nginx serving both under one origin at `/legalRag`
(`/legalRag/api/*` → backend, `/legalRag/*` → frontend — see
`nginx/nginx.conf`). Before running, set in the root `.env`:

```
NEXT_PUBLIC_API_URL=https://your-domain/legalRag/api
CORS_ORIGINS=https://your-domain
```

`NEXT_PUBLIC_API_URL` is inlined into the frontend's client bundle at
**build** time (a Next.js requirement), so it's passed in as a Docker build
arg (see `docker-compose.yml`'s `frontend.build.args` and `ui/Dockerfile`)
rather than left to `env_file`, which only sets runtime env — too late for
an already-built bundle.

```
docker compose up --build
```

SQLite and Chroma data persist to `./store_data` on the host; report markdown
files persist to `./data`. On every backend container start, `entrypoint.sh`
runs `ingest/ingest_pipeline.py`, which ingests any `.md` file in `./data`
not already in the store — so dropping in new reports and redeploying is
enough; no manual ingest step needed. It skips report_ids already ingested
by default (cheap restarts, no repeat embedding-API calls); run
`docker compose exec backend python ingest/ingest_pipeline.py --force` to
force re-ingesting everything (e.g. after editing a report file by hand).

## Notes

- CORS on the backend defaults to `http://localhost:3000` for local dev. Set
  `CORS_ORIGINS` (comma-separated) in `.env` before deploying anywhere public
  — see above. In production nginx serves the frontend and API from the same
  origin, so CORS isn't actually exercised there; it mainly matters for
  direct API access or alternate frontend deployments.
- Data in `data/` and `store/` is fictional/synthetic, generated for testing.
