"""Generate ZYY combined letter reference trajectory for paper_reproduction."""

from __future__ import annotations

import numpy as np

from src.quad_mpc.create_ros_mpc import custom_quad_param_loader
from src.utils.trajectory_generator import fit_multi_segment_polynomial_trajectory, get_full_traj
from src.utils.trajectories import minimum_snap_trajectory_generator

# Letter geometry (half-width / half-height in local frame)
_LW = 1.1
_LH = 1.15
_JY = 0.2  # Y fork junction height


def _densify_polyline(points: np.ndarray, samples_per_edge: int = 4) -> np.ndarray:
    """Insert collinear samples so minimum-snap stays close to straight strokes."""
    if len(points) < 2:
        return points
    out: list[np.ndarray] = []
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        seg = np.linspace(a, b, samples_per_edge + 1)
        if i > 0:
            seg = seg[1:]
        out.append(seg)
    return np.vstack(out)


def _letter_z_polyline() -> np.ndarray:
    """Block Z: top bar -> diagonal (via midpoint) -> bottom bar."""
    w, h = _LW, _LH
    return np.array(
        [
            [-w, h],
            [w, h],
            [0.0, 0.0],
            [-w, -h],
            [w, -h],
        ],
        dtype=float,
    )


def _letter_y_polyline(mirror: bool = False) -> np.ndarray:
    """Block Y: fork then vertical stem (5 points, one stem pass)."""
    w, h = _LW, _LH
    jy = _JY
    if mirror:
        return np.array(
            [
                [w, h],
                [0.0, jy],
                [-w, h],
                [0.0, jy],
                [0.0, -h],
            ],
            dtype=float,
        )
    return np.array(
        [
            [-w, h],
            [0.0, jy],
            [w, h],
            [0.0, jy],
            [0.0, -h],
        ],
        dtype=float,
    )


def _penup_transit(
    end_xy: np.ndarray,
    start_xy: np.ndarray,
    cruise_lift: float,
    samples_per_edge: int = 6,
    below: bool = True,
) -> np.ndarray:
    """Connect letters via a low bypass (under the text line) to keep glyphs clean."""
    if below:
        low_y = min(float(end_xy[1]), float(start_xy[1])) - cruise_lift
        path = np.array(
            [
                end_xy,
                [end_xy[0], low_y],
                [start_xy[0], low_y],
                start_xy,
            ],
            dtype=float,
        )
    else:
        top_y = max(float(end_xy[1]), float(start_xy[1])) + cruise_lift
        path = np.array(
            [
                end_xy,
                [end_xy[0], top_y],
                [start_xy[0], top_y],
                start_xy,
            ],
            dtype=float,
        )
    return _densify_polyline(path, samples_per_edge)


def zyy_waypoints(
    z: float = 2.5,
    center_xy: tuple[float, float] = (8.0, 0.0),
    scale: float = 1.15,
    letter_spacing: float = 5.2,
    cruise_lift: float = 1.35,
    samples_per_edge: int = 6,
) -> np.ndarray:
    """Z → Y → Y′ as one path: block strokes + overhead pen-up links."""
    cx, cy = center_xy
    s = scale
    gap = letter_spacing * s
    lift = cruise_lift * s

    letter_defs = (
        _letter_z_polyline(),
        _letter_y_polyline(mirror=False),
        _letter_y_polyline(mirror=True),
    )
    centers = (
        (cx - gap, cy),
        (cx, cy),
        (cx + gap, cy),
    )

    parts: list[np.ndarray] = []
    for i, (poly, (lcx, lcy)) in enumerate(zip(letter_defs, centers)):
        local = poly * s
        local[:, 0] += lcx
        local[:, 1] += lcy
        stroke = _densify_polyline(local, samples_per_edge)
        if i == 0:
            parts.append(stroke)
        else:
            transit = _penup_transit(parts[-1][-1], stroke[0], lift, samples_per_edge)
            parts.append(transit)
            parts.append(stroke)

    xy = np.vstack(parts)
    return np.column_stack([xy, np.full(len(xy), z)])


def letter_label_positions(
    center_xy: tuple[float, float] = (8.0, 0.0),
    scale: float = 1.15,
    letter_spacing: float = 6.0,
) -> list[tuple[str, float, float]]:
    cx, cy = center_xy
    gap = letter_spacing * scale
    return [
        ("Z", cx - gap, cy - 2.0 * scale),
        ("Y", cx, cy - 2.0 * scale),
        ("Y", cx + gap, cy - 2.0 * scale),
    ]


def _segment_times(waypoints: np.ndarray, v_max: float, lin_acc: float) -> list[float]:
    seg_lengths = np.linalg.norm(np.diff(waypoints, axis=0), axis=1)
    seg_times: list[float] = []
    for length in seg_lengths:
        t_acc = v_max / lin_acc
        d_acc = 0.5 * lin_acc * t_acc * t_acc
        if 2 * d_acc >= length:
            seg_times.append(2 * np.sqrt(length / lin_acc))
        else:
            seg_times.append(2 * t_acc + (length - 2 * d_acc) / v_max)
    return [max(t, 0.35) for t in seg_times]


