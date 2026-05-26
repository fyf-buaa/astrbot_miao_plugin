from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...components.format import Format
from ...components.meta import Meta
from ...tools.path import miao_path

# Mihomo affixId (1-indexed) -> meta.json sub key name
_SR_AFFIX_ID_TO_KEY: dict[int, str] = {
    1: "hpPlus", 2: "atkPlus", 3: "defPlus",
    4: "hp", 5: "atk", 6: "def",
    7: "speed", 8: "cpct", 9: "cdmg",
    10: "effPct", 11: "effDef", 12: "stance",
}


_sr_data_cache: tuple | None = None

def _get_sr_data() -> tuple[dict[str, Any], dict[str, Any]]:
    global _sr_data_cache
    if _sr_data_cache is not None:
        return _sr_data_cache
    star_data: dict[str, Any] = {}
    main_idx: dict[str, Any] = {}
    fp = Path(f"{miao_path}/resources/meta-sr/artifact/meta.json")
    if fp.exists():
        meta = json.loads(fp.read_text(encoding="utf-8"))
        star_data = meta.get("starData", {})
        main_idx = meta.get("mainIdx", {})
    _sr_data_cache = (star_data, main_idx)
    return star_data, main_idx


def get_main_attr_sr(slot_type: int, main_affix_id: int, level: int, star: int = 5) -> dict[str, Any] | bool:
    sdata, midx = _get_sr_data()
    slot_key = str(slot_type)
    affix_key = str(main_affix_id)
    slot_map = midx.get(slot_key, {})
    stat_name = slot_map.get(affix_key)
    if not stat_name:
        return False
    rarity = str(star)
    rarity_data = sdata.get(rarity, {})
    main_stats = rarity_data.get("main", {})
    stat_cfg = main_stats.get(stat_name, {})
    base = float(stat_cfg.get("base", 0))
    step = float(stat_cfg.get("step", stat_cfg.get("add", 0)))
    value = base + step * level
    return {"id": main_affix_id, "key": stat_name, "value": value}


def get_sub_attr_sr(affix_ids: list[str], star: int = 5) -> list[dict[str, Any]]:
    sdata, _ = _get_sr_data()
    rarity = str(star)
    rarity_data = sdata.get(rarity, {})
    sub_stats = rarity_data.get("sub", {})
    ret: list[dict[str, Any]] = []
    for aid_str in affix_ids:
        parts = aid_str.split(",")
        aid = parts[0]
        count = int(parts[1]) if len(parts) > 1 else 0
        step_val = int(parts[2]) if len(parts) > 2 else 0
        attr_cfg = sub_stats.get(aid)
        if not attr_cfg:
            continue
        key = attr_cfg.get("key", "")
        if not key:
            continue
        base = float(attr_cfg.get("base", 0))
        step = float(attr_cfg.get("step", 0))
        value = base * count + step * step_val
        denom = base + step * 2
        eff = value / denom if denom else 0.0
        ret.append({
            "key": key,
            "value": value,
            "upNum": count,
            "eff": eff,
        })
    return ret


def get_attr_data_sr(arti: dict[str, Any], star: int = 5, slot_type: int | None = None) -> dict[str, Any] | bool:
    main_id = arti.get("mainId", 0)
    attr_ids = arti.get("attrIds", [])
    level = arti.get("level", 0)
    if slot_type is None:
        slot_type = arti.get("type", 0)
    return {
        "main": get_main_attr_sr(slot_type, main_id, level, star),
        "attrs": get_sub_attr_sr(attr_ids, star),
    }


def get_main_attr_gs(main_id: str, level: int, star: int = 5) -> dict[str, Any]:
    meta = Meta.get_meta("gs", "arti")
    main_id_map = meta.get("mainIdMap", {})
    attr_map = meta.get("attrMap", {})
    key = main_id_map.get(str(main_id))
    if not key:
        return {}
    attr_cfg = attr_map.get("dmg" if Format.is_elem(key) else key, {})
    pos_eff = 2 if key in ("hpPlus", "atkPlus", "defPlus") else 1
    star_eff = {1: 0.21, 2: 0.36, 3: 0.6, 4: 0.9, 5: 1.0}
    return {
        "id": main_id,
        "key": key,
        "value": attr_cfg.get("value", 0) * (1.2 + 0.34 * level) * pos_eff * star_eff.get(star, 1),
    }


def get_sub_attr_gs(attr_ids: list[str], star: int = 5) -> list[dict[str, Any]]:
    ret: list[dict[str, Any]] = []
    tmp: dict[str, dict[str, float]] = {}
    meta = Meta.get_meta("gs", "arti")
    attr_id_map = meta.get("attrIdMap", {})
    attr_map = meta.get("attrMap", {})
    for aid in attr_ids:
        cfg = attr_id_map.get(str(aid))
        if not cfg:
            continue
        key = cfg.get("key", "")
        value = cfg.get("value", 0)
        fmt = attr_map.get(key, {}).get("format", "comma")
        if key not in tmp:
            tmp[key] = {"key": key, "upNum": 0, "eff": 0.0, "value": 0.0}
        tmp[key]["value"] += value * (100 if fmt == "pct" else 1)
        tmp[key]["upNum"] += 1
        attr_value = attr_map.get(key, {}).get("value", value) or value or 1
        tmp[key]["eff"] += value / attr_value * (100 if fmt == "pct" else 1)
    return list(tmp.values())


def get_attr_data_gs(main_id: str, attr_ids: list[str], level: int, star: int = 5) -> dict[str, Any]:
    return {"main": get_main_attr_gs(main_id, level, star), "attrs": get_sub_attr_gs(attr_ids, star)}


def get_data(arti: dict[str, Any], idx: int = 1, game: str = "gs") -> dict[str, Any] | bool:
    if game == "gs":
        return get_attr_data_gs(arti.get("mainId", ""), arti.get("attrIds", []), arti.get("level", 0), arti.get("star", 5))
    if game == "sr":
        return get_attr_data_sr(arti, arti.get("star", 5), slot_type=arti.get("type", idx))
    return False
