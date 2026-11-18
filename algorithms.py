"""
algorithms.py - BFS, UCS, Greedy Best-First Search and A*.

All four algorithms follow the graph-search procedure of Appendix A.2
(tree search plus a closed set of expanded states):

  1. Insert the start node into the frontier.
  2. Remove the next node from the frontier:
         BFS    : first in, first out
         UCS    : lowest g(n)
         Greedy : lowest h(n)
         A*     : lowest f(n) = g(n) + h(n)
  3. If its cell is already in the closed set, skip it and go back to step 2.
  4. If its cell is the goal, return the solution.
  5. Otherwise add the cell to the closed set and expand it. Insert every
     successor that is not an obstacle and not already in the closed set,
     generated in the order Up, Down, Left, Right.
  6. If the frontier becomes empty, return failure.

Ties: when nodes have equal priority, the one inserted earliest is removed first.
Nodes expanded     : number of nodes added to the closed set in step 5.
Peak frontier size : largest number of nodes held in the frontier at any point,
                     including nodes that are later skipped in step 3.

All four functions share ONE interface:
    algorithm(problem, start, goal, heuristic=None, max_expanded=None)
BFS and UCS ignore the heuristic.
"""
import heapq
from collections import deque
from dataclasses import dataclass
from itertools import count

# Search status values
FOUND = "solution found"
NO_SOLUTION = "no solution"
LIMIT = "resource limit reached"


# ---------------------------------------------------------------- heuristics
def manhattan(state, goal):
    """h(n) = |xn - xg| + |yn - yg|"""
    return abs(state[0] - goal[0]) + abs(state[1] - goal[1])


def zero_heuristic(state, goal):
    """h(n) = 0. With this heuristic A* behaves like UCS."""
    return 0


HEURISTICS = {"manhattan": manhattan, "zero": zero_heuristic}


# --------------------------------------------------------------- data types
class _Node:
    """A node in the search tree."""
    __slots__ = ("state", "parent", "g")

    def __init__(self, state, parent, g):
        self.state = state      # (row, column)
        self.parent = parent    # node this one was generated from
        self.g = g              # cost from the start to this node


@dataclass
class SearchResult:
    algorithm: str
    status: str                 # FOUND, NO_SOLUTION or LIMIT
    path: list | None           # list of (row, column) cells from S to G, or None
    cost: int | None            # total path cost, or None
    expanded: int               # nodes added to the closed set
    peak_frontier: int          # largest frontier size

    @property
    def moves(self):
        """Solution length in moves."""
        return len(self.path) - 1 if self.path else None


def _route(node):
    """Route reconstruction: follow the parent links back to the start."""
    cells = []
    while node is not None:
        cells.append(node.state)
        node = node.parent
    cells.reverse()
    return cells


def _found(name, node, expanded, peak):
    return SearchResult(name, FOUND, _route(node), node.g, expanded, peak)


def _failed(name, status, expanded, peak):
    return SearchResult(name, status, None, None, expanded, peak)


# ----------------------------------------------------------------------- BFS
def bfs(problem, start, goal, heuristic=None, max_expanded=None):
    """Breadth-First Search: the frontier is a FIFO queue."""
    frontier = deque([_Node(start, None, 0)])          # step 1
    closed = set()
    expanded = 0
    peak = 1

    while frontier:                                    # step 6: empty -> failure
        node = frontier.popleft()                      # step 2: first in, first out
        if node.state in closed:                       # step 3
            continue
        if problem.is_goal(node.state):                # step 4
            return _found("BFS", node, expanded, peak)

        if max_expanded is not None and expanded >= max_expanded:
            return _failed("BFS", LIMIT, expanded, peak)
        closed.add(node.state)                         # step 5
        expanded += 1
        for _action, next_state, step in problem.successors(node.state):
            if next_state not in closed:
                frontier.append(_Node(next_state, node, node.g + step))
                peak = max(peak, len(frontier))

    return _failed("BFS", NO_SOLUTION, expanded, peak)


# ------------------------------------------------- shared priority-queue loop
def _priority_search(name, problem, start, priority, max_expanded):
    """Graph search where the frontier is a priority queue.

    'priority(node)' is the only thing that differs between UCS, Greedy and A*.
    Frontier entries are (priority, insertion number, node), so equal
    priorities are broken by the earliest insertion.
    """
    insertion = count()
    root = _Node(start, None, 0)
    frontier = [(priority(root), next(insertion), root)]   # step 1
    closed = set()
    expanded = 0
    peak = 1

    while frontier:                                        # step 6
        _, _, node = heapq.heappop(frontier)               # step 2: lowest priority
        if node.state in closed:                           # step 3
            continue
        if problem.is_goal(node.state):                    # step 4
            return _found(name, node, expanded, peak)

        if max_expanded is not None and expanded >= max_expanded:
            return _failed(name, LIMIT, expanded, peak)
        closed.add(node.state)                             # step 5
        expanded += 1
        for _action, next_state, step in problem.successors(node.state):
            if next_state not in closed:
                child = _Node(next_state, node, node.g + step)
                heapq.heappush(frontier, (priority(child), next(insertion), child))
                peak = max(peak, len(frontier))

    return _failed(name, NO_SOLUTION, expanded, peak)


# ----------------------------------------------------------------------- UCS
def ucs(problem, start, goal, heuristic=None, max_expanded=None):
    """Uniform Cost Search: remove the node with the lowest g(n)."""
    return _priority_search("UCS", problem, start,
                            lambda node: node.g, max_expanded)


# -------------------------------------------------------------------- Greedy
def greedy(problem, start, goal, heuristic=None, max_expanded=None):
    """Greedy Best-First Search: remove the node with the lowest h(n)."""
    h = heuristic or manhattan
    return _priority_search("Greedy", problem, start,
                            lambda node: h(node.state, goal), max_expanded)


# ------------------------------------------------------------------------ A*
def astar(problem, start, goal, heuristic=None, max_expanded=None):
    """A* Search: remove the node with the lowest f(n) = g(n) + h(n)."""
    h = heuristic or manhattan
    return _priority_search("A*", problem, start,
                            lambda node: node.g + h(node.state, goal), max_expanded)


ALGORITHMS = {"bfs": bfs, "ucs": ucs, "greedy": greedy, "astar": astar}
