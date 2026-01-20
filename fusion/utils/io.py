import json
import os
import pandas as pd


def load_poles_csv(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    return pd.read_csv(csv_path)


def export_connections_json(connections, df, output_dir):
    """
    Exports connections to JSON.
    `connections` must be a list of dictionaries.
    """

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "connections.json")

    export_data = []

    for conn in connections:
        export_data.append({
            "from_id": conn["from_id"],
            "to_id": conn["to_id"],
            "distance": conn["distance"],
            "from_pole": df[df["Pole_ID"] == conn["from_id"]].iloc[0].to_dict(),
            "to_pole": df[df["Pole_ID"] == conn["to_id"]].iloc[0].to_dict()
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=4, ensure_ascii=False)

    return output_path