from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any, Mapping


FORMULA_TARGET_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class FormulaEvaluationError(ValueError):
    pass


class MissingFormulaVariablesError(FormulaEvaluationError):
    def __init__(
        self,
        *,
        calc_expr: str,
        target: str | None,
        expression: str,
        missing_variables: tuple[str, ...],
    ) -> None:
        self.calc_expr = calc_expr
        self.target = target
        self.expression = expression
        self.missing_variables = missing_variables
        super().__init__(f"Missing formula variables: {', '.join(missing_variables)}")


@dataclass(frozen=True)
class FormulaEvaluationResult:
    calc_expr: str
    target: str | None
    expression: str
    value: float
    used_variables: dict[str, float]


@dataclass(frozen=True)
class DocumentFormulaEvaluationItem:
    unit_id: str
    unit_type: str
    order: int
    text: str | None
    calc_expr: str
    target: str | None
    expression: str
    status: str
    value: float | None
    used_variables: dict[str, float]
    missing_variables: tuple[str, ...]
    error: str | None


@dataclass(frozen=True)
class DocumentFormulaEvaluationResult:
    formula_units: int
    calc_expr_units: int
    evaluated_count: int
    missing_count: int
    error_count: int
    results: tuple[DocumentFormulaEvaluationItem, ...]


def evaluate_formula_expression(calc_expr: str, values: Mapping[str, Any]) -> FormulaEvaluationResult:
    target, expression, tree, variable_names = _parse_formula_expression(calc_expr)
    normalized_values = _normalize_values(values)
    missing_variables = tuple(name for name in variable_names if name not in normalized_values)
    if missing_variables:
        raise MissingFormulaVariablesError(
            calc_expr=calc_expr,
            target=target,
            expression=expression,
            missing_variables=missing_variables,
        )

    try:
        value = _evaluate_ast_node(tree.body, normalized_values)
    except ZeroDivisionError as exc:
        raise FormulaEvaluationError("Division by zero while evaluating formula expression.") from exc

    return FormulaEvaluationResult(
        calc_expr=calc_expr,
        target=target,
        expression=expression,
        value=value,
        used_variables={name: normalized_values[name] for name in variable_names},
    )


def evaluate_document_formulas(
    payload: Mapping[str, Any],
    values: Mapping[str, Any],
) -> DocumentFormulaEvaluationResult:
    raw_units = payload.get("units")
    if not isinstance(raw_units, list):
        raise FormulaEvaluationError("Document payload must contain a units array.")

    ordered_units = [unit for unit in raw_units if isinstance(unit, dict)]
    ordered_units.sort(key=lambda item: item.get("order", 0) if isinstance(item.get("order"), int) else 0)

    formula_units = 0
    pending: list[tuple[int, dict[str, Any], str]] = []
    for index, unit in enumerate(ordered_units):
        formula = unit.get("formula")
        if not isinstance(formula, dict):
            continue
        formula_units += 1
        calc_expr = formula.get("calc_expr")
        if isinstance(calc_expr, str) and calc_expr.strip():
            pending.append((index, unit, calc_expr))

    calc_expr_units = len(pending)
    evaluated_count = 0
    missing_count = 0
    error_count = 0
    available_values = _normalize_values(values)
    result_items: list[tuple[int, DocumentFormulaEvaluationItem]] = []

    while pending:
        progress = False
        next_pending: list[tuple[int, dict[str, Any], str]] = []

        for index, unit, calc_expr in pending:
            unit_id = _unit_string_value(unit, "unit_id")
            unit_type = _unit_string_value(unit, "type")
            order = _unit_order_value(unit)
            text = _unit_optional_string_value(unit, "text")

            try:
                evaluation = evaluate_formula_expression(calc_expr, available_values)
            except MissingFormulaVariablesError:
                next_pending.append((index, unit, calc_expr))
                continue
            except FormulaEvaluationError as exc:
                error_count += 1
                target, expression = _safe_formula_summary(calc_expr)
                result_items.append(
                    (
                        index,
                        DocumentFormulaEvaluationItem(
                            unit_id=unit_id,
                            unit_type=unit_type,
                            order=order,
                            text=text,
                            calc_expr=calc_expr,
                            target=target,
                            expression=expression,
                            status="error",
                            value=None,
                            used_variables={},
                            missing_variables=(),
                            error=str(exc),
                        ),
                    )
                )
                continue

            evaluated_count += 1
            progress = True
            if evaluation.target is not None:
                available_values[evaluation.target] = evaluation.value
            result_items.append(
                (
                    index,
                    DocumentFormulaEvaluationItem(
                        unit_id=unit_id,
                        unit_type=unit_type,
                        order=order,
                        text=text,
                        calc_expr=calc_expr,
                        target=evaluation.target,
                        expression=evaluation.expression,
                        status="ok",
                        value=evaluation.value,
                        used_variables=evaluation.used_variables,
                        missing_variables=(),
                        error=None,
                    ),
                )
            )

        if not progress:
            for index, unit, calc_expr in next_pending:
                unit_id = _unit_string_value(unit, "unit_id")
                unit_type = _unit_string_value(unit, "type")
                order = _unit_order_value(unit)
                text = _unit_optional_string_value(unit, "text")
                try:
                    evaluate_formula_expression(calc_expr, available_values)
                except MissingFormulaVariablesError as exc:
                    missing_count += 1
                    result_items.append(
                        (
                            index,
                            DocumentFormulaEvaluationItem(
                                unit_id=unit_id,
                                unit_type=unit_type,
                                order=order,
                                text=text,
                                calc_expr=calc_expr,
                                target=exc.target,
                                expression=exc.expression,
                                status="missing_variables",
                                value=None,
                                used_variables={},
                                missing_variables=exc.missing_variables,
                                error=None,
                            ),
                        )
                    )
                except FormulaEvaluationError as exc:
                    error_count += 1
                    target, expression = _safe_formula_summary(calc_expr)
                    result_items.append(
                        (
                            index,
                            DocumentFormulaEvaluationItem(
                                unit_id=unit_id,
                                unit_type=unit_type,
                                order=order,
                                text=text,
                                calc_expr=calc_expr,
                                target=target,
                                expression=expression,
                                status="error",
                                value=None,
                                used_variables={},
                                missing_variables=(),
                                error=str(exc),
                            ),
                        )
                    )
            break

        pending = next_pending

    result_items.sort(key=lambda item: item[0])
    results = tuple(result for _, result in result_items)

    return DocumentFormulaEvaluationResult(
        formula_units=formula_units,
        calc_expr_units=calc_expr_units,
        evaluated_count=evaluated_count,
        missing_count=missing_count,
        error_count=error_count,
        results=results,
    )


