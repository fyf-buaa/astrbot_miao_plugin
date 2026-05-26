from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger, AstrBotConfig

from .adapter import MiaoEvent, resolve_uid
from .uid_store import UIDStore
from .components.cfg import Cfg

# ── App handler imports ───────────────────────────────────────────────

from .apps.help import help_handler, version_handler
from .apps.admin import update_res_handler, sys_cfg_handler
from .apps.character import (
    character_handler,
    wife_handler,
    CHARACTER_PATTERN,
    WIFE_PATTERN,
)
from .apps.wiki import (
    wiki_handler,
    charWiki_handler,
    calendar_handler,
    todayMaterial_handler,
    charTalent_handler,
    charMaterial_handler,
    WIKI_PATTERN,
    CHAR_WIKI_PATTERN,
    CALENDAR_PATTERN,
    TODAY_MATERIAL_PATTERN,
    CHAR_TALENT_PATTERN,
    CHAR_MATERIAL_PATTERN,
)
from .apps.profile import (
    profileRefresh_handler,
    profileDel_handler,
    profileReload_handler,
    profileStat_handler,
    talentStat_handler,
    avatarList_handler,
    profileList_handler,
    profileHelp_handler,
    enemyLv_handler,
    groupProfile_handler,
    resetRank_handler,
    refreshRank_handler,
    manageRank_handler,
    artisList_handler,
    profileDetail_handler,
    damageCalc_handler,
)

# ── Regex dispatch table (#-prefixed commands) ─────────────────────
# Ordered most-specific-first to avoid false matches.

_REGEX_DISPATCH: list[tuple[str, Any]] = [
    # -- Exact #喵喵 patterns --
    (CHARACTER_PATTERN, character_handler),     # ^#喵喵角色卡片$
    (WIKI_PATTERN, wiki_handler),               # ^#喵喵WIKI$
    (r"^#喵喵(角色|查询)[ \|0-9]*$", avatarList_handler),
    # -- Admin commands --
    (r"^#喵喵(强制)?(更新图像|图像更新|更新资源)$", update_res_handler),
    (r"^#喵喵设置\s*(.*?)\s*(.*)$", sys_cfg_handler),
    # -- Calendar --
    (CALENDAR_PATTERN, calendar_handler),
    # -- Wife / husband --
    (WIFE_PATTERN, wife_handler),
    # -- Profile help --
    (r"^#(角色|换|更换)?面[板版]帮助$", profileHelp_handler),
    # -- Enemy level --
    (r"^#(敌人|怪物)等级\s*\d{1,3}\s*$", enemyLv_handler),
    # -- Profile commands with optional game prefix --
    (r"^#(星铁|原神)?(全部面板更新|更新全部面板|获取游戏角色详情|更新面板|面板更新)\s*(\d{9,10})?$", profileRefresh_handler),
    (r"^#(星铁|原神)?(删除全部面板|删除面板|删除面板数据)\s*(\d{9,10})?$", profileDel_handler),
    (r"^#(星铁|原神)?(加载|重新加载|重载)面板\s*(\d{9,10})?$", profileReload_handler),
    (r"^#(星铁|原神)?(面板)?练度统计\s*(\d{9,10})?$", profileStat_handler),
    (r"^#(星铁|原神)?(面板角色|角色面板|面板)(列表)?\s*(\d{9,10})?$", profileList_handler),
    (r"^#(星铁|原神)?(圣遗物|遗器)列表\s*(\d{9,10})?$", artisList_handler),
    # -- Rank management --
    (r"^#(开启|打开|启用|关闭|禁用)(群内|群|全部)*(排名|排行)$", manageRank_handler),
    (r"^#(星铁|原神)?(重置|重设)(.*)(排名|排行)$", resetRank_handler),
    (r"^#(星铁|原神)?(刷新|更新|重新加载)(群内|群|全部)*(排名|排行)$", refreshRank_handler),
    (r"^#(星铁|原神)?(群|群内)?(排名|排行)?(最强|最高|最高分|最牛|第一|极限)+.+", groupProfile_handler),
    # -- Wiki fuzzy commands --
    (CHAR_WIKI_PATTERN, charWiki_handler),         # ^#(.+)(WIKI|wiki|资料|百科)$
    (CHAR_TALENT_PATTERN, charTalent_handler),     # ^#(.+)(天赋|技能)(表|数据)?$
    (CHAR_MATERIAL_PATTERN, charMaterial_handler), # ^#(.+)(材料|突破)$
    (TODAY_MATERIAL_PATTERN, todayMaterial_handler),
    (r"^#*(我的)?(今日|今天|明日|明天|周.*)?([五四54]星)?(技能|天赋)+(汇总|统计|列表)?[ \|0-9]*$", talentStat_handler),
    # -- Broadest profile matchers (catch-all) --
    (r"^#*([^#]+)\s*(详细|详情|面板|面版|圣遗物|遗器)\s*(\d{9,10})*$", profileDetail_handler),
    (r"^#*([^#]+)\s*(伤害|伤害\d+)\s*(\d{9,10})*$", damageCalc_handler),
]


