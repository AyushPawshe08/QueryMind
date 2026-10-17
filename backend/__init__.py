"""
QueryMind Backend Package
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure the backend directory is in sys.path
_current_dir = Path(__file__).resolve().parent
load_dotenv(_current_dir / ".env")
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# Also ensure parent directory (QM_V1) is in sys.path
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))
