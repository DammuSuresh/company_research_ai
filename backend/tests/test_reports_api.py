"""Integration tests for the REST endpoints (reports CRUD + health)."""


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_mock_mode"] is True
    assert body["search_mock_mode"] is True


def test_list_reports_empty_initially(client):
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_nonexistent_report_returns_404(client):
    resp = client.get("/api/reports/999")
    assert resp.status_code == 404


def test_delete_nonexistent_report_returns_404(client):
    resp = client.delete("/api/reports/999")
    assert resp.status_code == 404


def test_full_research_then_list_get_delete_flow(client):
    # 1. Kick off research (mock mode -- fully deterministic, no network calls).
    resp = client.post("/api/research", json={"company_name": "Acme Corp"})
    assert resp.status_code == 200
    assert "event: complete" in resp.text
    assert "event: sections_done" in resp.text

    # 2. The report should now be listed, newest first.
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    reports = resp.json()
    assert len(reports) == 1
    assert reports[0]["company_name"] == "Acme Corp"
    report_id = reports[0]["id"]

    # 3. Fetching the single report returns all 5 sections.
    resp = client.get(f"/api/reports/{report_id}")
    assert resp.status_code == 200
    detail = resp.json()
    for section in ("overview", "key_people", "news", "financials", "risks"):
        assert section in detail
        assert detail[section]["status"] in {"complete", "unavailable", "error"}

    # 4. Delete it.
    resp = client.delete(f"/api/reports/{report_id}")
    assert resp.status_code == 204

    # 5. It's gone.
    resp = client.get(f"/api/reports/{report_id}")
    assert resp.status_code == 404
    resp = client.get("/api/reports")
    assert resp.json() == []


def test_reports_are_returned_newest_first(client):
    client.post("/api/research", json={"company_name": "First Co"})
    client.post("/api/research", json={"company_name": "Second Co"})

    resp = client.get("/api/reports")
    names = [r["company_name"] for r in resp.json()]
    assert names == ["Second Co", "First Co"]
