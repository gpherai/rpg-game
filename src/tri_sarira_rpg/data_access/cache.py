"""Cache-hulpmiddelen voor data-layer."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """Zeer eenvoudige memoize-decorator voor dure loaderfuncties."""

    cache: dict[tuple, T] = {}

    def wrapper(*args) -> T:
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return wrapper


__all__ = ["memoize"]
