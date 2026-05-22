from __future__ import annotations


def text_quality_flags(text: str, *, size_bytes: int, route: str) -> list[str]:
    stripped = text.strip()
    flags: list[str] = []
    if not stripped:
        flags.append("empty_text")
        return flags

    if route in {"docx_native", "pdf_text"}:
        expected_floor = max(100, min(size_bytes // 300, 5000))
        if len(stripped) < expected_floor:
            flags.append("short_extraction")
    return flags


def review_required(flags: list[str]) -> bool:
    severe = {"empty_text", "ocr_failed", "ocr_unavailable", "asset_extraction_warning"}
    return any(flag in severe for flag in flags)


def quality_payload(flags: list[str], warnings: list[str] | None = None) -> dict[str, object]:
    normalized_flags = list(dict.fromkeys(flags))
    if review_required(normalized_flags) and "review_required" not in normalized_flags:
        normalized_flags.append("review_required")
    return {
        "flags": normalized_flags,
        "warnings": warnings or [],
    }