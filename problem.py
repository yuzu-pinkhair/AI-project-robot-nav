"""
This section is for map handling.

"""
from pathlib import Path

# Appendix A.2: successors are generated in the fixed order Up, Down, Left, Right.
ACTIONS = (("Up", -1, 0), ("Down", 1, 0), ("Left", 0, -1), ("Right", 0, 1))

# Cost of entering a cell. S and G are normal walkway cells (cost 1).
CELL_COST = {"S": 1, "G": 1, "1": 1, "3": 3, "5": 5}
VALID_SYMBOLS = set(CELL_COST) | {"X"}


class MapError(ValueError):
    """Error action when a map file cannot be read or it is not a valid map."""


class RouteError(ValueError):
    """This happen when returned value breaks the route movement rules."""


def validate_grid(grid):
    """Check a map (list of rows). Raise MapError with a clear message if invalid."""
    if not grid:
        raise MapError("The map is empty.")

    width = len(grid[0])
    for row_number, row in enumerate(grid):
        if len(row) != width:
            raise MapError(
                f"Row {row_number} has {len(row)} cells but row 0 has {width}. "
                "All rows must have the same length.")
        for column_number, symbol in enumerate(row):
            if symbol not in VALID_SYMBOLS:
                raise MapError(
                    f"Invalid symbol '{symbol}' at (row {row_number}, column {column_number}). "
                    "Allowed symbols: S G 1 3 5 X.")

    for symbol, name in (("S", "start"), ("G", "goal")):
        count = sum(row.count(symbol) for row in grid)
        if count != 1:
            raise MapError(f"The map must contain exactly one {symbol} ({name}), found {count}.")


def load_map(path):
    """Read a map file (one row per line, cells separated by spaces) and validate it."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise MapError(f"Cannot read map file '{path}': {error.strerror or error}") from error

    grid = [line.split() for line in text.splitlines() if line.strip()]
    validate_grid(grid)
    return grid


class GridProblem:
    """The campus delivery problem on one map."""

    def __init__(self, grid):
        validate_grid(grid)
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.start = self._locate("S")      # initial state
        self.goal = self._locate("G")

    def _locate(self, symbol):
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                if cell == symbol:
                    return (r, c)

    def is_goal(self, state):
        """Goal test."""
        return state == self.goal

    def passable(self, state):
        """True if the cell is on the map and is not an obstacle."""
        r, c = state
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] != "X"

    def step_cost(self, state):
        """Cost of entering this cell."""
        return CELL_COST[self.grid[state[0]][state[1]]]

    def successors(self, state):
        """Yield (action, next_state, step_cost) in the order Up, Down, Left, Right."""
        r, c = state
        for name, dr, dc in ACTIONS:
            next_state = (r + dr, c + dc)
            if self.passable(next_state):
                yield name, next_state, self.step_cost(next_state)


def route_cost(problem, path): #validate a route and return its total cost

    if not path:
        raise RouteError("The route is empty.")
    if path[0] != problem.start:
        raise RouteError(f"The route starts at {path[0]}, not at S {problem.start}.")
    if path[-1] != problem.goal:
        raise RouteError(f"The route ends at {path[-1]}, not at G {problem.goal}.")

    total = 0
    for before, after in zip(path, path[1:]):
        if abs(before[0] - after[0]) + abs(before[1] - after[1]) != 1:
            raise RouteError(f"Illegal move from {before} to {after}.")
        if not problem.passable(after):
            raise RouteError(f"The route enters an obstacle or leaves the map at {after}.")
        total += problem.step_cost(after)
    return total
