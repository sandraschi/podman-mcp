#!/usr/bin/env python3
"""
Test script to verify JSON logging configuration.
"""

import json
import logging
import logging.handlers
import os
import uuid
from datetime import datetime


class LogContext:
    """Simple context manager for logging context."""

    def __init__(self):
        self.correlation_id = None
        self.request_id = None

    def contextualize(self, **kwargs):
        """Set context variables."""
        self.correlation_id = kwargs.get("correlation_id")
        self.request_id = kwargs.get("request_id")
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.correlation_id = None
        self.request_id = None


# Create a simple log context
log_context = LogContext()


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, *args, **kwargs):
        self.disable_json = kwargs.pop("disable_json", False)
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        # Create a dict with the log record data
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname.lower(),
            "name": record.name,
            "message": record.getMessage(),
            "pid": record.process,
            "thread": record.thread,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "environment": "test",
            "hostname": "test-host",
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
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": "error",
                    "name": "logging",
                    "message": f"Failed to serialize log record: {e!s}",
                    "original_message": str(record.msg),
                },
                default=str,
            )


def configure_logging(level="INFO", log_file=None, json_format=True, **kwargs):
    """Configure logging with JSON formatting."""
    # Create logs directory if it doesn't exist
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Set up the root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove all existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    if json_format:
        formatter = JsonFormatter(disable_json=kwargs.get("disable_json_for_rpc", False))
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Add console handler
    if kwargs.get("enable_console", True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if log file is specified
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


# Configure logging
configure_logging(level="DEBUG", log_file="logs/test_json.log", json_format=True, disable_json_for_rpc=False)

# Get the logger
logger = logging.getLogger("test_logger")


def test_json_logging():
    """Test JSON logging with different log levels and structured data."""
    # Simple log messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test with extra fields
    logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})

    # Test with context
    with log_context.contextualize(correlation_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()), user_id="test_user"):
        logger.info("Processing request with context")

    # Test exception
    try:
# 1 / 0  # intentional
    except Exception:
        logger.exception("An error occurred")

    # Test complex data
    complex_data = {"nested": {"key": "value"}, "list": [1, 2, 3], "timestamp": datetime.utcnow().isoformat()}
    logger.info("Complex data example", extra={"data": complex_data})

    logger.critical("This is a critical message", extra={"key5": True})


if __name__ == "__main__":
    print("Testing JSON logging... (check stderr for JSON output)")
    test_json_logging()
    print("Test complete. Check the output above for JSON-formatted logs.")
    print("Log file created at: logs/test_json.log")
