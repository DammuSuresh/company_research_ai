"""SQLAlchemy ORM models."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Report(Base):
    """A completed (or partially-completed) company research report.

    Each of the five section fields stores its section's structured data as
    JSON. A section that couldn't be researched (no data found, or an error)
    stores {"status": "error"|"unavailable", "data": None, "error": "..."}
    rather than fabricated content -- see app/agent/schemas.py.
    """

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    status: Mapped[str] = mapped_column(String(32), default="complete")  # complete | failed

    overview: Mapped[dict] = mapped_column(JSON, nullable=True)
    key_people: Mapped[dict] = mapped_column(JSON, nullable=True)
    news: Mapped[dict] = mapped_column(JSON, nullable=True)
    financials: Mapped[dict] = mapped_column(JSON, nullable=True)
    risks: Mapped[dict] = mapped_column(JSON, nullable=True)

    error_message: Mapped[str] = mapped_column(Text, nullable=True)