def _build_from_waypoints(
    waypoints: np.ndarray,
    v_max: float,
    lin_acc: float,
    opt_dt: float,
    quad,
    plot: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    seg_times = _segment_times(waypoints, v_max, lin_acc)
    pos_traj = waypoints.T
    yaw_traj = np.zeros(waypoints.shape[0])
    poly = fit_multi_segment_polynomial_trajectory(pos_traj[:3, :], yaw_traj)
    full_traj, yaw, t_ref = get_full_traj(poly, seg_times, opt_dt)
    return minimum_snap_trajectory_generator(full_traj, yaw, t_ref, quad, map_limits=None, plot=plot)


def generate_letter_trajectory(
    letter: str,
    v_max: float = 10.0,
    z: float = 2.5,
    lin_acc: float = 0.25,
    center_xy: tuple[float, float] = (8.0, 0.0),
    scale: float = 1.15,
    quad_name: str = "hummingbird",
    opt_dt: float = 0.02,
    plot: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    quad = custom_quad_param_loader(quad_name)

    if letter == "zyy":
        waypoints = zyy_waypoints(z=z, center_xy=center_xy, scale=scale)
        traj_name = "letter_zyy"
    elif letter == "z":
        local = _letter_z_polyline() * scale
        local[:, 0] += center_xy[0]
        local[:, 1] += center_xy[1]
        waypoints = np.column_stack([_densify_polyline(local), np.full(len(local), z)])
        traj_name = "letter_z"
    elif letter in ("y", "y2"):
        local = _letter_y_polyline(mirror=(letter == "y2")) * scale
        local[:, 0] += center_xy[0]
        local[:, 1] += center_xy[1]
        dense = _densify_polyline(local)
        waypoints = np.column_stack([dense, np.full(len(dense), z)])
        traj_name = "letter_y2" if letter == "y2" else "letter_y"
    else:
        raise ValueError(f"unknown letter {letter!r}; use zyy, z, y, y2")

    x_ref, t_ref, u_ref = _build_from_waypoints(waypoints, v_max, lin_acc, opt_dt, quad, plot)
    return x_ref, t_ref, u_ref, traj_name


if __name__ == "__main__":
    import sys
    from pathlib import Path

    import matplotlib.pyplot as plt

    _SCRIPT_DIR = Path(__file__).resolve().parent
    if str(_SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPT_DIR))
    from plot_cn_font import chinese_fontproperties, setup_chinese_style

    setup_chinese_style()
    fp = chinese_fontproperties()

    wpts = zyy_waypoints()
    x_ref, t_ref, _, _ = generate_letter_trajectory("zyy", v_max=10.0, plot=False)
    out_dir = Path(__file__).resolve().parents[1] / "data" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax = axes[0]
    ax.plot(x_ref[:, 0], x_ref[:, 1], "b-", linewidth=2.2, label="平滑轨迹")
    ax.plot(wpts[:, 0], wpts[:, 1], "r.", markersize=2, alpha=0.35, label="密航点")
    for text, lx, ly in letter_label_positions():
        ax.annotate(text, (lx, ly), fontsize=26, fontweight="bold", ha="center", fontproperties=fp, color="#444")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("ZYY 连续轨迹 — XY 俯视图", fontproperties=fp, fontsize=13)
    ax.legend(prop=fp, fontsize=9)

    ax3 = axes[1]
    s, gap, cx = 1.15, 5.2 * 1.15, 8.0
    for poly, ox in (
        (_letter_z_polyline(), cx - gap),
        (_letter_y_polyline(False), cx),
        (_letter_y_polyline(True), cx + gap),
    ):
        c = poly * s
        c[:, 0] += ox
        ax3.plot(c[:, 0], c[:, 1], "k--", linewidth=1.5, alpha=0.55)
        ax3.plot(c[:, 0], c[:, 1], "ko", markersize=7)
    ax3.plot(x_ref[:, 0], x_ref[:, 1], "b-", linewidth=2)
    ax3.set_aspect("equal")
    ax3.grid(True, alpha=0.3)
    ax3.set_xlabel("x (m)")
    ax3.set_ylabel("y (m)")
    ax3.set_title(f"方块字骨架 + 平滑轨迹（{t_ref[-1]:.0f} s）", fontproperties=fp, fontsize=12)

    plt.tight_layout()
    out_png = out_dir / "letter_zyy_preview.png"
    plt.savefig(out_png, bbox_inches="tight", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(wpts[:, 0], wpts[:, 1], "r--", linewidth=1.0, alpha=0.45, label="航点折线")
    ax.plot(x_ref[:, 0], x_ref[:, 1], "k-", linewidth=2.5, label="平滑轨迹")
    for text, lx, ly in letter_label_positions():
        ax.annotate(text, (lx, ly), fontsize=28, fontweight="bold", ha="center", fontproperties=fp, color="#333")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("参考轨迹 ZYY（规划路径）", fontproperties=fp, fontsize=14)
    ax.legend(prop=fp, fontsize=9, loc="upper right")
    ref_png = out_dir / "letter_zyy_ref_only_v10.0.png"
    fig.savefig(ref_png, bbox_inches="tight", dpi=150)
    plt.close(fig)

    print(f"preview -> {out_png}")
    print(f"preview -> {ref_png}")
    print(f"samples={len(t_ref)}  duration={t_ref[-1]:.1f}s  waypoints={len(wpts)}")
