# ch13 — On-Policy Distillation（OPD）

> DeepSeek-V4 的后训练核心，2026 前沿加分项。理解 reverse-KL 和"分域+统一"范式。

---

## Q1 🔥 On-Policy Distillation 是什么？和离线蒸馏的区别？
- **离线蒸馏（off-policy）**：学生学习教师**采样的固定数据**（teacher forcing 在教师轨迹上）。
- **On-Policy Distillation（OPD）**：**学生自己采样**（on-policy），教师在**学生的输出分布上**打分/给 token 级监督（通常用 reverse-KL 损失）。
```
OPD 损失 ≈ E_{y~π_student}[ KL(π_student || π_teacher) ]  （在学生采样的轨迹上）
```

---

## Q2 🔥 为什么 on-policy 比离线蒸馏好？
1. **训练-推理分布一致**：学生在自己会遇到的分布上学习，避免离线蒸馏的**曝光偏差（exposure bias）**——离线蒸馏时学生只见过教师的完美轨迹，推理时一旦偏离就无法恢复。
2. **reverse-KL 的 mode-seeking 特性**：reverse-KL `KL(student||teacher)` 让学生**聚焦教师的高概率模式**，不会把概率质量摊到教师认为不可能的区域（forward-KL 是 mean-seeking，会摊平）。

---

## Q3 🔥 OPD 相比 RL 的定位？
- **信号密度**：RL 的奖励是稀疏的（序列级 0/1），OPD 的教师提供**密集的 token 级信号**（每个 token 都有教师分布监督）。
- **OPD = on-policy 采样（像 RL）+ 教师密集监督（像蒸馏）**，取两者之长：比稀疏奖励 RL 信号更密，比离线蒸馏更 on-policy。

---

## Q4 🔥 DeepSeek-V4 的"分而治之 + OPD 统一"范式？
**问题**：多领域 RL 会互相干扰——同时练数学、代码、写作，能力此消彼长（多任务 RL 的负迁移）。

**V4 方案**：
1. **分域练强**：用 SFT + GRPO 分别把各领域专家模型练到最强（数学专家、代码专家等）。
2. **OPD 统一**：用 on-policy 蒸馏把多个专家模型的能力合并进单一模型——学生采样，各领域专家教师给监督。

**为什么用 OPD 而非直接多任务 RL**：OPD 的密集信号 + on-policy 一致性，让能力融合更稳定，避免多任务 RL 的相互干扰。

---

## Q5 🔥 GKD 是什么？和 OPD 的关系？
- **GKD（Generalized Knowledge Distillation，Agarwal ICLR 2024）**：OPD 的理论框架，统一了 on-policy / off-policy 数据的插值，以及多种散度（forward-KL、reverse-KL、JSD）的选择。
- OPD 是 GKD 在 on-policy + reverse-KL 设定下的特例。
- **MiniLLM**：首次为 LLM 形式化 reverse-KL 的 OPD。

---

## 一句话速记
- OPD：学生自己采样，教师在学生分布上给密集 token 级监督（reverse-KL）。
- 优于离线蒸馏：避免曝光偏差 + reverse-KL mode-seeking。
- 优于稀疏 RL：信号更密集。
- V4 范式：分域 SFT+GRPO 练强 → OPD 蒸馏统一，避免多任务负迁移。
