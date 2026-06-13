#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

GP_VERSION="${1:-}"
GP_NAME="${2:-gazebo_sim_gp}"
TRIALS=${TRIALS:-1}

if [ -z "${GP_VERSION}" ]; then
  echo "Usage: $0 <gp_model_git_hash> [model_name]"
  echo "Train GP first via scripts/05_train_gp_model.sh"
  exit 1
fi

declare -A RUNS=(
  ["nominal:circle:10.0"]=1
  ["ssi:circle:10.0"]=1
  ["gpmpc:circle:10.0"]=1
  ["nominal:lemniscate:10.0"]=1
  ["ssi:lemniscate:10.0"]=1
  ["gpmpc:lemniscate:10.0"]=1
)

for key in "${!RUNS[@]}"; do
  IFS=':' read -r algo traj vmax <<< "${key}"
  for trial in $(seq 1 "${TRIALS}"); do
    echo "==== Fig7 ${algo} | ${traj} | v=${vmax} | trial=${trial} ===="
    extra=()
    if [ "${algo}" = "gpmpc" ]; then
      extra=(--gp-model-version "${GP_VERSION}" --gp-model-name "${GP_NAME}")
    fi
    python3 "${SCRIPT_DIR}/run_single_trial.py" \
      --algorithm "${algo}" \
      --trajectory "${traj}" \
      --v-max "${vmax}" \
      --trial "${trial}" \
      "${extra[@]}"
  done
done

echo "[done] Fig.7 mat files archived under data/mat/"
