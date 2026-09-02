# Company Research Tool

A sales rep types in a company name; an AI agent researches it with live web search and Gemini, streaming a 5-section briefing to the screen in real time. Reports are saved to SQLite and can be browsed, reopened, and deleted.

```
Backend:  Python + FastAPI + SQLite (SQLAlchemy)
Frontend: React + TypeScript + Tailwind CSS v4 (Vite)
AI:       Google Gemini (gemini-2.5-flash by default)
Search:   Google Programmable Search Engine (Custom Search JSON API)
```

## Quick start

Two terminals, two commands. No Docker, no external database.

```bash
# Terminal 1 — backend (http://localhost:8000)
# Use Python 3.13.x for this project. Python 3.14 can fail while building pydantic-core.

# (For MAC/Linux)
cd backend
python3.13 -m venv .venv && source .venv/bin/activate

# (For Windows PowerShell)
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 2 — frontend (http://localhost:5173)
cd frontend
npm install
npm start
```

Open **http://localhost:5173**. That's it — **no API keys are required to run the app.** With no keys configured, the backend automatically runs in **mock mode**: the exact same search → LLM → save pipeline runs, but the search and LLM calls return clearly-labeled simulated data instead of hitting a real API. This lets you see the full streaming UI, all five sections, the history sidebar, and every UI state without spending a cent or waiting on any signup.

