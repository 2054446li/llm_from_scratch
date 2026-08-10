# ch01 — Transformer 与注意力机制

> 高频必背。注意力是所有 LLM 的地基，MLA/GQA 直接关系到后训练 RL 的 rollout 吞吐（KV Cache 越小，长序列采样越快）。

---

## Q1 ⭐ 自注意力（Self-Attention）的计算过程？为什么要除以 √d_k？
**要点**：
- 输入 X 经三个投影得到 Q、K、V。注意力 `Attention(Q,K,V) = softmax(QKᵀ / √d_k) · V`。
- **除以 √d_k 的原因**：当 d_k 较大时，QKᵀ 的点积方差随维度线性增长（假设各分量独立均值0方差1，点积方差≈d_k），数值过大会把 softmax 推向饱和区（梯度接近0）。除以 √d_k 把方差归一化回 1，稳定梯度。
- **复杂度**：序列长 n、维度 d，时间与显存均为 O(n²·d)，这是长上下文的根本瓶颈。

**追问：为什么用点积而非加性注意力？** 点积可用高度优化的矩阵乘法（GEMM）实现，GPU 友好；加性注意力（Bahdanau）表达力相近但慢。

---

## Q2 ⭐ 多头注意力（MHA）的意义？多头是不是就是把维度切开？
**要点**：
- 把 d_model 切成 h 个头，每个头独立做注意力再拼接。**动机**：不同头可关注不同子空间/不同位置关系（有的头看语法、有的头看指代），增强表达。
- 是的，本质是把 d_model 分成 h×d_k，各头并行。参数量与单头基本一致（多了输出投影 W_O）。

---

## Q3 ⭐🔥 MHA / MQA / GQA / MLA 的区别？各自解决什么问题？
这是**推理效率**主线，直接影响 RL rollout 吞吐，必背对比表：

| 方案 | K/V 头数 | KV Cache | 质量 | 代表 |
|------|---------|---------|------|------|
| **MHA** | = Q 头数(h) | 最大 | 最好 | 原始 Transformer |
| **MQA** | 1（所有 Q 头共享） | 最小(1/h) | 略降 | PaLM、Falcon |
| **GQA** | g 组（1<g<h） | 中(g/h) | 接近 MHA | Llama2/3、Qwen2 |
| **MLA** | 低秩压缩 | 极小 | ≈MHA 甚至更好 | DeepSeek-V2/V3 |

- **核心矛盾**：推理时 KV Cache 占显存，长序列/大 batch 下成为瓶颈。减少 K/V 头数 = 压缩 KV Cache = 提高吞吐，但可能损失质量。
- **GQA** 是 MHA 和 MQA 的折中：Q 头分 g 组，组内共享一份 K/V。
- **MLA（Multi-head Latent Attention）**🔥：把 K/V 联合**低秩压缩**成一个小的 latent 向量 c，缓存 c 而非完整 K/V，推理时再上投影还原。DeepSeek 用它把 KV Cache 压到 GQA 的更小水平，同时质量不降（配合解耦 RoPE）。详见 ch15。

**为什么后训练工程师要关心这个？** RL 训练里 rollout（在线采样）是吞吐瓶颈，KV Cache 越小 → 同显存能跑越大 batch / 越长序列 → RL 采样越快。MLA 让 DeepSeek 的 RL 更可扩展。

---

## Q4 ⭐ FlashAttention 的原理？它降低了什么复杂度？
**要点**：
- **关键认知**：FlashAttention **不降低计算复杂度**（仍是 O(n²)），它降低的是**显存 IO / 显存占用**——避免显式生成 n×n 的注意力矩阵。
- **手段**：① **tiling 分块**——把 Q/K/V 切块，在 SRAM 里逐块计算，用 **online softmax**（增量更新最大值与归一化因子）避免存整个矩阵；② **重计算（recomputation）**——反向传播时不存中间注意力矩阵，重新算，用计算换显存。
- **收益**：显存从 O(n²) 降到 O(n)，速度因减少 HBM↔SRAM 数据搬运而大幅提升（IO-aware）。
- **v2 改进**：更好的并行划分（在序列维并行）、减少非矩阵乘运算；**v3**：利用 Hopper 架构的异步与 FP8。

**追问：online softmax 为什么能分块？** softmax 可增量计算——维护当前块的最大值 m 和指数和 l，新块来时用 `exp(m_old - m_new)` 校正旧的累加值即可，数学上等价于全局 softmax。

---

## Q5 为什么 Transformer 用 LayerNorm 而非 BatchNorm？
- NLP 序列**变长**、batch 内样本长度不一，BatchNorm 在序列/batch 维统计不稳定（尤其小 batch、推理时 batch=1）；LayerNorm 在**特征维**归一化，与 batch 无关，对变长序列稳定。详见 ch03。

---

## Q6 Encoder-only / Decoder-only / Encoder-Decoder 的区别与适用场景？
- **Encoder-only（BERT）**：双向注意力，擅长理解/分类，不能自回归生成。
- **Decoder-only（GPT/Llama/DeepSeek）**：因果掩码单向，自回归生成，是当前 LLM 主流（scaling 好、预训练目标统一）。
- **Encoder-Decoder（T5）**：翻译/摘要等 seq2seq，cross-attention 连接。
- **为什么主流是 Decoder-only？** 预训练目标简单统一（next-token）、few-shot 涌现好、架构简洁易 scale。

---

## Q7 因果掩码（causal mask）如何实现？训练时如何并行？
- 在 QKᵀ 后、softmax 前，把上三角（未来位置）置为 -∞，softmax 后即为 0，保证位置 t 只能看到 ≤t。
- **训练可并行**：一次前向对所有位置并行计算 loss（teacher forcing），因果掩码保证不泄露未来。**推理不能并行**：自回归逐 token 生成，故需 KV Cache 复用历史。

---

## Q8 ⭐ KV Cache 是什么？为什么需要？占多少显存？
**是什么**：自回归解码时，生成第 t 个 token 需要用到前面所有 token 的 K/V。如果每步都重算整个序列的 K/V，复杂度是 O(n²)。KV Cache 把已计算的 K/V 缓存下来，每步只算新 token 的 K/V，把单步复杂度降到 O(n)。

**显存占用**：`2（K和V）× n_layers × n_heads × d_head × seq_len × batch × 精度字节数`。
- 长序列 / 大 batch 下，KV Cache 会超过模型权重本身，成为推理显存瓶颈。
- 这正是 **GQA / MQA / MLA 要压缩的对象**（Q3），也是 RL rollout 吞吐的关键约束。

**追问：prefill 和 decode 阶段的区别？** Prefill（处理 prompt）是计算密集（一次并行算完整 prompt 的 K/V）；decode（逐 token 生成）是访存密集（每步只算一个 token，但要读全部 KV Cache）。两阶段的优化策略不同（如 chunked prefill、continuous batching）。

---

## 一句话速记
- 注意力除 √d_k：防点积方差过大致 softmax 饱和。
- GQA/MQA/MLA：都在压 KV Cache 换吞吐，MLA 低秩压缩质量几乎不降。
- FlashAttention：不降计算复杂度，降显存 IO（tiling + online softmax + 重计算）。
