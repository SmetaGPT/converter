from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

from docx.text.paragraph import Paragraph
from PIL import Image, ImageChops, ImageDraw, ImageFont, UnidentifiedImageError

from doc_converter.font_bundle import bundled_font_paths

from .formulas.wmf import _extract_formula_text_from_asset

REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
INLINE_GLYPH_SYMBOLS = (
    "+",
    "-",
    "=",
    "<",
    ">",
    "÷",
    "±",
    "×",
    "≤",
    "≥",
    "≈",
    "≠",
    "√",
    "∑",
    "∏",
    "∫",
    "∂",
    "∇",
    "∞",
    "·",
    "•",
    "°",
    "∅",
    "∀",
    "∃",
    "∈",
    "∉",
    "∩",
    "∪",
    "⊂",
    "⊃",
    "⊆",
    "⊇",
    "→",
    "←",
    "↔",
    "⇒",
    "⇔",
    "∝",
    "∥",
    "⊥",
    "∠",
    "⊕",
    "⊗",
    "∴",
    "∵",
)
INLINE_GLYPH_SYSTEM_FONT_CANDIDATES = (
    "C:/Windows/Fonts/cambria.ttc",
    "C:/Windows/Fonts/cambriai.ttf",
    "C:/Windows/Fonts/seguisym.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/arial.ttf",
)
INLINE_GLYPH_TEMPLATE_SIZE = 64
INLINE_GLYPH_TEMPLATE_MARGIN = 8
INLINE_GLYPH_MAX_EXTENT_EMU = 2000000
INLINE_GLYPH_SCORE_THRESHOLD = 0.16
INLINE_GLYPH_SCORE_MARGIN = 0.02
INLINE_GLYPH_RENDER_TIMEOUT_SECONDS = 15
INLINE_GLYPH_RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff"}
INLINE_GLYPH_METAFILE_SUFFIXES = {".wmf", ".emf"}
INLINE_GLYPH_CACHE: dict[str, str | None] = {}
LANCZOS_RESAMPLING = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else cast(Any, Image).LANCZOS


def _inline_drawing_placeholders(paragraph: Paragraph, drawing: Any) -> list[str]:
    placeholders: list[str] = []
    seen_rel_ids: set[str] = set()
    drawing_extent = _inline_drawing_extent_emu(drawing)
    for node in drawing.iter():
        rel_id = node.attrib.get(f"{REL_NS}embed")
        if rel_id is None or rel_id in seen_rel_ids:
            continue
        seen_rel_ids.add(rel_id)
        placeholders.append(_inline_drawing_placeholder(paragraph, rel_id, drawing_extent))
    return placeholders


def _inline_drawing_placeholder(
    paragraph: Paragraph,
    rel_id: str,
    drawing_extent: tuple[int, int] | None = None,
) -> str:
    asset_name, blob = _resolve_inline_drawing_asset(paragraph, rel_id)
    text = _extract_formula_text_from_asset(blob, asset_name)
    if text is not None:
        return text

    symbol = _recognize_inline_glyph(blob, asset_name, drawing_extent)
    if symbol is not None:
        return symbol

    if asset_name is not None:
        return f"[INLINE_DRAWING:{asset_name}]"

    related_parts = getattr(paragraph.part, "related_parts", None)
    if related_parts is not None:
        related_part = related_parts.get(rel_id)
        part_name = getattr(related_part, "partname", None)
        if part_name is not None:
            return f"[INLINE_DRAWING:{Path(str(part_name)).name}]"

    relationships = getattr(paragraph.part, "rels", None)
    if relationships is not None and rel_id in relationships:
        target_ref = getattr(relationships[rel_id], "target_ref", None)
        if target_ref:
            return f"[INLINE_DRAWING:{Path(str(target_ref)).name}]"

    return f"[INLINE_DRAWING:{rel_id}]"


