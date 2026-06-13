#!/usr/bin/env bash
# Re-arm hummingbird autopilot between batch trials.
set -euo pipefail

QUAD="${QUAD_NAME:-hummingbird}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

echo "[rearm] publishing /${QUAD}/bridge/arm true"
rostopic pub -1 "/${QUAD}/bridge/arm" std_msgs/Bool "{data: true}" >/dev/null
sleep 1
echo "[rearm] done"
