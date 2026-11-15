"""Admissible and consistent Block World heuristics.

All stacks are ordered bottom-to-top; table stack order is immaterial.
"""
from __future__ import annotations

from environment import State


def direct_supports(state: State) -> dict[str, str]:
    """Return the direct support (underneath block or TABLE) for each block."""
    return {
        block: (stack[i - 1] if i else "TABLE")
        for stack in state
        for i, block in enumerate(stack)
    }


def h0(state: State, goal: State) -> int:
    """Zero heuristic baseline."""
    return 0


def h1(state: State, goal: State) -> int:
    """Count blocks whose direct support does not match the goal."""
    current = direct_supports(state)
    wanted = direct_supports(goal)
    return sum(current[block] != support for block, support in wanted.items())


def h2(state: State, goal: State) -> int:
    """Count blocks not in a correctly built prefix anchored to the table.

    A block counts as settled iff its direct support is correct, and
    the support is TABLE or is itself settled. Each unsettled block
    must be moved at least once in any solution.
    """
    wanted = direct_supports(goal)
    settled = 0
    for stack in state:
        prefix_correct = True
        for i, block in enumerate(stack):
            support = stack[i - 1] if i else "TABLE"
            prefix_correct = prefix_correct and wanted.get(block) == support
            if prefix_correct:
                settled += 1
    return sum(len(stack) for stack in state) - settled


HEURISTICS = {"h0": h0, "h1": h1, "h2": h2}
