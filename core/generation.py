"""
Takes retrieved chunks + the user's question, calls Gemini via google-genai,
and returns an answer that cites report IDs/dates inline.
"""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GENERATION_MODEL = os.getenv("GEMINI_GENERATION_MODEL", "gemini-2.5-flash")

_client = None

SYSTEM_INSTRUCTION = """You are a legal/HR records assistant. You answer questions
about incident reports using ONLY the context provided below - never from
outside knowledge or assumptions.

Rules:
- Every factual claim must be followed by a citation in the form [Report ID, date].
- If the context doesn't contain enough information to answer, say so plainly -
  do not guess or fabricate details.
- If multiple reports are relevant, synthesize across them, citing each one.
- Be concise and factual. This is for records review, not casual conversation.
"""


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set - copy .env.example to .env")
        _client = genai.Client(api_key=api_key)
    return _client


def _format_context(chunks: list[dict]) -> str:
    if not chunks:
        return "(No relevant reports were found.)"

    blocks = []
    for c in chunks:
        meta = c["metadata"]
        header = f"[Report {meta.get('report_id')}, {meta.get('date')}] " \
                  f"({meta.get('incident_type', 'unknown type')}, {meta.get('location', 'unknown location')})"
        blocks.append(f"{header}\n{c['text']}")
    return "\n\n---\n\n".join(blocks)


def generate_answer(query: str, chunks: list[dict]) -> str:
    context = _format_context(chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"

    client = get_client()
    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
        ),
    )
    return response.text