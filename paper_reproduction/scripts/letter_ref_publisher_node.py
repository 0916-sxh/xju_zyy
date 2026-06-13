#!/usr/bin/env python3.8
"""Publish Z/Y letter reference trajectories for MPC tracking (paper_reproduction)."""

from __future__ import annotations

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROS_MPC_DIR = os.environ.get("ROS_MPC_DIR", os.path.abspath(os.path.join(_SCRIPT_DIR, "../../SSI-MPC/ros_mpc")))
for p in (_SCRIPT_DIR, ROS_MPC_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
import rospy
from std_msgs.msg import Bool
from ros_mpc.msg import ReferenceTrajectory

from letter_trajectories import generate_letter_trajectory


class LetterReferencePublisher:
    def __init__(self) -> None:
        rospy.init_node("letter_reference_generator")
        self.mpc_busy = True

        plot = rospy.get_param("~plot", default=False)
        letter = rospy.get_param("~letter", default="z")
        loop_z = rospy.get_param("~loop_z", default=2.5)
        loop_v_max = rospy.get_param("~loop_v_max", default=10.0)
        loop_a = rospy.get_param("~loop_lin_a", default=0.25)
        scale = rospy.get_param("~letter_scale", default=1.15)
        center_x = rospy.get_param("~letter_center_x", default=8.0)
        center_y = rospy.get_param("~letter_center_y", default=0.0)

        t_horizon = rospy.get_param("~t_horizon", default=1.0)
        n_nodes = rospy.get_param("~n_nodes", default=10)
        control_freq_factor = rospy.get_param("~control_freq_factor", default=5)
        opt_dt = t_horizon / (n_nodes * control_freq_factor)

        x_ref, t_ref, u_ref, traj_name = generate_letter_trajectory(
            letter=letter,
            v_max=loop_v_max,
            z=loop_z,
            lin_acc=loop_a,
            center_xy=(center_x, center_y),
            scale=scale,
            opt_dt=opt_dt,
            plot=plot,
        )

        self.msg = ReferenceTrajectory()
        self.msg.traj_name = traj_name
        self.msg.v_input = loop_v_max
        self.msg.seq_len = x_ref.shape[0]
        self.msg.trajectory = np.reshape(x_ref, (-1,)).tolist()
        self.msg.dt = t_ref.tolist()
        self.msg.inputs = np.reshape(u_ref, (-1,)).tolist()
        self.published = False

        self.pub = rospy.Publisher("reference", ReferenceTrajectory, queue_size=1)
        rospy.Subscriber("busy", Bool, self._busy_cb)
        rospy.loginfo(
            "Letter '%s' ready: %d samples, duration %.1fs, v_max=%.1f",
            letter,
            x_ref.shape[0],
            t_ref[-1],
            loop_v_max,
        )

    def _busy_cb(self, msg: Bool) -> None:
        self.mpc_busy = msg.data

    def spin(self) -> None:
        rate = rospy.Rate(20)
        sent_end = False
        while not rospy.is_shutdown():
            if not self.mpc_busy and not self.published:
                rospy.loginfo("Publishing letter trajectory: %s", self.msg.traj_name)
                self.pub.publish(self.msg)
                self.published = True
                self.mpc_busy = True
            elif self.published and not self.mpc_busy and not sent_end:
                end_msg = ReferenceTrajectory()
                end_msg.seq_len = 0
                self.pub.publish(end_msg)
                sent_end = True
                rospy.loginfo("Letter trajectory complete.")
                rospy.signal_shutdown("Letter trajectory sent")
                break
            rate.sleep()


if __name__ == "__main__":
    LetterReferencePublisher().spin()
