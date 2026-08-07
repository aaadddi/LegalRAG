"""
Looks at the user's question and decides which retrieval path to use:
- Named a person -> filter SQLite by person first
- Named/implied a date range -> filter SQLite by date first
- Neither -> pure semantic search over everything

This reuses spaCy NER rather than a second Gemini call, since it's a cheap,
local, deterministic classification step - no need to spend an API call
just to figure out routing.
"""
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import spacy
from dateutil import parser as date_parser

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


@dataclass
class QueryIntent:
    raw_query: str
    people: list[str] = field(default_factory=list)
    date_start: str | None = None
    date_end: str | None = None

    @property
    def has_filters(self) -> bool:
        return bool(self.people or self.date_start or self.date_end)


# Loose month-range phrases like "in March", "last quarter", "this year"
# spaCy's DATE entities catch a lot, but not relative phrases well - handle
# the common ones explicitly.
RELATIVE_PATTERNS = {
    r"\blast month\b": lambda today: _month_range(today, months_back=1),
    r"\bthis month\b": lambda today: _month_range(today, months_back=0),
    r"\blast quarter\b": lambda today: _quarter_range(today, quarters_back=1),
    r"\bthis quarter\b": lambda today: _quarter_range(today, quarters_back=0),
    r"\bthis year\b": lambda today: (date(today.year, 1, 1), today),
    r"\blast year\b": lambda today: (date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)),
}


def _month_range(today: date, months_back: int):
    year, month = today.year, today.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    start = date(year, month, 1)
    next_month = date(year + (month // 12), (month % 12) + 1, 1)
    end = next_month - timedelta(days=1)
    return start, end


def _quarter_range(today: date, quarters_back: int):
    current_q = (today.month - 1) // 3
    target_q = current_q - quarters_back
    year = today.year
    while target_q < 0:
        target_q += 4
        year -= 1
    start_month = target_q * 3 + 1
    start = date(year, start_month, 1)
    end_month = start_month + 2
    next_month = date(year + (end_month // 12), (end_month % 12) + 1, 1)
    end = next_month - timedelta(days=1)
    return start, end


def _month_range_for(year: int, month: int):
    start = date(year, month, 1)
    next_month = date(year + (month // 12), (month % 12) + 1, 1)
    end = next_month - timedelta(days=1)
    return start, end


def parse_query(query: str, today: date | None = None) -> QueryIntent:
    today = today or date.today()
    doc = get_nlp()(query)

    people = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

    date_start, date_end = None, None

    # 1. Check relative-phrase patterns first (spaCy often mislabels these).
    lowered = query.lower()
    for pattern, resolver in RELATIVE_PATTERNS.items():
        if re.search(pattern, lowered):
            start, end = resolver(today)
            date_start, date_end = start.isoformat(), end.isoformat()
            break

    # 2. Fall back to spaCy DATE entities parsed via dateutil.
    if not date_start:
        date_ents = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
        for ent_text in date_ents:
            try:
                # Parse twice with different sentinel defaults - if the day
                # component differs between the two, the text didn't actually
                # specify a day (e.g. "January 2026"), so treat it as a
                # month-only mention and expand to the full month.
                default_a = datetime(2000, 1, 1)
                default_b = datetime(2010, 6, 15)
                parsed_a = date_parser.parse(ent_text, fuzzy=True, default=default_a)
                parsed_b = date_parser.parse(ent_text, fuzzy=True, default=default_b)

                if parsed_a.day != parsed_b.day:
                    # Day wasn't specified - use the real parse (against
                    # today's year as default) and expand to the full month.
                    real = date_parser.parse(ent_text, fuzzy=True, default=datetime(today.year, 1, 1))
                    start, end = _month_range_for(real.year, real.month)
                    date_start, date_end = start.isoformat(), end.isoformat()
                else:
                    real = date_parser.parse(ent_text, fuzzy=True, default=datetime(today.year, 1, 1))
                    date_start = date_end = real.date().isoformat()
                break
            except (ValueError, OverflowError):
                continue

    return QueryIntent(raw_query=query, people=people, date_start=date_start, date_end=date_end)