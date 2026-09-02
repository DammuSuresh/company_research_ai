"""Prompt construction for each report section."""
import json

from app.agent.schemas import SECTION_RESPONSE_KEYS, SECTION_SCHEMAS

_SECTION_INSTRUCTIONS = {
    "overview": (
        "Write the company overview a sales rep needs before a meeting: what the company does, "
        "its industry, core products/services, target customers, and market positioning. "
        "It should read like a briefing, not an encyclopedia entry."
    ),
    "key_people": (
        "Identify key executives and senior leadership relevant to a sales conversation "
        "(CEO, CTO, CFO, CIO, CISO, etc.). Only include people you can find in the search results. "
        "If none are found, return an empty list -- do not invent names."
    ),
    "news": (
        "Summarize 3-4 recent, newsworthy items: acquisitions, earnings, product launches, "
        "partnerships, layoffs, leadership changes. Prefer items with a specific date or timeframe. "
        "Only use information present in the search results -- do not fabricate events."
    ),
    "financials": (
        "Extract revenue, employee count, market cap, and year-over-year growth. "
        "If a metric is not present in the search results (e.g. a private company has no market cap), "
        "set that field to null. Never estimate or fabricate a number."
    ),
    "risks": (
        "Identify 2-3 concrete risk factors a sales rep should be aware of: regulatory scrutiny, "
        "security breaches, competitive threats, pending litigation, financial instability. "
        "Base these only on what the search results indicate -- do not speculate."
    ),
}


def build_search_queries(section: str, company_name: str) -> list[str]:
    """Return the web search queries used to gather source material for a section."""
    if section == "overview":
        return [f"{company_name} company overview products services"]
    if section == "key_people":
        return [f"{company_name} CEO CTO CFO executives leadership team"]
    if section == "news":
        return [f"{company_name} news 2026", f"{company_name} announcement OR acquisition OR earnings"]
    if section == "financials":
        return [f"{company_name} revenue employees market cap financials"]
    if section == "risks":
        return [f"{company_name} risk factors lawsuit OR investigation OR security breach OR competition"]
    raise ValueError(f"Unknown section: {section}")


def build_research_prompt(company_name: str) -> str:
    section_schemas = {
        SECTION_RESPONSE_KEYS[section]: schema.model_json_schema()
        for section, schema in SECTION_SCHEMAS.items()
    }
    tasks = "\n".join(
        f"- {SECTION_RESPONSE_KEYS[section]}: {_SECTION_INSTRUCTIONS[section]}"
        for section in SECTION_SCHEMAS
    )
    queries = "\n".join(
        f"- {query}"
        for section in SECTION_SCHEMAS
        for query in build_search_queries(section, company_name)
    )
    return f"""You are a research analyst preparing a briefing for a sales rep about to meet with "{company_name}".

Research all five areas in this single task:
{tasks}

Use Google Search grounding to find current, authoritative sources. Suggested queries:
{queries}

Ground every claim ONLY in the sources returned by Google Search grounding. If sources do not
contain enough information to fill a field, leave it null / empty rather than guessing.

Respond with ONLY one valid JSON object, with exactly these top-level keys:
{json.dumps(section_schemas, indent=2)}
Do not use markdown fences or commentary.
"""
