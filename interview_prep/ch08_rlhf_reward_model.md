# ch08 — RLHF 全景与奖励模型

> RLHF 三段式流程 + 奖励模型训练是后训练工程师的核心知识，reward hacking 是高频追问。

---

## Q1 ⭐ RLHF 的完整流程？
三个阶段：
1. **SFT**：在高质量指令数据上监督微调，得到 SFT 模型。
2. **奖励模型训练（RM）**：收集人类偏好数据（同一 prompt 的两个回复，标注哪个更好），用 Bradley-Terry 模型训练 RM。
3. **RL 优化**：用 PPO 等算法，以 RM 分数为奖励，优化 SFT 模型，同时加 KL 惩罚防止偏离太远。

---

## Q2 ⭐ 奖励模型（RM）怎么训练？Bradley-Terry 模型是什么？
**数据格式**：同一 prompt 下，人类标注 `(y_w, y_l)`（y_w 更好，y_l 更差）。

**Bradley-Terry 模型**：假设偏好概率为：
```
P(y_w > y_l) = σ(r(x, y_w) - r(x, y_l))
```
其中 σ 是 sigmoid，r 是奖励模型打分。训练目标是最大化对数似然：
```
L = -E[log σ(r(x, y_w) - r(x, y_l))]
```

**实现**：通常在 SFT 模型基础上加一个线性头，输出标量分数，只对最后一个 token 的隐状态打分。

---

## Q3 ⭐ Reward Hacking 是什么？如何防止？
**定义**：RL 优化过程中，模型找到了让 RM 打高分但实际质量差的"捷径"（利用 RM 的漏洞）。例如：生成冗长重复的回复、特定格式触发 RM 高分、说奉承话。

**根本原因**：RM 是对真实人类偏好的不完美近似，优化 RM 分数 ≠ 优化真实质量。

**防止方法**：
1. **KL 惩罚**：`reward = r(x,y) - β·KL(π||π_ref)`，限制策略偏离 SFT 模型太远。
2. **RM 集成**：用多个 RM 取平均，减少单个 RM 的漏洞。
3. **定期人工评估**：监控 RL 训练过程中的真实质量。
4. **RLVR（可验证奖励）**：用规则/代码执行结果替代 RM，从根本上消除 hacking 空间（DeepSeek-R1 路线）。

---

## Q4 🔥 RLAIF（AI Feedback）vs RLHF？
- **RLAIF**：用强 LLM（如 GPT-4/Claude）替代人类标注偏好，大幅降低标注成本。
- **Constitutional AI（CAI）**：Anthropic 方案，先让模型根据"宪法"（原则列表）自我批评和修改回复，再用 AI 偏好数据训练 RM。
- **优点**：可扩展，成本低；**缺点**：AI 偏好可能有系统性偏差（如偏好冗长、奉承）。

---

## Q5 Process Reward Model（PRM）vs Outcome Reward Model（ORM）？
- **ORM**：只对最终答案打分（对/错），简单但信号稀疏，中间步骤无反馈。
- **PRM**：对推理链的每一步打分，提供密集过程监督信号。
- **优点**：PRM 能识别"答案对但推理错"的情况，训练信号更精准；**缺点**：标注成本高（需要逐步标注）。
- **应用**：数学/代码推理任务中 PRM 效果更好；DeepSeek-R1 用 RLVR（规则奖励）替代 PRM，避免标注成本。

---

## 一句话速记
- RLHF：SFT → RM（Bradley-Terry）→ PPO+KL 惩罚。
- Reward hacking：RM 被利用，KL 惩罚 + RLVR 是主要防御。
- PRM：逐步打分，信号密集，适合推理任务但标注贵。
