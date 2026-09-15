"""Typed parameters for physical quantities."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Self, get_args

from compareexpressions.expression_parsing import ExpressionParams, ExpressionParsingError

from .data import UNIT_SETS

Strictness = Literal["strict", "natural"]
"""``strict``: only unit names and symbols, units separated by ``*`` / ``/`` / spaces;
``natural`` also accepts alternative spellings and plurals, and units written together."""


@dataclass(frozen=True)
class QuantityParams(ExpressionParams):
    """:class:`ExpressionParams` plus how quantities (value and unit) are read."""

    strictness: Strictness = "natural"
    legacy_preprocessing: bool = False
    """Deprecated: rewrite the response the way the old ``legacy`` strictness did (natural otherwise)."""
    unit_sets: frozenset[str] = frozenset(UNIT_SETS)
    """Names from :data:`~compareexpressions.units.data.UNIT_SETS` whose units are recognised."""

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.strictness not in get_args(Strictness):
            raise ExpressionParsingError(f"Unknown strictness {self.strictness!r}.")
        object.__setattr__(self, "unit_sets", frozenset(self.unit_sets))
        if self.legacy_preprocessing:
            warnings.warn(
                "legacy_preprocessing is deprecated; use strictness='natural' (the default) instead.",
                DeprecationWarning,
                stacklevel=3,
            )

    @classmethod
    def from_dict(cls, params: Mapping[str, Any]) -> Self:
        """Build from evaluation-function parameters.

        ``strictness: "legacy"`` (deprecated) means natural strictness with
        legacy preprocessing; ``units_string`` names the unit sets (any of
        ``"SI"``, ``"common"``, ``"imperial"`` it contains).
        """
        values = dict(params)
        if values.get("strictness") == "legacy":
            values["strictness"] = "natural"
            values["legacy_preprocessing"] = True
        units_string = values.pop("units_string", None)
        if units_string is not None:
            values["unit_sets"] = frozenset(name for name in UNIT_SETS if name in units_string)
        return super().from_dict(values)
