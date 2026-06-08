from __future__ import annotations

import math
import sys
from pathlib import Path

APP_ROOT = Path(__file__).parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from services.rbac_service import can_edit_claim


def test_can_edit_claim_handles_nan_assignment_without_crashing():
    assert can_edit_claim("Assigned", math.nan, "APatil")


def test_can_edit_claim_handles_non_string_assignment_values_without_crashing():
    assert not can_edit_claim("On Hold", 12345.0, "12345.0")
