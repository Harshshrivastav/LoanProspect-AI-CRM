"""
FastAPI Application Entry Point
LoanProspect AI CRM — Multi-Agent Banking Intelligence Platform
Powered by CrewAI + Gemini (via LiteLLM)
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure the project root (backend/) is on sys.path so that
# `from app.xxx import yyy` works regardless of how this file is invoked:
#   python app/main.py  ← adds backend/ automatically
#   python -m app.main  ← already works
#   uvicorn app.main:app ← already works
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.api import (
    agents,
    audit,
    campaigns,
    chat,
    customers,
    messages,
    prospects,
    transactions,
)
from app.config import settings
from app.db.database import init_db
from app.utils.logger import get_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = get_logger(__name__)


# ── Lifespan lifecycle and app definition (Unchanged) ─────────────────────────
# ... (omitted for brevity, let's keep original lines)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle manager."""
    logger.info("🚀 Starting LoanProspect AI CRM...")

    # Ensure the data directory exists for SQLite
    Path("data").mkdir(exist_ok=True)

    # Create all DB tables (no-op if they already exist)
    init_db()
    logger.info("✅ Database initialized")

    # Auto-seed if the database is empty
    try:
        from app.db.database import get_db_context
        from app.db.models import Customer

        with get_db_context() as db:
            count = db.query(Customer).count()

        if count == 0:
            logger.info("📊 No customers found — running seed script...")
            from app.seed.seed_data import run_seed

            run_seed()
            logger.info("✅ Seed complete")
        else:
            logger.info(f"✅ Database has {count} customers — skipping seed")
    except Exception as e:
        logger.warning(f"Seed check failed (non-fatal): {e}")

    yield

    logger.info("👋 Shutting down LoanProspect AI CRM...")


# ── Application factory ───────────────────────────────────────────────────────

app = FastAPI(
    title="LoanProspect AI CRM",
    description=(
        "Multi-Agent Banking Intelligence Platform powered by CrewAI + Gemini. "
        "Identifies personal loan prospects, generates personalized outreach, "
        "and orchestrates agentic conversations for relationship managers."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health check ──────────────────────────────────────────────────────────────


@app.get("/health", tags=["health"])
def health():
    """Lightweight health check — confirms the app is running and config is set."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "llm": f"gemini/{settings.gemini_model}",
        "api_key_set": bool(settings.gemini_api_key),
        "framework": "CrewAI",
    }


# ── API routers ───────────────────────────────────────────────────────────────

app.include_router(customers.router, prefix="/api")
app.include_router(prospects.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(agents.router, prefix="/api")


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
