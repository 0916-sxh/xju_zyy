# SSI-MPC 论文仿真复现（Section V-D）

本目录是**独立复现包**，用于复现论文

> *Simultaneous System Identification and Model Predictive Control with No Dynamic Regret* (arXiv:2407.04143)

中 **Section V-D 四旋翼 Gazebo 仿真** 的主要曲线（Fig.5–7 风格）。

**不会修改** `src/SSI-MPC/` 里的任何原始代码。

---

## 能复现什么 / 不能复现什么

| 论文内容 | 是否可复现 | 说明 |
|---------|-----------|------|
| Fig.5 参考轨迹 3D 图 | ✅ | 用归档的 `.mat` 中 `ref_x` 绘制 |
| Fig.6 RMSE vs 速度 | ✅（耗时） | Nominal / SSI-MPC / GP-MPC；需批量实验 |
| Fig.7 轨迹片段 + 累积误差 | ✅（部分） | 需三种算法各跑一次；**Ours+INDI 无开源实现** |
| Fig.3–4 Cart-Pole | ❌ | 原仓库未包含 PyBullet Cart-Pole 代码 |
| Fig.9–12 硬件实验 | ❌ | 需真实飞机 + L1-MPC |

---

## 目录结构

```
paper_reproduction/
├── README.md                 # 本文档
├── QUICKSTART.md             # 最短上手流程
├── launch/                   # 复现专用 launch（含 save_data）
├── scripts/                  # 一键脚本 + Python 运行器
├── matlab/                   # 读复现数据并画图（可选 MATLAB）
├── config/generated/         # 自动生成的轨迹 yaml（运行时写入）
└── data/
    ├── mat/                  # 归档的实验 .mat
    ├── logs/                 # 每次 roslaunch 日志
    └── results/              # RMSE 汇总 CSV
```

原始 `.mat` 会先写到 `SSI-MPC/ros_mpc/benchmark/`，脚本会自动复制到 `data/mat/` 并按 trial 归档。

---

## 0. 一次性准备

### 0.1 编译复现包

```bash
cd /home/sxh/zyy_ws
catkin_make --pkg paper_reproduction
source devel/setup.bash
```

### 0.2 Python 虚拟环境 + ROS 环境（每个新终端都要 source）

`env_setup.sh` 会自动激活你的 mpc 虚拟环境 `~/zyy/mpc_venv`，并 source 工作空间：

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
```

等价于手动执行：

```bash
source ~/zyy/mpc_venv/bin/activate
cd /home/sxh/zyy_ws && source devel/setup.bash
export PYTHONPATH=$PYTHONPATH:/home/sxh/zyy_ws/src/SSI-MPC/ros_mpc
```

若 venv 不在默认路径，可临时指定：

```bash
export MPC_VENV=/your/path/to/mpc_venv
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
```

### 0.3 检查环境

```bash
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/check_env.sh
```

---

## 1. 运行仿真（三个终端）

### 终端 A：Gazebo

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/01_start_gazebo.sh
```

启动后在 RPG Quadrotor GUI 点击 **Connect** 和 **Arm Bridge**。

### 终端 B：单次实验（示例）

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh

# 参数: 算法 轨迹 速度  trial编号
# 算法: nominal | ssi | gpmpc
# 轨迹: circle | wrapped_circle | lemniscate | wrapped_lemniscate

bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/02_run_single_trial.sh ssi circle 10.0 1
```

等价 Python 命令：

```bash
python3 /home/sxh/zyy_ws/src/paper_reproduction/scripts/run_single_trial.py \
  --algorithm ssi --trajectory circle --v-max 10.0 --trial 1
```

### 终端 C（可选）：观察

```bash
rostopic echo /hummingbird/ground_truth/odometry -n 1
```

---

## 2. 快速验证（对应 README _demo）

在 Gazebo 已启动的前提下：

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/03_run_quick_demo.sh
```

会依次跑 **Nominal MPC** 与 **SSI-MPC**（circle, v=10），并生成 `data/results/fig6_summary.csv`。

期望趋势（与原仓库 README 一致）：
- Nominal RMSE ~ 0.22 m
- SSI-MPC RMSE ~ 0.05 m

单次实验结束后，脚本会自动结束 `roslaunch` 并继续下一组（原 `mpc_node` 不会自行退出，此前会导致批量脚本卡住）。

