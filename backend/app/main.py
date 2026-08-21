"""FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

The application uses async SQLAlchemy with asyncpg and JWT-based
ID/PW authentication (passlib + python-jose).
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine

# ---------------------------------------------------------------------------
# Lifespan — runs once at startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    # Startup: verify DB connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        import logging

        logging.getLogger("uvicorn.error").warning(
            "Database connectivity check failed at startup: %s", exc
        )

    # Startup: launch serialized git commit queue worker
    from app.services.git_queue import start_git_queue_worker
    start_git_queue_worker(app)

    yield
    # Shutdown: dispose connection pool
    await engine.dispose()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="JoyCity Ontology Builder API",
    description=(
        "워크플로우 맵 — backend REST API for managing ontology objects, "
        "links, actions, and rules with an approval workflow."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request timing middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):  # type: ignore[no-untyped-def]
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}"
    return response


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging

    logging.getLogger("uvicorn.error").exception(
        "Unhandled exception for %s %s", request.method, request.url
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Health"],
    summary="Liveness / readiness probe",
    response_description="Service health status",
)
async def health_check() -> dict:
    """Returns HTTP 200 with service metadata when the app is running."""
    return {
        "status": "ok",
        "app": "joycity-ontology-builder",
        "version": app.version,
        "env": settings.APP_ENV,
    }


# ---------------------------------------------------------------------------
# Routers — import here after models are ready to avoid circular imports
# ---------------------------------------------------------------------------
from app.routers import objects, links, actions, rules, graph, extraction_jobs  # noqa: E402
from app.routers import auth as auth_router  # noqa: E402
from app.routers import review as review_router  # noqa: E402

API_PREFIX = "/api/v1"

app.include_router(auth_router.router, prefix=API_PREFIX)
app.include_router(objects.router, prefix=API_PREFIX)
app.include_router(links.router, prefix=API_PREFIX)
app.include_router(actions.router, prefix=API_PREFIX)
app.include_router(rules.router, prefix=API_PREFIX)
app.include_router(graph.router, prefix=API_PREFIX)
app.include_router(extraction_jobs.router, prefix=API_PREFIX)
app.include_router(review_router.router, prefix=API_PREFIX)
