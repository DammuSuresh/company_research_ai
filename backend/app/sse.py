"""Server-Sent Events formatting helper."""
import json
from typing import Any


def format_sse(event: str, data: dict[str, Any]) -> str:
    """Format a single SSE message. Each event carries a JSON-encoded data payload."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
