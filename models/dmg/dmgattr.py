from __future__ import annotations

from typing import Any

from ..attr.attrdata import AttrData

_FIGHT_PROP_TO_ATTR: dict[str, str] = {
    "FIGHT_PROP_HP": "hp",
    "FIGHT_PROP_ATTACK": "atk",
    "FIGHT_PROP_DEFENSE": "def",
    "FIGHT_PROP_HP_PERCENT": "hpPct",
    "FIGHT_PROP_ATTACK_PERCENT": "atkPct",
    "FIGHT_PROP_DEFENSE_PERCENT": "defPct",
    "FIGHT_PROP_CRITICAL": "cpct",
    "FIGHT_PROP_CRITICAL_HURT": "cdmg",
    "FIGHT_PROP_CHARGE_EFFICIENCY": "recharge",
    "FIGHT_PROP_HEAL_ADD": "heal",
    "FIGHT_PROP_ELEMENT_MASTERY": "mastery",
    "FIGHT_PROP_PHYSICAL_ADD_HURT": "phy",
    "FIGHT_PROP_FIRE_ADD_HURT": "dmg",
    "FIGHT_PROP_ELEC_ADD_HURT": "dmg",
    "FIGHT_PROP_WATER_ADD_HURT": "dmg",
    "FIGHT_PROP_GRASS_ADD_HURT": "dmg",
    "FIGHT_PROP_WIND_ADD_HURT": "dmg",
    "FIGHT_PROP_ROCK_ADD_HURT": "dmg",
    "FIGHT_PROP_ICE_ADD_HURT": "dmg",
}


def get_attr(data: dict[str, Any]) -> AttrData:
    char = data.get("char")
    attr = data.get("attr", {})
    ad = AttrData.create(char, attr)
    return ad


def calc_attr(data: dict[str, Any]) -> dict[str, Any]:
    ad = get_attr(data)
    attr_dict = ad.get_attr()
    return {"attr": attr_dict, "msg": ""}
