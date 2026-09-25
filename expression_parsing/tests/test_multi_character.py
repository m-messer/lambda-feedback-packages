import pytest

from lambdafeedback.expression_parsing import ExpressionParams, SympyParsingConfig, parse_expression


class TestMultiCharImplicitMultiHigherPrecedenceIntegration:
    """
    Integration tests for multi-characters symbols and the convention of implicit_higher_precedence enabled.
    """

    def assert_expression_equality(self, response, answer, symbols_dict, local_dict=None):
        """
        Helper to parse both response and answer with the same parameters
        and assert they result in equivalent SymPy expressions.
        """
        if local_dict is None:
            local_dict = {}

        # define parameters
        params = {
            "complexNumbers": False,
            "strict_syntax": False,
            "elementary_functions": True,
            "convention": "implicit_higher_precedence",
            "symbols": symbols_dict,
        }

        parsing_params = SympyParsingConfig.from_params(ExpressionParams.from_dict(params))

        try:
            parsed_response = parse_expression(response, parsing_params)
            parsed_answer = parse_expression(answer, parsing_params)
        except Exception as e:
            pytest.fail(f"Parsing failed for input '{response}' or '{answer}': {e!s}")

        assert parsed_response == parsed_answer, (
            f"\nInput:    {response}\nExpected: {parsed_answer}\nGot:      {parsed_response}"
        )

    def test_multi_character_implicit_multi_variable(self):
        symbols = {"a": {"aliases": ["a"]}, "bc": {"aliases": ["bc"]}, "d": {"aliases": ["d"]}}
        answer = "a/(bc*d)"

        # Case 1: Full explicit
        self.assert_expression_equality("a/(bc*d)", answer, symbols)

        # Case 2: Implicit with brackets
        self.assert_expression_equality("a/(bcd)", answer, symbols)

        # Case 3: Implicit no brackets
        self.assert_expression_equality("a/bcd", answer, symbols)

    def test_multiple_divisions_with_implicit(self):
        """Test multiple divisions in sequence"""
        symbols = {
            "a": {"aliases": ["a"]},
            "b": {"aliases": ["b"]},
            "c": {"aliases": ["c"]},
            "d": {"aliases": ["d"]},
            "f": {"aliases": ["f"]},
        }

        answer = "a/(b*c)/(d*f)"
        response = "a/bc/df"
        self.assert_expression_equality(response, answer, symbols)

    def test_addition_with_division_and_implicit(self):
        """Test that addition doesn't interfere"""
        symbols = {"a": {"aliases": ["a"]}, "b": {"aliases": ["b"]}, "c": {"aliases": ["c"]}, "d": {"aliases": ["d"]}}
        answer = "a/(b*c) + d"
        response = "a/bc + d"
        self.assert_expression_equality(response, answer, symbols)

    def test_multiplication_after_division(self):
        """Test explicit multiplication after division"""
        symbols = {"a": {"aliases": ["a"]}, "b": {"aliases": ["b"]}, "c": {"aliases": ["c"]}, "d": {"aliases": ["d"]}}

        answer = "(a/(b*c))*d"
        response = "a/bc*d"
        self.assert_expression_equality(response, answer, symbols)

    def test_power_with_implicit_multiplication(self):
        symbols = {
            "a": {"aliases": ["a"]},
            "b": {"aliases": ["b"]},
            "c": {"aliases": ["c"]},
        }
        answer = "a/(b**2*c)"
        response = "a/b^2c"
        self.assert_expression_equality(response, answer, symbols)

    def test_longer_multi_character_symbols(self):
        symbols = {
            "x": {"aliases": ["x"]},
            "abc": {"aliases": ["abc"]},
            "df": {"aliases": ["df"]},
        }
        answer = "x/(abc*df)"
        test_cases = [
            "x/(abc*df)",
            "x/(abcdf)",
            "x/abcdf",
        ]
        for response in test_cases:
            self.assert_expression_equality(response, answer, symbols)

    def test_overlapping_symbol_names(self):
        symbols = {
            "a": {"aliases": ["a"]},
            "ab": {"aliases": ["ab"]},
            "abc": {"aliases": ["abc"]},
            "c": {"aliases": ["c"]},
        }
        answer = "a/(abc*c)"
        response = "a/abcc"
        self.assert_expression_equality(response, answer, symbols)

    def test_numbers_with_implicit_multiplication(self):
        """Test with numeric literals"""
        symbols = {
            "a": {"aliases": ["a"]},
            "b": {"aliases": ["b"]},
        }

        answer = "a/(2*b)"
        response = "a/2b"
        self.assert_expression_equality(response, answer, symbols)

    def test_number_variable_number(self):
        """Test number followed by variable followed by number"""
        symbols = {
            "x": {"aliases": ["x"]},
        }

        answer = "1/(2*x*3)"
        response = "1/2x3"
        self.assert_expression_equality(response, answer, symbols)

    def test_implicit_before_parentheses(self):
        """Test implicit multiplication before parentheses"""
        symbols = {
            "a": {"aliases": ["a"]},
            "b": {"aliases": ["b"]},
            "c": {"aliases": ["c"]},
            "d": {"aliases": ["d"]},
        }

        answer = "a*(b*c*d)"
        response = "a(bcd)"
        self.assert_expression_equality(response, answer, symbols)

    def test_implicit_before_parentheses_with_multichar(self):
        """Test implicit multiplication before parentheses with multi-char symbols"""
        symbols = {
            "a": {"aliases": ["a"]},
            "bc": {"aliases": ["bc"]},
            "d": {"aliases": ["d"]},
        }

        answer = "a*(bc*d)"
        response = "a(bcd)"
        self.assert_expression_equality(response, answer, symbols)

    def test_complex_expression(self):
        """Test a complex expression"""
        symbols = {
            "a": {"aliases": ["a"]},
            "b": {"aliases": ["b"]},
            "c": {"aliases": ["c"]},
            "d": {"aliases": ["d"]},
            "f": {"aliases": ["f"]},
            "g": {"aliases": ["g"]},
        }
        answer = "a/(b*c) + d/(g*f)"
        response = "a/bc + d/gf"
        self.assert_expression_equality(response, answer, symbols)

    def test_three_way_implicit_multiplication(self):
        """Test three or more implicitly multiplied terms"""
        symbols = {
            "a": {"aliases": ["a"]},
            "b": {"aliases": ["b"]},
            "c": {"aliases": ["c"]},
            "d": {"aliases": ["d"]},
            "f": {"aliases": ["f"]},
        }
        answer = "a/(b*c*d*f)"
        response = "a/bcdf"
        self.assert_expression_equality(response, answer, symbols)

    def test_explicit_multiplication_should_not_be_grouped(self):
        """Test that explicit multiplication maintains standard precedence"""
        symbols = {
            "a": {"aliases": ["a"]},
            "b": {"aliases": ["b"]},
            "c": {"aliases": ["c"]},
        }
        answer = "(a/b)*c"
        response = "a/b*c"
        self.assert_expression_equality(response, answer, symbols)

    def test_mixed_implicit_and_explicit(self):
        """Test mixing implicit and explicit multiplication"""
        symbols = {
            "a": {"aliases": ["a"]},
            "b": {"aliases": ["b"]},
            "c": {"aliases": ["c"]},
            "d": {"aliases": ["d"]},
        }
        answer = "(a/(b*c))*d"
        response = "a/bc*d"
        self.assert_expression_equality(response, answer, symbols)
