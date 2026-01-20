import matplotlib.pyplot as plt


def plot_connections(df, connections, title):
    """
    Draw poles and connections in a single color with distance labels.
    `connections` must be a list of dictionaries.
    """

    fig, ax = plt.subplots(figsize=(10, 8))

    # --- Plot poles ---
    ax.scatter(
        df["Center_X"],
        df["Center_Y"],
        s=150,
        edgecolors="black",
        zorder=2
    )

    for _, row in df.iterrows():
        ax.text(
            row["Center_X"],
            row["Center_Y"],
            str(int(row["Pole_ID"])),
            fontsize=9,
            ha="center",
            va="center",
            weight="bold"
        )

    # --- Plot connections (SINGLE COLOR + DISTANCES) ---
    for conn in connections:
        x1, y1 = conn["from_xy"]
        x2, y2 = conn["to_xy"]
        dist = conn["distance"]

        ax.plot(
            [x1, x2],
            [y1, y2],
            color="skyblue", 
            linewidth=2.8,
            zorder=1
        )

        ax.text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            f"{dist:.1f} m",
            fontsize=8,
            ha="center",
            va="bottom",
            alpha=0.7
        )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Center_X")
    ax.set_ylabel("Center_Y")
    ax.axis("equal")
    ax.grid(True, linestyle="--", alpha=0.3)

    return fig


def save_figure(fig, output_dir):
    path = f"{output_dir}/connections.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path