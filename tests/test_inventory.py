from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from doc_converter.inventory import build_inventory, classify_route


class InventoryTests(unittest.TestCase):
    def test_build_inventory_hashes_supported_files_and_ignores_temp_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.docx").write_bytes(b"same")
            (root / "b.docx").write_bytes(b"same")
            (root / "~$temp.docx").write_bytes(b"ignored")
            (root / "note.txt").write_text("ignored", encoding="utf-8")

            scan = build_inventory(root)
            records = scan.supported_records

            self.assertEqual(scan.scanned_files, 3)
            self.assertEqual(len(scan.unsupported_records), 1)
            self.assertEqual(scan.unsupported_records[0].relative_path, "note.txt")
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

    def test_classify_xlsx_route(self) -> None:
        route, warnings = classify_route(Path("sample.xlsx"))
        self.assertEqual(route, "xlsx_native")
        self.assertEqual(warnings, ())

    def test_build_inventory_sorts_records_and_duplicate_primary_independently_of_iterator_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            later_duplicate = root / "z.docx"
            earlier_duplicate = root / "a.docx"
            unique = root / "m.docx"
            unsupported = root / "note.txt"

            later_duplicate.write_bytes(b"same")
            earlier_duplicate.write_bytes(b"same")
            unique.write_bytes(b"unique")
            unsupported.write_text("ignored", encoding="utf-8")

            with patch(
                "doc_converter.inventory._iter_input_files",
                return_value=[later_duplicate, unsupported, unique, earlier_duplicate],
            ):
                scan = build_inventory(root)

            self.assertEqual(
                [record.relative_path for record in scan.supported_records],
                ["a.docx", "m.docx", "z.docx"],
            )
            self.assertEqual([record.relative_path for record in scan.unsupported_records], ["note.txt"])

            records_by_path = {record.relative_path: record for record in scan.supported_records}
            self.assertIsNone(records_by_path["a.docx"].duplicate_of)
            self.assertEqual(records_by_path["z.docx"].duplicate_of, "a.docx")


if __name__ == "__main__":
    unittest.main()
