# GSPO（组序列策略优化，Group Sequence Policy Optimization）

> 后训练 RL 面试高频。源自 Qwen Team（2025-07），是 Qwen3 系列 RL 训练的算法基石。前置：理解 [[9_grpo]]（GRPO）、[[14_ppo]]（PPO）、重要性采样。

## 概述

GSPO 是 **GRPO 的直接改进版**，核心贡献一句话：**把重要性比率与裁剪从 token 级搬到序列级（sequence-level）**。

它解决 GRPO 在**超大模型 / 长回复 / MoE 场景**下的最大痛点——**token 级重要性权重带来高方差噪声，长序列上不断累积，最终导致灾难性且不可逆的模型崩溃（model collapse）**。

三大优势：
1. **训练更稳定、更高效**（相同算力下奖励与基准分数都更高）；
2. **天然稳定 MoE 的 RL 训练**，免除 GRPO 必须的 Routing Replay 补丁；
3. **简化 RL 基础设施**——序列级似然对训练/推理引擎的精度差异容忍度高，可直接用推理引擎返回的似然优化。

## 动机：GRPO 为什么会崩（核心）

### 1. 重要性采样被误用

重要性采样的原理是：用行为分布 $\pi_{beh}$ 的样本重新加权，估计目标分布 $\pi_{tar}$ 下的期望：

$$\mathbb{E}_{z\sim\pi_{tar}}[f(z)] = \mathbb{E}_{z\sim\pi_{beh}}\left[\frac{\pi_{tar}(z)}{\pi_{beh}(z)}f(z)\right]$$

**关键前提**：需要对**多个样本（$N\gg 1$）求平均**，重要性权重才能起到分布校正作用。

而 GRPO 在**每个 token 位置**施加权重 $w_{i,t}=\dfrac{\pi_\theta(y_{i,t}\mid x,y_{i,<t})}{\pi_{\theta_{old}}(y_{i,t}\mid x,y_{i,<t})}$，这个权重只基于该 next-token 分布上的**单个样本** $y_{i,t}$。**单样本无法完成分布校正**，反而向梯度注入高方差噪声 → 长序列上累积 → 被 clip 放大 → 模型崩溃（一旦崩溃，回退 checkpoint、调超参、换 query 都救不回来）。

### 2. 核心原则：优化的单位应与奖励的单位匹配

奖励 $r(x,y)$ 是**授予整个序列**的。既然如此，off-policy 校正也应在**序列级**进行，而不是拆到 token 级。这就是 GSPO 的出发点。

## 核心原理与公式

### 1. 序列级重要性比率（GSPO 的灵魂）

$$s_i(\theta) = \left(\frac{\pi_\theta(y_i\mid x)}{\pi_{\theta_{old}}(y_i\mid x)}\right)^{\frac{1}{|y_i|}} = \exp\left(\frac{1}{|y_i|}\sum_{t=1}^{|y_i|}\log\frac{\pi_\theta(y_{i,t}\mid x,y_{i,<t})}{\pi_{\theta_{old}}(y_{i,t}\mid x,y_{i,<t})}\right)$$

**两个关键设计**：
- 用整条回复的序列似然比，反映回复 $y$ 从 $\pi_{\theta_{old}}$ 偏离到 $\pi_\theta$ 的整体程度，天然对齐序列级奖励；
- **长度归一化**（$\frac{1}{|y_i|}$ 次方）：把不同长度回复的比率拉回统一数值范围、降低方差。否则少数几个 token 的似然变化就会让序列比率剧烈波动，且不同长度需要不同 clip 范围。

### 2. 目标函数

$$\mathcal{J}_{GSPO}(\theta) = \mathbb{E}_{x\sim\mathcal{D},\,\{y_i\}_{i=1}^G\sim\pi_{\theta_{old}}}\left[\frac{1}{G}\sum_{i=1}^G \min\left(s_i(\theta)\hat{A}_i,\ \mathrm{clip}(s_i(\theta),1-\varepsilon,1+\varepsilon)\hat{A}_i\right)\right]$$

优势沿用 GRPO 的组内归一化：

$$\hat{A}_i = \frac{r(x,y_i)-\mathrm{mean}(\{r(x,y_i)\}_{i=1}^G)}{\mathrm{std}(\{r(x,y_i)\}_{i=1}^G)}$$

