"""Rewriting quantity responses before parsing."""

from __future__ import annotations

import re
from collections.abc import Callable
from functools import cache

from compareexpressions.expression_parsing import Preprocessed

from .data import ALL_UNITS, SI_PREFIXES
from .params import QuantityParams


def preprocess_quantity(name: str, expr: str, params: QuantityParams) -> Preprocessed:
    """Normalise prefix spellings (or apply the legacy rewrites); never raises feedback.

    Same shape as ``expression_parsing.preprocess_expression``, so either can
    serve as a context's preprocessing step. ``name`` is unused.
    """
    if params.legacy_preprocessing:
        return Preprocessed(preprocess_legacy(expr))
    return Preprocessed(transform_prefixes_to_standard(expr))


def _rewrite_all(pattern: re.Pattern[str], expr: str, rewrite: Callable[[str, re.Match[str]], str]) -> str:
    """Apply ``rewrite`` at the first match of ``pattern`` until nothing matches."""
    while (match := pattern.search(expr)) is not None:
        expr = rewrite(expr, match)
    return expr


def _alternation(forms: list[str]) -> str:
    return "(" + "|".join(re.escape(form) for form in forms) + ")"


@cache
def _legacy_patterns() -> dict[str, re.Pattern[str]]:
    prefixes = [form for prefix in SI_PREFIXES for form in (prefix.name, *prefix.alternatives)]
    prefix_symbols = [prefix.symbol for prefix in SI_PREFIXES]
    unit_symbols = [unit.symbol for unit in ALL_UNITS]
    long_forms = _alternation(
        [*prefixes, *(form for unit in ALL_UNITS for form in (unit.name, *unit.alternatives, *unit.plurals))]
    )
    return {
        "star_before_unit": re.compile(r"(?<!\*)\* *" + long_forms),
        "spaced_prefix": re.compile(_alternation(prefixes) + " " + long_forms),
        "glued_symbol": re.compile(r"[0-9\*\(\)]" + _alternation(list(dict.fromkeys(prefix_symbols + unit_symbols)))),
        "spaced_prefix_symbol": re.compile(r"[0-9\*\(\) ]" + _alternation(prefix_symbols) + " "),
        "starred_prefix_symbol": re.compile(r"[0-9\*\(\) ]" + _alternation(prefix_symbols) + r"\* "),
        "star_before_symbol": re.compile(r"[0-9\(\) ]\* " + _alternation(unit_symbols)),
    }


def preprocess_legacy(expr: str) -> str:
    """The rewrites of the old ``legacy`` strictness, applied in order."""
    patterns = _legacy_patterns()

    # "newton*metre" -> "newton metre": "*UNIT" (but not "**UNIT") becomes " UNIT", after the first character
    pattern = patterns["star_before_unit"]
    while (match := pattern.search(expr[1:])) is not None:
        start, end = match.span()
        expr = expr[: start + 1] + match.group().replace("*", " ") + expr[end + 1 :]

    # "kilo metre" -> "kilometre"
    expr = _rewrite_all(
        patterns["spaced_prefix"], expr, lambda s, m: s[: m.start()] + " " + "".join(m.group().split()) + s[m.end() :]
    )
    # "100Pa" -> "100 Pa": space before a prefix or unit symbol after a digit, '*' or bracket
    expr = _rewrite_all(patterns["glued_symbol"], expr, lambda s, m: s[: m.start() + 1] + " " + s[m.start() + 1 :])
    # "100 m Pa" -> "100 mPa"
    expr = _rewrite_all(
        patterns["spaced_prefix_symbol"], expr, lambda s, m: s[: m.start() + 1] + m.group()[:-1] + s[m.end() :]
    )
    # "100 m* Pa" -> "100 mPa"
    expr = _rewrite_all(
        patterns["starred_prefix_symbol"], expr, lambda s, m: s[: m.start() + 1] + m.group()[:-2] + s[m.end() :]
    )
    # "100* Pa" -> "100 Pa"
    return _rewrite_all(
        patterns["star_before_symbol"], expr, lambda s, m: s[: m.start()] + m.group().replace("*", " ") + s[m.end() :]
    )


def transform_prefixes_to_standard(expr: str) -> str:
    """Rewrite alternative prefix spellings (``deka``, ``μ``, ...) as standard names, and collapse spaces.

    Works whether the prefix is attached to the unit (``μs``) or spaced from
    it (``μ s``).
    """
    for prefix in SI_PREFIXES:
        for alternative in prefix.alternatives:
            expr = re.sub(rf"(?<!\w){re.escape(alternative)}\s*(?=[A-Za-zµΩ])", prefix.name, expr)
    return re.sub(r"\s{2,}", " ", expr).strip()
