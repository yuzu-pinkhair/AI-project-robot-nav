"""
This section only for plot creation based on the result produced
"""


def plot_route(grid, path, title, filename=None, show=False):
    """Draw the map and the route. Save to 'filename' and/or open a window.

    grid : the map (list of rows of symbols)
    path : list of (row, column) cells from S to G, or None when there is no route
    """
    try:
        import matplotlib
        if not show:
            matplotlib.use("Agg")           # draw to a file, no window needed
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        from matplotlib.patches import Patch
    except ImportError as error:
        raise RuntimeError("matplotlib is not installed. Install it with: "
                           "python -m pip install -r requirements.txt") from error

    rows, cols = len(grid), len(grid[0])

    # Colour code for each cell: 0 normal, 1 crowded, 2 difficult, 3 obstacle.
    code = {"X": 3, "3": 1, "5": 2}
    image = [[code.get(cell, 0) for cell in row] for row in grid]
    colours = ["#ffffff", "#fde0b0", "#f4a259", "#333333"]

    fig, ax = plt.subplots(figsize=(max(4.5, cols * 0.6 + 1), max(3.5, rows * 0.6 + 1.5)))
    ax.imshow(image, cmap=ListedColormap(colours), vmin=0, vmax=3)

    # Grid lines
    ax.set_xticks([x - 0.5 for x in range(cols + 1)], minor=True)
    ax.set_yticks([y - 0.5 for y in range(rows + 1)], minor=True)
    ax.grid(which="minor", color="#999999", linewidth=0.6)
    ax.tick_params(which="both", length=0, labelbottom=False, labelleft=False)

    # Cell labels: the cost of entering each cell, S and G highlighted.
    for r in range(rows):
        for c in range(cols):
            symbol = grid[r][c]
            if symbol == "S":
                ax.text(c, r, "S", ha="center", va="center", fontsize=11, fontweight="bold",
                        color="white", zorder=5, bbox=dict(boxstyle="round", facecolor="#2ca02c", edgecolor="none"))
            elif symbol == "G":
                ax.text(c, r, "G", ha="center", va="center", fontsize=11, fontweight="bold",
                        color="white", zorder=5, bbox=dict(boxstyle="round", facecolor="#d62728", edgecolor="none"))
            elif symbol != "X":
                ax.text(c, r, symbol, ha="center", va="center", fontsize=8, color="#555555", zorder=2)

    # The route
    if path:
        ax.plot([c for _r, c in path], [r for r, _c in path],
                color="#1f77b4", linewidth=2.5, marker="o", markersize=4, zorder=3)

    ax.set_title(title, fontsize=10)
    legend = [Patch(facecolor=colours[0], edgecolor="#999999", label="normal (1)"),
              Patch(facecolor=colours[1], edgecolor="#999999", label="crowded (3)"),
              Patch(facecolor=colours[2], edgecolor="#999999", label="difficult (5)"),
              Patch(facecolor=colours[3], edgecolor="#999999", label="obstacle")]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=4, fontsize=7, frameon=False)
    fig.tight_layout()

    if filename:
        fig.savefig(filename, dpi=150)
    if show:
        plt.show()
    plt.close(fig)
