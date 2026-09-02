"""The research agent: orchestrates search + LLM synthesis for all 5 sections.

This is deliberately a plain async generator rather than a "framework" agent
(no LangChain/etc.) -- for a 5-step, fixed-order pipeline like this, a
straightforward loop is easier to read, test, and reason about than a graph
of tool-calling abstractions.
"""
import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from app.agent.llm import GeminiClient, LLMError
from app.agent.schemas import SECTION_ORDER
from app.config import Settings

logger = logging.getLogger(__name__)


def _section_is_empty(section: str, data: dict) -> bool:
    """Decide whether a successfully-parsed section actually has no content."""
    if section == "overview":
        return not data.get("summary", "").strip()
    if section == "key_people":
        return not data.get("people")
    if section == "news":
        return not data.get("items")
    if section == "financials":
        return not any(data.get(f) for f in ("revenue", "employee_count", "market_cap", "yoy_growth"))
    if section == "risks":
        return not data.get("items")
    return False


class ResearchAgent:
    """Runs the 5-section research pipeline for a single company."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm_client = GeminiClient(settings)

    async def run(self, company_name: str) -> AsyncIterator[dict[str, Any]]:
        """Yield SSE-ready events: {"event": str, "data": dict}.

        Event types:
          started         -- research kicked off
          section_status  -- a section entered "searching" or "synthesizing"
          section_result  -- a section finished (status: complete|unavailable|error)
          sections_done   -- all 5 sections have been attempted (carries full results dict)
        """
        yield {
            "event": "started",
            "data": {
                "company_name": company_name,
                "mock_mode": {
                    "llm": self.llm_client.mock_mode,
                    "search": self.llm_client.mock_mode,
                },
            },
        }

        results: dict[str, dict] = {}
        # When running fully in mock mode there's no real network/API latency at all,
        # which would make the "streaming" UI (and the duplicate-request guard) hard to
        # observe. A small artificial delay keeps the demo experience realistic; it's
        # skipped entirely as soon as either provider is live, since real API calls
        # already take meaningful time.
        simulate_latency = (
            self.llm_client.mock_mode
            and "PYTEST_CURRENT_TEST" not in os.environ  # keep the test suite fast
        )

        for section in SECTION_ORDER:
            yield {"event": "section_status", "data": {"section": section, "status": "searching"}}
        if simulate_latency:
            await asyncio.sleep(3)
        for section in SECTION_ORDER:
            yield {"event": "section_status", "data": {"section": section, "status": "synthesizing"}}

        try:
            report = await self.llm_client.generate_report(company_name)
        except LLMError as exc:
            logger.info("LLM report generation failed for company=%r: %s", company_name, exc)
            for section in SECTION_ORDER:
                results[section] = {"status": "error", "data": None, "error": str(exc)}
                yield {"event": "section_result", "data": {"section": section, **results[section]}}
        else:
            for section in SECTION_ORDER:
                data = report[section]
                status = "unavailable" if _section_is_empty(section, data) else "complete"
                results[section] = {"status": status, "data": data, "error": None}
                yield {"event": "section_result", "data": {"section": section, **results[section]}}

        yield {"event": "sections_done", "data": {"results": results}}
