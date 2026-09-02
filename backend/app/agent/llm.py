"""LLM synthesis via Google Gemini.

Docs: https://ai.google.dev/gemini-api/docs

Falls back to deterministic mock output when GEMINI_API_KEY is not
configured. The aggregate call site (`generate_report`) is identical for both
branches -- swapping in a real key requires no code changes elsewhere.
"""
import asyncio
import json
import logging

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.agent.prompts import build_research_prompt
from app.agent.schemas import SECTION_RESPONSE_KEYS, SECTION_SCHEMAS
from app.config import Settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM provider fails or returns unparseable output."""


class GeminiClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self.mock_mode = settings.llm_mock_mode
        if not self.mock_mode:
            self._client = genai.Client(api_key=settings.gemini_api_key)

    async def generate_report(self, company_name: str) -> dict[str, dict]:
        """Research and validate all five report sections in one Gemini call."""
        prompt = build_research_prompt(company_name)
        raw = self._mock_report(company_name) if self.mock_mode else await self._live_generate(prompt)

        report: dict[str, dict] = {}
        try:
            for section, response_key in SECTION_RESPONSE_KEYS.items():
                report[section] = SECTION_SCHEMAS[section].model_validate(raw[response_key]).model_dump()
        except (KeyError, ValidationError) as exc:
            raise LLMError(f"LLM returned data that didn't match the report schema: {exc}") from exc
        return report

    async def _live_generate(self, prompt: str) -> dict:
        def _call() -> str:
            response = self._client.models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    tools=[{"google_search": {}}],
                ),
            )
            return response.text

        try:
            text = await asyncio.to_thread(_call)
        except Exception as exc:  # Gemini SDK raises various exception types
            logger.warning("Gemini generation failed: %s", exc)
            raise LLMError(f"LLM request failed: {exc}") from exc

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM did not return valid JSON: {exc}") from exc

    @staticmethod
    def _mock_generate(section: str, company_name: str) -> dict:
        """Deterministic mock data, clearly labeled as simulated.

        Financials are intentionally returned as all-null: this both avoids
        fabricating numbers (the brief is explicit that unknown metrics must
        be null, never guessed) and exercises the "missing data" UI state
        without needing a real company with no financial data.
        """
        note = "(Simulated data — configure GEMINI_API_KEY and Google Search credentials for a live briefing.)"

        if section == "overview":
            return {
                "summary": (
                    f"{company_name} is presented here with simulated data because no live API keys "
                    f"are configured. {note} In live mode, this section summarizes {company_name}'s "
                    "industry, core products/services, target customers, and market positioning, "
                    "grounded in real-time web search results."
                )
            }
        if section == "key_people":
            return {
                "people": [
                    {"name": "Simulated Executive", "title": "Chief Executive Officer"},
                    {"name": "Simulated Executive", "title": "Chief Technology Officer"},
                ]
            }
        if section == "news":
            return {
                "items": [
                    f"Simulated headline: {company_name} recent announcement. {note}",
                    f"Simulated headline: {company_name} product or partnership update.",
                ]
            }
        if section == "financials":
            return {"revenue": None, "employee_count": None, "market_cap": None, "yoy_growth": None}
        if section == "risks":
            return {
                "items": [
                    f"Simulated risk factor placeholder for {company_name}. {note}",
                ]
            }
        raise ValueError(f"Unknown section: {section}")

    @classmethod
    def _mock_report(cls, company_name: str) -> dict[str, dict]:
        return {
            response_key: cls._mock_generate(section, company_name)
            for section, response_key in SECTION_RESPONSE_KEYS.items()
        }
