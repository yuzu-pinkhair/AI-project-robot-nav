"""
Make comparison charts from results.csv (Greedy vs A*).
Run AFTER tree_search_csv.py has created results.csv.
Libraries: csv (read data), matplotlib (plotting).
"""
import csv
import matplotlib
matplotlib.use("Agg")                  # save to files, no window needed
import matplotlib.pyplot as plt

# ---- read the CSV ----
with open("results.csv") as f:
    rows = list(csv.DictReader(f))

# Keep only maps where a path was found (map6 has no path, so it has no cost).
maps = []
for r in rows:
    if r["found"] == "True" and r["map"] not in maps:
        maps.append(r["map"])

def values(algorithm, column):
    """Return the numbers of one column for one algorithm, in map order."""
    return [int(r[column]) for m in maps for r in rows
            if r["map"] == m and r["algorithm"] == algorithm]

def grouped_bar(column, ylabel, title, filename):
    greedy = values("greedy", column)
    astar = values("astar", column)
    x = range(len(maps))
    fig, ax = plt.subplots(figsize=(7, 4))
    bars1 = ax.bar([i - 0.2 for i in x], greedy, 0.4, label="Greedy")
    bars2 = ax.bar([i + 0.2 for i in x], astar, 0.4, label="A*")
    ax.bar_label(bars1, fontsize=8)    # print the number on top of each bar
    ax.bar_label(bars2, fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(maps)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)

grouped_bar("cost", "Total path cost", "Path cost: Greedy vs A*", "chart_cost.png")
grouped_bar("expanded", "Nodes expanded", "Nodes expanded: Greedy vs A*", "chart_expanded.png")
grouped_bar("generated", "Nodes generated", "Nodes generated: Greedy vs A*", "chart_generated.png")
print("Saved chart_cost.png, chart_expanded.png, chart_generated.png")
