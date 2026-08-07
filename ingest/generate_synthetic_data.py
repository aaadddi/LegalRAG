"""
Generates synthetic incident reports as markdown files with YAML frontmatter,
matching the format in data/sample_report_0001.md.

Run:
    python ingest/generate_synthetic_data.py --count 40

Requires GOOGLE_API_KEY in your environment (see .env.example).
"""
import argparse
import os
import random
import re
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# A recurring cast so people show up across multiple reports -> makes
# person-profiling actually interesting to query later.
PEOPLE = [
    "Marcus Reyes", "David Chen", "Priya Nataraj", "Sofia Alvarez",
    "James Whitfield", "Angela Brooks", "Tomas Kowalski", "Lena Fischer",
    "Omar Haddad", "Grace Okafor",
]
INCIDENT_TYPES = [
    "Workplace Altercation", "Property Damage", "Safety Violation",
    "Theft Report", "Harassment Complaint", "Equipment Malfunction",
    "Unauthorized Access", "Noise Complaint",
]
LOCATIONS = [
    "Warehouse B, Loading Dock 3", "Main Office, 2nd Floor Break Room",
    "Parking Structure C", "Server Room 1", "Front Reception",
    "Warehouse A, Aisle 12", "Executive Conference Room",
]

PROMPT_TEMPLATE = """Write a realistic, professional workplace incident report narrative,
3-5 sentences, in the style of a security/HR incident log. This is entirely
fictional data for a software testing dataset - no real people, places, or events.

Incident type: {incident_type}
Location: {location}
People involved: {people}
Date: {report_date}

Write ONLY the narrative paragraph. No headers, no frontmatter, no preamble.
"""


def slugify_id(n: int) -> str:
    return f"INC-{n:04d}"


def random_date() -> date:
    start = date(2025, 9, 1)
    end = date(2026, 8, 1)
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def generate_one(client: "genai.Client", model: str, n: int) -> str:
    incident_type = random.choice(INCIDENT_TYPES)
    location = random.choice(LOCATIONS)
    people = random.sample(PEOPLE, k=random.choice([1, 2]))
    report_date = random_date()
    officer = "Officer T. Alvarez"

    prompt = PROMPT_TEMPLATE.format(
        incident_type=incident_type,
        location=location,
        people=", ".join(people),
        report_date=report_date.isoformat(),
    )

    response = client.models.generate_content(model=model, contents=prompt)
    narrative = response.text.strip()

    report_id = slugify_id(n)
    frontmatter = (
        "---\n"
        f"report_id: {report_id}\n"
        f"date: {report_date.isoformat()}\n"
        f"location: {location}\n"
        f"incident_type: {incident_type}\n"
        "people_involved:\n"
        + "".join(f"  - {p}\n" for p in people)
        + f"reporting_officer: {officer}\n"
        "---\n\n"
        f"# Incident Report {report_id}\n\n"
        f"{narrative}\n"
    )
    return frontmatter, report_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--model", default=os.getenv("GEMINI_GENERATION_MODEL", "gemini-2.5-flash"))
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit(
            "GOOGLE_API_KEY not set. Copy .env.example to .env and add your key "
            "from https://aistudio.google.com"
        )

    client = genai.Client(api_key=api_key)
    DATA_DIR.mkdir(exist_ok=True)

    # Start numbering after existing sample files so we don't overwrite them.
    existing = list(DATA_DIR.glob("sample_report_*.md"))
    start_n = len(existing) + 1

    for i in range(args.count):
        n = start_n + i
        content, report_id = generate_one(client, args.model, n)
        out_path = DATA_DIR / f"sample_report_{n:04d}.md"
        out_path.write_text(content, encoding="utf-8")
        print(f"Wrote {out_path.name} ({report_id})")

    print(f"\nDone. Generated {args.count} reports in {DATA_DIR}")


if __name__ == "__main__":
    main()