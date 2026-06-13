#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

echo "[check] roscore reachable?"
if ! rostopic list >/dev/null 2>&1; then
  echo "[fail] ROS master not running. Start roscore or launch Gazebo first."
  exit 1
fi

echo "[check] ros_mpc package"
if ! rospack find ros_mpc >/dev/null 2>&1; then
  echo "[fail] ros_mpc not found in ROS_PACKAGE_PATH"
  exit 1
fi

echo "[check] paper_reproduction package"
if ! rospack find paper_reproduction >/dev/null 2>&1; then
  echo "[fail] paper_reproduction not found. Run: cd ${WS_ROOT} && catkin_make --pkg paper_reproduction"
  exit 1
fi

echo "[check] python interpreter"
echo "  which python3: $(command -v python3)"
python3 --version

echo "[check] python imports"
python3 - <<'PY'
import sys
sys.path.insert(0, __import__('os').environ.get('PYTHONPATH','').split(':')[0])
import casadi  # noqa: F401
import acados_template  # noqa: F401
print('casadi/acados OK')
PY

echo "[ok] environment looks ready"
