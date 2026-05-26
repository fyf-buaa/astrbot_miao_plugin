from __future__ import annotations

from typing import Any

from ...components.format import Format

_ELEM_DMG_KEYS = {"phy", "fire", "ice", "elec", "wind", "quantum", "imaginary"}


def _apply_sr_stat_simple(key: str, val: float,
                          hp_pct: float, atk_pct: float, def_pct: float, speed_pct: float,
                          hp_plus: float, atk_plus: float, def_plus: float,
                          cpct: float, cdmg: float,
                          speed: float, eff_pct: float, eff_def: float, heal: float,
                          stance: float, recharge: float, dmg_bonus: float
                          ) -> tuple[float, ...]:
    if key in ("hpPlus",):
        hp_plus += val
    elif key in ("atkPlus",):
        atk_plus += val
    elif key in ("defPlus",):
        def_plus += val
    elif key in ("hp", "hpPct"):
        hp_pct += val
    elif key in ("atk", "atkPct"):
        atk_pct += val
    elif key in ("def", "defPct"):
        def_pct += val
    elif key in ("speed",):
        speed += val
    elif key in ("speedPct",):
        speed_pct += val
    elif key in ("cpct",):
        cpct += val
    elif key in ("cdmg",):
        cdmg += val
    elif key in ("effPct",):
        eff_pct += val
    elif key in ("effDef",):
        eff_def += val
    elif key in ("heal",):
        heal += val
    elif key in ("stance",):
        stance += val
    elif key in ("recharge",):
        recharge += val
    elif key in _ELEM_DMG_KEYS:
        dmg_bonus += val
    return (hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus,
            cpct, cdmg, speed, eff_pct, eff_def, heal, stance, recharge, dmg_bonus)


def calc_promote(level: int, game: str = "gs") -> int:
    thresholds = {"gs": [(80, 6), (70, 5), (60, 4), (50, 3), (40, 2), (20, 1)],
                  "sr": [(80, 6), (70, 5), (60, 4), (50, 3), (40, 2), (30, 1)]}
    for max_lv, promote in thresholds.get(game, thresholds["gs"]):
        if level >= max_lv:
            return promote
    return 0


