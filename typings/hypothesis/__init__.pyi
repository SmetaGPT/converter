from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from . import strategies as strategies

_P = ParamSpec("_P")
_R = TypeVar("_R")


def given(*args: Any, **kwargs: Any) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...


class settings:
    def __init__(self, **kwargs: Any) -> None: ...
    def __call__(self, func: Callable[_P, _R]) -> Callable[_P, _R]: ...
