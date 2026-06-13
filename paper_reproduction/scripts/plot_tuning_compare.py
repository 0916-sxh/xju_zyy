#!/usr/bin/env python3
"""Bar chart comparing controller variants at one speed (Chinese labels)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from algorithm_registry import ALGO_REGISTRY, BASELINE_COMPARE, TUNING_CANDIDATES, get_algo  # noqa: E402
from plot_cn_font import apply_cn_to_figure, chinese_fontproperties, setup_chinese_style  # noqa: E402

# Short axis labels (avoid multi-line / missing-glyph issues on narrow bars).
PLOT_LABEL_CN = {
    "nominal": "名义 MPC",
    "ssi": "SSI-MPC",
    "gpmpc": "GP-MPC",
    "ssi_n100": "SSI M=100",
    "ssi_n100_lr015": "SSI M=100 η=0.15",
    "ssi_longhorizon": "SSI 长预测域",
    "ssi_heuristic": "SSI 启发式",
    "rdrv": "RDRv-MPC",
}


TRAJ_CN = {
    "circle": "圆形",
    "wrapped_circle": "缠绕圆",
    "lemniscate": "双纽线",
    "wrapped_lemniscate": "缠绕双纽线",
}

COLORS = {
    "nominal": "#77ac30",
    "ssi": "#0072bd",
    "ssi_n100": "#004488",
    "ssi_n100_lr015": "#0055aa",
    "ssi_longhorizon": "#3399ff",
    "ssi_heuristic": "#66bbff",
    "gpmpc": "#a2142f",
    "rdrv": "#ff8800",
}


def plot_label(algo: str) -> str:
    return PLOT_LABEL_CN.get(algo, get_algo(algo).label_cn)


def apply_cn_font(text_obj, fp) -> None:
    if fp is not None:
        text_obj.set_fontproperties(fp)


def load_rmse(records_csv: Path, v_max: float) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    with records_csv.open(encoding="utf-8") as fp:
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
    parser.add_argument(
        "--algorithms",
        nargs="*",
        default=None,
        help="subset to plot (default: tuning candidates + baselines present in data)",
    )
    args = parser.parse_args()

    setup_chinese_style()
    fp = chinese_fontproperties()
    root = Path(os.environ.get("PAPER_REPRO_DIR", _SCRIPT_DIR.parent))
    records = args.records or (root / "data" / "results" / "rmse_records.csv")
    out_png = args.output or (root / "data" / "results" / f"tuning_compare_v{args.v_max:.1f}.png")

    if not records.is_file():
        print(f"[error] {records} not found")
        return 1

    data = load_rmse(records, args.v_max)
    trajs = [t for t in TRAJ_CN if any((t, a) in data for a in ALGO_REGISTRY)]
    if not trajs:
        print("[error] no records for requested v_max")
        return 1

    if args.algorithms:
        algos = args.algorithms
    else:
        present = {a for _, a in data}
        algos = [a for a in BASELINE_COMPARE + TUNING_CANDIDATES if a in present]
        algos = list(dict.fromkeys(algos))

    fig, axes = plt.subplots(1, len(trajs), figsize=(3.6 * len(trajs), 5.8), sharey=True)
    if len(trajs) == 1:
        axes = [axes]

    tick_fp = fp.copy() if fp is not None else None
    if tick_fp is not None:
        tick_fp.set_size(7)

    for ax, traj in zip(axes, trajs):
        vals = []
        labels = []
        colors = []
        for algo in algos:
            rmse = data.get((traj, algo))
            if rmse is None:
                continue
            vals.append(rmse)
            labels.append(plot_label(algo))
            colors.append(COLORS.get(algo, "#888888"))
        x = np.arange(len(vals))
        bars = ax.bar(x, vals, color=colors, edgecolor="k", linewidth=0.4)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=40, ha="right")
        if tick_fp is not None:
            for lbl in ax.get_xticklabels():
                lbl.set_fontproperties(tick_fp)
        apply_cn_font(ax.set_title(TRAJ_CN[traj]), fp)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, val, f"{val:.3f}", ha="center", va="bottom", fontsize=7)

    ylabel = axes[0].set_ylabel(f"RMSE (m) @ v={args.v_max:.1f} m/s")
    apply_cn_font(ylabel, fp)
    st = fig.suptitle("控制器调参对比（越低越好）", fontsize=12)
    apply_cn_font(st, fp)
    fig.subplots_adjust(bottom=0.28)
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    apply_cn_to_figure(fig, fp)
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    print(f"[info] saved {out_png}")

    best_json = root / "data" / "results" / "best_algorithm.json"
    if best_json.is_file():
        rec = json.loads(best_json.read_text(encoding="utf-8")).get("overall_recommendation")
        if rec:
            print(f"[recommend] {rec['algorithm']}: {rec['label_cn']} (mean RMSE {rec['mean_rmse_m']:.5f} m)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
