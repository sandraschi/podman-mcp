"""
Miscellaneous helpers used by podmanmcp.server.

Ported from docker-mcp (dockermcp/tools/assorted_crap.py); podmanmcp.server
imported this module but it was never added, so the console-script entry
crashed with ModuleNotFoundError at import.
"""

import json
import logging
from typing import Any, TextIO

logger = logging.getLogger(__name__)


class SafeJSONEncoder(json.JSONEncoder):
    """A JSON encoder that safely handles non-serializable types."""

    def default(self, o: Any) -> Any:
        """Convert non-serializable objects to a serializable format."""
        try:
            return super().default(o)
        except (TypeError, OverflowError):
            # Convert non-serializable objects to string representation
            return str(o)


def warn_with_log(
    message: str | Warning,
    category: type[Warning] = UserWarning,
    filename: str = "",
    lineno: int = 0,
    file: TextIO | None = None,
    line: str | None = None,
) -> None:
    """
    Log a warning instead of printing it.

    Signature-compatible with warnings.showwarning, so it can replace it.

    Args:
        message: The warning message (str or Warning object)
        category: The warning category (default: UserWarning)
        filename: The filename where the warning occurred (default: "")
        lineno: The line number where the warning occurred (default: 0)
        file: Ignored; present for showwarning compatibility
        line: Ignored; present for showwarning compatibility
    """
    msg_str = str(message)
    if filename and lineno:
        logger.warning(f"{category.__name__}: {msg_str} (at {filename}:{lineno})")
    else:
        logger.warning(f"{category.__name__}: {msg_str}")
