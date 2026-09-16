"""Physical quantities: unit data, parsing into value and unit, dimensional analysis.

Typical use::

    params = QuantityParams.from_dict(evaluation_params)
    quantity = parse_quantity("9.81 m/s^2", params)
    quantity.value, quantity.unit, quantity.dimension, quantity.standard_value

Extracted from compareExpressions; unit-like text read as part of a value is
reported as ``REVERTED_UNIT`` :class:`FeedbackTag` messages.
Previewing a response (LaTeX/SymPy rendering) is an app-layer concern and
lives in compareExpressions, not here.
"""

from .data import (
    ALL_UNITS,
    COMMON_UNITS,
    CONVERSION_TO_BASE_SI,
    IMPERIAL_UNITS,
    SI_BASE_UNITS,
    SI_DERIVED_UNITS,
    SI_PREFIXES,
    UNIT_SETS,
    VERY_COMMON_UNITS,
    BaseUnit,
    Prefix,
    Unit,
    units_in,
)
from .errors import QuantityError, QuantityParseError, UnitConversionError
from .feedback import FeedbackTag
from .params import QuantityParams, Strictness
from .parser import build_quantity_parser
from .preprocessing import preprocess_legacy, preprocess_quantity, transform_prefixes_to_standard
from .quantity import REVERTED_UNIT, PhysicalQuantity, parse_quantity
from .tags import QuantityTag

__all__ = [
    "ALL_UNITS",
    "COMMON_UNITS",
    "CONVERSION_TO_BASE_SI",
    "IMPERIAL_UNITS",
    "REVERTED_UNIT",
    "SI_BASE_UNITS",
    "SI_DERIVED_UNITS",
    "SI_PREFIXES",
    "UNIT_SETS",
    "VERY_COMMON_UNITS",
    "BaseUnit",
    "FeedbackTag",
    "PhysicalQuantity",
    "Prefix",
    "QuantityError",
    "QuantityParams",
    "QuantityParseError",
    "QuantityTag",
    "Strictness",
    "Unit",
    "UnitConversionError",
    "build_quantity_parser",
    "parse_quantity",
    "preprocess_legacy",
    "preprocess_quantity",
    "transform_prefixes_to_standard",
    "units_in",
]
