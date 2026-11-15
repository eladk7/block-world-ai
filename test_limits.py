
from search import astar, ida_star

start = [["D", "A", "B", "C"]]
goal = [["D"], ["A", "B", "C"]]

for algorithm in [astar, ida_star]:
    print(f"\nAlgorithm: {algorithm.__name__}")

    result = algorithm(start, goal, timeout_seconds=0)
    print("Time limit:", result.status)

    result = algorithm(start, goal, max_expansions=2)
    print("Expansion limit:", result.status)

    result = algorithm(start, goal, cancelled=lambda: True)
    print("Cancellation:", result.status)
