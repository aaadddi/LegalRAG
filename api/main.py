"""
FastAPI backend for the legal incident RAG app.

Run:
    uvicorn api.main:app --reload

Endpoints:
    POST /query                  - ask a question, get a cited answer
    GET  /profile/{person_name}  - all incidents involving a person, date-sorted
    GET  /reports                - list/filter reports by date range
    POST /reports                - create a report
    GET  /reports/{report_id}    - fetch a single report
    PUT  /reports/{report_id}    - update a report
    DELETE /reports/{report_id}  - delete a report
    GET  /health                 - basic liveness check
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.rag_engine import answer as rag_answer
from store.db import (
    init_db, get_conn, find_reports_by_person, find_reports_by_date_range,
    get_report, get_report_with_people, delete_report, get_next_report_id, upsert_report,
)
from store.vector_store import add_report_chunks, delete_report_chunks
from ingest.parse_report import write_report_file

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

app = FastAPI(title="Legal Incident RAG API", version="0.1.0")

# Wide open for local dev / Streamlit on a different port. Tighten this
# before deploying anywhere public - restrict to your actual frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ---------- Schemas ----------

class QueryRequest(BaseModel):
    question: str


class QuerySource(BaseModel):
    report_id: str | None
    date: str | None
    incident_type: str | None
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[QuerySource]
    routing: dict


class ReportSummary(BaseModel):
    report_id: str
    date: str
    location: str | None
    incident_type: str | None
    reporting_officer: str | None


class ReportCreate(BaseModel):
    report_id: str | None = Field(None, description="Auto-generated as INC-XXXX if omitted")
    date: str = Field(..., description="YYYY-MM-DD")
    location: str = ""
    incident_type: str = ""
    reporting_officer: str = ""
    people_involved: list[str] = []
    narrative: str = Field(..., min_length=1)


class ReportUpdate(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    location: str = ""
    incident_type: str = ""
    reporting_officer: str = ""
    people_involved: list[str] = []
    narrative: str = Field(..., min_length=1)


class ReportDetail(ReportSummary):
    narrative: str
    source_path: str
    people_involved: list[str] = []


def _index_report_vectors(report_id: str, req: ReportCreate | ReportUpdate):
    delete_report_chunks(report_id)
    add_report_chunks(
        report_id=report_id,
        narrative=req.narrative,
        metadata={
            "date": req.date,
            "incident_type": req.incident_type,
            "location": req.location,
            "people": ", ".join(req.people_involved),
        },
    )


def _save_report(report: dict) -> dict:
    path = write_report_file(report, DATA_DIR)
    report["source_path"] = str(path)
    with get_conn() as conn:
        upsert_report(conn, report)
    try:
        _index_report_vectors(
            report["report_id"],
            ReportUpdate(
                date=report["date"],
                location=report.get("location") or "",
                incident_type=report.get("incident_type") or "",
                reporting_officer=report.get("reporting_officer") or "",
                people_involved=report.get("people_involved") or [],
                narrative=report["narrative"],
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=207,
            detail=(
                "Report saved to database but embedding failed (won't appear in "
                f"semantic search until re-ingested): {e}"
            ),
        )
    with get_conn() as conn:
        return get_report_with_people(conn, report["report_id"])


# ---------- Routes ----------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")
    result = rag_answer(req.question)
    return result


@app.get("/profile/{person_name}", response_model=list[ReportSummary])
def profile(person_name: str):
    with get_conn() as conn:
        reports = find_reports_by_person(conn, person_name)
    if not reports:
        raise HTTPException(status_code=404, detail=f"No reports found for '{person_name}'")
    return reports


@app.get("/reports", response_model=list[ReportSummary])
def list_reports(
    start_date: str | None = Query(None, description="YYYY-MM-DD"),
    end_date: str | None = Query(None, description="YYYY-MM-DD"),
):
    with get_conn() as conn:
        if start_date and end_date:
            reports = find_reports_by_date_range(conn, start_date, end_date)
        else:
            reports = conn.execute("SELECT * FROM reports ORDER BY date ASC").fetchall()
            reports = [dict(r) for r in reports]
    return reports


@app.post("/reports", response_model=ReportDetail, status_code=201)
def create_report(req: ReportCreate):
    with get_conn() as conn:
        report_id = req.report_id or get_next_report_id(conn)

        if get_report(conn, report_id):
            raise HTTPException(status_code=409, detail=f"Report '{report_id}' already exists")

        report = {
            "report_id": report_id,
            "date": req.date,
            "location": req.location,
            "incident_type": req.incident_type,
            "reporting_officer": req.reporting_officer,
            "people_involved": req.people_involved,
            "narrative": req.narrative,
        }

    return _save_report(report)


@app.put("/reports/{report_id}", response_model=ReportDetail)
def update_report(report_id: str, req: ReportUpdate):
    with get_conn() as conn:
        existing = get_report(conn, report_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

        report = {
            "report_id": report_id,
            "date": req.date,
            "location": req.location,
            "incident_type": req.incident_type,
            "reporting_officer": req.reporting_officer,
            "people_involved": req.people_involved,
            "narrative": req.narrative,
        }

    return _save_report(report)


@app.delete("/reports/{report_id}", status_code=204)
def remove_report(report_id: str):
    with get_conn() as conn:
        report = get_report(conn, report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
        deleted = delete_report(conn, report_id)

    # Remove from the vector store too, so it stops showing up in semantic search.
    delete_report_chunks(report_id)

    # Remove the backing markdown file, if one exists, so re-ingestion doesn't
    # resurrect it.
    source_path = report.get("source_path")
    if source_path and Path(source_path).exists():
        Path(source_path).unlink()

    return None


@app.get("/reports/{report_id}", response_model=ReportDetail)
def report_detail(report_id: str):
    with get_conn() as conn:
        report = get_report_with_people(conn, report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return report