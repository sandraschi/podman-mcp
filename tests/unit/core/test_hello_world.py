"""
Simple test module to verify test output capture functionality.
"""

import logging
import sys

# Configure basic logging that works with pytest-capture
logger = logging.getLogger(__name__)


def test_hello_world(capsys, caplog):
    """A simple test that outputs to stdout, stderr, and logs."""
    # Set up logging to capture all levels
    caplog.set_level(logging.DEBUG)

    # This will be captured by capsys
    print("Hello, world! This is stdout output.")
    print("This is an error message.", file=sys.stderr)

    # This will be captured by caplog
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Capture the output
    captured = capsys.readouterr()

    # Verify stdout/stderr
    assert "Hello, world!" in captured.out
    assert "This is an error message." in captured.err

    # Verify logs
    log_messages = [record.msg for record in caplog.records]
    assert "This is an info message" in log_messages
    assert "This is a warning message" in log_messages
    assert "This is an error message" in log_messages

    # Verify log levels
    log_levels = [record.levelname for record in caplog.records]
    assert "INFO" in log_levels
    assert "WARNING" in log_levels
    assert "ERROR" in log_levels
