"""SCENTIQ FastAPI Application Factory.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.errors import AppException
from app.core.middleware import (
    RequestIdMiddleware,
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.db.base import Base
from app.db.session import engine
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: setup structured logging
    setup_logging(settings.LOG_LEVEL)
    logger.info(f"Starting {settings.PROJECT_NAME} API [{settings.ENVIRONMENT}]")

    # In local SQLite mode, automatically ensure tables exist for instant developer convenience
    if settings.DATABASE_URL.startswith("sqlite"):
        logger.info("Initializing SQLite database tables...")
        Base.metadata.create_all(bind=engine)

    yield

    # Shutdown
    logger.info(f"Stopping {settings.PROJECT_NAME} API")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Evidence-led fragrance discovery and recommendation platform.",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 1. Request ID Middleware
    app.add_middleware(RequestIdMiddleware)

    # 2. CORS Middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 3. Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # 4. Include API v1 Router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
