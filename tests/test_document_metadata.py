from __future__ import annotations

import unittest

from doc_converter.canonical import SourceRef, StructuralUnit, document_id_from_sha256, unit_id
from doc_converter.document_metadata import build_document_metadata, fallback_document_metadata


class DocumentMetadataTests(unittest.TestCase):
    def test_build_document_metadata_extracts_order_summary(self) -> None:
        document_id = document_id_from_sha256("1" * 64)
        units = [
            _paragraph(document_id, 1, "МИНИСТЕРСТВО ЗДРАВООХРАНЕНИЯ И СОЦИАЛЬНОГО РАЗВИТИЯ"),
            _paragraph(document_id, 2, "РОССИЙСКОЙ ФЕДЕРАЦИИ"),
            _paragraph(document_id, 3, "ПРИКАЗ"),
            _paragraph(document_id, 4, "от 6 апреля 2007 г. N 243"),
            _paragraph(document_id, 5, "ОБ УТВЕРЖДЕНИИ"),
            _paragraph(document_id, 6, "ЕДИНОГО ТАРИФНО-КВАЛИФИКАЦИОННОГО СПРАВОЧНИКА РАБОТ"),
            _paragraph(document_id, 7, "Приказываю:"),
        ]

        metadata = build_document_metadata(filename="sample.docx", units=units, search_text="")

        self.assertEqual(metadata["document_type"], "приказ")
        self.assertEqual(metadata["confidence"], "high")
        self.assertIn("ПРИКАЗ", metadata["title"])
        self.assertIn("ЕДИНОГО ТАРИФНО-КВАЛИФИКАЦИОННОГО", metadata["short_summary"])

    def test_build_document_metadata_classifies_sp_from_filename(self) -> None:
        metadata = build_document_metadata(filename="СП 48.13330.pdf", units=[], search_text="Основной текст")

        self.assertEqual(metadata["document_type"], "свод правил")
        self.assertEqual(metadata["method"], "rule_based_title_extraction")

    def test_build_document_metadata_classifies_common_document_types(self) -> None:
        document_id = document_id_from_sha256("4" * 64)
        cases = [
            ("Приказ Минстроя.docx", ["ПРИКАЗ", "ОБ УТВЕРЖДЕНИИ МЕТОДИКИ"], "приказ"),
            ("Постановление Правительства РФ.pdf", ["ПОСТАНОВЛЕНИЕ", "О ПОРЯДКЕ ПРИМЕНЕНИЯ"], "постановление"),
            ("СП 48.13330.pdf", [], "свод правил"),
            ("ГОСТ Р 21.101-2020.pdf", [], "гост"),
            ("Методика определения сметной стоимости.docx", ["МЕТОДИКА", "ОПРЕДЕЛЕНИЯ СМЕТНОЙ СТОИМОСТИ"], "методика"),
        ]

        for filename, lines, expected_type in cases:
            with self.subTest(filename=filename):
                units = [_paragraph(document_id, order, line) for order, line in enumerate(lines, start=1)]
                metadata = build_document_metadata(filename=filename, units=units, search_text="")

                self.assertEqual(metadata["document_type"], expected_type)
                self.assertTrue(metadata["short_summary"])

    def test_build_document_metadata_prefers_title_type_over_body_references(self) -> None:
        document_id = document_id_from_sha256("2" * 64)
        units = [
            _paragraph(document_id, 1, "ПРИКАЗ"),
            _paragraph(document_id, 2, "ОБ УТВЕРЖДЕНИИ МЕТОДИКИ"),
        ]

        metadata = build_document_metadata(
            filename="Приказ Минстроя.docx",
            units=units,
            search_text="Ссылка на постановление правительства Российской Федерации.",
        )

        self.assertEqual(metadata["document_type"], "приказ")

    def test_build_document_metadata_classifies_methodical_guidelines_from_filename(self) -> None:
        metadata = build_document_metadata(
            filename="Государственный сметный норматив. Методические указания о порядке.docx",
            units=[_paragraph(document_id_from_sha256("3" * 64), 1, "В СТРОИТЕЛЬСТВЕ")],
            search_text="",
        )

        self.assertEqual(metadata["document_type"], "методические указания")
        self.assertIn("Методические указания", metadata["title"])

    def test_fallback_document_metadata_uses_filename(self) -> None:
        metadata = fallback_document_metadata("unknown.docx")

        self.assertEqual(metadata["document_type"], "unknown")
        self.assertEqual(metadata["title"], "unknown")
        self.assertEqual(metadata["confidence"], "low")


def _paragraph(document_id: str, order: int, text: str) -> StructuralUnit:
    return StructuralUnit(
        unit_id=unit_id(order),
        type="paragraph",
        order=order,
        text=text,
        source_ref=SourceRef(document_id=document_id),
    )


if __name__ == "__main__":
    unittest.main()