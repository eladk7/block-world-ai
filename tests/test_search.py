import unittest
from environment import apply_move, validate_problem
from search import astar, ida_star


class SearchTests(unittest.TestCase):
    def test_goal_equals_start(self):
        for search in (astar, ida_star):
            result = search([["A"], ["B"]], [["B"], ["A"]])
            self.assertEqual((result.status, result.cost, result.moves), ("solved", 0, []))

    def test_five_move_example(self):
        start, goal = validate_problem([["D", "A", "B", "C"]], [["D"], ["A", "B", "C"]])
        for search in (astar, ida_star):
            result = search(start, goal)
            self.assertEqual(result.status, "solved")
            self.assertEqual(result.cost, 5)
            state = start
            for move in result.moves:
                state = apply_move(state, move)
            self.assertEqual(state, goal)
            self.assertEqual(result.states[-1], goal)

    def test_input_validation(self):
        for search in (astar, ida_star):
            with self.assertRaises(ValueError):
                search([["A", "B"]], [["A", "C"]])

    def test_limits(self):
        start, goal = [["A", "B", "C"]], [["C", "B", "A"]]
        for search in (astar, ida_star):
            self.assertEqual(search(start, goal, max_expansions=0).status, "expansion_limit")
            self.assertEqual(search(start, goal, cancelled=lambda: True).status, "cancelled")

    def test_multiple_small_problems_same_cost(self):
        problems = [
            ([["A", "B"]], [["A"], ["B"]]),
            ([["A"], ["B"]], [["A", "B"]]),
            ([["A", "B", "C"]], [["A", "C", "B"]]),
            ([["A", "B"], ["C"]], [["C", "A"], ["B"]]),
        ]
        for initial, goal in problems:
            a = astar(initial, goal)
            b = ida_star(initial, goal)
            self.assertEqual((a.status, a.cost), (b.status, b.cost))

    def test_astar_trace(self):
        result = astar([["A", "B"]], [["A"], ["B"]])
        self.assertEqual(result.trace[0]["g"], 0)
        self.assertIn(result.trace[0]["successors"][0]["status"], {"added", "improved", "rejected"})

    def test_ida_iterations(self):
        result = ida_star([["A", "B"]], [["A"], ["B"]])
        self.assertEqual(result.status, "solved")
        self.assertGreaterEqual(result.iterations, 2)
        self.assertEqual(result.trace[0]["threshold"], 0)
