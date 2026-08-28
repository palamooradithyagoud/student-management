import sys
from pathlib import Path

# Ensure both project root and backend directory are in sys.path so both
# `from backend.app...` and `from app...` work seamlessly in any environment.
_CURRENT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _CURRENT_DIR.parent
_ROOT_DIR = _BACKEND_DIR.parent

for _p in [str(_ROOT_DIR), str(_BACKEND_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
