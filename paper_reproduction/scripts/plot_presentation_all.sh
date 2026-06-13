#!/usr/bin/env bash
# Generate all presentation-ready figures from archived benchmark data.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/env_setup.sh"

GP_VERSION="${GP_VERSION:-e0d4afb}"
V_MAX="${V_MAX:-10.0}"
RESULTS="${PAPER_REPRO_DATA}/results"

echo "=== 期末展示图批量生成 ==="
echo "REPRO_DIR=${PAPER_REPRO_DIR}  GP_VERSION=${GP_VERSION}  v_max=${V_MAX}"

python3 "${SCRIPT_DIR}/summarize_results.py" \
  --output "${RESULTS}/fig6_summary.csv"

python3 "${SCRIPT_DIR}/summarize_results.py" \
  --output "${RESULTS}/tuning_summary.csv"

python3 "${SCRIPT_DIR}/pick_best_algorithm.py" --v-max "${V_MAX}"

echo "--- 论文 Fig.5–7 + 补充图 ---"
python3 "${SCRIPT_DIR}/plot_figures.py" --fig all --v-max-fig7 "${V_MAX}" --gp-version "${GP_VERSION}"

echo "--- 调参对比 ---"
python3 "${SCRIPT_DIR}/plot_tuning_compare.py" --v-max "${V_MAX}"
python3 "${SCRIPT_DIR}/plot_tuning_heatmap.py" --v-max "${V_MAX}"

echo "--- ZYY 字母轨迹 ---"
python3 "${SCRIPT_DIR}/plot_letter_zyy_traj.py" --algorithm ssi --v-max "${V_MAX}" --trial 1
python3 "${SCRIPT_DIR}/plot_zyy_compare.py" --v-max "${V_MAX}" || true

echo "--- GP 训练可视化 ---"
python3 "${SCRIPT_DIR}/plot_gp_training_cn.py" \
  --model-version "${GP_VERSION}" \
  --save-dir "${RESULTS}/gp_training" \
  --grid-x 7 8 9 || echo "[warn] GP training plots skipped"

echo ""
echo "[done] 输出目录: ${RESULTS}/"
echo "  论文复现: fig5_*.png fig6_*.png fig7_* track3d_* ref_timeseries_*"
echo "  调参:     tuning_compare_v${V_MAX}.png tuning_heatmap_v${V_MAX}.png"
echo "  字母:     letter_zyy_*.png zyy_compare_v${V_MAX}.png"
echo "  GP:       gp_training/"
ls -1 "${RESULTS}"/*.png 2>/dev/null | wc -l | xargs -I{} echo "  PNG 总数: {}"
