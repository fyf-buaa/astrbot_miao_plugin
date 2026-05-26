from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PLUGIN_DIR = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _PLUGIN_DIR / "_conf_schema.json"
_CFG_SAVE_PATH = _PLUGIN_DIR / "config" / "cfg.json"


class Cfg:
    """Configuration manager for Miao-Plugin on AstrBot.

    Receives config dict from AstrBotConfig via init_config(), then
    provides static accessors (get / set / get_cfg / get_cfg_schema / scale).
    Schema defaults are sourced from ``_conf_schema.json`` (no JS exec).
    """

    _config: dict[str, Any] = {}
    _schema: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Initialisation (called once by the plugin __init__)
    # ------------------------------------------------------------------

    @classmethod
    def init_config(cls, config: dict[str, Any]) -> None:
        """Receive the resolved AstrBot config dict and load the schema."""
        cls._config = config
        cls._load_schema()

    @classmethod
    def _load_schema(cls) -> None:
        try:
            raw: dict[str, Any] = json.loads(
                _SCHEMA_PATH.read_text(encoding="utf-8")
            )
            cls._schema = raw
        except (OSError, json.JSONDecodeError):
            cls._schema = {}

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    @staticmethod
    def get(key: str, default: Any = "") -> Any:
        """Read a config value (falls back to *default* when missing)."""
        return Cfg._config.get(key, default)

    @staticmethod
    def set(key: str, val: Any) -> None:
        """Update a config value in memory **and** persist to JSON."""
        Cfg._config[key] = val
        Cfg._save_cfg()

    @staticmethod
    def get_cfg() -> dict[str, Any]:
        """Return the full config dictionary."""
        return Cfg._config

    @staticmethod
    def get_cfg_schema() -> dict[str, Any]:
        """Return the schema loaded from ``_conf_schema.json``."""
        return Cfg._schema

    @staticmethod
    def scale(pct: float = 1) -> str:
        """Return an inline style string with a clamped scale transform.

        ``renderScale`` (50‑200) from config is applied as an additional
        multiplier on top of *pct*.
        """
        s = Cfg.get("renderScale", 100)
        s = max(50, min(200, int(s))) / 100
        pct = pct * s
        return f'style="transform:scale({pct})"'

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _save_cfg() -> None:
        _CFG_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CFG_SAVE_PATH.write_text(
            json.dumps(Cfg._config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
