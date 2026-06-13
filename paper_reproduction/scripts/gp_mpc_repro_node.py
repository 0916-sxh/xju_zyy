#!/usr/bin/env python3.8
"""GP-MPC ROS node wrapper for paper reproduction.

Identical to ros_mpc/nodes/gp_mpc_node.py, but exposes the ~save_data parameter so
trajectory .mat files can be exported for Fig. 7 plotting.
Original SSI-MPC source is not modified.
"""

import os
import sys

ROS_MPC_DIR = os.environ.get("ROS_MPC_DIR")
if not ROS_MPC_DIR:
    ROS_MPC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../SSI-MPC/ros_mpc"))
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
if ROS_MPC_DIR not in sys.path:
    sys.path.insert(0, ROS_MPC_DIR)

import importlib.util

import rospy

from casadi_gp_compat import apply_casadi_gp_compat

apply_casadi_gp_compat()

from src.model_fitting.rdrv_fitting import load_rdrv

_gp_mpc_path = os.path.join(ROS_MPC_DIR, "nodes", "gp_mpc_node.py")
_spec = importlib.util.spec_from_file_location("gp_mpc_node", _gp_mpc_path)
_gp_mpc_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gp_mpc_module)
GPMPCWrapper = _gp_mpc_module.GPMPCWrapper

_BENCHMARK_DIR = os.path.join(ROS_MPC_DIR, "benchmark")
_orig_gpmpc_init = GPMPCWrapper.__init__
_orig_set_reference = GPMPCWrapper.set_reference
_orig_plot_mse_experiment = GPMPCWrapper.plot_tracking_mse_experiment


def _ensure_benchmark_data_dir(self) -> None:
    os.makedirs(_BENCHMARK_DIR, exist_ok=True)
    self.data_dir = _BENCHMARK_DIR


def _set_reference_benchmark(self, *args, **kwargs):
    _ensure_benchmark_data_dir(self)
    return _orig_set_reference(self, *args, **kwargs)


def _plot_mse_experiment_safe(self):
    if not self.plot:
        return
    try:
        _orig_plot_mse_experiment(self)
    except Exception as exc:
        rospy.logwarn("plot_tracking_mse_experiment skipped: %s", exc)


def _gpmpc_init_save_to_benchmark(self, *args, **kwargs):
    """gp_mpc_node.__init__ blocks forever; redirect saves via set_reference patch."""
    _orig_gpmpc_init(self, *args, **kwargs)


GPMPCWrapper.__init__ = _gpmpc_init_save_to_benchmark
GPMPCWrapper.set_reference = _set_reference_benchmark
GPMPCWrapper.plot_tracking_mse_experiment = _plot_mse_experiment_safe


def main():
    rospy.init_node("gp_mpc")

    recording_options = {
        "recording": rospy.get_param('~recording', default=True),
        "dataset_name": "deleteme",
        "training_split": True,
        "overwrite": True,
        "record_raw_optitrack": True,
    }

    dataset_name = rospy.get_param('~dataset_name', default=None)
    overwrite = rospy.get_param('~overwrite', default=None)
    training = rospy.get_param('~training_split', default=None)
    raw_optitrack = rospy.get_param('~record_raw_optitrack', default=None)
    if dataset_name is not None:
        recording_options["dataset_name"] = dataset_name
    if overwrite is not None:
        recording_options["overwrite"] = overwrite
    if training is not None:
        recording_options["training_split"] = training
    if raw_optitrack is not None:
        recording_options["record_raw_optitrack"] = raw_optitrack

    load_options = {
        "git": "b6e73a5",
        "model_name": "",
        "params": None,
    }
    git_id = rospy.get_param('~model_version', default=None)
    model_name = rospy.get_param('~model_name', default=None)
    model_type = rospy.get_param('~model_type', default="gp")
    if git_id is not None:
        load_options["git"] = git_id
    if model_name is not None:
        load_options["model_name"] = str(model_name)

    plot = rospy.get_param('~plot', default=False)
    save_data = rospy.get_param('~save_data', default=False)
    env = rospy.get_param('~environment', default='gazebo')
    default_quad = "hummingbird" if env == "gazebo" else "colibri"
    load_options["params"] = {env: "default"}

    if model_type == "rdrv":
        rdrv = load_rdrv(model_options=load_options)
        rospy.loginfo("RDRv drag matrix loaded (GP regressors disabled)")
    else:
        rdrv = None

    quad_name = rospy.get_param('~quad_name', default=None)
    quad_name = quad_name if quad_name is not None else default_quad

    if env == "gazebo":
        assert quad_name == "hummingbird"
        ekf_sync = False
    else:
        assert quad_name == "colibri"
        ekf_sync = rospy.get_param('~use_ekf_synchronization', default=False)

    reset = rospy.get_param('~reset_experiment', default=True)

    # RDRv shares the model directory with GP pickles; skip GP load but keep load_options metadata.
    _orig_load_pickled = _gp_mpc_module.load_pickled_models
    if model_type == "rdrv":
        _gp_mpc_module.load_pickled_models = lambda *args, **kwargs: None
    try:
        GPMPCWrapper(
            quad_name,
            env,
            recording_options,
            load_options,
            use_ekf=ekf_sync,
            rdrv=rdrv,
            plot=plot,
            reset_experiment=reset,
            save_data=save_data,
        )
    finally:
        _gp_mpc_module.load_pickled_models = _orig_load_pickled


if __name__ == "__main__":
    main()
