from fastapi import FastAPI

from backend.routes.meetings import router as meetings_router
from backend.routes.rag import router as rag_router
from config.settings import settings
from core.logging import logger


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-powered meeting intelligence backend "
            "for transcription, analysis and meeting management."
        ),
    )

    application.include_router(meetings_router)
    application.include_router(rag_router)

    return application


app = create_application()


@app.get("/")
def health_check() -> dict[str, str]:
    """Return basic API health information."""

    logger.info("Health check endpoint called.")

    return {
        "status": "ok",
        "message": "AI Meeting Intelligence API is running.",
    }