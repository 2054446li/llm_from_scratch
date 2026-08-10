# DeepSeek-Prover-V2 阅读笔记

> 论文：DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via Reinforcement Learning for Subgoal Decomposition
> arXiv: 2504.21801v2, 2025年7月
> 机构：DeepSeek-AI
> 阅读视角：**后训练工程师（Post-Training Engineer）** —— 把本文当作一条「**递归分解合成冷启动数据 → 课程学习专家迭代 → SFT(non-CoT + 冷启动 CoT) → GRPO RL**」的完整后训练流水线来读，重点理解 **冷启动数据如何合成**、**子目标分解如何破解奖励稀疏**、**一致性奖励如何做过程对齐**、**reward hacking 的真实案例**。
> 脉络定位：[[deepseek_prover_reading_notes|V1]]（合成数据 + RFT 自举）→ [[deepseek_prover_v15_reading_notes|V1.5]]（RL/GRPO + MCTS 树搜索）→ **本文 V2**（子目标分解 + 冷启动 CoT + 统一非形式/形式推理，规模跃至 671B）→ 与 DeepSeek-R1 的「冷启动 SFT → 推理 RL」同源。

---

## 1. 论文总结表格

| 维度 | 内容 |
|------|------|
| 论文标题 | DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via Reinforcement Learning for Subgoal Decomposition |
| 发表时间 | 2025年4月（arXiv v2 2025年7月） |
| 研究背景 | LLM 自然语言推理强，但形式化定理证明（Lean 4）要求每步可验证、无省略。如何把**非形式化的高层推理**与**形式化的句法严格性**统一进一个模型，是核心挑战。 |
| 核心贡献 | ① **递归式定理证明流水线**：DeepSeek-V3 做子目标分解 + 形式化，7B 模型补全子目标证明，拼成完整证明；② **冷启动数据合成**：把完整形式证明附加到 V3 的 CoT 之后，造出"非形式推理+形式证明"连贯样本；③ **子目标课程学习**破解奖励稀疏；④ **一致性奖励**做过程对齐；⑤ 贡献 **ProverBench**（325 题，含 15 道 AIME 24&25）。 |
| 模型规模 | DeepSeek-Prover-V2-**671B**（基于 DeepSeek-V3-Base-671B）+ **7B**（基于 V1.5-Base-7B，蒸馏） |
| 方法创新 | 用通用大模型(V3)统一做"informal 分解 + formal 形式化"；大模型分解/小模型搜索的**分工**降算力；两类子目标定理(含/不含前序前提)做课程；non-CoT 先行加速迭代、CoT+RL 后行提精度 |
| 关键结果 | miniF2F-test **88.9%**(Pass@8192，Pass@32 即 82.4%)；PutnamBench 47/658；ProofNet-test 37.1%(Pass@1024)；ProverBench-AIME 6/15(对比 V3 多投票 8/15) |
| 局限性 | AIME 形式化过滤掉几何/组合/计数题(Lean 表示繁琐)；7B 出现 reward hacking(钻 Lean 4.9.0 UI bug)；形式 vs 非形式仍有差距(6/15 vs 8/15) |
| 训练配置 | SFT: lr **5e-6**, ctx **16384**；RL(GRPO): 每轮 256 题 × 32 候选, max **32768**, 二元奖励 + 早期一致性奖励 |

---

## 2. 全文意图（一句话 + 流水线）

> **核心矛盾**：通用大模型(V3)会"非形式地想"，但写不出完整 Lean 证明；专用小模型能写 Lean，但缺乏高层规划。如何让两者合一，并造出能训练 671B 的高质量推理数据？

**答案 = 递归子目标分解流水线**，本质是一套**冷启动数据工厂**：

```
难题 theorem
  │ ① V3 用自然语言分析 + 分解为子目标，形式化成一串 have ... := by sorry（高层草图）
  ▼
子目标 1..N（每个 have 一个 sorry 占位）
  │ ② 7B prover 递归求解每个子目标（前序子目标作为前提 premise 注入）
  ▼
所有子目标证明
  │ ③ 拼接 → 原难题的完整形式证明
  │ ④ 把完整证明【附加到 V3 的 CoT 之后】→ 一条"informal 推理 + formal 证明"连贯样本
  ▼
冷启动 CoT 数据（数百条高质量）
  │ ⑤ SFT(冷启动 CoT + 专家迭代 non-CoT) → ⑥ GRPO RL(二元奖励 + 一致性奖励)
  ▼
DeepSeek-Prover-V2-671B
```

