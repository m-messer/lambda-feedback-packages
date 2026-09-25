"""The criteria graph: evaluations, the criteria they establish, and outputs."""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from typing import Any, ClassVar

from .errors import CriteriaEvaluationError, CriteriaGraphError
from .nodes import (
    CriterionNode,
    Edge,
    Evaluate,
    EvaluationNode,
    FeedbackStringGenerator,
    Node,
    OutputNode,
    ReachedCriteria,
    ResultLike,
    no_feedback,
)
from .render import graph_to_json, graph_to_mermaid
from .tree import CriteriaTree, build_tree


class CriteriaGraph:
    """A graph of evaluations, the criteria they establish, and outputs.

    Evaluations point to criteria; criteria point to further evaluations or
    to outputs. ``generate_feedback`` walks the graph from the evaluations
    leading to a main criterion and collects every criterion reached;
    ``export_feedback`` turns those into feedback on a result object.

    To export feedback differently, subclass and override ``export_feedback``
    (building on ``resolve_feedback`` for the text).
    """

    END: ClassVar[OutputNode] = OutputNode("END", "END", "Evaluation completed.")
    """Conventional terminal output; add it with ``graph.add_node(CriteriaGraph.END)``."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.evaluations: dict[str, EvaluationNode] = {}
        self.criteria: dict[str, CriterionNode] = {}
        self.outputs: dict[str, OutputNode] = {}
        # Evaluation label -> criteria whose evaluations can stand in for it
        # when choosing where to start (see starting_evaluations).
        self.sufficiencies: dict[str, list[str] | None] = {}

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def add_evaluation_node(
        self,
        label: str,
        summary: str,
        details: str,
        sufficiencies: Iterable[str] | None = None,
        evaluate: Evaluate | None = None,
        feedback_string_generator: FeedbackStringGenerator | None = None,
    ) -> EvaluationNode:
        # feedback_string_generator is accepted (and rejected) so that attach()
        # can pass the same keywords whichever kind of node it creates.
        if feedback_string_generator is not None:
            raise CriteriaGraphError(
                f"{label} is an evaluation node, evaluation nodes cannot generate feedback strings."
            )
        if label in self.evaluations:
            raise CriteriaGraphError(f"Evaluation node {label} is already defined.")
        node = EvaluationNode(label, summary, details, evaluate)
        self.evaluations[label] = node
        self.sufficiencies[label] = list(sufficiencies) if sufficiencies is not None else None
        return node

    def add_criterion_node(
        self,
        label: str,
        summary: str,
        details: str,
        sufficiencies: Iterable[str] | None = None,
        evaluate: Evaluate | None = None,
        feedback_string_generator: FeedbackStringGenerator | None = None,
    ) -> CriterionNode:
        # sufficiencies/evaluate are accepted for attach(), as above; criteria
        # cannot have sufficiencies, and `evaluate` is ignored.
        if label in self.criteria:
            raise CriteriaGraphError(f"Criterion node {label} is already defined.")
        if sufficiencies is not None:
            raise CriteriaGraphError("Criterion nodes cannot have sufficiencies.")
        node = CriterionNode(label, summary, details, feedback_string_generator or no_feedback)
        self.criteria[label] = node
        self.sufficiencies[label] = None
        return node

    def add_output_node(self, label: str, summary: str, details: str) -> OutputNode:
        if label in self.outputs:
            raise CriteriaGraphError(f"Output node {label} is already defined.")
        node = OutputNode(label, summary, details)
        self.outputs[label] = node
        return node

    def add_node(self, node: Node) -> None:
        """Add a copy of ``node`` (e.g. ``CriteriaGraph.END``) to this graph."""
        if isinstance(node, EvaluationNode):
            self.add_evaluation_node(node.label, node.summary, node.details, evaluate=node.evaluate)
        elif isinstance(node, CriterionNode):
            self.add_criterion_node(
                node.label, node.summary, node.details, feedback_string_generator=node.feedback_string_generator
            )
        elif isinstance(node, OutputNode):
            self.add_output_node(node.label, node.summary, node.details)
        else:
            raise CriteriaGraphError("Can only add evaluation, criterion or output nodes to criteria graph.")

    def attach(
        self,
        source_label: str,
        target_label: str,
        summary: str | None = None,
        details: str | None = None,
        sufficiencies: Iterable[str] | None = None,
        evaluate: Evaluate | None = None,
        feedback_string_generator: FeedbackStringGenerator | None = None,
    ) -> None:
        """Add an edge from ``source_label`` to ``target_label``.

        Evaluations attach to criteria, criteria to evaluations or outputs. If
        the target doesn't exist it is created (of the kind the source leads
        to), which requires ``summary`` and ``details``; the remaining keywords
        configure the new node.
        """
        source: Node | None = self.evaluations.get(source_label) or self.criteria.get(source_label)
        if source is None:
            if source_label in self.outputs:
                raise CriteriaGraphError(f"{source_label} is an output node. Output nodes cannot have outgoing edges.")
            raise CriteriaGraphError(f"Unknown node {source_label}.")

        target: Node | None
        wrong_kind: Mapping[str, Node]
        if isinstance(source, EvaluationNode):
            target, wrong_kind = self.criteria.get(target_label), self.evaluations
            kind, other_kind = "evaluation", "criterion"
        else:
            target = self.evaluations.get(target_label) or self.outputs.get(target_label)
            wrong_kind, kind, other_kind = self.criteria, "criterion", "evaluation"

        if target is None:
            if target_label in wrong_kind:
                raise CriteriaGraphError(
                    f"Both {source_label} and {target_label} are {kind} nodes. "
                    f"Only {other_kind} nodes can be attached to {kind} nodes."
                )
            if summary is None or details is None:
                raise CriteriaGraphError(
                    f"Unknown node {target_label}. If you wish to create a new node summary and details must be "
                    "specified."
                )
            add = self.add_criterion_node if isinstance(source, EvaluationNode) else self.add_evaluation_node
            target = add(
                target_label,
                summary,
                details,
                sufficiencies=sufficiencies,
                evaluate=evaluate,
                feedback_string_generator=feedback_string_generator,
            )

        edge = Edge(source, target)
        if edge in source.outgoing:
            raise CriteriaGraphError(f"{target_label} is already attached to {source_label}.")
        source.outgoing.append(edge)
        target.incoming.append(edge)

    def add_sufficiencies(self, source_label: str, sufficiencies: Iterable[str]) -> None:
        if source_label not in self.evaluations:
            raise CriteriaGraphError(
                f"Unknown evaluation node {source_label}. Only evaluation nodes can have sufficiencies."
            )
        existing = self.sufficiencies.get(source_label)
        if existing is None:
            existing = self.sufficiencies[source_label] = []
        for sufficiency in sufficiencies:
            if sufficiency not in existing:
                existing.append(sufficiency)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def starting_evaluations(self, label: str) -> list[str]:
        """The evaluations to start from to decide criterion (or evaluation) ``label``.

        Evaluations with sufficiencies are replaced by the evaluations leading
        to those sufficient criteria, recursively.
        """
        # TODO: Consider if starting evaluations should only accept evaluation nodes
        #       instead of guessing the intent when using criteria nodes as targets
        if label in self.criteria:
            base = list(dict.fromkeys(edge.source.label for edge in self.criteria[label].incoming))
        elif label in self.evaluations:
            base = [label]
        else:
            raise CriteriaGraphError(f"No criterion or evaluation with label {label}.")
        # Ordered worklist (not a set): the result must not depend on the hash seed.
        starting: list[str] = []
        candidates = list(base)
        seen: set[str] = set()
        while candidates:
            candidate = candidates.pop(0)
            if candidate in seen:
                continue  # sufficiencies can form cycles
            seen.add(candidate)
            sufficiencies = self.sufficiencies.get(candidate)
            if sufficiencies is None:
                starting.append(candidate)
            else:
                for sufficiency in sufficiencies:
                    candidates += [edge.source.label for edge in self.criteria[sufficiency].incoming]
        return starting or base

    def build_tree(self, starting_evaluation: str, main_criteria: Collection[str] = ()) -> CriteriaTree:
        """The graph unrolled from ``starting_evaluation`` as a tree (for display)."""
        return build_tree(self, starting_evaluation, main_criteria)

    def trees(self, label: str) -> list[CriteriaTree]:
        """One tree per starting evaluation for criterion ``label``."""
        return [self.build_tree(start, main_criteria=[label]) for start in self.starting_evaluations(label)]

    def generate_feedback(self, response: Any, main_criteria: str) -> dict[str, Mapping[str, Any] | None]:
        """Run the evaluations reachable from ``main_criteria``'s starting evaluations.

        Returns every criterion reached, mapped to the inputs for its feedback
        text, in the order reached (breadth-first, in attachment order); pass
        it to ``export_feedback`` or ``resolve_feedback`` for the text.
        Evaluations with a ``replacement`` are skipped in favour of it.
        """
        queue = self.starting_evaluations(main_criteria)
        visited: set[str] = set()
        feedback: dict[str, Mapping[str, Any] | None] = {}
        while queue:
            label = queue.pop(0)
            node = self.evaluations.get(label)
            if node is not None and node.replacement is not None:
                visited.add(label)
                label = node.replacement.label
            if label in visited or label not in self.evaluations:
                continue
            visited.add(label)
            evaluate = self.evaluations[label].evaluate
            if evaluate is None:
                raise CriteriaGraphError(f"Evaluation node {label} has no evaluate function.")
            try:
                results = evaluate(response)
            except Exception as exc:
                raise CriteriaEvaluationError(label) from exc
            feedback.update(results)
            for criterion in results:
                queue += [edge.target.label for edge in self.criteria[criterion].outgoing]
        return feedback

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    def resolve_feedback(
        self,
        reached: ReachedCriteria,
        custom_feedback: Mapping[str, str] | None = None,
    ) -> list[tuple[str, str]]:
        """Feedback text for each reached criterion, as ``(tag, text)`` pairs.

        ``reached`` maps criterion labels to the inputs for their feedback
        string generators (as returned by ``generate_feedback``).
        ``custom_feedback`` overrides the text for given tags. Text is stripped,
        and a generator returning ``None`` gives ``""``: the tag still counts as
        reached, it just has nothing to say.
        """
        custom_feedback = custom_feedback or {}
        resolved = []
        for tag, inputs in reached.items():
            if tag in custom_feedback:
                text: str | None = custom_feedback[tag]
            else:
                text = self.criteria[tag].feedback_string_generator(inputs or {})
            resolved.append((tag, (text or "").strip()))
        return resolved

    def export_feedback(
        self,
        result: ResultLike,
        reached: ReachedCriteria,
        custom_feedback: Mapping[str, str] | None = None,
    ) -> None:
        """Add the feedback for each reached criterion to ``result``.

        Tags already on the result are skipped, so exporting several graphs'
        feedback into one result keeps the first text for a shared tag. Blank
        feedback is added as ``""`` so that the tag is still recorded.

        Override in a subclass to export feedback differently.
        """
        existing = set(result.tags or ())
        for tag, text in self.resolve_feedback(reached, custom_feedback):
            if tag not in existing:
                result.add_feedback(tag, text)
                existing.add(tag)

    @staticmethod
    def test_data(graphs: Mapping[str, CriteriaGraph]) -> dict[str, dict[str, str]]:
        """The criteria-graph payload for a result's test data (JSON and mermaid per graph).

        Merge it into the serialised result when test data is requested, e.g.
        ``{**result.to_dict(include_test_data=True), **CriteriaGraph.test_data(graphs)}``.
        """
        return {
            "criteria_graphs": {name: graph.to_json() for name, graph in graphs.items()},
            "criteria_graphs_vis": {name: graph.to_mermaid() for name, graph in graphs.items()},
        }

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """The graph's nodes, edges and sufficiencies as a JSON string."""
        return graph_to_json(self)

    def to_mermaid(self) -> str:
        """Mermaid flowchart source for the graph."""
        return graph_to_mermaid(self)
