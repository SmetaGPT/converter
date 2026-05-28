from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from typing import Any

from doc_converter.schema_validation import validate_payload

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"
SNAPSHOT_PATH = SCHEMAS_DIR / "__snapshot__" / "stable-contracts.v1.json"


class ContractStabilityTests(unittest.TestCase):
    def test_stable_contract_schemas_match_snapshots(self) -> None:
        snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        contracts = snapshot["contracts"]

        for schema_filename, expected in contracts.items():
            with self.subTest(schema=schema_filename):
                schema_path = SCHEMAS_DIR / schema_filename
                self.assertTrue(schema_path.exists(), schema_filename)
                actual_hash = hashlib.sha256(schema_path.read_bytes()).hexdigest()
                self.assertEqual(actual_hash, expected["sha256"])

    def test_formula_recognition_schema_accepts_known_record_shapes(self) -> None:
        records: list[dict[str, Any]] = [
            {
                "unit_id": "u_000001",
                "asset_ref": "assets/formula.png",
                "status": "recognized_provider",
                "candidate_kind": "formula_image",
                "provider": "openrouter",
                "model": "openai/gpt-4o",
                "confidence": "medium",
            },
            {
                "unit_id": "u_000002",
                "asset_ref": None,
                "status": "unresolved_without_provider",
                "candidate_kind": "formula_text",
                "local_backend": None,
            },
            {
                "unit_id": "u_000003",
                "asset_ref": "assets/missing.wmf",
                "status": "asset_missing",
            },
        ]

        for record in records:
            with self.subTest(status=record["status"]):
                validate_payload(record, "formula-recognition.v1.schema.json")

    def test_formula_recognition_schema_rejects_extra_fields(self) -> None:
        with self.assertRaises(Exception):
            validate_payload(
                {
                    "unit_id": "u_000001",
                    "status": "recognized_provider",
                    "api_key": "must-not-be-serialized",
                },
                "formula-recognition.v1.schema.json",
            )


if __name__ == "__main__":
    unittest.main()
