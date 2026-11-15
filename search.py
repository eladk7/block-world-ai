"""A* and IDA* Block World search with metrics, traces and safety limits."""
from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import itertools
import math
import time
from typing import Callable

from environment import Move, State, successors, validate_problem

Heuristic = Callable[[State, State], int | float]


def h0(state: State, goal: State) -> int:
    """Uniform-cost baseline."""
    return 0


@dataclass
class SearchResult:
    algorithm: str
    status: str = "pending"
    moves: list[Move] = field(default_factory=list)
    states: list[State] = field(default_factory=list)
    cost: int | None = None
    generated: int = 0
    expanded: int = 0
    max_frontier: int = 0
    improvements: int = 0
    iterations: int = 0
    elapsed_seconds: float = 0.0
    trace: list[dict] = field(default_factory=list)


def _heuristic(h: Heuristic, state: State, goal: State) -> float:
    value = float(h(state, goal))
    if not math.isfinite(value) or value < 0:
        raise ValueError("Heuristic must be finite and nonnegative")
    return value


def _reconstruct(start: State, goal: State, parents: dict[State, tuple[State, Move]]):
    states, moves = [goal], []
    current = goal
    while current != start:
        parent, move = parents[current]
        moves.append(move)
        states.append(parent)
        current = parent
    return list(reversed(moves)), list(reversed(states))


def astar(start_stacks, goal_stacks, heuristic: Heuristic = h0, *,
          max_expansions: int | None = 100_000, timeout_seconds: float | None = 30,
          cancelled: Callable[[], bool] | None = None, record_trace: bool = True) -> SearchResult:
    """A* graph search, ties: lowest f, highest g, lexical canonical state."""
    start, goal = validate_problem(start_stacks, goal_stacks)
    result = SearchResult("A*")
    begin = time.perf_counter()
    best_g: dict[State, int] = {start: 0}
    parents: dict[State, tuple[State, Move]] = {}
    heap: list[tuple[float, int, State, int]] = []
    serial = itertools.count()
    heapq.heappush(heap, (_heuristic(heuristic, start, goal), 0, start, next(serial)))
    result.max_frontier = 1
    try:
        while heap:
            if cancelled is not None and cancelled():
                result.status = "cancelled"
                break
            if timeout_seconds is not None and time.perf_counter() - begin >= timeout_seconds:
                result.status = "timeout"
                break
            f, neg_g, state, _ = heapq.heappop(heap)
            g = -neg_g
            if g != best_g.get(state):
                continue  # ignore stale priority queue entries
            h = _heuristic(heuristic, state, goal)
            event = {"state": state, "g": g, "h": h, "f": f,
                     "open_size": len(heap), "successors": []}
            if state == goal:  # goal checked on pop, not generation
                result.moves, result.states = _reconstruct(start, goal, parents)
                result.cost = g
                result.status = "solved"
                if record_trace:
                    result.trace.append(event)
                break
            if max_expansions is not None and result.expanded >= max_expansions:
                result.status = "expansion_limit"
                break
            result.expanded += 1
            for move, child in successors(state):
                result.generated += 1  # count before deduplication
                new_g = g + move.cost
                old = best_g.get(child)
                if old is None or new_g < old:
                    if old is not None:
                        result.improvements += 1
                    best_g[child] = new_g
                    parents[child] = (state, move)
                    new_h = _heuristic(heuristic, child, goal)
                    heapq.heappush(heap, (new_g + new_h, -new_g, child, next(serial)))
                    status = "added" if old is None else "improved"
                else:
                    status = "rejected"
                if record_trace:
                    event["successors"].append({"move": move, "state": child, "status": status})
            result.max_frontier = max(result.max_frontier, len(heap))
            if record_trace:
                result.trace.append(event)
        else:
            result.status = "unsolvable"
    finally:
        result.elapsed_seconds = time.perf_counter() - begin
    return result


def ida_star(start_stacks, goal_stacks, heuristic: Heuristic = h0, *,
             max_expansions: int | None = 100_000, timeout_seconds: float | None = 30,
             cancelled: Callable[[], bool] | None = None, record_trace: bool = True) -> SearchResult:
    """IDA*: iterative f-threshold DFS, path-only cycle checks, no global closed."""
    start, goal = validate_problem(start_stacks, goal_stacks)
    result = SearchResult("IDA*")
    begin = time.perf_counter()
    threshold = _heuristic(heuristic, start, goal)
    path_states: list[State] = [start]
    path_moves: list[Move] = []
    on_path: set[State] = {start}

    class StopSearch(Exception):
        def __init__(self, status: str):
            self.status = status

    def check_limits():
        if cancelled is not None and cancelled():
            raise StopSearch("cancelled")
        if timeout_seconds is not None and time.perf_counter() - begin >= timeout_seconds:
            raise StopSearch("timeout")

    def dfs(g: int, bound: float, iteration: dict) -> float | None:
        check_limits()
        state = path_states[-1]
        h = _heuristic(heuristic, state, goal)
        f = g + h
        if f > bound:
            iteration["prunes"] += 1
            if record_trace:
                iteration["events"].append({"state": state, "g": g, "h": h, "f": f, "status": "f_pruned"})
            return f
        if state == goal:
            return None  # success sentinel
        if max_expansions is not None and result.expanded >= max_expansions:
            raise StopSearch("expansion_limit")
        result.expanded += 1
        iteration["expanded"] += 1
        if record_trace:
            iteration["events"].append({"state": state, "g": g, "h": h, "f": f, "status": "expanded"})
        minimum_exceeded = math.inf
        for move, next_state in successors(state):
            check_limits()
            result.generated += 1
            if next_state in on_path:
                iteration["prunes"] += 1
                if record_trace:
                    iteration["events"].append({"state": next_state, "move": move, "status": "cycle_pruned"})
                continue
            path_states.append(next_state)
            path_moves.append(move)
            on_path.add(next_state)
            result.max_frontier = max(result.max_frontier, len(path_states))  # max DFS stack depth
            exceeded = dfs(g + move.cost, bound, iteration)
            if exceeded is None:
                return None
            minimum_exceeded = min(minimum_exceeded, exceeded)
            on_path.remove(next_state)
            path_states.pop()
            path_moves.pop()
        return minimum_exceeded

    result.max_frontier = 1
    try:
        while True:
            check_limits()
            result.iterations += 1
            iteration = {"threshold": threshold, "expanded": 0, "prunes": 0, "next_threshold": None, "events": []}
            if record_trace:
                result.trace.append(iteration)
            exceeded = dfs(0, threshold, iteration)
            if exceeded is None:
                result.status = "solved"
                result.cost = len(path_moves)
                result.moves = list(path_moves)
                result.states = list(path_states)
                break
            iteration["next_threshold"] = exceeded if math.isfinite(exceeded) else None
            if math.isinf(exceeded):
                result.status = "unsolvable"
                break
            threshold = exceeded
    except StopSearch as exc:
        result.status = exc.status
    finally:
        result.elapsed_seconds = time.perf_counter() - begin
    return result
