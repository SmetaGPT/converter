from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .config import ConverterConfig, ConverterOptions
from .runner import ConverterError, run_convert_folder, validate_run_directories


class ConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Windows Document Converter")
        self.geometry("820x520")
        self.minsize(720, 460)
        self.events: queue.Queue[dict[str, object]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.cancel_requested = threading.Event()
        self.last_run_dir: Path | None = None

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.ocr_var = tk.StringVar(value="rus,eng")
        self.include_originals_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Готово")
        self.current_file_var = tk.StringVar(value="")
        self.progress_label_var = tk.StringVar(value="0 / 0")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.summary_var = tk.StringVar(value="")

        self._build_ui()
        self.after(100, self._drain_events)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(7, weight=1)

        ttk.Label(root, text="Входная папка").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(root, textvariable=self.input_var).grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(root, text="Выбрать", command=self._choose_input).grid(row=0, column=2, pady=4)

        ttk.Label(root, text="Выходная папка").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(root, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(root, text="Выбрать", command=self._choose_output).grid(row=1, column=2, pady=4)

        ttk.Label(root, text="OCR языки").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(root, textvariable=self.ocr_var, width=24).grid(row=2, column=1, sticky="w", padx=8, pady=4)

        ttk.Checkbutton(root, text="Сохранять оригиналы в output package", variable=self.include_originals_var).grid(
            row=3, column=1, sticky="w", padx=8, pady=4
        )

        ttk.Label(root, text="Текущий файл").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Label(root, textvariable=self.current_file_var).grid(row=4, column=1, columnspan=2, sticky="ew", padx=8, pady=4)

        ttk.Label(root, text="Прогресс").grid(row=5, column=0, sticky="w", pady=4)
        self.progress_bar = ttk.Progressbar(root, maximum=100.0, variable=self.progress_var)
        self.progress_bar.grid(row=5, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(root, textvariable=self.progress_label_var).grid(row=5, column=2, sticky="e", pady=4)
        ttk.Label(root, textvariable=self.summary_var).grid(row=6, column=0, columnspan=3, sticky="w", pady=4)

        buttons = ttk.Frame(root)
        buttons.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(12, 8))
        self.start_button = ttk.Button(buttons, text="Запустить обработку", command=self._start)
        self.start_button.pack(side=tk.LEFT)
        self.cancel_button = ttk.Button(buttons, text="Отменить", command=self._cancel, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=(8, 0))
        self.open_output_button = ttk.Button(buttons, text="Открыть результат", command=self._open_output, state=tk.DISABLED)
        self.open_output_button.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(buttons, textvariable=self.status_var).pack(side=tk.LEFT, padx=12)

        self.log = tk.Text(root, height=16, wrap="word")
        self.log.grid(row=8, column=0, columnspan=3, sticky="nsew")

    def _choose_input(self) -> None:
        value = filedialog.askdirectory(title="Выберите папку с DOCX/PDF")
        if value:
            self.input_var.set(value)

    def _choose_output(self) -> None:
        value = filedialog.askdirectory(title="Выберите папку для результата")
        if value:
            self.output_var.set(value)

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        input_dir = Path(self.input_var.get().strip())
        output_dir = Path(self.output_var.get().strip())
        if not str(input_dir) or not str(output_dir):
            messagebox.showerror("Ошибка", "Выберите входную и выходную папки.")
            return
        try:
            input_dir, output_dir = validate_run_directories(input_dir, output_dir)
        except ConverterError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        self.start_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)
        self.open_output_button.configure(state=tk.DISABLED)
        self.status_var.set("Обработка...")
        self.current_file_var.set("")
        self.progress_var.set(0.0)
        self.progress_label_var.set("0 / 0")
        self.summary_var.set("")
        self.last_run_dir = None
        self.cancel_requested.clear()
        self._append_log("Запуск обработки")
        self.worker = threading.Thread(target=self._run_worker, args=(input_dir, output_dir), daemon=True)
        self.worker.start()

    def _cancel(self) -> None:
        if self.worker and self.worker.is_alive():
            self.cancel_requested.set()
            self.status_var.set("Отмена после текущего файла...")
            self._append_log("Запрошена отмена обработки")

    def _run_worker(self, input_dir: Path, output_dir: Path) -> None:
        try:
            options = ConverterOptions(
                ocr_languages=tuple(item.strip() for item in self.ocr_var.get().split(",") if item.strip()),
                include_originals=self.include_originals_var.get(),
            )
            result = run_convert_folder(
                ConverterConfig(input_dir=input_dir, output_dir=output_dir, options=options),
                progress_callback=lambda payload: self.events.put({"type": "progress", **payload}),
                should_cancel=self.cancel_requested.is_set,
            )
            self.events.put(
                {
                    "type": "success",
                    "status": result.status,
                    "run_dir": str(result.run_dir),
                    "supported_files": result.supported_files,
                    "summary": json.loads((result.run_dir / "summary.json").read_text(encoding="utf-8")),
                }
            )
        except (ConverterError, ValueError, OSError) as exc:
            self.events.put({"type": "error", "message": str(exc)})

    def _drain_events(self) -> None:
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if event["type"] == "progress":
                self._handle_progress_event(event)
            elif event["type"] == "success":
                self.last_run_dir = Path(str(event["run_dir"]))
                final_status = str(event["status"])
                self.status_var.set("Отменено" if final_status == "cancelled" else "Готово")
                self._append_log(
                    json.dumps(
                        {
                            "status": final_status,
                            "run_dir": str(self.last_run_dir),
                            "supported_files": event["supported_files"],
                        },
                        ensure_ascii=False,
                    )
                )
                summary = event.get("summary")
                if isinstance(summary, dict):
                    self.summary_var.set(
                        f"review-required: {summary.get('review_required_files', 0)}, partial: {summary.get('partial_files', 0)}, failed: {summary.get('failed_files', 0)}"
                    )
                self.start_button.configure(state=tk.NORMAL)
                self.cancel_button.configure(state=tk.DISABLED)
                self.open_output_button.configure(state=tk.NORMAL)
            elif event["type"] == "error":
                self.status_var.set("Ошибка")
                self._append_log("Ошибка: " + str(event["message"]))
                self.start_button.configure(state=tk.NORMAL)
                self.cancel_button.configure(state=tk.DISABLED)
        self.after(100, self._drain_events)

    def _handle_progress_event(self, event: dict[str, object]) -> None:
        total_files = _coerce_event_int(event.get("total_files", 0))
        processed_files = _coerce_event_int(event.get("processed_files", 0))
        relative_path = str(event.get("relative_path", "") or "")
        event_name = str(event.get("event", ""))

        if relative_path:
            self.current_file_var.set(relative_path)
        if total_files > 0:
            self.progress_var.set((processed_files / total_files) * 100.0)
            self.progress_label_var.set(f"{processed_files} / {total_files}")
        if event_name == "document_finished" and relative_path:
            self._append_log(f"{relative_path}: {event.get('status', '')}")
        elif event_name == "run_cancelled":
            self._append_log("Обработка остановлена пользователем")

    def _open_output(self) -> None:
        if self.last_run_dir is None:
            return
        try:
            if hasattr(os, "startfile"):
                os.startfile(str(self.last_run_dir))
            else:
                subprocess.Popen(["explorer", str(self.last_run_dir)])
        except OSError as exc:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку результата: {exc}")

    def _append_log(self, message: str) -> None:
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)


def _coerce_event_int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def main() -> int:
    app = ConverterApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())