正常完成时终端应看到：
```
[INFO] ... Sending increasing speed loop trajectory
[info] waiting for trial result (timeout ...s, mat=MPC_circle_2.5.mat)...
[info] detected MPC_circle_2.5.mat, finalizing...
[info] parsed RMSE: 0.xxxxx m
==== nominal | circle | v=5.0 | trial=1 ====
```

**说明**：`Sending trajectory` 之后终端可能安静 **约 1–3 分钟**（Gazebo 50% 慢放），这是正常的。

结束时可能看到 `ROSInterruptException: ROS shutdown request` —— 这是脚本主动结束 `roslaunch` 时的**正常现象**，不是报错。

若之前 Ctrl+C 中断过，请先运行 `bash scripts/cleanup_stale_nodes.sh` 清掉残留 mpc 节点。

---

## 3. 复现 Fig.6（RMSE–速度曲线）

### 3.1 跑 Nominal + SSI-MPC 全网格（默认 5 次重复）

**重要：必须先在另一个终端启动 Gazebo，否则无人机会一直悬停不动、脚本也会卡住。**

**终端 A（保持运行）：**
```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/01_start_gazebo.sh
# GUI 中点击 Connect -> Arm Bridge
```

**终端 B（跑 benchmark）：**
```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh

# 预计 2(算法) × 4(轨迹) × 5(速度) × 5(重复) = 200 次仿真
# 每次约 3–15 分钟，总耗时很长；首次建议 TRIALS=1 试跑

export TRIALS=1   # 首次试跑
# export TRIALS=5   # 正式复现
export RESUME=1   # 断点续跑：跳过 data/mat/ 里已有的 trial
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/04_run_fig6_benchmark.sh
```

**断点续跑**：中断后直接再跑上面命令即可；已完成 12 条会自动 `[skip]`，从 `lemniscate v=5.0` 继续。单次失败不会整批退出（`CONTINUE_ON_ERROR=1`）。

每次 trial 结束应看到 `parsed RMSE` 后进入下一组；若出现 `trial timeout`，脚本已加长 lemniscate 类轨迹的超时时间。

### 3.2 训练 GP + 跑 GP-MPC

`FileNotFoundError` 表示 **还没采集训练数据**。GP 训练分两步，不能跳过第 1 步直接跑 `05_train_gp_model.sh`。

**终端 A**：Gazebo（若已在跑可跳过）

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/01_start_gazebo.sh
# GUI: Connect -> Arm Bridge
```

**终端 B — 第 1 步：采集随机轨迹数据**（约 30–90 分钟，`n_seeds=10`）

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/05a_collect_gp_dataset.sh
```

结束标志：`No more references will be received`。数据写入  
`SSI-MPC/ros_mpc/data/gazebo_dataset/train/dataset_001.csv`。

> 原仓库 README 里的 `flight_mode:=random` 对 Gazebo **无效**（只会跑 circle）。上面脚本使用 `traj_random.yaml`。

**终端 B — 第 2 步：训练 GP**（在 `mpc_venv` 里跑，约几分钟）

```bash
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/05_train_gp_model.sh
```

模型保存到 `ros_mpc/results/model_fitting/<git_hash>/gazebo_sim_gp/`。脚本末尾会打印 `<git_hash>`（你这边可能是 `e0d4afb`）。

**中文版图**（重新生成带中文图例/标题的 PNG，不修改 SSI-MPC 源码）：

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
python3 /home/sxh/zyy_ws/src/paper_reproduction/scripts/plot_gp_training_cn.py \
  --model-version e0d4afb --show --grid-x 7 8 9
```

输出：`data/figures/gp_training/`。中文显示为方块时：`sudo apt install fonts-noto-cjk`

**跑 GP-MPC trial：**

```bash
python3 /home/sxh/zyy_ws/src/paper_reproduction/scripts/run_single_trial.py \
  --algorithm gpmpc --trajectory circle --v-max 10.0 --trial 1 \
  --gp-model-version e0d4afb --gp-model-name gazebo_sim_gp --skip-gazebo-check
