"""Run both algorithms on the assignment's five-move example."""
from search import astar, ida_star

start = [["D", "A", "B", "C"]]
goal = [["D"], ["A", "B", "C"]]

for search in (astar, ida_star):
    result = search(start, goal)
    print(f"\n{result.algorithm}: {result.status}, cost={result.cost}")
    print(f"expanded={result.expanded}, generated={result.generated}, max_frontier={result.max_frontier}, iterations={result.iterations}")
    for number, move in enumerate(result.moves, 1):
        print(f"  {number}. Move {move.block} from {move.source} to {move.destination}")
