# Production Readiness Audit — Windows Document Converter

- **Дата:** 2026-05-31
- **Тип:** независимый технический аудит (senior/architect)
- **Вход:** [docs/production-roadmap.md](production-roadmap.md)
- **Метод:** сопоставление roadmap с фактическим кодом + локальный прогон проверок. Принцип: нет доказательства — считается невыполненным.

## Проверено независимо (а не по самоотчёту)

| Проверка | Результат |
| --- | --- |
| `python -m unittest discover` | 194 теста, OK, skipped=4, **exit 0** ✅ |
| `ruff check src tests scripts` | 0 ошибок ✅ |
| `pyright` | 0 ошибок ✅ |
| Файлы >800 строк в `src/doc_converter` | 1 нарушение: `formula_benchmark.py` = 1059 строк ⚠️ |
| Docker / docker-compose | отсутствует (для desktop EXE допустимо) |
| `hypothesis` в зависимостях | отсутствует ❌ |
| `docs/archive/`, `scripts/validate_session_exit.py` | отсутствуют ❌ |
| `schemas/agent-guardrails.v1.json`, `agent-stop-budgets.v1.json` | отсутствуют ❌ |
| GA-пороги формул | `calc_expr=0.6776` (цель 0.80), `native=0.1858` (цель 0.70) ❌ |

---

## 1. Сводка

- **Общий % выполнения roadmap:** ≈ **77%** (≈20.9 из 27 спринтов с учётом частичных).
- **Статус проекта:** 🟡 **почти готов** — production-ready в declared scope v0.3.0, но цель roadmap (v1.0 GA) **не достигнута**.
- **Главный разрыв:** ключевая заявленная возможность (распознавание формул) на GA-порогах проваливается: native coverage 0.186 при цели 0.70 (отставание в ~3.7 раза).
- **Завершённые волны (подтверждены кодом):** W0, W1, W2, W3, W6, W7, W9.
- **Незавершённые:** W4 (с оговорками), W5 (частично), W8 (отсутствует полностью), W10 (заблокирована).

---

## 2. Production Readiness Score (PRS)

| # | Критерий | Оценка | Обоснование |
| --- | --- | :---: | --- |
| 1 | Функциональная готовность | **7** | 4 маршрута (docx/pdf_text/pdf_scan/xlsx), CLI+GUI+release работают. Native-распознавание формул 18.6% — заявленная функция недотягивает. |
| 2 | Качество кода | **7** | Чистые ruff/pyright, пакетный сплит выполнен. Но ruff-набор слабее заявленного, 1 файл-переросток (1059 строк), много hardcoded-данных формул. |
| 3 | Архитектура | **8** | Все 4 Protocol-абстракции (Converter/Formula/OCR/Catalog) имеют ≥2 реализации, registry, модульные `run/`, `tables/`, `converters/`. |
| 4 | Надёжность | **7** | Schema-валидация, security hardening, redaction, детерминизм, graceful degraded modes. Эвристика формул даёт много low-confidence. |
| 5 | Тестирование | **7** | 194 теста, 22 файла, contracts-stability/determinism/secret-redaction. Нет property-based (S5.3), нет метрики покрытия, корпус формул переобучен. |
| 6 | Деплой и инфраструктура | **8** | 4 workflow (CI, nightly e2e, release, auto-merge), hosted proof релиза v0.3.0, portable EXE + checksum. |

**PRS = (7+7+8+7+7+8) / 6 = 7.33 ≈ 7.3**

**Интерпретация: 🟡 почти готов.** Готов к эксплуатации в declared scope (локальная пакетная конвертация v0.3.0), но не дотягивает до v1.0 GA.

---

## 3. Анализ по спринтам

