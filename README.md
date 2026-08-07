# Legal Incident RAG

A "chat with your docs" RAG app specialized for legal/HR incident reports:
hybrid retrieval (structured filters + semantic search), person profiling,
and cited answers. Built with Gemini + Chroma + FastAPI + Streamlit.

## Setup

1. Create a virtualenv and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate       # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. Get a Gemini API key from https://aistudio.google.com -> "Get API key",
   then copy the env template and fill it in:
   ```
   cp .env.example .env
   ```

3. Generate a synthetic dataset (or drop your own markdown reports into
   `data/`, matching the frontmatter format in `data/sample_report_0001.md`):
   ```
   python ingest/generate_synthetic_data.py --count 40
   ```

## Project structure

```
data/     raw incident reports (markdown, with YAML frontmatter)
ingest/   parsing, extraction, chunking, embedding scripts
store/    SQLite (structured fields) + Chroma (vector embeddings)
api/      FastAPI backend
ui/       Streamlit frontend
```

## Status

- [x] Project scaffolding
- [x] Synthetic dataset generator
- [ ] Ingestion pipeline (parse frontmatter -> SQLite, chunk+embed -> Chroma)
- [ ] Hybrid retrieval logic
- [ ] Generation with citations
- [ ] FastAPI backend
- [ ] Streamlit UI
