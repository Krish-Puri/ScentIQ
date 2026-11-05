"""SCENTIQ Structured Logging configuration.
Provides JSON or formatted console logging with request correlation.
"""
import logging
import sys
from typing import Any, Dict
from contextvars import ContextVar

# Context variable to hold current request ID across async tasks
request_id_ctx: ContextVar[str] = ContextVar("request_id_ctx", default="")


class RequestIdFilter(logging.Filter):
    """Injects current request_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configures application-wide logging."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = (
        "[%(asctime)s] [%(levelname)s] [req:%(request_id)s] [%(name)s]: %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers on re-init
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

    # Set third-party loggers to a reasonable level
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("scentiq")

