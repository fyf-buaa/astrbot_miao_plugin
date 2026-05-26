from __future__ import annotations

from typing import Any


def calc_damage(data: dict[str, Any]) -> dict[str, float]:
    atk = data.get("atk", 0)
    multiplier = data.get("skillMultiplier", 0)
    dmg_bonus = data.get("dmgBonus", 0)
    crit_rate = data.get("critRate", 0)
    crit_dmg = data.get("critDmg", 0)
    enemy_lv = data.get("enemyLv", 100)
    char_lv = data.get("charLv", 90)
    def_ignore_pct = data.get("defIgnorePct", 0.0)
    res_pen = data.get("resPen", 0.0)
    amplify = data.get("amplify", 0)
    weak_pct = data.get("weakPct", 0)
    add_atk = data.get("addAtk", 0)
    add_dmg = data.get("addDmg", 0)
    game = data.get("game", "gs")
    reaction_type = data.get("reactionType", "")
    reaction_em = data.get("reactionEM", 0)

    base_dmg = (atk + add_atk) * multiplier

    # Defense multiplier
    if game == "sr":
        def_mult = (200 + 10 * char_lv) / (200 + 10 * char_lv + (200 + 10 * enemy_lv) * (1 - def_ignore_pct / 100))
    else:
        def_mult = (char_lv + 100) / (char_lv + 100 + (enemy_lv + 100) * (1 - def_ignore_pct / 100))

    # Resistance multiplier
    if game == "sr":
        res_mult = 1 + res_pen / 100
    else:
        res_mult = 1 - (0.1 - res_pen / 100)
        if res_mult < 0:
            res_mult = res_mult / 2
        elif res_mult > 0.75:
            res_mult = 0.75

    # Damage bonus
    dmg_mult = 1 + (dmg_bonus + add_dmg) / 100

    # Amplify (reaction)
    if game == "gs" and reaction_type and reaction_em > 0:
        from .dmgmastery import reaction_bonus
        em_bonus = reaction_bonus(reaction_em).get("amplify", 0)
        base_amp = {"vaporize": 1.5, "melt": 2.0}.get(reaction_type, 1.0)
        amp_mult = base_amp * (1 + em_bonus / 100)
    else:
        amp_mult = 1 + amplify / 100

    # Weakness (additional multiplier)
    weak_mult = 1 + weak_pct / 100

    raw = base_dmg * def_mult * res_mult * dmg_mult * amp_mult * weak_mult
    avg = raw * (1 + crit_rate / 100 * crit_dmg / 100)
    crit_hit = raw * (1 + crit_dmg / 100)
    no_crit = raw

    return {
        "raw": round(raw),
        "avg": round(avg),
        "crit": round(crit_hit),
        "noCrit": round(no_crit),
        "defMult": round(def_mult, 4),
        "resMult": round(res_mult, 4),
        "dmgMult": round(dmg_mult, 4),
        "ampMult": round(amp_mult, 4),
        "reactionType": reaction_type,
    }


def basic_fn(atk_num: float, talent_type: str, char_lv: int, enemy_lv: int,
             attr: dict[str, Any], buffs_agg: dict[str, float],
             game: str = "gs", reaction_type: str = "",
             reaction_em: float = 0) -> dict[str, float]:
    cr = attr.get("critRate", attr.get("cpct", 5))
    cd = attr.get("critDmg", attr.get("cdmg", 50))

    dmg_bonus = attr.get(f"{talent_type}Dmg",
                attr.get("dmg",
                attr.get("dmgBonus", 0)))
    if talent_type == "a" and attr.get("dmgBonus", 0) == 0 and attr.get("physDmg", 0):
        dmg_bonus = attr.get("physDmg", 0)

    def_ignore = buffs_agg.get("defIgnore", 0)
    res_pen = buffs_agg.get("resPen", 0)
    add_dmg = buffs_agg.get("dmg", 0)
    multi_bonus = buffs_agg.get("multi", 0)

    multiplier = 1 + multi_bonus / 100
    effective_atk = atk_num * multiplier

    return calc_damage({
        "atk": effective_atk,
        "skillMultiplier": 1.0,
        "dmgBonus": dmg_bonus,
        "critRate": cr,
        "critDmg": cd,
        "enemyLv": enemy_lv,
        "charLv": char_lv,
        "defIgnorePct": def_ignore,
        "resPen": res_pen,
        "addDmg": add_dmg,
        "game": game,
        "reactionType": reaction_type,
        "reactionEM": reaction_em,
    })


def get_dmg_fn(ds: dict[str, Any]) -> Any:
    return lambda: calc_damage(ds)
