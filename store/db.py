"""
Structured store: one row per incident report, plus a normalized
people-to-report join table so we can query "all incidents involving X"
without scanning text.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "./store/incidents.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    report_id       TEXT PRIMARY KEY,
    date            TEXT NOT NULL,
    location        TEXT,
    incident_type   TEXT,
    reporting_officer TEXT,
    narrative       TEXT NOT NULL,
    source_path     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS report_people (
    report_id   TEXT NOT NULL,
    person_name TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports(report_id)
);

CREATE INDEX IF NOT EXISTS idx_report_people_name ON report_people(person_name);
CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(date);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(incident_type);
"""


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def upsert_report(conn, report: dict):
    conn.execute(
        """
        INSERT INTO reports (report_id, date, location, incident_type,
                              reporting_officer, narrative, source_path)
        VALUES (:report_id, :date, :location, :incident_type,
                :reporting_officer, :narrative, :source_path)
        ON CONFLICT(report_id) DO UPDATE SET
            date=excluded.date,
            location=excluded.location,
            incident_type=excluded.incident_type,
            reporting_officer=excluded.reporting_officer,
            narrative=excluded.narrative,
            source_path=excluded.source_path
        """,
        report,
    )
    conn.execute("DELETE FROM report_people WHERE report_id = ?", (report["report_id"],))
    for person in report.get("people_involved", []):
        conn.execute(
            "INSERT INTO report_people (report_id, person_name) VALUES (?, ?)",
            (report["report_id"], person),
        )


def find_reports_by_person(conn, person_name: str):
    rows = conn.execute(
        """
        SELECT r.* FROM reports r
        JOIN report_people rp ON rp.report_id = r.report_id
        WHERE rp.person_name LIKE ?
        ORDER BY r.date ASC
        """,
        (f"%{person_name}%",),
    ).fetchall()
    return [dict(row) for row in rows]


def find_reports_by_date_range(conn, start_date: str, end_date: str):
    rows = conn.execute(
        "SELECT * FROM reports WHERE date BETWEEN ? AND ? ORDER BY date ASC",
        (start_date, end_date),
    ).fetchall()
    return [dict(row) for row in rows]


def get_report(conn, report_id: str):
    row = conn.execute("SELECT * FROM reports WHERE report_id = ?", (report_id,)).fetchone()
    return dict(row) if row else None


def get_report_people(conn, report_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT person_name FROM report_people WHERE report_id = ? ORDER BY person_name",
        (report_id,),
    ).fetchall()
    return [row["person_name"] for row in rows]


def get_report_with_people(conn, report_id: str):
    report = get_report(conn, report_id)
    if not report:
        return None
    report["people_involved"] = get_report_people(conn, report_id)
    return report


def delete_report(conn, report_id: str) -> bool:
    """Returns True if a report existed and was deleted, False if it didn't exist."""
    existing = conn.execute("SELECT 1 FROM reports WHERE report_id = ?", (report_id,)).fetchone()
    if not existing:
        return False
    conn.execute("DELETE FROM report_people WHERE report_id = ?", (report_id,))
    conn.execute("DELETE FROM reports WHERE report_id = ?", (report_id,))
    return True


def get_next_report_id(conn) -> str:
    """Generates the next sequential INC-XXXX id based on existing report_ids."""
    rows = conn.execute("SELECT report_id FROM reports").fetchall()
    max_n = 0
    for row in rows:
        rid = row["report_id"]
        if rid.startswith("INC-"):
            try:
                n = int(rid.split("-")[1])
                max_n = max(max_n, n)
            except (ValueError, IndexError):
                continue
    return f"INC-{max_n + 1:04d}"