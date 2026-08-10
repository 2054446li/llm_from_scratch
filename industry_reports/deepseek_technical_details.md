# DeepSeek 系列技术深度分析

> 本文系统分析 DeepSeek 全系列模型的核心技术创新和设计演进。

---

## 📋 目录

1. [DeepSeek 系列概览与演进路线](#deepseek-系列概览与演进路线)
2. [DeepSeek-V2：MLA 与 DeepSeekMoE](#deepseek-v2mla-与-deepseekMoE)
3. [DeepSeek-V3：极致效率的 MoE](#deepseek-v3极致效率的-moe)
4. [DeepSeek-R1：纯 RL 激发推理能力](#deepseek-r1纯-rl-激发推理能力)
5. [DeepSeek-Coder 系列](#deepseek-coder-系列)
6. [DeepSeek-Math 与 Prover 系列](#deepseek-math-与-prover-系列)
7. [基础设施与工程创新](#基础设施与工程创新)
8. [核心技术创新总结](#核心技术创新总结)
9. [与其他模型的对标](#与其他模型的对标)
10. [技术启示与面试准备](#技术启示与面试准备)
11. [参考信息](#参考信息)

---

## DeepSeek 系列概览与演进路线

### 模型家族全景

| 模型 | 参数量 | 激活参数 | 发布时间 | 核心定位 |
|------|--------|----------|----------|----------|
| DeepSeek-LLM (V1) | 7B / 67B | 全量（稠密） | 2024-01 | 首个基座，追赶 Llama2 |
| DeepSeekMoE | 16B / 145B | 2B / ~28B | 2024-01 | MoE 路线验证 |
| DeepSeek-Coder | 1.3B-33B | 全量 | 2024-01 | 代码专项 |
| DeepSeek-Math | 7B | 全量 | 2024-02 | 数学推理 |
| DeepSeek-V2 | 236B | 21B | 2024-05 | **MLA + MoE 里程碑** |
| DeepSeek-Prover | 7B | 全量 | 2024-05 | 形式化定理证明 |
| DeepSeek-Coder-V2 | 236B | 21B | 2024-06 | MoE 代码模型 |
| DeepSeek-V2.5 | 236B | 21B | 2024-09 | 合并 Chat + Coder |
| DeepSeek-V3 | 671B | 37B | 2024-12 | **极致效率 MoE** |
| DeepSeek-R1 | 671B | 37B | 2025-01 | **纯 RL 推理（Nature）** |
| NSA（原生稀疏注意力） | - | - | 2025-02 | **可训练稀疏注意力**（论文） |
| DeepSeek-Prover-V2 | 671B | 37B | 2025-04 | 子目标分解 RL，定理证明 SOTA |
| DeepSeek-R1-0528 | 671B | 37B | 2025-05 | R1 升级版（R2 未达预期的替代） |
| DeepSeek-V3.1 | 671B | 37B | 2025-08 | **混合思考**（DeepThink 开关） |
| DeepSeek-V3.2-Exp | 671B | 37B | 2025-09 | DSA 稀疏注意力实验版 |
| DeepSeek-OCR | 3B (MoE-A570M) | 0.57B | 2025-10 | **上下文光学压缩** |
| DeepSeekMath-V2 | 671B | 37B | 2025-11 | 数学竞赛金牌级（基于 V3.2-Exp） |
| DeepSeek-V3.2 | 671B | 37B | 2025-12 | **DSA + 可扩展 RL，比肩 GPT-5** |
| DeepSeek-V4 | 1.6T / 284B | 49B / 13B | 2026-04 | **1M 上下文** MoE 系列（混合注意力 CSA+HCA） |

### 技术路线演进

```
2024.01  V1（稠密 67B，追赶 Llama2）
   │
   ├── 同期：DeepSeekMoE（验证 MoE 路线）
   ├── 同期：Coder（代码专项）
   │
2024.02  Math（数学推理）
   │
2024.05  V2 ⭐ 里程碑：MLA + MoE → 236B/21B
   │         训练成本 -42.5%，KV 缓存 -93.3%
   │
   ├── 同期：Prover（形式化证明）
   ├── 2024.06：Coder-V2（代码能力升级）
   ├── 2024.08：Prover-V1.5（RL+MCTS）
   ├── 2024.09：V2.5（合并 Chat + Coder）
   │
2024.12  V3 ⭐ 里程碑：671B/37B，$5.576M 训练成本
   │         辅助损失无关 + MTP + FP8
   │
2025.01  R1 ⭐ 范式突破：纯 RL → 推理涌现
              GRPO，比肩 o1，发表于 Nature
   │
2025.02  NSA：原生可训练稀疏注意力（硬件对齐）
   │
2025.04  Prover-V2：子目标分解 RL，MiniF2F 88.9%
   │
2025.05  R1-0528：R1 升级（R2 推迟的过渡版本）
   │
2025.08  V3.1：混合思考模型（DeepThink 开关，为 V4 铺路）
   │
2025.09  V3.2-Exp：引入 DSA 稀疏注意力（实验版）
   │
2025.10  OCR：上下文光学压缩（视觉 token 压缩文本）
   │
2025.11  Math-V2：数学竞赛金牌级（IMO/CMO gold）
   │
2025.12  V3.2 ⭐ DSA + 可扩展 RL → 比肩 GPT-5
   │         Speciale 变体超越 GPT-5，IMO/IOI/ICPC/CMO 金牌
   │
2026.04  V4 ⭐ 里程碑：1M 上下文 MoE，混合注意力（CSA+HCA）
              V4-Pro 1.6T/49B，V4-Flash 284B/13B
              1M 上下文下 FLOPs 仅 V3.2 的 27%、KV 缓存仅 10%
```

### 核心技术路线总结

稠密模型 → MoE（稀疏计算）→ MLA+MoE（高效推理）→ 纯 RL 推理（能力涌现）→ 稀疏注意力（NSA/DSA，长上下文效率）→ 1M 超长上下文 + 混合注意力（V4，CSA+HCA）


---

## DeepSeek-V2：MLA 与 DeepSeekMoE

### 参数配置

- **总参数**：236B
- **激活参数**：21B（每 token）
- **训练数据**：8.1T tokens
- **上下文长度**：128K tokens
- **训练成本**：比 DeepSeek-67B 降低 42.5%

### Multi-head Latent Attention (MLA)

V2 最核心的创新。解决 MHA/GQA/MQA 在推理时 KV 缓存过大的问题。

**传统方案对比**：

| 方案 | KV 缓存大小 | 表达能力 |
|------|------------|---------|
| MHA | n_heads × d_head × 2 | 最强 |
| GQA | n_groups × d_head × 2 | 中等 |
| MQA | 1 × d_head × 2 | 最弱 |
| **MLA** | **d_c（低维潜向量）** | **≈ MHA** |

**MLA 核心原理**：

```
传统 MHA:
  K = W_K · h_t    →  缓存 K (高维)
  V = W_V · h_t    →  缓存 V (高维)
  缓存量 = n_heads × d_head × 2 × seq_len

MLA:
  c_t = W_DKV · h_t   →  下投影到低维潜空间
  缓存 c_t（低维）
  K = W_UK · c_t       →  按需恢复 K（上投影）
  V = W_UV · c_t       →  按需恢复 V（上投影）
  缓存量 = d_c × seq_len    （d_c << n_heads × d_head）
```

**效果**：
- KV 缓存减少 **93.3%**（相比 DeepSeek-67B）
- 推理吞吐量达 DeepSeek-67B 的 **5.76 倍**
- 表达能力接近标准 MHA（不像 MQA 那样损失质量）

**关键洞察**：KV 缓存的信息是冗余的，可以用低秩压缩而几乎不损失性能。

### DeepSeekMoE 架构

两大创新（首次在 DeepSeekMoE 论文提出，V2 中进一步应用）：

#### 1. 细粒度专家分割（Fine-grained Expert Segmentation）

```
传统 MoE: N 个大专家，激活 K 个
  例：8 个专家，激活 2 个 → 组合数 C(8,2) = 28

DeepSeekMoE: mN 个小专家，激活 mK 个
  例：64 个专家，激活 8 个 → 组合数 C(64,8) ≈ 4.4 × 10^9
```

**优势**：更细粒度的知识组合 → 更精准的路由 → 更强的专家特化。

#### 2. 共享专家隔离（Shared Expert Isolation）

```
┌───────────────────────────────────┐
│         所有 token                 │
├───────────────────────────────────┤
│  共享专家 (K_s 个，永远激活)        │ ← 通用知识
├───────────────────────────────────┤
│  路由专家 (mN 个，选 mK 个)        │ ← 专项知识
└───────────────────────────────────┘
```

**优势**：
- 共享专家处理通用知识 → 路由专家无需重复存储
- 路由专家可以更加特化 → 专业性更强
- 减少专家间的知识冗余

### 关键数字

- DeepSeekMoE 16B 性能 ≈ LLaMA2 7B（仅用 ~40% 计算）
- DeepSeekMoE 145B 性能 ≈ DeepSeek 67B（仅用 28.5% 计算）


---

## DeepSeek-V3：极致效率的 MoE

### 参数配置

- **总参数**：671B
- **激活参数**：37B（每 token）
- **架构**：MLA + DeepSeekMoE（继承 V2）
- **专家配置**：256 路由专家 + 1 共享专家（每 MoE 层）
- **训练数据**：14.8T tokens
- **训练成本**：2.788M H800 GPU hours（约 **$5.576M**）
- **训练稳定性**：全程零 loss spike，零回滚

### 创新一：辅助损失无关的负载均衡

**问题**：MoE 需要负载均衡（避免某些专家过载），传统方法用辅助损失。

```
传统方法:
  L_total = L_main + α × L_balance
  问题：L_balance 干扰主损失的梯度 → 损害模型质量

DeepSeek-V3 方法:
  为每个专家维护一个 bias 项 b_i
  路由分数 = softmax(W_router · h_t) + b_i
  
  动态调整：
  - 专家 i 使用率低 → 增大 b_i → 吸引更多 token
  - 专家 i 使用率高 → 减小 b_i → 分流 token
```

**优势**：
- 不引入额外损失 → 不干扰训练信号
- 通过 bias 实现"软"平衡 → 模型质量无损

### 创新二：多 Token 预测（Multi-token Prediction, MTP）

```
标准 NTP（Next Token Prediction）:
  输入: [t1, t2, t3, t4] → 预测: [t5]

MTP:
  输入: [t1, t2, t3, t4] → 预测: [t5, t6, t7, ...]
  每个位置同时预测后续多个 token
```

**训练优势**：
- 额外的监督信号 → 改善表示学习
- 迫使模型"看得更远" → 更好的长程依赖建模

**推理优势**：
- MTP 模块可作为投机解码的 draft model
- 预测的多个 token 用于验证 → 加速生成

### 创新三：FP8 混合精度训练

```
训练精度分配:
  主权重 (Master Weights):    FP32 / BF16
  前向计算 (Forward):          FP8
  反向计算 (Backward):         FP8
  梯度累积 (Grad Accumulation): FP32
```

**为什么 FP8 可行**：
- 线性层（占大部分计算）对精度不敏感
- 通过 loss scaling 和精细的缩放因子补偿精度损失
- 仅在必要处（如 Attention softmax）保持高精度

**效果**：
- 计算速度接近翻倍
- 内存使用大幅降低
- 使 $5.576M 训练 671B 模型成为可能

### 训练稳定性

V3 训练全程无需任何回滚：
1. **超参数迁移**：从小模型验证的 LR、batch size 等直接用于大模型
2. **模型增长初始化**：小模型权重初始化大模型
3. **确定性计算**：便于复现和排查问题

### 性能

- 超越所有开源模型（当时）
- 比肩 GPT-4o、Claude-3.5-Sonnet
- 训练成本仅为同规模模型的 1/10 量级


---

## DeepSeek-R1：纯 RL 激发推理能力

### 核心贡献

证明了大语言模型的推理能力可以**纯粹通过强化学习激发**，无需人类标注的推理过程数据。论文发表于 Nature。

### DeepSeek-R1-Zero：纯 RL 实验

**训练设置**：
- 基座：DeepSeek-V3-Base（未经 SFT）
- 方法：直接用 RL 训练（无任何 SFT 阶段）
- 奖励：仅规则奖励（数学正确性、格式合规）

**涌现行为**：

1. **"Aha Moment"**：模型在推理过程中突然意识到自己犯了错
   ```
   "Wait, I think I made a mistake. Let me reconsider..."
   ```

2. **自我验证**：自发地回头检查计算结果

3. **反思**：识别推理过程中的薄弱环节

4. **动态策略调整**：遇到困难时自动切换解题方法

5. **延长思考**：难题自动分配更多 "thinking tokens"

**意义**：这些行为从未被显式教导，完全从 RL 的试错中涌现。

### GRPO 算法（Group Relative Policy Optimization）

**与 PPO 的对比**：

```
PPO:
  需要: Policy Model + Value Model (Critic)
  Value Model 参数量 ≈ Policy Model
  GPU 内存: 2x
  优势估计: A_t = R_t - V(s_t)

GRPO:
  只需: Policy Model（无 Critic）
  GPU 内存: 1x
  优势估计: 组内相对排名
```

**GRPO 工作流程**：

```
对于每个 prompt q:
  1. 采样 G 个回答: {o_1, o_2, ..., o_G} ~ π_old(·|q)
  2. 计算每个回答的奖励: r_1, r_2, ..., r_G
  3. 组内标准化: A_i = (r_i - mean(r)) / std(r)
  4. 策略更新（带 KL 惩罚和 clip）:
     L = E[min(ratio × A, clip(ratio, 1±ε) × A)] - β × KL
```

**为什么 GRPO 有效**：
- 组内相对排名消除了 reward 的绝对值偏差
- 无需训练额外的 Value Model → 省 ~50% 内存
- 更简单、更稳定

### DeepSeek-R1 完整训练流程

```
阶段 1: 冷启动 SFT
  └─ 少量长 CoT 数据 → 教会模型"思考"的格式
      ↓
阶段 2: 推理导向 RL
  └─ GRPO + 规则奖励（数学正确性、代码执行结果）
  └─ 模型学会"如何正确推理"
      ↓
阶段 3: 拒绝采样 + SFT
  └─ 从 RL checkpoint 生成大量回答
  └─ 筛选高质量回答 → 再做一轮 SFT
  └─ 目的：稳定推理能力 + 改善格式
      ↓
阶段 4: 最终 RL
  └─ 对齐训练（有用性 + 无害性）
  └─ 确保模型安全且有帮助
```

### 蒸馏

将 R1 的推理能力蒸馏到小模型：
- DeepSeek-R1-Distill-Qwen-1.5B / 7B / 14B / 32B
- DeepSeek-R1-Distill-Llama-8B / 70B

**关键发现**：蒸馏后的小模型在推理任务上显著优于同规模直接训练的模型。

### 性能

在数学、代码、STEM 推理上**比肩 OpenAI o1**。


---

## 2025-2026 演进：稀疏注意力与可扩展 RL

> 本节补充 R1 之后（2025-02 ~ 2026-06）的全部重要工作。结合后训练方向，**重点展开 RL 相关创新**（Prover-V2 子目标分解 RL、V3.2 可扩展 RL 框架、智能体任务合成、Math-V2 自验证 RL）。

### NSA：原生稀疏注意力（2025-02，arxiv:2502.11089）

R1 之后 DeepSeek 的第一篇重要论文，主题从"推理能力"转向"长上下文效率"。

**核心问题**：标准注意力 O(L²) 复杂度，长上下文成本极高；以往稀疏注意力多在推理阶段后加，无法端到端训练。

**NSA 三大设计**：

```
动态分层稀疏策略（三条并行分支）:
  ① 压缩 (Compression)：粗粒度，把 token 块压成摘要 → 全局上下文
  ② 选择 (Selection)：细粒度，挑选最相关的 token 块 → 局部精度
  ③ 滑窗 (Sliding Window)：保留近邻 token → 局部连续性
```

**两个关键突破**：
1. **硬件对齐**：算术强度（arithmetic intensity）平衡的 kernel 设计，按 GQA 组加载 query，在 SRAM 上算 attention → 实测加速
2. **原生可训练**：端到端训练，预训练即用稀疏注意力，不损失性能

**效果**：64k 序列在解码 / 前向 / 反向全程显著加速；通用、长上下文、推理任务上**持平或超越**全注意力。这是后来 V3.2 中 **DSA** 的前身。

### DeepSeek-Prover-V2（2025-04，arxiv:2504.21801）

形式化定理证明的重大升级，**子目标分解 + RL** 是核心后训练创新。

**方法（冷启动 + RL）**：
```
① 用 DeepSeek-V3 把复杂定理递归分解为子目标 (subgoal)
② 对每个子目标生成形式化证明草图 (Lean 4)
③ 冷启动数据：把分解过程整理成"思维链 → 形式化证明"
④ RL 阶段：用子目标分解奖励 + Lean 编译器验证反馈训练
```

**关键结果**：
- DeepSeek-Prover-V2-671B 在 **MiniF2F-test 达 88.9% pass ratio**（神经定理证明 SOTA）
- PutnamBench 658 题解出 49 题
- 新增 **ProverBench**（325 道形式化题）丰富评测

**后训练启示**：把"非形式推理（直觉）"与"形式验证（编译器奖励）"通过 RL 桥接——这是 verifiable reward（RLVR）在数学领域的典型范式。

### DeepSeek-R1-0528（2025-05）

R2 原计划 2025 年 5 月发布，但因性能未达梁文锋预期而推迟，**改为对 R1 做升级**得到 R1-0528。是一次过渡性增强，非全新架构。

### DeepSeek-V3.1（2025-08）

引入 **"DeepThink" 开关**：单一模型在**思考模式 / 非思考模式**间切换（混合推理）。这一设计为 V4 的统一架构铺路——不再像 R1 那样独立出一个推理模型，而是把推理能力融进基座，按需开启。

### DeepSeek-V3.2-Exp（2025-09）与 DSA

基于 V3.1-Terminus，通过**继续训练**装上 **DeepSeek Sparse Attention (DSA)** 的实验版。

**DSA 两大组件**：
```
① 闪电索引器 (Lightning Indexer)：
   计算 query token 与每个前序 token 的 index score
   → 决定哪些 token 被选中
② 细粒度 token 选择 (Fine-grained Token Selection)：
   只对选中的 top-k token 做完整注意力
```

**复杂度**：从 O(L²) 降到 **O(Lk)**（k ≪ L，k 为选中 token 数）→ 线性。目标不是超越 V3.1，而是**在保持性能的前提下大幅提升长上下文效率**。

### DeepSeek-OCR（2025-10，arxiv:2510.18234）

标题《Contexts Optical Compression》，一个反直觉的探索：**用视觉 token 压缩文本上下文**。

**架构**：DeepEncoder（视觉编码器）+ DeepSeek3B-MoE-A570M（解码器，3B 总参/0.57B 激活）

**核心发现（光学压缩比）**：
- 文本 token 数 ≤ 视觉 token 数的 **10 倍**（压缩比 <10x）时，OCR 精度 **97%**
- 压缩比 **20x** 时精度仍约 **60%**

**意义**：为 LLM 的**长上下文压缩**和**记忆遗忘机制**提供新思路——把历史文本"渲染成图"再用少量视觉 token 表示。OmniDocBench 上仅用 100 视觉 token 超越 GOT-OCR2.0。单张 A100 每天可生成 20 万+页训练数据。

### DeepSeekMath-V2（2025-11）

基于 V3.2-Exp-Base，专攻数学，**自验证 RL** 是亮点。在多项数学竞赛达**金牌级**成绩。其技术后被并入 V3.2 正式版，使 V3.2 在证明任务上达到 IMO/CMO 金牌门槛。

### DeepSeek-V3.2（2025-12，arxiv:2512.02556）⭐

R1 之后最重要的旗舰论文（263+ 作者），主题：**在效率与推理/智能体能力间取得平衡**。

**三大突破**：

1. **DeepSeek Sparse Attention (DSA)**：唯一的架构改动（相比 V3.1-Terminus），把注意力复杂度降到线性，长上下文场景保持性能
2. **可扩展 RL 框架**：通过稳健的 RL 协议 + 扩大后训练算力，标准版 **V3.2 性能比肩 GPT-5**
3. **大规模智能体任务合成流水线 (Agentic Task Synthesis)**：系统性生成训练数据，把推理能力融入工具使用场景 → 提升泛化与指令遵循鲁棒性

**V3.2-Speciale（高算力变体）**：
- **超越 GPT-5**，推理能力比肩 Gemini-3.0-Pro
- **2025 IMO / IOI / ICPC World Final / CMO 全部金牌级**
- 融合 DeepSeekMath-V2 的技术，复杂证明任务表现突出

**后训练视角重点**：V3.2 把"可扩展 RL + 智能体任务合成"作为核心卖点——标志 DeepSeek 后训练从"激发推理"（R1）走向"**RL 扩 scale + agentic 能力**"。这是当前后训练工程的最前沿方向。

### DeepSeek-V4（2026-04，arxiv:2606.19348）⭐

标题《DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence》。2026 年新一代开源 MoE 旗舰，核心赌注：**百万 token（1M）上下文的"效率"问题**（DeepSeek 的论点：1M 上下文已不是能力问题，而是效率问题）。MIT 许可，开源权重 + 技术报告 + 参考推理实现。

| 型号 | 总参数 | 激活参数 | 上下文 | 最大输出 |
|------|--------|----------|--------|----------|
| V4-Pro | 1.6T | 49B | 1M | 384K |
| V4-Flash | 284B | 13B | 1M | 384K |

**架构三大升级**：

1. **混合注意力（Hybrid Attention）**：组合两种机制提升长上下文效率
   - **CSA（Compressed Sparse Attention，压缩稀疏注意力）**
   - **HCA（Heavily Compressed Attention，重压缩注意力）**
   - 效率（1M 上下文，Pro vs V3.2）：单 token 推理 FLOPs 仅 **27%**，KV 缓存仅 **10%** → 这是 NSA(2025-02)→DSA(V3.2)→CSA/HCA(V4) 稀疏注意力路线的延续
2. **流形约束超连接（mHC, Manifold-Constrained Hyper-Connections）**：强化残差连接，提升跨层信号传播稳定性，同时保留模型表达力
3. **Muon 优化器**：更快收敛、更稳训练

**训练**：
- **预训练**：32T+ 高质量多样 token；**FP4 + FP8 混合精度**（MoE 专家用 FP4，其余多数参数用 FP8；base 模型仅 FP8）
- **后训练（两阶段范式）★** ——与后训练方向高度相关：
  1. **领域专家独立培养**：通过 **SFT + RL（GRPO）** 分别训练各领域的专精专家
  2. **统一模型整合**：通过 **on-policy 蒸馏（on-policy distillation）**，把不同领域的能力整合进单一模型

> **后训练视角重点**：V4 后训练范式 = "**分而治之 + on-policy 蒸馏统一**"。先用 SFT+GRPO 把每个领域（数学/代码/agent 等）各自练到强，再用 on-policy 蒸馏（学生自己采样、教师在学生分布上打分/纠正）把多个专家合并为一个模型。这解决了多领域 RL 互相干扰、能力此消彼长的问题，是 [[9_grpo|GRPO]] 之后多领域能力融合的前沿做法，呼应 V3.2 的"可扩展 RL"思路并更进一步。on-policy 蒸馏比离线蒸馏更能保持学生策略一致性（训练-推理一致性），值得重点研究。

**三档推理模式（混合思考，延续 V3.1 DeepThink 思路）**：

| 模式 | 特点 | 输出格式 |
|------|------|----------|
| Non-think | 快速直觉响应 | `</think>` + 摘要 |
| Think High | 有意识的逻辑分析，慢但更准 | `<think>` 思考 `</think>` + 摘要 |
| Think Max | 推理能力推到极致 | 特殊 system prompt + `<think>` 思考 `</think>` + 摘要 |

- **`-Max` 变体**（最大推理预算）：**V4-Pro-Max** 定位最强开源模型、代码 benchmark 顶尖；**V4-Flash-Max** 推理可比肩 Pro（更大思考预算），但纯知识/复杂 agentic 任务略逊。
- 采样建议：temperature=1.0, top_p=1.0；Think Max 模式需 ≥384K 上下文窗口。
- 不提供 Jinja chat template，改用专用 `encoding_dsv4`（assistant 消息含 `reasoning_content` 字段，分离思考与最终答案）。


---

## DeepSeek-Coder 系列

### DeepSeek-Coder（2024-01，arxiv:2401.14196）

- **规模**：1.3B / 6.7B / 33B
- **训练数据**：2T tokens（87% 代码 + 13% 自然语言）
- **支持语言**：多种编程语言
- **上下文**：16K tokens
- **特点**：
  - 仓库级代码理解（Repo-level）
  - Fill-in-the-Middle 训练目标
  - 在 HumanEval 上超越 CodeLlama

### DeepSeek-Coder-V2（2024-06，arxiv:2406.11931）

- **架构**：基于 DeepSeek-V2（236B MoE，21B 激活）
- **支持语言**：338 种编程语言
- **上下文**：128K tokens
- **关键突破**：首次在开源模型中打破闭源代码模型壁垒
- **性能**：比肩 GPT-4-Turbo 的代码能力

---

## DeepSeek-Math 与 Prover 系列

### DeepSeek-Math（2024-02，arxiv:2402.03300）

- **基座**：DeepSeek-Coder 7B（数学和代码有共通性）
- **训练数据**：120B 数学相关 tokens
- **创新**：
  - 提出 GRPO（后来被 R1 采用）的早期版本
  - 自我验证 + 过程奖励模型
- **性能**：
  - MATH benchmark: 51.7%（当时开源 SOTA）
  - GSM8K: 接近 GPT-4

### DeepSeek-Prover（2024-05，arxiv:2405.14333）

- **目标**：Lean 4 形式化定理证明
- **方法**：大规模合成训练数据
- **意义**：LLM 用于形式化数学的早期探索

### DeepSeek-Prover-V1.5（2024-08，arxiv:2408.08152）

- **创新**：RL + 蒙特卡洛树搜索（MCTS）
- **方法**：
  - 将 Lean 4 编译器的反馈作为 RL 奖励
  - MCTS 引导证明搜索
- **意义**：连接了"直觉推理"和"形式化验证"

---

## 基础设施与工程创新

DeepSeek 开源了其训练/推理基础设施，工程质量极高：

| 项目 | 功能 | GitHub Stars |
|------|------|-------------|
| **FlashMLA** | 高效 MLA 推理 kernel（CUDA） | 12.7K |
| **DeepEP** | 专家并行通信库 | 9.7K |
| **DeepGEMM** | FP8 细粒度缩放矩阵乘法 kernel | 7.3K |
| **DualPipe** | 双向流水线并行（V3/R1 训练用） | 3K |
| **3FS** | AI 训练/推理专用分布式文件系统 | 9.9K |
| **EPLB** | 专家并行负载均衡器 | 1.4K |
| **smallpond** | 基于 DuckDB + 3FS 的数据处理框架 | 5K |

### FlashMLA

- 针对 MLA 的高效 CUDA kernel
- 利用 MLA 的低秩结构避免 KV 展开
- 极大加速推理

### DualPipe

- V3/R1 训练中使用的双向流水线并行
- 核心思想：计算和通信双向重叠
- 最大化 GPU 利用率

### DeepGEMM

- 针对 FP8 的高效矩阵乘法
- 细粒度缩放（fine-grained scaling）
- 支撑 V3 的 FP8 训练

---

## 核心技术创新总结

| 技术 | 首次出现 | 解决的问题 | 核心思想 |
|------|---------|-----------|----------|
| 细粒度专家分割 | DeepSeekMoE (2024-01) | 专家特化不足 | 更多更小的专家 → 更灵活的组合 |
| 共享专家隔离 | DeepSeekMoE (2024-01) | 专家知识冗余 | 通用知识集中 → 路由专家更专业 |
| MLA | V2 (2024-05) | KV 缓存过大 | 低秩压缩 KV → 缓存减 93.3% |
| 辅助损失无关负载均衡 | V3 (2024-12) | 负载均衡损害质量 | bias 动态调整 → 不干扰训练信号 |
| 多 Token 预测 (MTP) | V3 (2024-12) | 训练信号不足 | 同时预测多 token → 更好的表示 |
| FP8 训练 | V3 (2024-12) | 训练成本过高 | 低精度计算 → 成本大幅降低 |
| GRPO | R1 (2025-01) | PPO 需要 Value Model | 组内相对排名 → 无需 Critic |
| 纯 RL 推理 | R1 (2025-01) | 推理依赖标注数据 | RL 激发涌现 → 无需人类推理轨迹 |
| 原生稀疏注意力 (NSA) | NSA (2025-02) | 长上下文 O(L²) + 稀疏注意力难训练 | 分层稀疏 + 硬件对齐 → 端到端可训 |
| 子目标分解 RL | Prover-V2 (2025-04) | 复杂证明难一步到位 | 递归分解 + 编译器奖励 (RLVR) |
| DeepSeek 稀疏注意力 (DSA) | V3.2 (2025-12) | 长上下文推理成本 | 闪电索引器 + token 选择 → O(Lk) |
| 可扩展 RL + 智能体合成 | V3.2 (2025-12) | RL 难 scale、智能体能力弱 | 扩后训练算力 + agentic 任务合成 |
| 混合注意力 (CSA + HCA) | V4 (2026-04) | 1M 上下文效率瓶颈 | 压缩稀疏 + 重压缩 → FLOPs 27%、KV 10% |
| 流形约束超连接 (mHC) | V4 (2026-04) | 深层信号传播稳定性 | 强化残差连接，保表达力 |
| 两阶段后训练（专家培养+蒸馏统一） | V4 (2026-04) | 多领域 RL 互相干扰 | SFT+GRPO 分域专精 → on-policy 蒸馏合一 |
| 上下文光学压缩 | OCR (2025-10) | 长文本 token 开销 | 文本渲染成图 → 视觉 token 压缩 |


---

## 与其他模型的对标

### DeepSeek-V3 vs 顶级模型

| 维度 | DeepSeek-V3 | GPT-4o | Claude-3.5-Sonnet | Llama-3.1-405B |
|------|-------------|--------|-------------------|----------------|
| 参数量 | 671B (MoE) | 未公开 | 未公开 | 405B (稠密) |
| 激活参数 | 37B | 未公开 | 未公开 | 405B |
| 训练成本 | ~$5.6M | 未公开(>>$100M) | 未公开 | 未公开(>>$10M) |
| 推理效率 | 极高 (MLA+MoE) | 高 | 高 | 低（稠密大模型） |
| 开源 | 是 | 否 | 否 | 是 |
| 通用性能 | ≈ GPT-4o | 基准 | ≈ GPT-4o | 略低 |

### DeepSeek-R1 vs OpenAI o1

| 维度 | DeepSeek-R1 | OpenAI o1 |
|------|-------------|-----------|
| 架构 | 671B MoE + RL | 未公开 |
| 训练方法 | GRPO (无 Critic) | 未公开 (推测 PPO) |
| 数学推理 | ≈ o1 | 基准 |
| 代码推理 | ≈ o1 | 基准 |
| 开源 | 是 | 否 |
| 成本 | 极低 | 高 |
| 涌现行为 | 已验证 (R1-Zero) | 未公开细节 |

### DeepSeek-V2 MoE vs LongCat-Flash MoE

| 维度 | DeepSeek-V2 | LongCat-Flash |
|------|-------------|---------------|
| 总参数 | 236B | 560B |
| 激活参数 | 21B (固定) | 18.6B-31.3B (动态) |
| 注意力 | MLA | 标准 MHA |
| MoE 特点 | 细粒度分割+共享专家 | Zero-comp Experts+Shortcut |
| KV 缓存 | 极小 (MLA) | 标准 |
| 计算分配 | 固定 | 动态 |
| 训练数据 | 8.1T | 20T+ |

---

## 技术启示与面试准备

### 对从业者的技术启示

1. **MLA 是注意力机制的重要演进**
   - MHA → GQA → MQA 是"减少 head"的路线
   - MLA 是"压缩 KV"的路线 → 更好的性能/效率平衡

2. **MoE 的设计细节决定性能**
   - 专家粒度、共享机制、负载均衡策略各有权衡
   - DeepSeek 的"辅助损失无关"是当前最优方案

3. **RL 是释放推理能力的关键**
   - SFT 教模型"模仿推理"
   - RL 让模型"学会推理"
   - R1-Zero 证明纯 RL 即可涌现高级推理

4. **训练效率是核心竞争力**
   - V3 以 $5.6M 训练出比肩 GPT-4o 的模型
   - FP8 + MoE + 高效通信是三大支柱

### 面试准备：高频问题

1. **MLA 如何减少 KV 缓存？与 GQA/MQA 有何不同？**
   - 思路：低秩压缩 vs 减少 head 数，MLA 保持表达能力的同时大幅压缩

2. **DeepSeekMoE 的细粒度分割和共享专家有什么作用？**
   - 思路：组合灵活性 vs 计算开销，共享专家减少冗余

3. **辅助损失无关的负载均衡如何实现？为什么更好？**
   - 思路：bias 动态调整 vs 辅助损失，避免梯度干扰

4. **GRPO 与 PPO 的区别？为什么不需要 Value Model？**
   - 思路：组内相对排名替代绝对价值估计，省内存、更稳定

5. **DeepSeek-R1-Zero 涌现了哪些推理行为？为什么？**
   - 思路：Aha moment、自我验证、反思、策略切换，RL 试错 → 自然涌现

6. **多 Token 预测的训练和推理各有什么优势？**
   - 思路：训练=额外监督信号，推理=投机解码加速

7. **FP8 训练如何保证精度？哪些地方不能用 FP8？**
   - 思路：线性层可用 FP8，Softmax/归一化保持高精度，loss scaling 补偿

8. **如何用 $5.6M 训练出 671B 模型？关键节省在哪？**
   - 思路：MoE(仅 37B 激活) + FP8 + 高效并行(DualPipe) + 稳定训练(零回滚)

9. **DeepSeek 的技术路线对行业有什么启示？**
    - 思路：开源可以比肩闭源、效率创新比堆算力更重要、RL 是推理的未来


---

## 参考信息

### 完整论文列表

| # | 论文 | arXiv | 日期 |
|---|------|-------|------|
| 1 | DeepSeek LLM: Scaling Open-Source Language Models with Longtermism | https://arxiv.org/abs/2401.02954 | 2024-01 |
| 2 | DeepSeekMoE: Towards Ultimate Expert Specialization in MoE LMs | https://arxiv.org/abs/2401.06066 | 2024-01 |
| 3 | DeepSeek-Coder: When the Large Language Model Meets Programming | https://arxiv.org/abs/2401.14196 | 2024-01 |
| 4 | DeepSeek-Math: Pushing the Limits of Mathematical Reasoning | https://arxiv.org/abs/2402.03300 | 2024-02 |
| 5 | DeepSeek-V2: A Strong, Economical, and Efficient MoE LM | https://arxiv.org/abs/2405.04434 | 2024-05 |
| 6 | DeepSeek-Prover: Advancing Theorem Proving via Large-Scale Synthetic Data | https://arxiv.org/abs/2405.14333 | 2024-05 |
| 7 | DeepSeek-Coder-V2: Breaking the Barrier of Closed-Source Models in Code Intelligence | https://arxiv.org/abs/2406.11931 | 2024-06 |
| 8 | DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for RL and MCTS | https://arxiv.org/abs/2408.08152 | 2024-08 |
| 9 | DeepSeek-V3 Technical Report | https://arxiv.org/abs/2412.19437 | 2024-12 |
| 10 | DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning | https://arxiv.org/abs/2501.12948 | 2025-01 |
| 11 | Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention | https://arxiv.org/abs/2502.11089 | 2025-02 |
| 12 | DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via RL for Subgoal Decomposition | https://arxiv.org/abs/2504.21801 | 2025-04 |
| 13 | DeepSeek-OCR: Contexts Optical Compression | https://arxiv.org/abs/2510.18234 | 2025-10 |
| 14 | DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models | https://arxiv.org/abs/2512.02556 | 2025-12 |
| 15 | DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence | https://arxiv.org/abs/2606.19348 | 2026-04 |

> 注：DeepSeekMath-V2（2025-11，基于 V3.2-Exp）、DeepSeek-V3.1（2025-08）、V3.2-Exp（2025-09，DSA 实验版）、R1-0528（2025-05）主要以模型/技术博客形式发布。

### 推荐阅读顺序

#### 路线 A：理解核心演进（面试必读，5 篇）

```
① DeepSeekMoE (2401.06066)
   └─ 理解 MoE 基础：细粒度分割 + 共享专家
       ↓
② DeepSeek-V2 (2405.04434) ⭐⭐⭐
   └─ 核心突破：MLA（KV 缓存压缩 93.3%）+ 改进的 MoE
       ↓
③ DeepSeek-V3 (2412.19437) ⭐⭐⭐
   └─ 工程极致：辅助损失无关负载均衡 + MTP + FP8 + $5.576M 训练
       ↓
④ DeepSeek-R1 (2501.12948) ⭐⭐⭐
   └─ 范式突破：纯 RL 激发推理 + GRPO + 涌现行为
       ↓
⑤ R1 论文中的 R1-Zero 部分
   └─ 理解 "Aha moment" 和纯 RL 涌现
```

#### 路线 B：完整技术栈（深入研究，按主题分组）

**基座演进线**（必读）：
```
V1 (2401.02954) → MoE (2401.06066) → V2 (2405.04434) → V3 (2412.19437)
```

**推理能力线**（重点）：
```
Math (2402.03300) → Prover (2405.14333) → Prover-V1.5 (2408.08152) → R1 (2501.12948)
                 → Prover-V2 (2504.21801) → Math-V2 (2025-11) → V3.2 可扩展 RL (2512.02556)
```

**效率 / 注意力线**（长上下文）：
```
MLA (V2, 2405.04434) → NSA (2502.11089) → DSA (V3.2-Exp/V3.2, 2512.02556) → CSA+HCA (V4, 2606.19348, 1M 上下文)
```

**代码能力线**：
```
Coder (2401.14196) → Coder-V2 (2406.11931)
```

#### 路线 C：应急面试准备（2-3 天速读）

只读 3 篇：
1. **DeepSeek-V2**（arxiv:2405.04434）：理解 MLA（面试必问）
2. **DeepSeek-V3**（arxiv:2412.19437）：理解 MoE 工程优化 + 训练效率
3. **DeepSeek-R1**（arxiv:2501.12948）：理解 GRPO + 纯 RL 推理（最热话题）

### 开源资源

- **GitHub 组织**：https://github.com/deepseek-ai（34 个仓库）
- **Hugging Face**：https://huggingface.co/deepseek-ai
- **对话平台**：https://chat.deepseek.com
- **API 平台**：https://platform.deepseek.com

### 关键基础设施仓库

- FlashMLA：https://github.com/deepseek-ai/FlashMLA
- DeepEP：https://github.com/deepseek-ai/DeepEP
- DeepGEMM：https://github.com/deepseek-ai/DeepGEMM
- DualPipe：https://github.com/deepseek-ai/DualPipe
- 3FS：https://github.com/deepseek-ai/3FS
