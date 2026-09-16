"""SymPy-based expression parsing, preprocessing and LaTeX preview.

Typical use::

    params = ExpressionParams.from_dict(evaluation_params)
    expr = preprocess_expression("response", response, params)
    parsed = parse_expression(expr, SympyParsingConfig.from_params(params))
    latex = sympy_to_latex(parsed, params.symbols)

or ``preview_function(response, evaluation_params)`` for a preview.

Extracted from compareExpressions and decoupled from its feedback strings:
feedback is surfaced as :class:`FeedbackTag`.
"""

from .conventions import apply_convention, convention_parser
from .errors import (
    AbsoluteValueNotationError,
    BracketNotationError,
    ExpressionParsingError,
    ExpressionSyntaxError,
    LatexParseError,
    SymbolAssumptionError,
    UnknownConventionError,
)
from .feedback import FeedbackTag, FeedbackTagName
from .latex import extract_latex, latex_symbols, parse_latex, sanitise_latex, sympy_to_latex
from .numbers import (
    PATTERNS,
    SyntacticalPattern,
    compute_relative_tolerance_from_significant_decimals,
    generate_arbitrary_number_pattern_matcher,
    is_number,
)
from .params import Convention, ExpressionParams, SymbolSpec, parse_symbol_assumptions
from .preprocessing import (
    convert_absolute_notation,
    convert_bracket_notation,
    create_expression_set,
    find_matching_parenthesis,
    has_matching_brackets,
    is_multiple_answers_wrapper,
    preprocess_expression,
)
from .preview import Preview, Result, parse_symbolic, preview_function
from .substitution import substitute, substitute_input_symbols, substitutions_sort_key
from .sympy_parsing import SympyParsingConfig, parse_expression, sympy_symbols

__all__ = [
    "PATTERNS",
    "AbsoluteValueNotationError",
    "BracketNotationError",
    "Convention",
    "ExpressionParams",
    "ExpressionParsingError",
    "ExpressionSyntaxError",
    "FeedbackTag",
    "FeedbackTagName",
    "LatexParseError",
    "Preview",
    "Result",
    "SymbolAssumptionError",
    "SymbolSpec",
    "SympyParsingConfig",
    "SyntacticalPattern",
    "UnknownConventionError",
    "apply_convention",
    "compute_relative_tolerance_from_significant_decimals",
    "convention_parser",
    "convert_absolute_notation",
    "convert_bracket_notation",
    "create_expression_set",
    "extract_latex",
    "find_matching_parenthesis",
    "generate_arbitrary_number_pattern_matcher",
    "has_matching_brackets",
    "is_multiple_answers_wrapper",
    "is_number",
    "latex_symbols",
    "parse_expression",
    "parse_latex",
    "parse_symbol_assumptions",
    "parse_symbolic",
    "preprocess_expression",
    "preview_function",
    "sanitise_latex",
    "substitute",
    "substitute_input_symbols",
    "substitutions_sort_key",
    "sympy_symbols",
    "sympy_to_latex",
]