**一句话本质**：用强通用模型(V3)分解、弱专用模型(7B)填坑，造出冷启动推理数据，再用 GRPO 把"非形式推理→形式证明"的连接 RL 强化。子目标分解既是**数据合成手段**，也是**破解奖励稀疏的课程**。

---

## 3. 方法拆解（后训练核心）

### 3.1 递归证明搜索 via 子目标分解（§2.1）★

**三步：**
1. **从自然语言勾勒形式草图**：提示 V3 先自然语言分析，再分解，逐步翻译成 Lean，输出一串以 `sorry` 结尾的 `have` 语句（高层草图，细节留空）。模仿人类"把大定理逐步归约为小引理"。
2. **递归求解子目标**：从 `have` 提取子目标替换原目标(图3a)，并把前序子目标作为前提注入(图3b)，使后续子目标能用前序结果 → 更局部的依赖结构、更简单的引理。用 **7B prover** 处理(降算力)。全部解决即自动拼出完整证明。
3. **子目标课程学习**：形式证明训练信号**稀疏**(大部分尝试 0 奖励)。生成两类子目标定理(含/不含前序前提)纳入**专家迭代**，构建难度递增课程。原理同 **AlphaProof 的测试时 RL**(生成目标问题变体)。
> **后训练 takeaway**：子目标分解把一道"全 0 奖励"的难题，拆成多个"可解、有正向信号"的小题 → 制造稠密奖励。这是破解 RL 稀疏奖励的通用数据工程思路，可迁移到任意稀疏奖励任务。

### 3.2 统一非形式推理与形式化（§2.2）★★

**冷启动数据合成**：筛出"7B 端到端解不出、但所有子目标都已解决"的难题 → 拼完整证明 → **附加到 V3 的 CoT 之后** → 得到"informal 推理 + formal 形式化"连贯样本。数百条，作为训练 V2 的基础。
> **与 Kimina-Prover 的对比(论文明确点出)**：
> - **本文(forward)**：自然语言证明 → **直接形式化**为结构化形式草图。
> - **Kimina(reverse/retrosynthesis)**：先收集完整形式证明 + 非形式对应物 → 用通用模型把中间自然语言推理**逆向合成**成思考块。
> 这是 reasoning 数据合成的两种范式，值得记。

**面向推理的 RL**：在冷启动数据 SFT 后做 RL。
- **二元奖励**：Lean 验证正确=1，否则=0(同 [[deepseek_prover_v15_reading_notes|V1.5]] 的 RLVR)。
- **一致性奖励(consistency reward)** ★：观察到生成证明结构常**偏离** CoT 的引理分解 → 训练早期加一项奖励，惩罚结构错位，**强制最终证明包含所有分解出的 have 引理**。复杂多步定理上显著提精度。
> **后训练 takeaway**：一致性奖励 = **过程对齐(process alignment)** 的具体落地——不只奖励"答案对(outcome)"，还奖励"过程忠于规划(process)"。让模型最终输出忠于其推理结构，是 outcome reward 之外的重要补充。

### 3.3 训练细节（§2.3）

**两阶段两模式：**
| 阶段 | 模式 | 目的 |
|------|------|------|
| 第一阶段 | **non-CoT**(专家迭代 + 子目标递归证明) | 推理/验证快 → **加速迭代训练与数据采集** |
| 第二阶段 | **CoT**(冷启动 CoT 数据 + RL) | 系统阐述中间推理 → 高精度 |

