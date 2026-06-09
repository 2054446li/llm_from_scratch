# GRPO（组相对策略优化，Group Relative Policy Optimization）

> 后训练 RL 面试高频核心。源自 DeepSeekMath（2024），是 DeepSeek-R1 等推理模型的 RL 基石。前置：理解 PPO / actor-critic。

## 概述

GRPO 是 **PPO 的一个变体**，专为 LLM 后训练设计。它解决 PPO 在 RLHF 场景下的最大工程痛点——**Critic（价值）模型太贵**。

核心思想一句话：**不训 Critic，对同一个问题采样一组回答，用「组内平均奖励」当基线。**

## 为什么要干掉 Critic（动机）

标准 PPO 是 actor-critic，需要同时维护两个大模型：

| 痛点 | 说明 |
|------|------|
| **显存/算力翻倍** | Value 模型通常与 Policy 模型同量级，训练时显存、算力直接 ×2 |
| **价值函数难训准** | LLM 里奖励模型一般只给**最后一个 token** 打分，导致逐 token 的价值估计很难准确 |

GRPO 的洞察：既然奖励模型本就是在「**同一问题、不同回答的两两比较**」上训练的，那就用**组内相对**的方式估计优势 —— 天然契合奖励模型的比较本质，还顺手省掉了 Critic。

## 核心原理与公式

### 1. 采样与基线

对每个问题 $q$，从旧策略 $\pi_{\theta_{old}}$ 采样一组 $G$ 个输出 $\{o_1, \dots, o_G\}$，奖励模型打分得 $\mathbf{r} = \{r_1, \dots, r_G\}$。**用这组奖励的均值/标准差做归一化**，作为优势：

$$\hat{A}_{i,t} = \tilde{r}_i = \frac{r_i - \mathrm{mean}(\mathbf{r})}{\mathrm{std}(\mathbf{r})}$$

这就是「组相对」的来源 —— 优势不靠 Value 网络估计，而是**组内排名**。回答比组里平均好 → 正优势（强化）；比平均差 → 负优势（抑制）。

### 2. 目标函数

$$\mathcal{J}_{GRPO}(\theta) = \mathbb{E}\Bigg[\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}\sum_{t=1}^{|o_i|}\min\Big(\rho_{i,t}\,\hat{A}_{i,t},\ \mathrm{clip}(\rho_{i,t},\,1-\varepsilon,\,1+\varepsilon)\,\hat{A}_{i,t}\Big) - \beta\,\mathbb{D}_{KL}\big[\pi_\theta \| \pi_{ref}\big]\Bigg]$$

其中重要性比率 $\rho_{i,t} = \dfrac{\pi_\theta(o_{i,t} \mid q, o_{i,<t})}{\pi_{\theta_{old}}(o_{i,t} \mid q, o_{i,<t})}$。

`min` + `clip` 的裁剪机制与 PPO 完全一致（限制单步更新幅度，防止策略跑飞）。**真正的区别在 $\hat{A}$ 怎么来、KL 放哪。**

### 3. KL 放进 loss，且用无偏估计

PPO 把 KL 惩罚揉进**逐 token 奖励**里；GRPO 则把 KL 散度**直接作为一项加进 loss**，避免污染优势 $\hat{A}$ 的计算。并采用一个**保证恒正的无偏估计量**（Schulman 2020）：

$$\mathbb{D}_{KL}\big[\pi_\theta \| \pi_{ref}\big] = \frac{\pi_{ref}(o_{i,t} \mid q, o_{i,<t})}{\pi_\theta(o_{i,t} \mid q, o_{i,<t})} - \log \frac{\pi_{ref}(o_{i,t} \mid q, o_{i,<t})}{\pi_\theta(o_{i,t} \mid q, o_{i,<t})} - 1$$

## 与 PPO 对比（必记三差异）

