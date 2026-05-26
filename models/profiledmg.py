from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import Base
from .character import Character
from .dmg.dmgbuffs import get_buffs
from .dmg.dmgcalc import basic_fn
from .dmg.dmgcalcmeta import get_char_dmg_data, get_skill_multiplier
from ..tools.path import miao_path


def dmg_rule_path(name: str, game: str = "gs") -> dict | bool:
    dmg_files = [
        {"file": "calc_user", "name": "\u81ea\u5b9a\u4e49\u4f24\u5bb3"},
        {"file": "calc", "name": "\u55b5\u55b5"},
    ]
    for df in dmg_files:
        path = Path(f"{miao_path}/resources/meta-{game}/character/{name}/{df['file']}.js")
        if path.exists():
            return {"path": str(path), "createdBy": df["name"]}
    return False


def _resolve_talent_level(talent_data: dict[str, Any], skill_key: str, default: int = 1) -> int:
    if isinstance(talent_data, dict):
        entry = talent_data.get(skill_key, {})
        if isinstance(entry, dict):
            return int(entry.get("level", default))
        return int(entry) if entry else default
    return default


def _resolve_all_talent_levels(profile: Any) -> dict[str, int]:
    talent_data = getattr(profile, "talent", {}) or {}
    # SR talent keys: a, e, q, t, me, mt, xe
    keys = ["a", "e", "q", "t", "me", "mt", "xe"]
    result: dict[str, int] = {}
    for k in keys:
        entry = talent_data.get(k, {})
        if isinstance(entry, dict):
            result[k] = int(entry.get("level", 1))
        elif entry:
            result[k] = int(entry)
        else:
            result[k] = 1
    # Enhanced versions (a2 = enhanced basic, e2 = enhanced skill, etc.)
    # These use the same talent level as the base key
    for suffix in ("2",):
        for base in ("a", "e", "q", "t", "me", "mt"):
            if base in result:
                result[f"{base}{suffix}"] = result[base]
    return result


def _get_talent_multiplier(char_id: str, talent_key: str, skill_name: str,
                           talent_levels: dict[str, int], game: str) -> float:
    level = talent_levels.get(talent_key, 1)
    multiplier = get_skill_multiplier(char_id, talent_key, skill_name, level, game)
    return multiplier


def _aggregate_buffs(buffs: list[dict[str, Any]]) -> dict[str, float]:
    agg: dict[str, float] = {}
    for buf in buffs:
        vals = buf.get("_values", {})
        for k, v in vals.items():
            agg[k] = agg.get(k, 0) + v
    return agg