```

Fig.7 批量 benchmark：`bash scripts/06_run_fig7_benchmark.sh <git_hash>`

**补跑 Fig.6 GP-MPC 曲线**（nominal/ssi 已跑完后单独跑 GP，共 20 条 @ TRIALS=1）：

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
export GP_VERSION=e0d4afb
export GP_NAME=gazebo_sim_gp
export TRIALS=1
export RESUME=1
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/07_run_fig6_gpmpc_benchmark.sh
```

已有 `data/mat/gpmpc/circle/trial01_v10.0.mat` 会自动 `[skip]`。每条 GP-MPC 约 4–8 分钟。

### 3.3 汇总 + 画图

```bash
python3 /home/sxh/zyy_ws/src/paper_reproduction/scripts/summarize_results.py
python3 /home/sxh/zyy_ws/src/paper_reproduction/scripts/plot_figures.py --fig all
```

输出 PNG 在 `data/results/`（**中文图题/图例**）：

**论文主图**
- `fig5_{circle,wrapped_circle,lemniscate,wrapped_lemniscate}.png` — 3D 参考轨迹
- `fig6_plot.png` — 四轨迹 RMSE vs 速度（Nominal / SSI-MPC / GP-MPC）
- `fig7_{traj}_v10.0_xy.png` — 平面轨迹片段对比（四种轨迹）
- `fig7_{traj}_v10.0_cumerr.png` — 累积位置跟踪误差
- `fig7_{traj}_v10.0_insterr.png` — 瞬时位置跟踪误差

**补充图**
- `fig6_bar_mean.png` — 各算法平均 RMSE（全部轨迹与速度）
- `fig6_heatmap_v10.png` — v=10 m/s 时轨迹×算法 RMSE 热力图
- `ref_timeseries_{traj}_v10.0.png` — 参考轨迹状态时序（位置/四元数/速度/角速度/控制）
- `track3d_{traj}_v10.0.png` — 三算法三维实际轨迹对比

**GP 训练图**（`data/results/gp_training/`）
- `gp_test_error_e0d4afb.png` — 测试集速度预测误差
- `gp_grid_v{7,8,9}_e0d4afb.png` — vx/vy/vz GP 网格切片

可选参数：`--fig {5,6,7,extra,gp,all}`、`--v-max-fig7 10.0`

MATLAB（可选，脚本在 `matlab/`）：

```matlab
cd /home/sxh/zyy_ws/src/paper_reproduction/matlab
plot_fig6_from_records('../data/results/fig6_summary.csv')
plot_fig7_from_mat('../data/mat', 'circle', 10.0)
plot_fig5_reference_traj('../data/mat', '../data/results')
```

---

## 4. 复现 Fig.7（轨迹对比）

先确保 GP 模型已训练，然后：

```bash
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/06_run_fig7_benchmark.sh <gp_git_hash>
```

MATLAB 画图：

```matlab
cd /home/sxh/zyy_ws/src/paper_reproduction/matlab
plot_fig7_from_mat('../data/mat', 'circle', 10.0)
plot_fig7_from_mat('../data/mat', 'lemniscate', 10.0)
```

---

## 5. 复现 Fig.5（参考轨迹）

先至少跑完四种轨迹各一次 SSI-MPC（v=10），然后：

```matlab
cd /home/sxh/zyy_ws/src/paper_reproduction/matlab
plot_fig5_reference_traj('../data/mat', '../data/results')
```

---

## 6. 算法与论文参数对应

| 脚本参数 | 论文名称 | 关键参数 |
|---------|---------|---------|
| `nominal` | Nominal MPC | `n_rf=0` |
| `ssi` | Algorithm 1 (Ours) | `M=50`, `η=0.25`, Gaussian kernel σ=0.01 |
| `gpmpc` | GP-MPC | 需离线训练 GP（论文 3556 点） |
| `ssi_n100` | SSI-MPC 增强 | `M=100`, `η=0.25` |
| `ssi_n100_lr015` | SSI-MPC 增强 | `M=100`, `η=0.15`（更稳） |
| `ssi_longhorizon` | SSI-MPC 增强 | `t_horizon=2`, `n_nodes=20` |
| `rdrv` | RDRv-MPC | 线性阻力模型（Faessler 2018） |

---

## 7. 效果优先：自动调参对比

现有 60 组 benchmark 表明 **SSI-MPC（论文默认）已明显优于 GP-MPC / 名义 MPC**。若仍想继续压榨性能，在**不改 SSI-MPC 源码**的前提下，复现包提供若干增强变体并自动选最优：

