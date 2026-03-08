"""
Structured logging utility using structlog.
"""

import logging
import sys

import structlog
from app.config import get_settings


def setup_logging():
    """Configure structured logging based on config."""
    settings = get_settings()
    log_level = getattr(logging, settings.logging_config.get("level", "INFO").upper())
    log_format = settings.logging_config.get("format", "json")

    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a bound logger instance."""
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(module=name)
    return logger
