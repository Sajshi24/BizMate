import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import PyMongoError

from backend.config.database import close_database, get_client, get_database
from backend.routes.analytics import router as analytics_router
from backend.routes.finance import router as finance_router
from backend.routes.inventory import router as inventory_router
from backend.routes.products import router as products_router
from backend.routes.sales import router as sales_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

APP_TITLE = "Local-Logic"
APP_DESCRIPTION = "AI-Powered Smart Business Assistant for Local Retailers"
APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources on startup and release them on shutdown."""
    try:
        get_database()
        logger.info("Application startup complete")
    except PyMongoError as exc:
        logger.warning("Application started without MongoDB: %s", exc)

    yield

    close_database()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(sales_router)
app.include_router(inventory_router)
app.include_router(finance_router)
app.include_router(analytics_router)


def _database_status() -> str:
    try:
        get_client().admin.command("ping")
        return "connected"
    except PyMongoError:
        return "disconnected"


@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    return {
        "name": APP_TITLE,
        "description": APP_DESCRIPTION,
        "version": APP_VERSION,
        "status": "running",
        "message": "Welcome to Local-Logic API",
    }


@app.get("/health", tags=["Health"])
async def health() -> dict[str, Any]:
    database_status = _database_status()
    overall_status = "healthy" if database_status == "connected" else "degraded"

    return {
        "status": overall_status,
        "service": APP_TITLE,
        "version": APP_VERSION,
        "checks": {
            "api": "up",
            "database": database_status,
        },
    }
