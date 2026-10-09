import logging
import sys

import structlog

from app.core.config import settings

# Third-party loggers that are too chatty at INFO/DEBUG.
_QUIET_LOGGERS = {
    "sqlalchemy.engine": logging.WARNING,
    "asyncio": logging.WARNING,
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
}


def configure_logging() -> None:
    """One logging pipeline for everything.

    structlog calls AND stdlib logs (uvicorn, SQLAlchemy, libraries) all flow through the same
    processors, so every line has the same shape and carries request_id.
    Local: pretty colored console. Staging/production: one JSON object per line on stdout.
    """
    level = logging.getLevelName(settings.log_level.upper())
    if not isinstance(level, int):
        level = logging.INFO

    is_local = settings.environment == "local"

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # request_id, user_id, ...
        structlog.stdlib.add_logger_name,       # type: ignore
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_local:
        final_processors: list[structlog.types.Processor] = [
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(),  # pretty tracebacks
        ]
    else:
        final_processors = [
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)  # stdout: the platform collects it
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,  # applies the same fields to stdlib logs
            processors=final_processors,
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Route uvicorn's own logs through our handler; silence its access log (we log requests).
    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
    logging.getLogger("uvicorn.access").disabled = True

    for name, quiet_level in _QUIET_LOGGERS.items():
        logging.getLogger(name).setLevel(quiet_level)