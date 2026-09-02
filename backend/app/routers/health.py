from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "llm_mock_mode": settings.llm_mock_mode,
        "search_mock_mode": settings.search_mock_mode,
    }
