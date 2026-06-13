"""Algorithm definitions for paper_reproduction (no SSI-MPC source edits)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlgoSpec:
    """Launch configuration for one controller variant."""

    family: str  # mpc | gpmpc
    mat_prefix: str  # MPC | OLMPC | GPMPC
    label_cn: str
    launch_args: dict[str, str | int | float | bool] = field(default_factory=dict)
    needs_gp: bool = False
    needs_rdrv: bool = False


# Baseline paper algorithms + tuning candidates (ordered by expected performance).
ALGO_REGISTRY: dict[str, AlgoSpec] = {
    "nominal": AlgoSpec(
        family="mpc",
        mat_prefix="MPC",
        label_cn="名义 MPC",
        launch_args={"n_rf": 0},
    ),
    "ssi": AlgoSpec(
        family="mpc",
        mat_prefix="OLMPC",
        label_cn="SSI-MPC（论文默认）",
        launch_args={"n_rf": 50, "lr": 0.25},
    ),
    "ssi_n100": AlgoSpec(
        family="mpc",
        mat_prefix="OLMPC",
        label_cn="SSI-MPC M=100",
        launch_args={"n_rf": 100, "lr": 0.25},
    ),
    "ssi_n100_lr015": AlgoSpec(
        family="mpc",
        mat_prefix="OLMPC",
        label_cn="SSI-MPC M=100, η=0.15",
        launch_args={"n_rf": 100, "lr": 0.15},
    ),
    "ssi_longhorizon": AlgoSpec(
        family="mpc",
        mat_prefix="OLMPC",
        label_cn="SSI-MPC 长预测域",
        launch_args={"n_rf": 50, "lr": 0.25, "t_horizon": 2, "n_nodes": 20},
    ),
    "ssi_heuristic": AlgoSpec(
        family="mpc",
        mat_prefix="OLMPC",
        label_cn="SSI-MPC 启发式特征",
        launch_args={"n_rf": 50, "lr": 0.25, "heuristic": True},
    ),
    "gpmpc": AlgoSpec(
        family="gpmpc",
        mat_prefix="GPMPC",
        label_cn="GP-MPC",
        launch_args={"model_type": "gp"},
        needs_gp=True,
    ),
    "rdrv": AlgoSpec(
        family="gpmpc",
        mat_prefix="GPMPC",
        label_cn="RDRv-MPC（线性阻力）",
        launch_args={"model_type": "rdrv"},
        needs_rdrv=True,
    ),
}

# Quick screening set @ v=10 m/s — most likely to beat default SSI.
TUNING_CANDIDATES = ["ssi", "ssi_n100", "ssi_n100_lr015", "ssi_longhorizon", "rdrv"]

BASELINE_COMPARE = ["nominal", "ssi", "gpmpc", "ssi_n100", "rdrv"]

ALL_ALGORITHMS = list(ALGO_REGISTRY.keys())


def get_algo(name: str) -> AlgoSpec:
    if name not in ALGO_REGISTRY:
        raise KeyError(f"unknown algorithm {name!r}; choices: {ALL_ALGORITHMS}")
    return ALGO_REGISTRY[name]
