import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from fusion.utils.io import export_connections_json


def run_interactive_tool(df, output_dir):
    coords = df[["Center_X", "Center_Y"]].values
    connections = []
    selected = []
    finalized = False
    exported = False

    fig, ax = plt.subplots(figsize=(10, 8))
    plt.subplots_adjust(bottom=0.25)

    # --- Plot poles ---
    ax.scatter(coords[:, 0], coords[:, 1], s=150, edgecolors="black", zorder=2)
    for _, row in df.iterrows():
        ax.text(
            row["Center_X"], row["Center_Y"],
            str(int(row["Pole_ID"])),
            fontsize=9, ha="center", va="center", weight="bold"
        )

    ax.set_title("Manual Fusion Tool", fontsize=14, fontweight="bold")
    ax.axis("equal")
    ax.grid(True, linestyle="--", alpha=0.3)

    # =====================
    # CLICK HANDLER
    # =====================
    def onclick(event):
        nonlocal finalized
        if finalized or event.inaxes != ax:
            return

        idx = np.argmin(np.linalg.norm(coords - [event.xdata, event.ydata], axis=1))
        selected.append(idx)

        if len(selected) == 2:
            i, j = selected
            dist = float(np.linalg.norm(coords[i] - coords[j]))

            connections.append({
                "from_id": int(df.iloc[i]["Pole_ID"]),
                "to_id": int(df.iloc[j]["Pole_ID"]),
                "from_xy": tuple(coords[i]),
                "to_xy": tuple(coords[j]),
                "distance": dist
            })

            ax.plot(
                [coords[i][0], coords[j][0]],
                [coords[i][1], coords[j][1]],
                color="skyblue",
                linewidth=2.8,
                zorder=1
            )

            ax.text(
                (coords[i][0] + coords[j][0]) / 2,
                (coords[i][1] + coords[j][1]) / 2,
                f"{dist:.1f} m",
                fontsize=8,
                ha="center",
                va="bottom"
            )

            fig.canvas.draw()
            selected.clear()

    # =====================
    # BUTTON ACTIONS
    # =====================
    def finalize(event):
        nonlocal finalized
        finalized = True
        ax.set_title("Finalized – No more connections", color="green", fontweight="bold")
        fig.canvas.draw()

    def clear(event):
        nonlocal connections, finalized
        connections.clear()
        finalized = False

        ax.cla()
        ax.scatter(coords[:, 0], coords[:, 1], s=150, edgecolors="black", zorder=2)
        for _, row in df.iterrows():
            ax.text(row["Center_X"], row["Center_Y"],
                    str(int(row["Pole_ID"])),
                    fontsize=9, ha="center", va="center", weight="bold")

        ax.set_title("Manual Fusion Tool")
        ax.axis("equal")
        ax.grid(True, linestyle="--", alpha=0.3)
        fig.canvas.draw()

    def export(event):
        nonlocal exported
        os.makedirs(output_dir, exist_ok=True)

        json_path = export_connections_json(connections, df, output_dir)
        img_path = f"{output_dir}/connections.png"
        fig.savefig(img_path, dpi=300)
        exported = True

        print("✅ Fusion finished")
        print(f"📄 JSON: {json_path}")
        print(f"🖼️ Image: {img_path}")

    # =====================
    # BUTTONS (KEEP REFERENCES!)
    # =====================
    ax_final = plt.axes([0.10, 0.05, 0.22, 0.08])
    ax_clear = plt.axes([0.39, 0.05, 0.22, 0.08])
    ax_export = plt.axes([0.68, 0.05, 0.25, 0.08])

    btn_finalize = Button(ax_final, "Finalize")
    btn_clear = Button(ax_clear, "Clear")
    btn_export = Button(ax_export, "Export")

    btn_finalize.on_clicked(finalize)
    btn_clear.on_clicked(clear)
    btn_export.on_clicked(export)

    fig.canvas.mpl_connect("button_press_event", onclick)
    plt.show()