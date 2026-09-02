"""Tests for the POST /api/research SSE endpoint's HTTP-level behavior."""
from app.agent.schemas import SECTION_ORDER
from app.main import app


def test_invalid_company_name_rejected_before_streaming(client):
    resp = client.post("/api/research", json={"company_name": "???"})
    assert resp.status_code == 422
    assert "doesn't look like a company name" in resp.json()["detail"]


def test_blank_company_name_rejected_by_schema(client):
    resp = client.post("/api/research", json={"company_name": "   "})
    assert resp.status_code == 422


def test_missing_company_name_field(client):
    resp = client.post("/api/research", json={})
    assert resp.status_code == 422


def test_stream_contains_all_sections_in_order(client):
    resp = client.post("/api/research", json={"company_name": "Acme Corp"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    body = resp.text
    assert "event: started" in body
    for section in SECTION_ORDER:
        assert f'"section": "{section}"' in body

    # Sections must appear in the documented order (overview -> people -> news -> financials -> risks).
    positions = [body.index(f'"section": "{s}"') for s in SECTION_ORDER]
    assert positions == sorted(positions)


def test_duplicate_concurrent_research_is_rejected(client):
    """Simulates an in-flight request by pre-populating app.state.in_flight,
    which is exactly what a real concurrent second request would observe."""
    key = "duplicate co"
    app.state.in_flight.add(key)
    try:
        resp = client.post("/api/research", json={"company_name": "Duplicate Co"})
        assert resp.status_code == 409
        assert "already in progress" in resp.json()["detail"]
    finally:
        app.state.in_flight.discard(key)


def test_research_still_completes_when_a_section_fails(client, monkeypatch):
    from app.agent.llm import GeminiClient, LLMError

    original_generate = GeminiClient.generate_report

    async def flaky_generate(self, company_name):
        raise LLMError("simulated provider outage")

    monkeypatch.setattr(GeminiClient, "generate_report", flaky_generate)

    resp = client.post("/api/research", json={"company_name": "Acme Corp"})
    assert resp.status_code == 200
    body = resp.text
    assert '"section": "financials", "status": "error"' in body
    # The rest of the pipeline should still finish and save the report.
    assert "event: complete" in body
