# Morphology as Algorithm: Biophysical RPE Implementation

**项目简介**
本项目基于 NEURON 仿真环境，从生物物理底层验证了神经元形态学（Morphology）如何作为一种“算法”硬件，物理地计算强化学习中的**奖励预测误差（Reward Prediction Error, RPE）**。

核心机制在于利用**轴向电阻（Axial Resistance）**作为物理减法器，利用**树突钙平台电位（Dendritic Ca2+ Plateaus）**作为符合检测器，从而在不依赖数字电路的情况下实现复杂的认知功能（如顿悟、风险规避）。

## 📁 目录结构与环境

所有路径均基于项目根目录 `./` (即 `ladder/neuron`)。

### 核心文件列表
```text
.
├── cad.mod                 # 钙离子衰减机制 (NMODL)
├── ca_hva.mod              # 高阈值钙通道机制 (NMODL)
├── prepare_mod.py          # 自动生成上述 .mod 文件的脚本
├── phase1_test.py          # 阶段1：模型基础生理特性验证
├── phase2_tuning.py        # 阶段2：树突增益与符合检测参数调优
├── phase3_final.py         # 阶段3：核心物理实验集（Exp 1-7）
├── search.py               # 可塑性阈值与权重的网格搜索
├── learn.py                # 认知实验：对比 RPE Agent 与 Binary Agent
├── llama.py                # 简化的 Agent 学习循环测试
├── train/                  # 包含突触权重演化与早期实验的模块
├── requirements.txt        # Python 依赖库
└── x86_64/                 # 编译后的 NEURON 机制库 (.so 文件)
```

### 🚀 快速开始

1.  **环境配置**:
    确保已安装 Python 环境及 `requirements.txt` 中的依赖。

2.  **编译 NMODL 机制**:
    在运行任何仿真前，必须先编译离子通道机制。
    ```bash
    python prepare_mod.py  # 生成 .mod 文件
    nrnivmodl              # 编译生成 x86_64 文件夹
    ```

3.  **运行顺序**:
    建议按以下顺序复现实验结果：
    `phase1_test.py` -> `phase2_tuning.py` -> `phase3_final.py` -> `learn.py`

---

## 📄 详细文件说明

以下说明均使用相对路径。

### 1. `./prepare_mod.py`
*   **简介**: 机制生成器。
*   **功能**: 这是一个辅助脚本，用于将硬编码的 NMODL 代码写入磁盘，生成 `cad.mod` (细胞内钙离子浓度衰减动力学) 和 `ca_hva.mod` (高电压激活钙通道)。
*   **重要性**: 这是构建生物物理模型的第一步，没有这些文件，树突无法产生钙尖峰（Calcium Spike）。

### 2. `./phase1_test.py`
*   **简介**: **阶段一 - 基础生理验证**。
*   **功能**: 验证构建的 Ball-and-Stick 模型是否具有基本的电生理特性。
*   **核心逻辑**:
    *   在胞体（Soma）注入电流，检测是否能产生动作电位（AP）。
    *   检测动作电位是否能回传（Back-propagate）到树突远端。
*   **输出**: 生成 `phase1_guaranteed.png`，展示胞体和树突的电压轨迹，确保模型“是活的”。

### 3. `./phase2_tuning.py`
*   **简介**: **阶段二 - 参数调优与增益搜索**。
*   **功能**: 寻找实现“符合检测（Coincidence Detection）”所需的最佳参数组合（特别是树突 Na+ 和 Ca2+ 通道密度）。
*   **核心逻辑**:
    *   **bAP_only**: 仅胞体发放，测量树突钙浓度。
    *   **syn_only**: 仅突触输入，测量树突钙浓度。
    *   **both**: 两者结合。
    *   **目标**: 寻找一个参数空间，使得 `Both >> bAP + Syn` (超线性增益)，即只有当“预测（bAP）”与“现实（Syn）”重合时，才触发钙尖峰。
*   **输出**: 打印最佳的 `Dend_Na` 和 `Syn_W` 参数，用于后续实验。

