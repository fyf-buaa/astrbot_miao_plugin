from __future__ import annotations

from typing import Any

from ..artifact import Artifact, ArtifactSet


class Artis:
    def __init__(self, game: str = "gs", is_profile: bool = False) -> None:
        self.game = game
        self._data: dict[str, dict[str, Any]] = {}
        self._is_profile = is_profile

    @property
    def length(self) -> int:
        return len(self._data)

    def set_artis_data(self, data: dict[str, Any] | None) -> None:
        if not data:
            return
        self._data = {}
        for idx_str, arti_data in data.items():
            self._data[idx_str] = arti_data

    def get_set_data(self) -> dict[str, Any]:
        set_counts: dict[str, int] = {}
        for arti_data in self._data.values():
            name = arti_data.get("name", "")
            arti = Artifact.get(name, self.game)
            if arti:
                set_name = arti.set_name
                set_counts[set_name] = set_counts.get(set_name, 0) + 1

        names: list[str] = []
        imgs: list[str] = []
        abbrs: list[str] = []
        sets: dict[str, Any] = {}

        for sname, count in sorted(set_counts.items(), key=lambda x: -x[1]):
            arti_set = ArtifactSet.get(sname, self.game)
            if not arti_set:
                continue
            s_name = arti_set.meta.get("name", sname)
            names.append(s_name)
            imgs.append(arti_set.img)
            abbr = arti_set.meta.get("abbr", s_name[:4])
            abbrs.append(abbr)
            sets[sname] = count

        s_name = ", ".join(names[:3]) if names else ""
        return {
            "names": names,
            "imgs": imgs,
            "abbrs": abbrs,
            "sets": sets,
            "sName": s_name,
            "name": s_name,
        }

    @property
    def sets(self) -> dict[str, int]:
        return self.get_set_data().get("sets", {})

    def each_artis_set(self, fn) -> None:
        from ..artifact import ArtifactSet as AS
        for sname, count in self.sets.items():
            if count < 2:
                continue
            arti_set = AS.get(sname, self.game)
            if not arti_set:
                continue
            if count >= 4:
                fn(arti_set, 2)
            fn(arti_set, count)
