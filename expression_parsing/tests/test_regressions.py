"""Regression tests for bugs carried over from the v0.1 extraction."""

import subprocess
import sys
import warnings

import pytest

from lambdafeedback.expression_parsing import (
    ExpressionParams,
    LatexParseError,
    SymbolAssumptionError,
    SympyParsingConfig,
    create_expression_set,
    parse_expression,
    parse_latex,
    substitute_input_symbols,
    sympy_to_latex,
)


def parsing_params(**overrides):
    return SympyParsingConfig.from_params(ExpressionParams.from_dict(overrides))


class TestSymbolAssumptions:
    def test_assumption_tuples_are_not_executed(self):
        injected = "(__import__('sys').modules.__setitem__('pwned_by_assumptions', 1), 'positive')"
        with pytest.raises(ValueError):
            parsing_params(symbol_assumptions=injected)
        assert "pwned_by_assumptions" not in sys.modules

    def test_assumption_names_must_be_identifiers(self):
        with pytest.raises(SymbolAssumptionError, match="positive=True") as info:
            parsing_params(symbol_assumptions="('x', 'positive=True')")
        assert (info.value.symbol, info.value.assumption) == ("x", "positive=True")

    def test_valid_assumptions_still_apply(self):
        params = parsing_params(symbol_assumptions="('a','positive') ('f','function') ('c','constant')")
        assert params.symbol_dict["a"].is_positive
        assert params.symbol_dict["f"](1).func.__name__ == "f"
        assert "c" in params.constants


class TestParsing:
    def test_capital_e_after_implicit_multiplication(self):
        # Fixed in slr_parsing (the convention parser scanned "E" as a grammar symbol).
        assert str(parse_expression("2E", parsing_params())) == "2*E"
        assert str(parse_expression("xE", parsing_params())) == "E*x"

    def test_chained_equalities_are_rejected(self):
        with pytest.raises(ValueError, match="="):
            parse_expression("a=b=c", parsing_params())

    def test_arithmetic_on_sets_is_rejected_in_strict_syntax(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with pytest.raises(ValueError, match="set"):
                parse_expression("{x+1}*{x-1}", parsing_params(strict_syntax=True))

    def test_parsing_params_default_missing_keys(self):
        assert SympyParsingConfig.from_params(ExpressionParams.from_dict({})).complex_numbers is False

    def test_lone_plus_minus(self):
        assert sorted(create_expression_set("plus_minus", ExpressionParams())) == ["", "-"]


class TestInputSymbols:
    def test_user_defined_lambda_survives_repeated_substitution(self):
        params = ExpressionParams.from_dict({"symbols": {"lambda": {"latex": r"\Lambda_0", "aliases": ["lam"]}}})
        assert substitute_input_symbols(["lam"], params) == ["lamda"]
        assert substitute_input_symbols(["lam"], params) == ["lamda"]

    def test_empty_aliases_do_not_remove_real_ones(self):
        params = ExpressionParams.from_dict({"symbols": {"x": {"latex": "x", "aliases": ["", "", "xx"]}}})
        assert substitute_input_symbols(["xx"], params) == ["x"]

    def test_aliases_are_stripped(self):
        params = ExpressionParams.from_dict({"symbols": {"x": {"latex": "x", "aliases": [" xx "]}}})
        assert substitute_input_symbols(["xx"], params) == ["x"]


class TestNoSideEffects:
    def test_sympy_to_latex_does_not_mutate_settings(self):
        settings = {"mul_symbol": r" \cdot "}
        sympy_to_latex(parse_expression("2x", parsing_params()), {}, settings=settings)
        assert settings == {"mul_symbol": r" \cdot "}

    def test_parse_latex_reports_errors_cleanly(self, capsys):
        parse_latex("x", ExpressionParams.from_dict({"symbols": {"x": {"latex": "x", "aliases": ["1+"]}}}).symbols)
        assert capsys.readouterr().out == ""
        with pytest.raises(ValueError) as info:
            parse_latex(r"\frac{x", {})
        assert len(info.value.args) == 1


class TestSanitiseLatex:
    def test_unclosed_wrapper_raises_instead_of_hanging(self):
        # Run in a subprocess: the v0.1 code loops forever on this input.
        script = (
            "from lambdafeedback.expression_parsing import LatexParseError, sanitise_latex\n"
            "try:\n"
            "    sanitise_latex(r'3 \\mathrm{kg')\n"
            "except LatexParseError as e:\n"
            "    print('raised:', e, e.wrapper, e.response)\n"
        )
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=30)
        assert result.stdout.startswith(r"raised: Unclosed \mathrm{")
        assert result.stdout.strip().endswith(r"\mathrm 3\mathrm{kg")


class TestLatexEquations:
    def test_equation_parses_to_eq_on_any_latex2sympy_build(self):
        # PyPI's latex2sympy2 reads "x = 2" as an assignment (returning 2); the
        # lambda-feedback fork compareExpressions uses returns Eq(x, 2).
        assert parse_latex("x = 2", {}) == "Eq(x, 2)"
        assert parse_latex(r"\frac{x}{2} = y + 1", {}) == "Eq(x/2, y + 1)"

    def test_more_than_one_equals_sign_is_rejected(self):
        with pytest.raises(LatexParseError, match="=") as info:
            parse_latex("x = y = 2", {})
        assert info.value.expression == "x = y = 2"
