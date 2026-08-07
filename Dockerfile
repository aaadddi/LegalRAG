FROM python:3.12-slim

WORKDIR /app

# System deps for building some Python packages (chromadb, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# spaCy's small English model, used by core/query_router.py for NER-based
# query routing (person/date detection).
RUN python -m spacy download en_core_web_sm

COPY . .

# store/ is where SQLite + Chroma persist data - mount this as a volume
# in production so data survives container restarts/redeploys.
RUN mkdir -p /app/store

EXPOSE 8000

# Basic healthcheck so `docker ps` / orchestrators can see liveness.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]