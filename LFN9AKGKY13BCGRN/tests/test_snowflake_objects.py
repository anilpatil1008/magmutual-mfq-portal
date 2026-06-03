from __future__ import annotations

import re
import sys
from pathlib import Path

APP_ROOT = Path(__file__).parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


def _snowflake_object_constants() -> set[str]:
    registry_path = APP_ROOT / "config" / "snowflake_objects.py"
    registry_text = registry_path.read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Z0-9_]+)\s*=", registry_text, re.MULTILINE))


def test_snowflake_object_registry_defines_referenced_obj_constants() -> None:
    app_root = APP_ROOT
    constants = _snowflake_object_constants()
    references: set[str] = set()

    for path in app_root.rglob("*.py"):
        if any(part in {".venv", "__pycache__"} for part in path.parts):
            continue
        references.update(re.findall(r"obj\.([A-Z0-9_]+)", path.read_text(encoding="utf-8")))

    assert references <= constants


def test_claims_list_view_uses_source_vw_mfq_claims() -> None:
    from config import snowflake_objects as obj

    assert obj.VW_MFQ_CLAIMS == "MFQ_DEV_DWH.APP.VW_MFQ_CLAIMS"
    assert obj.MFQ_CLAIMS_LIST_VIEW == obj.VW_MFQ_CLAIMS
    assert obj.MFQ_RECENT_CLAIMS_VIEW == obj.VW_MFQ_CLAIMS


def test_dashboard_summary_view_uses_unqualified_summary_view() -> None:
    from config import snowflake_objects as obj

    assert obj.MFQ_DASHBOARD_SUMMARY_VIEW == "MFQ_DASHBOARD_SUMMARY_VW"
