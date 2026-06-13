#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

ALGO="${1:-ssi}"
TRAJ="${2:-circle}"
VMAX="${3:-10.0}"
TRIAL="${4:-1}"

python3 "${SCRIPT_DIR}/run_single_trial.py" \
  --algorithm "${ALGO}" \
  --trajectory "${TRAJ}" \
  --v-max "${VMAX}" \
  --trial "${TRIAL}"
