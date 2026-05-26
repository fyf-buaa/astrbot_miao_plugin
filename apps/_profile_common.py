from __future__ import annotations

from typing import Any

from ..components.common import render


async def profile_help(e: Any) -> Any:
    return await render("help/index", {
        "helpCfg": {"title": "面板帮助", "subTitle": "Miao-Plugin 面板系统"},
        "helpGroup": [
            {
                "group": "面板查询",
                "list": [
                    {"icon": 66, "title": "#雷神面板", "desc": "查看角色详细面板"},
                    {"icon": 63, "title": "#面板列表", "desc": "查看已获取面板的角色列表"},
                    {"icon": 65, "title": "#圣遗物列表", "desc": "查看圣遗物列表/评分"},
                    {"icon": 79, "title": "#面板帮助", "desc": "面板替换及其他帮助"},
                ],
            },
            {
                "group": "面板管理",
                "list": [
                    {"icon": 63, "title": "#更新面板", "desc": "从 Enka 获取最新面板数据"},
                    {"icon": 63, "title": "#删除面板", "desc": "删除指定面板数据"},
                ],
            },
        ],
        "colCount": 2,
        "style": "",
        "element": "default",
    }, e=e, scale=1.2)
