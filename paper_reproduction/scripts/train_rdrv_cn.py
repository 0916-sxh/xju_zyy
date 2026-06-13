#!/usr/bin/env python3
"""Train RDRv drag model (wrapper: plot=False to avoid SSI-MPC viz bug)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROS_MPC = Path(os.environ.get("ROS_MPC_DIR", Path(__file__).resolve().parents[2] / "SSI-MPC" / "ros_mpc"))
if str(ROS_MPC) not in sys.path:
    sys.path.insert(0, str(ROS_MPC))

from config.configuration_parameters import ModelFitConfig as Conf  # noqa: E402
from src.model_fitting.rdrv_fitting import main as train_rdrv  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default="gazebo_sim_rdrv")
    parser.add_argument("--dataset", default=None)
    args = parser.parse_args()

    ds_name = args.dataset or Conf.ds_name
    data_csv = ROS_MPC / "data" / ds_name / "train" / "dataset_001.csv"
    if not data_csv.is_file():
        print(f"[error] dataset missing: {data_csv}")
        return 1

    print(f"[info] training RDRv from {data_csv}")
    coeffs = train_rdrv(
        model_name=args.model_name,
        features=[7, 8, 9],
        quad_sim_options=Conf.ds_metadata,
        dataset_name=ds_name,
        x_cap=Conf.velocity_cap,
        hist_bins=Conf.histogram_bins,
        hist_thresh=Conf.histogram_threshold,
        plot=False,
    )
    print(f"[info] drag coefficient matrix:\n{coeffs}")

    try:
        git_hash = subprocess.check_output(
            ["git", "-C", str(ROS_MPC), "describe", "--always"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        git_hash = sorted((ROS_MPC / "results" / "model_fitting").iterdir())[-1].name

    out_dir = ROS_MPC / "results" / "model_fitting" / git_hash / args.model_name
    print(f"[done] model saved under {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
