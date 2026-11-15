import unittest

from environment import Move, apply_move, canonical, is_goal, successors, validate, validate_problem


class EnvironmentTests(unittest.TestCase):
    def test_canonical_order(self):
        self.assertEqual(canonical([["A", "B"], ["C"]]), canonical([["C"], ["A", "B"]]))

    def test_example_first_move(self):
        start, _ = validate_problem([["D", "A", "B", "C"]], [["D"], ["A", "B", "C"]])
        actions = successors(start)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], Move("C", "B", "TABLE"))

    def test_example_five_legal_moves(self):
        state, goal = validate_problem([["D", "A", "B", "C"]], [["D"], ["A", "B", "C"]])
        for action in [
            Move("C", "B", "TABLE"),
            Move("B", "A", "TABLE"),
            Move("A", "D", "TABLE"),
            Move("B", "TABLE", "A"),
            Move("C", "TABLE", "B"),
        ]:
            state = apply_move(state, action)
        self.assertTrue(is_goal(state, goal))

    def test_invalid_duplicate(self):
        with self.assertRaises(ValueError):
            validate([["A", "A"]])

    def test_invalid_different_blocks(self):
        with self.assertRaises(ValueError):
            validate_problem([["A", "B"]], [["A", "C"]])

    def test_no_table_to_table_move(self):
        state = validate([["A"], ["B"]])
        actions = successors(state)
        self.assertEqual(len(actions), 2)
        self.assertTrue(all(action.destination != "TABLE" for action, _ in actions))

    def test_goal_ignores_stack_order(self):
        start, goal = validate_problem([["A"], ["B"]], [["B"], ["A"]])
        self.assertTrue(is_goal(start, goal))


if __name__ == "__main__":
    unittest.main()
