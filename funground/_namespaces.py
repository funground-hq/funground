"""The base of f.COLORS and f.CONSTANTS (D-103, S-174): a fixed list of names whose values are plain strings.

``f.COLORS.TOMATO`` is the string ``"tomato"`` and ``f.CONSTANTS.CENTER`` is the string ``"center"``, so a
constant and the word it stands for are the same thing and every function that accepts the word accepts the constant.

A namespace is a class (CONSTANTS holds groups, each a namespace itself) that is never instantiated. Its names are written in the class body as ``NAME: Final = "word"``,
so an editor can list them and a type checker knows each one is that exact word. The metaclass below makes the class
read-only, iterable (it yields the words) and friendly about a misspelt name.
"""
from __future__ import annotations

import difflib
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

# The two names a ``from funground import *`` adds that are not functions (global_style.py leaves them out of its checks).
NAMESPACE_NAMES = ("COLORS", "CONSTANTS")


class _NamespaceMeta(type):
    """Makes a class a read-only, iterable list of ``NAME = "word"`` pairs."""

    _members: dict[str, Any]            # NAME -> the word (a str), or NAME -> a group (a namespace class)

    def __new__(mcs, name: str, bases: tuple[type, ...], body: dict[str, Any]):
        members = {key: value for key, value in body.items()
                   if not key.startswith("_") and (isinstance(value, (str, _NamespaceMeta)))}
        cls = super().__new__(mcs, name, bases, {**body, "_members": members})
        return cls

    def __call__(cls, *args: Any, **kwargs: Any):
        raise TypeError(f"f.{cls.__qualname__} is a list of names, not something to make. Write f.{cls.__qualname__}.<NAME>.")

    def __iter__(cls) -> Iterator[Any]:
        return iter(cls._members.values())

    def __len__(cls) -> int:
        return len(cls._members)

    def __contains__(cls, word: object) -> bool:
        return word in cls._members.values()

    def __repr__(cls) -> str:
        names = list(cls._members)
        shown = ", ".join(names) if len(names) <= 20 else f"{len(names)} names"
        return f"<f.{cls.__qualname__}: {shown}>"

    if not TYPE_CHECKING:               # type checkers would take these for "any name works"; they must flag a typo

        def __getattr__(cls, name: str):
            if name.startswith("_"):                         # tools such as inspect ask for dunder names
                raise AttributeError(name)
            members = cls._members
            close = difflib.get_close_matches(name.upper(), members, n=1, cutoff=0.6)
            hint = f" Did you mean {close[0]}?" if close else f" Names are written in capitals, such as {next(iter(members))}."
            raise AttributeError(f"f.{cls.__qualname__} has no name {name!r}.{hint}")

        def __setattr__(cls, name: str, value: Any) -> None:
            raise AttributeError(f"f.{cls.__qualname__} cannot be changed: its names are fixed. "
                                 "Use your own variable, for example my_red = ...")

        def __delattr__(cls, name: str) -> None:
            raise AttributeError(f"f.{cls.__qualname__} cannot be changed: its names are fixed.")
