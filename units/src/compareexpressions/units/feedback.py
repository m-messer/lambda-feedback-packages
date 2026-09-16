"""Feedback surfaced while splitting a quantity into value and unit.

This package doesn't carry compareExpressions' feedback text: it returns a
:class:`FeedbackTag`, the tag plus the inputs needed to render it. The
consumer owns the tag -> text mapping.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FeedbackTag:
    """A feedback tag and the inputs needed to render its text."""

    tag: str
    inputs: Mapping[str, Any] = field(default_factory=dict)
