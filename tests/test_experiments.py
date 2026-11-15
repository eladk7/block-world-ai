import tempfile
import unittest
from pathlib import Path
from experiments import SEED, make_cases, run_experiment
from environment import validate_problem, apply_move
from search import astar

class ExperimentsTests(unittest.TestCase):
    def test_reproducible_twelve_pairs(self):
        a, b = make_cases(SEED), make_cases(SEED)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 12)
        self.assertEqual({x["n"] for x in a}, {2, 3, 4, 5, 6, 7})
        for case in a:
            self.assertNotEqual(case["start"], case["goal"])
            validate_problem(case["start"], case["goal"])

    def test_path_is_legal(self):
        start, goal = validate_problem([["A", "B"]], [["A"], ["B"]])
        result = astar(start, goal)
        self.assertEqual(result.status, "solved")
        current = start
        for move in result.moves:
            current = apply_move(current, move)
        self.assertEqual(current, goal)

    def test_export_and_statistics(self):
        with tempfile.TemporaryDirectory() as path:
            rows, summaries = run_experiment(
                seed=17, sizes=[2, 3] * 6, max_expansions=100,
                timeout_seconds=2.0, output_dir=path, quiet=True
            )
            self.assertEqual(len(rows), 72)
            self.assertEqual(len(summaries), 6)
            for filename in ("runs.csv", "summary.csv", "config_and_cases.json", "report.txt"):
                self.assertTrue((Path(path) / filename).exists())
            self.assertTrue(all(row["status"] == "solved" for row in rows))
