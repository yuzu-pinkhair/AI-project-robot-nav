import sys

if sys.version_info < (3, 10):
    sys.exit("Python 3.10 or newer is required.") #for python version check

import argparse
import csv
import os
import platform
import statistics
import time
from pathlib import Path

from algorithms import ALGORITHMS, HEURISTICS
from problem import GridProblem, MapError, RouteError, load_map, route_cost

MAP_NAMES = [f"map{i}.txt" for i in range(1, 7)]

# What to run: (algorithm, heuristic name or None)
MAIN_EXPERIMENT = [("bfs", None), ("ucs", None), ("greedy", "manhattan"), ("astar", "manhattan")]
HEURISTIC_EXPERIMENT = [("astar", "zero"), ("astar", "manhattan")]

DEFAULT_RESOURCE_LIMIT = 1_000_000      # same limit for every run (max expanded nodes)


def find_maps_dir(requested):
    """Use --maps-dir if given, otherwise 'maps' if it exists, otherwise this folder."""
    if requested:
        return Path(requested)
    return Path("maps") if Path("maps").is_dir() else Path(".")


def same_outcome(a, b):
    """True when two results are identical (used to check repeatability)."""
    return (a.status, a.path, a.expanded, a.peak_frontier) == (b.status, b.path, b.expanded, b.peak_frontier)


def measure(problem, algorithm, heuristic_name, repeats, max_expanded):
    """Run one algorithm 'repeats' times. Only the search call is timed."""
    function = ALGORITHMS[algorithm]
    heuristic = HEURISTICS[heuristic_name] if heuristic_name else None
    runs = []
    for run in range(1, repeats + 1):
        started = time.perf_counter()
        result = function(problem, problem.start, problem.goal, heuristic, max_expanded)
        elapsed_ms = (time.perf_counter() - started) * 1000
        runs.append((run, elapsed_ms, result))
    return runs


def check_route(problem, result):
    """Route validation, done OUTSIDE the timing."""
    if result.path is None:
        return
    if route_cost(problem, result.path) != result.cost:
        raise RouteError("the cost reported by the search does not match the route")


def route_text(path):
    return " ".join(f"({r},{c})" for r, c in path) if path else ""


def write_environment(path, args, experiment):
    lines = [
        f"Python version   : {platform.python_version()}",
        f"Operating system : {platform.platform()}",
        f"Processor        : {platform.processor() or 'unknown'}",
        f"CPU cores        : {os.cpu_count()}",
        f"Experiment       : {'A* heuristic comparison (Task C)' if args.heuristic_comparison else 'four algorithms (Task B)'}",
        f"Configurations   : {', '.join(a + ('/' + h if h else '') for a, h in experiment)}",
        f"Repeats per run  : {args.repeats} (median runtime reported)",
        f"Resource limit   : {args.max_expanded} expanded nodes",
        "Timing           : search call only (map loading, validation and plots excluded)",
    ]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser():
    parser = argparse.ArgumentParser(description="Run the search experiments on the six test maps.")
    parser.add_argument("--repeats", type=int, default=5, help="timing repeats (at least 5; default 5)")
    parser.add_argument("--output", default="results.csv", help="summary CSV file (default results.csv)")
    parser.add_argument("--maps-dir", help="folder with map1.txt ... map6.txt (default: maps/ or this folder)")
    parser.add_argument("--heuristic-comparison", action="store_true",
                        help="run Task C: A* with h=0 versus A* with Manhattan distance")
    parser.add_argument("--max-expanded", type=int, default=DEFAULT_RESOURCE_LIMIT,
                        help="resource limit (maximum expanded nodes per run)")
    parser.add_argument("--plots-dir", help="also save a route picture for every run into this folder")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.repeats < 1:
        print("--repeats must be at least 1.")
        return 2
    if args.repeats < 5:
        print(f"Warning: the assignment asks for at least 5 repeats (you chose {args.repeats}).")

    experiment = HEURISTIC_EXPERIMENT if args.heuristic_comparison else MAIN_EXPERIMENT
    maps_dir = find_maps_dir(args.maps_dir)

    summary_rows, raw_rows, plot_jobs = [], [], []

    for map_name in MAP_NAMES:
        try:
            grid = load_map(maps_dir / map_name)
            problem = GridProblem(grid)
        except MapError as error:
            print(f"Map error: {error}")
            return 2

        for algorithm, heuristic_name in experiment:
            runs = measure(problem, algorithm, heuristic_name, args.repeats, args.max_expanded)
            first = runs[0][2]
            try:
                for _run, _ms, result in runs:
                    check_route(problem, result)
            except RouteError as error:
                print(f"Internal error on {map_name} with {algorithm}: {error}")
                return 3

            heuristic_label = heuristic_name or "n/a"
            consistent = all(same_outcome(first, result) for _r, _m, result in runs)
            median_ms = statistics.median(ms for _run, ms, _res in runs)

            for run, ms, result in runs:                       # raw measurements
                raw_rows.append({
                    "map": map_name, "algorithm": result.algorithm, "heuristic": heuristic_label,
                    "run": run, "status": result.status, "runtime_ms": round(ms, 4),
                    "expanded": result.expanded, "peak_frontier": result.peak_frontier,
                    "moves": result.moves if result.moves is not None else "",
                    "cost": result.cost if result.cost is not None else "",
                })

            summary_rows.append({
                "map": map_name, "algorithm": first.algorithm, "heuristic": heuristic_label,
                "status": first.status,
                "moves": first.moves if first.moves is not None else "",
                "cost": first.cost if first.cost is not None else "",
                "expanded": first.expanded, "peak_frontier": first.peak_frontier,
                "runtime_median_ms": round(median_ms, 4), "repeats": args.repeats,
                "same_result_every_run": consistent,
                "route": route_text(first.path),
            })
            plot_jobs.append((grid, map_name, algorithm, heuristic_name, first))

    # ---- save the CSV files ----
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)      # create the folder if needed
    raw_path = output.with_name(output.stem + "_raw.csv")
    env_path = output.with_name(output.stem + "_environment.txt")

    for path, rows in ((output, summary_rows), (raw_path, raw_rows)):
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    write_environment(env_path, args, experiment)

    # ---- show a short table ----
    print(f"{'map':9} {'algorithm':8} {'heuristic':10} {'status':15} {'moves':>5} {'cost':>5} "
          f"{'expanded':>8} {'peak':>5} {'median ms':>10}")
    for row in summary_rows:
        print(f"{row['map']:9} {row['algorithm']:8} {row['heuristic']:10} {row['status']:15} "
              f"{str(row['moves']):>5} {str(row['cost']):>5} {row['expanded']:>8} "
              f"{row['peak_frontier']:>5} {row['runtime_median_ms']:>10}")
    print(f"\nSaved: {output}  |  {raw_path}  |  {env_path}")

    # --------- optional route diagram for visualisation of data  ----------
    if args.plots_dir:
        try:
            from visualise import plot_route
            Path(args.plots_dir).mkdir(parents=True, exist_ok=True)
            for grid, map_name, algorithm, heuristic_name, result in plot_jobs:
                label = algorithm + (f"_{heuristic_name}" if heuristic_name else "")
                title = f"{result.algorithm} on {map_name}: " + (
                    f"cost {result.cost}, {result.moves} moves" if result.path else result.status)
                plot_route(grid, result.path, title,
                           Path(args.plots_dir) / f"{map_name.replace('.txt', '')}_{label}.png")
            print(f"Route pictures saved in: {args.plots_dir}/")
        except RuntimeError as error:
            print(f"Plots skipped: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
