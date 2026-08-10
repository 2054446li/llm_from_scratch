# 测试时扩展（Test-Time Scaling / Inference Scaling）

> 理解 o1 / R1 / DAPO 的**前提概念**：为什么要用大规模 RL 去训"长思维链"？因为目标是 test-time scaling。
> 关联：[[9_grpo]]、[[14_ppo]]、[[16_reward_model]]（Best-of-N / ORM）、[[10_process_reward_model]]（搜索用 PRM 引导）。

## 概述

**测试时扩展（test-time scaling，也叫 inference scaling / inference-time compute）**：在**不改变模型权重**的前提下，通过在**推理阶段**投入更多计算量来提升模型表现，尤其是推理（reasoning）能力。

它与传统的**训练时扩展（train-time scaling）**相对：

| 维度 | 训练时扩展 | 测试时扩展 |
|---|---|---|
| 加算力的位置 | 训练阶段 | 推理阶段 |
| 变量 | 参数量、数据量、训练算力 | 输出 token 数、采样次数、搜索宽度 |
| 权重是否改变 | 改变（训练） | **不变**（只在推理时花算力） |
| 代表 scaling law | Kaplan / Chinchilla | o1 的 test-time compute 曲线 |
| 代价 | 训练成本 | **推理成本**（延迟、KV cache） |

一句话定位：**train-time scaling 决定模型"能力上限的底座"，test-time scaling 决定"单次推理愿意花多少算力去逼近这个上限"**。

## 核心思想

传统 scaling law（train-time）：

$$
\text{性能} \propto f(N_{\text{params}},\ N_{\text{data}},\ C_{\text{train}})
$$

测试时扩展换一个轴——**固定权重，在推理时加算力**：

$$
\text{性能} \propto g(N_{\text{tokens}},\ N_{\text{samples}},\ W_{\text{search}})
$$

纯文本：`性能 ∝ 推理时花的 token 数 / 采样次数 N / 搜索宽度 W`。

## 三条主要路线

### 1. 更长的思维链（Sequential / 长 CoT）—— o1、R1 这一路

让模型"想得更久"：生成更长的推理链，中途做**自我验证（self-verification）、回溯、迭代修正（iterative refinement）**。

- 花的算力 = 更多的**输出 token**。
- DAPO 摘要即指此："inference scaling → 更长 CoT → 涌现 self-verification、iterative refinement"。
- 这是当前后训练最关注的一路——因为**长 CoT 能力需要用 RL 训出来**（见下文因果链）。

### 2. 并行采样 + 聚合（Parallel）

对同一问题采样 $N$ 条答案，再挑选/合成：

- **Best-of-N**：用 RM / verifier 给 N 条打分，选最高（见 [[16_reward_model]] §4.4，ORM 的经典用法）。
- **Self-Consistency（多数投票）**：采样多条 CoT，取最终答案的众数。

花的算力 = **采样条数 $N$**。

### 3. 搜索（Search / Tree）

在推理步骤上做 MCTS / beam search，配 **PRM（过程奖励模型，[[10_process_reward_model]]）** 在每一步打分引导搜索方向。

花的算力 = **搜索树的宽度 × 深度**。

## 与后训练的因果链（重点）

test-time scaling 是**目标能力**，reasoning RL 是**训练手段**：

```
想要 test-time scaling（模型能靠长 CoT 把问题想清楚）
  → 但基座模型不会自发"想很久"
  → 用大规模 RL（RLVR：可验证奖励 + GRPO/DAPO）激发长 CoT
  → 于是 RL 成为"激发长 CoT 推理"的核心手段
```

- DAPO 摘要首句 "Inference scaling empowers LLMs with unprecedented reasoning ability, with RL as the core technique to elicit complex reasoning" 说的正是这个因果。
- 所以 **o1 / R1 / DAPO 的本质**：不是训出一个"更聪明的权重"，而是训出一个"愿意且擅长花推理算力的策略"。

## 关键 trade-off：推理成本 ↔ 架构优化

test-time scaling 不是免费的——**长 CoT = 长序列 = 大 KV cache = 高推理成本**。这反过来推动了：

- **KV 缓存压缩 / MLA**（[[12_deepseek_v2]]）：压 KV cache 才能让长序列推理与 RL rollout 吞吐可控。
- **训练-推理一致性**：test-time scaling 依赖大量 rollout，采样效率直接决定 RL 训练成本。

即：**test-time scaling 的普及，是 MLA、KV 压缩、高效 rollout 等系统优化的直接动机之一**——架构与后训练在这里强耦合。

## 一句话总结

测试时扩展 = **不动权重、在推理阶段多花算力（更长 CoT / 更多采样 / 更宽搜索）换取更强推理**。它是 o1/R1/DAPO 的目标能力；因为基座模型不会自发长思考，才需要**大规模 RL（GRPO/DAPO）**去激发——这就是"reasoning RL"这一整条后训练路线的存在理由。

## 参考文献

- OpenAI, 2024. *Learning to Reason with LLMs (o1).*（test-time compute 曲线）
- Snell et al., 2024. *Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters.* arXiv:2408.03314.
- Wang et al., 2022. *Self-Consistency Improves Chain of Thought Reasoning.* arXiv:2203.11171.
- DeepSeek-AI, 2025. *DeepSeek-R1.* arXiv:2501.12948.（RL 激发长 CoT）
- Yu et al., 2025. *DAPO: An Open-Source LLM RL System at Scale.* arXiv:2503.14476.
