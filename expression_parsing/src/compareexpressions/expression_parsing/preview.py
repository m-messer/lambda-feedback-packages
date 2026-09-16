"""Previewing a learner's response: LaTeX and SymPy renderings of what was typed."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, NotRequired, TypedDict

from sympy import Basic
from sympy.parsing.sympy_parser import T as TRANSFORMATIONS

from .errors import AbsoluteValueNotationError, BracketNotationError, ExpressionParsingError, ExpressionSyntaxError
from .feedback import FeedbackTag, FeedbackTagName
from .latex import parse_latex, sympy_to_latex
from .params import ExpressionParams, as_params
from .preprocessing import convert_absolute_notation, create_expression_set, preprocess_expression
from .substitution import substitute_input_symbols
from .sympy_parsing import SympyParsingConfig, parse_expression, sympy_symbols


class Preview(TypedDict):
    """Structurally compatible with ``lf_toolkit.preview.Preview`` (whose ``feedback`` is required)."""

    latex: str
    sympy: str
    feedback: NotRequired[str]


class Result(TypedDict):
    """Structurally compatible with ``lf_toolkit.preview.Result``."""

    preview: Preview


def parse_symbolic(response: str, params: ExpressionParams) -> tuple[list[Basic | set[Basic]], list[FeedbackTag]]:
    """Parse a (preprocessed) response into SymPy expressions, one per expression it stands for.

    Also returns the feedback raised while converting ``|...|`` notation.
    Raises :class:`ExpressionSyntaxError` (with ``PARSE_ERROR`` feedback)
    when an expression can't be parsed.
    """
    responses = []
    feedback: list[FeedbackTag] = []
    for expression in create_expression_set(response, params):
        expression = substitute_input_symbols([expression.strip()], params)[0]
        try:
            expression = convert_absolute_notation(expression, "response")
        except AbsoluteValueNotationError as exc:
            feedback.append(FeedbackTag(FeedbackTagName.ABSOLUTE_VALUE_NOTATION_AMBIGUITY, {"name": exc.name}))
            expression = exc.expression
        responses.append(expression)

    config = SympyParsingConfig.from_params(params)
    config = config.replace(
        extra_transformations=TRANSFORMATIONS[9],  # convert equals signs
        symbol_dict={**config.symbol_dict, **sympy_symbols(params.symbols)},
    )
    parsed = []
    for expression in responses:
        try:
            parsed.append(parse_expression(expression, config))
        except Exception as exc:
            raise ExpressionSyntaxError(FeedbackTag(FeedbackTagName.PARSE_ERROR, {"response": expression})) from exc
    return parsed, feedback


def preview_function(response: str, params: ExpressionParams | Mapping[str, Any]) -> Result:
    """Preview a learner's response as LaTeX and SymPy syntax.

    ``params`` may be :class:`ExpressionParams` or evaluation-function
    parameters. Each side of an ``=`` is previewed separately; a response
    standing for several expressions (``{a, b}``, ``±``) previews as a set.
    Raises :class:`ExpressionParsingError` if the response can't be parsed.
    """
    params = as_params(params)
    if not response:
        return Result(preview=Preview(latex="", sympy=""))

    latex_parts = []
    sympy_parts = []
    for part in response.split("="):
        try:
            if params.is_latex:
                latex_out = [part]
                sympy_out = [parse_latex(part, params.symbols, params.simplify)]
            else:
                symbolic_params = params.replace(rationalise=False)
                try:
                    preprocessed = preprocess_expression("response", part, symbolic_params)
                except (BracketNotationError, AbsoluteValueNotationError) as exc:
                    preprocessed = exc.expression
                expressions, _ = parse_symbolic(preprocessed, symbolic_params)
                latex_out = sorted(
                    sympy_to_latex(expression, params.symbols, settings={"mul_symbol": r" \cdot "})
                    for expression in expressions
                )
                sympy_out = [preprocessed]
        except ExpressionSyntaxError as exc:
            raise ExpressionParsingError(f"Failed to parse SymPy expression: {response}") from exc
        except ValueError as exc:
            raise ExpressionParsingError(f"Failed to parse LaTeX expression: {response}") from exc

        sympy_parts.append(sympy_out[0] if len(sympy_out) == 1 else str(sympy_out))
        latex_parts.append(latex_out[0] if len(latex_out) == 1 else "\\left\\{" + ",~".join(latex_out) + "\\right\\}")

    return Result(preview=Preview(latex="=".join(latex_parts), sympy="=".join(sympy_parts)))
