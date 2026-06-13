#!/usr/bin/env bash
# One continuous ZYY trajectory: compare nominal / ssi / gpmpc @ v=10 (3 runs).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

bash "${SCRIPT_DIR}/wait_for_gazebo.sh" 30

GP_VERSION="${GP_VERSION:-e0d4afb}"
GP_NAME="${GP_NAME:-gazebo_sim_gp}"
V_MAX="${V_MAX:-10.0}"
RESUME=${RESUME:-1}
CONTINUE_ON_ERROR=${CONTINUE_ON_ERROR:-1}
TRAJ="letter_zyy"

ALGOS=(nominal ssi gpmpc)
BEST_ALGO="${BEST_ALGO:-ssi}"
RUN_BEST_EXTRA="${RUN_BEST_EXTRA:-0}"

RESUME_ARGS=()
if [ "${RESUME}" = "1" ]; then
  RESUME_ARGS=(--resume)
fi

echo "=== ZYY 连续字母轨迹 benchmark ==="
echo "trajectory=${TRAJ}  algorithms=${ALGOS[*]}  v_max=${V_MAX}"
echo "runs: ${#ALGOS[@]} (三算法 × 一条 ZYY 轨迹)"

python3 "${SCRIPT_DIR}/letter_trajectories.py" || true

FAILED=0
OK=0
for algo in "${ALGOS[@]}"; do
  echo "==== ${algo} | ${TRAJ} | v=${V_MAX} ===="
  EXTRA=()
  if [ "${algo}" = "gpmpc" ]; then
    EXTRA=(--gp-model-version "${GP_VERSION}" --gp-model-name "${GP_NAME}")
  fi
  if python3 "${SCRIPT_DIR}/run_single_trial.py" \
    --algorithm "${algo}" \
    --trajectory "${TRAJ}" \
    --v-max "${V_MAX}" \
    --trial 1 \
    --skip-gazebo-check \
    "${RESUME_ARGS[@]}" \
    "${EXTRA[@]}"; then
    OK=$((OK + 1))
  else
    FAILED=$((FAILED + 1))
    [ "${CONTINUE_ON_ERROR}" = "1" ] || exit 1
  fi
done

if [ "${RUN_BEST_EXTRA}" = "1" ] && [ "${BEST_ALGO}" != "ssi" ] && [ "${BEST_ALGO}" != "nominal" ] && [ "${BEST_ALGO}" != "gpmpc" ]; then
  echo "==== BEST ${BEST_ALGO} | ${TRAJ} | v=${V_MAX} ===="
  EXTRA=()
  [ "${BEST_ALGO}" = "gpmpc" ] && EXTRA=(--gp-model-version "${GP_VERSION}" --gp-model-name "${GP_NAME}")
  [ "${BEST_ALGO}" = "rdrv" ] && EXTRA=(--rdrv-model-version "${RDRV_VERSION:-${GP_VERSION}}" --rdrv-model-name "${RDRV_NAME:-gazebo_sim_rdrv}")
  python3 "${SCRIPT_DIR}/run_single_trial.py" \
    --algorithm "${BEST_ALGO}" --trajectory "${TRAJ}" --v-max "${V_MAX}" --trial 1 \
    --skip-gazebo-check "${RESUME_ARGS[@]}" "${EXTRA[@]}" || FAILED=$((FAILED + 1))
fi

python3 "${SCRIPT_DIR}/plot_zyy_compare.py" --v-max "${V_MAX}"
echo "[done] ZYY benchmark ok=${OK} failed=${FAILED}"
echo "See: data/results/zyy_compare_v${V_MAX}.png"
