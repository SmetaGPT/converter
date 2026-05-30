"""Document route converters and registry."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ..config import ConverterConfig
from .docx import convert_docx
from .pdf_scan import convert_pdf_scan
from .pdf_text import convert_pdf_text
from .protocol import ConversionOutcome, ConverterProtocol, DetectionResult
from .xlsx import convert_xlsx


@dataclass(frozen=True)
class ResolvedConverter:
	converter: ConverterProtocol
	warnings: tuple[str, ...] = ()

	@property
	def route(self) -> str:
		return self.converter.route


@lru_cache(maxsize=128)
def _classify_pdf_route(path_str: str) -> tuple[str, tuple[str, ...]]:
	pdf_path = Path(path_str)
	try:
		from pypdf import PdfReader
	except ImportError:
		return "pdf_scan", ("pypdf_not_available", "ocr_required")

	try:
		reader = PdfReader(str(pdf_path))
		pages = len(reader.pages)
		text_chars = 0
		for page in reader.pages[:5]:
			text_chars += len((page.extract_text() or "").strip())
		threshold = max(200, min(max(pages, 1), 5) * 40)
		if text_chars >= threshold:
			return "pdf_text", ()
		return "pdf_scan", ("ocr_required",)
	except Exception as exc:  # noqa: BLE001 - route detection must not stop inventory.
		return "pdf_scan", ("pdf_text_layer_check_failed", type(exc).__name__, "ocr_required")


class _DocxConverter:
	route = "docx_native"

	def detect(self, path: Path) -> DetectionResult | None:
		if path.suffix.lower() != ".docx":
			return None
		return DetectionResult()

	def convert(
		self,
		source_path: Path,
		output_dir: Path,
		sha256: str,
		*,
		config: ConverterConfig,
		relative_source_path: str | None = None,
	) -> ConversionOutcome:
		del config
		result = convert_docx(source_path, output_dir, sha256, relative_source_path=relative_source_path)
		return ConversionOutcome(
			status=result.status,
			units_count=result.units_count,
			manifest_data={
				"assets_count": result.assets_count,
				"search_text_chars": result.search_text_chars,
			},
		)


class _PdfTextConverter:
	route = "pdf_text"

	def detect(self, path: Path) -> DetectionResult | None:
		if path.suffix.lower() != ".pdf":
			return None
		route, warnings = _classify_pdf_route(str(path.resolve()))
		if route != self.route:
			return None
		return DetectionResult(warnings=warnings)

	def convert(
		self,
		source_path: Path,
		output_dir: Path,
		sha256: str,
		*,
		config: ConverterConfig,
		relative_source_path: str | None = None,
	) -> ConversionOutcome:
		del config
		result = convert_pdf_text(source_path, output_dir, sha256, relative_source_path=relative_source_path)
		return ConversionOutcome(
			status=result.status,
			units_count=result.units_count,
			manifest_data={
				"pages": result.pages,
				"search_text_chars": result.text_chars,
			},
		)


class _PdfScanConverter:
	route = "pdf_scan"

	def detect(self, path: Path) -> DetectionResult | None:
		if path.suffix.lower() != ".pdf":
			return None
		route, warnings = _classify_pdf_route(str(path.resolve()))
		if route != self.route:
			return None
		return DetectionResult(warnings=warnings)

	def convert(
		self,
		source_path: Path,
		output_dir: Path,
		sha256: str,
		*,
		config: ConverterConfig,
		relative_source_path: str | None = None,
	) -> ConversionOutcome:
		result = convert_pdf_scan(
			source_path,
			output_dir,
			sha256,
			config.options.ocr_languages,
			relative_source_path=relative_source_path,
		)
		return ConversionOutcome(
			status=result.status,
			units_count=result.units_count,
			manifest_data={
				"pages": result.pages,
				"search_text_chars": result.text_chars,
				"warnings": list(result.warnings),
			},
		)


class _XlsxConverter:
	route = "xlsx_native"

	def detect(self, path: Path) -> DetectionResult | None:
		if path.suffix.lower() != ".xlsx":
			return None
		return DetectionResult()

	def convert(
		self,
		source_path: Path,
		output_dir: Path,
		sha256: str,
		*,
		config: ConverterConfig,
		relative_source_path: str | None = None,
	) -> ConversionOutcome:
		del config
		result = convert_xlsx(source_path, output_dir, sha256, relative_source_path=relative_source_path)
		return ConversionOutcome(
			status=result.status,
			units_count=result.units_count,
			manifest_data={
				"sheets": result.sheets,
				"search_text_chars": result.text_chars,
				"formula_cells": result.formula_cells,
				"warnings": list(result.warnings),
			},
		)


REGISTERED_CONVERTERS: tuple[ConverterProtocol, ...] = (
	_DocxConverter(),
	_PdfTextConverter(),
	_PdfScanConverter(),
	_XlsxConverter(),
)


def detect_converter(path: Path) -> ResolvedConverter | None:
	for converter in REGISTERED_CONVERTERS:
		detection = converter.detect(path)
		if detection is not None:
			return ResolvedConverter(converter=converter, warnings=detection.warnings)
	return None


def get_converter(route: str) -> ConverterProtocol:
	for converter in REGISTERED_CONVERTERS:
		if converter.route == route:
			return converter
	raise KeyError(route)


__all__ = [
	"ConversionOutcome",
	"ConverterProtocol",
	"DetectionResult",
	"REGISTERED_CONVERTERS",
	"ResolvedConverter",
	"detect_converter",
	"get_converter",
]