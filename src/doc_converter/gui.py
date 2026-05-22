from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .config import ConverterConfig, ConverterOptions
from .runner import ConverterError, run_convert_folder


class ConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Windows Document Converter")
        self.geometry("820x520")
        self.minsize(720, 460)
        self.events: queue.Queue[dict[str, object]] = queue.Queue()
        self.worker: threading.Thread | None = None

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.ocr_var = tk.StringVar(value="rus,eng")
        self.workers_var = tk.IntVar(value=1)
        self.include_originals_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Готово")

        self._build_ui()
        self.after(100, self._drain_events)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(6, weight=1)

        ttk.Label(root, text="Входная папка").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(root, textvariable=self.input_var).grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(root, text="Выбрать", command=self._choose_input).grid(row=0, column=2, pady=4)

        ttk.Label(root, text="Выходная папка").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(root, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(root, text="Выбрать", command=self._choose_output).grid(row=1, column=2, pady=4)

        ttk.Label(root, text="OCR языки").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(root, textvariable=self.ocr_var, width=24).grid(row=2, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(root, text="Потоки").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Spinbox(root, from_=1, to=16, textvariable=self.workers_var, width=8).grid(
            row=3, column=1, sticky="w", padx=8, pady=4
        )

        ttk.Checkbutton(root, text="Сохранять оригиналы в output package", variable=self.include_originals_var).grid(
            row=4, column=1, sticky="w", padx=8, pady=4
        )

        buttons = ttk.Frame(root)
        buttons.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 8))
        self.start_button = ttk.Button(buttons, text="Запустить обработку", command=self._start)
        self.start_button.pack(side=tk.LEFT)
        ttk.Label(buttons, textvariable=self.status_var).pack(side=tk.LEFT, padx=12)

        self.log = tk.Text(root, height=16, wrap="word")
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew")

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

        self.start_button.configure(state=tk.DISABLED)
        self.status_var.set("Обработка...")
        self._append_log("Запуск обработки")
        self.worker = threading.Thread(target=self._run_worker, args=(input_dir, output_dir), daemon=True)
        self.worker.start()

    def _run_worker(self, input_dir: Path, output_dir: Path) -> None:
        try:
            options = ConverterOptions(
                ocr_languages=tuple(item.strip() for item in self.ocr_var.get().split(",") if item.strip()),
                workers=max(1, int(self.workers_var.get())),
                include_originals=self.include_originals_var.get(),
            )
            result = run_convert_folder(ConverterConfig(input_dir=input_dir, output_dir=output_dir, options=options))
            self.events.put(
                {
                    "type": "success",
                    "message": json.dumps(
                        {
                            "status": result.status,
                            "run_dir": str(result.run_dir),
                            "supported_files": result.supported_files,
                        },
                        ensure_ascii=False,
                    ),
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
            if event["type"] == "success":
                self.status_var.set("Готово")
                self._append_log(str(event["message"]))
                self.start_button.configure(state=tk.NORMAL)
            elif event["type"] == "error":
                self.status_var.set("Ошибка")
                self._append_log("Ошибка: " + str(event["message"]))
                self.start_button.configure(state=tk.NORMAL)
        self.after(100, self._drain_events)

    def _append_log(self, message: str) -> None:
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)


def main() -> int:
    app = ConverterApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())