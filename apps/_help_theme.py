from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from ..components.data import Data
from ..tools.path import miao_path

_theme_dir = Path(f"{miao_path}/resources/help/theme/")


async def get_theme_cfg(theme: str | list[str], exclude: list[str] | None = None,
                        res_path: str = "") -> dict[str, Any]:
    names: list[str] = []
    if _theme_dir.exists():
        for d in _theme_dir.iterdir():
            if d.is_dir() and (d / "main.png").exists():
                names.append(d.name)

    ret: list[str] = []
    if isinstance(theme, list):
        ret = [n for n in theme if n in names]
    elif theme == "all":
        ret = names
    if exclude:
        ret = [n for n in ret if n not in exclude]
    if not ret:
        ret = ["default"]

    name = random.choice(ret)
    theme_res = f"{res_path}help/theme/"
    bg_path = _theme_dir / name / "bg.jpg"
    bg = f"{theme_res}{name}/bg.jpg" if bg_path.exists() else f"{theme_res}default/bg.jpg"
    style_mod = await Data.import_module(f"resources/help/theme/{name}/config.js", "miao")
    return {
        "main": f"{theme_res}{name}/main.png",
        "bg": bg,
        "style": style_mod.get("style", {}),
    }


async def get_theme_data(diy_style: dict[str, Any], sys_style: dict[str, Any],
                         res_path: str = "") -> dict[str, Any]:
    help_cfg = {**sys_style, **diy_style}
    col_count = max(2, min(5, int(help_cfg.get("colCount", 3))))

    theme = await get_theme_cfg(
        diy_style.get("theme", sys_style.get("theme", "all")),
        diy_style.get("themeExclude", sys_style.get("themeExclude")),
        res_path=res_path,
    )
    ts = theme.get("style", {})

    css_lines: list[str] = [
        f"body{{background-image:url({theme['bg']})}}",
        f".container{{background-image:url({theme['main']})}}",
        f".help-items{{grid-template-columns:repeat({col_count},1fr)}}",
    ]

    def _css(sel: str, prop: str, key: str, default: str | int,
             transform=None) -> None:
        val = ts.get(key) or diy_style.get(key) or sys_style.get(key) or default
        if transform:
            val = transform(val)
        css_lines.append(f"{sel}{{{prop}:{val}}}")

    _css(".help-title,.help-group-name", "color", "fontColor", "#ceb78b")
    _css(".help-title,.help-group-name", "text-shadow", "fontShadow", "none")
    _css(".help-item-desc", "color", "descColor", "#eee")
    _css(".help-item-desc", "text-shadow", "descShadow", "none")
    _css(".help-group-box", "background", "contBgColor", "rgba(43,52,61,0.8)")
    _css(".help-group-box", "backdrop-filter", "contBgBlur", 3,
         lambda n: "none" if diy_style.get("bgBlur") is False else f"blur({n}px)")
    _css(".help-group-header", "background", "headerBgColor", "rgba(34,41,51,.4)")
    _css(".help-group-icon", "background", "fontColor", "#ceb78b")
    _css(".help-item:nth-child(odd)", "background", "rowBgColor1", "rgba(34,41,51,.2)")
    _css(".help-item:nth-child(even)", "background", "rowBgColor2", "rgba(34,41,51,.4)")

    return {"style": f"<style>{''.join(css_lines)}</style>", "colCount": col_count}
