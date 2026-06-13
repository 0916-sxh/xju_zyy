#!/usr/bin/env bash
# Kill leftover MPC / ref_gen nodes from interrupted batch runs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

mapfile -t stale < <(pgrep -af "ros_mpc/nodes/mpc_node.py|ros_mpc/nodes/gp_mpc|reference_publisher_node.py|roslaunch.*paper_reproduction" || true)

if [ "${#stale[@]}" -eq 0 ]; then
  echo "[cleanup] no stale MPC/ref_gen/roslaunch processes"
  exit 0
fi

echo "[cleanup] stopping stale processes:"
printf '  %s\n' "${stale[@]}"

pkill -f "roslaunch.*paper_reproduction" 2>/dev/null || true
pkill -f "ros_mpc/nodes/mpc_node.py" 2>/dev/null || true
pkill -f "ros_mpc/nodes/gp_mpc_node.py" 2>/dev/null || true
pkill -f "paper_reproduction/scripts/gp_mpc_repro_node.py" 2>/dev/null || true
pkill -f "ros_mpc/nodes/reference_publisher_node.py" 2>/dev/null || true

sleep 2
echo "[cleanup] done"
