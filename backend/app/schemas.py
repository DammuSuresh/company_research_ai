"""Pydantic schemas for API request/response bodies."""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ResearchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)

    @field_validator("company_name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("company_name must not be blank")
        return v


class KeyPerson(BaseModel):
    name: str
    title: str


class Financials(BaseModel):
    revenue: str | None = None
    employee_count: str | None = None
    market_cap: str | None = None
    yoy_growth: str | None = None


class SectionResult(BaseModel):
    """Generic wrapper for a single report section's outcome."""

    status: str  # "complete" | "unavailable" | "error"
    data: dict | list | str | None = None
    error: str | None = None


class ReportSummary(BaseModel):
    """Lightweight representation used in the report history list."""

    id: int
    company_name: str
    created_at: datetime
    status: str

    model_config = {"from_attributes": True}


class ReportDetail(BaseModel):
    """Full report with all section data."""

    id: int
    company_name: str
    created_at: datetime
    status: str
    overview: dict | None = None
    key_people: dict | None = None
    news: dict | None = None
    financials: dict | None = None
    risks: dict | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}
