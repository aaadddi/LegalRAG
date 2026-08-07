"""
Vector store: chunked report text embedded via Gemini, stored in Chroma
with metadata (report_id, date, people) so retrieval can filter by
metadata before or after the similarity search.
"""
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai

load_dotenv()

CHROMA_PATH = Path(os.getenv("CHROMA_DB_PATH", "./store/chroma_db"))
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
COLLECTION_NAME = "incident_chunks"

_client = None
_genai_client = None


def get_chroma_client():
    global _client
    if _client is None:
        CHROMA_PATH.parent.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return _client


def get_genai_client():
    global _genai_client
    if _genai_client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set - copy .env.example to .env")
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client


def get_collection():
    return get_chroma_client().get_or_create_collection(name=COLLECTION_NAME)


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Embed a batch of texts via Gemini. task_type differs for docs vs queries -
    use RETRIEVAL_QUERY when embedding a user question."""
    client = get_genai_client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config={"task_type": task_type},
    )
    return [e.values for e in result.embeddings]


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Simple character-based chunking with overlap. Good enough for
    report-length documents; swap for a token-aware splitter if reports
    get much longer."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def add_report_chunks(report_id: str, narrative: str, metadata: dict):
    chunks = chunk_text(narrative)
    embeddings = embed_texts(chunks, task_type="RETRIEVAL_DOCUMENT")
    ids = [f"{report_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{**metadata, "report_id": report_id, "chunk_index": i} for i in range(len(chunks))]

    collection = get_collection()
    collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)


def delete_report_chunks(report_id: str):
    collection = get_collection()
    collection.delete(where={"report_id": report_id})


def semantic_search(query: str, n_results: int = 5, where: dict | None = None):
    """where: optional Chroma metadata filter, e.g. {"report_id": {"$in": [...]}}"""
    query_embedding = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
    )
    return results