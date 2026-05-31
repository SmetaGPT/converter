Bundled font assets for inline glyph recognition.

- Primary font: DejaVuSans.ttf
- Source: local matplotlib distribution in the workspace virtual environment
- License: see LICENSE_DEJAVU in this directory

The inline glyph matcher prefers this bundle before any system font paths so DOCX formula symbol recognition stays stable on clean Windows hosts and in packaged EXE builds.