"""Compatibility entrypoint for runtimes that expect /streamlit_app.py at repo root."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

PROJECT_SUBDIR = Path(__file__).resolve().parent / "LFN9AKGKY13BCGRN"
TARGET_APP = PROJECT_SUBDIR / "streamlit_app.py"

# Ensure legacy absolute imports inside the app (e.g., `from components...`) continue to work.
if str(PROJECT_SUBDIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_SUBDIR))

runpy.run_path(str(TARGET_APP), run_name="__main__")
