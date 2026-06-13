#!/usr/bin/env python3
"""Bar chart: nominal / SSI / GP-MPC on one continuous ZYY trajectory."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from plot_cn_font import apply_cn_to_figure, chinese_fontproperties, setup_chinese_style  # noqa: E402

ALGOS = ["nominal", "ssi", "gpmpc"]
ALGO_CN = {"nominal": "名义 MPC", "ssi": "SSI-MPC", "gpmpc": "GP-MPC"}
COLORS = {"nominal": "#77ac30", "ssi": "#0072bd", "gpmpc": "#a2142f"}
TRAJ = "letter_zyy"


def load_rmse(records: Path, v_max: float) -> dict[str, float]:
    out: dict[str, float] = {}
    with records.open(encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            if row["trajectory"] != TRAJ:
                continue
            if abs(float(row["v_max"]) - v_max) > 1e-6:
                continue
            algo = row["algorithm"]
            rmse = float(row["rmse_m"])
            out[algo] = min(out.get(algo, rmse), rmse)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v-max", type=float, default=10.0)
    parser.add_argument("--records", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    setup_chinese_style()
    fp = chinese_fontproperties()
    root = Path(os.environ.get("PAPER_REPRO_DIR", _SCRIPT_DIR.parent))
    records = args.records or (root / "data" / "results" / "rmse_records.csv")
    out_png = args.output or (root / "data" / "results" / f"zyy_compare_v{args.v_max:.1f}.png")

    data = load_rmse(records, args.v_max)
    vals, labels, colors = [], [], []
    for algo in ALGOS:
        if algo not in data:
            continue
        vals.append(data[algo])
        labels.append(ALGO_CN[algo])
        colors.append(COLORS[algo])

    if not vals:
        print("[warn] no letter_zyy results yet")
        return 0

    fig, ax = plt.subplots(figsize=(6, 4.5))
    x = np.arange(len(vals))
    bars = ax.bar(x, vals, color=colors, edgecolor="k", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontproperties=fp)
    ax.set_ylabel(f"RMSE (m) @ v={args.v_max:.1f} m/s", fontproperties=fp)
    ax.set_title("连续 ZYY 字母轨迹 — 三算法对比", fontproperties=fp)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, val, f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    present = [a for a in ALGOS if a in data]
    best_algo = min(present, key=lambda a: data[a]) if present else None
    if best_algo:
        print(f"[best] {ALGO_CN[best_algo]}: RMSE={data[best_algo]:.5f} m")

    fig.tight_layout()
    apply_cn_to_figure(fig, fp)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    print(f"[info] saved {out_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
