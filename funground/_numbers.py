"""The sentence for a number that cannot be used: nan or infinity (S-256, D-130).

The maintainer's wording: nan is not called a number, and the sentence does not guess how the value was made, because
funground sees only the value. This is not learner API.
"""
from __future__ import annotations


def unusable(name: str, value: float, where: str = "") -> str:
    """The sentence for *value*, which is nan or an infinity, given for *name* in the call *where*."""
    if value != value:
        what = '"not a number" (nan)'
    else:
        what = "infinity (inf)" if value > 0 else "minus infinity (-inf)"
    start = f"{where}: " if where else ""
    return f"{start}{name} came out as {what}, so it cannot be used. Check how {name} was worked out."
