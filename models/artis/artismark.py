from __future__ import annotations

from typing import Any

from ...components.format import Format
from ...components.meta import Meta
from . import artismarkcfg
from .artisattr import get_data
from ..artifact import Artifact


_MARK_CLASSES = [["D", 7], ["C", 14], ["B", 21], ["A", 28], ["S", 35], ["SS", 42], ["SSS", 49], ["ACE", 56], ["MAX", 70]]


def get_key_title_map(game: str = "gs") -> dict[str, str]:
    ret: dict[str, str] = {}
    attr_map = Meta.get_meta(game, "arti", "attrMap") or {}
    for key, ds in attr_map.items():
        ret[key] = ds.get("title", key)

    def _each(key: str, name: str) -> None:
        ret[key] = f"{name}伤加成"
    Format.each_elem(_each, game)
    return ret


def get_mark_class(mark: float) -> str:
    for cls_name, threshold in _MARK_CLASSES:
        if mark < threshold:
            return cls_name
    return _MARK_CLASSES[-1][0]


def _get_max_attr(attrs: dict[str, Any], pool: list, max_len: int = 1, ban: str = "") -> list[str]:
    candidates = []
    for a in pool:
        if a == ban:
            continue
        if a not in attrs:
            continue
        candidates.append((a, attrs[a].get("fixWeight", 0)))
    candidates.sort(key=lambda x: -x[1])
    return [a for a, _ in candidates][:max_len]


def get_max_mark(attrs: dict[str, Any], game: str = "gs") -> dict[str, float]:
    ret: dict[str, float] = {}
    meta = Meta.get_meta(game, "arti")
    main_attr = meta.get("mainAttr", {})
    sub_attr = meta.get("subAttr", [])
    slot_count = 6 if game == "sr" else 5
    for idx in range(1, slot_count + 1):
        total = 0.0
        m_mark = 0.0
        m_attr = ""
        if idx == 1:
            m_attr = "hpPlus"
        elif idx == 2:
            m_attr = "atkPlus"
        elif idx >= 3:
            best = _get_max_attr(attrs, main_attr.get(idx, []))
            if best:
                m_attr = best[0]
                m_mark = attrs[m_attr].get("fixWeight", 0)
                total += m_mark * 2

        best_sub = _get_max_attr(attrs, sub_attr if isinstance(sub_attr, list) else [], 4, m_attr)
        for aidx, a in enumerate(best_sub):
            weight = attrs[a].get("fixWeight", 0)
            total += weight * (6 if aidx == 0 else 1)

        ret[idx] = total
        ret[f"m{idx}"] = m_mark
    return ret


def format_arti(ds: Any, char_cfg_attrs: dict[str, Any] | None = None,
                is_main: bool = False, game: str = "gs") -> dict[str, Any]:
    if isinstance(ds, list):
        return [format_arti(d, char_cfg_attrs, is_main, game) for d in ds]

    key = ds.get("key", "")
    if not key or key == "undefined":
        return {}

    is_dmg = Format.is_elem(key, game)
    arr_cfg = Meta.get_meta(game, "arti", "attrMap") or {}
    arr_cfg = arr_cfg.get("dmg" if is_dmg else key, {})
    num = ds.get("value", ds.get(1, 0))
    fmt_fn = getattr(Format, arr_cfg.get("format", "comma"), Format.comma)
    val = fmt_fn(num, 1) if arr_cfg else str(num)
    ret: dict[str, Any] = {
        "key": key,
        "value": val,
        "upNum": ds.get("upNum", 0),
        "eff": ds.get("eff", 0),
    }

    if char_cfg_attrs:
        mark = (char_cfg_attrs.get(key, {}) or {}).get("mark", 0) * num
        if is_dmg:
            mark = (char_cfg_attrs.get("dmg", {}) or {}).get("mark", 0) * num
        if is_main:
            mark = mark / 4 + 0.01
            ret["key"] = key
        ret["mark"] = Format.comma(mark, 1)
        ret["_mark"] = mark

    eff_denom = 0.85 if game == "gs" else 0.9
    ret["eff"] = Format.comma(ret["eff"] / eff_denom, 1) if ret.get("eff") else "-"
    return ret


