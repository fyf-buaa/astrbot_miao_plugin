"""Config management using AstrBot data paths (migrated from yunzai's runtime.py).

Provides:
- ``GenshinRuntime`` – YAML/JSON config loader with caching
- ``ensure_defaults()`` – creates default config files on first run
- ``gs_cfg`` – role/weapon name lookup singleton
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .tools.path import data_path, miao_path


@dataclass
class GenshinRuntime:
    """Configuration manager for the genshin plugin data files.

    File layout::

        {miao_path}/genshin_data/
            defSet/          # shipped default configs (YAML, read-only)
                role/
                element/
                weapon/
            config/          # user overridable configs (YAML)
                role.name.yaml
                mys.set.yaml
                ...

        {data_path}/genshin/  # runtime data (JSON, auto-generated)
    """

    root: Path = field(default_factory=lambda: Path(miao_path) / "genshin_data")
    _def_set_cache: dict[str, Any] = field(default_factory=dict)
    _config_cache: dict[str, Any] = field(default_factory=dict)

    # ── Directory properties ─────────────────────────────────────────

    @property
    def def_set_dir(self) -> Path:
        return self.root / "defSet"

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def data_dir(self) -> Path:
        return Path(data_path) / "genshin"

    # ── Directory / file helpers ─────────────────────────────────────

    def ensure(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        return self.config_dir / name

    # ── YAML I/O ─────────────────────────────────────────────────────

    def load_yaml(self, name: str, default: Any | None = None) -> Any:
        path = self.path(name)
        if not path.exists():
            return default if default is not None else {}
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if data is not None else (default if default is not None else {})

    def save_yaml(self, name: str, data: Any) -> None:
        self.ensure()
        self.path(name).write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    # ── JSON I/O ─────────────────────────────────────────────────────

    def load_json(self, name: str, default: Any | None = None) -> Any:
        path = self.data_dir / name
        if not path.exists():
            return default if default is not None else {}
        import json

        return json.loads(path.read_text(encoding="utf-8"))

    def save_json(self, name: str, data: Any) -> None:
        self.ensure()
        import json

        (self.data_dir / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Cached defSet / config ───────────────────────────────────────

    def load_def_set(self, app: str, name: str, default: Any | None = None) -> Any:
        """Load shipped default config ``defSet/{app}/{name}.yaml`` with cache."""
        cache_key = f"{app}.{name}"
        if cache_key in self._def_set_cache:
            return self._def_set_cache[cache_key]
        path = self.def_set_dir / app / f"{name}.yaml"
        if not path.exists():
            return default if default is not None else {}
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        result = data if data is not None else (default if default is not None else {})
        self._def_set_cache[cache_key] = result
        return result

    def get_config(self, app: str, name: str, default: Any | None = None) -> Any:
        """Merge defSet default with user config (user values win)."""
        cache_key = f"{app}.{name}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        def_set = self.load_def_set(app, name, default)
        user_config = self.load_yaml(f"{app}.{name}.yaml", default=None)
        if user_config is None:
            return def_set
        if isinstance(def_set, dict) and isinstance(user_config, dict):
            merged = {**def_set, **user_config}
        else:
            merged = user_config
        self._config_cache[cache_key] = merged
        return merged

    def clear_cache(self) -> None:
        self._def_set_cache.clear()
        self._config_cache.clear()


# Module singleton
runtime = GenshinRuntime()


def ensure_defaults() -> None:
    """Create default config YAML files if they do not exist yet."""
    runtime.ensure()
    defaults: dict[str, Any] = {
        "mys.set.yaml": {
            "cookieDoc": "当前 Python 版仅保留基础命令入口，米游社 Cookie/渲染能力待后续补齐。",
            "allowUseCookie": 0,
            "abbrSetAuth": 0,
        },
        "mys.pubCk.yaml": [],
        "role.name.yaml": {},
        "gacha.set.yaml": {
            "count": 1,
            "delMsg": 0,
            "LimitSeparate": 0,
        },
    }
    for name, data in defaults.items():
        path = runtime.path(name)
        if not path.exists():
            runtime.save_yaml(name, data)