class AstrBotMiaoPlugin(Star):
    """Main plugin entry point for astrbot_plugin_miao.

    Registers 28+ commands via AstrBot's @filter decorator system.
    Simple commands use @filter.command; complex / #-prefixed commands
    are dispatched via a single regex-based event listener.
    """

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)

        # Initialise persistent UID binding store
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path
        data_path = str(Path(get_astrbot_data_path()) / "plugin_data" / "miao")
        Path(data_path).mkdir(parents=True, exist_ok=True)
        self._uid_store = UIDStore(data_path)

        # Parse admin QQ set from AstrBot config
        raw_admins: list[Any] = config.get("admin_qq", []) or []
        self._admins: set[str] = {str(a).strip() for a in raw_admins if a}

        # Initialise static configuration manager
        Cfg.init_config(config)

        logger.info(
            "astrbot_plugin_miao loaded | admins=%s data_dir=%s",
            self._admins, data_path,
        )

    # ── Internal helper ─────────────────────────────────────────────

    async def _run_handler(
        self, event: AstrMessageEvent, handler: Any,
    ):
        """Common handler flow: wrap → resolve → dispatch → yield replies."""
        import tempfile
        from .tools.path import data_path

        e = MiaoEvent(event, admins=self._admins)
        await resolve_uid(e, self._uid_store)
        await handler(e)

        # Ensure tmp dir for temp images
        tmp_dir = data_path / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        for rtype, content in e.get_reply_results():
            if rtype == "plain":
                yield event.plain_result(str(content))
            elif rtype == "image":
                # image_result() expects a file path, not bytes
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False, dir=str(tmp_dir)
                ) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                yield event.image_result(tmp_path)

    # ═══════════════════════════════════════════════════════════════
    #  Literal @filter.command handlers  (5)
    # ═══════════════════════════════════════════════════════════════

    @filter.command("help", alias={"帮助", "菜单", "命令", "说明", "功能", "指令", "使用说明"})
    async def help_cmd(self, event: AstrMessageEvent) -> Any:
        """帮助/菜单"""
        async for result in self._run_handler(event, help_handler):
            yield result

    @filter.command("version", alias={"版本", "喵喵版本"})
    async def version_cmd(self, event: AstrMessageEvent) -> Any:
        """版本信息"""
        async for result in self._run_handler(event, version_handler):
            yield result

    @filter.command("喵喵角色卡片")
    async def character_cmd(self, event: AstrMessageEvent) -> Any:
        """角色卡片查询"""
        async for result in self._run_handler(event, character_handler):
            yield result

    @filter.command("喵喵WIKI")
    async def wiki_cmd(self, event: AstrMessageEvent) -> Any:
        """WIKI 查询"""
        async for result in self._run_handler(event, wiki_handler):
            yield result

    @filter.command("面板帮助")
    async def profile_help_cmd(self, event: AstrMessageEvent) -> Any:
        """面板帮助"""
        async for result in self._run_handler(event, profileHelp_handler):
            yield result

    # ═══════════════════════════════════════════════════════════════
    #  Regex event listener  (dispatches all #-prefixed commands)
    # ═══════════════════════════════════════════════════════════════

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent) -> Any:
        """Catch-all regex dispatcher for #-prefixed commands."""
        msg: str = event.message_str or ""
        for pattern, handler in _REGEX_DISPATCH:
            if re.match(pattern, msg):
                async for result in self._run_handler(event, handler):
                    yield result
                return  # first match wins

    # ═══════════════════════════════════════════════════════════════
    #  Lifecycle
    # ═══════════════════════════════════════════════════════════════

    async def terminate(self) -> None:
        """Clean up resources when plugin is unloaded."""
        logger.info("astrbot_plugin_miao terminated.")
