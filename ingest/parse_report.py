"""Parses the YAML-frontmatter markdown format used in data/*.md."""
import re
from pathlib import Path

import yaml


def write_report_file(report: dict, data_dir: Path) -> Path:
    """Writes a report dict out as a markdown file matching the frontmatter
    format parse_report_file expects, so it survives a future re-ingestion."""
    people_lines = "".join(f"  - {p}\n" for p in report.get("people_involved", []))
    content = (
        "---\n"
        f"report_id: {report['report_id']}\n"
        f"date: {report['date']}\n"
        f"location: {report.get('location', '')}\n"
        f"incident_type: {report.get('incident_type', '')}\n"
        "people_involved:\n"
        f"{people_lines}"
        f"reporting_officer: {report.get('reporting_officer', '')}\n"
        "---\n\n"
        f"# Incident Report {report['report_id']}\n\n"
        f"{report['narrative']}\n"
    )
    path = data_dir / f"{report['report_id'].lower().replace('-', '_')}.md"
    path.write_text(content, encoding="utf-8")
    return path


def parse_report_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path} is missing YAML frontmatter (--- ... ---)")

    frontmatter_raw, body = match.groups()
    meta = yaml.safe_load(frontmatter_raw)

    # Strip the leading "# Incident Report ..." heading from the narrative body.
    narrative = re.sub(r"^#.*\n+", "", body.strip())

    return {
        "report_id": str(meta["report_id"]),
        "date": str(meta["date"]),
        "location": meta.get("location", ""),
        "incident_type": meta.get("incident_type", ""),
        "reporting_officer": meta.get("reporting_officer", ""),
        "people_involved": meta.get("people_involved", []) or [],
        "narrative": narrative,
        "source_path": str(path),
    }