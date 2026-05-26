"""gsCfg adapted: role/weapon name lookups via vendored runtime.

Migrated from ``yunzai-py/plugins/genshin/model/gsCfg.py``.
Uses ``genshin_runtime`` instead of ``app.core.config``.
"""

from __future__ import annotations

from typing import Any

from .genshin_runtime import runtime


class GsCfg:
    """角色/武器配置——对应 JS: model/gsCfg.js"""

    def role_id_to_name(self, role_id: str) -> str:
        """Return the primary display name for a numeric role ID."""
        names = runtime.load_def_set("role", "name")
        entry = names.get(role_id, names.get(int(role_id) if role_id.isdigit() else role_id, []))
        return entry[0] if entry else ""

    def role_name_to_id(self, keyword: str) -> str | None:
        """Look up a role ID by any alias name."""
        names = runtime.load_def_set("role", "name")
        for rid, aliases in names.items():
            for a in aliases:
                if isinstance(a, str) and keyword == a:
                    return str(rid) if isinstance(rid, int) else rid
        return None

    def short_name(self, name: str) -> str:
        """Return shortened weapon/character name if one exists."""
        names = runtime.load_def_set("role", "name")
        for rid, aliases in names.items():
            if name in aliases:
                return aliases[0]
        wother = runtime.load_def_set("weapon", "other")
        sort_name = wother.get("sortName", {})
        if name in sort_name:
            return sort_name[name]
        return name

    def get_role(self, msg: str, filter_msg: str = "") -> dict[str, Any] | None:
        """Parse a role mention from message text.

        Returns a dict with ``roleId``, ``name``, ``alias``, ``uid``
        or ``None`` if no role could be identified.
        """
        for kw in filter_msg.split("|"):
            msg = msg.replace(kw, "").strip()
        alias = msg.replace("#", "").strip()
        role_id = self.role_name_to_id(alias)
        if not role_id:
            return None
        return {
            "roleId": role_id,
            "name": self.role_id_to_name(role_id),
            "alias": alias,
            "uid": "",
        }

    def get_element_map(self) -> dict[str, str]:
        return runtime.load_def_set("element", "role")

    def get_weapon_type_map(self) -> dict[str, str]:
        return runtime.load_def_set("element", "weapon")


gs_cfg = GsCfg()