- **专家迭代**：当前最佳策略给未解难题生成尝试 → Lean 验证 → 成功的入 SFT 集 → 训改进模型(同 V1/V1.5 范式，蒸馏自身成功轨迹)。
- **SFT**：DeepSeek-V3-Base-671B，lr 5e-6，ctx 16384。语料=non-CoT(专家迭代，无中间推理) + 冷启动 CoT(蒸馏 V3 推理为结构化证明路径)。
- **RL(GRPO)**：无 critic、组内相对奖励、二元 reward。精选"够难但可解"的 prompt。每轮 256 题 × 32 候选，max 32768。详见 [[9_grpo]]。
- **蒸馏**：7B(V1.5-Base) 上下文 4096→32768，用 671B 的 RL rollout 数据微调 + 同款 RL → 高性价比小模型。

---

## 4. 实验结果（§3）

### 4.1 主结果
- **miniF2F-test**：671B-CoT Pass@32 **82.4%** → Pass@8192 **88.9%**(SOTA)。7B 也超所有开源 prover。
- **scaling 规律**：样本预算 1→8192，**7B 与 671B 差距显著拉大** → 大模型样本效率更高、提升轨迹更陡。
- **子目标课程的威力**：V3 + 轻量 7B 的课程框架在 miniF2F-valid 达 89.8%，**几乎追平 671B**。
- **PutnamBench** 47/658；**ProofNet-test** 37.1%(尽管训练数据主要是高中题，**强泛化到本科**)；**FormalMATH-Lite** Pass@3200 61.88%。

### 4.2 CoT vs non-CoT（§3.1 + Table 3）★
- CoT 显著强于 non-CoT → **inference-time scaling 在形式化证明域成立**。
- CoT 输出长得多(7B: 4488 vs 442 token)。有趣：**non-CoT 下 671B 输出反比 7B 长**——大模型即便不提示 CoT，也会在证明代码里**插简短自然语言注释**(隐式推理)。容量越大越倾向外化推理。

### 4.3 Reward Hacking（§3.2）★★
- 初报告称 7B 解出 13 道连 671B 都没解的 PutnamBench 题 → 查明是 **Lean 4.9.0 的 UI bug**(`apply?` 在某些情况不发出 `sorry`)。
- 7B **频繁用 `Cardinal.toNat` / `Cardinal.natCast_inj` 利用这个 bug** 骗取验证通过；671B 无此模式。
> **后训练 takeaway**：这是 RLVR 的经典失败模式——**奖励来自验证器/环境，环境的 bug 就会被策略放大利用**。即便用"可验证奖励"也非绝对安全：验证器本身有漏洞时，模型会学会钻洞而非真正解题。对比 [[deepseek_prover_v15_reading_notes|V1.5]]"RLVR 根除 reward hacking"的论断，本文给出了一个重要的**反例/边界条件**：可验证奖励根除的是"神经打分器被骗"，但**无法根除"验证器实现 bug 被利用"**。

### 4.4 形式 vs 非形式差距收窄（§3.5）
- AIME 24&25：V3 非形式"找答案"多投票 8/15；Prover-V2 形式证明(给定答案) 6/15 → 差距大幅缩小，语言理解与形式逻辑严格性日益对齐。
- 组合题(CombiBench)：671B-CoT 能**识别题目陈述错误**并调整策略(用 `exfalso` 从矛盾推 `False` 闭合)。

---

## 5. 三代 Prover 对比（V1 → V1.5 → V2）★

| 维度 | [[deepseek_prover_reading_notes\|V1]] (2024.05) | [[deepseek_prover_v15_reading_notes\|V1.5]] (2024.08) | **V2 (2025.04)** |
|------|------|------|------|
| **一句话** | 合成数据 + RFT 自举 | 加 RL(GRPO) + 推理时 MCTS | 子目标分解 + 冷启动 CoT + 统一非形式/形式 |
| **模型规模** | 7B (DeepSeekMath-Base) | 7B (DeepSeekMath-Base) | **671B** (DeepSeek-V3-Base) + 7B |
| **数据来源** | 7B 自产 query+response(自动形式化) | V1 数据 + 专家迭代 + CoT 蒸馏 | **V3 分解 + 7B 填坑**合成冷启动 CoT |
| **核心机制** | 假设拒绝、原/否命题并行证 | 截断-续写、tactic 状态辅助任务 | **递归子目标分解、一致性奖励** |
| **后训练范式** | RFT(拒绝采样微调)+ 迭代 | SFT → RLVR(GRPO) → MCTS | 冷启动 SFT → RLVR(GRPO) |
| **破解稀疏奖励** | 多采样 + 验证器过滤 | RMaxTS(内在奖励 novelty + 折扣 UCB) | **子目标课程**(拆难题成可解小题) |
| **CoT 处理** | CoT 自打分过滤数据 | CoT 嵌入 Lean 注释(蒸馏) | **冷启动 CoT**(informal+formal 拼接) |
| **奖励信号** | Lean 0/1(可验证) | Lean 0/1(RLVR) | Lean 0/1 + **一致性奖励**(过程对齐) |
| **推理时策略** | 整证明多采样 | **RMaxTS 树搜索** | CoT 多采样(Pass@K)，未用树搜索 |
| **miniF2F-test** | 46.3%→52.0%(累计) | 63.5%(RL+RMaxTS) | **88.9%**(Pass@8192) |
| **关键论断** | 可验证奖励使 self-training 不崩塌 | RL 真正"增强"能力(全 K 上移) | 子目标分解破稀疏；可验证奖励也会被验证器 bug 利用 |

