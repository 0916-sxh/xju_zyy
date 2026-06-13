#!/usr/bin/env bash
# Screen promising controller variants @ v=10 m/s on all four trajectories.
# Goal: find settings that beat default SSI-MPC (paper config).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

bash "${SCRIPT_DIR}/wait_for_gazebo.sh" 30

GP_VERSION="${GP_VERSION:-e0d4afb}"
GP_NAME="${GP_NAME:-gazebo_sim_gp}"
RDRV_VERSION="${RDRV_VERSION:-${GP_VERSION}}"
RDRV_NAME="${RDRV_NAME:-gazebo_sim_rdrv}"
V_MAX="${V_MAX:-10.0}"
RESUME=${RESUME:-1}
CONTINUE_ON_ERROR=${CONTINUE_ON_ERROR:-1}

# Most likely improvements over default SSI; skip nominal/gpmpc (already benchmarked).
ALGOS=(ssi ssi_n100 ssi_n100_lr015 ssi_longhorizon rdrv)
TRAJS=(circle wrapped_circle lemniscate wrapped_lemniscate)

RESUME_ARGS=()
if [ "${RESUME}" = "1" ]; then
  RESUME_ARGS=(--resume)
fi

echo "=== Tuning benchmark (effect-first) ==="
echo "algorithms=${ALGOS[*]}"
echo "trajectories=${TRAJS[*]} v_max=${V_MAX}"
echo "GP_VERSION=${GP_VERSION} RDRV_VERSION=${RDRV_VERSION}"

# Ensure RDRv model exists
RDRV_PKL="${ROS_MPC_DIR}/results/model_fitting/${RDRV_VERSION}/${RDRV_NAME}/gazebo.pkl"
if [ ! -f "${RDRV_PKL}" ]; then
  echo "[step] RDRv model not found, training..."
  MODEL_NAME="${RDRV_NAME}" bash "${SCRIPT_DIR}/08_train_rdrv_model.sh"
fi

FAILED=0
OK=0
for algo in "${ALGOS[@]}"; do
  for traj in "${TRAJS[@]}"; do
    echo "==== ${algo} | ${traj} | v=${V_MAX} ===="
    EXTRA_ARGS=()
    if [ "${algo}" = "rdrv" ]; then
      EXTRA_ARGS=(--rdrv-model-version "${RDRV_VERSION}" --rdrv-model-name "${RDRV_NAME}")
    fi
    if python3 "${SCRIPT_DIR}/run_single_trial.py" \
      --algorithm "${algo}" \
      --trajectory "${traj}" \
      --v-max "${V_MAX}" \
      --trial 1 \
      --skip-gazebo-check \
      "${RESUME_ARGS[@]}" \
      "${EXTRA_ARGS[@]}"; then
      OK=$((OK + 1))
    else
      FAILED=$((FAILED + 1))
      if [ "${CONTINUE_ON_ERROR}" != "1" ]; then
        exit 1
      fi
    fi
  done
done

python3 "${SCRIPT_DIR}/summarize_results.py" \
  --output "${PAPER_REPRO_DATA}/results/tuning_summary.csv"
python3 "${SCRIPT_DIR}/pick_best_algorithm.py" --v-max "${V_MAX}"
python3 "${SCRIPT_DIR}/plot_tuning_compare.py" --v-max "${V_MAX}"

echo "[done] tuning batch finished ok=${OK} failed=${FAILED}"
echo "See: data/results/tuning_compare_v${V_MAX}.png"
echo "See: data/results/best_algorithm.json"
