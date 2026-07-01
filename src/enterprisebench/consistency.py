"""Multi-Turn Consistency Score (MTCS) — DESIGN_DOC.md Section 4.1 / 6.4.

MTCS measures whether an agent's decisions across a multi-turn workflow
contradict each other. The formalization: each turn produces a Decision
(a key-value fact the agent has committed to). Later turns can depend on
earlier decisions. A contradiction occurs when a later decision conflicts
with a prior one it depends on.

Example: at turn 2 the agent decides "priority = HIGH". At turn 7 the agent
references the same ticket and sets "priority = LOW" without any intervening
instruction to change it. That is a consistency violation.

MTCS = 1 - (contradictions / dependent_pairs_checked)

A score of 1.0 means no contradictions; 0.0 means every dependent pair
contains a contradiction.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Decision:
    """A single fact the agent committed to at a specific turn.

    Args:
        turn_index: Which turn this decision was made (0-indexed).
        key: What aspect of the world state this covers (e.g. "ticket_priority").
        value: The value the agent committed to (e.g. "HIGH").
    """
    turn_index: int
    key: str
    value: str


@dataclass
class ConsistencyViolation:
    """Records a single contradiction between two decisions."""
    earlier_turn: int
    later_turn: int
    key: str
    earlier_value: str
    later_value: str

    def __str__(self) -> str:
        return (
            f"Turn {self.later_turn} says {self.key}={self.later_value!r} "
            f"but turn {self.earlier_turn} said {self.key}={self.earlier_value!r}"
        )


@dataclass
class ConsistencyResult:
    """Output of check_consistency() for one multi-turn session."""
    session_id: str
    violations: list[ConsistencyViolation] = field(default_factory=list)
    n_pairs_checked: int = 0

    @property
    def mtcs(self) -> float:
        """Multi-Turn Consistency Score: 1 - fraction of pairs that contradict."""
        if self.n_pairs_checked == 0:
            return 1.0
        return 1.0 - len(self.violations) / self.n_pairs_checked


def check_consistency(
    session_id: str,
    decisions: list[Decision],
) -> ConsistencyResult:
    """Check all later decisions against earlier ones with the same key.

    For each key that appears more than once, every (earlier, later) pair
    with the same key is a dependency. If the values differ, that is a
    contradiction.

    This is an O(n²) scan over decisions — acceptable for session lengths
    up to a few hundred turns.
    """
    violations: list[ConsistencyViolation] = []
    pairs_checked = 0

    # Group decisions by key, preserving order
    by_key: dict[str, list[Decision]] = {}
    for d in decisions:
        by_key.setdefault(d.key, []).append(d)

    for key, ds in by_key.items():
        # Check every (earlier, later) pair for this key
        for i in range(len(ds)):
            for j in range(i + 1, len(ds)):
                pairs_checked += 1
                if ds[i].value != ds[j].value:
                    violations.append(
                        ConsistencyViolation(
                            earlier_turn=ds[i].turn_index,
                            later_turn=ds[j].turn_index,
                            key=key,
                            earlier_value=ds[i].value,
                            later_value=ds[j].value,
                        )
                    )

    return ConsistencyResult(
        session_id=session_id,
        violations=violations,
        n_pairs_checked=pairs_checked,
    )


def aggregate_mtcs(results: list[ConsistencyResult]) -> float:
    """Mean MTCS across multiple sessions."""
    if not results:
        return 1.0
    return sum(r.mtcs for r in results) / len(results)