def _parse_formula_expression(calc_expr: str) -> tuple[str | None, str, ast.Expression, tuple[str, ...]]:
    normalized = calc_expr.strip()
    if not normalized:
        raise FormulaEvaluationError("Formula expression must not be empty.")

    target: str | None = None
    expression = normalized
    if "=" in normalized:
        left, right = (part.strip() for part in normalized.split("=", 1))
        if not left or not right:
            raise FormulaEvaluationError("Formula assignment must contain both target and expression.")
        if FORMULA_TARGET_RE.fullmatch(left) is None:
            raise FormulaEvaluationError(f"Unsupported formula target: {left}")
        target = left
        expression = right

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise FormulaEvaluationError(f"Invalid formula expression syntax: {expression}") from exc

    variable_names = tuple(sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}))
    _validate_expression_ast(tree)
    return target, expression, tree, variable_names


def _safe_formula_summary(calc_expr: str) -> tuple[str | None, str]:
    try:
        target, expression, _, _ = _parse_formula_expression(calc_expr)
    except FormulaEvaluationError:
        return None, calc_expr.strip()
    return target, expression


def _unit_string_value(unit: dict[str, Any], key: str) -> str:
    value = unit.get(key)
    return value if isinstance(value, str) else ""


def _unit_optional_string_value(unit: dict[str, Any], key: str) -> str | None:
    value = unit.get(key)
    return value if isinstance(value, str) else None


def _unit_order_value(unit: dict[str, Any]) -> int:
    value = unit.get("order")
    return value if isinstance(value, int) else 0


def _validate_expression_ast(tree: ast.Expression) -> None:
    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.Expression,
                ast.BinOp,
                ast.UnaryOp,
                ast.Name,
                ast.Load,
                ast.Constant,
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.Div,
                ast.Pow,
                ast.UAdd,
                ast.USub,
            ),
        ):
            continue
        raise FormulaEvaluationError(f"Unsupported node in formula expression: {type(node).__name__}")


def _normalize_values(values: Mapping[str, Any]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not key:
            raise FormulaEvaluationError("Formula variable names must be non-empty strings.")
        normalized[key] = _coerce_numeric_value(value)
    return normalized


def _coerce_numeric_value(value: Any) -> float:
    if isinstance(value, bool):
        raise FormulaEvaluationError("Boolean values are not supported for formula evaluation.")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip().replace(",", ".")
        if not normalized:
            raise FormulaEvaluationError("Formula variable values must not be empty strings.")
        try:
            return float(normalized)
        except ValueError as exc:
            raise FormulaEvaluationError(f"Unsupported numeric value: {value}") from exc
    raise FormulaEvaluationError(f"Unsupported variable value type: {type(value).__name__}")


def _evaluate_ast_node(node: ast.AST, values: Mapping[str, float]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.Name):
        return values[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _evaluate_ast_node(node.operand, values)
        return operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.BinOp):
        left = _evaluate_ast_node(node.left, values)
        right = _evaluate_ast_node(node.right, values)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
    raise FormulaEvaluationError(f"Unsupported node in formula expression: {type(node).__name__}")