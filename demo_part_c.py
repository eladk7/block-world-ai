"""Part C: compare three admissible heuristics on the example."""
from environment import validate_problem
from heuristics import HEURISTICS
from search import astar, ida_star

start, goal = validate_problem([["D", "A", "B", "C"]], [["D"], ["A", "B", "C"]])
print("Initial: D,A,B,C | Goal: D / A,B,C")
print("Heuristic values at start:")
for name, heuristic in HEURISTICS.items():
    print(f"  {name}={heuristic(start, goal)}")

print("\nAlgorithm | Heuristic | Status | Cost | Expanded | Generated | Iterations")
for algorithm in (astar, ida_star):
    for name, heuristic in HEURISTICS.items():
        result = algorithm(start, goal, heuristic, record_trace=False)
        print(f"{result.algorithm:9} | {name:9} | {result.status:6} | {result.cost:4} | {result.expanded:8} | {result.generated:9} | {result.iterations:10}")

one_move_start, one_move_goal = validate_problem([["A", "B"]], [["A"], ["B"]])
print("\nCounterexample to admissibility of h1+h2:")
print(f"  h1={HEURISTICS['h1'](one_move_start, one_move_goal)}; h2={HEURISTICS['h2'](one_move_start, one_move_goal)}; true cost=1")
