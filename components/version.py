from __future__ import annotations

import re
from pathlib import Path

from ..tools.path import miao_path


def _get_line(line: str) -> str:
    line = re.sub(r"(^\s*\*|\r)", "", line)
    line = re.sub(r"\s*`([^`]+)`", r'<span class="cmd">\1</span>', line)
    line = re.sub(r"\s*\*\*([^*]+)\*\*", r'<span class="strong">\1</span>', line)
    line = line.replace("ⁿᵉʷ", '<span class="new"></span>')
    return line


def _read_log_file(root_dir: str, version_count: int = 4) -> dict:
    r = Path(root_dir)
    log_path = r / "CHANGELOG.md"
    logs_list: list[dict] = []
    current_version = ""
    if log_path.exists():
        text = log_path.read_text(encoding="utf-8")
        lines = text.split("\n")
        temp: dict = {}
        last_line: dict = {}
        for line in lines:
            if version_count <= -1:
                break
            vm = re.match(r"^#\s*([0-9a-zA-Z.\~\s]+?)\s*$", line)
            if vm and vm.group(1):
                v = vm.group(1).strip()
                if not current_version:
                    current_version = v
                else:
                    logs_list.append(temp)
                    if re.search(r"0\s*$", v) and version_count > 0:
                        version_count = 0
                    else:
                        version_count -= 1
                temp = {"version": v, "logs": []}
            else:
                if not line.strip():
                    continue
                if line.startswith("*"):
                    last_line = {"title": _get_line(line), "logs": []}
                    temp["logs"].append(last_line)
                elif re.match(r"^\s{2,}\*", line):
                    last_line.setdefault("logs", []).append(_get_line(line))
    return {"changelogs": logs_list, "currentVersion": current_version}


class Version:
    is_v3: bool = False
    is_miao: bool = False
    name: str = "AstrBot"
    is_alemonjs: bool = False

    @staticmethod
    def get_version() -> str:
        return "1.0.0"

    @staticmethod
    def get_yunzai() -> str:
        return "0.0.0"

    @staticmethod
    def get_changelogs() -> list[dict]:
        result = _read_log_file(f"{miao_path}/", version_count=4)
        return result["changelogs"]

    @staticmethod
    def read_log_file(root_dir: str, version_count: int = 4) -> dict:
        return {}
