# On-Policy Distillation（在线策略蒸馏）

## 概述

**On-Policy Distillation（OPD，在线策略蒸馏）** 是一种把 **强化学习（RL）的"在自己生成的轨迹上学习"** 与 **知识蒸馏（distillation）的"用教师模型提供密集监督信号"** 结合起来的后训练方法。

核心思想一句话：**让学生模型自己采样生成 rollout（on-policy），然后由一个更强的教师模型在学生走过的每一个 token 位置上给出"正确的概率分布"作为监督信号**。学生朝着教师的分布对齐，从而在自己真实会犯错的状态分布上被纠正。

它主要用于**推理能力蒸馏**（把大教师模型的推理能力压缩进小学生模型），是继 SFT 蒸馏、RL 之后的一条重要路线，Thinking Machines（Mira Murati 团队）2025 年的博客让这个概念广为人知。其奠基性的统一框架（GKD：数据分布 + 散度双维度解耦、可与 RL 结合）见 [[23_gkd]]。

## 为什么需要 OPD：两种传统方法的缺陷

要理解 OPD，先看它要解决的两个老问题：

### 1. Off-policy 蒸馏（=SFT on 教师数据）的问题：暴露偏差（exposure bias）

传统蒸馏做法是：让**教师**生成一批轨迹，学生用交叉熵去拟合这些轨迹（本质上就是在教师数据上做 SFT，可选地加上 soft-label KL）。

问题在于**训练分布 ≠ 推理分布**：
- 训练时学生看到的都是**教师生成的、高质量的**状态（context）。
- 推理时学生看到的是**自己生成的、可能已经跑偏的**状态。

一旦学生早期犯了个小错，就进入了训练时从没见过的状态，误差会**逐步累积（compounding error）**。这就是 **exposure bias（暴露偏差）**，也是模仿学习里经典的 distribution shift 问题。

### 2. RL（如 GRPO/PPO）的问题：监督信号太稀疏

RL 让学生 on-policy 采样，解决了分布不匹配。但它的奖励通常是**序列级、稀疏**的（例如整道数学题只有对/错一个标量 reward）。

- 一条几百 token 的轨迹，最后只得到 1 bit 信息（对还是错）。
- 学习效率低、方差大、需要海量 rollout。

## OPD 的核心：on-policy 状态 + 密集（per-token）监督

OPD 同时拿到两个世界的好处：

| 维度 | Off-policy 蒸馏(SFT) | RL(GRPO/PPO) | **On-policy 蒸馏** |
|------|---------------------|--------------|-------------------|
| 轨迹来自谁 | 教师 | 学生自己 | **学生自己（on-policy）** |
| 监督信号 | 密集（每 token 有标签） | 稀疏（序列级 reward） | **密集（每 token 有教师分布）** |
| 分布匹配 | ❌ 有 exposure bias | ✅ 匹配 | ✅ **匹配** |
| 信号来源 | 教师文本 | 环境奖励 | **教师的概率分布** |
| 每条轨迹信息量 | 中 | 低（~1 bit） | **高（每 token 一个分布）** |

### 训练流程

1. **学生采样**：用当前学生策略 $\pi_\theta$ 对 prompt 生成一条完整 rollout $x_{1:T}$（on-policy）。
2. **教师打分**：把这条学生轨迹喂给冻结的教师 $\pi_{teacher}$，在**每个 token 位置 $t$** 上拿到教师的下一 token 分布 $\pi_{teacher}(\cdot \mid x_{<t})$。
3. **计算逐 token 损失**：在每个位置最小化学生分布与教师分布的 **反向 KL 散度**：

$$
\mathcal{L}(\theta) = \mathbb{E}_{x \sim \pi_\theta} \left[ \sum_{t=1}^{T} D_{KL}\big(\pi_\theta(\cdot \mid x_{<t}) \,\|\, \pi_{teacher}(\cdot \mid x_{<t})\big) \right]
$$

4. **更新学生**，重复。

### 为什么用「反向 KL」

这里通常用 **reverse KL**  $D_{KL}(\pi_\theta \| \pi_{teacher})$ 而不是 forward KL：

- **Reverse KL 是 mode-seeking（寻峰）**：学生倾向于集中到教师认为最好的那几个模式上，行为更"确定"、更利于推理任务收敛，不会为了覆盖教师所有低概率尾巴而分散概率。
- 它天然与 RL 目标兼容：可以把 OPD 看成一个 **per-token reward = 教师给学生所选 token 的对数概率**（即 $\log \pi_{teacher}$）的 RL，只不过奖励是密集的、且不需要真实 label。
- 当学生完全等于教师时 KL=0，损失为 0，训练自然收敛。

## 与相关方法的关系

- **相对 SFT 蒸馏**：把"在教师轨迹上学"改成"在学生轨迹上学"，消除 exposure bias。
- **相对 GRPO/PPO**：把"稀疏的序列级环境奖励"换成"密集的、来自教师分布的 per-token 奖励"，样本效率大幅提升（Thinking Machines 报告称在数学推理蒸馏上比 RL 省 1~2 个数量级的算力）。
- **相对 DAgger（模仿学习）**：思路一脉相承——都是"在学习者自己的状态分布上，请专家给出正确动作"。OPD 相当于 token 级、用概率分布做监督的 DAgger。

## 优势

1. **训练/推理分布一致**：学生在自己真实会遇到的状态上被纠正，无暴露偏差。
2. **监督密集、样本高效**：每个 token 都有完整分布信号，远比 RL 的稀疏 reward 信息量大。
3. **无需奖励模型 / 无需标注答案**：监督来自教师分布本身，省掉了 RL 里 reward model 或可验证答案的依赖。
4. **稳定**：reverse KL 目标平滑，方差比 policy gradient 小得多。

## 局限性

1. **需要一个更强的教师**，且教师要与学生共享 tokenizer / 词表（否则 per-token 分布无法对齐）。
2. **教师推理成本高**：每条学生 rollout 都要教师做一次 forward。
3. **能力上限受教师约束**：学生很难超过教师（不同于 RL 可通过环境奖励探索出教师没有的解法）。
4. 对**教师本身有偏或有错**的领域，会把错误一并蒸馏过去。

## 在大模型中的应用

- **小模型推理蒸馏**：把大推理模型（如 R1、o1 类）的长链思维能力压进小模型，是当前"小而强推理模型"的主流路线之一。
- **RL 的替代/补充**：在有强教师时，用 OPD 替代或前置 GRPO，可以用更少算力达到相近推理能力，再用少量 RL 收尾。
- **持续对齐 / 领域适配**：让学生在目标领域自采样，教师做在线纠正，兼顾分布匹配与低成本监督。

## 与后训练的关联

OPD 本质上是一种 **post-training 技术**，处在 SFT 与 RL 之间的谱系上：它继承了 RL 的 on-policy 采样（保证 [[15_policy_gradient]] 式的分布正确性），又用教师分布替代了 [[16_reward_model]] 提供的稀疏奖励，从而在推理蒸馏场景下比 [[9_grpo]] 更高效。理解 KL 方向与估计方式可参考 [[13_unbiased_kl_estimate]]。

## 参考文献

- Thinking Machines Lab, "On-Policy Distillation" (2025).
- Agarwal et al., "On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes" (GKD, 2023).
- Ross et al., "A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning" (DAgger, 2011).
