#!/usr/bin/env python3
"""Pick lowest-RMSE algorithm per trajectory from rmse_records.csv."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from algorithm_registry import ALGO_REGISTRY, get_algo  # noqa: E402


def load_records(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise SystemExit(f"records not found: {path}")
    return list(csv.DictReader(path.open(encoding="utf-8")))


def pick_best(
    records: list[dict[str, str]],
    v_max: float,
    trajectories: list[str] | None = None,
) -> dict:
    grouped: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    for row in records:
        if abs(float(row["v_max"]) - v_max) > 1e-6:
            continue
        traj = row["trajectory"]
        if trajectories and traj not in trajectories:
            continue
        grouped[(traj, row["algorithm"])].append((row["trial"], float(row["rmse_m"])))

    per_traj: dict[str, dict] = {}
    for traj in trajectories or sorted({k[0] for k in grouped}):
        best_algo = None
        best_rmse = float("inf")
        candidates: dict[str, float] = {}
        for algo in ALGO_REGISTRY:
            key = (traj, algo)
            if key not in grouped:
                continue
            rmse = min(v for _, v in grouped[key])
            candidates[algo] = rmse
            if rmse < best_rmse:
                best_rmse = rmse
                best_algo = algo
        if best_algo is not None:
            spec = get_algo(best_algo)
            per_traj[traj] = {
                "algorithm": best_algo,
                "label_cn": spec.label_cn,
                "rmse_m": best_rmse,
                "candidates": candidates,
            }

    # Overall winner: average RMSE across trajectories where each algo has data
    algo_scores: dict[str, list[float]] = defaultdict(list)
    for info in per_traj.values():
        for algo, rmse in info["candidates"].items():
            algo_scores[algo].append(rmse)
    overall = None
    if algo_scores:
        overall_algo = min(algo_scores, key=lambda a: sum(algo_scores[a]) / len(algo_scores[a]))
        overall = {
            "algorithm": overall_algo,
            "label_cn": get_algo(overall_algo).label_cn,
            "mean_rmse_m": sum(algo_scores[overall_algo]) / len(algo_scores[overall_algo]),
        }

    return {
        "v_max": v_max,
        "per_trajectory": per_traj,
        "overall_recommendation": overall,
        "note": "Based on archived rmse_records.csv; re-run 09_run_tuning_benchmark.sh to refresh.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Select best algorithm per trajectory.")
    parser.add_argument("--records", type=Path, default=None)
    parser.add_argument("--v-max", type=float, default=10.0)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    root = Path(__import__("os").environ.get("PAPER_REPRO_DIR", _SCRIPT_DIR.parent))
    records_path = args.records or (root / "data" / "results" / "rmse_records.csv")
    out_path = args.output or (root / "data" / "results" / "best_algorithm.json")

    result = pick_best(load_records(records_path), v_max=args.v_max)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[info] wrote {out_path}")
    if result["overall_recommendation"]:
        rec = result["overall_recommendation"]
        print(f"[best] overall @ v={args.v_max}: {rec['algorithm']} ({rec['label_cn']}) "
              f"mean RMSE={rec['mean_rmse_m']:.5f} m")
    for traj, info in sorted(result["per_trajectory"].items()):
        print(f"  {traj}: {info['algorithm']} RMSE={info['rmse_m']:.5f} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
