"""
Structured JSON logging configuration for Podman MCP.

This module provides a centralized logging configuration with the following features:
- Structured JSON logging for better parsing and analysis
- Environment-based configuration (dev/staging/prod)
- Correlation IDs for request tracing
- Performance metrics logging
- Multiple log handlers (file, console, syslog)
- Log rotation and retention policies
- Async logging support
- Loguru integration
- Context-aware logging
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import socket
import sys
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import (
    Any,
    TypeVar,
)

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])
P = TypeVar("P")
T = TypeVar("T")

# Third-party imports
LOGURU_AVAILABLE = False
loguru_logger = None
LOGURU_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"

# Only try to import loguru if it's actually needed
if os.environ.get("ENABLE_LOGURU", "false").lower() == "true":
    try:
        from loguru import logger as loguru_logger
        from loguru._defaults import LOGURU_FORMAT as _LOGURU_FORMAT

        LOGURU_AVAILABLE = True
        LOGURU_FORMAT = _LOGURU_FORMAT
    except ImportError:
        pass

# Local imports
from .loki_handler import add_loki_handler  # noqa: E402

# Configure the log directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "podmanmcp.log"

# Default log level based on environment - set to WARNING to reduce noise
DEFAULT_LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING").upper()
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
HOSTNAME = os.environ.get("HOSTNAME", socket.gethostname())

# Silence noisy loggers
for logger_name in ["fastmcp", "urllib3", "podman", "asyncio"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)


# Thread-local storage for request context
class LogContext(threading.local):
    """Thread-local storage for log context."""

    def __init__(self):
        super().__init__()
        self.correlation_id: str | None = None
        self.request_id: str | None = None
        self.user_id: str | None = None
        self.metrics: dict[str, list[dict[str, Any]]] = {}
        self.labels: dict[str, str] = {
            "job": "podmanmcp",
            "app": "podmanmcp",
            "environment": ENVIRONMENT,
            "host": HOSTNAME,
        }
        self.tags: dict[str, str] = {}
        self.extra: dict[str, Any] = {}
        self.loki_handler_id: int | None = None


# Global log context
log_context = LogContext()


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def __init__(self, *args, **kwargs):
        self.disable_json = kwargs.pop("disable_json", False)
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        if self.disable_json or getattr(record, "disable_json", False):
            # For RPC logs, still use JSON but with a simpler structure
            log_record = {
                "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat() + "Z",
                "level": record.levelname.lower(),
                "message": record.getMessage(),
                "name": record.name,
            }

        # Create a dict with the log record data
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat() + "Z",
            "level": record.levelname.lower(),
            "name": record.name,
            "message": record.getMessage(),
            "pid": record.process,
            "thread": record.thread,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "environment": ENVIRONMENT,
            "hostname": HOSTNAME,
        }

        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id
        elif log_context.correlation_id:
            log_record["correlation_id"] = log_context.correlation_id

        # Add request ID if available
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        elif log_context.request_id:
            log_record["request_id"] = log_context.request_id

        # Add user ID if available
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id
        elif log_context.user_id:
            log_record["user_id"] = log_context.user_id

        # Add labels and tags
        log_record["labels"] = log_context.labels
        log_record["tags"] = log_context.tags

        # Add any extra context
        log_record.update(log_context.extra)

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in (
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "id",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            ) and not key.startswith("_"):
                try:
                    # Ensure value is JSON serializable
                    json.dumps(value)
                    log_record[key] = value
                except (TypeError, OverflowError):
                    log_record[key] = str(value)

        # Ensure the final output is valid JSON
        try:
            return json.dumps(log_record, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            # Fallback to a minimal valid JSON if serialization fails
            return json.dumps(
                {
                    "timestamp": datetime.now(UTC).isoformat() + "Z",
                    "level": "error",
                    "name": "logging",
                    "message": f"Failed to serialize log record: {e!s}",
                    "original_message": str(record.msg),
                },
                default=str,
            )


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter that adds context to log records."""

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Add context to the log record."""
        extra = kwargs.get("extra", {})

        # Add context from thread-local storage
        if log_context.correlation_id and "correlation_id" not in extra:
            extra["correlation_id"] = log_context.correlation_id
        if log_context.request_id and "request_id" not in extra:
            extra["request_id"] = log_context.request_id
        if log_context.user_id and "user_id" not in extra:
            extra["user_id"] = log_context.user_id

        # Add labels and tags
        extra["labels"] = {**log_context.labels, **extra.get("labels", {})}
        extra["tags"] = {**log_context.tags, **extra.get("tags", {})}

        # Add any extra context
        extra.update(log_context.extra)

        kwargs["extra"] = extra
        return msg, kwargs

    def bind(self, **kwargs: Any) -> ContextLogger:
        """Bind context variables to this logger."""
        extra = self.extra or {}
        extra.update(kwargs)
        return ContextLogger(self.logger, extra)

    def contextualize(self, **kwargs: Any) -> LogContextManager:
        """Create a context manager that binds context variables."""
        return LogContextManager(self, **kwargs)

    def patch_loguru(self) -> None:
        """Patch Loguru logger with context from this logger."""
        if not LOGURU_AVAILABLE:
            return

        def patcher(record: dict[str, Any]) -> None:
            """Patch Loguru record with context."""
            if log_context.correlation_id:
                record["extra"]["correlation_id"] = log_context.correlation_id
            if log_context.request_id:
                record["extra"]["request_id"] = log_context.request_id
            if log_context.user_id:
                record["extra"]["user_id"] = log_context.user_id

            # Add labels and tags
            record["extra"]["labels"] = {**log_context.labels, **record["extra"].get("labels", {})}
            record["extra"]["tags"] = {**log_context.tags, **record["extra"].get("tags", {})}

            # Add any extra context
            for key, value in log_context.extra.items():
                if key not in record["extra"]:
                    record["extra"][key] = value

        # Apply the patcher to Loguru
        loguru_logger.configure(patcher=patcher)


class LogContextManager:
    """Context manager for log context."""

    def __init__(self, logger: ContextLogger, **kwargs: Any):
        """Initialize the context manager."""
        self.logger = logger
        self.new_context = kwargs
        self.old_context: dict[str, Any] = {}

    def __enter__(self) -> LogContextManager:
        """Enter the context."""
        # Save old context
        for key in self.new_context.keys():
            if hasattr(log_context, key):
                self.old_context[key] = getattr(log_context, key)

            # Set new context
            setattr(log_context, key, self.new_context[key])

        # Patch Loguru if available
        if LOGURU_AVAILABLE and hasattr(self.logger, "patch_loguru"):
            self.logger.patch_loguru()

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context."""
        # Restore old context
        for key, value in self.old_context.items():
            setattr(log_context, key, value)

        # Clear any new context that wasn't in the old context
        for key in set(self.new_context.keys()) - set(self.old_context.keys()):
            if hasattr(log_context, key):
                setattr(log_context, key, None)

        # Re-patch Loguru if available
        if LOGURU_AVAILABLE and hasattr(self.logger, "patch_loguru"):
            self.logger.patch_loguru()


