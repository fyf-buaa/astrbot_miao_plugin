from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

from ..components.cfg import Cfg
from ..tools.path import root_path

logger = logging.getLogger(__name__)

_DB_PATH = Path(f"{root_path}/data/miao_rank.db")


def _get_db() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _init_db() -> None:
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS miao_rank (
            group_id INTEGER NOT NULL,
            char_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            uid TEXT NOT NULL,
            score REAL NOT NULL,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY (group_id, char_id, type, uid)
        );
        CREATE TABLE IF NOT EXISTS miao_rank_uid_info (
            uid TEXT PRIMARY KEY,
            qq TEXT DEFAULT '',
            uid_type TEXT DEFAULT 'bind',
            total_count INTEGER DEFAULT 0,
            basic_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS miao_rank_group_cfg (
            group_id INTEGER PRIMARY KEY,
            status INTEGER DEFAULT 0,
            timestamp INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_miao_rank_query ON miao_rank(group_id, char_id, type, score DESC);
        CREATE INDEX IF NOT EXISTS idx_miao_rank_group ON miao_rank(group_id, type, score DESC);
    """)
    conn.commit()
    conn.close()


_init_db()


class ProfileRank:
    def __init__(self, data: dict[str, Any]) -> None:
        self.group_id = int(data.get("groupId", data.get("group_id", 0)))
        self.qq = data.get("qq", "")
        self.uid = str(data.get("uid", ""))
        self.allow_rank = False

    @staticmethod
    async def create(data: dict[str, Any]) -> "ProfileRank":
        rank = ProfileRank(data)
        if rank.group_id and rank.uid:
            rank.allow_rank = await ProfileRank.check_rank_limit(rank.uid)
        return rank

    @staticmethod
    def _char_id_for_key(char_id: int, game: str = "gs") -> int:
        trailblazer_map = {
            8002: 8001, 8004: 8003, 8006: 8005, 8008: 8007,
            8010: 8009, 8012: 8011, 8014: 8013, 8016: 8015, 8018: 8017,
        }
        return trailblazer_map.get(char_id, char_id)

    @staticmethod
    def add_score(group_id: int, char_id: int, typ: str, uid: str, score: float) -> None:
        conn = _get_db()
        conn.execute(
            "INSERT OR REPLACE INTO miao_rank (group_id, char_id, type, uid, score, updated_at) VALUES (?,?,?,?,?,?)",
            (group_id, char_id, typ, uid, score, int(time.time())),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_rank(group_id: int, char_id: int, typ: str, uid: str) -> int | None:
        conn = _get_db()
        cursor = conn.execute(
            "SELECT COUNT(*) as r FROM miao_rank WHERE group_id=? AND char_id=? AND type=? AND score > (SELECT COALESCE(score,0) FROM miao_rank WHERE group_id=? AND char_id=? AND type=? AND uid=?)",
            (group_id, char_id, typ, group_id, char_id, typ, uid),
        )
        row = cursor.fetchone()
        conn.close()
        if row and row["r"] is not None:
            return row["r"] + 1
        return None

    @staticmethod
    def get_top_n(group_id: int, char_id: int, typ: str, n: int = 15) -> list[dict[str, Any]]:
        conn = _get_db()
        cursor = conn.execute(
            "SELECT uid, score FROM miao_rank WHERE group_id=? AND char_id=? AND type=? ORDER BY score DESC LIMIT ?",
            (group_id, char_id, typ, n),
        )
        rows = [{"uid": r["uid"], "score": r["score"]} for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_top_per_char(group_id: int, typ: str, game: str = "gs") -> list[dict[str, Any]]:
        conn = _get_db()
        cursor = conn.execute(
            "SELECT char_id, uid, MAX(score) as score FROM miao_rank WHERE group_id=? AND type=? GROUP BY char_id ORDER BY score DESC",
            (group_id, typ),
        )
        rows = [{"charId": r["char_id"], "uid": r["uid"], "score": r["score"]} for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def remove_uid(group_id: int, char_id: int, typ: str, uid: str) -> None:
        conn = _get_db()
        conn.execute(
            "DELETE FROM miao_rank WHERE group_id=? AND char_id=? AND type=? AND uid=?",
            (group_id, char_id, typ, uid),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def reset_group(group_id: int, char_id: int = 0, game: str = "gs") -> None:
        conn = _get_db()
        if char_id:
            cid = ProfileRank._char_id_for_key(char_id, game)
            conn.execute("DELETE FROM miao_rank WHERE group_id=? AND char_id=?", (group_id, cid))
        else:
            conn.execute("DELETE FROM miao_rank WHERE group_id=?", (group_id,))
            conn.execute("DELETE FROM miao_rank_group_cfg WHERE group_id=?", (group_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def set_uid_info(uid: str, qq: str = "", uid_type: str = "bind",
                     total_count: int = 0, basic_count: int = 0) -> None:
        conn = _get_db()
        conn.execute(
            "INSERT OR REPLACE INTO miao_rank_uid_info (uid, qq, uid_type, total_count, basic_count) VALUES (?,?,?,?,?)",
            (uid, qq, uid_type, total_count, basic_count),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_uid_info(uid: str) -> dict[str, Any]:
        conn = _get_db()
        cursor = conn.execute("SELECT * FROM miao_rank_uid_info WHERE uid=?", (uid,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return {}

    @staticmethod
    def del_uid_info(uid: str) -> None:
        conn = _get_db()
        conn.execute("DELETE FROM miao_rank_uid_info WHERE uid=?", (uid,))
        conn.execute("DELETE FROM miao_rank WHERE uid=?", (uid,))
        conn.commit()
        conn.close()

    @staticmethod
    def set_group_cfg(group_id: int, status: int = 0) -> dict[str, Any]:
        conn = _get_db()
        now = int(time.time())
        conn.execute(
            "INSERT OR REPLACE INTO miao_rank_group_cfg (group_id, status, timestamp) VALUES (?,?,?)",
            (group_id, status, now),
        )
        conn.commit()
        cursor = conn.execute("SELECT * FROM miao_rank_group_cfg WHERE group_id=?", (group_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {"group_id": group_id, "status": status, "timestamp": now}

    @staticmethod
    def get_group_cfg(group_id: int) -> dict[str, Any]:
        conn = _get_db()
        cursor = conn.execute("SELECT * FROM miao_rank_group_cfg WHERE group_id=?", (group_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            cfg = dict(row)
        else:
            cfg = ProfileRank.set_group_cfg(group_id, 0)
        from datetime import datetime
        cfg["time"] = datetime.fromtimestamp(cfg.get("timestamp", 0)).strftime("%m-%d %H:%M")
        cfg["number"] = Cfg.get("rankNumber", 15)
        cfg["limitTxt"] = {1: "无限制", 2: "绑定有CK的用户", 3: "绑定CK，或列表有16个角色数据",
                           4: "绑定CK，或列表有安柏&凯亚&丽莎的数据",
                           5: "绑定CK，或列表有16个角色数据且包含安柏&凯亚&丽莎"}.get(
            int(Cfg.get("groupRankLimit", 1)), "无限制")
        return cfg

    @staticmethod
    async def check_rank_limit(uid: str) -> bool:
        if not uid or not uid.isdigit() or int(uid) < 100000006:
            return False
        limit = int(Cfg.get("groupRankLimit", 1))
        if limit == 1:
            return True
        info = ProfileRank.get_uid_info(uid)
        if info.get("uid_type") == "ck":
            return True
        if limit == 2:
            return False
        if limit in (3, 5) and info.get("total_count", 0) < 16:
            return False
        if limit in (4, 5) and info.get("basic_count", 0) < 3:
            return False
        return True

    @staticmethod
    def get_all_uids_with_qq() -> dict[str, dict[str, Any]]:
        conn = _get_db()
        cursor = conn.execute("SELECT uid, qq, uid_type FROM miao_rank_uid_info")
        result: dict[str, dict[str, Any]] = {}
        for r in cursor.fetchall():
            result[r["uid"]] = {"uid": r["uid"], "qq": r["qq"], "type": r["uid_type"]}
        conn.close()
        return result

    def key(self, char_id: int, typ: str) -> tuple[int, int, str]:
        return (self.group_id, self._char_id_for_key(char_id), typ)

    async def get_rank_data(self, profile: Any, force: bool = False) -> dict[str, Any]:
        if not profile or not self.group_id or not self.allow_rank:
            return {}
        ret: dict[str, Any] = {}
        for typ in ("mark", "dmg", "crit", "valid"):
            gid, cid, _ = self.key(profile.id, typ)
            score = None
            rank = self.get_rank(gid, cid, typ, self.uid)
            if rank is None or force:
                score = await self._get_type_value(profile, typ)
                if score is not None:
                    self.add_score(gid, cid, typ, self.uid, score)
                rank = self.get_rank(gid, cid, typ, self.uid) or 99
            if typ in ("mark", "dmg"):
                ret[typ] = {"rank": (rank or 99)}
                if score is not None:
                    ret[typ]["value"] = score
                if not ret.get("rank") or ret["rank"] >= ret[typ]["rank"]:
                    ret["rank"] = ret[typ]["rank"]
                    ret["rankType"] = typ
        return ret

    async def _get_type_value(self, profile: Any, typ: str) -> float | None:
        if typ == "mark":
            mark = self._get_artis_mark(profile)
            if mark and mark.get("_mark"):
                return mark["_mark"]
        elif typ == "crit":
            mark = self._get_artis_mark(profile)
            if mark and mark.get("_crit"):
                return mark["_crit"]
        elif typ == "valid":
            mark = self._get_artis_mark(profile)
            if mark and mark.get("_valid"):
                return mark["_valid"]
        elif typ == "dmg":
            dmg = await self._calc_dmg(profile)
            if dmg and dmg.get("avg"):
                return dmg["avg"]
        return None

    def _get_artis_mark(self, profile: Any) -> dict[str, Any] | None:
        try:
            from .artis.artismark import get_mark_detail
        except ImportError:
            return None
        try:
            return get_mark_detail(profile, False)
        except Exception:
            logger.debug("_get_artis_mark failed", exc_info=True)
            return None

    async def _calc_dmg(self, profile: Any) -> dict[str, Any] | None:
        try:
            from .profiledmg import ProfileDmg
        except ImportError:
            return None
        try:
            p = ProfileDmg(profile, profile.game)
            return await p.calc_damage_simple()
        except Exception:
            logger.debug("_calc_dmg failed", exc_info=True)
            return None
