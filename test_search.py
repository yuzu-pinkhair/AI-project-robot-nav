"""
This section is to check if it run according to the rules. 

"""
import tempfile
import unittest
from pathlib import Path

from algorithms import (ALGORITHMS, FOUND, HEURISTICS, LIMIT, NO_SOLUTION,
                        astar, bfs, greedy, ucs)
from problem import GridProblem, MapError, RouteError, load_map, route_cost

HERE = Path(__file__).parent
MAPS_DIR = HERE / "maps" if (HERE / "maps").is_dir() else HERE

# Start and goal of the six maps
START_GOAL = {1: ((0, 0), (4, 4)), 2: ((0, 0), (9, 9)), 3: ((0, 0), (8, 10)),
              4: ((2, 0), (2, 8)), 5: ((0, 0), (7, 9)), 6: ((0, 0), (4, 4))}


def problem_for(number):
    return GridProblem(load_map(MAPS_DIR / f"map{number}.txt"))


def run_all(problem, heuristic="manhattan"):
    return {name: function(problem, problem.start, problem.goal, HEURISTICS[heuristic])
            for name, function in ALGORITHMS.items()}


class MapHandling(unittest.TestCase):
    def test_provided_maps_load_with_correct_start_and_goal(self):
        for number, (start, goal) in START_GOAL.items():
            problem = problem_for(number)
            self.assertEqual((problem.start, problem.goal), (start, goal), f"map{number}")

    def test_invalid_maps_are_rejected(self):
        bad_maps = {
            "empty": "",
            "ragged rows": "S 1 1\n1 X\n",
            "bad symbol": "S 1 Q\n1 X G\n",
            "no start": "1 1 1\n1 X G\n",
            "two goals": "S 1 G\n1 X G\n",
            "two starts": "S 1 G\n1 X S\n",
        }
        with tempfile.TemporaryDirectory() as folder:
            for name, text in bad_maps.items():
                path = Path(folder) / "bad.txt"
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(MapError, msg=name):
                    load_map(path)
        with self.assertRaises(MapError):
            load_map(Path("this_file_does_not_exist.txt"))


class ProblemRules(unittest.TestCase):
    def test_successor_order_is_up_down_left_right(self):
        problem = GridProblem([["S", "1", "1"], ["1", "1", "1"], ["1", "1", "G"]])
        actions = [action for action, _state, _cost in problem.successors((1, 1))]
        self.assertEqual(actions, ["Up", "Down", "Left", "Right"])

    def test_obstacles_and_edges_are_not_successors(self):
        problem = GridProblem([["S", "X"], ["1", "G"]])
        self.assertEqual([s for _a, s, _c in problem.successors((0, 0))], [(1, 0)])

    def test_cost_of_entering_cells(self):
        problem = GridProblem([["S", "3", "5", "G"]])
        self.assertEqual(route_cost(problem, [(0, 0), (0, 1), (0, 2), (0, 3)]), 3 + 5 + 1)  # start costs 0, G costs 1

    def test_route_validator_rejects_bad_routes(self):
        problem = GridProblem([["S", "1", "X"], ["1", "1", "G"]])
        bad_routes = [
            [(0, 1), (1, 1), (1, 2)],            # does not start at S
            [(0, 0), (0, 1), (1, 1)],            # does not end at G
            [(0, 0), (1, 1), (1, 2)],            # diagonal jump
            [(0, 0), (0, 1), (0, 2), (1, 2)],    # enters an obstacle
        ]
        for route in bad_routes:
            with self.assertRaises(RouteError, msg=str(route)):
                route_cost(problem, route)


class SearchBehaviour(unittest.TestCase):
    def test_every_returned_route_is_valid_and_cost_matches(self):
        for number in range(1, 6):
            problem = problem_for(number)
            for name, result in run_all(problem).items():
                self.assertEqual(result.status, FOUND, f"map{number} {name}")
                self.assertEqual(route_cost(problem, result.path), result.cost, f"map{number} {name}")

    def test_bfs_has_fewest_moves_and_ucs_has_lowest_cost(self):
        for number in range(1, 6):
            results = run_all(problem_for(number))
            for name, result in results.items():
                self.assertLessEqual(results["bfs"].moves, result.moves, f"map{number} {name}")
                self.assertLessEqual(results["ucs"].cost, result.cost, f"map{number} {name}")

    def test_astar_with_manhattan_is_optimal(self):
        for number in range(1, 6):
            results = run_all(problem_for(number))
            self.assertEqual(results["astar"].cost, results["ucs"].cost, f"map{number}")

    def test_astar_with_zero_heuristic_behaves_like_ucs(self):
        for number in range(1, 7):
            problem = problem_for(number)
            a = astar(problem, problem.start, problem.goal, HEURISTICS["zero"])
            u = ucs(problem, problem.start, problem.goal)
            self.assertEqual((a.status, a.path, a.expanded, a.peak_frontier),
                             (u.status, u.path, u.expanded, u.peak_frontier), f"map{number}")

    def test_map4_weighted_shortest_route_is_not_cheapest(self):
        results = run_all(problem_for(4))
        self.assertEqual((results["bfs"].moves, results["bfs"].cost), (8, 36))
        self.assertEqual(results["ucs"].cost, 12)
        self.assertEqual(results["greedy"].cost, 36)
        self.assertEqual(results["astar"].cost, 12)

    def test_map5_costs(self):
        results = run_all(problem_for(5))
        self.assertEqual(results["ucs"].cost, 26)
        self.assertEqual(results["astar"].cost, 26)
        self.assertGreater(results["greedy"].cost, 26)

    def test_unreachable_goal_on_map6(self):
        for name, result in run_all(problem_for(6)).items():
            self.assertEqual(result.status, NO_SOLUTION, name)
            self.assertIsNone(result.path, name)

    def test_resource_limit(self):
        problem = problem_for(2)
        result = bfs(problem, problem.start, problem.goal, None, 3)
        self.assertEqual(result.status, LIMIT)
        self.assertEqual(result.expanded, 3)

    def test_results_are_repeatable(self):
        problem = problem_for(5)
        for function in (bfs, ucs, greedy, astar):
            first = function(problem, problem.start, problem.goal)
            second = function(problem, problem.start, problem.goal)
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