def _get_mark_single(char_cfg: dict[str, Any], idx: int, arti: dict[str, Any],
                     elem: str, avatar_id: int, game: str = "gs") -> float:
    ret = 0.0
    m_attr_cfg = arti.get("main", {})
    s_attr_list = arti.get("attrs", [])
    attrs_cfg = char_cfg.get("attrs", {})
    pos_max_mark = char_cfg.get("posMaxMark", {})

    key = m_attr_cfg.get("key", "")
    if not key:
        return 0.0
    fix_pct = 1.0
    idx = int(idx)
    if idx >= 3:
        main_key = key
        if key != "recharge":
            dmg_idx = 5 if game == "sr" else 4
            if idx == dmg_idx:
                if Format.same_elem(elem, key, game) or avatar_id == 10000128:
                    main_key = "dmg"
            fix_pct = max(0, min(1, (attrs_cfg.get(main_key, {}).get("weight", 0) or 0)
                                 / (pos_max_mark.get(f"m{idx}") or 1)))
            if game == "gs" and main_key in ("atk", "hp", "def") and attrs_cfg.get(main_key, {}).get("weight", 0) >= 75:
                fix_pct = 1.0
        ret += (attrs_cfg.get(main_key, {}).get("mark", 0) or 0) * (m_attr_cfg.get("value", 0) or 0) / 4

    for s_attr in s_attr_list:
        sk = s_attr.get("key", "") if isinstance(s_attr, dict) else ""
        sv = s_attr.get("value", 0) if isinstance(s_attr, dict) else 0
        if sk:
            ret += (attrs_cfg.get(sk, {}).get("mark", 0) or 0) * sv

    return ret * (1 + fix_pct) / 2 / (pos_max_mark.get(idx) or 66) * 66


def get_mark_detail(profile: Any, with_detail: bool = True) -> dict[str, Any]:
    if not profile or not profile.is_profile:
        return {}
    char_cfg = artismarkcfg.get_cfg(profile)
    artis_ret: dict[str, Any] = {}
    total_mark = 0.0
    game = profile.game
    artis_obj = getattr(profile, "artis", None) or getattr(profile, "_artis", None)
    if not artis_obj:
        return {}

    for idx_str, arti_data in artis_obj._data.items():
        idx = int(idx_str)
        parsed = get_data(arti_data, idx, game)
        if parsed:
            main_data = parsed.get("main", {}) or {}
            attrs_data = parsed.get("attrs", []) or []
            arti_data = {**arti_data, "main": main_data, "attrs": attrs_data}
        mark = _get_mark_single(char_cfg, idx, arti_data, profile.elem, profile.id, game)
        total_mark += mark
        artis_ret[idx_str] = {
            "_mark": mark,
            "mark": Format.comma(mark, 1),
            "markClass": get_mark_class(mark),
        }
        if with_detail:
            artifact = Artifact.get(arti_data.get("id", ""), game)
            if not artifact:
                artifact = Artifact.get(arti_data.get("name", ""), game)
            a_info = {}
            if artifact:
                a_info = {
                    "name": getattr(artifact, "name", ""),
                    "abbr": getattr(artifact, "abbr", ""),
                    "set": getattr(artifact, "set_name", ""),
                    "img": getattr(artifact, "img", ""),
                }
            artis_ret[idx_str].update(a_info)
            artis_ret[idx_str]["level"] = arti_data.get("level", 0)
            artis_ret[idx_str]["main"] = format_arti(parsed.get("main", {}) if parsed else {}, char_cfg.get("attrs"), True, game) if with_detail else {}
            artis_ret[idx_str]["attrs"] = format_arti(parsed.get("attrs", []) if parsed else [], char_cfg.get("attrs"), False, game) if with_detail else []

    set_data = artis_obj.get_set_data()
    slot_count = 5 if game == "gs" else 6
    avg_mark = total_mark / slot_count
    ret = {
        "classTitle": char_cfg.get("classTitle", ""),
        "artis": artis_ret,
        "mark": Format.comma(total_mark, 1),
        "_mark": total_mark,
        "markClass": get_mark_class(avg_mark),
        "sets": set_data.get("sets", {}),
        "names": set_data.get("names", []),
        "imgs": set_data.get("imgs", []),
    }
    if with_detail:
        ret["charWeight"] = {k: v.get("weight", 0) for k, v in (char_cfg.get("attrs", {}) or {}).items()}
    return ret
