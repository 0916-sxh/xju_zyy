#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

N_SEEDS="${N_SEEDS:-10}"
DATASET_NAME="${DATASET_NAME:-gazebo_dataset}"

echo "[gp collect] Gazebo must be running (01_start_gazebo.sh) with Connect + Arm Bridge."
echo "[gp collect] Will fly ${N_SEEDS} random trajectories and write to ros_mpc/data/${DATASET_NAME}/"
echo "[gp collect] This typically takes 30-90 minutes at 50% physics speed."
echo "[gp collect] Done when ref_gen logs: No more references will be received"
echo

bash "${SCRIPT_DIR}/rearm_quad.sh"

roslaunch paper_reproduction gp_collect_dataset.launch \
  recording:=true \
  dataset_name:="${DATASET_NAME}" \
  n_seeds:="${N_SEEDS}"

DATA_CSV="${WS_ROOT}/src/SSI-MPC/ros_mpc/data/${DATASET_NAME}/train/dataset_001.csv"
if [ -f "${DATA_CSV}" ]; then
  echo "[gp collect] OK: $(wc -l < "${DATA_CSV}") lines in ${DATA_CSV}"
else
  echo "[error] expected dataset not found: ${DATA_CSV}" >&2
  exit 1
fi