class ProfileDmg(Base):
    def __init__(self, profile: Any = None, game: str = "gs") -> None:
        super().__init__()
        self.profile = profile
        self.game = game
        self.char = None
        if profile and getattr(profile, "id", None):
            pid = profile.id
            pelem = getattr(profile, "elem", "") or ""
            self.char = Character.get({"id": pid, "elem": pelem, "game": game})

    def talent_data(self) -> dict[str, Any]:
        if not self.char:
            return {}
        profile = self.profile
        talent_data = getattr(profile, "talent", {}) or {}
        ret: dict[str, Any] = {"talentLevel": {}}
        for key in ("a", "e", "q", "t", "me", "mt", "xe"):
            entry = talent_data.get(key, {})
            if isinstance(entry, dict):
                ret["talentLevel"][key] = entry.get("level", 1)
            elif entry:
                ret["talentLevel"][key] = int(entry)
            else:
                ret["talentLevel"][key] = 1
        return ret

    async def calc_damage_simple(self, enemy_lv: int = 103) -> dict[str, Any] | bool:
        if not hasattr(self, "char") or not self.char or not self.profile:
            return False
        profile = self.profile
        attr = getattr(profile, "attr", None) or {}
        cr = attr.get("FIGHT_PROP_CRITICAL", attr.get("cpct", attr.get("critRate", 5)))
        cd = attr.get("FIGHT_PROP_CRITICAL_HURT", attr.get("cdmg", attr.get("critDmg", 50)))
        dmg_bonus = attr.get("FIGHT_PROP_FIRE_ADD_HURT", attr.get("dmg", attr.get("dmgBonus", 0)))
        lv = getattr(profile, "level", 90)

        # Pick best stat from atk/hp/def
        atk = attr.get("FIGHT_PROP_ATTACK", attr.get("atk", 0))
        hp = attr.get("FIGHT_PROP_HP", attr.get("hp", 0))
        defense = attr.get("FIGHT_PROP_DEFENSE", attr.get("def", 0))
        best_stat = max(atk, hp, defense)
        stat_name = "atk"
        if hp >= atk and hp >= defense:
            stat_name = "hp"
        elif defense >= atk and defense >= hp:
            stat_name = "def"

        from .dmg.dmgcalc import calc_damage
        dmg_input = {
            "atk": best_stat,
            "skillMultiplier": 2.0,
            "dmgBonus": dmg_bonus,
            "critRate": cr,
            "critDmg": cd,
            "enemyLv": enemy_lv,
            "charLv": lv,
            "game": self.game,
        }
        if self.game == "gs":
            em = attr.get("em", attr.get("mastery", attr.get("FIGHT_PROP_ELEMENT_MASTERY", 0)))
            if em > 0:
                from .dmg.dmgmastery import reaction_bonus
                em_amp = reaction_bonus(em).get("amplify", 0)
                if em_amp > 0:
                    dmg_input["amplify"] = em_amp
        return calc_damage(dmg_input)

    async def calc_damage_full(self, detail_idx: int = -1, enemy_lv: int = 103) -> list[dict[str, Any]] | bool:
        if not self.char or not self.profile:
            return False
        char_id = str(self.char.id)
        game = self.game
        dmg_data = get_char_dmg_data(char_id, game)
        if not dmg_data or not dmg_data.get("calc"):
            return {"noConfig": True}
        calc_info = dmg_data.get("calc", {})
        details = calc_info.get("details", [])
        if not details:
            return False
        if detail_idx < 0:
            detail_idx = calc_info.get("defDmgIdx", 0)
        if detail_idx >= len(details):
            detail_idx = 0

        profile = self.profile
        attr = getattr(profile, "attr", {}) or {}
        cons = getattr(profile, "cons", 0)
        lv = getattr(profile, "level", 90)
        talent_levels = _resolve_all_talent_levels(profile)

        # Determine default stat from mainAttr
        main_attr_str = calc_info.get("mainAttr", "atk,cpct,cdmg")
        default_stat = main_attr_str.split(",")[0].strip() if main_attr_str else "atk"

        # Get buffs from calc.js
        buffs_data = calc_info.get("buffs", [])
        active_buffs = get_buffs(profile, buffs_data, game)

        results = []
        for idx, detail in enumerate(details):
            # Check constellation requirement
            detail_cons = detail.get("cons", 0)
            if detail_cons and cons < detail_cons:
                continue

            # Check custom check function (simplified: check for params)
            detail_params = detail.get("params", {}) if isinstance(detail.get("params"), dict) else {}

            # Determine reaction type for GS
            reaction_type = detail_params.get("reaction", "")
            reaction_em = 0
            if game == "gs" and not reaction_type:
                elem = getattr(profile, "elem", "") or ""
                if elem in ("pyro", "hydro", "cryo"):
                    reaction_type = {"pyro": "vaporize", "hydro": "vaporize", "cryo": "melt"}.get(elem, "")

            dmg_info = detail.get("dmg", {})
            if not dmg_info:
                continue

            stat = dmg_info.get("stat", default_stat)
            talent_key = dmg_info.get("talentKey", "a")
            skill_name = dmg_info.get("skillName", "")
            skill_type = dmg_info.get("skillType", "a")
            multi_talent = dmg_info.get("multiTalent", None)
            var_talent = dmg_info.get("varTalent", {})
            var_attr = dmg_info.get("varAttr", {})

            if not skill_name and not multi_talent:
                continue

            # Aggregate buff values
            buffs_agg = _aggregate_buffs(active_buffs)

            if multi_talent:
                # Complex: multiple talent multipliers combined with multiple stats
                total_effective = 0.0
                for mt in multi_talent:
                    mt_key = mt.get("key", talent_key)
                    mt_name = mt.get("name", "")
                    if not mt_name:
                        continue
                    mt_mult = _get_talent_multiplier(char_id, mt_key, mt_name,
                                                     talent_levels, game)
                    if mt_mult == 0:
                        continue
                    # Find which stat this talent is paired with via variable mapping
                    mt_stat = stat
                    for vname, (vk, vn) in var_talent.items():
                        if vk == mt_key and vn == mt_name:
                            mapped_stat = var_attr.get(vname, stat)
                            mt_stat = mapped_stat
                            break
                    sv = attr.get(mt_stat, 0)
                    total_effective += mt_mult * sv
                effective_stat = total_effective
                if effective_stat == 0:
                    continue
                result = basic_fn(effective_stat, skill_type, lv, enemy_lv,
                                  attr, buffs_agg, game=game)
                result["stat"] = stat
                result["multiplier"] = effective_stat / (attr.get(stat, 1) or 1)
            else:
                if not skill_name:
                    continue
                multiplier = _get_talent_multiplier(char_id, talent_key, skill_name,
                                                     talent_levels, game)
                if multiplier == 0:
                    continue
                stat_val = attr.get(stat, 0)
                effective_stat = stat_val * multiplier
                # For GS, compute reaction amplify from EM
                if game == "gs" and reaction_type:
                    reaction_em = attr.get("em", attr.get("FIGHT_PROP_ELEMENT_MASTERY", 0))
                result = basic_fn(effective_stat, skill_type, lv, enemy_lv,
                                  attr, buffs_agg, game=game,
                                  reaction_type=reaction_type, reaction_em=reaction_em)
                result["multiplier"] = multiplier

            result["title"] = detail.get("title", f"\u4f24\u5bb3{idx + 1}")
            result["idx"] = idx
            result["isDefault"] = (idx == detail_idx)
            result["stat"] = stat
            results.append(result)

        return results
