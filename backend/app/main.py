"""FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import health, reports, research

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.in_flight = set()  # company names (lowercased) currently being researched
    settings = get_settings()
    if settings.llm_mock_mode:
        logger.warning("GEMINI_API_KEY not set -- running with MOCK LLM responses.")
    yield


app = FastAPI(title="Company Research Tool API", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router, prefix="/api", tags=["research"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(health.router, prefix="/api", tags=["health"])