def _resolve_inline_drawing_asset(paragraph: Paragraph, rel_id: str) -> tuple[str | None, bytes | None]:
    related_parts = getattr(paragraph.part, "related_parts", None)
    if related_parts is not None:
        related_part = related_parts.get(rel_id)
        if related_part is not None:
            part_name = getattr(related_part, "partname", None)
            blob = getattr(related_part, "blob", None)
            if part_name is not None:
                return Path(str(part_name)).name, bytes(blob) if blob is not None else None

    relationships = getattr(paragraph.part, "rels", None)
    if relationships is not None and rel_id in relationships:
        target_ref = getattr(relationships[rel_id], "target_ref", None)
        if target_ref:
            return Path(str(target_ref)).name, None
    return None, None


def _inline_drawing_extent_emu(drawing: Any) -> tuple[int, int] | None:
    for node in drawing.iter():
        cx = node.attrib.get("cx")
        cy = node.attrib.get("cy")
        if cx is None or cy is None:
            continue
        try:
            return int(cx), int(cy)
        except ValueError:
            continue
    return None


def _recognize_inline_glyph(
    blob: bytes | None,
    asset_name: str | None,
    drawing_extent: tuple[int, int] | None,
) -> str | None:
    if blob is None or asset_name is None or drawing_extent is None:
        return None
    if max(drawing_extent) > INLINE_GLYPH_MAX_EXTENT_EMU:
        return None

    cache_key = hashlib.sha256(blob + b"|" + asset_name.encode("utf-8", errors="ignore")).hexdigest()
    if cache_key in INLINE_GLYPH_CACHE:
        return INLINE_GLYPH_CACHE[cache_key]

    image = _load_inline_glyph_image(blob, asset_name)
    if image is None:
        INLINE_GLYPH_CACHE[cache_key] = None
        return None

    symbol = _match_inline_glyph(image)
    INLINE_GLYPH_CACHE[cache_key] = symbol
    return symbol


def _load_inline_glyph_image(blob: bytes, asset_name: str) -> Image.Image | None:
    suffix = Path(asset_name).suffix.lower()
    if suffix in INLINE_GLYPH_RASTER_SUFFIXES:
        return _open_inline_glyph_image(blob)
    if suffix in INLINE_GLYPH_METAFILE_SUFFIXES:
        return _render_windows_metafile(blob, suffix)
    return None


def _open_inline_glyph_image(blob: bytes) -> Image.Image | None:
    try:
        with Image.open(io.BytesIO(blob)) as image:
            return image.convert("RGBA")
    except UnidentifiedImageError:
        return None


def _render_windows_metafile(blob: bytes, suffix: str) -> Image.Image | None:
    if os.name != "nt":
        return None

    powershell = shutil.which("powershell") or shutil.which("powershell.exe")
    if powershell is None:
        return None

    script = """param([string]$src, [string]$dst)
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($src)
$bmp = New-Object System.Drawing.Bitmap $img.Width, $img.Height
$graphics = [System.Drawing.Graphics]::FromImage($bmp)
$graphics.Clear([System.Drawing.Color]::White)
$graphics.DrawImage($img, 0, 0, $img.Width, $img.Height)
$bmp.Save($dst, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bmp.Dispose()
$img.Dispose()
"""
    try:
        with tempfile.TemporaryDirectory(prefix="docx-inline-glyph-") as temp_dir:
            source_path = Path(temp_dir) / f"inline{suffix}"
            target_path = Path(temp_dir) / "inline.png"
            script_path = Path(temp_dir) / "render-inline-metafile.ps1"
            source_path.write_bytes(blob)
            script_path.write_text(script, encoding="ascii")
            completed = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script_path),
                    str(source_path),
                    str(target_path),
                ],
                capture_output=True,
                text=True,
                timeout=INLINE_GLYPH_RENDER_TIMEOUT_SECONDS,
                check=False,
            )
            if completed.returncode != 0 or not target_path.exists():
                return None
            return _open_inline_glyph_image(target_path.read_bytes())
    except (OSError, subprocess.SubprocessError):
        return None


