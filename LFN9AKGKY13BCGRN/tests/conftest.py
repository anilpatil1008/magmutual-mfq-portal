from __future__ import annotations

import sys
import types
from pathlib import Path

APP_ROOT = Path(__file__).parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# Unit tests do not need a live Snowflake dependency, but application modules
# import Snowpark symbols at module import time.
snowflake_module = types.ModuleType("snowflake")
snowpark_module = types.ModuleType("snowflake.snowpark")
snowpark_context_module = types.ModuleType("snowflake.snowpark.context")


def _missing_active_session():
    raise RuntimeError("No active Snowflake session in unit tests")


snowpark_context_module.get_active_session = _missing_active_session
snowpark_module.Session = object
snowpark_module.context = snowpark_context_module
snowflake_module.snowpark = snowpark_module

sys.modules.setdefault("snowflake", snowflake_module)
sys.modules.setdefault("snowflake.snowpark", snowpark_module)
sys.modules.setdefault("snowflake.snowpark.context", snowpark_context_module)