### 4. `./phase3_final.py`
*   **简介**: **阶段三 - 物理机制综合实验 (Exp 1-7)**。
*   **功能**: 本项目的核心文件，包含了论文/报告中提及的大部分生物物理实验。
*   **包含实验**:
    1.  **Speed Tuning**: 验证树突作为物理延迟线，对特定速度（3ms 间隔）产生共振。
    2.  **Direction Selectivity**: 验证模型对 Preferred vs Null 方向的选择性（DSI）。
    3.  **Mechanism Proof**: 通过模拟 TTX（阻断钠通道）实验，证明钙平台电位依赖于 bAP 的回传。
    4.  **Jitter Robustness**: 测试模型在输入噪声（Jitter）下的鲁棒性。
    5.  **Attention**: 模拟注意力机制如何通过调节离子通道电导来改变神经元敏感度。
    6.  **TD Learning**: 模拟二级条件反射，展示突触权重如何通过反向传播实现价值预测。
    7.  **Morphological RPE**: **核心创新点**。通过电压钳实验，展示轴向电流（Axial Current）如何物理地编码 $R - V$（奖励预测误差）。
*   **输出**: 生成一系列 `exp*.png` 图表。

### 5. `./search.py`
*   **简介**: **可塑性网格搜索**。
*   **功能**: 探索突触可塑性（LTP/LTD）的稳定性区域。
*   **核心逻辑**:
    *   遍历 **初始突触权重** 和 **钙离子阈值** 两个变量。
    *   计算在给定参数下 LTP 发生的概率，生成热力图（Heatmap）。
*   **输出**: `grid_search_plasticity.png`，用于确定“Goldilocks Zone”（最佳学习区）。

### 6. `./learn.py`
*   **简介**: **认知环路实验 (Agent Loop)**。
*   **功能**: 将 NEURON 模型作为一个物理计算核心，嵌入到一个高层认知任务（猜数字规则）中。
*   **核心逻辑**:
    *   **Binary Agent**: 仅接收“对/错”数字信号。
    *   **RPE Agent (Ours)**: 接收神经元产生的模拟电压差（RPE信号）。
    *   **对比**: 证明 RPE Agent 因接收了连续的模拟信号，能在遇到巨大误差时产生“顿悟（Epiphany）”，瞬间调整策略，而 Binary Agent 容易陷入震荡。
*   **输出**: `learning_curve_rpe_agent.png` 和 `learning_curve_binary_agent.png`。

### 7. `./llama.py`
*   **简介**: **轻量级 Agent 测试**。
*   **功能**: `learn.py` 的简化版本，包含一个 `SimpleAgent` 类。
*   **用途**: 用于快速测试 NEURON 环境与 Python 逻辑的交互是否正常，或者演示最基本的 RPE 学习过程，不包含复杂的对比分析。

### 8. `./train` (代码模块)
*   **简介**: **权重演化与风险实验模块**。
*   **功能**: 这里的代码逻辑主要关注突触权重的动态演化过程。
*   **核心逻辑**:
    *   包含 `run_plasticity_experiment`: 模拟 120 次试验中，突触权重如何根据钙离子浓度动态平衡（LTP/LTD）。
    *   包含 `run_risk_aversion_experiment`: **风险规避实验**。通过在近端树突引入抑制性输入（Shunting Inhibition），物理地模拟“风险”。结果显示，在高风险环境下，神经元需要更高的“奖励”才能触发决策，从而物理地解释了风险规避行为。
*   **注意**: 这里的代码通常作为实验脚本运行，生成权重轨迹图和风险效用函数图。

---

## 📊 输出图表说明

运行上述脚本后，项目根目录下将生成以下关键结果：

*   **exp1_speed_tuning.png**: 速度调谐曲线。
*   **exp2_direction_selectivity.png**: 方向选择性对比。
*   **exp3_mechanism_proof.png**: 只有当胞体的动作电位（Prediction）回传并与树突的突触输入（Reality）重合时，才会产生非线性的钙平台电位。TTX 阻断实验证明了这一点。
*   **exp5_attention.png**
*   **exp7_morphological_rpe.png**: 轴向电流作为 RPE 的物理证据。
*   **exp5_risk_aversion.png**: 风险对神经元效用函数的影响。
*   **learning_curve_rpe_agent.png**: 顿悟时刻的学习曲线。

---

**维护者**: Nyh
**最后更新**: 2025-12-06
