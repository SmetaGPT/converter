from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from doc_converter.inventory import build_inventory, classify_route


class InventoryTests(unittest.TestCase):
    def test_build_inventory_hashes_supported_files_and_ignores_temp_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.docx").write_bytes(b"same")
            (root / "b.docx").write_bytes(b"same")
            (root / "~$temp.docx").write_bytes(b"ignored")
            (root / "note.txt").write_text("ignored", encoding="utf-8")

            records = build_inventory(root)

            self.assertEqual(len(records), 2)
            self.assertEqual({record.route for record in records}, {"docx_native"})
            self.assertTrue(all(record.sha256 for record in records))
            self.assertTrue(all(record.duplicate_group_id for record in records))
            self.assertEqual(sum(1 for record in records if record.duplicate_of is None), 1)
            self.assertEqual(sum(1 for record in records if record.duplicate_of is not None), 1)

    def test_classify_docx_route(self) -> None:
        route, warnings = classify_route(Path("sample.docx"))
        self.assertEqual(route, "docx_native")
        self.assertEqual(warnings, ())


if __name__ == "__main__":
    unittest.main()