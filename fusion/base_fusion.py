import argparse
import json
from fusion.interface import run_fusion


def load_config(path="config.json"):
    """
    Load configuration from a JSON file.
    """
    with open(path, "r") as f:
        return json.load(f)


def main():
    # Command-line argument parser
    parser = argparse.ArgumentParser(description="Run pole fusion process")
    parser.add_argument(
        "--mode",
        choices=["automatic", "manual"],
        required=True,
        help="Fusion mode: automatic or manual"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file"
    )
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Run fusion using classified poles CSV
    run_fusion(
        mode=args.mode,
        input_csv=f"{config['output_dir']}/poles_MT_info_classified.csv",
        output_dir=config["output_dir"]
    )


# Script entry point
if __name__ == "__main__":
    main()