```bash
# 终端 A：Gazebo
bash src/paper_reproduction/scripts/01_start_gazebo.sh

# 终端 B：训练 RDRv（无需 Gazebo，若尚未训练）
bash src/paper_reproduction/scripts/08_train_rdrv_model.sh

# 终端 B：四种轨迹 @ v=10 跑调参候选（约 20 条 trial）
source src/paper_reproduction/scripts/env_setup.sh
export GP_VERSION=e0d4afb
export RDRV_VERSION=e0d4afb   # RDRv 模型目录 hash
bash src/paper_reproduction/scripts/09_run_tuning_benchmark.sh
```

输出：
- `data/results/tuning_compare_v10.0.png` — 各算法 RMSE 柱状对比
- `data/results/best_algorithm.json` — 每条轨迹 / 全局推荐算法
- `data/mat/<algorithm>/...` — 各变体归档数据

单条试跑示例：

```bash
python3 src/paper_reproduction/scripts/run_single_trial.py \
  --algorithm ssi_n100 --trajectory circle --v-max 10.0 --trial 1
```

**当前数据结论（v=10）**：默认 `ssi` 已是最佳；`ssi_n100` / 长预测域等需 Gazebo 实测后由 `pick_best_algorithm.py` 自动更新推荐。

---

## 8. ZYY 字母轨迹（自定义展示）

在圆形/双纽线 benchmark 之外，可用 **一条连续的 Z→Y→Y 字母轨迹** 对比三种论文算法：

```bash
# 终端 A：Gazebo
bash src/paper_reproduction/scripts/01_start_gazebo.sh

# 终端 B：先 catkin 安装字母节点（只需一次）
cd ~/zyy_ws && catkin_make --pkg paper_reproduction && source devel/setup.bash

# 预览连续 ZYY 路径（无需 Gazebo）
python3 src/paper_reproduction/scripts/letter_trajectories.py
# -> data/results/letter_zyy_preview.png

# 三算法 × 一条 ZYY 轨迹 = 3 次仿真
source src/paper_reproduction/scripts/env_setup.sh
export GP_VERSION=e0d4afb
bash src/paper_reproduction/scripts/10_run_zyy_benchmark.sh
```

输出：`data/results/zyy_compare_v10.0.png`

单条试跑（推荐 **ssi**，当前最佳）：

```bash
python3 src/paper_reproduction/scripts/run_single_trial.py \
  --algorithm ssi --trajectory letter_zyy --v-max 10.0 --trial 1
```

轨迹名：`letter_zyy`（一条路径依次写 Z、Y、Y′，字母间有短过渡段）。

**中断调参 batch**：`09_run_tuning_benchmark.sh` 运行中按 `Ctrl+C` 即可；默认 `RESUME=1` 下次会跳过已归档的 trial。

---

## 9. 常见问题

**Q: roslaunch 报错找不到 `paper_reproduction`？**  
A: 运行 `catkin_make --pkg paper_reproduction && source devel/setup.bash`。

**Q: GP-MPC 无法保存 .mat？**  
A: 原 `gp_mpc_node.py` 未暴露 `save_data`；本包用 `scripts/gp_mpc_repro_node.py` 包装，不改动原文件。

**Q: GP-MPC 启动报 `gp_p, gp_a, gp_v, gp_r, trigger are free`？**  
A: CasADi 3.6+ 与 SSI-MPC GP 动力学不兼容；`gp_mpc_repro_node.py` 已内置兼容补丁。请重新 `catkin_make --pkg paper_reproduction` 后再跑 trial。

**Q: 为什么和论文数值不完全一致？**  
A: Gazebo 随机性、机器性能、仿真速度（50% physics）都会影响；趋势一致即可。正式对比请用 `TRIALS=5` 取均值/方差。

**Q: Ours + INDI 曲线？**  
A: 论文 Fig.6/7 中的 INDI 版本**未开源**，本包无法生成。

---

## 10. 与原仓库的关系

- 控制器/仿真仍调用 `ros_mpc` 原节点
- 仅新增：`launch/mpc_repro.launch`、`launch/gp_mpc_repro.launch`、Python 归档脚本
- 原始 SSI-MPC README 的 demo 命令仍然有效，本包是更系统的论文图复现流程
