#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

# Quick sanity check matching README demo (circle, v=10)
python3 "${SCRIPT_DIR}/run_single_trial.py" --algorithm nominal --trajectory circle --v-max 10.0 --trial 1
python3 "${SCRIPT_DIR}/run_single_trial.py" --algorithm ssi --trajectory circle --v-max 10.0 --trial 1

python3 "${SCRIPT_DIR}/summarize_results.py"
echo "[done] quick demo finished. See data/results/fig6_summary.csv"
