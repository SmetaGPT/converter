from __future__ import annotations

import unittest


class GuiImportTests(unittest.TestCase):
    def test_gui_module_imports(self) -> None:
        import doc_converter.gui as gui

        self.assertTrue(hasattr(gui, "ConverterApp"))


if __name__ == "__main__":
    unittest.main()