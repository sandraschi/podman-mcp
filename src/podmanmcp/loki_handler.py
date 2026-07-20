"""
Loki handler for Loguru to ship logs to a Loki instance.
"""

import json
import logging
import os
import time
from typing import Any

import requests

# Make loguru optional
LOGURU_AVAILABLE = False
try:
    from loguru import logger

    LOGURU_AVAILABLE = True
except ImportError:
    # Create a dummy logger if loguru is not available
    class DummyLogger:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    logger = DummyLogger()

# Only enable Loki if explicitly requested
ENABLE_LOKI = os.environ.get("ENABLE_LOKI", "false").lower() == "true" and LOGURU_AVAILABLE


class LokiHandler:
    """A handler for Loguru that sends logs to a Loki instance."""

    def __init__(
        self,
        url: str = "http://localhost:3100/loki/api/v1/push",
        tags: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
        batch_size: int = 10,
        batch_timeout: float = 5.0,
    ):
        """Initialize the Loki handler.

        Args:
            url: The Loki API endpoint URL
            tags: Additional tags to include with every log entry
            labels: Labels to identify the log stream
            batch_size: Number of log entries to batch before sending
            batch_timeout: Maximum time in seconds to wait before sending a batch
        """
        self.url = url
        self.tags = tags or {}
        self.labels = labels or {"job": "podmanmcp", "app": "podmanmcp", "environment": "development"}
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._buffer: list[dict[str, Any]] = []
        self._last_send = 0.0

        # Configure default labels from environment
        self._configure_from_environment()

    def _configure_from_environment(self) -> None:
        """Configure handler from environment variables."""
        import os

        # Update from environment variables if available
        if "LOKI_URL" in os.environ:
            self.url = os.environ["LOKI_URL"]

        # Update labels from environment
        env_mapping = {
            "ENVIRONMENT": "environment",
            "HOSTNAME": "host",
            "POD_NAME": "pod",
            "CONTAINER_NAME": "container",
        }

        for env_var, label in env_mapping.items():
            if env_var in os.environ and label not in self.labels:
                self.labels[label] = os.environ[env_var]

    def _format_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Format a log record for Loki."""
        # Extract message and level
        message = record.get("message", "")
        level = record.get("level", {}).get("name", "info").lower()

        # Extract timestamp (nanoseconds)
        timestamp_ns = int(record.get("time", {}).get("timestamp", time.time() * 1e9))

        # Prepare labels (Loki requires string values)
        labels = {"level": level, **self.labels, **self.tags}

        # Add any extra fields as labels (with string conversion)
        extra = record.get("extra", {})
        for key, value in extra.items():
            if key not in labels and not key.startswith("_"):
                labels[key] = str(value)

        # Prepare log entry
        log_entry = {"stream": labels, "values": [[str(timestamp_ns), message]]}

        return log_entry

    def _send_batch(self, force: bool = False) -> None:
        """Send the current batch of logs to Loki."""
        now = time.time()

        # Check if we should send the batch
        if not force and len(self._buffer) < self.batch_size and (now - self._last_send) < self.batch_timeout:
            return

        if not self._buffer:
            return

        try:
            # Prepare the payload for Loki
            payload = {"streams": self._buffer}

            # Send to Loki
            response = requests.post(self.url, json=payload, headers={"Content-Type": "application/json"}, timeout=10.0)

            # Check for errors
            response.raise_for_status()

            # Clear the buffer on success
            self._buffer = []
            self._last_send = now

        except Exception as e:
            # Log the error but don't raise to avoid crashing the application
            logging.error(f"Failed to send logs to Loki: {e!s}")

    def __call__(self, message: str) -> None:
        """Handle a log message."""
        try:
            # Parse the JSON message from Loguru
            record = json.loads(message.record)

            # Format the record for Loki
            log_entry = self._format_record(record)

            # Add to buffer
            self._buffer.append(log_entry)

            # Try to send the batch
            self._send_batch(force=False)

        except Exception as e:
            logging.error(f"Error in Loki handler: {e!s}")

    def flush(self) -> None:
        """Flush any buffered logs."""
        self._send_batch(force=True)

    def stop(self) -> None:
        """Stop the handler and flush any remaining logs."""
        self.flush()


def add_loki_handler(
    logger_instance=logger,
    url: str | None = None,
    tags: dict[str, str] | None = None,
    labels: dict[str, str] | None = None,
    level: str = "INFO",
):
    """Add a Loki handler to a Loguru logger.

    Args:
        logger_instance: The logger instance to add the handler to
        url: The Loki API endpoint URL
        tags: Additional tags to include with every log entry
        labels: Labels to identify the log stream
        level: The minimum log level to send to Loki

    Returns:
        The handler ID that can be used to remove the handler later or None if not available
    """
    if not ENABLE_LOKI or not LOGURU_AVAILABLE:
        logger.warning("Loki logging is not enabled or loguru is not available.")
        return None

    try:
        handler = LokiHandler(url=url, tags=tags, labels=labels)

        # Add the handler to the logger
        handler_id = logger_instance.add(
            handler, level=level.upper(), format="{message}", filter=lambda record: "loki" in record["extra"]
        )

        logger.info(f"Loki logging enabled. Sending logs to {url}")
        return handler_id
    except Exception as e:
        logger.error(f"Failed to initialize Loki handler: {e!s}")
        return None
    return handler_id