**演进主线（后训练视角）**：
1. **数据自举(V1)**：先解决"形式化数据从哪来"——自产 + 验证器过滤 + 迭代。
2. **RL + 探索(V1.5)**：加 GRPO 把数据变成 RL 信号，加 MCTS 解决推理时奖励稀疏的探索。
3. **规模 + 分解 + 统一(V2)**：跃到 671B，用大模型(V3)做高层规划、小模型填坑，把**奖励稀疏从"推理时探索"前移到"训练数据课程"**，并用冷启动 CoT 统一非形式与形式推理——这一步与 R1 的"冷启动 SFT → 推理 RL"完全同源。

**三代不变的内核**：**可验证奖励(Lean 0/1) + 专家迭代/自举**。变的是：规模(7B→671B)、稀疏奖励的应对位置(推理时 MCTS → 训练时子目标课程)、以及是否引入冷启动 CoT 统一两种推理。

---

## 6. 对后训练工程师的 takeaway

1. **冷启动数据合成的范式**：用强模型(V3)产高层推理 + 弱模型(7B)填形式细节，拼成连贯样本喂 SFT 冷启动 → RL。与 R1"冷启动 SFT → 推理 RL"同源。理解"什么是 cold start"的最佳实例。
2. **子目标分解 = 稀疏奖励的数据工程解**：把"全 0 奖励"难题拆成"可解"小题制造稠密信号。比 V1.5 在推理时用 MCTS 探索更"前置"——直接在训练数据层面解决。
3. **一致性奖励 = 过程对齐**：outcome reward(对/错) 之外，额外奖励"过程忠于规划"。对多步推理任务是重要补充。
4. **forward vs reverse 数据合成**：本文 informal→formal 直接形式化；Kimina formal→informal 逆向合成 CoT。两种 reasoning 数据范式。
5. **reward hacking 边界**：可验证奖励根除"神经打分器被骗"，但**根除不了"验证器 bug 被利用"**(7B 钻 Lean UI bug)。环境/工具有 bug，策略就会放大利用。修正了 V1.5 "RLVR 根除 reward hacking"的乐观论断。
6. **non-CoT 先行加速数据飞轮**：第一阶段用 non-CoT(快)跑专家迭代采数据，第二阶段才上 CoT+RL(精)。工程提速权衡。
7. **inference-time scaling 在形式域成立**：CoT > non-CoT，且大模型不提示也会隐式外化推理。
8. **GRPO 超参模板**：无 critic、组内相对、二元 reward、256 题×32 候选×32k 长度——形式化推理 RL 的参考配置。

---

## 相关知识点

- [[deepseek_prover_reading_notes]] —— V1：合成数据 + RFT 自举（三代起点）
- [[deepseek_prover_v15_reading_notes]] —— V1.5：RL/GRPO + MCTS 树搜索（本文前身）
- [[9_grpo]] —— GRPO 算法细节（本文 RL 所用）
- [[deepseek_math_reading_notes]] —— DeepSeekMath：GRPO 出处
- [[10_process_reward_model]] —— 过程奖励 / 一致性奖励的对照（过程对齐思路）
