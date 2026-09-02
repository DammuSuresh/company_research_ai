"""Compatibility search interface.

Live research is performed by Gemini's native Google Search grounding in
``GeminiClient.generate_report``. This class remains for the mock/demo
search-result contract and for callers that still import the old interface.
"""
import logging

from app.config import Settings

logger = logging.getLogger(__name__)

class SearchError(Exception):
    """Raised when the live search provider fails."""


class GoogleSearchClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self.mock_mode = settings.search_mock_mode

    async def search(self, query: str, num_results: int = 4) -> list[dict]:
        """Return a list of {title, snippet, link} dicts for the query."""
        return self._mock_search(query, num_results)

    @staticmethod
    def _mock_search(query: str, num_results: int) -> list[dict]:
        """Deterministic, plausible-looking mock results for offline/demo use."""
        base = [
            {
                "title": f"{query} - Company Profile",
                "snippet": (
                    f"Overview of results related to '{query}'. This is simulated search data "
                    "returned because GEMINI_API_KEY is not configured. Configure a Gemini "
                    "credential to fetch live grounded research."
                ),
                "link": "https://example.com/mock-source-1",
            },
            {
                "title": f"{query} - Recent Coverage",
                "snippet": (
                    "Simulated snippet standing in for a live news/search result. In live mode this "
                    "would contain a real excerpt sourced through Gemini Google Search grounding."
                ),
                "link": "https://example.com/mock-source-2",
            },
            {
                "title": f"{query} - Industry Analysis",
                "snippet": (
                    "Simulated snippet. The agent's prompt construction and JSON parsing pipeline "
                    "is identical whether this data comes from mock or live search."
                ),
                "link": "https://example.com/mock-source-3",
            },
        ]
        return base[:num_results]
