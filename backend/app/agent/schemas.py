"""Pydantic models describing the expected shape of each report section.

These serve three purposes:
  1. They're embedded in the Gemini prompt so the model knows exactly what
     JSON shape to return.
  2. They validate/parse the LLM's JSON response.
  3. They document the section contract used by both mock and live modes.
"""
from pydantic import BaseModel, Field

SECTION_ORDER = ["overview", "key_people", "news", "financials", "risks"]

SECTION_TITLES = {
    "overview": "Company Overview",
    "key_people": "Key People",
    "news": "Recent News",
    "financials": "Financial Highlights",
    "risks": "Risk Factors",
}

SECTION_RESPONSE_KEYS = {
    "overview": "company_overview",
    "key_people": "key_people",
    "news": "recent_news",
    "financials": "financial_highlights",
    "risks": "risk_factors",
}


class OverviewData(BaseModel):
    summary: str = Field(description="2-4 sentence briefing: industry, core products/services, target customers, market positioning.")


class KeyPersonItem(BaseModel):
    name: str
    title: str


class KeyPeopleData(BaseModel):
    people: list[KeyPersonItem] = Field(default_factory=list)


class NewsData(BaseModel):
    items: list[str] = Field(default_factory=list, description="3-4 bullet points of recent, dated news.")


class FinancialsData(BaseModel):
    revenue: str | None = None
    employee_count: str | None = None
    market_cap: str | None = None
    yoy_growth: str | None = None


class RisksData(BaseModel):
    items: list[str] = Field(default_factory=list, description="2-3 bullet points of concrete risk factors.")


SECTION_SCHEMAS: dict[str, type[BaseModel]] = {
    "overview": OverviewData,
    "key_people": KeyPeopleData,
    "news": NewsData,
    "financials": FinancialsData,
    "risks": RisksData,
}