class Attr:
    def __init__(self, avatar: Any) -> None:
        self.avatar = avatar
        self._attr: dict[str, float] = {}
        self._base: dict[str, float] = {}

    def calc(self) -> dict[str, float]:
        avatar = self.avatar
        char = avatar.char
        weapon_data = avatar.weapon or {}
        lv = getattr(avatar, "level", 80)
        promote = getattr(avatar, "promote", calc_promote(lv, avatar.game))

        if avatar.game == "sr":
            return self._calc_sr(char, lv, promote, weapon_data)
        return self._calc_gs(char, lv, weapon_data)

    def _calc_sr(self, char: Any, lv: int, promote: int, weapon_data: dict[str, Any]) -> dict[str, float]:
        lv_attr = char.get_lv_attr(lv, promote) if char else {}
        char_hp = float(lv_attr.get("hp", 0))
        char_atk = float(lv_attr.get("atk", 0))
        char_def = float(lv_attr.get("def", 0))
        char_speed = float(lv_attr.get("speed", 0))
        cpct = float(lv_attr.get("cpct", 5))
        cdmg = float(lv_attr.get("cdmg", 50))
        eff_pct = 0.0
        eff_def = 0.0
        stance = 0.0
        heal = 0.0
        recharge = 100.0
        dmg_bonus = 0.0

        hp_base = char_hp
        atk_base = char_atk
        def_base = char_def
        hp_pct = 0.0
        atk_pct = 0.0
        def_pct = 0.0
        speed_pct = 0.0
        hp_plus = 0.0
        atk_plus = 0.0
        def_plus = 0.0
        speed_flat = char_speed

        avatar = self.avatar
        trees = getattr(avatar, "_trees", []) or []
        if trees and char:
            tree_data = (char.get_detail() or {}).get("tree", {})
            for tid in trees:
                tcfg = tree_data.get(str(tid)) if isinstance(tree_data, dict) else None
                if tcfg:
                    tk = tcfg.get("key", "")
                    tv = float(tcfg.get("value", 0))
                    if tk in ("atk", "hp", "def"):
                        tk = tk + "Pct"
                    hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus, \
                        cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus = \
                        _apply_sr_stat_simple(tk, tv,
                                              hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus,
                                              cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus)

        weapon_lv = int(weapon_data.get("level", 1))
        if weapon_lv > 1 and weapon_data.get("id"):
            from ..weapon import Weapon
            w = Weapon.get(str(weapon_data.get("id")), char.game if char else "sr")
            if w:
                w_attr = w.calc_attr(weapon_lv, weapon_data.get("promote", 0))
                if w_attr:
                    hp_base += float(w_attr.get("hpBase", w_attr.get("hp", 0)))
                    atk_base += float(w_attr.get("atkBase", w_attr.get("atk", 0)))
                    def_base += float(w_attr.get("defBase", w_attr.get("def", 0)))
                    for wk in w_attr:
                        if wk in ("hp", "atk", "def", "hpBase", "atkBase", "defBase"):
                            continue
                        wv = float(w_attr[wk] or 0)
                        if wv:
                            hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus, \
                                cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus = \
                                _apply_sr_stat_simple(wk, wv,
                                                      hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus,
                                                       cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus)

                    # Apply weapon passive/affix buffs (e.g. 让告别更美一些: +30% HP)
                    from ...components.meta import Meta
                    weapon_buffs = Meta.get_meta("sr", "weapon", "weaponBuffs") or {}
                    wname = weapon_data.get("name", "")
                    wbuffs = weapon_buffs.get(wname) if wname else None
                    if wbuffs and w:
                        w_detail = w.get_detail()
                        skill_tables = (w_detail or {}).get("skill", {}).get("tables", {})
                        w_affix = int(weapon_data.get("affix", 1))
                        for wb in wbuffs:
                            if wb.get("isStatic"):
                                idx = wb.get("idx", 0)
                                key = wb.get("key", "")
                                tbl = skill_tables.get(str(idx), [])
                                if tbl and 0 <= w_affix - 1 < len(tbl):
                                    val = float(tbl[w_affix - 1])
                                    hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus, \
                                        cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus = \
                                        _apply_sr_stat_simple(key, val,
                                                              hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus,
                                                              cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus)

        from ..artis.artisattr import get_data as _get_arti_data
        artis = getattr(avatar, "_artis", None)
        if artis:
            raw_data = getattr(artis, "_data", {})
            for idx_str, piece in raw_data.items():
                ad = _get_arti_data(piece, int(idx_str), game="sr")
                if not ad:
                    continue
                for src in (ad.get("main", {}), *ad.get("attrs", [])):
                    if not src:
                        continue
                    hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus, \
                        cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus = \
                        _apply_sr_stat_simple(src.get("key", ""), src.get("value", 0),
                                              hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus,
                                              cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus)

        from ..artifact import ArtifactSet
        artis_obj = getattr(avatar, "_artis", None)
        if artis_obj and hasattr(artis_obj, "sets"):
            for sname, scount in artis_obj.sets.items():
                if scount < 2:
                    continue
                for count_key in ("2", "4"):
                    if count_key == "2" and scount < 2:
                        continue
                    if count_key == "4" and scount < 4:
                        continue
                    buffs = ArtifactSet.get_artis_set_buff(sname, int(count_key), "sr")
                    for buff in buffs:
                        bk = buff.get("key", "")
                        bv = buff.get("value", 0)
                        if bk and bv:
                            hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus, \
                                cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus = \
                                _apply_sr_stat_simple(bk, bv,
                                                      hp_pct, atk_pct, def_pct, speed_pct, hp_plus, atk_plus, def_plus,
                                                      cpct, cdmg, speed_flat, eff_pct, eff_def, heal, stance, recharge, dmg_bonus)

        total_hp = hp_base * (1 + hp_pct / 100.0) + hp_plus
        total_atk = atk_base * (1 + atk_pct / 100.0) + atk_plus
        total_def = def_base * (1 + def_pct / 100.0) + def_plus
        total_speed = speed_flat * (1 + speed_pct / 100.0)

        attr: dict[str, float] = {
            "FIGHT_PROP_HP": total_hp,
            "FIGHT_PROP_ATTACK": total_atk,
            "FIGHT_PROP_DEFENSE": total_def,
            "FIGHT_PROP_BASE_HP": hp_base,
            "FIGHT_PROP_BASE_ATTACK": atk_base,
            "FIGHT_PROP_BASE_DEFENSE": def_base,
            "FIGHT_PROP_CRITICAL": cpct,
            "FIGHT_PROP_CRITICAL_HURT": cdmg,
            "FIGHT_PROP_SPEED": total_speed,
            "FIGHT_PROP_CHARGE_EFFICIENCY": recharge,
            "FIGHT_PROP_HEAL_ADD": heal,
            "FIGHT_PROP_EFFECT_HIT_RATE": eff_pct,
            "FIGHT_PROP_EFFECT_RESIST": eff_def,
            "FIGHT_PROP_STANCE": stance,
            "FIGHT_PROP_DMG_BONUS": dmg_bonus,
        }
        self._attr = attr
        self._base = {"hp": hp_base, "atk": atk_base, "def": def_base}
        return attr

    def _calc_gs(self, char: Any, lv: int, weapon_data: dict[str, Any]) -> dict[str, float]:
        detail = char.get_detail() if char else {}
        base_attr = detail.get("baseAttr", {}) or {}
        grow_attr = detail.get("growAttr", {}) or {}

        hp_base = float(base_attr.get("hp", 0))
        atk_base = float(base_attr.get("atk", 0))
        def_base = float(base_attr.get("def", 0))
        cpct = float(base_attr.get("cpct", 5))
        cdmg = float(base_attr.get("cdmg", 50))
        recharge = float(base_attr.get("recharge", 100))
        em = float(base_attr.get("em", 0))
        dmg_bonus = 0.0

        # Apply level scaling from growAttr
        grow_key = grow_attr.get("key", "")
        grow_val = grow_attr.get("value", 0)
        if grow_key and grow_val:
            grow_total = float(grow_val)
            if grow_key == "hp":
                hp_base += grow_total
            elif grow_key == "atk":
                atk_base += grow_total
            elif grow_key == "def":
                def_base += grow_total
            elif grow_key == "cpct":
                cpct += grow_total
            elif grow_key == "cdmg":
                cdmg += grow_total
            elif grow_key == "mastery":
                em += grow_total
        elif lv > 1:
            for key, grow in grow_attr.items():
                try:
                    grow_val = float(grow) * (lv - 1)
                except (ValueError, TypeError):
                    continue
                if key == "hp":
                    hp_base += grow_val
                elif key == "atk":
                    atk_base += grow_val
                elif key == "def":
                    def_base += grow_val
                elif key == "cpct":
                    cpct += grow_val
                elif key == "cdmg":
                    cdmg += grow_val

        # Apply weapon
        weapon_lv = int(weapon_data.get("level", 1))
        if weapon_lv > 1 and weapon_data.get("id"):
            from ..weapon import Weapon
            w = Weapon.get(str(weapon_data.get("id")), char.game if char else "gs")
            if w:
                w_attr = w.calc_attr(weapon_lv, weapon_data.get("promote", 0))
                if w_attr:
                    atk_base += float(w_attr.get("atkBase", w_attr.get("FIGHT_PROP_BASE_ATTACK", 0)))
                    bk = w_attr.get("bonusKey", "")
                    bv = float(w_attr.get("bonusValue", 0) or 0)
                    if bk and bv:
                        if bk == "cpct": cpct += bv
                        elif bk == "cdmg": cdmg += bv
                        elif bk == "recharge": recharge += bv
                        elif bk in ("em", "mastery"): em += bv
                        elif bk in ("atk", "hp", "def"):
                            if bk == "atk": atk_base *= (1 + bv / 100.0)
                            elif bk == "hp": hp_base *= (1 + bv / 100.0)
                            elif bk == "def": def_base *= (1 + bv / 100.0)

        # Apply artifact stats
        from ..artis.artisattr import get_data as _get_arti_data
        hp_plus = hp_pct = atk_plus = atk_pct = def_plus = def_pct = 0.0
        artis = getattr(self.avatar, "_artis", None)
        if artis:
            raw_data = getattr(artis, "_data", {})
            for idx_str, piece in raw_data.items():
                ad = _get_arti_data(piece, int(idx_str), game="gs")
                if not ad:
                    continue
                for src in (ad.get("main", {}), *ad.get("attrs", [])):
                    if not src:
                        continue
                    sk = src.get("key", "")
                    sv = float(src.get("value", 0))
                    if sk in ("hpPlus",):
                        hp_plus += sv
                    elif sk in ("hp", "hpPct"):
                        hp_pct += sv
                    elif sk in ("atkPlus",):
                        atk_plus += sv
                    elif sk in ("atk", "atkPct"):
                        atk_pct += sv
                    elif sk in ("defPlus",):
                        def_plus += sv
                    elif sk in ("def", "defPct"):
                        def_pct += sv
                    elif sk in ("cpct",):
                        cpct += sv
                    elif sk in ("cdmg",):
                        cdmg += sv
                    elif sk in ("recharge",):
                        recharge += sv
                    elif sk in ("mastery",):
                        em += sv
                    elif sk in ("heal",):
                        pass
                    elif sk in ("dmg", "phy") or Format.is_elem(sk, "gs"):
                        dmg_bonus += sv

        total_hp = hp_base * (1 + hp_pct / 100.0) + hp_plus
        total_atk = atk_base * (1 + atk_pct / 100.0) + atk_plus
        total_def = def_base * (1 + def_pct / 100.0) + def_plus

        attr: dict[str, float] = {
            "FIGHT_PROP_HP": total_hp,
            "FIGHT_PROP_ATTACK": total_atk,
            "FIGHT_PROP_DEFENSE": total_def,
            "FIGHT_PROP_BASE_HP": hp_base,
            "FIGHT_PROP_BASE_ATTACK": atk_base,
            "FIGHT_PROP_BASE_DEFENSE": def_base,
            "FIGHT_PROP_CRITICAL": cpct,
            "FIGHT_PROP_CRITICAL_HURT": cdmg,
            "FIGHT_PROP_SPEED": float(base_attr.get("speed", 0)),
            "FIGHT_PROP_CHARGE_EFFICIENCY": recharge,
            "FIGHT_PROP_ELEMENT_MASTERY": em,
            "FIGHT_PROP_DMG_BONUS": dmg_bonus,
        }
        self._attr = attr
        self._base = {"hp": hp_base, "atk": atk_base, "def": def_base}
        return attr

    def get_base(self) -> dict[str, float]:
        return self._base

    @staticmethod
    def create(avatar: Any) -> "Attr":
        return Attr(avatar)

    @staticmethod
    def calc_promote(level: int, game: str = "gs") -> int:
        return calc_promote(level, game)
