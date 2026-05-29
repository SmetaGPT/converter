from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doc_converter.formulas import get_mathtype_signature_rules

META_TEXTOUT = 0x0521
META_EXTTEXTOUT = 0x0A32
META_CREATEFONTINDIRECT = 0x02FB
META_SELECTOBJECT = 0x012D
META_DELETEOBJECT = 0x01F0
WMF_RUSSIAN_CHARSET = 204
SYMBOL_FONT_MAP = {
    0xB8: "÷",
}


@dataclass(frozen=True)
class WmfTextChunk:
    text: str
    face: str
    charset: int
    height: int
    order: int


@dataclass(frozen=True)
class WmfFormulaToken:
    text: str
    role: str
    face: str
    charset: int
    height: int
    order: int
    symbol_font: bool


@dataclass(frozen=True)
class WmfFormulaIR:
    tokens: tuple[WmfFormulaToken, ...]
    signature: str
    layout_class: str
    base_text: str
    script_text: str


def _extract_formula_text_from_asset(blob: bytes | None, asset_name: str | None) -> str | None:
    if blob is None or asset_name is None:
        return None
    suffix = Path(asset_name).suffix.lower()
    if suffix == ".wmf":
        return _extract_mathtype_wmf_text(blob)
    return None


def _extract_mathtype_wmf_text(blob: bytes) -> str | None:
    if b"MathType" not in blob and b"Design Science" not in blob:
        return None

    chunks = _extract_wmf_text_chunks(blob)
    if not chunks:
        return None
    return _assemble_mathtype_wmf_formula(chunks)


def _extract_wmf_text_chunks(blob: bytes) -> list[WmfTextChunk]:
    offset = 22 if blob[:4] == b"\xd7\xcd\xc6\x9a" else 0
    if len(blob) < offset + 18:
        return []
    offset += 18

    objects: list[dict[str, Any] | None] = []
    selected_handle: int | None = None
    chunks: list[WmfTextChunk] = []
    order = 0

    while offset + 6 <= len(blob):
        size_words = struct.unpack_from("<I", blob, offset)[0]
        func = struct.unpack_from("<H", blob, offset + 4)[0]
        if size_words == 0:
            break
        size_bytes = size_words * 2
        if offset + size_bytes > len(blob):
            break
        params = blob[offset + 6 : offset + size_bytes]

        if func == META_CREATEFONTINDIRECT and len(params) >= 50:
            height = struct.unpack_from("<h", params, 0)[0]
            charset = params[13]
            face_bytes = params[18:50]
            face = face_bytes.split(b"\x00", 1)[0].decode("latin1", errors="ignore")
            handle = next((index for index, item in enumerate(objects) if item is None), len(objects))
            if handle == len(objects):
                objects.append(None)
            objects[handle] = {
                "face": face,
                "charset": charset,
                "height": height,
            }
        elif func == META_SELECTOBJECT and len(params) >= 2:
            selected_handle = struct.unpack_from("<H", params, 0)[0]
        elif func == META_DELETEOBJECT and len(params) >= 2:
            handle = struct.unpack_from("<H", params, 0)[0]
            if handle < len(objects):
                objects[handle] = None
        elif func in {META_TEXTOUT, META_EXTTEXTOUT}:
            if selected_handle is None or selected_handle >= len(objects):
                offset += size_bytes
                if func == 0x0000:
                    break
                continue
            font = objects[selected_handle]
            if font is None:
                offset += size_bytes
                if func == 0x0000:
                    break
                continue
            raw_text = _extract_wmf_text_record_bytes(func, params)
            if raw_text:
                text = _decode_wmf_text(raw_text, str(font["face"]), int(font["charset"]))
                if text:
                    chunks.append(
                        WmfTextChunk(
                            text=text,
                            face=str(font["face"]),
                            charset=int(font["charset"]),
                            height=int(font["height"]),
                            order=order,
                        )
                    )
                    order += 1

        offset += size_bytes
    return chunks


def _extract_wmf_text_record_bytes(func: int, params: bytes) -> bytes:
    if func == META_TEXTOUT:
        if len(params) < 2:
            return b""
        count = struct.unpack_from("<h", params, 0)[0]
        return params[2 : 2 + count]

    if len(params) < 8:
        return b""
    count = struct.unpack_from("<h", params, 4)[0]
    options = struct.unpack_from("<h", params, 6)[0]
    text_offset = 8 + (8 if options & 0x0006 else 0)
    return params[text_offset : text_offset + count]


