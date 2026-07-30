"""Command-line entry point for the Northstar Commerce analytics pipeline."""
from __future__ import annotations

import argparse
from pathlib import Path

from northstar_analytics.config import load_config
from northstar_analytics.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Northstar Commerce EDA pipeline.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("eda_config.json"),
        help="Path to the JSON pipeline configuration.",
    )
    parser.add_argument("--skip-plots", action="store_true", help="Run analytics and exports without rendering PNG files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    run_pipeline(config, skip_plots=args.skip_plots)


if __name__ == "__main__":
    main()
