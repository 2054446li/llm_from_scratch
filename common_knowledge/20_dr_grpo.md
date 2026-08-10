# Dr. GRPO（GRPO Done Right，无偏组相对策略优化）

> 后训练 RL 面试高频。源自 *Understanding R1-Zero-Like Training: A Critical Perspective*（Sea AI Lab，COLM 2025）。核心是修掉 [[9_grpo]]（GRPO）的两个优化偏差。前置：理解 GRPO、[[14_ppo]]（PPO）、[[15_policy_gradient]]（策略梯度）。

## 概述

Dr. GRPO 是 **GRPO 的无偏（unbiased）修正版**，改动极简：**删掉 GRPO 目标里的两个归一化项**——回复长度归一化 $\frac{1}{|o_i|}$ 和逐题标准差归一化 $\mathrm{std}(\{R\})$。

一句话动机：**GRPO 的这两项引入了系统性偏差，会让模型对错误回复越写越长（伪"长 CoT 涌现"），并对不同难度题目不当加权。** 删掉后即还原了真实的 PPO/策略梯度目标，在保持推理性能的同时大幅提升 **token 效率**。

这篇论文的整体立场是**"祛魅（demystify）"**：R1-Zero 里"回复变长 = 推理能力涌现"的叙事，很大程度上是优化偏差的产物，而非纯 RL 的功劳。

## GRPO 的目标与两个偏差

GRPO 目标（省略 clip 与 KL）：

$$\mathcal{J}_{GRPO}(\theta) = \mathbb{E}\left[\frac{1}{G}\sum_{i=1}^G \textcolor{red}{\frac{1}{|o_i|}}\sum_{t=1}^{|o_i|}\left(\rho_{i,t}\,\hat{A}_{i,t}\right)\right],\quad \hat{A}_{i,t}=\frac{R(q,o_i)-\mathrm{mean}(\{R\})}{\textcolor{red}{\mathrm{std}(\{R\})}}$$

两个红色项就是偏差来源。

### 偏差 1：回复长度偏差（Response-level length bias）

源于 **除以 $|o_i|$**。每个 token 实际拿到的梯度系数是 $\hat{A}_i / |o_i|$：

- **正确回复（$\hat{A}_i>0$）**：短回复的每 token 权重更大 → 策略偏好"正确答案要简短"。
- **错误回复（$\hat{A}_i<0$）**：回复越长，$|o_i|$ 越大，每个 token 被压的力度 $|\hat{A}_i|/|o_i|$ 越小 → **长错误回复里每个 token"挨骂更轻"** → 模型在答错的题上越写越长。

**关键理解（易混点）**：整条回复的总梯度 $\sum_t \hat{A}_i/|o_i| = \hat{A}_i$ 确实与长度无关——但这正是病根。真实（无偏）策略梯度是**对 token 求和、不除长度**：

$$\nabla J = \mathbb{E}\left[\hat{A}\cdot\sum_{t=1}^{|o|}\nabla\log\pi(o_t)\right]$$

无偏梯度里长错误回复本应挨**正比于长度**的惩罚（错得越多字，罚越多）；GRPO 用 $\frac{1}{|o|}$ 把它抹成常数 $\hat{A}_i$，让长短错误回复挨一样的骂 → 相对于"应有惩罚"，越长的错误回复被打折越狠 → **偏袒长错误回复**。

### 偏差 2：问题难度偏差（Question-level difficulty bias）

源于 **除以 $\mathrm{std}(\{R(q,o_1),\dots,R(q,o_G)\})$**。标准差低的题（太简单或太难、奖励几乎全 1 或全 0）会被赋予更高权重。优势归一化本是 RL 常用技巧，但通常在**整个 batch** 上算；GRPO 的**逐题（question-level）**归一化会给不同难度题目带来不同权重，形成难度偏差。

## Dr. GRPO 的修法

**直接删掉这两项**，还原成 PPO 目标（优势 = 蒙特卡洛回报 − 无偏基线）：

$$\mathcal{J}_{\text{Dr.GRPO}}(\theta) = \mathbb{E}\left[\frac{1}{G}\sum_{i=1}^G \sum_{t=1}^{|o_i|}\left(\rho_{i,t}\,\hat{A}_{i,t}\right)\right],\quad \hat{A}_{i,t}=R(q,o_i)-\mathrm{mean}(\{R\})$$