| Спринт | Цель | Факт | % | Статус |
| --- | --- | --- | :---: | --- |
| S0.1 | Зелёный baseline + строгий линт | Тесты/ruff/pyright зелёные, но линт `E,F,W` вместо заявленных `E,F,W,I,UP,B,SIM`; pyright без `strict=true` | 80 | частично |
| S1.1 | Stable contracts catalog | `docs/contracts.md`, `test_contracts_stability.py`, snapshot | 100 | выполнен |
| S1.2 | Known formulas → data | `known-patterns.v1.json`, validator, тесты | 100 | выполнен |
| S1.3 | Agent metadata + validator | `agent_run_metadata`, `validate_document_package.py` | 100 | выполнен |
| S2.1 | Split docx.py | Пакет `converters/docx/`, нет файлов >800 строк | 100 | выполнен |
| S2.2 | Split runner.py | Тонкий wrapper + `run/` | 100 | выполнен |
| S2.3 | Shared tables | `tables/` общий парсер | 100 | выполнен |
| S2.4 | ConverterProtocol + registry | Registry + dummy txt-конвертер | 100 | выполнен |
| S3.1 | FormulaProvider Protocol | `formulas/providers.py`, 3 реализации | 100 | выполнен (локально) |
| S3.2 | OCR/Catalog Protocol | `ocr/backends.py`, `catalog_writers.py` | 100 | выполнен (локально) |
| S3.3 | Secret redaction | `redaction.py` + scan-тест | 100 | выполнен (локально) |
| S4.1 | Stable ordering | Детерминированная сортировка + тест | 100 | выполнен (локально) |
| S4.2 | Incremental benchmark | Кеш реализован, timing-smoke <30s НЕ прогнан | 80 | частично |
| S4.3 | Font bundling | `font_bundle.py` + assets, clean-VM proof отсутствует | 90 | частично |
| S5.1 | Corpus ≥80% calc / ≥70% native | В работе; пороги GA не достигнуты | 50 | частично |
| S5.2 | Negative samples | Нет доказательств (битый WMF/защищённый PDF не подтверждены) | 0 | не выполнен |
| S5.3 | Property-based + fixtures | `hypothesis` отсутствует в зависимостях | 0 | не выполнен |
| S6.1 | Structured CLI | `cli-result.v1`, exit-коды, doctor/dry-run | 100 | выполнен |
| S6.2 | Structured logs | `telemetry.jsonl` по `log.v1` | 100 | выполнен |
| S7.1 | Threat model + hardening | `security.md`, symlink/zip/WMF лимиты | 100 | выполнен |
| S7.2 | Secret scan CI | Gitleaks в CI | 100 | выполнен |
| S8.1 | State slim-down | `docs/archive/` отсутствует | 0 | не выполнен |
| S8.2 | Machine-readable guardrails | `validate_session_exit.py` и `*.v1.json` отсутствуют | 0 | не выполнен |
| S9.1 | PR-gates + branch protection | Workflow есть; branch protection локально не верифицируем | 90 | выполнен |
| S9.2 | Nightly e2e | Hosted proof, dispatch success | 100 | выполнен |
| S9.3 | Release automation | Hosted tag `v0.3.0`, GitHub Release | 100 | выполнен |
| S10.1 | v1.0 gate | Заблокирован: пороги формул + 4 недели telemetry + 30 ранов | 0 | не выполнен |

---

## 4. Критические проблемы

1. **GA-порог формул провален (критично).** Текущее: `calc_expr=0.6776` (цель 0.80), `native=0.1858` (цель 0.70). Native-распознавание отстаёт в ~3.7 раза. Это центральная заявленная ценность продукта.
2. **Переобучение распознавания формул (архитектурный риск).** Восстановление построено на hardcoded known-patterns под конкретные документы (`1/пр`, `421/пр`, `521/пр`, `904/пр`, `534/пр`): 21 noisy-mapping + 47 представлений привязаны к корпусу ФСНБ. Обобщённый WMF-парсер (P1-02) не закрыт — на незнакомых документах выигрыша не будет. Высокие локальные метрики benchmark вводят в заблуждение.
3. **Завышенные/расходящиеся exit-критерии S0.1.** Roadmap заявляет строгий ruff (`I,UP,B,SIM`) и pyright `strict=true`. Фактически: `pyproject.toml` → `select=["E","F","W"]` с `ignore=["E501","W191","W292"]`; `pyrightconfig.json` → нет `strict`/`typeCheckingMode`.
4. **Wave 8 отсутствует целиком.** Нет `docs/archive/`, нет `scripts/validate_session_exit.py`, нет `schemas/agent-guardrails.v1.json` / `agent-stop-budgets.v1.json`. Машинно-инфорсимых guardrails нет.
5. **Wave 5 не закрыта.** Negative-samples (S5.2) и property-based тесты (S5.3) отсутствуют — снижает доверие к устойчивости на «несчастливых путях».
6. **Файл-переросток.** `src/doc_converter/formula_benchmark.py` — 1059 строк (нарушает собственный лимит <800).
7. **Telemetry-окно 10 дней** vs требуемые 4 недели — реальных данных о долгосрочной стабильности нет.

---

## 5. Рекомендации

### Обязательно исправить (блокеры v1.0)

- Привести exit-критерии в соответствие коду либо ужесточить конфиг: включить `pyright strict` + расширенный ruff-набор, либо честно скорректировать roadmap S0.1.
- Закрыть обобщённый WMF-парсер (P1-02) до подъёма порогов native: без него GA-метрика native 0.70 недостижима честно.
- Снять «частично»-маркеры реальными доказательствами: прогнать timing-smoke S4.2 (<30s) и clean-VM рендер S4.3.

### Улучшить

- Закрыть W8 (slim state + `validate_session_exit.py`) и S5.2/S5.3 (negative samples + `hypothesis`).
- Вынести `formula_benchmark.py` из oversize-состояния.
- Добавить измерение покрытия тестами (`coverage`) как CI-сигнал.
- Расширить telemetry-окно до требуемых 4 недель перед verdict GA.

### Можно оставить

- Отсутствие Docker — для Windows desktop-приложения с portable EXE + GitHub Release это корректный выбор, не дефект.
- Маршруты docx/pdf_text/pdf_scan/xlsx, schema-контракты, CI/CD, security baseline — зрелые.
- Legacy compatibility mirrors логов — допустимый временный слой.

---

## Вердикт

Проект — крепкий инженерный prototype/v0.3.0 production-ready в узком объёме (**PRS 7.3**). Заявление о близости к v1.0 GA **не подтверждается**: ключевая формульная метрика далеко от цели, корпус формул переобучен, две волны (W5 частично, W8 полностью) не выполнены, строгость линта/типизации завышена относительно фактического конфига. До production-уровня v1.0 — не готов.
