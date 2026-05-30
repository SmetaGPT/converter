from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from ..inventory import InventoryRecord, UnsupportedInventoryRecord
from .catalog_writers import CatalogWriteContext, CatalogWriter, ProcessedDocumentCatalogEntry


def _write_processed_documents_catalog(
    *,
    run_dir: Path,
    run_id: str,
    inventory_records: list[InventoryRecord],
    unsupported_records: list[UnsupportedInventoryRecord],
    manifest_records: list[dict[str, object]],
    error_details_by_relative_path: dict[str, str],
    writers: Sequence[CatalogWriter],
    write_validated_json: Any,
) -> None:
    documents = _build_processed_documents_catalog_documents(
        inventory_records=inventory_records,
        unsupported_records=unsupported_records,
        manifest_records=manifest_records,
        error_details_by_relative_path=error_details_by_relative_path,
    )

    context = CatalogWriteContext(
        run_dir=run_dir,
        run_id=run_id,
        documents=documents,
        write_validated_json=write_validated_json,
    )
    for writer in writers:
        writer.write(context)


def _build_processed_documents_catalog_documents(
    *,
    inventory_records: list[InventoryRecord],
    unsupported_records: list[UnsupportedInventoryRecord],
    manifest_records: list[dict[str, object]],
    error_details_by_relative_path: dict[str, str],
) -> list[ProcessedDocumentCatalogEntry]:
    manifest_by_relative_path = {
        str(record["relative_path"]): record
        for record in manifest_records
        if isinstance(record.get("relative_path"), str)
    }
    documents: list[ProcessedDocumentCatalogEntry] = []

    for inventory_record in inventory_records:
        manifest_record = manifest_by_relative_path.get(inventory_record.relative_path)
        if manifest_record is None:
            continue
        output_dir = manifest_record.get("output_dir")
        output_folder = output_dir if isinstance(output_dir, str) else None
        status = str(manifest_record.get("status", ""))
        documents.append(
            {
                "relative_input_path": inventory_record.relative_path,
                "original_filename": inventory_record.filename,
                "output_dir": output_folder,
                "output_folder_name": Path(output_folder).name if output_folder else None,
                "status": status,
                "status_label": _catalog_status_label(status),
                "issue": _catalog_issue(
                    status=status,
                    manifest_record=manifest_record,
                    error_details_by_relative_path=error_details_by_relative_path,
                ),
            }
        )

    for unsupported_record in unsupported_records:
        documents.append(
            {
                "relative_input_path": unsupported_record.relative_path,
                "original_filename": unsupported_record.filename,
                "output_dir": None,
                "output_folder_name": None,
                "status": "skipped_unsupported",
                "status_label": _catalog_status_label("skipped_unsupported"),
                "issue": "; ".join(unsupported_record.warnings) if unsupported_record.warnings else None,
            }
        )

    return documents

def _catalog_status_label(status: str) -> str:
    return {
        "success": "Успешная обработка",
        "partial_success": "Частичная обработка",
        "failed": "Ошибка",
        "skipped_duplicate": "Дубликат",
        "skipped_unsupported": "Неподдерживаемый формат",
    }.get(status, status or "Неизвестный статус")


def _catalog_issue(
    *,
    status: str,
    manifest_record: dict[str, object],
    error_details_by_relative_path: dict[str, str],
) -> str | None:
    relative_path = str(manifest_record.get("relative_path", ""))
    if status == "failed":
        return error_details_by_relative_path.get(relative_path) or str(manifest_record.get("error") or "") or None
    if status == "partial_success":
        warnings = manifest_record.get("warnings")
        if isinstance(warnings, list):
            normalized = [str(item).strip() for item in warnings if str(item).strip()]
            if normalized:
                return "; ".join(normalized)
    if status == "skipped_duplicate":
        duplicate_of = manifest_record.get("duplicate_of")
        if isinstance(duplicate_of, str) and duplicate_of:
            return f"duplicate_of:{duplicate_of}"
    return None
