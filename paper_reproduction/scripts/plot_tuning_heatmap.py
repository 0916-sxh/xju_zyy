#!/usr/bin/env python3
"""Heatmap: tuning candidates RMSE @ one speed (Chinese labels)."""

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

from algorithm_registry import TUNING_CANDIDATES, get_algo  # noqa: E402
from plot_cn_font import apply_cn_to_figure, chinese_fontproperties, setup_chinese_style  # noqa: E402

TRAJ_CN = {
    "circle": "圆形",
    "wrapped_circle": "缠绕圆",
    "lemniscate": "双纽线",
    "wrapped_lemniscate": "缠绕双纽线",
}

PLOT_LABEL_CN = {
    "nominal": "名义 MPC",
    "ssi": "SSI-MPC",
    "gpmpc": "GP-MPC",
    "ssi_n100": "SSI M=100",
    "ssi_n100_lr015": "SSI M=100 η=0.15",
    "ssi_longhorizon": "SSI 长预测域",
    "rdrv": "RDRv-MPC",
}


def load_rmse(records: Path, v_max: float) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    with records.open(encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            if abs(float(row["v_max"]) - v_max) > 1e-6:
                continue
            key = (row["trajectory"], row["algorithm"])
            rmse = float(row["rmse_m"])
            out[key] = min(out.get(key, rmse), rmse)
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
    out_png = args.output or (root / "data" / "results" / f"tuning_heatmap_v{args.v_max:.1f}.png")

    if not records.is_file():
        print(f"[error] {records} not found")
        return 1

    data = load_rmse(records, args.v_max)
    trajs = [t for t in TRAJ_CN if any((t, a) in data for a in TUNING_CANDIDATES)]
    algos = [a for a in TUNING_CANDIDATES if any((t, a) in data for t in trajs)]
    if not trajs or not algos:
        print("[error] no tuning records at requested v_max")
        return 1

    mat = np.full((len(trajs), len(algos)), np.nan)
    for i, traj in enumerate(trajs):
        for j, algo in enumerate(algos):
            mat[i, j] = data.get((traj, algo), np.nan)

    fig, ax = plt.subplots(figsize=(1.2 * len(algos) + 2, 0.9 * len(trajs) + 2))
    im = ax.imshow(mat, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(algos)))
    ax.set_xticklabels([PLOT_LABEL_CN.get(a, get_algo(a).label_cn) for a in algos], rotation=35, ha="right")
    ax.set_yticks(range(len(trajs)))
    ax.set_yticklabels([TRAJ_CN[t] for t in trajs])
    ax.set_title(f"调参对比 RMSE 热力图 @ v={args.v_max:.1f} m/s（越低越好）")
    for i in range(len(trajs)):
        for j in range(len(algos)):
            if not np.isnan(mat[i, j]):
                ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center", fontsize=8)
    cbar = fig.colorbar(im, ax=ax, label="RMSE (m)")
    if fp is not None:
        cbar.ax.set_ylabel("RMSE (m)", fontproperties=fp)
    apply_cn_to_figure(fig, fp)
    fig.tight_layout()
    apply_cn_to_figure(fig, fp)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"[info] saved {out_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
