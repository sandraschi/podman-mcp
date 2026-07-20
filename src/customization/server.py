"""
ASGI entry point for uvicorn (web_sota backend).
Imports web_app from the main server module.
"""

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent.parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from server import web_app as app  # noqa: E402, F401
