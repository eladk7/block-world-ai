"""Test Part C: examples, dominance, consistency and admissibility."""
from collections import deque
import unittest

from environment import successors, validate_problem
from heuristics import h0, h1, h2
from search import astar, ida_star


class HeuristicTests(unittest.TestCase):
    def test_assignment_example(self):
        start, goal = validate_problem([["D", "A", "B", "C"]], [["D"], ["A", "B", "C"]])
        self.assertEqual((h0(start, goal), h1(start, goal), h2(start, goal)), (0, 1, 3))
        for h in (h0, h1, h2):
            self.assertEqual(astar(start, goal, h).cost, 5)
            self.assertEqual(ida_star(start, goal, h).cost, 5)

    def test_sum_is_not_always_admissible(self):
        start, goal = validate_problem([["A", "B"]], [["A"], ["B"]])
        self.assertEqual(h1(start, goal), 1)
        self.assertEqual(h2(start, goal), 1)
        self.assertEqual(astar(start, goal).cost, 1)
        self.assertGreater(h1(start, goal) + h2(start, goal), 1)

    def test_exhaustive_four_block_properties(self):
        initial, _ = validate_problem([["A"], ["B"], ["C"], ["D"]], [["A"], ["B"], ["C"], ["D"]])
        states = [initial]
        known = {initial}
        for state in states:
            for _, child in successors(state):
                if child not in known:
                    known.add(child)
                    states.append(child)
        self.assertGreater(len(states), 50)

        for goal in states:
            exact = {goal: 0}
            queue = deque([goal])
            while queue:
                state = queue.popleft()
                for _, child in successors(state):
                    if child not in exact:
                        exact[child] = exact[state] + 1
                        queue.append(child)
            self.assertEqual(len(exact), len(states))
            for state in states:
                self.assertEqual(h0(state, goal), 0)
                self.assertLessEqual(h1(state, goal), h2(state, goal))
                self.assertLessEqual(h2(state, goal), exact[state])
                for _, child in successors(state):
                    self.assertLessEqual(h1(state, goal), 1 + h1(child, goal))
                    self.assertLessEqual(h2(state, goal), 1 + h2(child, goal))


if __name__ == "__main__":
    unittest.main()
