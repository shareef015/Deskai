from __future__ import annotations

from dataclasses import dataclass

from .models import ExecutionState


@dataclass(frozen=True, slots=True)
class GraphContract:
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]

    def validate(self) -> None:
        node_set = set(self.nodes)
        for source, target in self.edges:
            if source not in node_set or target not in node_set:
                raise ValueError("graph_edge_references_unknown_node")
        if len(node_set) != len(self.nodes):
            raise ValueError("duplicate_graph_node")


PRODUCTION_GRAPH = GraphContract(
    nodes=tuple(state.value for state in ExecutionState if state is not ExecutionState.FAILED),
    edges=(
        ("intake", "retrieving"),
        ("retrieving", "grounding"),
        ("grounding", "routing"),
        ("routing", "diagnosing"),
        ("diagnosing", "awaiting_approval"),
        ("awaiting_approval", "remediating"),
        ("remediating", "verifying"),
        ("verifying", "closed"),
        ("verifying", "diagnosing"),
    ),
)


def assert_transition(current: ExecutionState, target: ExecutionState) -> None:
    if (current.value, target.value) not in PRODUCTION_GRAPH.edges:
        raise ValueError(f"illegal_graph_transition:{current.value}->{target.value}")
