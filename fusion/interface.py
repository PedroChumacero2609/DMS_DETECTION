from fusion.utils.io import load_poles_csv, export_connections_json
from fusion.utils.visualization import save_figure
from fusion.automatic.mst_method import run_mst_method
from fusion.manual.interactive_tool import run_interactive_tool


def run_fusion(mode, input_csv, output_dir):
    df = load_poles_csv(input_csv)

    if mode == "automatic":
        connections, fig = run_mst_method(df)

        json_path = export_connections_json(connections, df, output_dir)
        img_path = save_figure(fig, output_dir)

        print("✅ Fusion finished")
        print(f"📄 JSON: {json_path}")
        print(f"🖼️ Image: {img_path}")

    elif mode == "manual":
        # 🔒 Manual controla TODO (export + prints)
        run_interactive_tool(df, output_dir)

    else:
        raise ValueError("Invalid fusion mode")