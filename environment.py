"""Block World environment. Stacks are ordered bottom-to-top."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

State = tuple[tuple[str, ...], ...]

@dataclass(frozen=True)
class Move:
    block: str
    source: str
    destination: str
    cost: int = 1


def canonical(stacks: Iterable[Iterable[str]]) -> State:
    """Normalize stack order; table positions do not matter."""
    return tuple(sorted(tuple(stack) for stack in stacks))


def validate(stacks: Iterable[Iterable[str]]) -> State:
    raw = [tuple(s) for s in stacks]
    if not raw or any(not s for s in raw):
        raise ValueError("At least one nonempty stack is required; empty stacks are invalid")
    blocks = [b for stack in raw for b in stack]
    if not 1 <= len(blocks) <= 10:
        raise ValueError("Number of blocks must be between 1 and 10")
    if any(not isinstance(b, str) or not b.strip() for b in blocks):
        raise ValueError("Block names must be nonempty strings")
    if len(set(blocks)) != len(blocks):
        raise ValueError("Block names must be unique")
    if "TABLE" in blocks:
        raise ValueError("TABLE is a reserved name")
    return canonical(raw)


def validate_problem(start: Iterable[Iterable[str]], goal: Iterable[Iterable[str]]) -> tuple[State, State]:
    s, g = validate(start), validate(goal)
    if {b for stack in s for b in stack} != {b for stack in g for b in stack}:
        raise ValueError("Start and goal must contain exactly the same blocks")
    return s, g


def successors(state: State) -> list[tuple[Move, State]]:
    """Return legal one-block moves and their canonical successor states."""
    result: list[tuple[Move, State]] = []
    for i, stack in enumerate(state):
        block = stack[-1]
        source = stack[-2] if len(stack) > 1 else "TABLE"
        if len(stack) > 1:
            next_stacks = [list(s) for s in state]
            next_stacks[i].pop()
            next_stacks.append([block])
            result.append((Move(block, source, "TABLE"), canonical(next_stacks)))
        for j, target in enumerate(state):
            if i == j:
                continue
            next_stacks = [list(s) for s in state]
            next_stacks[i].pop()
            next_stacks[j].append(block)
            result.append((Move(block, source, target[-1]), canonical(s for s in next_stacks if s)))
    return result


def is_goal(state: State, goal: State) -> bool:
    return state == goal


def apply_move(state: State, move: Move) -> State:
    for action, successor in successors(state):
        if action == move:
            return successor
    raise ValueError(f"Illegal move: {move}")
