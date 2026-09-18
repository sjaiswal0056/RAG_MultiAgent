from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import router
from app.config import settings
from app.logging_config import configure_logging


configure_logging(settings.log_level)
app = FastAPI(title="Policy-Aware Multi-Agent RAG Claim Decision Engine", version=__version__)
app.include_router(router)


@app.exception_handler(Exception)
async def unhandled_exception(_request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": "Internal analysis error", "category": type(exc).__name__})
