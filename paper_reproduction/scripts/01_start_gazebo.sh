#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

echo "Launch Gazebo + Hummingbird (50% physics speed)."
echo "After GUI appears: click Connect and Arm Bridge."
roslaunch ros_mpc quadrotor_empty_world.launch enable_command_feedthrough:=True
