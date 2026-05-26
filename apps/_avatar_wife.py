from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from ..components.meta import Meta
from ..models.player import Player
from ..tools.path import miao_path

_RELATION_MAP: list[dict[str, Any]] = [
    {"key": "wife",     "keywords": ["老婆", "媳妇", "妻子", "娘子", "宝贝"],            "type": 0},
    {"key": "husband",  "keywords": ["老公", "丈夫", "夫君", "郎君", "死鬼"],            "type": 1},
    {"key": "gf",       "keywords": ["女朋友", "女友", "女神", "女王", "女票"],          "type": 0},
    {"key": "bf",       "keywords": ["男朋友", "男友", "男神", "男票"],                  "type": 1},
    {"key": "daughter", "keywords": ["女儿", "闺女", "小宝贝"],                          "type": 2},
    {"key": "son",      "keywords": ["儿子", "犬子"],                                   "type": 3},
]

_ALL_KEYWORDS = [kw for rel in _RELATION_MAP for kw in rel["keywords"]]

_WIFE_STORE_FILE = Path(f"{miao_path}/data/wife_store.json")


def _get_wife_store() -> dict[str, dict[str, list[str]]]:
    if _WIFE_STORE_FILE.exists():
        try:
            return json.loads(_WIFE_STORE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_wife_store(store: dict[str, dict[str, list[str]]]) -> None:
    _WIFE_STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _WIFE_STORE_FILE.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_user_wife_list(user_id: str, key: str) -> list[str]:
    store = _get_wife_store()
    return store.get(user_id, {}).get(key, [])


def _set_user_wife_list(user_id: str, key: str, names: list[str]) -> None:
    store = _get_wife_store()
    if user_id not in store:
        store[user_id] = {}
    store[user_id][key] = names
    _save_wife_store(store)


def _build_wife_regex() -> str:
    return rf"^/\s*({'|'.join(_ALL_KEYWORDS)})\s*(设置|选择|指定|添加|列表|查询|是|是谁|照片|相片|图片|写真|图像)?\s*([^\d]*)\s*(\d*)$"


def _get_avatars_by_type(player: Any, wtype: int | None = None) -> list[Any]:
    chars: list[Any] = []
    def _cb(avatar, aid):
        if wtype is None or avatar.char.check_wife_type(wtype):
            chars.append(avatar)
            return
        chars.append(avatar)
    player.for_each_avatar(_cb)
    if wtype is not None:
        chars = [a for a in chars if a.char.check_wife_type(wtype)]
    chars.sort(key=lambda a: (-a.level, -getattr(a, "fetter", 0)))
    return chars


async def wife_render(e: Any) -> Any:
    import re
    msg = str(getattr(e, "msg", "")).strip()
    user_id = str(getattr(e, "user_id", ""))
    uid = str(getattr(e, "uid", ""))

    m = re.match(_build_wife_regex(), msg)
    if not m:
        e.reply("格式错误，请使用 #老婆/设置/列表 等命令"); return

    target_keyword = m.group(1)
    action = (m.group(2) or "卡片").strip()
    action_param = (m.group(3) or "").strip()

    target_cfg = None
    for rel in _RELATION_MAP:
        if target_keyword in rel["keywords"]:
            target_cfg = rel
            break
    if not target_cfg:
        e.reply("未识别的称呼"); return

    key = target_cfg["key"]
    wtype = target_cfg["type"]

    if action in ("设置", "选择", "挑选", "指定", "添加"):
        if not action_param:
            e.reply(f"请指定角色名，如 #{target_keyword}设置甘雨"); return
        splitted = [x.strip() for x in action_param.replace("，", ",").split(",")]
        splitted = [s for s in splitted if s]

        from ..models.character import Character
        resolved: list[str] = []
        for name in splitted:
            if name in ("全部", "任意", "随机", "全都要"):
                resolved = ["随机"]
                break
            char = Character.get(name)
            if char and char.check_wife_type(wtype):
                resolved.append(char.name)
        if resolved:
            existing = _get_user_wife_list(user_id, key)
            updated = existing + [n for n in resolved if n not in existing]
            if resolved == ["随机"]:
                updated = ["随机"]
            _set_user_wife_list(user_id, key, updated)
            e.reply(f"已设置{target_keyword}列表：{'、'.join(resolved) if resolved != ['随机'] else '随机'}")
            return
        e.reply(f"未找到符合条件的角色"); return

    if action in ("列表", "是", "是谁"):
        names = _get_user_wife_list(user_id, key)
        if not names:
            e.reply(f"尚未设置{target_keyword}"); return
        e.reply(f"你的{target_keyword}：{'、'.join(names)}")
        return

    if action in ("照片", "相片", "图片", "写真", "图像"):
        render_type = "photo"

    if action in ("卡片", "照片", "相片", "图片", "写真", "图像"):
        names = _get_user_wife_list(user_id, key)
        if not names:
            if not uid:
                e.reply(f"请先绑定 UID 或使用 #老婆设置[名字]"); return
            player = Player.create(uid, "gs")
            avatars = _get_avatars_by_type(player, wtype)
            if not avatars:
                e.reply(f"没有符合条件的角色"); return
            chosen = random.choice(avatars)
            from ._character_card import _render_card
            return await _render_card(e, chosen, uid, "gs")
        else:
            if names == ["随机"]:
                if uid:
                    player = Player.create(uid, "gs")
                    avatars = _get_avatars_by_type(player, wtype)
                    if avatars:
                        chosen = random.choice(avatars)
                        from ._character_card import _render_card
                        return await _render_card(e, chosen, uid, "gs")
                from ..models.character import Character
                all_released = []
                for _id in Meta.get_ids("gs", "char"):
                    char_data = Meta.get_data("gs", "char", _id)
                    if char_data and char_data.get("star", 0) in (4, 5):
                        c = Character.get(_id)
                        if c and c.check_wife_type(wtype) and c.is_release:
                            all_released.append(c)
                if all_released:
                    chosen = random.choice(all_released)
                    from ._character_card import _render_card
                    return await _render_card(e, chosen, uid, "gs")
                e.reply(f"没有符合条件的角色"); return
            else:
                chosen_name = random.choice(names)
                from ..models.character import Character
                char = Character.get(chosen_name)
                if char:
                    player = Player.create(uid, "gs") if uid else None
                    avatar = player.get_avatar(char.id) if player and hasattr(player, "get_avatar") else None
                    from ._character_card import _render_card
                    return await _render_card(e, avatar or char, uid, "gs")
                e.reply(f"角色 {chosen_name} 未找到"); return

    e.reply(f"未知操作"); return
