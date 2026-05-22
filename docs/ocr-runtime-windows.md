# OCR Runtime on Windows

Дата: 2026-05-22

## 1. Назначение

Этот документ фиксирует runtime-зависимости для маршрута `pdf_scan`.

Без OCR runtime сканированные PDF не теряются: converter создаёт `document.v1.json`, page units, `ocr/ocr-status.json` и возвращает `partial_success` с flags `ocr_required`, `ocr_unavailable`, `review_required`. Полный OCR-текст появится только после установки OCRmyPDF, Tesseract и Ghostscript.

## 2. Проверка готовности

```powershell
.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr
```

Готовый runtime возвращает JSON `ocr-runtime.v1` со `status: ready` и exit code `0`.

Текущая проверка на этой машине вернула `status: ready`: локальный `ocrmypdf` найден в `.venv\Scripts`, Tesseract и Ghostscript установлены через `scoop`, языки `eng`, `rus`, `osd` доступны.

## 3. Установка через helper

Сначала можно посмотреть план без установки:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-ocr-runtime.ps1 -CheckOnly
```

Если `scoop` уже установлен, helper использует validated user-scope path и не требует elevated PowerShell. Если `scoop` недоступен, helper fallback-ится на старый admin path через `winget + choco`.

Основной проверенный путь на этой машине:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-ocr-runtime.ps1
```

Helper выполняет следующие шаги:

1. создаёт `.venv`, если её ещё нет;
2. ставит проект в `.venv` через `pip install -e .`;
3. ставит `tesseract` и `ghostscript` через `scoop install tesseract ghostscript`;
4. докладывает `eng`, `rus`, `osd` traineddata в `~/scoop/persist/tesseract/tessdata`.

На этой машине `scoop install tesseract-languages` не сработал из-за symlink extraction error без специальных прав, поэтому helper сразу использует прямую загрузку нужных traineddata.

## 4. Ручная проверка после установки

```powershell
.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr
.\.venv\Scripts\python.exe scripts\run_sample_pilot.py --clean
```

Проверенный результат на этой машине: `check-ocr` возвращает `status: ready`; full representative pilot даёт `21 success`, `0 partial_success`, `0 failed`; реальный OCR smoke на `PPRF_680.pdf` возвращает `processing.status: success`, `ocr_applied: true`.

## 5. Неблокирующие optional gaps

- `jbig2` не установлен, поэтому OCRmyPDF пропускает часть image optimizations.
- `pngquant` не установлен, поэтому OCRmyPDF пропускает часть PNG optimizations.
- `verapdf` не установлен, поэтому OCRmyPDF пишет `Auto mode: no verapdf available`; OCR работает, но строгая PDF/A-проверка не выполняется.
