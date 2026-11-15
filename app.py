"""Interactive Block World solver (Streamlit).

Run: streamlit run app.py
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
import html
import json
import threading

import streamlit as st

from environment import State, validate_problem
from heuristics import HEURISTICS
from search import astar, ida_star


st.set_page_config(page_title="Block World AI", page_icon="🧱", layout="wide")
st.title("🧱 Block World AI")
st.caption("A* / IDA* · optimal planning · search trace")


def parse_stacks(raw: str) -> list[list[str]]:
    """Example: D,A,B,C  or  D | A,B,C. Bottom to top."""
    groups = raw.split("|")
    stacks = [[block.strip() for block in group.split(",")] for group in groups]
    if any(not group or any(not block for block in group) for group in stacks):
        raise ValueError("Each stack must contain nonempty block names; separate stacks with |.")
    return stacks


def label_state(state: State) -> str:
    return " | ".join(",".join(stack) for stack in state)


def display_state(state: State, heading: str) -> None:
    st.markdown(f"**{heading}**")
    if not state:
        st.info("No blocks")
        return
    cells = []
    for stack in state:
        blocks = "".join(
            '<div class="bw-block">' + html.escape(block) + "</div>"
            for block in reversed(stack)
        )
        cells.append('<div class="bw-stack">' + blocks + "</div>")
    st.markdown(
        """<style>
        .bw-world {display:flex;align-items:flex-end;justify-content:center;gap:18px;
                   min-height:180px;max-width:100%;overflow-x:auto;padding:12px;
                   border:1px solid #9ba4ae55;border-radius:12px}
        .bw-stack {display:flex;flex-direction:column;justify-content:flex-end;gap:5px;
                   min-width:64px;border-bottom:3px solid #8b929b;padding:0 4px 6px}
        .bw-block {border:1px solid #497eb2;background:#c7e4fc;color:#1a3954;
                   border-radius:6px;text-align:center;font-weight:700;
                   min-width:55px;padding:7px 10px;white-space:nowrap}
        </style>"""
        + '<div class="bw-world">' + "".join(cells) + "</div>",
        unsafe_allow_html=True,
    )


def json_default(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def build_run_output(result) -> str:
    lines = [
        f"Algorithm: {result.algorithm}",
        f"Status: {result.status}",
        f"Cost: {result.cost}",
        f"Elapsed seconds: {result.elapsed_seconds:.6f}",
        f"Expanded: {result.expanded}",
        f"Generated: {result.generated}",
        f"Max frontier / DFS stack: {result.max_frontier}",
        f"Path improvements: {result.improvements}",
        f"IDA* iterations: {result.iterations}",
        "Actions:",
    ]
    for index, move in enumerate(result.moves, 1):
        lines.append(
            f"{index}. Move {move.block} from {move.source} to {move.destination}; total cost={index}"
        )
    return "\n".join(lines) + "\n"


def execute(holder: dict, cancel_event: threading.Event,
            start: State, goal: State, algo: str, h_name: str,
            limit: int, timeout: float) -> None:
    try:
        function = astar if algo == "A*" else ida_star
        result = function(
            start, goal, HEURISTICS[h_name],
            max_expansions=limit, timeout_seconds=timeout,
            cancelled=cancel_event.is_set, record_trace=True,
        )
        holder["result"] = result
    except Exception as exc:
        holder["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        holder["done"] = True


if "job" not in st.session_state:
    st.session_state.job = None

st.markdown("Stacks are entered **bottom to top**. Use `|` between stacks and commas between blocks.")
st.info("Example: initial `D,A,B,C`, goal `D | A,B,C`. The order of stacks on the table is irrelevant.")


@st.fragment(run_every="0.5s")
def workspace() -> None:
    running_job = st.session_state.job
    busy = running_job is not None and not running_job["holder"]["done"]
    left, right = st.columns(2)
    with left:
        initial_raw = st.text_input("Initial stacks", value="D,A,B,C", disabled=busy)
    with right:
        goal_raw = st.text_input("Goal stacks", value="D | A,B,C", disabled=busy)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        algorithm = st.selectbox("Algorithm", ["A*", "IDA*"], disabled=busy)
    with c2:
        heuristic_name = st.selectbox("Heuristic", ["h0", "h1", "h2"], index=2, disabled=busy)
    with c3:
        max_expansions = st.number_input("Expansion limit", 1, 1_000_000, 50_000, 1000, disabled=busy)
    with c4:
        timeout_seconds = st.number_input("Timeout (seconds)", 1, 3600, 20, 1, disabled=busy)

    actions_col, cancel_col = st.columns([2, 1])
    with actions_col:
        if st.button("▶ Run search", type="primary", disabled=busy, use_container_width=True):
            try:
                start, goal = validate_problem(parse_stacks(initial_raw), parse_stacks(goal_raw))
            except ValueError as exc:
                st.error(f"Invalid input: {exc}")
            else:
                cancel_event = threading.Event()
                holder = {"result": None, "error": None, "done": False}
                thread = threading.Thread(
                    target=execute,
                    args=(holder, cancel_event, start, goal, algorithm, heuristic_name,
                          int(max_expansions), float(timeout_seconds)),
                    daemon=True,
                )
                st.session_state.job = {
                    "holder": holder,
                    "thread": thread,
                    "cancel_event": cancel_event,
                    "start": start,
                    "goal": goal,
                    "algorithm": algorithm,
                    "heuristic": heuristic_name,
                }
                st.session_state.pop("step_slider", None)
                thread.start()
                st.rerun(scope="fragment")

    with cancel_col:
        if st.button("■ Stop", disabled=not busy, use_container_width=True):
            running_job["cancel_event"].set()
            st.warning("Cancellation requested. Waiting for the algorithm to stop.")

    job = st.session_state.job
    if job is None:
        st.info("Configure the problem and press Run search.")
        return
    holder = job["holder"]
    if not holder["done"]:
        st.info("Search is running. You may press Stop to cancel it.")
        return
    if holder["error"]:
        st.error(holder["error"])
        return
    result = holder["result"]
    if result is None:
        st.error("No result was returned.")
        return

    translations = {
        "solved": "Solution found",
        "timeout": "Stopped: time limit reached (not 'no solution')",
        "expansion_limit": "Stopped: expansion limit reached (not 'no solution')",
        "cancelled": "Stopped by user (not 'no solution')",
        "unsolvable": "No solution exists",
    }
    if result.status == "solved":
        st.success(f"{translations[result.status]} · optimal cost: {result.cost}")
    else:
        st.warning(translations.get(result.status, result.status))

    metrics = [
        ("Time (s)", f"{result.elapsed_seconds:.4f}"),
        ("Generated", str(result.generated)),
        ("Expanded", str(result.expanded)),
        ("Max priority queue" if result.algorithm == "A*" else "Max DFS stack", str(result.max_frontier)),
        ("Improved paths", str(result.improvements)),
        ("IDA* iterations", str(result.iterations)),
    ]
    columns = st.columns(3)
    for i, (name, value) in enumerate(metrics):
        columns[i % 3].metric(name, value)

    st.divider()
    st.subheader("States and solution actions")
    display_state(job["start"], "Initial")
    display_state(job["goal"], "Goal")

    if result.status == "solved":
        maximum = len(result.moves)
        selected_step = st.slider("Walk through the solution", 0, maximum,
                                  value=0, key="step_slider")
        back, forward = st.columns(2)
        with back:
            st.button("◀ Previous step", disabled=selected_step == 0,
                      on_click=lambda: st.session_state.update(step_slider=max(0, st.session_state.step_slider - 1)))
        with forward:
            st.button("Next step ▶", disabled=selected_step == maximum,
                      on_click=lambda: st.session_state.update(step_slider=min(maximum, st.session_state.step_slider + 1)))
        display_state(result.states[selected_step], f"Step {selected_step} of {maximum}")
        if selected_step:
            move = result.moves[selected_step - 1]
            st.write(f"Move **{move.block}**: **{move.source} → {move.destination}**; cumulative cost: **{selected_step}**")
        st.dataframe(
            [
                {"Step": i, "Block": m.block, "Source": m.source,
                 "Destination": m.destination, "Cumulative cost": i}
                for i, m in enumerate(result.moves, 1)
            ],
            use_container_width=True, hide_index=True,
        )

    st.divider()
    st.subheader("Search trace")
    if result.algorithm == "A*":
        trace = result.trace
        st.caption("Order of states popped from the priority queue (stale entries excluded).")
        rows = []
        for i, entry in enumerate(trace):
            action = entry.get("incoming_move")
            rows.append({
                "#": i + 1, "State": label_state(entry["state"]),
                "g": entry["g"], "h": entry["h"], "f": entry["f"],
                "Open size": entry["open_size"],
                "Incoming action": (
                    f"{action.block}: {action.source} → {action.destination}" if action else "start"
                ),
            })
        st.dataframe(rows, hide_index=True, use_container_width=True, height=280)
        if trace:
            index = st.number_input("Inspect popped state #", 1, len(trace), 1)
            entry = trace[int(index) - 1]
            st.dataframe(
                [{"Action": f"{x['move'].block}: {x['move'].source} → {x['move'].destination}",
                  "Next state": label_state(x["state"]), "Status": x["status"]}
                 for x in entry["successors"]],
                hide_index=True, use_container_width=True,
            )
    else:
        trace = result.trace
        rows = [
            {"Iteration": i + 1, "Threshold": x["threshold"],
             "Expanded": x["expanded"], "Pruned": x["prunes"],
             "Next threshold": x["next_threshold"]}
            for i, x in enumerate(trace)
        ]
        st.dataframe(rows, hide_index=True, use_container_width=True)
        if trace:
            iteration_number = st.selectbox("Inspect IDA* iteration", list(range(1, len(trace) + 1)))
            entries = trace[iteration_number - 1]["events"]
            only_pruned = st.checkbox("Show only pruning events")
            if only_pruned:
                entries = [x for x in entries if "pruned" in x["status"]]
            st.dataframe(
                [{"State": label_state(x["state"]),
                  "g": x.get("g"), "h": x.get("h"), "f": x.get("f"),
                  "Event": x["status"]}
                 for x in entries],
                hide_index=True, use_container_width=True, height=300,
            )

    st.divider()
    st.subheader("Save evidence for the report")
    st.download_button("Download run output (.txt)", build_run_output(result),
                       file_name="part_d_run.txt", mime="text/plain")
    st.download_button("Download search trace (.json)",
                       json.dumps({"algorithm": result.algorithm, "status": result.status,
                                   "trace": result.trace}, ensure_ascii=False,
                                  indent=2, default=json_default),
                       file_name="part_d_trace.json", mime="application/json")


workspace()
