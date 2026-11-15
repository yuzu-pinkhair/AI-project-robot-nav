"""
Tree-based search for a robot on a puzzle map.
Algorithms : Greedy Best-First Search and A* Search
Heuristic  : Manhattan distance  h(n) = |xn - xg| + |yn - yg|
Goal       : the robot must reach ANY one of the goals (cells marked G)
Output     : one CSV file only (results.csv)

Libraries used (all allowed by the assignment rules):
    heapq  -> priority queue
    csv    -> data storage
    time   -> measuring running time
The search algorithm itself is written by hand (no ready-made search library).
"""
import csv
import heapq
import time

# List of map files to test. range(1, 8) means map1.txt ... map7.txt
MAP_FILES = [f"map{i}.txt" for i in range(1, 8)]

# Name of the CSV file that will be created
OUTPUT_FILE = "results.csv"


# =====================================================================
# PART 1: MAP HELPERS
# =====================================================================

def load_map(path):
    """Read a map file and return it as a list of rows (each row is a list of cells).

    Example line "S 1 X 3" becomes ["S", "1", "X", "3"].
    Empty lines are ignored.
    """
    with open(path) as f:
        return [line.split() for line in f if line.strip()]


def find_all(grid, symbol):
    """Return the (row, col) of every cell that matches the symbol.

    We use this to find S (start) and ALL the G cells (goals).
    """
    return [(r, c) for r, row in enumerate(grid)
                   for c, cell in enumerate(row) if cell == symbol]


def cost(grid, cell):
    """Return the cost of ENTERING a cell.

    S and G cost 1. Other cells cost the number written in them (1, 3 or 5).
    """
    value = grid[cell[0]][cell[1]]
    return 1 if value in ("S", "G") else int(value)


def neighbours(grid, cell):
    """Yield every cell the robot can move to from 'cell'.

    The robot moves up, down, left or right (no diagonals).
    It cannot leave the map and cannot enter an obstacle (X).
    """
    rows, cols = len(grid), len(grid[0])
    r, c = cell
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:   # up, down, left, right
        nr, nc = r + dr, c + dc
        # Check the map edges FIRST, then check for an obstacle.
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != "X":
            yield (nr, nc)


# =====================================================================
# PART 2: HEURISTIC
# =====================================================================

def manhattan(a, b):
    """Manhattan distance between two cells: |row difference| + |column difference|."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def heuristic(cell, goals):
    """h(n): Manhattan distance from 'cell' to the NEAREST goal.

    With several goals we take the minimum, so the estimate never
    overestimates the real cost to the closest goal (admissible).
    """
    return min(manhattan(cell, g) for g in goals)


# =====================================================================
# PART 3: SEARCH TREE NODE
# =====================================================================

class Node:
    """One node in the search tree.

    state  : the robot's position (row, col)
    parent : the node this one was created from (None for the root)
    g      : total cost from the start to this node
    """

    def __init__(self, state, parent=None, g=0):
        self.state = state
        self.parent = parent
        self.g = g

    def path(self):
        """Return the list of cells from the start to this node.

        We follow the parent links backwards, then reverse the list.
        """
        cells, node = [], self
        while node is not None:
            cells.append(node.state)
            node = node.parent
        cells.reverse()
        return cells

    def on_path(self, state):
        """Return True if 'state' is already on the path from the root to this node.

        This is the cycle check. Tree search does not remember visited cells
        globally, so without this the robot could walk back and forth forever.
        """
        node = self
        while node is not None:
            if node.state == state:
                return True
            node = node.parent
        return False


# =====================================================================
# PART 4: TREE SEARCH (Greedy and A*)
# =====================================================================

def tree_search(grid, start, goals, mode):
    """Search for a path from 'start' to ANY cell in 'goals'.

    mode = "greedy" -> priority f(n) = h(n)
    mode = "astar"  -> priority f(n) = g(n) + h(n)

    Returns: (path, total_cost, expanded, generated)
        expanded  = nodes removed from the frontier and examined
        generated = nodes created and added to the frontier
    If no path exists, path is None.
    """
    root = Node(start)

    # 'counter' is a tie-breaker. If two nodes have the same priority,
    # heapq would try to compare the Node objects and crash.
    # A unique counter number always decides the tie first.
    counter = 0

    # The frontier is a priority queue of (priority, counter, node).
    # heapq always gives back the entry with the smallest priority.
    frontier = [(heuristic(start, goals), counter, root)]

    expanded, generated = 0, 1      # the root counts as 1 generated node

    while frontier:
        # Take the most promising node out of the frontier.
        _, _, node = heapq.heappop(frontier)
        expanded += 1

        # Goal test: is the robot standing on ANY goal?
        # (Done when the node is removed, which keeps A* optimal.)
        if node.state in goals:
            return node.path(), node.g, expanded, generated

        # Expand the node: create a child for every cell the robot can move to.
        for nxt in neighbours(grid, node.state):
            # Cycle check: do not step back onto a cell already on this branch.
            if node.on_path(nxt):
                continue

            # The child's cost so far = parent's cost + cost of entering the new cell.
            child = Node(nxt, node, node.g + cost(grid, nxt))

            # h(n) = estimated distance from the new cell to the nearest goal.
            h = heuristic(nxt, goals)

            # THE ONLY DIFFERENCE between the two algorithms:
            #   Greedy : priority = h        (only looks at the estimate)
            #   A*     : priority = g + h    (cost so far + estimate)
            priority = h if mode == "greedy" else child.g + h

            counter += 1
            heapq.heappush(frontier, (priority, counter, child))
            generated += 1

    # The frontier is empty and no goal was reached: there is no path.
    return None, 0, expanded, generated


# =====================================================================
# PART 5: MAIN PROGRAM (run every map with both algorithms, save CSV)
# =====================================================================

def main():
    rows_out = []       # each item will become one row in the CSV file

    for filename in MAP_FILES:
        grid = load_map(filename)
        start = find_all(grid, "S")[0]      # there is only one start
        goals = find_all(grid, "G")         # there can be several goals

        for mode in ("greedy", "astar"):
            # Measure how long the search takes (in milliseconds).
            t0 = time.perf_counter()
            path, total, expanded, generated = tree_search(grid, start, goals, mode)
            ms = (time.perf_counter() - t0) * 1000

            found = path is not None

            # Build one CSV row. If no path was found, the path-related
            # columns are left empty.
            rows_out.append({
                "map": filename.replace(".txt", ""),
                "algorithm": mode,
                "found": found,
                # path[-1] is the last cell = the goal that was reached.
                # Written as "row-col" so the comma does not split the column.
                "goal_reached": f"{path[-1][0]}-{path[-1][1]}" if found else "",
                "cost": total if found else "",
                "steps": len(path) - 1 if found else "",   # moves = cells - 1
                "expanded": expanded,
                "generated": generated,
                "time_ms": round(ms, 3),
                "path": " ".join(f"({r},{c})" for r, c in path) if found else "",
            })

    # Write all rows to the CSV file.
    # newline="" stops Windows from adding blank lines between rows.
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows_out[0].keys())
        writer.writeheader()      # first line: column names
        writer.writerows(rows_out)

    print(f"Saved {OUTPUT_FILE}")


# Run main() only when this file is run directly (not when imported).
if __name__ == "__main__":
    main()