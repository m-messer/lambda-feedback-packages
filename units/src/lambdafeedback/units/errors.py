"""Exceptions raised by the units package."""


class QuantityError(ValueError):
    """Base class for errors raised by the units package."""


class QuantityParseError(QuantityError):
    """A response could not be read as a physical quantity."""


class UnitConversionError(QuantityError):
    """A quantity's unit could not be converted to SI base units."""
