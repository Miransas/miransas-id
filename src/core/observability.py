"""Sentry error tracking and structured logging setup."""
import json
import logging
import sys
from datetime import datetime, timezone

from src.core.config import settings

_SENSITIVE_KEYS = frozenset({
    "password", "new_password", "old_password",
    "hashed_password", "secret_key", "access_token",
    "refresh_token", "token", "authorization",
    "cookie", "set-cookie",
})


def scrub_sensitive_data(event: dict, hint: object) -> dict:
    """Remove sensitive fields from Sentry events before transmission."""
    def _scrub(obj: object) -> object:
        if isinstance(obj, dict):
            return {
                k: ("[REDACTED]" if k.lower() in _SENSITIVE_KEYS else _scrub(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_scrub(i) for i in obj]
        return obj

    if "request" in event:
        req = event["request"]
        if "data" in req:
            req["data"] = _scrub(req["data"])
        if "headers" in req:
            req["headers"] = _scrub(req["headers"])

    return event


def setup_sentry() -> None:
    """Initialize Sentry SDK. No-op when SENTRY_DSN is empty."""
    if not settings.SENTRY_DSN:
        return

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        before_send=scrub_sensitive_data,
    )


class _JsonFormatter(logging.Formatter):
    """Structured JSON logs for log aggregators (production)."""

    def format(self, record: logging.LogRecord) -> str:
        _skip = frozenset({
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "message", "pathname", "process", "processName",
            "relativeCreated", "thread", "threadName",
            "exc_info", "exc_text", "stack_info",
        })
        data: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _skip:
                data[key] = value
        return json.dumps(data, default=str)


def setup_logging() -> None:
    """Configure root logger. JSON in production, plain text in development."""
    root = logging.getLogger()
    root.setLevel(logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG)

    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    if settings.ENVIRONMENT == "production":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
