"""Genshin plugin command handlers for astrbot_plugin_miao.

Migrated from ``yunzai-py/plugins/genshin/genshin.py``.

Provides handlers for:
- Genshin-specific help
- UID bind / unbind / show (with ``gs``/``sr``/``zzz`` game detection)
- Character alias set / delete / list

All data is persisted via :class:`GenshinStore` (JSON) and :class:`UIDStore`.
"""

from __future__ import annotations

import re
from typing import Any

from ..adapter import MiaoEvent, qtext
from ..genshin_store import GenshinStore
from ..genshin_render import render_uid_list
from ..genshin_model import gs_cfg
from ..uid_store import UIDStore

# ── Module-level references (set via init_genshin) ──────────────────

_uid_store: UIDStore | None = None
_genshin_store: GenshinStore | None = None


def init_genshin(uid_store: UIDStore, data_dir: str) -> None:
    """Initialise the module with shared UIDStore and data path.

    Must be called from ``main.py`` during plugin initialisation.
    """
    global _uid_store, _genshin_store
    _uid_store = uid_store
    _genshin_store = GenshinStore(data_dir, uid_store)


# ── Help ────────────────────────────────────────────────────────────


async def help_handler(e: MiaoEvent) -> None:
    """Show genshin-specific help text."""
    e.reply(
        "genshin 可用入口\n"
        "/绑定uid / /uid\n"
    )


# ── UID helpers ─────────────────────────────────────────────────────

_UID_RE = re.compile(r"\b[1-9]\d{8,9}\b")


def _detect_game(msg: str) -> str:
    """Detect game from message keywords. Returns ``"gs"``, ``"sr"``, or ``"zzz"``."""
    if "星铁" in msg:
        return "sr"
    if "绝区零" in msg:
        return "zzz"
    return "gs"


# ── UID Bind / Unbind / Show ────────────────────────────────────────


async def uid_bind_handler(e: MiaoEvent) -> None:
    """Handle ``#绑定uid`` / ``#原神绑定uid`` / ``#星铁绑定uid`` / ``#绝区零绑定uid``."""
    msg = e.msg or ""
    m = _UID_RE.search(msg)
    if not m:
        e.reply("UID 输入错误")
        return
    uid = m.group(0)
    qq = e.user_id
    if not qq:
        e.reply("无法获取用户信息")
        return

    if _uid_store is None:
        e.reply("存储服务未初始化")
        return

    game = _detect_game(msg)
    await _uid_store.set_uid(qq, game, uid)
    await _uid_store.set_default_game(qq, game)

    game_labels = {"gs": "原神", "sr": "星铁", "zzz": "绝区零"}
    e.reply(f"已绑定{game_labels.get(game, game)} UID：{uid}")


async def uid_unbind_handler(e: MiaoEvent) -> None:
    """Handle ``#删除uid <index>`` / ``#解绑uid``."""
    msg = e.msg or ""
    m = re.search(r"(\d{1,2})$", msg)
    if not m:
        e.reply("删除UID请带上序号")
        return
    if _genshin_store is None:
        e.reply("存储服务未初始化")
        return
    if not await _genshin_store.delete_uid_by_index(e.user_id, int(m.group(1))):
        e.reply("UID 序号错误")
        return
    e.reply("UID 已删除")


async def uid_show_handler(e: MiaoEvent) -> None:
    """Handle ``#uid`` / ``#原神uid`` / ``#uid1`` etc.

    With an index suffix, toggles the main UID.
    Without index, renders the full UID list as an image.
    """
    msg = e.msg or ""
    m = re.search(r"(\d{1,2})$", msg)
    if m:
        # Toggle main UID by index
        if _genshin_store is None:
            e.reply("存储服务未初始化")
            return
        if not await _genshin_store.toggle_main_uid(e.user_id, int(m.group(1))):
            e.reply("UID 序号错误")
            return
        e.reply("当前主 UID 已切换")
        return

    # Show UID list
    if _uid_store is None:
        e.reply("存储服务未初始化")
        return
    qq = e.user_id
    uid_map = await _uid_store.get_uid_map(qq)
    uids = uid_map.get("gs_list", [])
    sr_uid = uid_map.get("sr", "")
    zzz_uid = uid_map.get("zzz", "")
    main_uid = uid_map.get("gs_main", "")

    all_uids: list[dict[str, Any]] = [
        {"uid": u, "is_main": u == main_uid, "type": "原神"} for u in uids
    ]
    if sr_uid:
        all_uids.append({"uid": sr_uid, "is_main": False, "type": "星铁"})
    if zzz_uid:
        all_uids.append({"uid": zzz_uid, "is_main": False, "type": "绝区零"})

    if not all_uids:
        e.reply("暂无绑定 UID")
        return

    img_bytes = await render_uid_list({
        "uids": all_uids,
        "main_uid": main_uid,
        "qq": qq,
    })
    e.reply_image(img_bytes)


