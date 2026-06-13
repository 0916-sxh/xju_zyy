#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

bash "${SCRIPT_DIR}/wait_for_gazebo.sh" 30

ALGOS=(nominal ssi)
TRAJS=(circle wrapped_circle lemniscate wrapped_lemniscate)
SPEEDS=(2.5 5.0 7.5 10.0 12.5)
TRIALS=${TRIALS:-5}
RESUME=${RESUME:-1}
CONTINUE_ON_ERROR=${CONTINUE_ON_ERROR:-1}

RESUME_ARGS=()
if [ "${RESUME}" = "1" ]; then
  RESUME_ARGS=(--resume)
fi

echo "Fig.6 full benchmark: algorithms=${ALGOS[*]} trajectories=${TRAJS[*]} speeds=${SPEEDS[*]} trials=${TRIALS}"
echo "RESUME=${RESUME} CONTINUE_ON_ERROR=${CONTINUE_ON_ERROR}"
echo "Estimated runs: $((${#ALGOS[@]} * ${#TRAJS[@]} * ${#SPEEDS[@]} * TRIALS)) (GP-MPC not included)"

FAILED=0
SKIPPED=0
OK=0

for algo in "${ALGOS[@]}"; do
  for traj in "${TRAJS[@]}"; do
    for speed in "${SPEEDS[@]}"; do
      for trial in $(seq 1 "${TRIALS}"); do
        echo "==== ${algo} | ${traj} | v=${speed} | trial=${trial} ===="
        if python3 "${SCRIPT_DIR}/run_single_trial.py" \
          --algorithm "${algo}" \
          --trajectory "${traj}" \
          --v-max "${speed}" \
          --trial "${trial}" \
          --skip-gazebo-check \
          "${RESUME_ARGS[@]}"; then
          OK=$((OK + 1))
        else
          code=$?
          if [ "${CONTINUE_ON_ERROR}" = "1" ]; then
            echo "[warn] trial failed (exit ${code}), continuing..."
            FAILED=$((FAILED + 1))
          else
            exit "${code}"
          fi
        fi
      done
    done
  done
done

python3 "${SCRIPT_DIR}/summarize_results.py"
echo "[done] Fig.6 batch finished. ok=${OK} failed=${FAILED} (skipped trials logged as ok with --resume)"
