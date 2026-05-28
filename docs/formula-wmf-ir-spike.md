# WMF IR Spike (P1-01)

Дата: 2026-05-26
Статус: done (go)

## 1. Цель

Проверить, можно ли перейти от расширения hardcoded signature catalog к более общему data-driven parser слою для MathType WMF formulas.

## 2. Что проверено

- В коде введён промежуточный IR слой:
  - `WmfFormulaToken`
  - `WmfFormulaIR`
  - `_build_wmf_formula_ir(...)`
  - `_classify_wmf_formula_ir(...)`
  - `_assemble_wmf_formula_ir(...)`
- Existing known-signature путь сохранён как compatibility fallback.
- Для formula payload добавлен `formula.provenance`:
  - `parser_path`
  - `normalization`
  - `confidence_basis`

## 3. Representative WMF token streams

Ниже representative patterns, подтверждённые текущими тестами и benchmark corpus:

1. Interleaved symbol:
   - text chunk: `n1N`
   - symbol chunk: `=÷`
   - expected assembly: `n = 1 ÷ N`

2. Base + scripts:
   - base chunks: `(СЦ)`
   - script chunks: `тек`, `k`
   - expected assembly: `(СЦ)_(тек)^(k)`

3. Known dense signature class (double-sum family):
   - chunks around `ОТЗТСЦV`, `IN`, `nini`, `==`, `=`
   - currently handled by known-pattern fallback

## 4. Классификация unresolved residue

- `parsable_with_rules`:
  - interleaved symbol cases
  - base/script cases, где различие даёт высота/font role
- `needs_richer_ast`:
  - вложенные sum/index layouts с неоднозначным соответствием индексов
- `needs_ocr_fallback`:
  - случаи, где WMF text records частично/сильно повреждены
- `not_enough_signal`:
  - assets, где нет достаточного WMF text signal

## 5. Решение go/no-go

`GO` для generalized parser implementation.

Обоснование:

- Первый IR слой уже внедрён без регрессии ключевых WMF сборок.
- Есть явная точка расширения для rule-based assembly до fallback signatures.
- Введён machine-readable provenance для downstream диагностики parser path.

## 6. Следующий execution slice (P1-02)

Минимальный следующий slice:

1. Взять один residue-case (`904/пр` formula `(2)` или structural residue в `1/пр`).
2. Добавить rule-driven assembly на IR-токенах для этого класса.
3. Оставить known signatures как fallback.
4. Подтвердить uplift через focused benchmark rerun и update в `formula-summary`.