def _decode_wmf_text(raw_text: bytes, face: str, charset: int) -> str:
    normalized_face = face.strip().lower()
    if normalized_face == "symbol":
        pieces: list[str] = []
        for byte in raw_text:
            if 32 <= byte < 127:
                pieces.append(chr(byte))
                continue
            mapped = SYMBOL_FONT_MAP.get(byte)
            if mapped is not None:
                pieces.append(mapped)
        return "".join(pieces)

    encoding = "cp1251" if charset == WMF_RUSSIAN_CHARSET else "latin1"
    return raw_text.decode(encoding, errors="ignore")


def _assemble_mathtype_wmf_formula(chunks: list[WmfTextChunk]) -> str | None:
    meaningful_chunks = [chunk for chunk in chunks if chunk.text.strip()]
    if not meaningful_chunks:
        return None

    known = _assemble_known_mathtype_formula(meaningful_chunks)
    if known is not None:
        return known

    formula_ir = _build_wmf_formula_ir(meaningful_chunks)
    assembled = _assemble_wmf_formula_ir(formula_ir)
    if assembled is not None:
        return assembled

    return None


def _build_wmf_formula_ir(chunks: list[WmfTextChunk]) -> WmfFormulaIR:
    meaningful_chunks = _coalesce_adjacent_mathtype_chunks([chunk for chunk in chunks if chunk.text.strip()])
    if not meaningful_chunks:
        return WmfFormulaIR(tokens=(), signature="", layout_class="empty", base_text="", script_text="")

    max_height = max(abs(chunk.height) for chunk in meaningful_chunks)
    tokens = tuple(
        WmfFormulaToken(
            text=chunk.text,
            role="base" if abs(chunk.height) == max_height else "script",
            face=chunk.face,
            charset=chunk.charset,
            height=chunk.height,
            order=chunk.order,
            symbol_font=chunk.face.strip().lower() == "symbol",
        )
        for chunk in meaningful_chunks
    )
    base_text = "".join(token.text for token in tokens if token.role == "base").strip()
    script_text = "".join(token.text for token in tokens if token.role == "script").strip()
    return WmfFormulaIR(
        tokens=tokens,
        signature=_chunk_signature(meaningful_chunks),
        layout_class=_classify_wmf_formula_ir(tokens, base_text=base_text, script_text=script_text),
        base_text=base_text,
        script_text=script_text,
    )


def _classify_wmf_formula_ir(
    tokens: tuple[WmfFormulaToken, ...],
    *,
    base_text: str,
    script_text: str,
) -> str:
    if not tokens:
        return "empty"
    if _assemble_wmf_ir_interleaved_symbol_formula(tokens) is not None:
        return "interleaved_symbol"
    if base_text and script_text:
        return "base_with_scripts"
    if base_text:
        return "base_only"
    if script_text:
        return "script_only"
    return "unclassified"


def _assemble_wmf_formula_ir(formula_ir: WmfFormulaIR) -> str | None:
    interleaved = _assemble_wmf_ir_interleaved_symbol_formula(formula_ir.tokens)
    if interleaved is not None:
        return interleaved

    aggregate_price_formula = _assemble_wmf_ir_aggregate_price_formula(formula_ir.tokens)
    if aggregate_price_formula is not None:
        return aggregate_price_formula

    if formula_ir.layout_class == "base_only":
        return formula_ir.base_text or None
    if formula_ir.layout_class != "base_with_scripts":
        return None

    base_text = formula_ir.base_text
    script_tokens = [token for token in formula_ir.tokens if token.role == "script"]

    superscript_tokens: list[WmfFormulaToken] = []
    subscript_tokens: list[WmfFormulaToken] = []
    for token in script_tokens:
        if len(token.text) == 1 and token.charset != WMF_RUSSIAN_CHARSET:
            superscript_tokens.append(token)
        else:
            subscript_tokens.append(token)

    parts: list[str] = [base_text] if base_text else []
    if subscript_tokens:
        parts.append(f"_({''.join(token.text for token in subscript_tokens)})")
    if superscript_tokens:
        parts.append(f"^({''.join(token.text for token in superscript_tokens)})")
    result = "".join(parts).strip()
    return result or None


