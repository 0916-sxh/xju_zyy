#!/usr/bin/env python3
"""Plot reference vs actual for letter_zyy trial (.mat)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.io import loadmat

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from letter_trajectories import generate_letter_trajectory, letter_label_positions
from plot_cn_font import chinese_fontproperties, setup_chinese_style

ALGO_CN = {
    "nominal": "名义 MPC",
    "ssi": "SSI-MPC",
    "gpmpc": "GP-MPC",
    "ssi_n100": "SSI-MPC M=100",
    "rdrv": "RDRv-MPC",
}


def pos_rmse(ref_x: np.ndarray, x: np.ndarray) -> float:
    n = min(len(ref_x), len(x))
    return float(np.sqrt(np.mean(np.sum((x[:n, :3] - ref_x[:n, :3]) ** 2, axis=1))))


def _annotate_letters(ax, fp) -> None:
    for text, lx, ly in letter_label_positions():
        ax.annotate(text, (lx, ly), fontsize=16, fontweight="bold", ha="center", fontproperties=fp, color="#555555")


def _legend_outside_right(ax, fp, fontsize: int = 8) -> None:
    ax.legend(
        prop=fp,
        fontsize=fontsize,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0,
    )


def _legend_above(ax, fp, fontsize: int = 7, ncol: int = 3) -> None:
    ax.legend(
        prop=fp,
        fontsize=fontsize,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=ncol,
        borderaxespad=0,
    )


def plot_mat(mat_path: Path, algo: str, out_dir: Path, v_max: float) -> None:
    fp = chinese_fontproperties()
    raw = loadmat(mat_path, squeeze_me=True)
    ref_x = np.atleast_2d(raw["ref_x"])
    x = np.atleast_2d(raw["x"])
    t = np.atleast_1d(raw["ref_time"])
    n = min(len(t), ref_x.shape[0], x.shape[0])
    t, ref_x, x = t[:n], ref_x[:n], x[:n]
    err = np.linalg.norm(x[:, :3] - ref_x[:, :3], axis=1)
    rmse = pos_rmse(ref_x, x)
    label = ALGO_CN.get(algo, algo)

    # Latest planned path (may differ if trajectory was updated after this trial)
    new_ref, _, _, _ = generate_letter_trajectory("zyy", v_max=v_max, plot=False)

    fig = plt.figure(figsize=(12, 5))

    ax_xy = fig.add_subplot(131)
    ax_xy.plot(ref_x[:, 0], ref_x[:, 1], "k-", linewidth=2, label="参考（本次飞行）")
    ax_xy.plot(
        new_ref[:, 0],
        new_ref[:, 1],
        "g--",
        linewidth=1.2,
        alpha=0.7,
        label="新规划 ZYY",
    )
    ax_xy.plot(x[:, 0], x[:, 1], color="#0072bd", linewidth=1.2, alpha=0.85, label=f"实际 ({label})")
    _annotate_letters(ax_xy, fp)
    ax_xy.set_aspect("equal")
    ax_xy.grid(True, alpha=0.3)
    ax_xy.set_xlabel("x (m)")
    ax_xy.set_ylabel("y (m)")
    ax_xy.set_title(
        f"XY 俯视图  RMSE={rmse:.3f} m",
        fontproperties=fp,
        y=1.38,
        transform=ax_xy.transAxes,
    )
    _legend_above(ax_xy, fp, fontsize=7)

    ax3 = fig.add_subplot(132, projection="3d")
    ax3.plot(ref_x[:, 0], ref_x[:, 1], ref_x[:, 2], "k-", linewidth=1.5, label="参考")
    ax3.plot(x[:, 0], x[:, 1], x[:, 2], color="#0072bd", linewidth=1.0, alpha=0.85, label="实际")
    ax3.set_xlabel("x (m)")
    ax3.set_ylabel("y (m)")
    ax3.set_zlabel("z (m)")
    ax3.set_title("三维轨迹", fontproperties=fp)
    _legend_outside_right(ax3, fp, fontsize=8)

    ax_t = fig.add_subplot(133)
    ax_t.plot(t, err, color="#a2142f", linewidth=1.0)
    ax_t.set_xlabel("时间 (s)", fontproperties=fp)
    ax_t.set_ylabel("位置误差 (m)", fontproperties=fp)
    ax_t.set_title("瞬时跟踪误差", fontproperties=fp)
    ax_t.grid(True, alpha=0.3)

    fig.suptitle(f"连续 ZYY 字母轨迹 — {label}  @ v={v_max:.1f} m/s", fontproperties=fp, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.subplots_adjust(wspace=0.42, top=0.74)

    out_png = out_dir / f"letter_zyy_track_{algo}_v{v_max:.1f}.png"
    fig.savefig(out_png, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"[info] saved {out_png}  RMSE={rmse:.4f} m  duration={t[-1]:.1f}s")


def save_ref_preview(out_dir: Path, v_max: float) -> None:
    fp = chinese_fontproperties()
    x_ref, _, _, _ = generate_letter_trajectory("zyy", v_max=v_max, plot=False)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(x_ref[:, 0], x_ref[:, 1], "k-", linewidth=2.2)
    _annotate_letters(ax, fp)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("参考轨迹 ZYY（规划路径）", fontproperties=fp, fontsize=13)
    out_png = out_dir / f"letter_zyy_ref_only_v{v_max:.1f}.png"
    fig.savefig(out_png, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"[info] saved {out_png}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algorithm", default="nominal")
    parser.add_argument("--mat", type=Path, default=None)
    parser.add_argument("--v-max", type=float, default=10.0)
    parser.add_argument("--trial", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--ref-only", action="store_true", help="only regenerate reference preview")
    args = parser.parse_args()

    setup_chinese_style()
    root = Path(os.environ.get("PAPER_REPRO_DIR", _SCRIPT_DIR.parent))
    out_dir = args.output_dir or (root / "data" / "results")
    out_dir.mkdir(parents=True, exist_ok=True)

    save_ref_preview(out_dir, args.v_max)
    if args.ref_only:
        return 0

    mat_path = args.mat or (
        root / "data" / "mat" / args.algorithm / "letter_zyy" / f"trial{args.trial:02d}_v{args.v_max:.1f}.mat"
    )
    if not mat_path.is_file():
        print(f"[error] mat not found: {mat_path}")
        return 1

    plot_mat(mat_path, args.algorithm, out_dir, args.v_max)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
