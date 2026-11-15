# Block World AI

Academic AI search and planning project for the Blocks World problem.

## Current status
- **Part A**: State model, legal moves, input validation and canonicalization.
- **Part B**: A* graph search and IDA* with the zero heuristic `h0`, execution limits, metrics and traces.
- **Not yet implemented**: h1/h2 heuristics and proofs (Part C), interactive user interface (Part D), reproducible 12-case experiments and final report (Part E).

## Requirements
Python 3.10+ (standard library only).

## Run tests
```bash
python -m unittest discover -s tests -v
```

## Run the example
```bash
python demo.py
```

The example is: initial stack D,A,B,C, goal stacks D and A,B,C (all bottom-to-top). Both algorithms should report a 5-move optimal plan with h0.

## Algorithms
See `search.py`: `astar(start, goal)` and `ida_star(start, goal)`. Both return a `SearchResult` containing status, cost, moves, intermediate states, counters and optional trace. Cancellation may be supplied through `cancelled=lambda: condition`; `timeout_seconds` and `max_expansions` can bound computation. A* uses `(f,-g,canonical_state)` priority; IDA* uses iterative f-bounded DFS with path-cycle detection.

## Documentation / outputs
- `PART_A_HE.md` — Part A explanation (Hebrew)
- `docs/PART_B_HE.md` — search implementation notes (Hebrew)
- `results/example_h0.txt` — saved command-line example output

No UI is available yet. A document for submission is being authored separately by the student.
