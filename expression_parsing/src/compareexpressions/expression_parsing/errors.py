"""Exceptions raised by the expression_parsing package."""

from __future__ import annotations

from .feedback import FeedbackTag


class ExpressionParsingError(ValueError):
    """An expression or its parsing parameters could not be parsed."""

    def __init__(self, text: str, *, expression: str | None = None) -> None:
        super().__init__(text)
        self.expression = expression


class UnknownConventionError(ExpressionParsingError):
    """``convention`` is not one of the recognised implicit-multiplication conventions."""

    def __init__(self, convention: str) -> None:
        super().__init__(f"Unknown convention {convention!r}.")
        self.convention = convention


class SymbolAssumptionError(ExpressionParsingError):
    """A ``symbol_assumptions`` parameter is malformed or names an invalid assumption.

    ``text`` is the raw offending substring (when the parameter as a whole was
    malformed); ``symbol``/``assumption`` identify a specific bad pair.
    """

    def __init__(
        self, message: str, *, text: str | None = None, symbol: str | None = None, assumption: str | None = None
    ) -> None:
        super().__init__(message)
        self.text = text
        self.symbol = symbol
        self.assumption = assumption


class LatexParseError(ExpressionParsingError):
    """A LaTeX expression (or a symbol's LaTeX) could not be parsed."""

    def __init__(
        self,
        text: str,
        *,
        symbol: str | None = None,
        expression: str | None = None,
        response: str | None = None,
        wrapper: str | None = None,
    ) -> None:
        super().__init__(text)
        self.symbol = symbol
        self.expression = expression
        self.response = response
        self.wrapper = wrapper


class ExpressionSyntaxError(ExpressionParsingError):
    """A response could not be parsed; ``feedback`` is the tag to show the learner."""

    def __init__(self, feedback: FeedbackTag) -> None:
        super().__init__(f"{feedback.tag}: {dict(feedback.inputs)}")
        self.feedback = feedback
