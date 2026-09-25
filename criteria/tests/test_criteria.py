"""Native tests for the criteria package.

compareExpressions exercises the criteria parser/graph only through its core
evaluation tests, so these are written fresh to cover the DSL parser labels and
the CriteriaGraph structure directly.
"""

import json

import pytest

from lambdafeedback.criteria import CriteriaGraph, CriteriaGraphError, build_criteria_parser

RESERVED = {"learner": {"response": None}, "task": {"answer": None}}


def _parse(criterion):
    parser = build_criteria_parser(RESERVED)
    return parser.parse(parser.scan(criterion))[0]


class TestCriteriaParser:
    @pytest.mark.parametrize(
        "criterion, label",
        [
            ("response = answer", "EQUALITY"),
            ("response written as answer", "WRITTEN_AS"),
            ("response proportional to answer", "PROPORTIONAL_TO"),
            ("response contains answer", "CONTAINS"),
        ],
    )
    def test_operator_label(self, criterion, label):
        node = _parse(criterion)
        assert node.label == label

    @pytest.mark.parametrize(
        "criterion",
        ["response = answer", "response written as answer"],
    )
    def test_content_string_roundtrips(self, criterion):
        assert _parse(criterion).content_string() == criterion

    def test_where_clause_parses(self):
        node = _parse("response = answer where x = 1")
        assert node.label == "WHERE"


class TestCriteriaGraph:
    def test_build_and_serialise(self):
        g = CriteriaGraph("root")
        g.add_evaluation_node("EVAL", "eval", "eval details")
        g.add_criterion_node("CRIT", "crit", "crit details")
        g.add_output_node("OUT", "out", "out details")

        data = json.loads(g.to_json())
        assert "EVAL" in data["evaluations"]
        assert "CRIT" in data["criteria"]
        assert "OUT" in data["outputs"]

    def test_mermaid_returns_string(self):
        g = CriteriaGraph("root")
        g.add_evaluation_node("EVAL", "eval", "eval details")
        assert isinstance(g.to_mermaid(), str)

    def test_duplicate_evaluation_node_rejected(self):
        g = CriteriaGraph("root")
        g.add_evaluation_node("EVAL", "eval", "eval details")
        with pytest.raises(CriteriaGraphError):
            g.add_evaluation_node("EVAL", "eval", "eval details")
