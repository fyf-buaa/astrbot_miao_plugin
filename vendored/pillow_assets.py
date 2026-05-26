from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from .pillow_fonts import FontManager
from .pillow_draw import crop_circle


class AssetLoader:
    """Centralized asset loader.
    Wraps a res_root and provides methods to locate any image asset
    used by the original JS rendering pipeline.
    """

    def __init__(self, res_root: Path):
        self.res_root = Path(res_root)

    # ── low-level ──────────────────────────────────────────────────────

    def exists(self, rel_path: str) -> bool:
        return (self.res_root / rel_path.lstrip("/")).exists()

    def load(self, rel_path: str) -> Image.Image | None:
        p = self.res_root / rel_path.lstrip("/")
        if not p.exists():
            return None
        try:
            return Image.open(p).convert("RGBA")
        except Exception:
            return None

    def load_resize(self, rel_path: str, w: int, h: int | None = None) -> Image.Image | None:
        img = self.load(rel_path)
        if img is None:
            return None
        if h:
            return img.resize((w, h), Image.LANCZOS)
        ratio = w / img.width
        return img.resize((w, int(img.height * ratio)), Image.LANCZOS)

    def resolve(self, rel_path: str) -> Path:
        return self.res_root / rel_path.lstrip("/")

    # ── character assets ───────────────────────────────────────────────

    def char_face(self, name: str, game: str = "gs", costume: str = "") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/character/{name}/imgs/face{costume}.webp"
        if self.exists(base):
            return base
        base2 = f"{meta}/character/{name}/imgs/face.webp"
        if self.exists(base2):
            return base2
        # common fallback
        cb = f"{meta}/character/common/imgs/card.webp"
        if self.exists(cb):
            return cb
        return "common/item/face.webp"

    def char_splash(self, name: str, game: str = "gs", costume: str = "") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/character/{name}/imgs/splash{costume}.webp"
        if self.exists(base):
            return base
        base2 = f"{meta}/character/{name}/imgs/splash{costume}.png"
        if self.exists(base2):
            return base2
        base3 = f"{meta}/character/{name}/imgs/splash.webp"
        if self.exists(base3):
            return base3
        return None

    def char_side(self, name: str, game: str = "gs", costume: str = "") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/character/{name}/imgs/side{costume}.webp"
        if self.exists(base):
            return base
        base2 = f"{meta}/character/{name}/imgs/side.webp"
        if self.exists(base2):
            return base2
        return None

    def char_cons(self, name: str, game: str, idx: int) -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        sub = "imgs" if game == "sr" else "icons"
        base = f"{meta}/character/{name}/{sub}/cons-{idx}.webp"
        if self.exists(base):
            return base
        return None

    def char_talent(self, name: str, game: str, key: str) -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        sub = "imgs" if game == "sr" else "icons"
        base = f"{meta}/character/{name}/{sub}/talent-{key}.webp"
        if self.exists(base):
            return base
        if game == "gs":
            cons_map = {"a": "6", "e": "3", "q": "5"}
            fallback = f"{meta}/character/{name}/icons/cons-{cons_map.get(key, '1')}.webp"
            if self.exists(fallback):
                return fallback
        return None

    def char_passive(self, name: str, game: str, idx: int) -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/character/{name}/icons/passive-{idx}.webp"
        if self.exists(base):
            return base
        return None

    def char_banner(self, name: str, game: str = "gs") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/character/{name}/imgs/banner.webp"
        if self.exists(base):
            return base
        fallback = f"{meta}/character/common/imgs/banner.webp"
        if self.exists(fallback):
            return fallback
        return None

    def char_card(self, name: str, game: str = "gs") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/character/{name}/imgs/card.webp"
        if self.exists(base):
            return base
        fallback = f"{meta}/character/common/imgs/card.webp"
        if self.exists(fallback):
            return fallback
        return None

    def char_gacha(self, name: str, game: str = "gs") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/character/{name}/imgs/gacha.webp"
        if self.exists(base):
            return base
        return None

    # ── weapon assets ──────────────────────────────────────────────────

    def weapon_icon(self, name: str, type_: str, game: str = "gs") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/weapon/{type_}/{name}/icon.webp"
        if self.exists(base):
            return base
        return None

    def weapon_splash(self, name: str, type_: str, game: str = "sr") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/weapon/{type_}/{name}/splash.webp"
        if self.exists(base):
            return base
        return None

    def weapon_gacha(self, name: str, type_: str, game: str = "gs") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/weapon/{type_}/{name}/gacha.webp"
        if self.exists(base):
            return base
        return None

    def weapon_awaken(self, name: str, type_: str, game: str = "gs") -> str | None:
        meta = "meta-sr" if game == "sr" else "meta-gs"
        base = f"{meta}/weapon/{type_}/{name}/awaken.webp"
        if self.exists(base):
            return base
        return None

    # ── artifact / relic assets ────────────────────────────────────────

    def arti_icon(self, set_name: str, slot: str, game: str = "gs") -> str | None:
        if game == "sr":
            idx_map = {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
                       "head": "0", "hands": "1", "body": "2", "feet": "3",
                       "planar": "4", "rope": "4"}
            slot = idx_map.get(slot, slot)
            base = f"meta-sr/artifact/{set_name}/arti-{slot}.webp"
        else:
            base = f"meta-gs/artifact/{set_name}/{slot}.webp"
        if self.exists(base):
            return base
        return None

    # ── common UI assets ───────────────────────────────────────────────

    def star_sprite(self) -> str:
        return "common/item/star.png"

    def star_ltr(self) -> str:
        return "common/item/star-ltr.png"

    def fetter_sprite(self) -> str:
        return "common/item/fetter.png"

    def bg_frame(self, rank: int, variant: str = "") -> str | None:
        v = f"-{variant}" if variant else ""
        base = f"common/item/bg{rank}{v}.png"
        if self.exists(base):
            return base
        # fallback: try without variant
        base2 = f"common/item/bg{rank}.png"
        if self.exists(base2):
            return base2
        return None

    def cons0(self) -> str:
        return "common/item/cons0.webp"

    def face_default(self) -> str:
        return "common/item/face.webp"

    def crown_gs(self) -> str | None:
        base = "common/item/crown-o.png"
        return base if self.exists(base) else None

    def crown_sr(self) -> str | None:
        base = "common/item/crown-sr-o.png"
        return base if self.exists(base) else None

    def atk_icon(self, weapon_type: str) -> str | None:
        base = f"common/item/atk-{weapon_type}.webp"
        return base if self.exists(base) else None

    def artifact_icon(self) -> str:
        return "common/item/artifact-icon.webp"

    def element_bg(self, elem: str) -> str | None:
        base = f"common/bg/bg-{elem}.webp"
        return base if self.exists(base) else None

    def talent_bg(self, elem: str) -> str | None:
        base = f"common/bg/talent-{elem}.webp"
        return base if self.exists(base) else None

    def card_bg_texture(self) -> str | None:
        base = "common/cont/card-bg.png"
        return base if self.exists(base) else None

    def logo(self) -> str | None:
        base = "common/cont/logo.png"
        return base if self.exists(base) else None

    def region_icon(self, region: str) -> str | None:
        base = f"common/item/{region}.png"
        return base if self.exists(base) else None

    def elem_icon(self, elem: str, game: str = "gs") -> str | None:
        if game == "sr":
            base = f"meta-sr/public/icons/elem-{elem}.webp"
            if self.exists(base):
                return base
            base2 = f"meta-sr/public/icons/elm-{elem}.webp"
            if self.exists(base2):
                return base2
        # try genshin plugin element icons
        base3 = f"img/element/{elem}.png"
        if self.exists(base3):
            return base3
        return None

    # ── SR public icons ────────────────────────────────────────────────

    def sr_attr_icon(self, stat: str) -> str | None:
        base = f"meta-sr/public/icons/attr-{stat}.webp"
        return base if self.exists(base) else None

    def sr_path_icon(self, path: str) -> str | None:
        base = f"meta-sr/public/icons/type-{path}.webp"
        if self.exists(base):
            return base
        base2 = f"meta-sr/public/icons/type-{path}s.webp"
        if self.exists(base2):
            return base2
        return None

    def sr_tree_icon(self, stat: str) -> str | None:
        base = f"meta-sr/public/icons/tree-{stat}.webp"
        return base if self.exists(base) else None

    def sr_star(self, rank: int) -> str | None:
        base = f"meta-sr/public/icons/star-{rank}.png"
        return base if self.exists(base) else None

    def sr_artis_pos(self, idx: int) -> str | None:
        base = f"meta-sr/public/icons/artis-{idx}.webp"
        return base if self.exists(base) else None

    # ── screen-specific assets ─────────────────────────────────────────

    def profile_icon_sprite(self, game: str = "gs") -> str | None:
        f = "character/imgs/icon-sr.png" if game == "sr" else "character/imgs/icon.png"
        return f if self.exists(f) else None

    def crown_profile(self, game: str = "gs") -> str | None:
        f = "character/imgs/crown-sr.webp" if game == "sr" else "character/imgs/crown.png"
        return f if self.exists(f) else None

    def up_num_icon(self, variant: int = 0) -> str | None:
        f = f"character/imgs/up-num-icon{variant}.png"
        return f if self.exists(f) else None

    def main_header(self, idx: int = 1) -> str | None:
        f = f"character/imgs/main-0{idx}.png"
        return f if self.exists(f) else None

    def mark_icon(self, idx: int = 1) -> str | None:
        f = "character/imgs/mark-icon2.png" if idx == 2 else "character/imgs/mark-icon.png"
        return f if self.exists(f) else None

    def dmg_rank_bg(self) -> str | None:
        f = "character/imgs/dmg-rank-bg.png"
        return f if self.exists(f) else None

    def mark_rank_bg(self) -> str | None:
        f = "character/imgs/mark-rank-bg.png"
        return f if self.exists(f) else None

    def profile_bg(self, idx: int = 1) -> str | None:
        f = f"character/imgs/bg-0{idx}.jpg"
        return f if self.exists(f) else None

    # card art: character-img/{Name}/01.jpg etc.
    def card_art(self, char_name: str) -> str | None:
        base = f"character-img/{char_name}"
        for ext in (".jpg", ".png", ".webp", ".jpeg"):
            for f in sorted(self.res_root.rglob(f"{base}/*{ext}")):
                rel = f.relative_to(self.res_root).as_posix()
                return rel
        fallback = "character-img/default/01.jpg"
        if self.exists(fallback):
            return fallback
        return None

    # ── element theme helpers ──────────────────────────────────────────

    ELEM_COLORS: dict[str, tuple[int, int, int, int]] = {
        "pyro":       (255, 100, 50, 255),
        "hydro":      (50, 150, 255, 255),
        "cryo":       (100, 200, 255, 255),
        "electro":    (180, 80, 255, 255),
        "anemo":      (120, 220, 180, 255),
        "geo":        (255, 200, 50, 255),
        "dendro":     (100, 200, 80, 255),
        "quantum":    (80, 150, 255, 255),
        "imaginary":  (255, 210, 80, 255),
        "physical":   (180, 180, 180, 255),
        "fire":       (255, 100, 50, 255),
        "ice":        (100, 200, 255, 255),
        "wind":       (120, 220, 180, 255),
        "lightning":  (180, 80, 255, 255),
        "thunder":    (180, 80, 255, 255),
    }

    def elem_color(self, elem: str) -> tuple[int, int, int, int]:
        return self.ELEM_COLORS.get(elem, (100, 120, 200, 255))

    def elem_gradient(self, elem: str) -> tuple[tuple, tuple]:
        c = self.elem_color(elem)
        darker = tuple(max(0, v - 60) for v in c[:3]) + (c[3],)
        return c, darker

    # ── compose helpers ────────────────────────────────────────────────

    def compose_avatar_frame(self, face_rel: str, rank: int,
                             size: int = 80) -> Image.Image | None:
        face = self.load(face_rel)
        if face is None:
            face = self.load(self.face_default())
        if face is None:
            return None
        face = crop_circle(face.resize((size, size), Image.LANCZOS))
        frame_rel = self.bg_frame(rank)
        if frame_rel:
            frame = self.load_resize(frame_rel, size + 8, size + 8)
            if frame:
                result = frame.copy()
                result.paste(face, (4, 4), face)
                return result
        return face
