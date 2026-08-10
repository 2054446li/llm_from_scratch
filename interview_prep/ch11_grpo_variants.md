# ch11 — GRPO 变体

> 2025-2026 前沿，面试加分项。核心心法：所有变体都在改 GRPO 的三个轴——① 归一化 ② 裁剪 ③ 信用分配粒度，共同敌人是熵坍缩。

---

## Q0 ⭐ 记忆框架：三个轴 + 一个共同敌人
读任何 GRPO 变体，先问它动了哪个轴：
1. **轴① 归一化方式**：去长度偏置 / 去 std 难度偏置（Dr.GRPO）
2. **轴② 裁剪策略**：阈值/粒度/软化（DAPO 的 Clip-Higher、CISPO、GMPO）
3. **轴③ 信用分配粒度**：token 级 vs 序列级（GSPO、GTPO）
- **共同敌人：熵坍缩**（entropy collapse）——策略熵快速下降，过早失去探索。

---

## Q1 ⭐🔥 DAPO 的四件套是什么？
DAPO（字节，2025）是社区标准基线，四个改进：
1. **Clip-Higher**：解耦上下裁剪阈值（ε_low / ε_high），**放宽上界**（ε_high 更大），让低概率 token 有机会被提升，**防熵坍缩**。
2. **动态采样**：过滤掉全对或全错的 prompt 组（这些组内 std=0，优势全为 0，无梯度贡献），提高样本效率。
3. **Token-level 损失**：损失按 token 平均而非按样本平均，**避免长回答被稀释**（样本级平均下，长回答的每个 token 权重被摊薄）。
4. **超长回答软惩罚 + 去 std 归一化**：对过长回答加软惩罚（防止无意义拉长），去掉 std 归一化避免难度偏置。

---

## Q2 ⭐🔥 Dr. GRPO 指出了 GRPO 的什么偏置？
Dr. GRPO（Sea AI Lab，*Understanding R1-Zero-Like Training*）指出 GRPO 的两个偏置：
1. **长度偏置**：损失除以回复长度 |o|，导致**长回答的每个 token 梯度被稀释**，模型倾向生成更长的错误回答。
2. **难度偏置**：优势除以组内 std，导致**简单题（std 小）的优势被放大**，模型过度关注简单题。

**解决**：去掉这两个归一化项（不除 |o|、不除 std），提升 token 效率。

---

## Q3 ⭐🔥 GSPO 的核心改进？为什么对 MoE 重要？
GSPO（Qwen，*Group Sequence Policy Optimization*）：把重要性采样比从 **token 级改为序列级**。
```
token 级（GRPO）：r_i,t = π_θ(y_t|...) / π_old(y_t|...)   逐 token 连乘
序列级（GSPO）：  r_i = (π_θ(y_i|x) / π_old(y_i|x))^(1/|y_i|)  整条序列一个比值
```
**为什么对 MoE 重要**🔥：MoE 模型每个 token 的路由可能不同，token 级 ratio 连乘会累积巨大方差（尤其长序列），导致训练不稳定。序列级 ratio 平滑了这个方差，**稳定 MoE 的 RL 训练**。Qwen3 采用。

---

## Q4 🔥 熵坍缩（Entropy Collapse）是什么？如何缓解？
- **现象**：RLVR 训练中，策略熵快速下降，模型过早收敛到少数确定性输出，失去探索能力，性能停滞。
- **原因**：clip 的上界限制了低概率 token 的提升，模型倾向强化已有高概率 token。
- **缓解**：
  - **Clip-Higher**（DAPO）：放宽上界，给低概率 token 提升空间。
  - **熵正则**：loss 加熵奖励项，鼓励探索。
  - **温度调整**：采样时用更高温度增加多样性。

---

## Q5 🔥 第二梯队变体速览（知道名字和一句话即可）
- **CISPO**（MiniMax-M1）：裁剪重要性采样权重本身，而非裁 token 更新，让低概率 token 也贡献梯度。
- **GMPO**（Geometric-Mean PO）：token 奖励用几何平均替代算术平均，对离群 token 更鲁棒。
- **GTPO / GRPO-S**：用熵加权给每个 token 分配不同奖励，改善长 CoT 稳定性。

---

## 一句话速记（面试只需记第一梯队 + 三轴归位法）
- DAPO：Clip-Higher + 动态采样 + token 级损失 + 去 std，防熵坍缩。
- Dr.GRPO：去长度偏置（���除|o|）+ 去难度偏置（不除 std）。
- GSPO：序列级 ratio，稳定 MoE 的 RL 训练。
- 共同敌人：熵坍缩，Clip-Higher/熵正则缓解。
