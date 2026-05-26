from __future__ import annotations
from pathlib import Path


def _ensure_dir(path: str) -> str:
    """Ensure the given directory exists and return the path."""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


# Plugin root directory
_miao_path = Path(__file__).resolve().parent.parent
miao_path = str(_miao_path)

# Data directory — resolve from AstrBot's context or fallback to local data/
try:
    from astrbot.api import get_astrbot_data_path
    _data_path = str(get_astrbot_data_path())
except (ImportError, RuntimeError):
    _data_path = str(_miao_path / "data")

data_path = _ensure_dir(_data_path)

# Deprecated: old yunzai root (kept for compatibility)
_yunzai_path = str(_miao_path.parent.parent)


def get_root(root: str = "") -> str:
    """Resolve a named root directory.

    Args:
        root: One of "", "miao", or "yunzai".

    Returns:
        The corresponding directory path.
    """
    if not root or root == "miao":
        return data_path
    if root == "yunzai":
        return _yunzai_path
    return data_path


# Alias for compatibility with migrated modules
root_path = data_path

__all__ = [
    "miao_path",
    "data_path",
    "root_path",
    "get_root",
]
