from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch


class GuiImportTests(unittest.TestCase):
    def test_gui_module_imports(self) -> None:
        import doc_converter.gui as gui

        self.assertTrue(hasattr(gui, "ConverterApp"))

    def test_converter_app_initializes(self) -> None:
        import doc_converter.gui as gui

        try:
            app = gui.ConverterApp()
        except tk.TclError as exc:
            self.skipTest(f"Tk is not available: {exc}")

        try:
            app.update_idletasks()
            self.assertEqual(app.title(), "Windows Document Converter")
            self.assertTrue(app.start_button.winfo_exists())
            self.assertTrue(app.cancel_button.winfo_exists())
            self.assertTrue(app.open_output_button.winfo_exists())
            self.assertTrue(app.open_html_qc_button.winfo_exists())
            self.assertTrue(app.progress_bar.winfo_exists())
        finally:
            app.destroy()

    def test_progress_events_update_gui_state(self) -> None:
        import doc_converter.gui as gui

        try:
            app = gui.ConverterApp()
        except tk.TclError as exc:
            self.skipTest(f"Tk is not available: {exc}")

        try:
            app.events.put({"type": "progress", "event": "inventory_built", "total_files": 3, "processed_files": 0})
            app.events.put(
                {
                    "type": "progress",
                    "event": "document_finished",
                    "relative_path": "sample.docx",
                    "status": "success",
                    "total_files": 3,
                    "processed_files": 1,
                }
            )
            app._drain_events()

            self.assertEqual(app.current_file_var.get(), "sample.docx")
            self.assertEqual(app.progress_label_var.get(), "1 / 3")
            self.assertGreater(app.progress_var.get(), 0.0)
        finally:
            app.destroy()

    def test_cancel_sets_flag_for_running_worker(self) -> None:
        import doc_converter.gui as gui

        try:
            app = gui.ConverterApp()
        except tk.TclError as exc:
            self.skipTest(f"Tk is not available: {exc}")

        try:
            app.worker = cast(Any, SimpleNamespace(is_alive=lambda: True))
            app._cancel()
            self.assertTrue(app.cancel_requested.is_set())
            self.assertEqual(app.status_var.get(), "Отмена после текущего файла...")
        finally:
            app.destroy()

    def test_start_rejects_overlapping_directories_before_worker_launch(self) -> None:
        import doc_converter.gui as gui

        try:
            app = gui.ConverterApp()
        except tk.TclError as exc:
            self.skipTest(f"Tk is not available: {exc}")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                input_dir = Path(temp_dir) / "input"
                input_dir.mkdir()
                app.input_var.set(str(input_dir))
                app.output_var.set(str(input_dir / "out"))

                with patch.object(gui.messagebox, "showerror") as showerror:
                    app._start()

                showerror.assert_called_once()
                self.assertIsNone(app.worker)
                self.assertEqual(app.status_var.get(), "Готово")
        finally:
            app.destroy()

    def test_success_event_enables_html_qc_button(self) -> None:
        import doc_converter.gui as gui

        try:
            app = gui.ConverterApp()
        except tk.TclError as exc:
            self.skipTest(f"Tk is not available: {exc}")

        try:
            app.events.put(
                {
                    "type": "success",
                    "status": "success",
                    "run_dir": "D:/converter-output/runs/example",
                    "supported_files": 1,
                    "summary": {"review_required_files": 0, "partial_files": 0, "failed_files": 0},
                }
            )
            app._drain_events()

            self.assertEqual(str(app.open_html_qc_button["state"]), tk.NORMAL)
        finally:
            app.destroy()

    def test_open_html_qc_exports_index_and_opens_browser(self) -> None:
        import doc_converter.gui as gui

        try:
            app = gui.ConverterApp()
        except tk.TclError as exc:
            self.skipTest(f"Tk is not available: {exc}")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                run_dir = Path(temp_dir)
                index_path = run_dir / "human-readable-index.html"
                app.last_run_dir = run_dir

                with patch.object(gui, "export_run_human_readable_html", return_value=index_path) as exporter:
                    with patch.object(gui.webbrowser, "open") as browser_open:
                        app._open_html_qc()

                exporter.assert_called_once_with(run_dir)
                browser_open.assert_called_once_with(index_path.resolve().as_uri())
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()