# ── Alias helpers ───────────────────────────────────────────────────

_COMMAND_PREFIX_RE = re.compile(r"^/(?:星铁)?(?:设置|配置)")
_ALIAS_SUFFIX_RE = re.compile(r"(别名|昵称).*$")
_DEL_PREFIX_RE = re.compile(r"^/(?:星铁)?删除(?:别名|昵称)")


def _extract_role_name(msg: str) -> str | None:
    """Extract the pure role name from an alias command message.

    Strips command prefixes like ``#设置`` / ``#配置`` / ``#星铁设置``
    and suffixes like ``别名/昵称...`` to isolate just the character name.
    """
    text = _COMMAND_PREFIX_RE.sub("", msg)
    text = _ALIAS_SUFFIX_RE.sub("", text).strip()
    return text or None


# ── Alias (Abbr) Commands ──────────────────────────────────────────


async def abbr_set_handler(e: MiaoEvent) -> None:
    """Handle ``#设置<角色名>别名/昵称`` / ``#配置<角色名>别名``."""
    msg = qtext(e)
    role_name = _extract_role_name(msg)
    if not role_name:
        e.reply("未识别到角色，请使用角色名+别名的方式")
        return
    role = gs_cfg.get_role(role_name)
    if not role:
        e.reply("未识别到角色，请使用角色名+别名的方式")
        return
    role_id = role["roleId"]

    # Extract alias list from text after 别名/昵称
    aliases_raw = _ALIAS_SUFFIX_RE.sub("", msg)
    aliases_raw = _COMMAND_PREFIX_RE.sub("", aliases_raw).strip()
    # Also remove leftover "设置" / "配置" if they appear mid-text
    aliases_raw = re.sub(r"^(设置|配置)", "", aliases_raw).strip()
    alias_list = [
        a for a in re.split(r"[\s,，、]+", aliases_raw) if a and len(a) <= 10
    ]
    if not alias_list:
        e.reply("请提供至少一个别名")
        return
    if _genshin_store is None:
        e.reply("存储服务未初始化")
        return
    await _genshin_store.set_aliases(e.user_id, role_id, alias_list)
    e.reply(f"已设置 {role_id} 别名：{'、'.join(alias_list)}")


async def abbr_del_handler(e: MiaoEvent) -> None:
    """Handle ``#删除别名/昵称<角色名>``."""
    msg = qtext(e)
    alias = _DEL_PREFIX_RE.sub("", msg).strip()
    if not alias:
        e.reply("请指定要删除的别名")
        return
    role = gs_cfg.get_role(alias)
    if not role:
        e.reply("未识别到角色")
        return
    role_id = role["roleId"]
    if _genshin_store is None:
        e.reply("存储服务未初始化")
        return
    if not await _genshin_store.delete_alias(e.user_id, role_id, alias):
        e.reply("别名不存在")
        return
    e.reply(f"已删除别名：{alias}")


async def abbr_list_handler(e: MiaoEvent) -> None:
    """Handle ``#<角色名>别名/昵称`` – list aliases for a character."""
    msg = qtext(e)
    # Strip trailing 别名/昵称 to get the role name
    role_name = _ALIAS_SUFFIX_RE.sub("", msg).strip().lstrip("#")
    if not role_name:
        e.reply("未识别到角色")
        return
    role = gs_cfg.get_role(role_name)
    if not role:
        e.reply("未识别到角色")
        return
    role_id = role["roleId"]
    if _genshin_store is None:
        e.reply("存储服务未初始化")
        return
    aliases = await _genshin_store.get_aliases(e.user_id, role_id)
    if not aliases:
        e.reply("暂无别名")
        return
    name = gs_cfg.role_id_to_name(role_id) or role_id
    e.reply(f"{name} 别名：\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(aliases, 1)))
