# TMN3233 Assignment - Campus Delivery Robot Search 

Pair Group: **[Group 20]**
Students: **[Mohamad Irman bin Bally, 105019]**, **[Muhammad Asyraf bin Ismawi, 102726]**

## Environment

- Python version: **[Python 3.15.2]**
- Operating system: **[Windows 11]**
- Third-party package: `matplotlib` (for plots), see `requirements.txt`
- No internet connection is needed to run the program.

## Files

| File | Purpose |
|---|---|
| `problem.py` | Problem formulation (state, actions, transition, goal test, path cost), map loading and validation, route validation |
| `algorithms.py` | BFS, UCS, Greedy Best-First and A* (one common interface), heuristics (Manhattan, zero) |
| `visualise.py` | Static plot of the map, start, goal and route (matplotlib) |
| `search_runner.py` | Run one algorithm on one map |
| `experiment_runner.py` | Run the experiments (Task B and Task C) and save CSV results |
| `test_search.py` | Correctness checks (`python -m unittest -v`) |
| `maps/map1.txt` ... `maps/map6.txt` | The six provided test maps, unmodified |

## Installation

```
python -m pip install -r requirements.txt
```
(`py -m pip install -r requirements.txt` also can be used on Windows)

## Run one algorithm on one map

```
python search_runner.py --algo bfs --map maps/map1.txt
python search_runner.py --algo ucs --map maps/map5.txt
python search_runner.py --algo greedy --map maps/map4.txt
python search_runner.py --algo astar --map maps/map4.txt --heuristic manhattan
```
`--algo` is one of `bfs`, `ucs`, `greedy`, `astar`.
`--heuristic` is `manhattan` (default) or `zero` and is used by `greedy` and `astar`.

The program prints the status, solution length in moves, total path cost, nodes
expanded, peak frontier size and the route.

Save a picture of the route (Task A):
```
python search_runner.py --algo astar --map maps/map4.txt --plot route_map4_astar.png
```
Use `--show` to open the picture in a window instead.

## Run the experiments

Task B - BFS, UCS, Greedy and A* (Manhattan) on all six maps, 5 repeats:
```
python experiment_runner.py --repeats 5 --output results.csv
```

Task C - A* heuristic comparison, h(n) = 0 versus Manhattan distance:
```
python experiment_runner.py --repeats 5 --heuristic-comparison --output heuristic_results.csv
```

Optional: also save a route picture for every run:
```
python experiment_runner.py --repeats 5 --output results.csv --plots-dir plots
```

### Output files (the located folder where you run the command)

| File | Content |
|---|---|
| `results.csv` | One row per map and algorithm: status, moves, cost, nodes expanded, peak frontier, **median runtime**, route |
| `results_raw.csv` | **Raw results:** one row for every single repeat |
| `results_environment.txt` | Python version, operating system, processor, repeats, resource limit |
| `plots/` | Route pictures (only with `--plots-dir`) |

The same three files, with the chosen name, are written for the heuristic comparison.

## The Rules followed

- Maps are read withint the format. S and G cost 1 to enter; a move costs the cost of the
  cell entered; the starting cell contributes 0.
- All four algorithms follow the graph-search procedure (tree search plus a closed set),
  with successors in the order Up, Down, Left, Right.
- Connection are broken when removing the node that was inserted earliest.
- Nodes expanded = nodes added to the closed set. Peak frontier size = largest number of
  nodes in the frontier at any point, including nodes later skipped.
- Runtime is the median of the repeats. Only the search call is timed (map loading,
  route validation and plotting are excluded).
- Every returned route is checked by an independent validator (correct start and goal, legal moves,
  no obstacles, cost recalculated from the map).
- Resource limit: 1,000,000 expanded nodes per run for more consistent result (`--max-expanded`).

## Check the code

```
python -m unittest -v
```
