from __future__ import annotations

import html
from typing import Any


def safe_str(value: Any) -> str:
    return "" if value is None else html.escape(str(value))


def initials(name: str) -> str:
    parts = [p for p in str(name).split() if p.strip()]
    return "".join(p[0].upper() for p in parts[:2]) or "U"
