import pytest

from lambdafeedback.expression_parsing import generate_arbitrary_number_pattern_matcher


class TestGenerateArbitraryNumberPatternMatcher:
    @pytest.mark.parametrize(
        "pattern_string, matching_strings, non_matching_strings",
        [
            ("2x+3", ["2x+3", "5x+7"], ["2x-3", "2x+3+1"]),
            # Regression test: the text following the last matched number
            # (here the closing bracket ")") used to be inserted into the
            # generated regex unescaped and unwrapped, which could produce
            # an invalid pattern and raise `re.error: unbalanced parenthesis`.
            ("(2x-5)(3x+2)", ["(2x-5)(3x+2)", "(7x-1)(4x+9)"], ["(3x+2)(2x-5)", "3x^2-11x-10"]),
            ("(x-4)^2-5", ["(x-4)^2-5", "(x-6)^2-1"], ["(x-4)^2+5", "x^2-8x+11"]),
        ],
    )
    def test_matcher(self, pattern_string, matching_strings, non_matching_strings):
        matcher = generate_arbitrary_number_pattern_matcher(pattern_string)
        for matching_string in matching_strings:
            assert matcher(matching_string) is True
        for non_matching_string in non_matching_strings:
            assert matcher(non_matching_string) is False
