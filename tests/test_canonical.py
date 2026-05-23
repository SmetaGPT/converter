from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from doc_converter.canonical import (
    SourceRef,
    StructuralUnit,
    document_id_from_sha256,
    minimal_document,
    sha256_file,
    unit_id,
)


class CanonicalTests(unittest.TestCase):
    def test_document_id_from_sha256(self) -> None:
        digest = "a" * 64
        self.assertEqual(document_id_from_sha256(digest), f"sha256:{digest}")

    def test_document_id_rejects_invalid_digest(self) -> None:
        with self.assertRaises(ValueError):
            document_id_from_sha256("not-a-digest")

    def test_unit_id_is_stable_and_padded(self) -> None:
        self.assertEqual(unit_id(0), "u_000000")
        self.assertEqual(unit_id(42), "u_000042")

    def test_sha256_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "a.txt"
            path.write_text("abc", encoding="utf-8")
            self.assertEqual(sha256_file(path), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_minimal_document_is_json_serializable(self) -> None:
        digest = "b" * 64
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.docx"
            path.write_bytes(b"doc")
            doc_id = document_id_from_sha256(digest)
            unit = StructuralUnit(
                unit_id=unit_id(1),
                type="paragraph",
                order=1,
                text="hello",
                source_ref=SourceRef(document_id=doc_id, docx_path="/w:document/w:body/w:p[1]"),
            )

            payload = minimal_document(
                source_path=path,
                source_format="docx",
                sha256=digest,
                route="docx_native",
                status="success",
                units=[unit],
                relative_source_path="nested/sample.docx",
            )

            self.assertEqual(payload["schema_version"], "document.v1")
            self.assertEqual(payload["document_id"], doc_id)
            self.assertEqual(payload["source"]["relative_input_path"], "nested/sample.docx")
            self.assertEqual(payload["metadata"]["document_type"], "unknown")
            self.assertEqual(payload["metadata"]["method"], "filename_fallback")
            self.assertEqual(payload["units"][0]["unit_id"], "u_000001")
            self.assertEqual(payload["units"][0]["quality"], {"flags": [], "warnings": []})
            json.dumps(payload, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()