def _assemble_wmf_ir_aggregate_price_formula(tokens: tuple[WmfFormulaToken, ...]) -> str | None:
    if len(tokens) < 3:
        return None

    text_tokens = [token.text for token in tokens if not token.symbol_font]
    symbol_text = "".join(token.text for token in tokens if token.symbol_font)
    if len(text_tokens) != 2 or symbol_text != "*+*=+":
        return None

    if re.fullmatch(r"ОЦ\(\d+\),", text_tokens[0]) is None:
        return None

    weights = text_tokens[1]
    if len(weights) != 4 or any(char not in {"n", "m"} for char in weights):
        return None

    left_weight = weights[0]
    right_weight = weights[1]
    denominator_left = weights[2]
    denominator_right = weights[3]
    return (
        "ОЦ_(а) = "
        f"(Х_(св) × {left_weight} + Х_(сп) × {right_weight}) / "
        f"({denominator_left} + {denominator_right})"
    )


def _assemble_interleaved_symbol_formula(chunks: list[WmfTextChunk]) -> str | None:
    tokens = tuple(
        WmfFormulaToken(
            text=chunk.text,
            role="base",
            face=chunk.face,
            charset=chunk.charset,
            height=chunk.height,
            order=chunk.order,
            symbol_font=chunk.face.strip().lower() == "symbol",
        )
        for chunk in chunks
    )
    return _assemble_wmf_ir_interleaved_symbol_formula(tokens)


def _assemble_wmf_ir_interleaved_symbol_formula(tokens: tuple[WmfFormulaToken, ...]) -> str | None:
    if len(tokens) != 2:
        return None
    symbol_token = next((token for token in tokens if token.symbol_font), None)
    text_token = next((token for token in tokens if not token.symbol_font), None)
    if symbol_token is None or text_token is None:
        return None
    if len(symbol_token.text) != 2 or len(text_token.text) != 3:
        return None
    if symbol_token.text[0] != "=":
        return None
    return (
        f"{text_token.text[0]} {symbol_token.text[0]} {text_token.text[1]} "
        f"{symbol_token.text[1]} {text_token.text[2]}"
    )


def _chunk_signature(chunks: list[WmfTextChunk]) -> str:
    return "|".join(chunk.text for chunk in chunks)


def _coalesce_adjacent_mathtype_chunks(chunks: list[WmfTextChunk]) -> list[WmfTextChunk]:
    if not chunks:
        return []

    coalesced = [chunks[0]]
    for chunk in chunks[1:]:
        previous = coalesced[-1]
        if (
            chunk.order == previous.order + 1
            and chunk.face == previous.face
            and chunk.charset == previous.charset
            and chunk.height == previous.height
        ):
            coalesced[-1] = WmfTextChunk(
                text=previous.text + chunk.text,
                face=previous.face,
                charset=previous.charset,
                height=previous.height,
                order=previous.order,
            )
            continue
        coalesced.append(chunk)
    return coalesced


def _assemble_known_mathtype_formula(chunks: list[WmfTextChunk]) -> str | None:
    signatures = {_chunk_signature(chunks)}
    coalesced_chunks = _coalesce_adjacent_mathtype_chunks(chunks)
    if coalesced_chunks != chunks:
        signatures.add(_chunk_signature(coalesced_chunks))

    def has_all_markers(*markers: str) -> bool:
        return any(all(marker in signature for marker in markers) for signature in signatures)

    rules = get_mathtype_signature_rules()

    for rule in rules:
        condition = rule["condition"]

        if "signature_exact" in condition:
            if condition["signature_exact"] in signatures:
                return rule["linear_text"]

        elif "signature_contains_all" in condition:
            if has_all_markers(*condition["signature_contains_all"]):
                return rule["linear_text"]

        elif "signature_complex" in condition:
            complex_cond = condition["signature_complex"]
            if "contains_any" in complex_cond:
                for any_condition in complex_cond["contains_any"]:
                    all_markers = any_condition["all_of"]
                    ends_with = any_condition.get("ends_with")
                    if any(
                        all(marker in signature for marker in all_markers)
                        and (not isinstance(ends_with, str) or signature.endswith(ends_with))
                        for signature in signatures
                    ):
                        return rule["linear_text"]

    return None