To get **live** results, add your own API keys — see [Configuring API keys](#configuring-api-keys) below.

## Which providers, and why

| Concern | Choice | Why |
|---|---|---|
| LLM and search | **Google Gemini** (`gemini-3.6-flash`) with native Google Search grounding | Gemini performs the research and returns schema-validated JSON in one grounded call per section. |

The integration is a complete implementation in `backend/app/agent/llm.py`, using the `google-genai` SDK. When the key is absent it falls back to deterministic mock data (per the assignment's own note that this is acceptable), while prompt construction, JSON parsing/validation, and error handling remain the same.

## Configuring API keys

1. `cd backend && cp .env.example .env`
2. Fill in whichever keys you have — you can set just one provider and leave the other in mock mode, they're independent:
  - **`GEMINI_API_KEY`** — from [Google AI Studio](https://aistudio.google.com/apikey) (free tier available). It enables both Gemini generation and native Google Search grounding.
3. Restart the backend. `GET /api/health` reports `llm_mock_mode` / `search_mock_mode` so you can confirm which providers are live.

**Never commit `.env`** — it's already gitignored. `.env.example` is the template that ships in the repo.

## How it works

`POST /api/research` kicks off the agent and streams progress back over **Server-Sent Events** as each of the 5 sections is researched, in order:

1. **Company Overview** — industry, products, positioning
2. **Key People** — executives as `{name, title}` pairs
3. **Recent News** — 3-4 dated bullet points
4. **Financial Highlights** — revenue / employees / market cap / YoY growth (`null` when unknown — never fabricated)
5. **Risk Factors** — 2-3 concrete risks

For each section the agent builds a targeted research query → calls Gemini with native Google Search grounding and a forced JSON shape matching that section's schema → validates the response → emits it. If a grounded Gemini call fails, that section is marked `error` and the pipeline **keeps going** — one bad section never sinks the whole report. If a section legitimately has no data (e.g. no market cap for a private company), it's marked `unavailable` and rendered as "No public data found," never guessed.

On completion the full report is saved to SQLite and the frontend gets a `complete` event with the new report's id.

### SSE event shape

```
event: started         { company_name, mock_mode: { llm, search } }
event: section_status  { section, status: "searching" | "synthesizing" }
event: section_result   { section, status: "complete" | "unavailable" | "error", data, error }
event: sections_done   { results: { <all 5 sections> } }
event: complete         { report_id, company_name, created_at }
event: error            { message }   // only on a fatal, pipeline-wide failure
```

The frontend consumes this via `fetch` + a hand-rolled SSE parser (`frontend/src/api.ts`) rather than the browser's `EventSource`, because `EventSource` only supports GET and this endpoint needs a POST body.

### REST endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/research` | Start research, stream results via SSE, auto-save on completion |
| GET | `/api/reports` | List saved reports, newest first |
| GET | `/api/reports/{id}` | Full report detail |
| DELETE | `/api/reports/{id}` | Delete a report |
| GET | `/api/health` | Health check + current mock-mode status |

## UI states

Empty (no reports yet) · Streaming (live per-section progress with a pulsing "Live" indicator on the active section) · Complete · Error (plain-English message, never a stack trace) · Invalid input (rejected before a search/LLM round-trip is even attempted).

Nice-to-haves implemented: cancel in-progress research, a visual per-section streaming indicator, `Cmd/Ctrl+K` to focus search, a responsive layout, relative timestamps ("3m ago"), and a same-company duplicate-request guard (backend returns `409` if you're already mid-research for that exact company; the frontend also disables re-submission client-side).

## Testing

```bash
cd backend
source .venv/bin/activate
pytest       # 24 tests: reports CRUD, SSE stream shape, agent unit tests, validators, partial-failure handling
```

All tests run in mock mode with no network access, and no I/O beyond an in-memory SQLite database — no API keys required to run the suite. External calls are never made in tests: either mock mode is active (default), or `GoogleSearchClient.search` is monkeypatched to simulate a provider outage.

Frontend: `cd frontend && npm run build` type-checks (`tsc -b`) and bundles; `npm run lint` runs `oxlint`.

## Do's and Don'ts

**Do:**
- Run it with zero setup first (mock mode) before wiring up real keys — confirms the app itself works before you debug API quota/billing issues.
- Keep `GEMINI_API_KEY` / `GOOGLE_SEARCH_API_KEY` / `GOOGLE_SEARCH_CX` in `backend/.env` only.
- Treat a `null` financial field as "genuinely unknown," not a bug — see [Trade-offs](#trade-offs--limitations) on why we never fabricate numbers.
- Expect the two dev servers (`:5173` frontend, `:8000` backend) to run side-by-side; Vite proxies `/api/*` to the backend, so you never have to think about CORS or base URLs.

**Don't:**
- Don't commit `.env`, `node_modules/`, `__pycache__/`, `.venv/`, or `backend/data/*.db` — all gitignored already.
- Don't expect this to catch every piece of "gibberish" input — see [Trade-offs](#trade-offs--limitations).
- Don't add auth, PDF export, dark mode, pagination, WebSockets, Docker, CI/CD, or heavy logging/monitoring — explicitly out of scope per the brief, and intentionally left out here.
- Don't reach for Postgres/Redis/an external DB — SQLite is a hard requirement and is more than enough at this scale.
- Don't spend more than the brief's time box chasing polish beyond what's listed above as implemented.

## Trade-offs & limitations

- **"Gibberish" detection is heuristic, not semantic.** `is_researchable_company_name` (`backend/app/validators.py`) rejects blank input, input with no letters, and input that's mostly punctuation — catching `"????"` or `"12345"` before wasting a search+LLM round trip. It will *not* catch a string like `"asdkjhaskjdh"` that happens to look word-shaped; that case is instead handled gracefully downstream as an `unavailable`/near-empty report, since truly distinguishing "not a real company" from "a real company with no web presence" reliably needs another model call, which felt like overkill for this brief.
- **Cancel is client-side only.** Clicking "Cancel" aborts the browser's fetch immediately (and the UI resets right away), but the FastAPI generator on the server keeps running until its next `await` point notices the client disconnected, at which point it stops before persisting — so a cancelled search is not saved, but it may burn one more already-in-flight search/LLM call server-side before that happens. True mid-request cancellation would need a task-based (not generator-based) execution model.
- **Duplicate-request guard is in-memory and per-process.** `app.state.in_flight` is a plain set, which is correct for a single `uvicorn` process (the only deployment target here) but wouldn't coordinate across multiple worker processes. Fine at this scale; would move to a shared store (e.g. Redis) if this ever ran with `--workers > 1`.
- **Mock-mode "financials" are all-null by design**, not just "whatever the mock generator felt like." This was a deliberate choice: it demonstrates the missing-data UI state (a real company can genuinely have no market cap) without needing a live search hit, and it keeps the mock path honest about not fabricating numbers, matching the same rule the live path follows.
- **SQLite datetime handling**: SQLite has no native timezone-aware column type, so `created_at` round-trips as a naive UTC string. The frontend explicitly treats any timestamp without an offset as UTC (`frontend/src/utils/time.ts`) rather than letting the browser guess the local timezone.
- **No retry/backoff on the live search or LLM call.** A single transient failure marks that section `error` rather than retrying. Reasonable for a 5-section report where one missing section doesn't ruin the briefing, but a production version would want at least one retry with backoff on 5xx/429s.

## What I'd do with more time

- Add a lightweight per-report "confidence"/"sourced from N results" indicator so a rep can tell a thin-data report from a well-sourced one at a glance.
- Retry logic (with backoff) around the live search and Gemini calls, distinguishing retryable (rate limit, timeout) from terminal (bad request, auth) failures.
- Real backend-side cancellation via an `asyncio.Task` per research run (instead of a bare async generator) so "Cancel" can actually interrupt an in-flight provider call, not just the client's read of the stream.
- Parallelize the 5 sections' search+LLM calls (they're currently sequential) — they're independent of each other, so this would meaningfully cut wall-clock time in live mode.
- A small eval set of ~10 real companies with hand-checked expected sections, to catch prompt regressions.

## Project structure

```
backend/
  app/
    agent/          # search client, LLM client, prompts, section schemas, orchestrator
    routers/         # research (SSE), reports (CRUD), health
    main.py, config.py, database.py, models.py, schemas.py, validators.py, sse.py
  tests/             # pytest — reports API, SSE stream, agent unit tests, validators
  requirements.txt, .env.example, pytest.ini

frontend/
  src/
    api.ts           # REST + SSE client
    hooks/useResearchStream.ts
    components/      # SearchBar, ReportView, ReportHistorySidebar, EmptyState, ErrorBanner
    types.ts, utils/time.ts
```
#   c o m p a n y _ r e s e a r c h _ a i  
 