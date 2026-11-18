import sys

if sys.version_info < (3, 10):
    sys.exit("Python 3.10 or newer is required.")

import argparse

from algorithms import ALGORITHMS, FOUND, HEURISTICS, LIMIT
from problem import GridProblem, MapError, RouteError, load_map, route_cost


def build_parser():
    parser = argparse.ArgumentParser(description="Run one search algorithm on one map.")
    parser.add_argument("--algo", required=True, choices=sorted(ALGORITHMS),
                        help="search algorithm")
    parser.add_argument("--map", required=True, help="path to the map file, e.g. maps/map1.txt")
    parser.add_argument("--heuristic", choices=sorted(HEURISTICS), default="manhattan",
                        help="heuristic for greedy and astar (default: manhattan)")
    parser.add_argument("--max-expanded", type=int, default=None,
                        help="resource limit: stop after this many expanded nodes")
    parser.add_argument("--plot", metavar="FILE", help="save a picture of the route (e.g. route.png)")
    parser.add_argument("--show", action="store_true", help="open the picture in a window")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    # --- load and validate the map ---
    try:
        grid = load_map(args.map)
        problem = GridProblem(grid)
    except MapError as error:
        print(f"Map error: {error}")
        return 2

    # --- run the search ---
    uses_heuristic = args.algo in ("greedy", "astar")
    result = ALGORITHMS[args.algo](problem, problem.start, problem.goal,
                                   HEURISTICS[args.heuristic], args.max_expanded)

    # --- validate the route (independent of the search code) ---
    if result.status == FOUND:
        try:
            checked_cost = route_cost(problem, result.path)
        except RouteError as error:
            print(f"Internal error: the returned route is not valid: {error}")
            return 3
        if checked_cost != result.cost:
            print(f"Internal error: cost mismatch ({result.cost} vs {checked_cost}).")
            return 3

    # --- report ---
    print(f"Map              : {args.map}  ({problem.rows} rows x {problem.cols} columns)")
    print(f"Start / Goal     : {problem.start} / {problem.goal}")
    print(f"Algorithm        : {result.algorithm}"
          + (f"  (heuristic: {args.heuristic})" if uses_heuristic else ""))
    print(f"Status           : {result.status}")
    if result.status == FOUND:
        print(f"Solution length  : {result.moves} moves")
        print(f"Total path cost  : {result.cost}")
    print(f"Nodes expanded   : {result.expanded}")
    print(f"Peak frontier    : {result.peak_frontier}")
    if result.status == FOUND:
        print("Route            : " + " -> ".join(f"({r},{c})" for r, c in result.path))
    elif result.status == LIMIT:
        print("The search stopped because the resource limit was reached.")
    else:
        print("The goal cannot be reached from the start.")

    # --- optional picture ---
    if args.plot or args.show:
        try:
            from visualise import plot_route
            title = f"{result.algorithm} on {args.map}: " + (
                f"cost {result.cost}, {result.moves} moves" if result.status == FOUND else result.status)
            plot_route(grid, result.path, title, args.plot, args.show)
            if args.plot:
                print(f"Picture saved    : {args.plot}")
        except RuntimeError as error:
            print(f"Plot skipped: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
