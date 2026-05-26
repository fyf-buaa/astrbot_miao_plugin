from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..components.cfg import Cfg
from ..components.common import render
from ..components.data import Data
from ..tools.path import miao_path
from ..components.version import Version
from ._help_theme import get_theme_data

_help_path = Path(f"{miao_path}/resources/help")


async def render_help(e: Any) -> Any:
    msg = str(getattr(e, "msg", ""))
    if "喵喵" not in msg and not Cfg.get("help", False):
        return False

    custom: dict[str, Any] = {}
    help_mod: dict[str, Any] = {}

    player_path = _help_path / "help-cfg.js"
    if player_path.exists():
        help_mod = await Data.import_module("resources/help/help-cfg.js", "miao")
    else:
        player_path = _help_path / "help-list.js"
        if player_path.exists():
            help_mod = await Data.import_module("resources/help/help-list.js", "miao")

    cfg_result = await Data.import_cfg("help")
    sys_cfg = cfg_result["sysCfg"]
    diy_cfg = cfg_result["diyCfg"]

    if not sys_cfg and not diy_cfg:
        yaml_path = Path(f"{miao_path}/config/help_default.yaml")
        if yaml_path.exists():
            raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                sys_cfg = {"helpCfg": raw.get("helpCfg", {}), "helpList": raw.get("helpList", [])}

    if isinstance(help_mod.get("helpCfg"), list):
        custom = {"helpList": help_mod["helpCfg"], "helpCfg": {}}
    else:
        custom = help_mod

    help_cfg = {**sys_cfg.get("helpCfg", {}), **custom.get("helpCfg", {}), **diy_cfg.get("helpCfg", {})}
    help_list = diy_cfg.get("helpList") or custom.get("helpList") or sys_cfg.get("helpList", [])

    help_group: list[dict] = []
    for group in help_list:
        if group.get("auth") == "master" and not getattr(e, "isMaster", False):
            continue
        for h in group.get("list", []):
            icon = h.get("icon", 0)
            if not icon:
                h["css"] = "display:none"
            else:
                x = (int(icon) - 1) % 10
                y = (int(icon) - x - 1) // 10
                h["css"] = f"background-position:-{x * 50}px -{y * 50}px"
        help_group.append(group)

    res_path = Path(miao_path, "resources").as_uri() + "/"
    theme_data = await get_theme_data(diy_cfg.get("helpCfg", {}), sys_cfg.get("helpCfg", {}),
                                      res_path=res_path)
    return await render("help/index", {
        "helpCfg": help_cfg,
        "helpGroup": help_group,
        "colCount": theme_data["colCount"],
        "style": theme_data["style"],
        "element": "default",
    }, e=e, scale=1.2)


async def version_info(e: Any) -> Any:
    return await render("help/version-info", {
        "currentVersion": Version.get_version(),
        "changelogs": Version.get_changelogs(),
        "elem": "cryo",
    }, e=e, scale=1.2)
