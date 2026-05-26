from __future__ import annotations

from typing import Any

from .base import Base
from ._character_model import Character
from .weapon import Weapon
from .attr.attr import Attr, calc_promote
from .artis.artis import Artis

_FIGHT_PROP_MAP: dict[str, str] = {
    "1": "hp", "2": "atk", "3": "def", "4": "hp", "5": "atk", "6": "def",
    "20": "critRate", "22": "critDmg", "23": "recharge", "26": "heal",
    "27": "healed", "28": "em", "29": "physDmg", "30": "anemoDmg",
    "31": "geoDmg", "32": "electroDmg", "33": "hydroDmg", "34": "pyroDmg",
    "35": "cryoDmg", "36": "dendroDmg",
    "40": "hpPct", "41": "atkPct", "42": "defPct",
    "44": "critRate", "45": "critDmg",
    "50": "heal", "51": "shield",
    "1000": "baseHp", "1001": "baseAtk", "1002": "baseDef",
}


class Avatar(Base):
    def __init__(self, ds: dict[str, Any], game: str = "gs") -> None:
        char = Character.get({"id": ds.get("id"), "elem": ds.get("elem", ""), "game": game})
        if not char:
            return
        self.id = char.id
        self.char = char
        self.game = char.game or game
        self._artis = Artis(self.game, True)
        self._profile = False

        self.level: int = 1
        self.cons: int = 0
        self.fetter: int = 0
        self.promote: int = 0
        self.elem: str = ""
        self._costume: int = 0
        self.talent: dict[str, Any] = {}
        self.weapon: dict[str, Any] = {}
        self._source: str = ""
        self._time: int = 0
        self._update: int = 0
        self._fight_prop_map: dict[str, float] = {}
        self.attr: dict[str, float] = {}
        self.base: dict[str, float] = {}
        self._trees: list[int] = []

        self.set_avatar(ds)

    @property
    def name(self) -> str:
        return self.char.name if self.char else ""

    @property
    def is_profile(self) -> bool:
        return self._profile

    @property
    def has_data(self) -> bool:
        return self.level > 1 or bool(self.weapon.get("name"))

    @property
    def imgs(self) -> dict[str, str]:
        return self.char.get_imgs(str(self.costume)) if self.char else {}

    @property
    def costume(self) -> int:
        c = self._costume
        if isinstance(c, list):
            c = c[0] if c else 0
        return int(c)

    @property
    def artis(self) -> Artis:
        return self._artis

    def set_avatar(self, ds: dict[str, Any], source: str = "") -> None:
        self._set_basic(ds, source)
        weapon_ds = ds.get("weapon", {})
        if weapon_ds:
            self._set_weapon(weapon_ds)
        talent_ds = ds.get("talent", {})
        if talent_ds:
            self._set_talent(talent_ds)
        artis_data = ds.get("artis", {})
        if artis_data:
            self._artis.set_artis_data(artis_data)
        trees_data = ds.get("trees")
        if trees_data is not None:
            self._trees = list(trees_data) if isinstance(trees_data, (list, tuple)) else []
        fpm = ds.get("fightPropMap", {})
        if fpm:
            self._fight_prop_map = {str(k): float(v) for k, v in fpm.items()}
        self._profile = True
        self.calc_attr()

    def calc_attr(self) -> None:
        fpm = self._fight_prop_map
        if fpm:
            def _get(key: str) -> float:
                return fpm.get(key, 0.0)
            self.attr = {
                "hp": _get("4"),
                "atk": _get("5"),
                "def": _get("6"),
                "critRate": _get("20") * 100.0 if _get("20") < 1 else _get("20"),
                "critDmg": _get("22") * 100.0 if _get("22") < 1 else _get("22"),
                "recharge": _get("23") * 100.0 if _get("23") < 1 else _get("23"),
                "em": _get("28"),
                "heal": _get("26") * 100.0 if _get("26") < 1 else _get("26"),
                "physDmg": _get("29") * 100.0 if _get("29") < 1 else _get("29"),
            }
            for elem_name, fp_key in [("anemoDmg", "30"), ("geoDmg", "31"), ("electroDmg", "32"),
                                       ("hydroDmg", "33"), ("pyroDmg", "34"), ("cryoDmg", "35"),
                                       ("dendroDmg", "36")]:
                val = _get(fp_key)
                if val:
                    self.attr[elem_name] = val * 100.0 if val < 1 else val
            self.base = {
                "hp": _get("1000") or _get("4"),
                "atk": _get("1001") or _get("5"),
                "def": _get("1002") or _get("6"),
            }
        else:
            a = Attr.create(self).calc()
            self.attr = {
                "hp": a.get("FIGHT_PROP_HP", 0),
                "atk": a.get("FIGHT_PROP_ATTACK", 0),
                "def": a.get("FIGHT_PROP_DEFENSE", 0),
                "critRate": a.get("FIGHT_PROP_CRITICAL", 5),
                "critDmg": a.get("FIGHT_PROP_CRITICAL_HURT", 50),
                "recharge": a.get("FIGHT_PROP_CHARGE_EFFICIENCY", 100),
                "em": a.get("FIGHT_PROP_ELEMENT_MASTERY", 0),
                "heal": a.get("FIGHT_PROP_HEAL_ADD", 0),
                "dmgBonus": a.get("FIGHT_PROP_DMG_BONUS", 0),
                "speed": a.get("FIGHT_PROP_SPEED", 0),
                "effPct": a.get("FIGHT_PROP_EFFECT_HIT_RATE", 0),
                "effDef": a.get("FIGHT_PROP_EFFECT_RESIST", 0),
                "stance": a.get("FIGHT_PROP_STANCE", 0),
            }
            self.base = {
                "hp": a.get("FIGHT_PROP_BASE_HP", 0),
                "atk": a.get("FIGHT_PROP_BASE_ATTACK", 0),
                "def": a.get("FIGHT_PROP_BASE_DEFENSE", 0),
            }

    def _set_basic(self, ds: dict[str, Any], source: str = "") -> None:
        import time
        now = int(time.time() * 1000)
        self.level = int(ds.get("level", ds.get("lv", self.level or 1)))
        self.cons = int(ds.get("cons", self.cons or 0))
        self.fetter = int(ds.get("fetter", self.fetter or 0))
        self._costume = int(ds.get("costume", self._costume or 0))
        elem = ds.get("elem")
        if elem:
            self.elem = elem
        elif not self.elem and self.char:
            self.elem = self.char.meta.get("elem", "")
        self.promote = max(int(ds.get("promote", self.promote or 0)), calc_promote(self.level, self.game))
        self._source = ds.get("_source", self._source) if not source else source
        self._time = int(ds.get("_time", self._time or now))
        self._update = int(ds.get("_update", self._update or now))

    def _set_weapon(self, ds: dict[str, Any]) -> None:
        weapon_id = str(ds.get("id", ""))
        weapon_name = ds.get("name", "") or weapon_id
        w = Weapon.get(weapon_name, self.game)
        if not w and weapon_id:
            w = Weapon.get(weapon_id, self.game)
        if not w:
            return
        self.weapon = {
            "id": ds.get("id", w.id),
            "name": ds.get("name", w.name),
            "level": int(ds.get("level", ds.get("lv", 1))),
            "promote": int(ds.get("promote", calc_promote(int(ds.get("level", ds.get("lv", 1))), self.game))),
            "affix": int(ds.get("affix", 1)),
            "star": w.star,
            "type": w.type,
            "abbr": w.abbr,
            "img": w.img,
        }
        if self.weapon["level"] < 20:
            self.weapon["promote"] = 0

    def _set_talent(self, ds: dict[str, Any]) -> None:
        if not self.char:
            return
        talent_cons = self.char.talent_cons
        ret: dict[str, dict[str, int]] = {}
        for key, lv in ds.items():
            if isinstance(lv, dict):
                ret[key] = {"original": int(lv.get("original", 1)), "level": int(lv.get("level", 1))}
            else:
                addon = talent_cons.get(key, 0) if self.cons >= 3 else 0
                original = int(lv)
                ret[key] = {"original": original, "addon": addon, "level": original + addon}
        self.talent = ret

    def get_detail(self, keys: str = "") -> dict[str, Any]:
        imgs = self.char.get_imgs(str(self.costume)) if self.char else {}
        from .artis.artisattr import get_data as _get_arti_attr
        arti_list: list[dict[str, Any]] = []
        raw_artis = getattr(self._artis, "_data", {})
        for idx_str in ("1", "2", "3", "4", "5", "6"):
            piece = raw_artis.get(idx_str)
            if piece:
                attr_data = _get_arti_attr(piece, int(idx_str), game=self.game)
                if attr_data:
                    arti_list.append({
                        "idx": idx_str,
                        "name": piece.get("name", ""),
                        "level": piece.get("level", 0),
                        "main": attr_data.get("main", {}),
                        "attrs": attr_data.get("attrs", []),
                    })
        detail: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "star": self.char.star if self.char else 4,
            "cons": self.cons,
            "fetter": self.fetter,
            "elem": self.elem,
            "abbr": self.char.abbr if self.char else "",
            "weapon": self.weapon,
            "talent": self.talent,
            "artisSet": self._artis.get_set_data(),
            "artis": arti_list,
            "hp": self.attr.get("hp", 0),
            "atk": self.attr.get("atk", 0),
            "def": self.attr.get("def", 0),
            "em": self.attr.get("em", 0),
            "critRate": self.attr.get("critRate", 0),
            "critDmg": self.attr.get("critDmg", 0),
            "recharge": self.attr.get("recharge", 0),
            "heal": self.attr.get("heal", 0),
            "dmgBonus": self.attr.get("dmgBonus", 0),
            "speed": self.attr.get("speed", 0),
            "effPct": self.attr.get("effPct", 0),
            "effDef": self.attr.get("effDef", 0),
            "stance": self.attr.get("stance", 0),
        }
        if self.attr.get("pyroDmg"):
            detail["dmgBonus"] = self.attr.get("pyroDmg", 0)
        elif self.attr.get("hydroDmg"):
            detail["dmgBonus"] = self.attr.get("hydroDmg", 0)
        elif self.attr.get("anemoDmg"):
            detail["dmgBonus"] = self.attr.get("anemoDmg", 0)
        elif self.attr.get("electroDmg"):
            detail["dmgBonus"] = self.attr.get("electroDmg", 0)
        elif self.attr.get("cryoDmg"):
            detail["dmgBonus"] = self.attr.get("cryoDmg", 0)
        elif self.attr.get("geoDmg"):
            detail["dmgBonus"] = self.attr.get("geoDmg", 0)
        elif self.attr.get("dendroDmg"):
            detail["dmgBonus"] = self.attr.get("dendroDmg", 0)
        elif self.attr.get("physDmg"):
            detail["dmgBonus"] = self.attr.get("physDmg", 0)
        detail.update(imgs)
        return detail

    @staticmethod
    def create(ds: dict[str, Any], game: str = "gs") -> "Avatar | bool":
        avatar = Avatar(ds, game)
        if not avatar or not avatar.char:
            return False
        return avatar
