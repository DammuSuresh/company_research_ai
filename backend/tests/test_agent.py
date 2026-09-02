"""Unit tests for the research agent's building blocks (mock mode)."""
import pytest

from app.agent.llm import GeminiClient
from app.agent.orchestrator import ResearchAgent, _section_is_empty
from app.agent.schemas import SECTION_ORDER, SECTION_SCHEMAS
from app.agent.search import GoogleSearchClient
from app.config import Settings


@pytest.fixture()
def mock_settings():
    return Settings(gemini_api_key=None)


def test_search_client_defaults_to_mock_mode(mock_settings):
    client = GoogleSearchClient(mock_settings)
    assert client.mock_mode is True


def test_llm_client_defaults_to_mock_mode(mock_settings):
    client = GeminiClient(mock_settings)
    assert client.mock_mode is True


@pytest.mark.asyncio
async def test_mock_search_returns_nonempty_results(mock_settings):
    client = GoogleSearchClient(mock_settings)
    results = await client.search("Acme Corp overview")
    assert len(results) > 0
    for r in results:
        assert {"title", "snippet", "link"} <= r.keys()


@pytest.mark.asyncio
async def test_mock_llm_generates_schema_valid_data_for_every_section(mock_settings):
    client = GeminiClient(mock_settings)
    report = await client.generate_report("Acme Corp")
    assert set(report) == set(SECTION_ORDER)
    for section, data in report.items():
        SECTION_SCHEMAS[section].model_validate(data)


@pytest.mark.asyncio
async def test_mock_financials_are_all_null_not_fabricated(mock_settings):
    """The brief is explicit: never fabricate a financial number."""
    client = GeminiClient(mock_settings)
    data = (await client.generate_report("Acme Corp"))["financials"]
    assert all(v is None for v in data.values())


def test_section_is_empty_detects_missing_data():
    assert _section_is_empty("overview", {"summary": ""})
    assert not _section_is_empty("overview", {"summary": "Acme makes widgets."})
    assert _section_is_empty("key_people", {"people": []})
    assert not _section_is_empty("key_people", {"people": [{"name": "A", "title": "CEO"}]})
    assert _section_is_empty("financials", {"revenue": None, "employee_count": None, "market_cap": None, "yoy_growth": None})
    assert not _section_is_empty("financials", {"revenue": "$1B", "employee_count": None, "market_cap": None, "yoy_growth": None})
    assert _section_is_empty("risks", {"items": []})
    assert _section_is_empty("news", {"items": []})


@pytest.mark.asyncio
async def test_orchestrator_yields_full_event_sequence(mock_settings):
    agent = ResearchAgent(mock_settings)
    events = [evt async for evt in agent.run("Acme Corp")]

    event_types = [e["event"] for e in events]
    assert event_types[0] == "started"
    assert event_types[-1] == "sections_done"
    assert event_types.count("section_result") == len(SECTION_ORDER)

    sections_seen = [e["data"]["section"] for e in events if e["event"] == "section_result"]
    assert sections_seen == SECTION_ORDER

    final = events[-1]["data"]["results"]
    assert set(final.keys()) == set(SECTION_ORDER)
    for section, result in final.items():
        assert result["status"] in {"complete", "unavailable", "error"}


@pytest.mark.asyncio
async def test_orchestrator_continues_after_a_section_llm_failure(mock_settings, monkeypatch):
    """A single grounded Gemini call failing must not abort the whole run."""

    async def failing_generate(self, company_name):
        from app.agent.llm import LLMError

        raise LLMError("simulated provider outage")

    monkeypatch.setattr(GeminiClient, "generate_report", failing_generate)

    agent = ResearchAgent(mock_settings)
    events = [evt async for evt in agent.run("Acme Corp")]

    results = events[-1]["data"]["results"]
    assert all(r["status"] == "error" for r in results.values())
    # Every section should still have been attempted despite each one failing.
    assert set(results.keys()) == set(SECTION_ORDER)
