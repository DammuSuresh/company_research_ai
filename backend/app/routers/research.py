import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agent.orchestrator import ResearchAgent
from app.agent.schemas import SECTION_ORDER
from app.config import get_settings
from app.database import get_db
from app.models import Report
from app.schemas import ResearchRequest
from app.sse import format_sse
from app.validators import is_researchable_company_name

logger = logging.getLogger(__name__)

router = APIRouter()


def _save_report(db: Session, company_name: str, results: dict) -> Report:
    report = Report(
        company_name=company_name,
        status="complete",
        overview=results.get("overview"),
        key_people=results.get("key_people"),
        news=results.get("news"),
        financials=results.get("financials"),
        risks=results.get("risks"),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.post("/research")
async def research(request: Request, body: ResearchRequest, db: Session = Depends(get_db)):
    company_name = body.company_name.strip()

    if not is_researchable_company_name(company_name):
        raise HTTPException(
            status_code=422,
            detail=(
                f"\"{company_name}\" doesn't look like a company name we can research. "
                "Try something like 'Acme Corp' or 'Salesforce'."
            ),
        )

    in_flight: set[str] = request.app.state.in_flight
    key = company_name.lower()
    if key in in_flight:
        raise HTTPException(
            status_code=409,
            detail=f"Research for \"{company_name}\" is already in progress.",
        )
    in_flight.add(key)

    settings = get_settings()
    agent = ResearchAgent(settings)

    async def event_stream():
        results: dict = {}
        try:
            async for evt in agent.run(company_name):
                if evt["event"] == "sections_done":
                    results = evt["data"]["results"]
                yield format_sse(evt["event"], evt["data"])

            # Ensure every section has *some* entry even if the loop above
            # was somehow short-circuited, so the saved report is well-formed.
            for section in SECTION_ORDER:
                results.setdefault(section, {"status": "error", "data": None, "error": "Section did not complete."})

            report = _save_report(db, company_name, results)
            yield format_sse(
                "complete",
                {
                    "report_id": report.id,
                    "company_name": report.company_name,
                    "created_at": report.created_at.isoformat(),
                },
            )
        except Exception:
            logger.exception("Unhandled error while researching %r", company_name)
            yield format_sse(
                "error",
                {"message": "Something went wrong while researching this company. Please try again."},
            )
        finally:
            in_flight.discard(key)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
