from __future__ import annotations

from typing import Any

from ..adapter import MiaoEvent
from ._profile_common import profile_help
from ._profile_detail import detail
from ._profile_list import delete_profile, profile_list, profile_reload, refresh_profile
from ._profile_stat import avatar_list, stat_summary, talent_stat
from ._profile_artis import artis_list
from ._profile_rank import group_rank, manage_rank, refresh_rank, reset_rank
from ._profile_utils import enemy_level
from ._profile_dmg import calc_damage_handler

# ── 16 handler functions ─────────────────────────────────────────────────────
# Each delegates to the imported helper and, if the helper returns image bytes,
# passes them back via e.reply_image().
#
# The regex pattern originally registered for each handler is preserved as a
# comment to ensure exact reproduction when re-registering.


async def profileRefresh_handler(e: MiaoEvent) -> None:
    """Handle #更新面板 — refresh profile data from Enka.
    Pattern: ^/(星铁|原神)?(全部面板更新|更新全部面板|获取游戏角色详情|更新面板|面板更新)\s*(\d{9,10})?$
    """
    result = await refresh_profile(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def profileDel_handler(e: MiaoEvent) -> None:
    """Handle #删除面板 — delete profile data.
    Pattern: ^/(星铁|原神)?(删除全部面板|删除面板|删除面板数据)\s*(\d{9,10})?$
    """
    result = await delete_profile(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def profileReload_handler(e: MiaoEvent) -> None:
    """Handle #重载面板 — reload profile data from cache.
    Pattern: ^/(星铁|原神)?(加载|重新加载|重载)面板\s*(\d{9,10})?$
    """
    result = await profile_reload(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def profileStat_handler(e: MiaoEvent) -> None:
    """Handle #练度统计 — show stat summary.
    Pattern: ^/(星铁|原神)?(面板)?练度统计\s*(\d{9,10})?$
    """
    result = await stat_summary(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def talentStat_handler(e: MiaoEvent) -> None:
    """Handle #天赋汇总 — show talent stats.
    Pattern: ^/*(我的)?(今日|今天|明日|明天|周.*)?([五四54]星)?(技能|天赋)+(汇总|统计|列表)?[ \|0-9]*$
    """
    result = await talent_stat(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def avatarList_handler(e: MiaoEvent) -> None:
    """Handle #喵喵角色 — list avatars.
    Pattern: ^/喵喵(角色|查询)[ \|0-9]*$
    """
    result = await avatar_list(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def profileList_handler(e: MiaoEvent) -> None:
    """Handle #面板列表 — list profiles.
    Pattern: ^/(星铁|原神)?(面板角色|角色面板|面板)(列表)?\s*(\d{9,10})?$
    """
    result = await profile_list(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def profileHelp_handler(e: MiaoEvent) -> None:
    """Handle #面板帮助 — show help.
    Pattern: ^/(角色|换|更换)?面[板版]帮助$
    """
    result = await profile_help(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def enemyLv_handler(e: MiaoEvent) -> None:
    """Handle #敌人等级 — set enemy level.
    Pattern: ^/(敌人|怪物)等级\s*\d{1,3}\s*$
    """
    result = await enemy_level(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def groupProfile_handler(e: MiaoEvent) -> None:
    """Handle #群内最强 — show group rank.
    Pattern: ^/(星铁|原神)?(群|群内)?(排名|排行)?(最强|最高|最高分|最牛|第一|极限)+.+
    """
    result = await group_rank(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def resetRank_handler(e: MiaoEvent) -> None:
    """Handle #重置排名 — reset rank data.
    Pattern: ^/(星铁|原神)?(重置|重设)(.*)(排名|排行)$
    """
    result = await reset_rank(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def refreshRank_handler(e: MiaoEvent) -> None:
    """Handle #刷新排名 — refresh rank data.
    Pattern: ^/(星铁|原神)?(刷新|更新|重新加载)(群内|群|全部)*(排名|排行)$
    """
    result = await refresh_rank(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def manageRank_handler(e: MiaoEvent) -> None:
    """Handle #开启/关闭排名 — manage rank toggle.
    Pattern: ^/(开启|打开|启用|关闭|禁用)(群内|群|全部)*(排名|排行)$
    """
    result = await manage_rank(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def artisList_handler(e: MiaoEvent) -> None:
    """Handle #圣遗物列表 — show artifact list.
    Pattern: ^/(星铁|原神)?(圣遗物|遗器)列表\s*(\d{9,10})?$
    """
    result = await artis_list(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def profileDetail_handler(e: MiaoEvent) -> None:
    """Handle #雷神面板 — show character detail.
    Pattern: ^/*([^/]+)\s*(详细|详情|面板|面版|圣遗物|遗器)\s*(\d{9,10})*$
    """
    result = await detail(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def damageCalc_handler(e: MiaoEvent) -> None:
    """Handle #雷神伤害 — calculate damage.
    Pattern: ^/*([^/]+)\s*(伤害|伤害\d+)\s*(\d{9,10})*$
    """
    result = await calc_damage_handler(e)
    if isinstance(result, bytes):
        e.reply_image(result)


# ── Exports ──────────────────────────────────────────────────────────────────

__all__ = [
    "profileRefresh_handler",
    "profileDel_handler",
    "profileReload_handler",
    "profileStat_handler",
    "talentStat_handler",
    "avatarList_handler",
    "profileList_handler",
    "profileHelp_handler",
    "enemyLv_handler",
    "groupProfile_handler",
    "resetRank_handler",
    "refreshRank_handler",
    "manageRank_handler",
    "artisList_handler",
    "profileDetail_handler",
    "damageCalc_handler",
]
