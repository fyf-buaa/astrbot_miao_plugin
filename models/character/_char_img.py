from __future__ import annotations

from typing import Any


def get_imgs(name: str, costume: str = "", elem: str = "",
             weapon_type: str = "", talent_cons: dict = None) -> dict[str, str]:
    base = f"meta-gs/character/{name}/"
    imgs = f"{base}imgs/"
    return {
        "face": f"{imgs}face.webp",
        "side": f"{imgs}side.webp",
        "gacha": f"{imgs}gacha.webp",
        "banner": f"{base}banner.webp",
        "icon": f"{base}icon.webp",
        "qFace": f"{imgs}face-q.webp",
        "splash": f"{imgs}splash.webp",
    }


def get_imgs_sr(name: str, talent_cons: dict = None) -> dict[str, str]:
    base = f"meta-sr/character/{name}/"
    imgs = f"{base}imgs/"
    return {
        "face": f"{imgs}face.webp",
        "side": f"{imgs}side.webp",
        "gacha": f"{imgs}gacha.webp",
        "banner": f"meta-sr/character/common/imgs/banner.webp",
        "splash": f"{imgs}splash.webp",
    }


def get_card_img(name: str | list, se: bool = False, default: bool = True) -> str:
    if isinstance(name, list):
        name = name[0]
    return f"character-img/{name}.png"
