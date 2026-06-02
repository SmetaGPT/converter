from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

type FormulaAssignmentCase = tuple[str, str, str]
type TableTextCase = tuple[str, int, int]

_IDENTIFIER_BASES = ("A", "B", "C", "K", "S", "З", "Н", "К", "С", "Т")
_IDENTIFIER_SCRIPTS = ("", "_(п)", "_(общ)", "_(i)", "_(1)", "_(факт)")
_TABLE_CELLS = ("A", "B", "C", "10", "20", "Колонка", "Значение", "Примечание")


def formula_identifier_texts() -> SearchStrategy[str]:
    return st.builds(
        lambda base, script: f"{base}{script}",
        st.sampled_from(_IDENTIFIER_BASES),
        st.sampled_from(_IDENTIFIER_SCRIPTS),
    )


def formula_assignment_texts() -> SearchStrategy[FormulaAssignmentCase]:
    return st.builds(
        lambda target, left, operator, right: (f"{target} = {left} {operator} {right}", target, left),
        formula_identifier_texts(),
        formula_identifier_texts(),
        st.sampled_from(("+", "-", "×", "÷", "x")),
        formula_identifier_texts() | st.integers(min_value=1, max_value=999).map(str),
    )


def table_cell_texts() -> SearchStrategy[str]:
    return st.sampled_from(_TABLE_CELLS)


def rectangular_table_texts(*, min_width: int = 2, max_width: int = 5, min_rows: int = 2, max_rows: int = 6) -> SearchStrategy[TableTextCase]:
    return st.integers(min_value=min_width, max_value=max_width).flatmap(
        lambda width: st.lists(
            st.lists(table_cell_texts(), min_size=width, max_size=width),
            min_size=min_rows,
            max_size=max_rows,
        ).map(lambda rows: ("\n".join("  ".join(row) for row in rows), width, len(rows)))
    )
