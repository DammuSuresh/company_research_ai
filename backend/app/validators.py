"""Lightweight input validation for the research endpoint.

This is intentionally simple: a full "is this a real company" check would
require its own model/lookup call. Instead we filter out obvious junk
(empty, punctuation-only, no letters at all) up front so the UI can show an
"invalid input" state immediately rather than burning a search+LLM round
trip on unresearchable input. Anything that passes this check but genuinely
has no findable information is instead handled gracefully downstream via
per-section "unavailable" statuses.
"""
import re

_HAS_LETTER = re.compile(r"[A-Za-z]")


def is_researchable_company_name(name: str) -> bool:
    name = name.strip()
    if len(name) < 2:
        return False
    if not _HAS_LETTER.search(name):
        return False
    # Reject strings that are almost entirely repeated/non-alphanumeric noise, e.g. "asdkjhaskjdh", "!!!???"
    alnum_ratio = sum(c.isalnum() or c.isspace() for c in name) / len(name)
    if alnum_ratio < 0.6:
        return False
    return True
