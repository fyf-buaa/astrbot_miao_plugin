from __future__ import annotations

from typing import Any

from ..artifact import Artifact
from ...components.meta import Meta


_WEAPON_CFG: dict[str, dict[str, Any]] = {
    "磐岩结绿": {"attr": "hp", "abbr": "绿剑", "max": 30, "min": 15},
    "猎人之径": {"attr": "mastery"},
    "薙草之稻光": {"attr": "recharge", "abbr": "薙刀"},
    "护摩之杖": {"attr": "hp", "abbr": "护摩", "max": 18, "min": 10},
}


def get_char_artis_cfg(profile: Any) -> dict[str, Any]:
    char = getattr(profile, "char", None)
    if not char:
        return {"title": "通用", "attrWeight": {}}

    game = char.game
    is_gs = char.is_gs
    weapon = getattr(profile, "weapon", {}) or {}
    artis_obj = getattr(profile, "artis", None) or getattr(profile, "_artis", None)

    meta = Meta.get_meta(game, "arti")
    useful_attr = meta.get("usefulAttr", {})

    default_weight = {"atk": 75, "cpct": 100, "cdmg": 100, "dmg": 100, "phy": 100} if is_gs else {"atk": 75, "cpct": 100, "cdmg": 100, "dmg": 100, "speed": 100}
    weight = dict(useful_attr.get(char.name, default_weight))

    if is_gs and weapon:
        wn = weapon.get("name", "")
        w_cfg = _WEAPON_CFG.get(wn)
        if w_cfg and weight.get("atk", 0) > 0:
            attr_key = w_cfg["attr"]
            max_val = w_cfg.get("max", 20)
            min_val = w_cfg.get("min", 10)
            affix = weapon.get("affix", 1)
            plus = min_val + (max_val - min_val) * (affix - 1) / 4
            current = weight.get(attr_key, 0)
            if current != 100:
                weight[attr_key] = min(round(current + plus), 100)

        if artis_obj:
            from ..artifact import ArtifactSet
            is_insulated = False
            for arti_data in artis_obj._data.values():
                name = arti_data.get("name", "")
                arti = Artifact.get(name, game)
                if arti and arti.set_name and ArtifactSet.get(arti.set_name, game):
                    from ...components.meta import Meta as M
                    set_meta = M.get_data(game, "artiSet", arti.set_name)
                    if set_meta and set_meta.get("name", "") == "绝缘之旗印":
                        is_insulated = True
                        break
            if is_insulated:
                max_w = max(weight.get("atk", 0), weight.get("hp", 0), weight.get("def", 0), weight.get("mastery", 0))
                if weight.get("recharge", 0) < max_w:
                    weight["recharge"] = min(round(weight.get("recharge", 0) + max_w * 0.75), int(max_w))

        import re
        xf_pat = re.compile(r"^西风(长枪|大剑|剑|猎弓|秘典)$")
        if xf_pat.match(wn) and weight.get("cpct", 0) < 100:
            weight["cpct"] = 100

    return {"title": f"{char.abbr}-通用", "attrWeight": weight}


def get_cfg(profile: Any) -> dict[str, Any]:
    char = getattr(profile, "char", None)
    if not char:
        return {"attrs": {}, "classTitle": "", "posMaxMark": {}}

    game = char.game
    result = get_char_artis_cfg(profile)
    attr_weight = result.get("attrWeight", {})
    base_attr = getattr(char, "baseAttr", None) or {"hp": 14000, "atk": 230, "def": 700}

    meta = Meta.get_meta(game, "arti")
    attr_map = meta.get("attrMap", {})

    attrs: dict[str, Any] = {}
    for key, attr_cfg in attr_map.items():
        k = attr_cfg.get("base", "")
        weight = attr_weight.get(k or key, 0)
        if not weight:
            continue
        if not k:
            mark = weight / max(attr_cfg.get("value", 1), 1)
            fix_weight = weight
        else:
            plus = 520 if k == "atk" else 0
            base_val = base_attr.get(k, 0) + plus
            mark = weight / max(attr_map[k]["value"], 1) / max(base_val, 1) * 100
            fix_weight = weight * attr_cfg["value"] / max(attr_map[k]["value"], 1) / max(base_val, 1) * 100
        attrs[key] = {**attr_cfg, "weight": weight, "fixWeight": fix_weight, "mark": mark}

    from .artismark import get_max_mark as _gmm
    pos_max_mark = _gmm(attrs, game)
    return {"attrs": attrs, "classTitle": result.get("title", ""), "posMaxMark": pos_max_mark}
