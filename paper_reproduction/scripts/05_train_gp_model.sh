#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

ROS_MPC="${WS_ROOT}/src/SSI-MPC/ros_mpc"
DATASET_NAME="${DATASET_NAME:-gazebo_dataset}"
DATA_CSV="${ROS_MPC}/data/${DATASET_NAME}/train/dataset_001.csv"
MODEL_NAME="${MODEL_NAME:-gazebo_sim_gp}"

if [ ! -f "${DATA_CSV}" ]; then
  echo "[error] GP training dataset missing: ${DATA_CSV}" >&2
  echo "Collect data first (Gazebo must be running):" >&2
  echo "  bash ${SCRIPT_DIR}/05a_collect_gp_dataset.sh" >&2
  exit 1
fi

echo "[step 1/2] Train GP models for vx/vy/vz error components (indices 7,8,9)"
echo "[info] dataset: ${DATA_CSV} ($(wc -l < "${DATA_CSV}") lines)"
cd "${ROS_MPC}"

python3 src/model_fitting/gp_fitting.py --n_points 20 --model_name "${MODEL_NAME}" --x 7 --y 7
python3 src/model_fitting/gp_fitting.py --n_points 20 --model_name "${MODEL_NAME}" --x 8 --y 8
python3 src/model_fitting/gp_fitting.py --n_points 20 --model_name "${MODEL_NAME}" --x 9 --y 9

echo
echo "[step 2/2] Model folders under ${ROS_MPC}/results/model_fitting/"
GIT_HASH="$(git -C "${ROS_MPC}" describe --always 2>/dev/null || true)"
if [ -n "${GIT_HASH}" ]; then
  echo "[info] use this hash for GP-MPC runs: ${GIT_HASH}"
  ls -la "${ROS_MPC}/results/model_fitting/${GIT_HASH}/${MODEL_NAME}/" 2>/dev/null || true
else
  ls -1 "${ROS_MPC}/results/model_fitting/" 2>/dev/null || true
fi

echo
echo "Example GP-MPC trial:"
echo "  python3 ${SCRIPT_DIR}/run_single_trial.py \\"
echo "    --algorithm gpmpc --trajectory circle --v-max 10.0 --trial 1 \\"
echo "    --gp-model-version ${GIT_HASH:-<git_hash>} --gp-model-name ${MODEL_NAME} --skip-gazebo-check"
