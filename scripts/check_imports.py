#!/usr/bin/env python3
"""Check if all required modules can be imported."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podmanmcp.logging_config import configure_logging, logger

configure_logging()

logger.info("Python Path:")
for path in sys.path:
    logger.info(f"  - {path}")
logger.info("Checking imports...")

try:
    import podman
    logger.info("podman OK")
except ImportError as e:
    logger.info(f"podman: {e}")

try:
    import fastmcp
    version = fastmcp.__version__ if hasattr(fastmcp, "__version__") else "unknown"
    logger.info(f"fastmcp ({version})")
except ImportError as e:
    logger.info(f"fastmcp: {e}")

try:
    from podmanmcp import mcp  # noqa: F401
    logger.info("podmanmcp.mcp OK")
except ImportError as e:
    logger.info(f"podmanmcp.mcp: {e}")

try:
    from podmanmcp.tools.images import image_tools  # noqa: F401
    logger.info("podmanmcp.tools.images.image_tools OK")
except ImportError as e:
    logger.info(f"podmanmcp.tools.images.image_tools: {e}")

logger.info(f"CWD: {os.getcwd()}")
src_dir = Path(__file__).parent.parent / "src" / "podmanmcp"
if src_dir.exists():
    for f in src_dir.glob("**/*.py"):
        logger.info(f"  - {f.relative_to(src_dir.parent)}")
