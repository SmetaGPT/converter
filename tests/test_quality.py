from __future__ import annotations

import unittest
from typing import cast

from doc_converter.quality import quality_payload, review_required, text_quality_flags


class QualityTests(unittest.TestCase):
    def test_empty_text_sets_review_required(self) -> None:
        flags = text_quality_flags("", size_bytes=10000, route="pdf_text")
        payload = quality_payload(flags)
        payload_flags = cast(list[str], payload["flags"])
        self.assertIn("empty_text", payload_flags)
        self.assertIn("review_required", payload_flags)

    def test_short_extraction_for_large_text_source(self) -> None:
        flags = text_quality_flags("tiny", size_bytes=90000, route="docx_native")
        self.assertIn("short_extraction", flags)
        self.assertFalse(review_required(flags))

    def test_reasonable_text_has_no_flags(self) -> None:
        flags = text_quality_flags("x" * 1000, size_bytes=1000, route="pdf_text")
        self.assertEqual(flags, [])


if __name__ == "__main__":
    unittest.main()