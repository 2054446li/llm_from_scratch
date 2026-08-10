# ch03 — 归一化与激活函数

> RMSNorm + SwiGLU 是当前主流 LLM 标配，Pre-LN 稳定性是面试必答点。

---

## Q1 ⭐ LayerNorm 的原理？为什么 LLM 用 Pre-LN 而非 Post-LN？
**LayerNorm**：对每个样本的**特征维**（d_model）做归一化，`y = (x - mean) / std * γ + β`，与 batch 无关，适合变长序列。

**Pre-LN vs Post-LN**：
- **Post-LN**（原始 Transformer）：`x = LN(x + sublayer(x))`，归一化在残差之后。训练不稳定，深层梯度消失，需要 warmup。
- **Pre-LN**（现代 LLM 主流）：`x = x + sublayer(LN(x))`，归一化在子层之前。梯度流更稳定，可用更大 LR，不需要精细 warmup。**代价**：理论上表达力略弱，但工程上稳定性收益远大于此。

**追问：为什么 Pre-LN 梯度更稳定？** 残差路径上没有 LN，梯度可以直接从输出流回输入，不被归一化截断。

---

## Q2 ⭐ RMSNorm 相比 LayerNorm 的区别？为什么 LLM 更偏好它？
**RMSNorm**：去掉均值中心化，只做 RMS 缩放：`y = x / RMS(x) * γ`，其中 `RMS(x) = sqrt(mean(x²))`。

**优点**：
- 计算量更小（省去均值计算）
- 实验表明效果与 LayerNorm 相当甚至更好
- 无需 β 参数，参数量略少

**代表**：Llama / Qwen / DeepSeek 全用 RMSNorm。

---

## Q3 ⭐ SwiGLU 的原理？为什么比 ReLU/GELU 好？
**FFN 的演变**：
- 原始 FFN：`FFN(x) = max(0, xW₁ + b₁)W₂`（ReLU）
- GLU（门控线性单元）：`GLU(x) = (xW₁) ⊙ σ(xW₂)`，用 sigmoid 门控
- **SwiGLU**：把 sigmoid 换成 Swish（`Swish(x) = x·σ(x)`）：`SwiGLU(x) = (xW₁) ⊙ Swish(xW₂)`，再乘 W₃

**为什么更好**：
- Swish 是平滑的非单调激活，梯度比 ReLU 更平滑（无死区）
- 门控机制让网络可以动态选择信息，表达力更强
- PaLM / Llama / Qwen / DeepSeek 均采用

**代价**：SwiGLU 需要三个权重矩阵（W₁/W₂/W₃），为保持参数量不变，通常把隐层维度从 4d 缩到 8d/3（约 2.67d）。

---

## Q4 Dropout 在现代 LLM 中还用吗？
基本**不用**。大规模预训练时 dropout 会损害性能（数据量足够大，正则化不是瓶颈）。SFT/RLHF 阶段偶尔在小数据集上用极小的 dropout（0.05 以下），但主流做法是不加。

---

## 一句话速记
- Pre-LN：残差路径无 LN，梯度稳定，现代 LLM 标配。
- RMSNorm：去均值中心化，更快，效果相当，Llama/Qwen/DeepSeek 全用。
- SwiGLU：门控 + Swish，平滑无死区，需三矩阵但隐层缩小补偿参数量。
