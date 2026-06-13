#!/usr/bin/env bash
# Train RDRv (linear drag) model from existing Gazebo dataset — no Gazebo needed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

ROS_MPC="${WS_ROOT}/src/SSI-MPC/ros_mpc"
DATASET_NAME="${DATASET_NAME:-gazebo_dataset}"
DATA_CSV="${ROS_MPC}/data/${DATASET_NAME}/train/dataset_001.csv"
MODEL_NAME="${MODEL_NAME:-gazebo_sim_rdrv}"

if [ ! -f "${DATA_CSV}" ]; then
  echo "[error] dataset missing: ${DATA_CSV}" >&2
  echo "Run first: bash ${SCRIPT_DIR}/05a_collect_gp_dataset.sh" >&2
  exit 1
fi

echo "[info] training RDRv drag model from ${DATA_CSV}"
python3 "${SCRIPT_DIR}/train_rdrv_cn.py" --model-name "${MODEL_NAME}"

GIT_HASH="$(git -C "${ROS_MPC}" describe --always 2>/dev/null || ls -1 "${ROS_MPC}/results/model_fitting/" | tail -1)"
echo
echo "[done] RDRv model: ${ROS_MPC}/results/model_fitting/${GIT_HASH}/${MODEL_NAME}/"
ls -la "${ROS_MPC}/results/model_fitting/${GIT_HASH}/${MODEL_NAME}/" 2>/dev/null || true
echo
echo "Example trial:"
echo "  python3 ${SCRIPT_DIR}/run_single_trial.py \\"
echo "    --algorithm rdrv --trajectory circle --v-max 10.0 --trial 1 \\"
echo "    --rdrv-model-version ${GIT_HASH} --rdrv-model-name ${MODEL_NAME} --skip-gazebo-check"
