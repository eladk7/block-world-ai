# Block World AI

Academic AI search and planning project for the Blocks World problem.

## Current status
- **Part A**: State model, legal moves, input validation and canonicalization.
- **Part B**: A* graph search and IDA* with the zero heuristic `h0`, execution limits, metrics and traces.
- **Part C**: h1/h2 consistent, admissible heuristics, exhaustive 4-block property tests, Hebrew proofs.
- **Part D**: Streamlit graphical interface, solution playback, search logs, runtime limits and cancellation.
- **Not yet implemented**: reproducible 12-case experiments and final report (Part E).

## Requirements
Python 3.10+ (the GUI additionally requires Streamlit).

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

## Launch the graphical interface

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Enter stacks bottom-to-top; separate stacks with `|`. Choose A*/IDA*, h0/h1/h2, limits and press Run search. Use Stop to request cancellation. Export output and trace via download buttons. See `docs/PART_D_HE.md` for usage and documentation in Hebrew. A document for submission is being authored separately by the student.

## Part C – heuristics

Run `python demo_part_c.py` to compare h0/h1/h2 on the assignment example. Proofs: `docs/PART_C_HE.md`. Saved results: `results/example_heuristics.txt`.
