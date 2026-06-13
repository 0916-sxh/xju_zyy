# 快速上手（5 步）

## 1) 编译

```bash
cd /home/sxh/zyy_ws
catkin_make --pkg paper_reproduction
```

## 2) 终端 A：启动 Gazebo

`env_setup.sh` 会自动 `source ~/zyy/mpc_venv` 和 `devel/setup.bash`：

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/01_start_gazebo.sh
```

GUI 中点击 **Connect** → **Arm Bridge**。

## 3) 终端 B：跑一条 SSI-MPC

```bash
source /home/sxh/zyy_ws/src/paper_reproduction/scripts/env_setup.sh
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/02_run_single_trial.sh ssi circle 10.0 1
```

## 4) 对比 Nominal vs SSI（快速 demo）

```bash
bash /home/sxh/zyy_ws/src/paper_reproduction/scripts/03_run_quick_demo.sh
```

## 5) 看结果

- 日志：`data/logs/`
- 轨迹 mat：`data/mat/<algorithm>/<trajectory>/trialXX_v10.0.mat`
- RMSE 汇总：`data/results/fig6_summary.csv`

完整 Fig.6/7 流程见 `README.md`。
