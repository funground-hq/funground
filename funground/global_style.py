"""The global style (D-088, S-176): sketches that start with ``from funground import *``.

Such a sketch calls ``circle(...)`` instead of ``f.circle(...)``, and reads ``width`` and ``mouse_x`` from its own
globals. Those are copies taken when the import ran, so funground writes the current values into the sketch's
globals before ``setup()``, before every ``draw()`` and event callback, and after the calls that change them
(``size()``, ``resize_canvas()``, ``full_screen()``, ``new_page()``, ``load_pixels()``). A sketch that did
``import funground as f`` holds none of funground's functions in its globals, so it is never touched: a variable
called ``width`` there stays the sketch's own.

A helper module imported by the sketch is not refreshed; it uses ``f.mouse_x`` (the guide says so).
"""
from __future__ import annotations

from typing import Any

Namespace = dict[str, Any]

_functions: frozenset[int] | None = None


def _funground_functions() -> frozenset[int]:
    """The identities of funground's public functions and classes (not the live values)."""
    global _functions
    if _functions is None:
        import funground

        from ._namespaces import NAMESPACE_NAMES
        from .api import LIVE_NAMES

        # COLORS and CONSTANTS are lists of words, not functions: a sketch that holds only them is not in this style.
        _functions = frozenset(id(getattr(funground, name)) for name in funground._PUBLIC_NAMES
                               if name not in LIVE_NAMES and name not in NAMESPACE_NAMES)
    return _functions


def uses_global_style(namespace: Namespace) -> bool:
    """True when the globals hold any of funground's own functions, as ``from funground import *`` leaves them.

    Any one is enough, so a sketch that defines its own ``circle()`` is still recognised."""
    functions = _funground_functions()
    return any(id(value) in functions for value in list(namespace.values()))


def live_names_in(namespace: Namespace) -> tuple[str, ...]:
    """The live names (width, mouse_x, ...) to keep current in these globals; none for an ``import funground as f``
    sketch."""
    from .api import LIVE_NAMES

    if not uses_global_style(namespace):
        return ()
    return tuple(name for name in sorted(LIVE_NAMES) if name in namespace)


def publish(namespace: Namespace, names: tuple[str, ...]) -> None:
    """Write the current value of each live name into the globals, as ``f.<name>`` would read it now."""
    from .api import live_value

    for name in names:
        namespace[name] = live_value(name)


def clash_note(namespace: Namespace) -> str | None:
    """A sentence for "'int' object is not callable" when the sketch's own variable hides a funground function.

    ``size = 40`` in a global-style sketch replaces funground's ``size()`` in that file; the call
    ``size(640, 400)`` then fails with Python's cryptic message. None when nothing is hidden."""
    import funground

    from ._namespaces import NAMESPACE_NAMES

    if not uses_global_style(namespace):
        return None
    hidden = sorted(name for name in funground.__all__
                    if name not in NAMESPACE_NAMES and name in namespace and callable(getattr(funground, name)) and not callable(namespace[name]))
    if not hidden:
        return None
    if len(hidden) == 1:
        name = hidden[0]
        return (f"Your sketch has a variable called {name}, which hides funground's {name}(). Give the variable "
                f"another name (for example my_{name}).")
    listed = ", ".join(hidden)
    return (f"Your sketch has variables called {listed}, which hide funground's functions of the same names. "
            f"Give the variables other names (for example my_{hidden[0]}).")


def left_out_note(name: str) -> str | None:
    """A sentence for "name 'random' is not defined": one of the four names the star leaves out."""
    import funground

    if name not in funground.STAR_NAMES_FOR:
        return None
    hidden = "Python's random module" if name == "random" else f"Python's own {name}()"
    return (f"funground's {name}() is not brought in by from funground import *, because it would hide {hidden}. "
            f"Write {funground.STAR_NAMES_FOR[name]}() instead: the same function.")


def explain_clash(error: BaseException, namespace: Namespace) -> None:
    """Add a sentence to a "not callable" TypeError, or to a NameError for a name the star leaves out."""
    if isinstance(error, TypeError) and "not callable" in str(error):
        note = clash_note(namespace)
    elif isinstance(error, NameError) and not isinstance(error, UnboundLocalError) and error.name:
        note = left_out_note(error.name) if uses_global_style(namespace) else None
    else:
        note = None
    if note is not None and note not in getattr(error, "__notes__", ()):
        error.add_note(note)
