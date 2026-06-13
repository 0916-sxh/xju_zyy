#!/usr/bin/env bash
# Fig.6 GP-MPC batch: 4 trajectories × 5 speeds × TRIALS (default 1).
# Requires trained GP model (05_train_gp_model.sh).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

bash "${SCRIPT_DIR}/wait_for_gazebo.sh" 30

GP_VERSION="${GP_VERSION:-e0d4afb}"
GP_NAME="${GP_NAME:-gazebo_sim_gp}"
TRAJS=(circle wrapped_circle lemniscate wrapped_lemniscate)
SPEEDS=(2.5 5.0 7.5 10.0 12.5)
TRIALS=${TRIALS:-1}
RESUME=${RESUME:-1}
CONTINUE_ON_ERROR=${CONTINUE_ON_ERROR:-1}

RESUME_ARGS=()
if [ "${RESUME}" = "1" ]; then
  RESUME_ARGS=(--resume)
fi

echo "Fig.6 GP-MPC batch: trajectories=${TRAJS[*]} speeds=${SPEEDS[*]} trials=${TRIALS}"
echo "GP_VERSION=${GP_VERSION} GP_NAME=${GP_NAME} RESUME=${RESUME}"

FAILED=0
OK=0

for traj in "${TRAJS[@]}"; do
  for speed in "${SPEEDS[@]}"; do
    for trial in $(seq 1 "${TRIALS}"); do
      echo "==== gpmpc | ${traj} | v=${speed} | trial=${trial} ===="
      if python3 "${SCRIPT_DIR}/run_single_trial.py" \
        --algorithm gpmpc \
        --trajectory "${traj}" \
        --v-max "${speed}" \
        --trial "${trial}" \
        --gp-model-version "${GP_VERSION}" \
        --gp-model-name "${GP_NAME}" \
        --skip-gazebo-check \
        "${RESUME_ARGS[@]}"; then
        OK=$((OK + 1))
      else
        if [ "${CONTINUE_ON_ERROR}" = "1" ]; then
          echo "[warn] trial failed, continuing..."
          FAILED=$((FAILED + 1))
        else
          exit 1
        fi
      fi
    done
  done
done

python3 "${SCRIPT_DIR}/summarize_results.py"
echo "[done] GP-MPC batch finished. ok=${OK} failed=${FAILED}"
