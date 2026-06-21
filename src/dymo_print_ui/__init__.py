"""dymo-print-ui — local web label editor for the Dymo LetraTag 200B."""

from __future__ import annotations

import sys
from pathlib import Path

# The dymo_bluetooth driver ships as a git submodule under external/. Its PEP 621
# packaging can't be consumed as a Poetry path dependency (Poetry 1.7), so we make
# it importable directly. parents[2] is the repo root from src/dymo_print_ui/.
_SUBMODULE = Path(__file__).resolve().parents[2] / "external" / "dymo-bluetooth"
if _SUBMODULE.exists() and str(_SUBMODULE) not in sys.path:
    sys.path.insert(0, str(_SUBMODULE))

__version__ = "0.1.0"