| 维度 | PPO | GRPO |
|------|-----|------|
| **基线 baseline** | Value 模型估计 | **组内平均奖励**（去 Critic） |
| **额外模型** | 需 Critic（≈Policy 大小） | **无需 Critic**，省约一半显存 |
| **KL 位置** | 加在 reward 里（逐 token 惩罚） | **直接加进 loss**，不污染优势 |
| **KL 估计** | 普通 | **无偏估计量**，恒正 |
| 裁剪机制 | min + clip | min + clip（相同） |

## 两种奖励监督粒度

- **结果监督（Outcome Supervision）**：奖励只在序列末尾，整条回答所有 token 共享同一个归一化奖励作优势。
- **过程监督（Process Supervision）**：奖励打在**每个推理步骤末尾**；某 token 的优势 = 其**后续所有步骤**归一化奖励之和：

$$\hat{A}_{i,t} = \sum_{\mathrm{index}(j)\geq t} \tilde{r}_i^{\,\mathrm{index}(j)}$$

  复杂数学题上 **过程监督 > 结果监督**（信号更细粒度、更密集）。

## 迭代式 GRPO

奖励模型会随策略漂移而**逐渐过时**。迭代式做法：用策略的新采样**持续重训奖励模型**（带 10% 历史数据的 replay），再把参考模型更新为当前策略，继续训。实验显示迭代能进一步涨点，**第一轮迭代提升最大**。

## 优势

1. **省显存/算力**：免掉与 Policy 同量级的 Value 模型，是 7B 乃至更大模型 RL 可负担的关键。
2. **契合奖励模型本质**：组内相对 ↔ 奖励模型的成对比较训练方式。
3. **工程更简单**：少一个待训模型、少一处调参（GAE 的 λ 等）。
4. **效果不打折**：DeepSeekMath-Instruct 已高分（MATH 46.8%）时，GRPO 仍能拉到 51.7%。

## 在大模型中的应用

- **DeepSeekMath**：首次提出，把开源 MATH 成绩推过 50%。
- **DeepSeek-R1 系列**：大规模推理模型 RL 的核心算法，配合规则奖励（rule-based reward）激发长链推理。
- 已成为开源社区做 **reasoning RL** 的主流选择之一，常与「可验证奖励（RLVR）」组合使用。

## 一个关键认知：RL 提升的是什么？

DeepSeekMath 实测：**RL 提升 Maj@K，但几乎不提升 Pass@K**。

含义：GRPO（及一般后训练 RL）的本质是**把已有的正确答案在输出分布里排得更靠前（对齐/分布锐化）**，而非注入新能力。模型的**能力上界由 SFT / 预训练决定**。想提上界 → 回到 SFT/预训练或更强的探索采样，而非堆 RL。详见 [[5_learning_rate_stages]] 同目录的 DeepSeekMath 阅读笔记。

## 类比记忆（考试 + 班级排名）

| 概念 | 类比 |
|---|---|
| 一组 G 个采样 | 同一道题让一个学生写 G 份答卷 |
| 奖励模型打分 | 老师给每份答卷打分 |
| 组内归一化做优势 | 不看绝对分，看**这份相对班级平均高还是低** |
| 正优势 | 高于平均 → 以后多这么写（强化） |
| 负优势 | 低于平均 → 以后少这么写（抑制） |
| 去掉 Critic | 不再单独养一个「预测这题该得几分」的老师，直接用全班平均当基准 |

## 一句话总结

GRPO = **去 Critic 的 PPO**：对每题采一组答案，用**组内平均奖励**当基线算优势，KL 放进 loss 用无偏估计。省一半显存、契合奖励模型的比较本质，是当代 reasoning RL 的基石；但它做的是**对齐/排序**，不是**能力注入**。

## 参考文献

- Shao et al., 2024. *DeepSeekMath.* arXiv:2402.03300.（GRPO 提出，公式 3–4）
- Schulman et al., 2017. *Proximal Policy Optimization.*（PPO 基础）
- Schulman, 2020. *Approximating KL Divergence.*（无偏 KL 估计量）
