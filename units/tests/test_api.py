"""Tests for the typed units API introduced in 0.2.0."""

import pytest
from sympy import Rational

from compareexpressions.expression_parsing import ExpressionParsingError, FeedbackTag
from compareexpressions.units import (
    CONVERSION_TO_BASE_SI,
    REVERTED_UNIT,
    SI_BASE_UNITS,
    SI_PREFIXES,
    UNIT_SETS,
    QuantityError,
    QuantityParams,
    QuantityParseError,
    QuantityTag,
    build_quantity_parser,
    parse_quantity,
    preprocess_quantity,
    units_in,
)


class TestQuantityParams:
    def test_defaults(self):
        params = QuantityParams()
        assert (params.strictness, params.legacy_preprocessing, params.unit_sets) == (
            "natural",
            False,
            frozenset({"SI", "common", "imperial"}),
        )

    def test_from_dict_maps_legacy_and_units_string(self):
        with pytest.deprecated_call():
            params = QuantityParams.from_dict(
                {"strictness": "legacy", "units_string": "SI imperial", "complexNumbers": True}
            )
        assert params.strictness == "natural" and params.legacy_preprocessing is True
        assert params.unit_sets == {"SI", "imperial"}
        assert params.complex_numbers is True

    def test_it_is_expression_params(self):
        from compareexpressions.expression_parsing import ExpressionParams

        assert isinstance(QuantityParams(), ExpressionParams)
        assert isinstance(QuantityParams().replace(simplify=True), QuantityParams)

    def test_unknown_strictness(self):
        with pytest.raises(ExpressionParsingError, match="strictness"):
            QuantityParams(strictness="lenient")


class TestData:
    def test_named_fields(self):
        metre = next(unit for unit in SI_BASE_UNITS if unit.name == "metre")
        assert (metre.symbol, metre.dimension, metre.alternatives, metre.plurals) == (
            "m",
            "length",
            ("meter",),
            ("metres", "meters"),
        )
        kilo = next(prefix for prefix in SI_PREFIXES if prefix.name == "kilo")
        assert (kilo.symbol, kilo.factor) == ("k", "(10**3)")

    def test_units_in_deduplicates_in_table_order(self):
        units = units_in(frozenset({"SI", "common"}))
        assert len(units) == len(set(units))
        assert units[: len(SI_BASE_UNITS)] == SI_BASE_UNITS
        assert set(units_in(frozenset({"imperial"}))) == set(UNIT_SETS["imperial"])

    def test_conversion_to_base_si(self):
        assert CONVERSION_TO_BASE_SI["metre"] == "metre"
        assert CONVERSION_TO_BASE_SI["kilometre"] == "((10**3)*metre)"
        assert CONVERSION_TO_BASE_SI["newton"] == "(metre*kilogram*second**(-2))"
        assert "kilokilometre" not in CONVERSION_TO_BASE_SI


class TestParser:
    def test_parsers_are_cached_per_unit_sets_and_strictness(self):
        sets = frozenset({"SI"})
        assert build_quantity_parser(sets, "strict") is build_quantity_parser(sets, "strict")
        assert build_quantity_parser(sets, "strict") is not build_quantity_parser(sets, "natural")

    def test_tags(self):
        quantity = parse_quantity("9.81 m/s^2", QuantityParams())
        assert QuantityTag.NUMBER in quantity.value.tags
        assert quantity.unit.tags == {QuantityTag.UNIT}


class TestPhysicalQuantity:
    def test_value_unit_and_si_forms(self):
        quantity = parse_quantity("5 km/h", QuantityParams())
        assert (quantity.value.content_string(), quantity.unit.content_string()) == ("5", "kilometre/hour")
        # The dimension keeps the unit's conversion factor (symbols are declared positive).
        assert str(quantity.dimension.simplify()) == "5*length/(18*time)"
        assert quantity.unit_factor == Rational(5, 18)
        assert str(quantity.standard_unit) == "metre/second"
        assert quantity.latex == r"5~\frac{\mathrm{kilometre}}{\mathrm{hour}}"

    def test_unit_only_and_value_only(self):
        assert parse_quantity("kg", QuantityParams()).value is None
        assert parse_quantity("2x", QuantityParams()).unit is None

    def test_reverted_unit_messages(self):
        quantity = parse_quantity("2 kg + 3", QuantityParams())
        assert {feedback.tag for _, feedback in quantity.messages} == {REVERTED_UNIT}
        # Known quirk (as in v0.1): the enclosing group is reported too, with garbled positions.
        message_id, feedback = quantity.messages[-1]
        assert message_id == f"response_REVERTED_UNIT_{len(quantity.messages) - 1}"
        assert feedback == FeedbackTag(REVERTED_UNIT, {"before": "2 ", "marked": "kg", "after": " + 3"})

    def test_strict_mode_rejects_natural_spellings(self):
        assert parse_quantity("2 metres", QuantityParams(strictness="strict")).unit is None
        assert parse_quantity("2 metres", QuantityParams(strictness="natural")).unit.content_string() == "metre"

    def test_parse_errors_are_quantity_errors(self):
        with pytest.raises(QuantityParseError) as info:
            parse_quantity("10 kg *", QuantityParams())
        assert isinstance(info.value, QuantityError) and isinstance(info.value, ValueError)


class TestPreprocessing:
    def test_same_shape_as_expression_preprocessing(self):
        assert preprocess_quantity("response", "5 μ s", QuantityParams()) == "5 micros"

    def test_legacy(self):
        with pytest.deprecated_call():
            legacy_params = QuantityParams(legacy_preprocessing=True)
        assert preprocess_quantity("response", "100Pa", legacy_params) == "100 Pa"
        assert preprocess_quantity("response", "newton*metre", legacy_params) == "newton metre"
