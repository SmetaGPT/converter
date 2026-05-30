from __future__ import annotations

import json
from pathlib import Path

from doc_converter.canonical import SourceRef, StructuralUnit, document_id_from_sha256, minimal_document, unit_id
from doc_converter.schema_validation import validate_payload

from .protocol import ConversionOutcome, DetectionResult


class _DummyTxtConverter:
    route = "txt_dummy"

    def detect(self, path: Path) -> DetectionResult | None:
        return DetectionResult() if path.suffix.lower() == ".txt" else None

    def convert(self, source_path: Path, output_dir: Path, sha256: str, *, config: object, relative_source_path: str | None = None) -> ConversionOutcome:
        del config
        text = source_path.read_text(encoding="utf-8")
        output_dir.mkdir(parents=True, exist_ok=True)
        document_id = document_id_from_sha256(sha256)
        units = [
            StructuralUnit(unit_id=unit_id(0), type="document", order=0, source_ref=SourceRef(document_id=document_id)),
            StructuralUnit(unit_id=unit_id(1), parent_id=unit_id(0), type="paragraph", order=1, text=text, source_ref=SourceRef(document_id=document_id)),
        ]
        status = "success" if text else "partial_success"
        payload = minimal_document(
            source_path=source_path,
            source_format="txt",
            sha256=sha256,
            route=self.route,
            status=status,
            units=units,
            relative_source_path=relative_source_path,
        )
        validate_payload(payload, "document.v1.schema.json")
        (output_dir / "document.v1.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (output_dir / "search_text.txt").write_text(text, encoding="utf-8")
        return ConversionOutcome(status=status, units_count=len(units), manifest_data={"search_text_chars": len(text)})


TXT_DUMMY_CONVERTER = _DummyTxtConverter()