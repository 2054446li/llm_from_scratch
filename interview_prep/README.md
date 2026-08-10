# 后训练 / LLM 面试题库（秋招速攻版）

> 目标：以**后训练工程师**视角，覆盖从 Transformer 基础到 Agentic RL 的完整面试高频题。每章「问题 → 要点答案 → 追问」结构，公式用可读纯文本，方便直接背诵与口述。
> 用法：面试前按章过一遍「一句话答案」，能复述即可；标 ⭐ 为高频必背，标 🔥 为 2025-2026 前沿加分项。

## 章节索引

### 一、LLM 通用基础（架构 & 系统）
- [ch01 — Transformer 与注意力机制](ch01_transformer_attention.md)（MHA / GQA / MQA / MLA / FlashAttention）⭐
- [ch02 — 位置编码](ch02_positional_encoding.md)（绝对/相对 / RoPE / YaRN 长度外推）
- [ch03 — 归一化与激活函数](ch03_norm_activation.md)（LayerNorm / RMSNorm / Pre-LN vs Post-LN / SwiGLU）⭐
- [ch04 — 混合专家 MoE](ch04_moe.md)（路由 / 负载均衡损失 / 共享专家 / token drop）⭐
- [ch05 — 训练系统与优化器](ch05_training_system.md)（AdamW / LR 调度 / 混合精度 / DeepSpeed-ZeRO / 3D 并行）⭐
- [ch06 — 预训练与评估](ch06_pretrain_eval.md)（tokenizer / Scaling Law / perplexity / 数据配比）

### 二、后训练主线
- [ch07 — SFT 监督微调](ch07_sft.md)（数据构造 / chat template / loss mask / 灾难性遗忘 / LoRA）⭐
- [ch08 — RLHF 全景与奖励模型](ch08_rlhf_reward_model.md)（三段式 / Bradley-Terry / reward hacking / RLAIF）⭐
- [ch09 — 策略梯度与 PPO](ch09_policy_gradient_ppo.md)（REINFORCE / TRPO / clip / GAE / actor-critic / 四模型）⭐
- [ch10 — GRPO 与 RLVR](ch10_grpo_rlvr.md)（去 Critic / 组内基线 / 可验证奖励 / DeepSeek-R1）⭐🔥
- [ch11 — GRPO 变体](ch11_grpo_variants.md)（DAPO / Dr.GRPO / GSPO / 熵坍缩）🔥
- [ch12 — DPO 系列](ch12_dpo.md)（DPO 推导 / IPO / KTO / ORPO / SimPO）⭐
- [ch13 — On-Policy Distillation](ch13_opd.md)（reverse-KL / GKD / DeepSeek-V4 分域+统一）🔥
- [ch14 — Agentic RL](ch14_agentic_rl.md)（多轮 MDP / 工具 token mask / 信用分配 / 异步 rollout）🔥

### 三、工业模型串讲
- [ch15 — DeepSeek 架构与后训练串讲](ch15_deepseek.md)（MLA / DeepSeekMoE / R1 四段式 / V3 训练）⭐🔥

### 复习追踪
- [TODO_review.md](TODO_review.md) — 未完成的知识点 & 代码复习清单（按优先级）

---

## 面试口述四大主线（贯穿所有 RL 章节，被问到任何算法都回到这四个坐标）
1. **优势估计怎么做**：Critic(PPO) / 组内均值(GRPO) / 隐式(DPO) / 长程信用分配(Agent)
2. **KL 约束放哪、怎么算**：reward 里(PPO) vs loss 里(GRPO) vs 隐式(DPO)；k1/k2/k3 估计器
3. **on-policy 还是 off-policy**：在线采样 vs 离线数据；训练-推理一致性
4. **奖励从哪来**：RM / 规则(RLVR) / 偏好对(DPO) / 教师(OPD) / 环境(Agentic RLVR)；reward hacking 如何防