- 去掉 $\frac{1}{|o_i|}$ → 消除长度偏差；
- 去掉 $\mathrm{std}(\{R\})$ → 消除难度偏差（优势只做去均值中心化，不做逐题方差归一化）。

**工程实现层面**（重要警示）：主流开源库（trl、OpenRLHF、verl、SimpleRL-Zero、Open-Reasoner-Zero）的 PPO loss **普遍偷偷做了长度归一化**，与 PPO 公式不符。修法是把 `masked_mean` 里的除数从"每条回复实际 token 数"换成**全局常数**（如生成预算 `MAX_TOKENS`）：

```python
# 有偏（多数开源实现）
return (tensor * mask).sum(axis=dim) / mask.sum(axis=dim)
# 无偏（Dr. GRPO）
return (tensor * mask).sum(axis=-1) / MAX_TOKENS
```

**即使算法公式无偏（如 PPO），实现也可能引入长度偏差**——用之前务必检查 loss 归一化方式。

## 效果

- **抑制错误回复变长**：GRPO 即便奖励提升放缓仍持续拉长回复；Dr. GRPO 让长度趋于平稳，且**大幅缩短错误回复长度**（缓解 overthinking）。
- **更高 token 效率**：相同/更好准确率下用更少 token。
- **SOTA**：用 Qwen2.5-Math-7B + Dr. GRPO，仅 8×A100 训练 27 小时，AIME 2024 达 **43.3%**。

## 与 GRPO / GSPO 的对比（面试重点）

| 维度 | GRPO | Dr. GRPO | [[19_gspo]] GSPO |
|------|------|----------|------|
| 长度归一化 $\frac{1}{|o|}$ | 有（引入长度偏差） | **删掉**（无偏） | 有，但作用于**重要性比率**（控方差），非 loss |
| std 归一化 | 有（难度偏差） | **删掉** | 保留组内 std 归一化优势 |
| 重要性比率单位 | token 级 | token 级 | **序列级** |
| 主要解决的问题 | — | GRPO 的优化偏差 / token 效率 | GRPO 的 token 级高方差 / 训练崩溃 / MoE 稳定 |

**关键辨析——为何 Dr. GRPO 删长度归一化、GSPO 却保留？** 两者归一化的**对象不同、目的不同**：
- Dr. GRPO 删的是 **loss 里优势加权求和的 $\frac{1}{|o|}$**，目的是**无偏性**（还原真实策略梯度）。
- GSPO 保留的是 **重要性比率 $s_i$ 里的 $\frac{1}{|y|}$ 次方**，目的是**数值稳定/控方差**（把序列比率拉进统一区间让 clip 有意义）。

两者不矛盾。这也说明"长度归一化该不该要"没有绝对答案，取决于它作用在哪个量、服务什么目的。

## 批判性看待（值得记住）

1. Dr. GRPO 的无偏性是**相对于"轨迹级 outcome reward"目标**而言的。若目标本就是"惩罚啰嗦、鼓励简洁"，长度归一化反而是合理设计——论文没讨论这个隐含前提。
2. 去偏后长正确回复的总梯度随长度线性放大 → **梯度方差上升**，这是一个 bias→variance 的转移，论文着墨不足。
3. "长度增长 = 纯偏差"略夸张：真实情况是**偏差 + 难度混杂**（难题客观上需要更长推理，论文附录也承认错误回复更长部分因为来自难题）。

## 论文其他"祛魅"结论（配套认知）

- **模板决定基座可训练性**，错配的模板会先破坏推理能力再由 RL 重建 → 对"纯 RL 巨大增益"要保守。
- **Qwen2.5 无模板反而最强**（提升约 60%），疑似预训练已用拼接问答对，近似做过 SFT。
- **Aha moment 基座就有**（含 DeepSeek-V3-Base），且自我反思与推理阶段准确率**不正相关**（附录 F 组内对照实验）。
- **领域预训练提升 RL 天花板**：给弱基座（Llama-3.2-3B）做数学继续预训练后 RL 表现显著更强。

## 参考文献

- Liu et al., *Understanding R1-Zero-Like Training: A Critical Perspective*, arXiv:2503.20783, COLM 2025.
- Shao et al., *DeepSeekMath*（GRPO 出处）, arXiv:2402.03300, 2024.
- Zheng et al., *Group Sequence Policy Optimization*（GSPO）, arXiv:2507.18071, 2025.
