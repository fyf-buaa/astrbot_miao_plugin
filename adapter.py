from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("astrbot_plugin_miao.adapter")

# Match 9-10 digit UIDs (Genshin/Star Rail: 9 digits, ZZZ: 10 digits)
# Must start with a non-zero digit.
_UID_RE = re.compile(r"\b[1-9]\d{8,9}\b")

# Game keywords to detect from message text
_GAME_KEYWORDS: dict[str, str] = {
    "星铁": "sr",
    "绝区零": "zzz",
}


def qtext(e) -> str:
    """Extract command text by stripping game keywords and UID numbers from msg."""
    msg = str(getattr(e, "msg", "") or "")
    # Strip game keywords
    for kw in _GAME_KEYWORDS:
        msg = msg.replace(kw, "")
    # Strip UID numbers
    msg = _UID_RE.sub("", msg).strip()
    return msg


class MiaoEvent:
    """Adapter wrapping AstrMessageEvent into the format expected by py_miao_plugin apps.

    Collects reply messages via reply() / reply_image() for the caller to
    yield later with get_reply_results(). Does NOT send messages directly.
    """

    def __init__(self, event, admins: set[str] | None = None) -> None:
        self._event = event
        self._admins: set[str] = admins or set()
        self._replies: list[tuple[str, Any]] = []

        # ── Map from AstrMessageEvent ──────────────────────────────
        self.msg: str = event.message_str or ""
        raw_uid = event.get_sender_id()
        self.user_id: str = str(raw_uid) if raw_uid is not None else ""
        self.sender_id: str = self.user_id
        raw_gid = event.get_group_id()
        self.group_id: str = str(raw_gid) if raw_gid is not None else ""
        if event.message_obj:
            self.self_id: str = str(event.message_obj.self_id or "")
        else:
            self.self_id: str = ""

        # ── Admin check ─────────────────────────────────────────────
        self.isMaster: bool = self.user_id in self._admins

        # ── Resolved later by resolve_uid() ──────────────────────────
        self.uid: str = ""
        self.game: str = "gs"
        self._uid_map: dict[str, Any] = {}

    # ── Reply collection (does NOT send messages) ─────────────────

    def reply(self, text: str) -> None:
        """Store a text reply for the caller to yield later."""
        self._replies.append(("plain", text))

    def reply_image(self, image_data: Any) -> None:
        """Store an image reply for the caller to yield later."""
        self._replies.append(("image", image_data))

    def get_reply_results(self) -> list[tuple[str, Any]]:
        """Return all collected replies as (type, content) tuples.

        The caller should iterate and yield appropriate event.plain_result()
        or event.image_result() calls.
        """
        return list(self._replies)

    def clear_replies(self) -> None:
        """Clear all stored replies."""
        self._replies.clear()


async def resolve_uid(e: MiaoEvent, uid_store) -> None:
    """Resolve UID and game for a MiaoEvent using uid_store.

    Sets e.uid, e.game, and e._uid_map on the event.

    uid_store must provide:
        async get_uid_map(qq: str) -> dict[str, Any]

    Optionally used if available:
        async get_default_game(qq: str) -> str
        async set_default_game(qq: str, game: str) -> None
    """
    qq = e.user_id
    if not qq:
        logger.warning("resolve_uid: empty user_id, skipping")
        return

    # 1. Fetch UID binding map from store
    uid_map: dict[str, Any] = await uid_store.get_uid_map(qq)
    e._uid_map = uid_map

    msg = e.msg or ""

    # 2. Detect game from message keywords
    has_sr = "星铁" in msg
    has_zzz = "绝区零" in msg

    if has_sr:
        e.game = "sr"
    elif has_zzz:
        e.game = "zzz"
    else:
        # Check user's default game preference
        default = ""
        if hasattr(uid_store, "get_default_game"):
            try:
                default = await uid_store.get_default_game(qq)
            except Exception:
                pass
        e.game = default or ""

    # 3. Look up UID from the binding map for the detected game
    if e.game == "gs":
        e.uid = uid_map.get("gs_main", "") or ""
        if not e.uid:
            gs_list = uid_map.get("gs_list") or []
            if gs_list:
                e.uid = gs_list[0]
    elif e.game == "sr":
        e.uid = uid_map.get("sr", "") or ""
    elif e.game == "zzz":
        e.uid = uid_map.get("zzz", "") or ""

    # 4. Fallback: extract UID directly from message text
    if not e.uid:
        uid_match = _UID_RE.search(msg)
        if uid_match:
            e.uid = uid_match.group(0)

    # 5. Persist the resolved game as user's default
    if e.uid and hasattr(uid_store, "set_default_game"):
        try:
            await uid_store.set_default_game(qq, e.game)
        except Exception:
            pass

    logger.debug(
        "resolve_uid qq=%s msg=%s game=%s uid=%s",
        qq, msg, e.game, e.uid,
    )


def require_game(e) -> bool:
    """Check if game is resolved. If not, reply with prompt. Returns True if game is set."""
    if e.game:
        return True
    e.reply("请在命令前添加游戏名，如 /原神面板 或 /星铁面板")
    return False