注意：clip 施加在**整个回复**上（一条回复要么整条保留、要么整条裁掉）；且由于比率定义不同，GSPO 的 clip 范围与 GRPO **相差几个数量级**（论文中 GSPO 用 3e-4/4e-4，GRPO 用 0.2/0.27）。

### 3. GSPO-token 变体（多轮 RL 用）

当需要**逐 token 定制 advantage**（如 multi-turn RL）时，引入用 stop-gradient（`detach`）技巧构造的变体：

$$s_{i,t}(\theta) = \mathrm{sg}[s_i(\theta)]\cdot\frac{\pi_\theta(y_{i,t}\mid x,y_{i,<t})}{\mathrm{sg}[\pi_\theta(y_{i,t}\mid x,y_{i,<t})]}$$

由于第二项数值恒为 1，$s_{i,t}$ 在**数值上等于** $s_i$。当所有 token 的 advantage 设为同一值（$\hat{A}_{i,t}=\hat{A}_i$）时，**GSPO-token 与 GSPO 在目标、clip 条件、梯度上完全等价**，但额外获得逐 token 调 advantage 的灵活性。

## 与 GRPO 的本质区别（面试重点）

梯度视角看，两者区别在于**如何对每个 token 的对数似然梯度加权**：

| 维度 | GRPO | GSPO |
|------|------|------|
| 重要性比率单位 | **token 级** $w_{i,t}$ | **序列级** $s_i$（+长度归一化） |
| 每个 token 的权重 | 各不相同（$w_{i,t}$ 波动大） | **一条回复内所有 token 权重相同** |
| clip 对象 | 单个 token | 整条回复 |
| 噪声来源 | 单样本比率累积 → 高方差 → 崩溃 | 序列似然稳定，消除该不稳定源 |
| MoE 是否需 Routing Replay | **需要**（否则不收敛） | **不需要** |
| 训练/推理精度差异容忍度 | 低（需训练引擎重算似然） | 高（可直接用推理引擎似然） |

一句话：**GRPO 给每个 token 不同权重、噪声累积会崩；GSPO 给整条回复统一权重、稳定。**

## 反直觉现象：裁剪更多，效率反而更高

实验中 GSPO 裁掉的 token 比例（约 **0.15**）比 GRPO（约 **0.0013**）高**两个数量级**——GSPO 用于梯度估计的 token 更少，训练效率却更高。这反过来证明：**GRPO 的 token 级梯度本身噪声大、样本利用率低**，而 GSPO 的序列级信号更可靠。

## 为什么天然稳定 MoE（与后训练强相关）

MoE 的**稀疏激活**导致「专家激活波动性」：一次梯度更新后，同一回复在新策略 $\pi_\theta$ 下激活的专家可能有约 **10%** 与旧策略 $\pi_{\theta_{old}}$ 不同（层越深越严重）。这让 token 级比率 $w_{i,t}$ 剧烈波动、彻底失效。

- **GRPO 的补丁**：Routing Replay——缓存 $\pi_{\theta_{old}}$ 的激活专家，在算 $\pi_\theta$ 时"重放"同一路由。缺点是额外显存/通信开销、限制 MoE 实际容量。
- **GSPO 的解法**：只看**序列似然** $\pi_\theta(y_i\mid x)$，对单 token 似然不敏感。只要模型整体语言建模能力在，序列似然就不会剧烈波动 → 从根本上免除 Routing Replay。

## 在大模型中的应用

- **Qwen3 系列**：GSPO 是其大规模 RL 训练的算法基石，直接贡献了 Qwen3 的性能提升。
- 适用于**长 CoT 推理 RL**（数学、代码等长回复任务）、**MoE 模型 RL**、**partial rollout / multi-turn RL / 训练-推理分离框架**。

## 参考文献

- Zheng et al., *Group Sequence Policy Optimization*, arXiv:2507.18071, Qwen Team, 2025.
- Shao et al., *DeepSeekMath*（GRPO 出处）, arXiv:2402.03300, 2024.
- Zheng et al., *Click: Controllable text generation with sequence likelihood contrastive learning*, ACL Findings 2023（序列似然重要性比率来源）.
