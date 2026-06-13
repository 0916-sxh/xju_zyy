#!/usr/bin/env python3
"""Regenerate GP training figures with Chinese labels (paper_reproduction)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# ros_mpc on PYTHONPATH via env_setup.sh
from config.configuration_parameters import ModelFitConfig as Conf
from src.model_fitting.gp_common import GPDataset, read_dataset, restore_gp_regressors
from src.utils.utils import load_pickled_models


def setup_chinese_matplotlib() -> None:
    import matplotlib.font_manager as fm

    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                fm.fontManager.addfont(path)
            except Exception:
                pass

    preferred = [
        "Noto Sans CJK SC",
        "Noto Sans CJK JP",
        "WenQuanYi Micro Hei",
        "SimHei",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in preferred:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            break
    else:
        plt.rcParams["font.sans-serif"] = preferred + ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


STATE_LABELS_CN = [
    r"$p_x$ [m]",
    r"$p_y$ [m]",
    r"$p_z$ [m]",
    r"$q_w$ [rad]",
    r"$q_x$ [rad]",
    r"$q_y$ [rad]",
    r"$q_z$ [rad]",
    r"$v_x$ [m/s]",
    r"$v_y$ [m/s]",
    r"$v_z$ [m/s]",
    r"$\omega_x$ [rad/s]",
    r"$\omega_y$ [rad/s]",
    r"$\omega_z$ [rad/s]",
]

VEL_ERROR_CN = {
    7: r"$v_x$ 速度误差 [m/s]",
    8: r"$v_y$ 速度误差 [m/s]",
    9: r"$v_z$ 速度误差 [m/s]",
}


def plot_test_set_timeseries(
    gp_ensemble,
    test_gp_ds: GPDataset,
    y_dims: list[int],
    save_path: Path | None,
    show: bool,
) -> None:
    x_test = test_gp_ds.get_x(pruned=True, raw=True)
    u_test = test_gp_ds.get_u(pruned=True, raw=True)
    y_test = test_gp_ds.get_y(pruned=True, raw=False)
    dt_test = test_gp_ds.get_dt(pruned=True)
    x_pred = test_gp_ds.get_x_pred(pruned=True, raw=False)

    ensemble_y_dims = [int(np.where(gp_ensemble.dim_idx == y_dim)[0][0]) for y_dim in y_dims]

    print("测试集预测...")
    outs = gp_ensemble.predict(x_test.T, u_test.T, return_std=True, progress_bar=True)
    mean_estimate = np.atleast_2d(np.atleast_2d(outs["pred"])[ensemble_y_dims]).T
    std_estimate = np.atleast_2d(np.atleast_2d(outs["cov_or_std"])[ensemble_y_dims]).T
    mean_estimate = mean_estimate * dt_test[:, np.newaxis]
    std_estimate = std_estimate * dt_test[:, np.newaxis]

    y_test = y_test * dt_test[:, np.newaxis]

    nominal_diff = y_test.copy()
    augmented_diff = nominal_diff - mean_estimate
    mean_estimate = mean_estimate + x_pred

    nominal_rmse = np.mean(np.abs(nominal_diff), axis=0)
    augmented_rmse = np.mean(np.abs(augmented_diff), axis=0)

    t_vec = np.cumsum(dt_test)
    n_plots = len(y_dims)
    fig, axes = plt.subplots(n_plots, 1, figsize=(10, 3.2 * n_plots), squeeze=False)

    for i, y_dim in enumerate(y_dims):
        ax = axes[i, 0]
        ax.plot(t_vec, np.zeros_like(augmented_diff[:, i]), "k", linewidth=1)
        ax.plot(t_vec, augmented_diff[:, i], "b", label="GP 修正误差")
        ax.plot(t_vec, augmented_diff[:, i] - 3 * std_estimate[:, i], ":c")
        ax.plot(t_vec, augmented_diff[:, i] + 3 * std_estimate[:, i], ":c", label="±3σ 置信带")
        ax.plot(t_vec, nominal_diff[:, i], "r", label="名义模型误差")
        ax.set_ylabel(VEL_ERROR_CN.get(y_dim, f"维度 {y_dim}"))
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)
        ax.set_title(
            f"平均步长: {float(np.mean(dt_test)):.2f} s | "
            f"名义 RMSE: {nominal_rmse[i]:.5f} m/s | "
            f"GP 修正 RMSE: {augmented_rmse[i]:.5f} m/s"
        )
        if i == n_plots - 1:
            ax.set_xlabel("时间 [s]")

    fig.suptitle("GP 测试集误差对比", fontsize=14, y=1.01)
    fig.tight_layout()

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[info] 已保存: {save_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_single_feature_grid(
    gp_ensemble,
    test_ds,
    x_feat: int,
    y_dim: int,
    save_path: Path | None,
    show: bool,
) -> None:
    test_gp_ds = GPDataset(
        test_ds,
        x_features=[x_feat],
        u_features=[],
        y_dim=y_dim,
        cap=Conf.velocity_cap,
        n_bins=Conf.histogram_bins,
        thresh=Conf.histogram_threshold,
        visualize_data=False,
    )
    x_test = test_gp_ds.get_x(pruned=True, raw=True)
    u_test = test_gp_ds.get_u(pruned=True, raw=True)
    y_test = test_gp_ds.get_y(pruned=True, raw=False)

    y_idx = int(np.where(gp_ensemble.dim_idx == y_dim)[0][0])
    outs = gp_ensemble.predict(x_test.T, u_test.T)
    y_pred = np.atleast_2d(np.atleast_2d(outs["pred"])[y_idx])[0, :]
    y_mse = y_test[:, 0] if y_test.ndim > 1 else y_test

    n_bins = 20
    feat_vals = x_test[:, x_feat]
    _, bins = np.histogram(feat_vals, bins=n_bins)
    hist_indices = np.digitize(feat_vals, bins)
    win_average = np.zeros(n_bins)
    for i in range(n_bins):
        mask = hist_indices == i + 1
        win_average[i] = np.mean(y_mse[mask]) if np.any(mask) else np.nan
    bin_midpoints = bins[:-1] + np.diff(bins)[0] / 2

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4.5))
    ax0.scatter(feat_vals, y_mse, s=8, alpha=0.5)
    ax0.set_xlabel(STATE_LABELS_CN[x_feat])
    ax0.set_ylabel("误差 [m/s²]")
    ax0.set_title("处理后数据集")
    ax0.grid(True, alpha=0.3)

    ax1.scatter(feat_vals, y_pred, s=8, alpha=0.5, label="GP 预测")
    ax1.plot(bin_midpoints, win_average, "k-", linewidth=2, label="分箱滑动平均")
    ax1.set_xlabel(STATE_LABELS_CN[x_feat])
    ax1.set_title(f"GP 预测 — {VEL_ERROR_CN.get(y_dim, f'维度{y_dim}')}")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    fig.tight_layout()
    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[info] 已保存: {save_path}")
    if show:
        plt.show()
    else:
        plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot GP training results with Chinese labels.")
    parser.add_argument("--model-version", default="", help="Git hash folder, e.g. e0d4afb")
    parser.add_argument("--model-name", default="gazebo_sim_gp")
    parser.add_argument("--dataset-name", default=Conf.ds_name)
    parser.add_argument("--y-dims", type=int, nargs="+", default=[7, 8, 9], help="Velocity error dims to plot")
    parser.add_argument("--grid-x", type=int, nargs="*", default=[], help="Extra 1D grid plots, e.g. --grid-x 7 8 9")
    parser.add_argument(
        "--save-dir",
        default=os.environ.get("PAPER_REPRO_DATA", "") + "/figures/gp_training",
        help="Directory for PNG output",
    )
    parser.add_argument("--show", action="store_true", help="Show interactive windows")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_chinese_matplotlib()

    ros_mpc = Path(os.environ.get("ROS_MPC_DIR", ""))
    if not ros_mpc.is_dir():
        print("[error] ROS_MPC_DIR not set. source paper_reproduction/scripts/env_setup.sh first.", file=sys.stderr)
        return 1

    git_hash = args.model_version or (
        os.popen(f"git -C '{ros_mpc}' describe --always 2>/dev/null").read().strip()
    )
    if not git_hash:
        print("[error] could not determine model git hash; pass --model-version", file=sys.stderr)
        return 1

    load_options = {
        "git": git_hash,
        "model_name": args.model_name,
        "params": Conf.ds_metadata,
    }
    loaded = load_pickled_models(model_options=load_options)
    if loaded is None:
        print(f"[error] model not found: {git_hash}/{args.model_name}", file=sys.stderr)
        return 1

    gp_ensemble = restore_gp_regressors(loaded)
    available = sorted(set(int(d) for d in gp_ensemble.dim_idx))
    y_dims = [d for d in args.y_dims if d in available]
    if not y_dims:
        print(f"[error] none of {args.y_dims} in trained model dims {available}", file=sys.stderr)
        return 1
    if len(y_dims) < len(args.y_dims):
        missing = sorted(set(args.y_dims) - set(y_dims))
        print(f"[warn] missing trained dims {missing}; plot available dims only: {y_dims}")

    test_ds = read_dataset(args.dataset_name, True, Conf.ds_metadata)
    test_gp_ds = GPDataset(
        test_ds,
        x_features=[7, 8, 9],
        u_features=[],
        y_dim=y_dims if len(y_dims) > 1 else y_dims[0],
        cap=Conf.velocity_cap,
        n_bins=Conf.histogram_bins,
        thresh=Conf.histogram_threshold,
        visualize_data=False,
    )

    save_dir = Path(args.save_dir).expanduser()
    show = args.show

    plot_test_set_timeseries(
        gp_ensemble,
        test_gp_ds,
        y_dims,
        save_path=save_dir / f"gp_test_error_{git_hash}.png",
        show=show,
    )

    for x_feat in args.grid_x or []:
        for y_dim in y_dims:
            if x_feat != y_dim:
                continue
            plot_single_feature_grid(
                gp_ensemble,
                test_ds,
                x_feat=x_feat,
                y_dim=y_dim,
                save_path=save_dir / f"gp_grid_v{x_feat}_{git_hash}.png",
                show=show,
            )

    print(f"[done] figures in {save_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
