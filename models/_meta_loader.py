from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from ..components.meta import Meta
from ..tools.path import miao_path


def _load_json(rel_path: str) -> dict[str, Any]:
    full = f"{miao_path}/{rel_path}"
    p = Path(full).resolve()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logging.warning("[meta] failed to load %s: %s", rel_path, e)
        return {}


def _parse_js_aliases(filepath: str) -> dict[str, str]:
    p = Path(filepath)
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    for line in text.split("\n"):
        m = re.match(r"""\s*['"]?(\w+)['"]?\s*:\s*(?:'(.*?)'|"(.*?)")\s*,?\s*$""", line)
        if m:
            result[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return result


_RE_DETAIL_TITLE = re.compile(r"title:\s*['\"](.+?)['\"]")
_RE_DETAIL_PARAMS = re.compile(r"params:\s*\{([^}]*)\}")
_RE_DMG_FN1 = re.compile(r"""basic\(\s*(?:calc\s*\(\s*)?attr\.(\w+)\s*(?:\s*\))?\s*\*\s*talent\.([\w]+)\[(?:'|")(.+?)(?:'|")\]\s*,\s*(?:'|")(.*?)(?:'|")\s*""")
_RE_DMG_FN1_V2 = re.compile(r"""basic\(\s*talent\.([\w]+)\[(?:'|")(.+?)(?:'|")\]\s*\*\s*(?:calc\s*\(\s*)?attr\.(\w+)\s*(?:\s*\))?\s*,\s*(?:'|")(.*?)(?:'|")\s*""")
_RE_DMG_FN1_V3 = re.compile(r"""basic\(\s*(?:calc\s*\(\s*)?attr\.(\w+)\s*(?:\s*\))?\s*\*\s*talent\.([\w]+)\[(?:'|")(.+?)(?:'|")\]""")
_RE_DMG_FN2 = re.compile(r"""dmg\(\s*talent\.([\w]+)\[(?:'|")(.+?)(?:'|")\].*?,\s*(?:'|")(.*?)(?:'|")\s*""")
_RE_BASIC_BODY = re.compile(r"""return\s+basic\(\s*(.+?)\s*,\s*(?:'|")(.*?)(?:'|")\s*\)""", re.DOTALL)
_RE_TALENT_REF = re.compile(r"""talent\.(\w+)\[(?:'|")(.+?)(?:'|")""")
_RE_ATTR_REF = re.compile(r"""attr\.(\w+)""")
_RE_CONST_TALENT = re.compile(r"""const\s+(\w+)\s*=\s*(?:.*?\b)?talent\.(\w+)\[(?:'|")(.+?)(?:'|")\]""")
_RE_CONST_ATTR = re.compile(r"""const\s+(\w+)\s*=\s*(?:.*?\b)?(?:calc\s*\(\s*)?attr\.(\w+)\s*(?:\s*\))?""")
_RE_DEFPARAMS = re.compile(r"export\s+const\s+defParams\s*=\s*\{([^}]+)\}")
_RE_DEFDMGIDX = re.compile(r"export\s+const\s+defDmgIdx\s*=\s*(\d+)")
_RE_MAINATTR = re.compile(r"export\s+const\s+mainAttr\s*=\s*['\"](.+?)['\"]")
_RE_BUFF_TITLE = re.compile(r"title:\s*['\"](.+?)['\"]")
_RE_BUFF_SORT = re.compile(r"sort:\s*(\d+)")
_RE_BUFF_DATA = re.compile(r"data:\s*\{([^}]+)\}")
_RE_BUFF_CHECK = re.compile(r"check:\s*\{([^}]+)\}")


def _find_matching_bracket(text: str, open_ch: str, close_ch: str, start: int = 0) -> int:
    depth = 0
    in_str = False
    str_char = None
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 1
                continue
            if ch == str_char:
                in_str = False
            continue
        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            continue
        if ch == open_ch:
            depth += 1
            if depth == 1 and i != start:
                depth = 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
    return 0


def _extract_objects_from_array(array_text: str) -> list[str]:
    objects: list[str] = []
    # Find the array brackets
    start = array_text.find("[")
    if start == -1:
        return objects
    # Walk through the array, extracting each top-level object
    i = start + 1
    while i < len(array_text):
        ch = array_text[i]
        if ch in " \t\n\r,":
            i += 1
            continue
        if ch == "{":
            end = _find_matching_bracket(array_text, "{", "}", i)
            if end == 0:
                break
            obj = array_text[i:end]
            objects.append(obj)
            i = end
            continue
        if ch == "]":
            break
        # Skip non-object tokens
        if ch in ("'", '"'):
            q = ch
            i += 1
            while i < len(array_text):
                if array_text[i] == "\\":
                    i += 2
                    continue
                if array_text[i] == q:
                    break
                i += 1
            i += 1
            continue
        i += 1
    return objects


def _extract_basic_type(text: str) -> str | None:
    m = re.search(r"""basic\(.*?,\s*'(.*?)'\s*\)""", text, re.DOTALL)
    return m.group(1) if m else None


def _infer_primary_stat(expr: str, var_attr: dict[str, str], var_talent: dict[str, tuple],
                         attr_refs: list[tuple[str, ...]]) -> str:
    # Try to find which stat is multiplied by a talent variable in the expression
    # Pattern: td * atk or atk * td or td * calc(attr.atk) etc.
    used_stats: set[str] = set()
    for ref in attr_refs:
        if isinstance(ref, tuple):
            used_stats.add(ref[0])
        elif isinstance(ref, str):
            used_stats.add(ref)
    for vname, stat in var_attr.items():
        used_stats.add(stat)
    if "hp" in used_stats:
        return "hp"
    if "atk" in used_stats:
        return "atk"
    if "def" in used_stats:
        return "def"
    return "atk"


def _parse_calc_js(filepath: str) -> dict[str, Any] | None:
    p = Path(filepath)
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8")
    result: dict[str, Any] = {
        "details": [],
        "buffs": [],
        "defParams": {},
        "defDmgIdx": 0,
        "mainAttr": "",
    }

    # defParams
    m = _RE_DEFPARAMS.search(text)
    if m:
        result["defParams"] = _simple_parse_kv(m.group(0))

    # defDmgIdx
    m = _RE_DEFDMGIDX.search(text)
    if m:
        result["defDmgIdx"] = int(m.group(1))

    # mainAttr
    m = _RE_MAINATTR.search(text)
    if m:
        result["mainAttr"] = m.group(1)

    # Extract the details array with brace-counting
    details_part = text.split("export const details")
    if len(details_part) < 2:
        return result if result["details"] else None
    details_body = details_part[1]
    # Remove everything after the first complete `];` for the array
    arr_end = _find_matching_bracket(details_body, "[", "]")
    if arr_end == 0:
        # Fallback: use old split approach
        if "];" in details_body:
            details_body = details_body.split("];")[0]
    else:
        details_body = details_body[:arr_end]

    # Extract each object in the array using brace counting
    detail_objects = _extract_objects_from_array(details_body)
    for obj_text in detail_objects:
        # --- Title extraction (static or dynamic) ---
        title_m = _RE_DETAIL_TITLE.search(obj_text)
        if title_m:
            title = title_m.group(1)
        else:
            # Try dynamic title: title: ({params}) => `...`
            dyn_m = re.search(r"title:\s*\([^)]*\)\s*=>\s*[`'\"]([^`'\"]+)[`'\"]", obj_text)
            title = dyn_m.group(1) if dyn_m else None
        if not title:
            continue
        params_m = _RE_DETAIL_PARAMS.search(obj_text)

        # --- Intentional skips ---
        has_heal = bool(re.search(r"\bheal\s*\(", obj_text))
        has_shield = bool(re.search(r"\bshield\s*\(|dmg\.shield\s*\(", obj_text))
        has_reaction_dmg = bool(re.search(r"dmg\.reaction\s*\(", obj_text))
        has_reaction_destructured = bool(re.search(r"\breaction\b", obj_text)) and not has_reaction_dmg
        has_percent = bool(re.search(r"Format\.percent", obj_text))
        has_text_avg = bool(re.search(r"avg:\s*['`]", obj_text))
        if has_heal or has_shield or has_reaction_dmg or has_reaction_destructured or has_percent or has_text_avg:
            detail: dict[str, Any] = {"title": title, "params": {}, "dmg": None}
            if params_m:
                detail["params"] = _simple_parse_kv("{" + params_m.group(1) + "}")
            result["details"].append(detail)
            continue

        # --- Common helpers for complex patterns ---
        def _build_multi(o: str) -> dict:
            talent_refs = _RE_TALENT_REF.findall(o)
            attr_refs = _RE_ATTR_REF.findall(o)
            var_talent = {m.group(1): (m.group(2), m.group(3)) for m in _RE_CONST_TALENT.finditer(o)}
            var_attr = {m.group(1): m.group(2) for m in _RE_CONST_ATTR.finditer(o)}
            multi = [{"key": tk, "name": tn} for tk, tn in var_talent.values()]
            if not multi:
                multi = [{"key": tk, "name": tn} for tk, tn in talent_refs]
            primary_stat = _infer_primary_stat("", var_attr, var_talent, attr_refs)
            return {
                "stat": primary_stat,
                "talentKey": multi[0]["key"] if multi else "a",
                "skillName": multi[0]["name"] if multi else "",
                "skillType": "a",
                "multiTalent": multi,
                "varTalent": var_talent,
                "varAttr": var_attr,
            }

        dmg_m1 = _RE_DMG_FN1.search(obj_text)
        dmg_m1v2 = _RE_DMG_FN1_V2.search(obj_text) if not dmg_m1 else None
        dmg_m1v3 = _RE_DMG_FN1_V3.search(obj_text) if not dmg_m1 and not dmg_m1v2 else None
        dmg_m2 = _RE_DMG_FN2.search(obj_text)
        dmg_m3 = _RE_BASIC_BODY.search(obj_text)
        dmg_m4 = re.search(r"""dmg\.basic\(\s*(.+?)\s*,\s*(?:'|")(.*?)(?:'|")\s*\)""", obj_text, re.DOTALL) if not any([dmg_m1, dmg_m1v2, dmg_m1v3, dmg_m2, dmg_m3]) else None
        # Standalone basic(expr, type) without return keyword
        dmg_m5 = re.search(r"""(?<!dmg\.)basic\(\s*(.+?)\s*,\s*(?:'|"|`)([^'\"`]*?)(?:'|"|`)\s*(?:,.*?)?\)""", obj_text, re.DOTALL) if not any([dmg_m1, dmg_m1v2, dmg_m1v3, dmg_m2, dmg_m3, dmg_m4]) else None
        # dynamic(talent.X['Y'], 'type')
        dmg_m6 = re.search(r"""dynamic\(\s*talent\.(\w+)\[(?:'|")(.+?)(?:'|")\]\s*,\s*(?:'|")([^'"]*?)(?:'|")\s*\)""", obj_text) if not any([dmg_m1, dmg_m1v2, dmg_m1v3, dmg_m2, dmg_m3, dmg_m4, dmg_m5]) else None
        # basic(expr) without type (last basic resort)
        dmg_m7 = re.search(r"""(?<!dmg\.)basic\(\s*(.+?)\s*\)""", obj_text, re.DOTALL) if not any([dmg_m1, dmg_m1v2, dmg_m1v3, dmg_m2, dmg_m3, dmg_m4, dmg_m5, dmg_m6]) else None
        # broader dmg(expr, type) / dmg(expr)
        dmg_m8 = re.search(r"""dmg\(\s*(talent\.(\w+)\[(?:'|")(.+?)(?:'|")\]|[^,)]+)\s*(?:,\s*(?:'|"|`)([^'\"`]*?)(?:'|"|`)\s*(?:,.*?)?)?\)""", obj_text) if not any([dmg_m1, dmg_m1v2, dmg_m1v3, dmg_m2, dmg_m3, dmg_m4, dmg_m5, dmg_m6, dmg_m7]) else None
        # Fallback: avg: calc(attr.X) * talent.Y['Z'] or avg: talent.Y['Z'] * attr.X
        dmg_m9 = re.search(r"""avg:\s*(?:(?:calc\s*\(\s*)?attr\.(\w+)\s*(?:\s*\))?\s*\*\s*)?talent\.(\w+)\[(?:'|")(.+?)(?:'|")\]\s*(?:\*\s*(?:calc\s*\(\s*)?attr\.(\w+)\s*(?:\s*\))?)?""", obj_text) if not any([dmg_m1, dmg_m1v2, dmg_m1v3, dmg_m2, dmg_m3, dmg_m4, dmg_m5, dmg_m6, dmg_m7, dmg_m8]) else None
        # Plain avg with only talent ref
        dmg_m10 = re.search(r"""avg:\s*talent\.(\w+)\[(?:'|")(.+?)(?:'|")\]""", obj_text) if not any([dmg_m1, dmg_m1v2, dmg_m1v3, dmg_m2, dmg_m3, dmg_m4, dmg_m5, dmg_m6, dmg_m7, dmg_m8, dmg_m9]) else None

        detail = {"title": title, "params": {}, "dmg": None}
        if params_m:
            detail["params"] = _simple_parse_kv("{" + params_m.group(1) + "}")
        if dmg_m1:
            detail["dmg"] = {
                "stat": dmg_m1.group(1),
                "talentKey": dmg_m1.group(2),
                "skillName": dmg_m1.group(3),
                "skillType": dmg_m1.group(4) if dmg_m1.lastindex >= 4 else _extract_basic_type(obj_text) or "a",
            }
        elif dmg_m1v2:
            detail["dmg"] = {
                "stat": dmg_m1v2.group(3),
                "talentKey": dmg_m1v2.group(1),
                "skillName": dmg_m1v2.group(2),
                "skillType": dmg_m1v2.group(4),
            }
        elif dmg_m1v3:
            detail["dmg"] = {
                "stat": dmg_m1v3.group(1),
                "talentKey": dmg_m1v3.group(2),
                "skillName": dmg_m1v3.group(3),
                "skillType": _extract_basic_type(obj_text) or "a",
            }
        elif dmg_m2:
            detail["dmg"] = _build_multi(obj_text)
            detail["dmg"]["skillType"] = dmg_m2.group(3)
        elif dmg_m3:
            basic_expr = dmg_m3.group(1)
            basic_type = dmg_m3.group(2)
            talent_refs = _RE_TALENT_REF.findall(obj_text)
            attr_refs = _RE_ATTR_REF.findall(obj_text)
            var_talent = {m.group(1): (m.group(2), m.group(3)) for m in _RE_CONST_TALENT.finditer(obj_text)}
            var_attr = {m.group(1): m.group(2) for m in _RE_CONST_ATTR.finditer(obj_text)}
            primary_stat = _infer_primary_stat(basic_expr, var_attr, var_talent, attr_refs)
            multi = [{"key": tk, "name": tn} for tk, tn in var_talent.values()]
            if not multi:
                multi = [{"key": tk, "name": tn} for tk, tn in talent_refs]
            detail["dmg"] = {
                "stat": primary_stat,
                "talentKey": multi[0]["key"] if multi else "a",
                "skillName": multi[0]["name"] if multi else "",
                "skillType": basic_type,
                "multiTalent": multi,
                "varTalent": var_talent,
                "varAttr": var_attr,
            }
        elif dmg_m4:
            basic_val = dmg_m4.group(1)
            basic_type = dmg_m4.group(2)
            talent_refs = _RE_TALENT_REF.findall(obj_text)
            attr_refs = _RE_ATTR_REF.findall(obj_text)
            var_talent = {m.group(1): (m.group(2), m.group(3)) for m in _RE_CONST_TALENT.finditer(obj_text)}
            var_attr = {m.group(1): m.group(2) for m in _RE_CONST_ATTR.finditer(obj_text)}
            primary_stat = _infer_primary_stat(basic_val or "", var_attr, var_talent, attr_refs)
            multi = [{"key": tk, "name": tn} for tk, tn in var_talent.values()]
            if not multi:
                multi = [{"key": tk, "name": tn} for tk, tn in talent_refs]
            if multi:
                detail["dmg"] = {
                    "stat": primary_stat,
                    "talentKey": multi[0]["key"],
                    "skillName": multi[0]["name"],
                    "skillType": basic_type,
                    "multiTalent": multi,
                    "varTalent": var_talent,
                    "varAttr": var_attr,
                }
        elif dmg_m5:
            basic_expr = dmg_m5.group(1)
            basic_type = dmg_m5.group(2)
            dmg_dict = _build_multi(obj_text)
            dmg_dict["skillType"] = basic_type
            detail["dmg"] = dmg_dict
        elif dmg_m6:
            detail["dmg"] = {
                "stat": "atk",
                "talentKey": dmg_m6.group(1),
                "skillName": dmg_m6.group(2),
                "skillType": dmg_m6.group(3),
            }
        elif dmg_m7:
            basic_expr = dmg_m7.group(1)
            dmg_dict = _build_multi(obj_text)
            detail["dmg"] = dmg_dict
        elif dmg_m8:
            raw_expr = dmg_m8.group(1)
            raw_type = dmg_m8.group(4) if dmg_m8.lastindex >= 4 and dmg_m8.group(4) else None
            dmg_dict = _build_multi(obj_text)
            if raw_type:
                dmg_dict["skillType"] = raw_type
            detail["dmg"] = dmg_dict
        elif dmg_m9:
            stat = dmg_m9.group(1) or dmg_m9.group(4) or ""
            detail["dmg"] = {
                "stat": stat if stat else "atk",
                "talentKey": dmg_m9.group(2),
                "skillName": dmg_m9.group(3),
                "skillType": _extract_basic_type(obj_text) or "a",
            }
        elif dmg_m10:
            detail["dmg"] = {
                "stat": "atk",
                "talentKey": dmg_m10.group(1),
                "skillName": dmg_m10.group(2),
                "skillType": "a",
            }
        result["details"].append(detail)

    # Parse buffs using brace-counting
    buffs_part = text.split("export const buffs")
    if len(buffs_part) >= 2:
        buffs_body = buffs_part[-1]
        arr_end = _find_matching_bracket(buffs_body, "[", "]")
        if arr_end > 0:
            buffs_body = buffs_body[:arr_end]
        buff_objects = _extract_objects_from_array(buffs_body)
        for obj_text in buff_objects:
            title_m = _RE_BUFF_TITLE.search(obj_text)
            if not title_m:
                continue
            buf: dict[str, Any] = {"title": title_m.group(1), "data": {}}
            sort_m = _RE_BUFF_SORT.search(obj_text)
            if sort_m:
                buf["sort"] = int(sort_m.group(1))
            cons_m = re.search(r"cons:\s*(\d+)", obj_text)
            if cons_m:
                buf["cons"] = int(cons_m.group(1))
            # Only parse data with simple numeric values (skip function-based data)
            data_m = _RE_BUFF_DATA.search(obj_text)
            if data_m:
                parsed_data = _simple_parse_kv("{" + data_m.group(1) + "}")
                if parsed_data:
                    buf["data"] = parsed_data
            result["buffs"].append(buf)

    return result if result["details"] else None


def _simple_parse_kv(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for m in re.finditer(r"""(\w+)\s*:\s*(?:'([^']*)'|"([^"]*)"|(\S+))""", text, re.MULTILINE):
        key = m.group(1)
        val = m.group(2) or m.group(3) or m.group(4) or ""
        if val.isdigit():
            val = int(val)
        elif val.replace(".", "").isdigit():
            val = float(val)
        result[key] = val
    return result


def _parse_talent_value(v: Any) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if "%" in s:
        try:
            return float(s.replace("%", "").strip()) / 100.0
        except (ValueError, TypeError):
            return 0.0
    if "+" in s:
        try:
            parts = [float(p.strip()) for p in s.split("+") if p.strip()]
            return sum(parts)
        except (ValueError, TypeError):
            return 0.0
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _load_talent_multipliers(char_dir: Path) -> dict[str, list[dict[str, Any]]]:
    data_json = char_dir / "data.json"
    if not data_json.exists():
        return {}
    try:
        data = json.loads(data_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    talent = data.get("talent", {})
    result: dict[str, list[dict[str, Any]]] = {}
    for skill_key, skill_data in talent.items():
        raw_tables = skill_data.get("tables", [])
        if not raw_tables:
            continue
        if isinstance(raw_tables, dict):
            raw_tables = raw_tables.values()
        parsed = []
        for tbl in raw_tables:
            if isinstance(tbl, str):
                continue
            name = tbl.get("name", "")
            values = tbl.get("values", [])
            if not isinstance(values, list):
                continue
            parsed.append({"name": name, "values": [_parse_talent_value(v) for v in values]})
        if parsed:
            result[skill_key] = parsed
    return result


_WIFE_CFG: dict[str, list[str]] = {
    "girlfriend": [
        "琴,丽莎,荧,芭芭拉,安柏,香菱,北斗,凝光,菲谢尔,诺艾尔,甘雨,莫娜,刻晴,砂糖,辛焱,罗莎莉亚,胡桃,烟绯,优菈",
        "绫华,宵宫,雷神,心海,九条裟罗,八重神子,埃洛伊,申鹤,云堇,夜兰,久岐忍",
        "柯莱,多莉,妮露,坎蒂丝,迪希雅,莱依拉,珐露珊,绮良良",
        "琳妮特,夏洛蒂,芙宁娜,夏沃蕾,娜维娅,闲云,千织,仆人,克洛琳德",
        "玛拉妮,希诺宁,恰斯卡,玛薇卡,茜特菈莉,蓝砚,梦见月瑞希,伊安珊,瓦雷莎,爱可菲,丝柯克,伊涅芙",
        "菈乌玛,奈芙尔,雅珂达,哥伦比娅,兹白,莉奈娅,尼可,桑多涅",
        "女士,萍姥姥,归终,伐难,应达,少女,天理",
    ],
    "boyfriend": [
        "空,凯亚,迪卢克,雷泽,温迪,行秋,魈,钟离,班尼特,公子,重云,阿贝多,万叶",
        "托马,五郎,一斗,平藏,绫人",
        "提纳里,流浪者,赛诺,卡维,艾尔海森,米卡,白术",
        "林尼,菲米尼,莱欧斯利,那维莱特,嘉明,塞索斯",
        "基尼奇,欧洛伦,伊法,塔利雅",
        "菲林斯,叶洛亚,法尔伽,洛恩",
        "富人,博士,丑角,公鸡,队长,戴因",
    ],
    "daughter": "可莉,七七,迪奥娜,早柚,派蒙,瑶瑶,纳西妲,希格雯,卡齐娜,爱诺,布伦妮",
    "son": "",
}


def _load_wife_data(game: str) -> None:
    if game != "gs":
        return
    char_meta = Meta.create(game, "char")
    wife_data: dict[str, dict[str, bool]] = {}
    for wtype, names in _WIFE_CFG.items():
        wife_data[wtype] = {}
        if isinstance(names, list):
            text = ",".join(names)
        else:
            text = names
        for name in text.split(","):
            name = name.strip()
            if not name:
                continue
            _id = char_meta.get_id(name)
            if _id:
                wife_data[wtype][str(_id)] = True
    char_meta.add_meta({"wifeData": wife_data})


def _load_dmg_meta(game: str) -> None:
    base = f"{miao_path}/resources/meta-{game}"
    chars_dir = Path(f"{base}/character")
    if not chars_dir.exists():
        return
    for char_dir in sorted(chars_dir.iterdir()):
        if not char_dir.is_dir():
            continue
        calc_file = char_dir / "calc.js"
        if not calc_file.exists():
            continue
        parsed = _parse_calc_js(str(calc_file))
        if not parsed:
            continue
        multipliers = _load_talent_multipliers(char_dir)
        char_name = char_dir.name
        char_data = Meta.get_data(game, "char", char_name)
        char_id = str(char_data.get("id")) if char_data else char_name
        Meta.create(game, "dmg").add_data_item(char_id, {
            "name": char_name,
            "calc": parsed,
            "multipliers": multipliers,
        })


def _parse_js_const(text: str, const_name: str) -> str | None:
    """Extract the value of `(export) const <const_name> = <value>;` from JS text.
    Uses brace-counting for robust nested object extraction.
    Handles both `export const` and bare `const` (SR's meta.js attrMap).
    """
    m = re.search(
        rf"(?:export\s+)?const\s+{re.escape(const_name)}\s*=\s*",
        text, re.DOTALL
    )
    if not m:
        return None
    start = m.end()
    if start >= len(text):
        return None
    # Skip whitespace after '='
    text = text[start:]
    text = text.lstrip()
    if not text:
        return None
    start = 0  # now relative to the stripped text

    # Determine value type and extract from stripped `text`
    if text[0] in ("'", '"'):
        quote = text[0]
        end = 1
        while end < len(text):
            if text[end] == "\\":
                end += 2
                continue
            if text[end] == quote:
                end += 1
                # Check for .split(',') pattern after the string
                rest = text[end:end + 20]
                split_m = re.match(r"\s*\.split\s*\(\s*['\"]\s*,\s*['\"]\s*\)", rest)
                if split_m:
                    end += split_m.end()
                return text[:end]
            end += 1
        return text
    if text[0] == "[":
        depth = 1
        end = 1
        while end < len(text) and depth > 0:
            if text[end] == "[":
                depth += 1
            elif text[end] == "]":
                depth -= 1
            elif text[end] in ("'", '"'):
                q = text[end]
                end += 1
                while end < len(text):
                    if text[end] == "\\":
                        end += 2
                        continue
                    if text[end] == q:
                        break
                    end += 1
            end += 1
        return text[:end]
    if text[0] == "{":
        depth = 1
        end = 1
        while end < len(text) and depth > 0:
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
            elif text[end] in ("'", '"'):
                q = text[end]
                end += 1
                while end < len(text):
                    if text[end] == "\\":
                        end += 2
                        continue
                    if text[end] == q:
                        break
                    end += 1
            end += 1
        return text[:end]
    # Fallback: return up to semicolon or newline
    end = 0
    while end < len(text) and text[end] not in ";\n":
        end += 1
    return text[:end].strip() or None


def _parse_js_object_literal(text: str) -> dict[str, Any]:
    """Parse a JS object literal string into a Python dict.
    Handles nested objects, string/number values, and .split(',') patterns.
    """
    text = text.strip()
    # Remove surrounding braces
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1].strip()
    if text.endswith(";"):
        text = text[:-1].strip()

    result: dict[str, Any] = {}
    # Match key: value pairs
    i = 0
    while i < len(text):
        # Skip whitespace and commas
        if text[i] in " \t\n\r,":
            i += 1
            continue
        # Extract key (can be identifier or quoted string)
        key_m = re.match(r"""\s*(?:(['"])(.*?)\1|(\w+))\s*:\s*""", text[i:])
        if not key_m:
            i += 1
            continue
        key = key_m.group(2) or key_m.group(3)
        i += key_m.end()

        # Extract value
        val, consumed = _parse_js_value(text[i:])
        if consumed > 0:
            result[key] = val
            i += consumed
        else:
            i += 1
    return result


def _parse_js_value(text: str) -> tuple[Any, int]:
    """Parse a single JS value. Returns (value, consumed_chars)."""
    text = text.lstrip()
    if not text:
        return None, 0
    orig = text

    # .split(',') pattern
    split_m = re.match(r"""\s*('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")\s*\.split\s*\(\s*['"]\s*,\s*['"]\s*\)""", text)
    if split_m:
        raw = split_m.group(1)[1:-1]
        return [s.strip() for s in raw.split(",")], split_m.end()

    # String
    if text[0] in ("'", '"'):
        idx = 1
        while idx < len(text):
            if text[idx] == "\\":
                idx += 2
                continue
            if text[idx] == text[0]:
                end = idx + 1
                val = text[1:idx]
                return val, end
            idx += 1
        return text[1:], len(text)

    # Number with optional arithmetic (*, /)
    num_m = re.match(r"-?\d+(?:\.\d+)?\s*(?:[\*/]\s*-?\d+(?:\.\d+)?)?", text)
    if num_m:
        raw = num_m.group()
        if "*" in raw or "/" in raw:
            parts = re.split(r"\s*[\*/]\s*", raw)
            if len(parts) == 2:
                a, b = float(parts[0]), float(parts[1])
                return (a * b if "*" in raw else a / b) if b != 0 else a, num_m.end()
        return int(raw) if "." not in raw else float(raw), num_m.end()

    # Object literal
    if text[0] == "{":
        depth = 1
        idx = 1
        while idx < len(text) and depth > 0:
            if text[idx] == "{":
                depth += 1
            elif text[idx] == "}":
                depth -= 1
            elif text[idx] in ("'", '"'):
                # Skip string content
                q = text[idx]
                idx += 1
                while idx < len(text):
                    if text[idx] == "\\":
                        idx += 2
                        continue
                    if text[idx] == q:
                        break
                    idx += 1
            idx += 1
        obj_str = text[:idx]
        return _parse_js_object_literal(obj_str), idx

    # Array literal
    if text[0] == "[":
        depth = 1
        idx = 1
        while idx < len(text) and depth > 0:
            if text[idx] == "[":
                depth += 1
            elif text[idx] == "]":
                depth -= 1
            elif text[idx] in ("'", '"'):
                q = text[idx]
                idx += 1
                while idx < len(text):
                    if text[idx] == "\\":
                        idx += 2
                        continue
                    if text[idx] == q:
                        break
                    idx += 1
            idx += 1
        arr_str = text[:idx]
        items: list[Any] = []
        inner = arr_str[1:-1].strip()
        if inner:
            # Parse comma-separated items
            while inner:
                inner = inner.lstrip()
                if not inner or inner[0] == ",":
                    inner = inner[1:] if inner else ""
                    continue
                val, consumed = _parse_js_value(inner)
                if consumed > 0:
                    items.append(val)
                    inner = inner[consumed:].lstrip()
                    if inner and inner[0] == ",":
                        inner = inner[1:]
                else:
                    break
        return items, idx

    # Boolean / null
    if text.startswith("true"):
        return True, 4
    if text.startswith("false"):
        return False, 5
    if text.startswith("null") or text.startswith("undefined"):
        return None, 4

    return None, 0


def _load_artis_meta_js(game: str) -> None:
    """Load artifact meta config from JS files (extra.js / meta.js + artis-mark.js)."""
    base = f"{miao_path}/resources/meta-{game}"

    # GS uses extra.js, SR uses meta.js
    js_file = Path(f"{base}/artifact/extra.js" if game == "gs" else f"{base}/artifact/meta.js")
    if not js_file.exists():
        return
    text = js_file.read_text(encoding="utf-8")

    meta_data: dict[str, Any] = {}

    # Parse attrMap
    attr_map_str = _parse_js_const(text, "attrMap")
    if attr_map_str:
        meta_data["attrMap"] = _parse_js_object_literal(attr_map_str)

    # Parse mainAttr
    main_attr_str = _parse_js_const(text, "mainAttr")
    if main_attr_str:
        meta_data["mainAttr"] = _parse_js_object_literal(main_attr_str)

    # Parse subAttr
    sub_attr_str = _parse_js_const(text, "subAttr")
    if sub_attr_str:
        val, _ = _parse_js_value(sub_attr_str)
        if isinstance(val, list):
            meta_data["subAttr"] = val

    # Parse attrIdMap (GS only) — maps numeric affix IDs to {key, value}
    if game == "gs":
        attr_id_str = _parse_js_const(text, "attrIdMap")
        if attr_id_str:
            meta_data["attrIdMap"] = _parse_js_object_literal(attr_id_str)

    # Parse mainIdMap (GS only)
    if game == "gs":
        main_id_str = _parse_js_const(text, "mainIdMap")
        if main_id_str:
            meta_data["mainIdMap"] = _parse_js_object_literal(main_id_str)

    # Parse basicNum and attrPct — needed to compute attrMap[].value (computed dynamically in JS)
    if game == "gs":
        basic_num_str = _parse_js_const(text, "basicNum")
        basic_num = 3.885
        if basic_num_str:
            bn_val, _ = _parse_js_value(basic_num_str)
            if isinstance(bn_val, (int, float)):
                basic_num = float(bn_val)

        attr_pct_str = _parse_js_const(text, "attrPct")
        attr_pct: dict[str, Any] = {}
        if attr_pct_str:
            attr_pct = _parse_js_object_literal(attr_pct_str)

        # Compute value = basicNum * attrPct[key] for each attrMap entry
        if "attrMap" in meta_data:
            for key, cfg in meta_data["attrMap"].items():
                if "value" not in cfg and isinstance(cfg, dict):
                    pct = attr_pct.get(key, 1)
                    cfg["value"] = basic_num * float(pct)

    if meta_data:
        Meta.create(game, "arti").add_meta(meta_data)

    # Load artis-mark.js (usefulAttr = per-character scoring weights)
    mark_file = Path(f"{base}/artifact/artis-mark.js")
    if mark_file.exists():
        mark_text = mark_file.read_text(encoding="utf-8")
        useful_str = _parse_js_const(mark_text, "usefulAttr")
        if useful_str:
            useful_data = _parse_js_object_literal(useful_str)
            Meta.create(game, "arti").add_meta({"usefulAttr": useful_data})


_RE_ATTR = re.compile(r"""attr\(\s*['"](.+?)['"]\s*,\s*([0-9.-]+)\s*\)""")


def _load_artis_set_buffs(game: str) -> None:
    calc_file = Path(f"{miao_path}/resources/meta-{game}/artifact/calc.js")
    if not calc_file.exists():
        return
    raw = calc_file.read_text(encoding="utf-8").replace("\r", "")
    arti_buffs: dict[str, dict[str, list[dict[str, Any]]]] = {}

    # Find each set block: "setName: { 2: ..., 4: ... }"
    set_pat = re.compile(r"""^\s{2}(?:'(.*?)'|"(.*?)"|([^'"]\S+?))\s*:\s*\{""", re.MULTILINE)
    for m in set_pat.finditer(raw):
        set_name = m.group(1) or m.group(2) or m.group(3)
        brace_start = m.end()
        depth = 1
        pos = brace_start
        while pos < len(raw) and depth > 0:
            if raw[pos] == "{":
                depth += 1
            elif raw[pos] == "}":
                depth -= 1
            pos += 1
        block = raw[brace_start:pos - 1]

        # Extract 2-piece and 4-piece attr calls
        for count_key in ("2", "4"):
            inner_pat = re.compile(
                r"^\s{4}" + re.escape(count_key) + r"\s*:\s*(\[|)", re.MULTILINE
            )
            cm = inner_pat.search(block)
            if not cm:
                continue
            inner_start = cm.end()
            if cm.group(1) == "[":
                inner_depth = 1
                ipos = inner_start
                while ipos < len(block) and inner_depth > 0:
                    if block[ipos] == "[":
                        inner_depth += 1
                    elif block[ipos] == "]":
                        inner_depth -= 1
                    ipos += 1
                inner_text = block[inner_start:ipos - 1]
            else:
                inner_text = block[inner_start:]
                ipos = 0
                paren_depth = 0
                while ipos < len(inner_text):
                    ch = inner_text[ipos]
                    if ch == "(":
                        paren_depth += 1
                    elif ch == ")":
                        paren_depth -= 1
                    elif ch in ",}\n" and paren_depth == 0:
                        break
                    ipos += 1
                inner_text = inner_text[:ipos]

            buffs_for_count: list[dict[str, Any]] = []
            for am in _RE_ATTR.finditer(inner_text):
                buffs_for_count.append({
                    "isStatic": True,
                    "key": am.group(1),
                    "value": float(am.group(2)),
                })
            if buffs_for_count:
                arti_buffs.setdefault(set_name, {})[count_key] = buffs_for_count

    if arti_buffs:
        Meta.create(game, "arti").add_meta({"artiBuffs": arti_buffs})


def _load_weapon_buffs() -> None:
    types = "记忆,毁灭,巡猎,智识,同谐,虚无,存护,丰饶,欢愉".split(",")
    base = f"{miao_path}/resources/meta-sr/weapon"
    weapon_buffs: dict[str, list[dict[str, Any]]] = {}
    for typ in types:
        calc_file = Path(f"{base}/{typ}/calc.js")
        if not calc_file.exists():
            continue
        text = calc_file.read_text(encoding="utf-8").replace("\r", "")
        weapon_pat = re.compile(r"""^\s{4}(?:'(.*?)'|"(.*?)"|(.+?))\s*:\s*\[""", re.MULTILINE)
        for m in weapon_pat.finditer(text):
            wname = m.group(1) or m.group(2) or (m.group(3).rstrip().lstrip() if m.group(3) else "")
            if not wname:
                continue
            brace_start = m.end()
            depth = 1
            pos = brace_start
            while pos < len(text) and depth > 0:
                if text[pos] == "[":
                    depth += 1
                elif text[pos] == "]":
                    depth -= 1
                pos += 1
            block = text[brace_start:pos - 1]
            buffs: list[dict[str, Any]] = []
            for sm in re.finditer(r"""staticIdx\(\s*(\d+)\s*,\s*['"](.+?)['"]\s*\)""", block):
                buffs.append({"isStatic": True, "idx": int(sm.group(1)), "key": sm.group(2)})
            if buffs:
                weapon_buffs[wname] = buffs
    if weapon_buffs:
        Meta.create("sr", "weapon").add_meta({"weaponBuffs": weapon_buffs})


def load_meta_game(game: str = "gs") -> None:
    base = f"{miao_path}/resources/meta-{game}"

    # Character
    data = _load_json(f"resources/meta-{game}/character/data.json")
    if data:
        Meta.create(game, "char").add_data(data)
    alias = _parse_js_aliases(f"{base}/character/alias.js")
    if alias:
        Meta.create(game, "char").add_alias(alias)
    extra = _parse_js_aliases(f"{base}/character/extra.js")
    if extra:
        Meta.create(game, "char").add_alias(extra)

    # Weapon — GS uses per-type subdirs, SR uses single data.json
    weapon_dir = Path(f"{base}/weapon")
    if weapon_dir.exists():
        # Try top-level data.json first (SR format)
        wdata = _load_json(f"resources/meta-{game}/weapon/data.json")
        if wdata:
            Meta.create(game, "weapon").add_data(wdata)
        else:
            # Try per-type subdirectory format (GS format)
            for wtype_dir in sorted(weapon_dir.iterdir()):
                if not wtype_dir.is_dir():
                    continue
                wdata = _load_json(f"resources/meta-{game}/weapon/{wtype_dir.name}/data.json")
                if wdata:
                    for entry in wdata.values():
                        if isinstance(entry, dict) and "type" not in entry:
                            entry["type"] = wtype_dir.name
                    Meta.create(game, "weapon").add_data(wdata)
        alias = _parse_js_aliases(f"{base}/weapon/alias.js")
        if alias:
            Meta.create(game, "weapon").add_alias(alias)

    # Artifact (individual pieces) + artifact sets
    data = _load_json(f"resources/meta-{game}/artifact/data.json")
    if data:
        Meta.create(game, "arti").add_data(data)
        arti_set_meta = Meta.create(game, "artiSet")
        for set_id, set_data in data.items():
            arti_set_meta.add_data_item(set_id, set_data)
            set_name = set_data.get("name", "")
            idxs = set_data.get("idxs", {})
            for slot_key, piece in idxs.items():
                piece_id = str(piece.get("id", ""))
                piece_name = piece.get("name", "")
                if piece_id and piece_name:
                    # Register individual piece in arti meta (for Artifact.get by itemId)
                    Meta.create(game, "arti").add_data_item(piece_id, {
                        "id": piece_id,
                        "name": piece_name,
                        "set": set_name,
                        "idx": int(slot_key),
                    })
                # Register 2-digit piece ID prefix as artiSet alias
                if game == "gs" and len(piece_id) >= 2:
                    prefix = piece_id[:2]
                    if prefix not in arti_set_meta.data and prefix not in arti_set_meta.alias:
                        arti_set_meta.alias[prefix] = set_id
    alias = _parse_js_aliases(f"{base}/artifact/alias.js")
    if alias:
        Meta.create(game, "arti").add_alias(alias)

    # Artifact meta config (attrMap, mainAttr, subAttr, usefulAttr) from JS files
    _load_artis_meta_js(game)

    # Meta config
    info = _load_json(f"resources/meta-{game}/info/index.json")
    if isinstance(info, dict):
        for category in ("char", "weapon", "arti"):
            cat_data = info.get(category, {})
            if cat_data:
                Meta.create(game, category).add_meta(cat_data)

    # Artifact set buffs (from calc.js)
    _load_artis_set_buffs(game)

    # Damage calc metadata (calc.js + talent multipliers)
    _load_dmg_meta(game)

    # Wife data
    _load_wife_data(game)


def load_all_meta() -> None:
    for game in ["gs", "sr"]:
        load_meta_game(game)
    _load_weapon_buffs()