def configure_logging(
    level: str | int = DEFAULT_LOG_LEVEL,
    log_file: str | Path | None = None,
    enable_console: bool = True,
    enable_syslog: bool = False,
    enable_loki: bool | None = None,
    loki_url: str | None = None,
    loki_tags: dict[str, str] | None = None,
    loki_labels: dict[str, str] | None = None,
    json_format: bool = True,
    disable_json_for_rpc: bool = True,  # New parameter to control RPC logging format
) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file (default: logs/podmanmcp.log)
        enable_console: Whether to enable console logging
        enable_syslog: Whether to enable syslog logging
        enable_loki: Whether to enable Loki logging (default: True if LOKI_URL is set)
        loki_url: URL of the Loki instance (default: from LOKI_URL env var)
        loki_tags: Additional tags to include with Loki logs
        loki_labels: Additional labels to identify the log stream
        json_format: Whether to use JSON format for logs
        disable_json_for_rpc: Whether to disable JSON formatting for RPC logs

    Returns:
        The root logger
    """
    # Convert string log level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # Get the root logger
    root_logger = logging.getLogger()

    # Set the root logger level
    root_logger.setLevel(level)

    # Clear existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        try:
            handler.close()
            root_logger.removeHandler(handler)
        except Exception as e:
            logger.error(f"Error removing handler: {e}")

    # Ensure basic config is called with force=True to clear any existing config
    logging.basicConfig(level=level, force=True, handlers=[])

    # Configure formatters
    if json_format:
        formatter = JsonFormatter(disable_json=disable_json_for_rpc)
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Add console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Add syslog handler if enabled
    if enable_syslog and hasattr(logging.handlers, "SysLogHandler"):
        try:
            syslog_handler = logging.handlers.SysLogHandler(address=("localhost", 514))
            syslog_handler.setLevel(level)
            syslog_handler.setFormatter(formatter)
            root_logger.addHandler(syslog_handler)
        except Exception as e:
            root_logger.warning(f"Failed to configure syslog: {e}")

    # Configure log levels for third-party libraries
    logging.getLogger("podman").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiopodman").setLevel(logging.WARNING)

    # Configure Loguru if available
    if LOGURU_AVAILABLE:
        _configure_loguru(level, log_file, enable_console, enable_syslog)

        # Configure Loki if enabled
        if enable_loki or (enable_loki is None and "LOKI_URL" in os.environ):
            _configure_loki(level=level, url=loki_url, tags=loki_tags, labels=loki_labels)

    return root_logger


def _configure_loguru(
    level: str | int,
    log_file: str | Path | None = None,
    enable_console: bool = True,
    enable_syslog: bool = False,
) -> None:
    """Configure Loguru logger."""
    # Remove default handler
    loguru_logger.remove()

    # Get log level as string
    if isinstance(level, int):
        level_name = logging.getLevelName(level).upper()
    else:
        level_name = level.upper()

    # Configure console handler
    if enable_console:
        loguru_logger.add(
            sys.stderr,
            level=level_name,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    # Configure file handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        loguru_logger.add(
            str(log_file.with_suffix(".log")),  # Ensure .log extension
            level=level_name,
            format=("{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"),
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )

    # Configure syslog handler if enabled
    if enable_syslog:
        try:
            from systemd import journal

            loguru_logger.add(
                journal.JournalHandler(),
                level=level_name,
                format="{message}",
                serialize=True,
                enqueue=True,
            )
        except ImportError:
            loguru_logger.warning("systemd-python not installed, syslog logging disabled")


def _configure_loki(
    level: str | int = "INFO",
    url: str | None = None,
    tags: dict[str, str] | None = None,
    labels: dict[str, str] | None = None,
) -> None:
    """
    Configure Loki logging handler.

    Args:
        level: Log level as string or int
        url: Loki server URL
        tags: Optional tags for Loki logs
        labels: Optional labels for Loki stream
    """
    if not LOGURU_AVAILABLE:
        return

    # Use environment variables if not provided
    if url is None:
        url = os.environ.get("LOKI_URL")
        if not url:
            loguru_logger.warning("Loki URL not provided and LOKI_URL environment variable not set")
            return

    # Get log level as string
    if isinstance(level, int):
        level_name = logging.getLevelName(level).upper()
    else:
        level_name = level.upper()

    # Configure labels
    if labels is None:
        labels = {}

    # Add default labels if not overridden
    default_labels = {
        "job": "podmanmcp",
        "app": "podmanmcp",
        "environment": ENVIRONMENT,
        "host": HOSTNAME,
    }

    for key, value in default_labels.items():
        if key not in labels:
            labels[key] = value

    # Add Loki handler
    try:
        # Remove existing Loki handler if any
        if hasattr(log_context, "loki_handler_id") and log_context.loki_handler_id is not None:
            try:
                loguru_logger.remove(log_context.loki_handler_id)
            except ValueError:
                pass

        # Add new Loki handler
        handler_id = add_loki_handler(
            logger_instance=loguru_logger,
            url=url,
            tags=tags,
            labels=labels,
            level=level_name,
        )

        # Save handler ID for later removal
        log_context.loki_handler_id = handler_id
        loguru_logger.info(f"Loki logging configured with URL: {url}")

    except Exception as e:
        loguru_logger.error(f"Failed to configure Loki logging: {e}")


# Create a default logger instance
logger = ContextLogger(logging.getLogger(__name__), {})

# Configure default logging if not already configured
root_logger = logging.getLogger()
if not root_logger.handlers:
    # Remove any existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure with JSON format and proper stream handling
    configure_logging(enable_console=True, json_format=True, log_file=str(LOG_FILE))


# Add a filter to add correlation ID to log records
class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the log record."""
        if not hasattr(record, "correlation_id") and log_context.correlation_id:
            record.correlation_id = log_context.correlation_id
        return True


# Add the filter to the root logger
for handler in logging.root.handlers:
    handler.addFilter(CorrelationIdFilter())


# Define BoundLogger and BoundLoggerAdapter classes
class BoundLoggerAdapter(logging.LoggerAdapter):
    """Adapter that adds context to log records."""

    def __init__(self, logger: logging.Logger, extra: dict[str, Any]):
        super().__init__(logger, extra)

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Process the logging message and keyword arguments."""
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"].update(self.extra)
        return msg, kwargs


class BoundLogger(logging.Logger):
    """Logger class that supports context binding."""

    def bind(self, **kwargs: Any) -> BoundLogger:
        """Bind context variables to this logger."""
        return BoundLoggerAdapter(self, kwargs)

    def contextualize(self, **kwargs: Any) -> LogContextManager:
        """Create a context manager that binds context variables."""
        return LogContextManager(ContextLogger(self, {}), **kwargs)


# Patch the logger class
logging.setLoggerClass(BoundLogger)

# Export loguru logger if available
if LOGURU_AVAILABLE:
    logger.patch_loguru()
    logger = loguru_logger  # type: ignore