def _match_inline_glyph(image: Image.Image) -> str | None:
    normalized = _normalize_inline_glyph_image(image)
    if normalized is None:
        return None

    font_candidates = _available_inline_glyph_fonts()
    if not font_candidates:
        return None

    scores: list[tuple[float, str]] = []
    for symbol in INLINE_GLYPH_SYMBOLS:
        best_symbol_score = 1.0
        for font_name in font_candidates:
            for font_size in range(24, 61, 4):
                template = _render_inline_glyph_template(symbol, font_name, font_size)
                if template is None:
                    continue
                score = _inline_glyph_difference_score(normalized, template)
                best_symbol_score = min(best_symbol_score, score)
        scores.append((best_symbol_score, symbol))

    scores.sort(key=lambda item: item[0])
    best_score, best_symbol = scores[0]
    second_score = scores[1][0] if len(scores) > 1 else 1.0
    if best_score > INLINE_GLYPH_SCORE_THRESHOLD:
        return None
    if second_score - best_score < INLINE_GLYPH_SCORE_MARGIN:
        return None
    return best_symbol


def _normalize_inline_glyph_image(image: Image.Image) -> Image.Image | None:
    grayscale = image.convert("L")
    bbox = grayscale.point(_inline_glyph_mask_value).getbbox()
    if bbox is None:
        return None
    cropped = grayscale.crop(bbox)
    max_dimension = max(cropped.size)
    if max_dimension == 0:
        return None
    scale = (INLINE_GLYPH_TEMPLATE_SIZE - 2 * INLINE_GLYPH_TEMPLATE_MARGIN) / max_dimension
    resized = cropped.resize(
        (max(1, round(cropped.size[0] * scale)), max(1, round(cropped.size[1] * scale))),
        LANCZOS_RESAMPLING,
    )
    canvas = Image.new("L", (INLINE_GLYPH_TEMPLATE_SIZE, INLINE_GLYPH_TEMPLATE_SIZE), color=255)
    offset_x = (INLINE_GLYPH_TEMPLATE_SIZE - resized.size[0]) // 2
    offset_y = (INLINE_GLYPH_TEMPLATE_SIZE - resized.size[1]) // 2
    canvas.paste(resized, (offset_x, offset_y))
    return canvas.point(_inline_glyph_binary_value)


def _inline_glyph_mask_value(value: int) -> int:
    return 255 if value < 240 else 0


def _inline_glyph_binary_value(value: int) -> int:
    return 0 if value < 200 else 255


def _available_inline_glyph_fonts() -> tuple[str, ...]:
    fonts: list[str] = [str(path) for path in bundled_font_paths()]
    seen = set(fonts)
    for font in INLINE_GLYPH_SYSTEM_FONT_CANDIDATES:
        candidate = Path(font)
        if not candidate.exists():
            continue
        resolved = str(candidate.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        fonts.append(resolved)
    return tuple(fonts)


def _render_inline_glyph_template(symbol: str, font_name: str, font_size: int) -> Image.Image | None:
    image = Image.new("L", (INLINE_GLYPH_TEMPLATE_SIZE, INLINE_GLYPH_TEMPLATE_SIZE), color=255)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(font_name, font_size)
    except OSError:
        return None
    bbox = draw.textbbox((0, 0), symbol, font=font)
    x = (INLINE_GLYPH_TEMPLATE_SIZE - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (INLINE_GLYPH_TEMPLATE_SIZE - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((x, y), symbol, font=font, fill=0)
    return image.point(_inline_glyph_binary_value)


def _inline_glyph_difference_score(image: Image.Image, template: Image.Image) -> float:
    diff = ImageChops.difference(image, template)
    return sum(diff.tobytes()) / (255 * INLINE_GLYPH_TEMPLATE_SIZE * INLINE_GLYPH_TEMPLATE_SIZE)
