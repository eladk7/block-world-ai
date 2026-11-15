"""Part E: 12 reproducible Block World experiments with CSV/JSON evidence."""
from __future__ import annotations
import argparse
import csv
import json
import random
import statistics
from collections import Counter
from pathlib import Path
from environment import validate_problem, apply_move
from heuristics import HEURISTICS
from search import astar, ida_star

SEED = 20261115
SIZES = (2, 3, 4, 5, 6, 7, 2, 3, 4, 5, 6, 7)

def random_state(blocks, rng):
    order = list(blocks)
    rng.shuffle(order)
    stacks = []
    for block in order:
        if stacks and rng.random() < .65:
            rng.choice(stacks).append(block)
        else:
            stacks.append([block])
    return validate_problem(stacks, stacks)[0]

def make_cases(seed=SEED, sizes=SIZES):
    rng = random.Random(seed)
    cases = []
    for i, n in enumerate(sizes, 1):
        if not 1 <= n <= 10:
            raise ValueError("Invalid number of blocks")
        blocks = list("ABCDEFGHIJ"[:n])
        start = random_state(blocks, rng)
        goal = random_state(blocks, rng)
        for _ in range(50):
            if goal != start:
                break
            goal = random_state(blocks, rng)
        if goal == start:
            goal = validate_problem([[x] for x in blocks], [[x] for x in blocks])[0]
            if goal == start:
                goal = validate_problem([blocks], [blocks])[0]
        cases.append({"id": i, "n": n, "start": start, "goal": goal})
    return cases

def label(state):
    return " | ".join(",".join(stack) for stack in state)

def validate_result(start, goal, result):
    if result.status != "solved":
        assert result.cost is None, "Stopped run must not claim a solution"
        return
    assert result.cost == len(result.moves)
    assert len(result.states) == len(result.moves) + 1
    assert result.states[0] == start and result.states[-1] == goal
    current = start
    for i, move in enumerate(result.moves):
        current = apply_move(current, move)
        assert current == result.states[i + 1], f"Illegal move at step {i + 1}"
    assert current == goal

def summary_table(rows):
    groups = []
    for algorithm in ("A*", "IDA*"):
        for name in HEURISTICS:
            data = [r for r in rows if r["algorithm"] == algorithm and r["heuristic"] == name]
            solved = [r for r in data if r["status"] == "solved"]
            status = Counter(r["status"] for r in data)
            def stats(key, subset):
                values = [float(r[key]) for r in subset]
                return ((round(statistics.mean(values), 6) if values else None),
                        (round(statistics.stdev(values), 6) if len(values) > 1 else None))
            time_mean, time_std = stats("seconds", data)
            exp_mean, exp_std = stats("expanded", data)
            gen_mean, gen_std = stats("generated", data)
            cost_mean, cost_std = stats("cost", solved)
            groups.append({
                "algorithm": algorithm, "heuristic": name,
                "runs": len(data), "solved": len(solved),
                "timeout": status["timeout"], "expansion_limit": status["expansion_limit"],
                "time_mean_s": time_mean, "time_std_s": time_std,
                "expanded_mean": exp_mean, "expanded_std": exp_std,
                "generated_mean": gen_mean, "generated_std": gen_std,
                "cost_mean_solved_only": cost_mean, "cost_std_solved_only": cost_std,
            })
    return groups

def run_experiment(seed=SEED, sizes=SIZES, max_expansions=3000,
                   timeout_seconds=2.0, output_dir="results/part_e", quiet=False):
    cases = make_cases(seed, sizes)
    if len(cases) < 12:
        raise ValueError("At least 12 case pairs are required")
    rows = []
    for case in cases:
        case_rows = []
        for algorithm, solver in (("A*", astar), ("IDA*", ida_star)):
            for name, heuristic in HEURISTICS.items():
                result = solver(case["start"], case["goal"], heuristic,
                                max_expansions=max_expansions,
                                timeout_seconds=timeout_seconds, record_trace=False)
                validate_result(case["start"], case["goal"], result)
                row = {
                    "case_id": case["id"], "n": case["n"],
                    "initial": label(case["start"]), "goal": label(case["goal"]),
                    "algorithm": algorithm, "heuristic": name,
                    "status": result.status, "cost": result.cost,
                    "seconds": round(result.elapsed_seconds, 6),
                    "expanded": result.expanded, "generated": result.generated,
                    "max_frontier": result.max_frontier,
                    "improvements": result.improvements, "iterations": result.iterations,
                }
                rows.append(row)
                case_rows.append(row)
        for name in HEURISTICS:
            good = [r for r in case_rows if r["heuristic"] == name and r["status"] == "solved"]
            if len(good) == 2:
                assert good[0]["cost"] == good[1]["cost"], "A*/IDA* mismatch"
        assert len({r["cost"] for r in case_rows if r["status"] == "solved"}) <= 1
        if not quiet:
            print(f"Case {case['id']:02d} | n={case['n']} | solved {sum(x['status']=='solved' for x in case_rows)}/6")
    summary = summary_table(rows)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    def write_csv(name, data):
        with (out / name).open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    write_csv("runs.csv", rows)
    write_csv("summary.csv", summary)
    config = {
        "seed": seed, "sizes": list(sizes), "pairs": len(cases),
        "runs": len(rows), "expansion_limit": max_expansions,
        "timeout_seconds": timeout_seconds,
        "cases": cases,
        "notes": [
            "Generated counts states before duplicate checks.",
            "Summary time and expansion averages include stopped runs.",
            "Cost statistics include solved runs only.",
            "A* max_frontier is priority queue size; IDA* is maximum DFS depth.",
        ],
    }
    (out / "config_and_cases.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        f"Part E | seed={seed} | pairs={len(cases)} | runs={len(rows)}",
        f"Expansion limit={max_expansions} | timeout={timeout_seconds}s",
        "Algorithm | Heuristic | Solved | Timeout | Expansion limit | Time mean/std | Expanded mean/std",
    ]
    for s in summary:
        lines.append(
            f"{s['algorithm']} | {s['heuristic']} | {s['solved']}/{s['runs']} | "
            f"{s['timeout']} | {s['expansion_limit']} | "
            f"{s['time_mean_s']}/{s['time_std_s']} | "
            f"{s['expanded_mean']}/{s['expanded_std']}"
        )
    (out / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not quiet:
        print("\n" + "\n".join(lines))
        print(f"Files saved to: {out.resolve()}")
    return rows, summary

def main():
    parser = argparse.ArgumentParser(description="Part E reproducible search experiments")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--max-expansions", type=int, default=3000)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--output", default="results/part_e")
    args = parser.parse_args()
    if args.max_expansions < 1 or args.timeout <= 0:
        parser.error("Limits must be positive")
    run_experiment(args.seed, SIZES, args.max_expansions, args.timeout, args.output)

if __name__ == "__main__":
    main()
