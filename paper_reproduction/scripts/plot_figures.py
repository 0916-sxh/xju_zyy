#!/usr/bin/env python3
"""Generate all reproducible paper figures (Chinese labels) from archived data."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import loadmat

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from plot_cn_font import apply_cn_to_figure, chinese_fontproperties, setup_chinese_style  # noqa: E402

FP = None  # set in main()

TRAJS = ["circle", "wrapped_circle", "lemniscate", "wrapped_lemniscate"]
ALGOS = ["nominal", "ssi", "gpmpc"]
ALGO_PLOT_ORDER = ["nominal", "gpmpc", "ssi"]

TRAJ_CN = {
    "circle": "圆形轨迹",
    "wrapped_circle": "缠绕圆形轨迹",
    "lemniscate": "双纽线轨迹",
    "wrapped_lemniscate": "缠绕双纽线轨迹",
}

ALGO_CN = {
    "nominal": "名义 MPC",
    "ssi": "本文方法 (SSI-MPC)",
    "gpmpc": "GP-MPC",
}

ALGO_COLORS = {
    "nominal": "#77ac30",
    "gpmpc": "#a2142f",
    "ssi": "#0072bd",
}


def _save(fig, path: Path, tag: str = "saved") -> None:
    apply_cn_to_figure(fig, FP)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"[{tag}] {path}")


def repro_paths() -> dict[str, Path]:
    root = Path(os.environ.get("PAPER_REPRO_DIR", Path(__file__).resolve().parent.parent))
    return {
        "root": root,
        "mat": root / "data" / "mat",
        "results": root / "data" / "results",
        "scripts": root / "scripts",
    }


def mat_file(mat_root: Path, algo: str, traj: str, v_max: float) -> Path:
    return mat_root / algo / traj / f"trial01_v{v_max:.1f}.mat"


def load_trial(mat_root: Path, algo: str, traj: str, v_max: float) -> Optional[dict]:
    path = mat_file(mat_root, algo, traj, v_max)
    if not path.is_file():
        print(f"[warn] missing {path}")
        return None
    raw = loadmat(path, squeeze_me=True)
    return {
        "ref_time": np.atleast_1d(raw["ref_time"]),
        "ref_x": np.atleast_2d(raw["ref_x"]),
        "ref_u": np.atleast_2d(raw["ref_u"]),
        "x": np.atleast_2d(raw["x"]),
        "u": np.atleast_2d(raw["u"]),
    }


def align_length(ref_x: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = min(ref_x.shape[0], x.shape[0])
    return ref_x[:n], x[:n]


def pos_error(ref_x: np.ndarray, x: np.ndarray) -> np.ndarray:
    ref_x, x = align_length(ref_x, x)
    return np.linalg.norm(x[:, :3] - ref_x[:, :3], axis=1)


def segment_slice(n: int, frac_start: float = 0.4, frac_end: float = 0.5) -> slice:
    t0 = max(0, int(frac_start * n))
    t1 = max(t0 + 1, int(frac_end * n))
    return slice(t0, t1)


# ---------- Fig.5 ----------
def plot_fig5(mat_root: Path, out_dir: Path, v_max: float = 10.0) -> None:
    for traj in TRAJS:
        data = load_trial(mat_root, "ssi", traj, v_max)
        if data is None:
            continue
        ref_x = data["ref_x"]
        fig = plt.figure(figsize=(7, 5))
        ax = fig.add_subplot(111, projection="3d")
        ax.plot(ref_x[:, 0], ref_x[:, 1], ref_x[:, 2], "b-", linewidth=1.8, label="参考轨迹")
        ax.plot(ref_x[:, 0], ref_x[:, 1], np.zeros(ref_x.shape[0]), color="0.75", linewidth=1.0, label="地面投影")
        ax.set_xlabel("x 位置 (m)")
        ax.set_ylabel("y 位置 (m)")
        ax.set_zlabel("z 高度 (m)")
        ax.set_title(f"图5  参考轨迹 — {TRAJ_CN[traj]}（$v_{{max}}$={v_max:.1f} m/s）")
        ax.legend(loc="upper right", fontsize=9)
        out_png = out_dir / f"fig5_{traj}.png"
        _save(fig, out_png, "fig5")


# ---------- Fig.6 ----------
def plot_fig6(summary_csv: Path, out_png: Path) -> None:
    df = pd.read_csv(summary_csv)
    trajs = [t for t in TRAJS if t in set(df["trajectory"])]
    markers = {"nominal": "s", "ssi": "^", "gpmpc": "o"}

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for ax, traj in zip(axes.ravel(), trajs):
        for algo in ALGOS:
            sub = df[(df["trajectory"] == traj) & (df["algorithm"] == algo)].sort_values("v_max")
            if sub.empty:
                continue
            yerr = sub["rmse_std"].to_numpy()
            yerr = None if np.all(yerr == 0) else yerr
            ax.errorbar(
                sub["v_max"],
                sub["rmse_mean"],
                yerr=yerr,
                marker=markers[algo],
                color=ALGO_COLORS[algo],
                linewidth=1.8,
                capsize=3,
                label=ALGO_CN[algo],
            )
        ax.set_xlabel("设定最大速度 $v_{max}$ (m/s)")
        ax.set_ylabel("均方根误差 RMSE (m)")
        ax.set_title(TRAJ_CN[traj])
        ax.legend(loc="upper left", fontsize=8)

    fig.suptitle("图6  不同算法跟踪 RMSE 随速度变化", fontsize=13)
    _save(fig, out_png, "fig6")


def plot_fig6_bar(summary_csv: Path, out_png: Path) -> None:
    df = pd.read_csv(summary_csv)
    means = []
    for algo in ALGOS:
        sub = df[df["algorithm"] == algo]
        means.append(sub["rmse_mean"].mean() if not sub.empty else np.nan)

    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(ALGOS))
    bars = ax.bar(x, means, color=[ALGO_COLORS[a] for a in ALGOS], edgecolor="k", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([ALGO_CN[a] for a in ALGOS])
    ax.set_ylabel("平均 RMSE (m)")
    ax.set_title("图6 补充  各算法平均跟踪误差（全部轨迹与速度）")
    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val:.3f}", ha="center", va="bottom", fontsize=9)
    _save(fig, out_png, "fig6")


def plot_fig6_heatmap(summary_csv: Path, out_png: Path, v_max: float = 10.0) -> None:
    df = pd.read_csv(summary_csv)
    sub = df[np.isclose(df["v_max"], v_max)]
    mat = np.full((len(TRAJS), len(ALGOS)), np.nan)
    for i, traj in enumerate(TRAJS):
        for j, algo in enumerate(ALGOS):
            row = sub[(sub["trajectory"] == traj) & (sub["algorithm"] == algo)]
            if not row.empty:
                mat[i, j] = row.iloc[0]["rmse_mean"]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    im = ax.imshow(mat, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(ALGOS)))
    ax.set_xticklabels([ALGO_CN[a] for a in ALGOS], rotation=15, ha="right")
    ax.set_yticks(range(len(TRAJS)))
    ax.set_yticklabels([TRAJ_CN[t] for t in TRAJS])
    ax.set_title(f"图6 补充  RMSE 热力图（$v_{{max}}$={v_max:.1f} m/s）")
    for i in range(len(TRAJS)):
        for j in range(len(ALGOS)):
            if not np.isnan(mat[i, j]):
                ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center", color="black", fontsize=9)
    fig.colorbar(im, ax=ax, label="RMSE (m)")
    _save(fig, out_png, "fig6")


# ---------- Fig.7 & extras ----------
def plot_fig7_xy(mat_root: Path, traj: str, v_max: float, out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 6))
    ref_x = None
    for algo in ALGO_PLOT_ORDER:
        data = load_trial(mat_root, algo, traj, v_max)
        if data is None:
            continue
        if ref_x is None:
            ref_x = data["ref_x"]
            seg = segment_slice(ref_x.shape[0])
            ax.plot(ref_x[seg, 0], ref_x[seg, 1], "k-", linewidth=2, label="参考轨迹")
        x = data["x"]
        seg = segment_slice(min(ref_x.shape[0], x.shape[0]))
        ax.plot(x[seg, 0], x[seg, 1], "-", color=ALGO_COLORS[algo], linewidth=1.8, label=ALGO_CN[algo])

    ax.set_xlabel("x 位置 (m)")
    ax.set_ylabel("y 位置 (m)")
    ax.set_title(f"图7a  平面轨迹片段 — {TRAJ_CN[traj]}，$v_{{max}}$={v_max:.1f} m/s")
    ax.legend(loc="best", fontsize=9)
    ax.set_aspect("equal", adjustable="box")
    _save(fig, out_png, "fig7")


def plot_fig7_cumerr(mat_root: Path, traj: str, v_max: float, out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ref_time = None
    for algo in ALGO_PLOT_ORDER:
        data = load_trial(mat_root, algo, traj, v_max)
        if data is None:
            continue
        if ref_time is None:
            ref_time = data["ref_time"]
        err = pos_error(data["ref_x"], data["x"])
        n = min(len(ref_time), len(err))
        ax.plot(ref_time[:n], np.cumsum(err[:n]), color=ALGO_COLORS[algo], linewidth=1.8, label=ALGO_CN[algo])

    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("累积位置误差 (m)")
    ax.set_title(f"图7b  累积跟踪误差 — {TRAJ_CN[traj]}，$v_{{max}}$={v_max:.1f} m/s")
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, out_png, "fig7")


def plot_fig7_inst_err(mat_root: Path, traj: str, v_max: float, out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ref_time = None
    for algo in ALGO_PLOT_ORDER:
        data = load_trial(mat_root, algo, traj, v_max)
        if data is None:
            continue
        if ref_time is None:
            ref_time = data["ref_time"]
        err = pos_error(data["ref_x"], data["x"])
        n = min(len(ref_time), len(err))
        ax.plot(ref_time[:n], err[:n], color=ALGO_COLORS[algo], linewidth=1.2, alpha=0.85, label=ALGO_CN[algo])

    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("瞬时位置误差 (m)")
    ax.set_title(f"图7c  瞬时跟踪误差 — {TRAJ_CN[traj]}，$v_{{max}}$={v_max:.1f} m/s")
    ax.legend(loc="upper right", fontsize=9)
    _save(fig, out_png, "fig7")


def plot_ref_timeseries(mat_root: Path, traj: str, v_max: float, out_png: Path) -> None:
    data = load_trial(mat_root, "ssi", traj, v_max)
    if data is None:
        return
    t = data["ref_time"]
    ref = data["ref_x"]
    ref_u = data["ref_u"]

    fig, axes = plt.subplots(5, 1, figsize=(9, 10), sharex=True, constrained_layout=True)
    axes[0].plot(t, ref[:, 0], label="$x$")
    axes[0].plot(t, ref[:, 1], label="$y$")
    axes[0].plot(t, ref[:, 2], label="$z$")
    axes[0].set_ylabel("位置 (m)")
    axes[0].legend(loc="upper right", ncol=3, fontsize=8)
    axes[0].set_title(f"参考轨迹状态时序 — {TRAJ_CN[traj]}，$v_{{max}}$={v_max:.1f} m/s")

    axes[1].plot(t, ref[:, 3:7])
    axes[1].set_ylabel("四元数")
    axes[1].legend(["$q_w$", "$q_x$", "$q_y$", "$q_z$"], loc="upper right", ncol=4, fontsize=8)

    axes[2].plot(t, ref[:, 7:10])
    axes[2].set_ylabel("速度 (m/s)")
    axes[2].legend(["$v_x$", "$v_y$", "$v_z$"], loc="upper right", ncol=3, fontsize=8)

    axes[3].plot(t, ref[:, 10:13])
    axes[3].set_ylabel("角速度 (rad/s)")
    axes[3].legend(["$\\omega_x$", "$\\omega_y$", "$\\omega_z$"], loc="upper right", ncol=3, fontsize=8)

    axes[4].plot(t, ref_u)
    axes[4].set_ylabel("归一化控制量")
    axes[4].set_xlabel("时间 (s)")
    axes[4].legend(["$u_1$", "$u_2$", "$u_3$", "$u_4$"], loc="upper right", ncol=4, fontsize=8)

    _save(fig, out_png, "extra")


def plot_track3d(mat_root: Path, traj: str, v_max: float, out_png: Path) -> None:
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ref_x = None
    for algo in ALGO_PLOT_ORDER:
        data = load_trial(mat_root, algo, traj, v_max)
        if data is None:
            continue
        if ref_x is None:
            ref_x = data["ref_x"]
            ax.plot(ref_x[:, 0], ref_x[:, 1], ref_x[:, 2], "k-", linewidth=2, label="参考轨迹")
        x = data["x"]
        ref_x_a, x_a = align_length(ref_x, x)
        ax.plot(x_a[:, 0], x_a[:, 1], x_a[:, 2], color=ALGO_COLORS[algo], linewidth=1.2, alpha=0.85, label=ALGO_CN[algo])

    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.set_title(f"补充图  三维实际轨迹对比 — {TRAJ_CN[traj]}，$v_{{max}}$={v_max:.1f} m/s")
    ax.legend(loc="upper left", fontsize=8)
    _save(fig, out_png, "extra")


def plot_gp_training(script_dir: Path, results_dir: Path, gp_version: str = "e0d4afb") -> None:
    gp_script = script_dir / "plot_gp_training_cn.py"
    if not gp_script.is_file():
        return
    out_dir = results_dir / "gp_training"
    cmd = [
        sys.executable,
        str(gp_script),
        "--model-version",
        gp_version,
        "--save-dir",
        str(out_dir),
        "--grid-x",
        "7",
        "8",
        "9",
    ]
    try:
        subprocess.run(cmd, check=False)
    except Exception as exc:
        print(f"[warn] GP training plots skipped: {exc}")


def plot_all_extras(mat_root: Path, results_dir: Path, summary_csv: Path, v7: float = 10.0) -> None:
    plot_fig6_bar(summary_csv, results_dir / "fig6_bar_mean.png")
    plot_fig6_heatmap(summary_csv, results_dir / "fig6_heatmap_v10.png", v_max=v7)

    for traj in TRAJS:
        plot_fig7_xy(mat_root, traj, v7, results_dir / f"fig7_{traj}_v{v7:.1f}_xy.png")
        plot_fig7_cumerr(mat_root, traj, v7, results_dir / f"fig7_{traj}_v{v7:.1f}_cumerr.png")
        plot_fig7_inst_err(mat_root, traj, v7, results_dir / f"fig7_{traj}_v{v7:.1f}_insterr.png")
        plot_ref_timeseries(mat_root, traj, v7, results_dir / f"ref_timeseries_{traj}_v{v7:.1f}.png")
        plot_track3d(mat_root, traj, v7, results_dir / f"track3d_{traj}_v{v7:.1f}.png")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot all reproducible figures (Chinese).")
    parser.add_argument(
        "--fig",
        choices=["5", "6", "7", "extra", "gp", "all"],
        default="all",
        help="5=参考3D, 6=RMSE曲线, 7=跟踪对比, extra=补充图, gp=GP训练, all=全部",
    )
    parser.add_argument("--mat-root", type=Path, default=None)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--summary-csv", type=Path, default=None)
    parser.add_argument("--v-max-fig7", type=float, default=10.0, help="Fig.7 系列使用的速度")
    parser.add_argument("--gp-version", default="e0d4afb")
    args = parser.parse_args()

    global FP
    setup_chinese_style()
    FP = chinese_fontproperties()
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.35})
    paths = repro_paths()
    mat_root = args.mat_root or paths["mat"]
    results_dir = args.results_dir or paths["results"]
    results_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = args.summary_csv or (results_dir / "fig6_summary.csv")

    if args.fig in ("6", "all"):
        if not summary_csv.is_file():
            print(f"[error] run summarize_results.py first: {summary_csv}")
            return 1
        plot_fig6(summary_csv, results_dir / "fig6_plot.png")

    if args.fig in ("5", "all"):
        plot_fig5(mat_root, results_dir, v_max=args.v_max_fig7)

    if args.fig in ("7", "extra", "all"):
        if not summary_csv.is_file() and args.fig == "all":
            print(f"[error] missing {summary_csv}")
            return 1
        if summary_csv.is_file() and args.fig in ("extra", "all"):
            plot_all_extras(mat_root, results_dir, summary_csv, v7=args.v_max_fig7)
        elif args.fig == "7":
            for traj in TRAJS:
                plot_fig7_xy(mat_root, traj, args.v_max_fig7, results_dir / f"fig7_{traj}_v{args.v_max_fig7:.1f}_xy.png")
                plot_fig7_cumerr(mat_root, traj, args.v_max_fig7, results_dir / f"fig7_{traj}_v{args.v_max_fig7:.1f}_cumerr.png")

    if args.fig in ("gp", "all"):
        plot_gp_training(paths["scripts"], results_dir, args.gp_version)

    print(f"[done] figures in {results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
