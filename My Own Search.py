import csv
import heapq
import os

#Load the maps
def load_map(path):
    with open(path) as f:
        return [line.split() for line in f if line.strip()]

#test the map
grid = load_map('map1.txt')
print(grid[0])
print(grid[1][1]) # Print the element at row 1, column 1

#Set the start(S) and goal(G) positions
def find(grid, symbol):
    for r, row in enumerate(grid):
         for c, cell in enumerate(row):
             if cell == symbol:
                 return (r, c)
    return None

#Cost and Heuristics(change based on problem cost)
def cost(grid,cell):
    value = grid[cell[0]][cell[1]]
    return 1 if value in ("S","G") else int(value)

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1]- b[1])

