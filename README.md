# Block World AI

Academic search/planning project. **Current milestone: Part A — environment model only.** A* and IDA* algorithms, heuristics, visual UI, experiments and final report are planned but not implemented yet.

## Requirements

Python 3.10+; standard library only for this milestone.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Model

A state consists of stacks, each ordered **bottom-to-top**. Stack order on the table is irrelevant and is canonicalized lexicographically. Only a top block can be moved. It can be placed onto the table as a new stack or on top of a different stack. Every move costs 1.

See `PART_A_HE.md` for Hebrew theoretical explanations.
