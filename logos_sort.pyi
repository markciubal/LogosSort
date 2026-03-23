"""Type stubs for logos_sort — enables IDE autocomplete and mypy checking."""

from typing import Callable, TypeVar, overload

__version__: str

_T = TypeVar("_T")
_KT = TypeVar("_KT")

@overload
def logos_sort(arr: list[_T], *, key: None = None, reverse: bool = False) -> list[_T]: ...
@overload
def logos_sort(arr: list[_T], *, key: Callable[[_T], _KT], reverse: bool = False) -> list[_T]: ...

def logos_sort_inplace(
    arr: list[_T],
    *,
    key: Callable[[_T], _KT] | None = None,
    reverse: bool = False,
) -> None: ...
