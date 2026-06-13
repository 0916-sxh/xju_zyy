#!/usr/bin/env bash
# Wait until Gazebo + hummingbird odometry is publishing.
# Usage: bash wait_for_gazebo.sh [timeout_seconds]

set -euo pipefail

TIMEOUT="${1:-120}"
TOPIC="/hummingbird/ground_truth/odometry"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

echo "[wait_for_gazebo] waiting for ${TOPIC} (timeout ${TIMEOUT}s)"
echo "[wait_for_gazebo] make sure terminal A is running:"
echo "  bash ${SCRIPT_DIR}/01_start_gazebo.sh"
echo "[wait_for_gazebo] and RPG GUI: Connect -> Arm Bridge"

if ! rostopic list >/dev/null 2>&1; then
  echo "[fail] roscore is not running. Start Gazebo first (01_start_gazebo.sh)."
  exit 1
fi

if ! rostopic list | grep -q "^${TOPIC}$"; then
  echo "[fail] topic ${TOPIC} not found."
  echo "       Is Gazebo running? Did you click Connect in RPG Quadrotor GUI?"
  exit 1
fi

if timeout "${TIMEOUT}" rostopic echo -n 1 "${TOPIC}" >/dev/null 2>&1; then
  echo "[ok] ${TOPIC} is publishing"
  exit 0
fi

echo "[fail] no odometry received within ${TIMEOUT}s."
echo "       Check: Gazebo running, Connect + Arm Bridge clicked, hummingbird spawned."
exit 1
