"""Grammar and parser for criteria such as ``response = answer where a = 2``.

Criteria are equalities and orderings between expressions, optionally with
``where`` substitutions, plus ``written as``, ``proportional to`` and
``contains``. Names from the reserved expressions (``response``,
``answer``, ...) scan as ``RESERVED``; other text is ``OTHER``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from lambdafeedback.slr_parsing import (
    Action,
    SLRParser,
    TokenSpec,
    append_last,
    catch_undefined,
    create_node,
    infix,
    join,
    proceed,
)

START_SYMBOL = "START"
END_SYMBOL = "END"
NULL_SYMBOL = "NULL"

TOKENS: tuple[TokenSpec, ...] = (
    (START_SYMBOL, START_SYMBOL),
    (END_SYMBOL, END_SYMBOL),
    (NULL_SYMBOL, NULL_SYMBOL),
    (" *BOOL *", "BOOL"),
    (" *EQUALITY *", "EQUALITY"),
    (" *EQUAL *", "EQUAL"),
    (" *EQUAL_LIST *", "EQUAL_LIST"),
    (" *RESERVED *", "RESERVED"),
    (" *= *", "EQUALITY"),
    (" *(>=?|<=?|ORDER) *", "ORDER"),  # less than (or equal), < (<=), greater than (or equal), > (>=)
    (" *where *", "WHERE"),
    (" *written +as *", "WRITTEN_AS"),
    (" *proportional +to *", "PROPORTIONAL_TO"),
    (" *contains *", "CONTAINS"),
    (" *; *", "SEPARATOR"),
    (" *OTHER *", "OTHER", catch_undefined),
)

# Order matters: when productions conflict, the one listed later wins.
PRODUCTIONS: tuple[tuple[str, str, Action], ...] = (
    ("START", "BOOL", create_node),
    ("BOOL", "EQUAL", proceed),
    ("BOOL", "ORDER", proceed),
    ("BOOL", "EQUAL where EQUAL", infix),
    ("BOOL", "EQUAL where EQUAL_LIST", infix),
    ("BOOL", "RESERVED written as OTHER", infix),
    ("BOOL", "RESERVED written as RESERVED", infix),
    ("EQUAL", "OTHER proportional to OTHER", infix),
    ("EQUAL", "RESERVED proportional to OTHER", infix),
    ("EQUAL", "OTHER proportional to RESERVED", infix),
    ("EQUAL", "RESERVED proportional to RESERVED", infix),
    ("BOOL", "RESERVED contains OTHER", infix),
    ("BOOL", "RESERVED contains RESERVED", infix),
    ("EQUAL_LIST", "EQUAL;EQUAL", infix),
    ("EQUAL_LIST", "EQUAL_LIST;EQUAL", append_last),
    ("EQUAL", "OTHER = OTHER", infix),
    ("EQUAL", "RESERVED = OTHER", infix),
    ("EQUAL", "OTHER = RESERVED", infix),
    ("EQUAL", "RESERVED = RESERVED", infix),
    ("EQUAL", "OTHER ORDER OTHER", infix),
    ("EQUAL", "RESERVED ORDER OTHER", infix),
    ("EQUAL", "OTHER ORDER RESERVED", infix),
    ("EQUAL", "RESERVED ORDER RESERVED", infix),
    ("OTHER", "RESERVED OTHER", join),
    ("OTHER", "OTHER RESERVED", join),
    ("OTHER", "OTHER OTHER", join),
)


def build_criteria_parser(
    reserved_expressions: Mapping[str, Mapping[str, Any]],
    token_list: Sequence[TokenSpec] = TOKENS,
    productions: Sequence[tuple[str, str, Action | None]] = PRODUCTIONS,
) -> SLRParser:
    """A parser for criteria, where the keys of each reserved-expression group scan as ``RESERVED``.

    ``reserved_expressions`` maps groups (e.g. ``"learner"``, ``"task"``) to
    ``{name: expression}``; only the names are used here.
    """
    reserved = [(name, "RESERVED") for group in reserved_expressions.values() for name in group]
    return SLRParser([*token_list, *reserved], productions, START_SYMBOL, END_SYMBOL, NULL_SYMBOL)
