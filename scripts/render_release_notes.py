from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from doc_converter.release_notes import write_release_notes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render portable release notes from CHANGELOG.md.")
    parser.add_argument("--name", required=True, help="Product name used in the release heading.")
    parser.add_argument("--version", required=True, help="Release version without path decoration.")
    parser.add_argument("--artifact-name", required=True, help="Portable artifact filename.")
    parser.add_argument("--checksum", required=True, help="SHA256 checksum of the portable artifact.")
    parser.add_argument("--output", required=True, help="Path to release-notes.md.")
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Path to the changelog source.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    write_release_notes(
        output_path=Path(args.output),
        name=args.name,
        version=args.version,
        artifact_name=args.artifact_name,
        checksum=args.checksum,
        changelog_path=Path(args.changelog),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
