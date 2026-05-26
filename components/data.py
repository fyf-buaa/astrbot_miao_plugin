from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Awaitable, Callable

from ..tools.path import get_root, miao_path

logger = logging.getLogger(__name__)


class Data:
    @staticmethod
    def create_dir(path: str, root: str = "", include_file: bool = False) -> None:
        root = get_root(root)
        parts = path.split("/")
        last = len(parts) - 1
        current = Path(root)
        for i, name in enumerate(parts):
            name = name.strip()
            if not name:
                continue
            if include_file and i == last:
                continue
            current = current / name
            current.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def read_json(file: str, root: str = "") -> dict[str, Any]:
        root = get_root(root)
        p = Path(root) / file
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    @staticmethod
    def write_json(cfg: str | dict, data: Any = None, root: str = "", space: int = 2) -> None:
        if isinstance(cfg, str) and data is not None:
            cfg = {"name": cfg, "data": data, "space": space, "root": root}
        assert isinstance(cfg, dict)
        c: dict = cfg
        name = c.get("path", "") + "/" + c["name"] if c.get("path") else c["name"]
        Data.create_dir(name, c.get("root", ""), True)
        root = get_root(c.get("root", ""))
        d = c["data"]
        if isinstance(d, dict):
            d.pop("_res", None)
        text = json.dumps(d, ensure_ascii=False, indent=c.get("space", 2))
        (Path(root) / name).write_text(text, encoding="utf-8")

    @staticmethod
    def del_file(file: str, root: str = "") -> bool:
        root = get_root(root)
        p = Path(root) / file
        if p.exists():
            try:
                p.unlink()
                return True
            except OSError:
                pass
        return False

    @staticmethod
    async def import_module(file: str, root: str = "") -> dict[str, Any]:
        root = get_root(root)
        if not file.endswith(".js") and not file.endswith(".py"):
            file = file + ".js"
        p = Path(root) / file
        if p.exists():
            try:
                text = p.read_text(encoding="utf-8")
                ns: dict[str, Any] = {}
                exec(text, ns)
                return ns
            except (OSError, SyntaxError):
                pass
        return {}

    @staticmethod
    async def import_default(file: str, root: str = "") -> dict[str, Any]:
        ret = await Data.import_module(file, root)
        return ret.get("default", {})

    @staticmethod
    async def import_cfg(key: str) -> dict[str, dict[str, Any]]:
        sys_cfg = await Data.import_module(f"config/system/{key}_system.js", "miao")
        diy_cfg = await Data.import_module(f"config/{key}.js", "miao")
        if diy_cfg.get("isSys"):
            diy_cfg = {}
        return {"sysCfg": sys_cfg, "diyCfg": diy_cfg}

    @staticmethod
    def get_data(target: dict[str, Any] | None, key_list: str | list[str],
                 cfg: dict[str, Any] | None = None) -> dict[str, Any]:
        target = target or {}
        cfg = cfg or {}
        default_data = cfg.get("defaultData", {})
        ret: dict[str, Any] = {}
        if isinstance(key_list, str):
            key_list = [k.strip() for k in key_list.split(",")]
        for key_cfg in key_list:
            parts = key_cfg.split(":")
            key_to = parts[0].strip()
            key_from = (parts[1] if len(parts) > 1 else parts[0]).strip()
            key_ret = key_to
            if cfg.get("lowerFirstKey"):
                key_ret = key_ret[0].lower() + key_ret[1:] if key_ret else key_ret
            if cfg.get("keyPrefix"):
                key_ret = cfg["keyPrefix"] + key_ret
            ret[key_ret] = Data.get_val(target, key_from, default_data.get(key_to, None))
        return ret

    @staticmethod
    def get_val(target: dict[str, Any], key_from: str, default_val: Any = None) -> Any:
        parts = key_from.split(".")
        val: Any = target
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return default_val
        return val if val is not None else default_val

    @staticmethod
    async def async_pool(pool_limit: int, items: list,
                         iterator_fn: Callable[[Any, list], Awaitable[Any]]) -> list[Any]:
        if pool_limit <= 0 or not items:
            return []
        ret: list[asyncio.Task] = []
        executing: list[asyncio.Task] = []
        for item in items:
            async def run(item=item):
                return await iterator_fn(item, items)
            task = asyncio.ensure_future(run())
            ret.append(task)
            executing.append(task)
            if len(executing) >= pool_limit:
                done, _ = await asyncio.wait(executing, return_when=asyncio.FIRST_COMPLETED)
                for d in done:
                    if d in executing:
                        executing.remove(d)
        if executing:
            await asyncio.wait(executing)
        return await asyncio.gather(*ret)

    @staticmethod
    def sleep(ms: int) -> Awaitable[None]:
        return asyncio.sleep(ms / 1000)

    @staticmethod
    def def_val(*args: Any) -> Any:
        for arg in args:
            if arg is not None:
                return arg
        return None

    @staticmethod
    async def for_each(data: Any, fn: Callable) -> None:
        if isinstance(data, list):
            for idx, item in enumerate(data):
                ret = fn(item, idx)
                if asyncio.iscoroutine(ret):
                    ret = await ret
                if ret is False:
                    break
        elif isinstance(data, dict):
            for k, v in data.items():
                ret = fn(v, k)
                if asyncio.iscoroutine(ret):
                    ret = await ret
                if ret is False:
                    break

    @staticmethod
    def each_str(text: Any, fn: Callable) -> None:
        if isinstance(text, str):
            text = re.sub(r"\s*(;|；|、|，)\s*", ",", text)
            parts = [t.strip() for t in text.split(",")]
        elif isinstance(text, (int, float)):
            parts = [str(text)]
        else:
            parts = list(text) if text else []
        for idx, s in enumerate(parts):
            if s is not None:
                fn(s.strip() if hasattr(s, "strip") else s, idx)

    @staticmethod
    def reg_ret(reg: re.Pattern | None, txt: str | None, idx: int) -> str | bool:
        if reg and txt:
            m = reg.search(txt)
            if m and len(m.groups()) >= idx:
                return m.group(idx)
        return False
