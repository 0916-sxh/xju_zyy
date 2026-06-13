#!/usr/bin/env bash
# Source ROS + Python paths for paper reproduction.
# Usage: source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh

REPRO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WS_ROOT="$(cd "${REPRO_DIR}/../.." && pwd)"

if [ -f "${WS_ROOT}/devel/setup.bash" ]; then
  # shellcheck disable=SC1091
  source "${WS_ROOT}/devel/setup.bash"
else
  echo "[warn] ${WS_ROOT}/devel/setup.bash not found. Run 'catkin_make --pkg paper_reproduction' first."
fi

export PYTHONPATH="${WS_ROOT}/src/SSI-MPC/ros_mpc:${PYTHONPATH:-}"

# mpc virtualenv (override with: export MPC_VENV=/path/to/venv)
MPC_VENV="${MPC_VENV:-${HOME}/zyy/mpc_venv}"
if [ -f "${MPC_VENV}/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "${MPC_VENV}/bin/activate"
  echo "[paper_reproduction] Python venv: ${MPC_VENV} ($(python3 --version 2>&1))"
else
  echo "[warn] mpc venv not found at ${MPC_VENV}; using current python: $(command -v python3)"
fi

export PAPER_REPRO_DIR="${REPRO_DIR}"
export PAPER_REPRO_DATA="${REPRO_DIR}/data"
export ROS_MPC_DIR="${WS_ROOT}/src/SSI-MPC/ros_mpc"

echo "[paper_reproduction] REPRO_DIR=${REPRO_DIR}"
echo "[paper_reproduction] WS_ROOT=${WS_ROOT}"
