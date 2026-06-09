# 第 1 周：Transformer 架构与注意力机制深度讲解

> **学习目标**：从数学原理深度理解 Attention 机制，掌握 Transformer 架构的每一个细节，理解位置编码的演进，了解前沿进展。

---

## 📖 目录

1. [Attention 机制的历史与直观理解](#1-attention-机制的历史与直观理解)
2. [Scaled Dot-Product Attention 详解](#2-scaled-dot-product-attention-详解)
3. [Multi-Head Attention](#3-multi-head-attention)
4. [位置编码的演进](#4-位置编码的演进)
5. [完整的 Transformer 架构](#5-完整的-transformer-架构)
6. [前沿进展](#6-前沿进展)
7. [总结与面试准备](#7-总结与面试准备)

---

## 1. Attention 机制的历史与直观理解

### 1.1 为什么需要 Attention？

在 Transformer 出现之前，序列模型主要使用 RNN（LSTM、GRU）。RNN 的问题：

1. **顺序依赖**：只能顺序处理序列，无法并行化
2. **长距离依赖**：难以学习长序列中远距离位置的依赖关系
3. **梯度消失/爆炸**：虽然有 LSTM 的改进，但问题依然存在

**Attention 的核心思想**：不是顺序地处理序列，而是让每个位置都可以直接"看到"序列中的其他位置，并根据相关性加权聚合信息。

### 1.2 Attention 的直观理解

想象你在阅读一篇文章，需要理解某个词的含义。你会：
1. **查看**所有其他词（查询）
2. **评估**它们与当前词的相关程度（注意力权重）
3. **聚合**相关词的信息来理解当前词

数学上，这可以表示为：
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

其中：
- **Q**（Query）：当前位置的查询向量
- **K**（Key）：所有位置的键向量
- **V**（Value）：所有位置的值向量
- **$\sqrt{d_k}$**：缩放因子

### 1.3 Attention 的演进历程

- **2014**：Bahdanau 等人提出 Attention 机制（序列到序列模型）
- **2015**：Attention is All You Need 前的各种 Attention 变体
- **2017**：Vaswani 等人提出 Multi-Head Attention（Transformer 论文）
- **2018 年后**：各种改进和优化（前面会详细讲）

---

## 2. Scaled Dot-Product Attention 详解

### 2.1 为什么要缩放？

在计算 $QK^T$ 时，如果 $d_k$ 很大（比如 64 或 128），矩阵乘积的结果会非常大。

**问题**：
- 当 $QK^T$ 中的值很大时，经过 softmax 后，梯度会非常小（接近 0）
- 这导致梯度消失，训练困难

**解决方案**：除以 $\sqrt{d_k}$ 来缩放

**数学分析**：
- Q 和 K 是随机初始化的，假设它们的元素均值为 0、方差为 1
- $QK^T$ 中每个元素是 $d_k$ 个随机变量的乘积之和
- 这个和的方差大约是 $d_k$（如果样本独立）
- 所以 $\sqrt{d_k}$ 的缩放使得 $\frac{QK^T}{\sqrt{d_k}}$ 的方差回到 1

### 2.2 Softmax 的作用

$$\text{softmax}(x_i) = \frac{e^{x_i}}{\sum_j e^{x_j}}$$

**为什么用 softmax？**

1. **输出归一化**：注意力权重和为 1，是一个有效的概率分布
2. **可微分**：便于反向传播
3. **关注高分项**：指数函数让高分的位置获得更多的注意

**关键性质**：
- softmax 对输入有平移不变性：$\text{softmax}(x + c) = \text{softmax}(x)$
- 这就是为什么可以在 softmax 前进行掩码（masking）

### 2.3 完整的计算流程

给定输入序列 $X \in \mathbb{R}^{n \times d}$（n 是序列长度，d 是向量维度）：

1. **投影到 Q, K, V**：
   - $Q = XW^Q$，$K = XW^K$，$V = XW^V$
   - 其中 $W^Q, W^K, W^V$ 是可学习的投影矩阵

2. **计算注意力分数**：
   - $S = QK^T$（大小 $n \times n$）
   - 这里计算了每对位置之间的"兼容性"

3. **缩放和 softmax**：
   - $A = \text{softmax}\left(\frac{S}{\sqrt{d_k}}\right)$
   - 现在 $A$ 是 $n \times n$ 的矩阵，第 $i$ 行表示第 $i$ 个位置对所有位置的注意权重

4. **聚合值向量**：
   - $\text{Output} = AV$
   - 第 $i$ 行是第 $i$ 个位置对所有值的加权和

### 2.4 计算复杂度分析

**时间复杂度**：
- $QK^T$：$O(n^2 d)$
- softmax：$O(n^2)$
- $AV$：$O(n^2 d)$
- 总计：**$O(n^2 d)$**

**空间复杂度**：
- 存储注意力矩阵 $A$：$O(n^2)$
- 存储中间结果：$O(n^2 + nd)$
- 总计：**$O(n^2 + nd)$**

**对长序列的影响**：
- 当 $n$ 很大时（如 4K、8K、32K token），$O(n^2)$ 的复杂度会变成瓶颈
- 这就是 Flash Attention 等优化方法的动机

### 2.5 Attention 的梯度分析

反向传播时，梯度流如下：

1. 输出梯度 $\nabla_{\text{Output}} \in \mathbb{R}^{n \times d_v}$
2. 流向 $A$ 和 $V$
3. 再流向 softmax，然后流向 $S$
4. 最后流向 $Q, K, V$ 的投影矩阵

**关键发现**：softmax 的梯度会根据注意力分布的"熵"而变化，高度集中的注意力会导致梯度流更加稀疏。

---

## 3. Multi-Head Attention

### 3.1 为什么需要多头？

单一的 Attention 头可能不足以捕捉序列中的多种关系：
- 某些头可能学习"语义关系"
- 另一些头可能学习"句法结构"
- 还有的可能学习"指代关系"

**多头的优势**：
- 允许模型同时关注序列的不同部分
- 增加模型的"表达能力"
- 每个头独立学习，可以学到互补的注意模式

### 3.2 数学定义

假设总维度为 $d_{model}$，分成 $h$ 个头，每个头的维度为 $d_k = d_{model} / h$：

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h) W^O$$

其中：
$$\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

**关键参数**：
- $W_i^Q, W_i^K, W_i^V$ 是投影矩阵（每个头独立）
- $W^O$ 是最终的输出投影矩阵

### 3.3 头数与维度的选择

在 GPT-3 和许多大模型中：
- 模型维度（$d_{model}$）：常见值 768, 1024, 2048, ..., 12288
- 头数（$h$）：常见值 8, 16, 32, ...
- 每头维度（$d_k = d_{model} / h$）：通常在 64 或 128

**选择原则**：
- 头数越多，计算细粒度越高，但参数量也越多
- 通常 $d_k$ 选择为 64，这在很多模型中被验证是有效的
- 头数根据模型大小选择，确保 $d_k$ 在合理范围内

### 3.4 多头并行处理

```
Input Sequence (n, d_model)
    |
    +---> Linear Projection (W^Q, W^K, W^V)
    |
    +---> Split into h heads (n, d_k) for each head
    |
    +---> h Attention heads in PARALLEL
    |       | head_1 | head_2 | ... | head_h |
    |       |   Attention   | Attention  | Attention |
    |
    +---> Concatenate (n, d_model)
    |
    +---> Linear Projection (W^O)
    |
Output (n, d_model)
```

**并行性**：
- h 个 Attention 头可以完全并行计算
- 总计算量：$O(h \cdot n^2 \cdot d_k) = O(n^2 d_{model})$（与单头相同）
- 但可以充分利用 GPU 的并行处理能力

---

## 4. 位置编码的演进

### 4.1 为什么需要位置编码？

Attention 机制是**置换不变的**（Permutation Invariant）：
- 如果你改变输入序列的顺序，只要重新排列输出，结果完全相同
- 但序列是有顺序的！"猫在狗前面" vs "狗在猫前面" 意思完全不同

**解决方案**：给每个位置的向量加上位置信息。

### 4.2 绝对位置编码（Absolute Positional Encoding）

**原始 Transformer 的方法**：

$$PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d}}\right)$$
$$PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d}}\right)$$

其中：
- $pos$ 是位置（0, 1, 2, ...）
- $i$ 是维度索引（0, 1, ..., $d/2$）
- 这样生成的 PE 是固定的，不需要学习

**直观理解**：
- 不同位置有不同的正弦/余弦波形
- 低频成分（$i$ 小）变化慢，捕捉全局位置
- 高频成分（$i$ 大）变化快，捕捉精细位置

**优势**：
- 无需额外参数，节省空间
- 可以外推到比训练序列更长的位置

**缺点**：
- 无法明确地编码相对位置信息
- 对长文本的泛化能力有限

### 4.3 RoPE（Rotary Position Embedding）

这是目前最流行的位置编码方法，被 LLaMA、GPT-3.5/4 等模型采用。

**核心思想**：用旋转矩阵来编码位置

$$\text{RoPE}(m) = \begin{pmatrix}
\cos(m\theta_1) & -\sin(m\theta_1) & 0 & 0 & \cdots \\
\sin(m\theta_1) & \cos(m\theta_1) & 0 & 0 & \cdots \\
0 & 0 & \cos(m\theta_2) & -\sin(m\theta_2) & \cdots \\
0 & 0 & \sin(m\theta_2) & \cos(m\theta_2) & \cdots \\
\vdots & \vdots & \vdots & \vdots & \ddots
\end{pmatrix}$$

其中 $\theta_j = 10000^{-2j/d}$

**为什么叫 RoPE？**
- 在二维平面上，旋转 $m$ 个角度可以编码位置 $m$
- 向量 $(x, y)$ 旋转 $\theta$ 角度后，它们之间的夹角关系被保留

**应用方式**：
直接在 Attention 的 Q 和 K 上应用旋转：
$$Q' = \text{RoPE}(pos) \cdot Q$$
$$K' = \text{RoPE}(pos) \cdot K$$

**优势**：
- ✅ **编码相对位置**：$Q_m^T K_n$ 只依赖于 $m - n$（相对距离）
- ✅ **长文本泛化**：可以处理比训练时更长的序列
- ✅ **参数高效**：不需要额外参数
- ✅ **计算高效**：只需要在初始化时计算一次

**数学证明**（为什么 RoPE 编码相对位置）：

设 $q_m = R_m q$，$k_n = R_n k$（$R_m$ 是旋转矩阵），则：
$$q_m^T k_n = q^T R_m^T R_n k = q^T R_{m-n} k$$

这表明，两个位置之间的点积只取决于它们的相对距离 $m - n$！

### 4.4 ALiBi（Attention with Linear Biases）

提出者认为位置编码不必要，可以用偏置项替代。

**方法**：在 softmax 之前，直接在注意力分数上加上一个线性偏置：

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}} + B\right) V$$

其中 $B_{ij} = -\alpha \cdot |i - j|$（$\alpha$ 是超参数）

**直观理解**：
- 同一位置（$i = j$）：偏置为 0，没有惩罚
- 相邻位置（$|i - j| = 1$）：偏置为负，减弱注意力
- 远距离位置：偏置更负，进一步减弱注意力

**优势**：
- ✅ **无参数**：不需要学习位置编码
- ✅ **自然的相对位置偏好**：模型自然倾向于关注近距离的位置
- ✅ **长文本外推**：可以处理更长的序列

**缺点**：
- 相比 RoPE，ALiBi 的表现略差（在大多数基准测试中）
- 位置信息较为"隐式"

### 4.5 其他位置编码方法对比

| 方法 | 参数 | 可学习 | 相对位置 | 长文本泛化 | 计算效率 |
|-----|------|-------|--------|----------|--------|
| 绝对 PE | 有 | ✗ | ✗ | ✗ | ✅ 高 |
| 相对 PE | 有 | ✓ | ✅ | ~ | ✗ 低 |
| RoPE | 无 | - | ✅ | ✅ | ✅ 高 |
| ALiBi | 无 | - | ✅ | ✅ | ✅ 高 |
| T5 Bias | 少 | ✓ | ✅ | ✅ | ✅ 高 |

**现状**：RoPE 因其优秀的性能和效率，已成为大多数最新模型的标准选择（LLaMA、GPT-3.5/4、Qwen、DeepSeek 等）。

---

## 5. 完整的 Transformer 架构

### 5.1 整体架构

```
输入序列
    |
    v
Token Embedding + Positional Encoding
    |
    v
+--[Encoder Block]--+  (重复 N 次)
|  - Multi-Head Attention
|  - Feed Forward Network (FFN)
|  - Layer Normalization
|  - Residual Connections
+-------------------+
    |
    v
[Encoder Output]
    |
    v (交叉注意力)
+--[Decoder Block]--+  (重复 M 次)
|  - Causal Self-Attention
|  - Cross-Attention (with Encoder)
|  - Feed Forward Network
|  - Layer Normalization
|  - Residual Connections
+-------------------+
    |
    v
Output Projection + Softmax
    |
    v
概率分布（下一个 token）
```

### 5.2 编码器块（Encoder Block）

```python
def EncoderBlock(x):
    # Multi-Head Self-Attention
    attn_output = MultiHeadAttention(x, x, x)
    x = LayerNorm(x + attn_output)  # Residual + Layer Norm
    
    # Feed Forward Network
    ffn_output = FFN(x)
    x = LayerNorm(x + ffn_output)  # Residual + Layer Norm
    
    return x
```

**关键组件**：

1. **Multi-Head Self-Attention**
   - Q, K, V 都来自同一输入
   - 可以并行处理整个序列

2. **Layer Normalization**
   - 对特征维度进行归一化
   - 比 Batch Norm 更适合 NLP（因为序列长度可变）

3. **Residual Connection（残差连接）**
   - 让梯度直接流向深层
   - 使得很深的模型也能训练

4. **Feed Forward Network**
   - 两层全连接网络
   - 通常第一层扩展到 $4d_{model}$，第二层回到 $d_{model}$
   - 激活函数是 ReLU 或 GELU

### 5.3 解码器块（Decoder Block）- 仅适用于 Encoder-Decoder 模型

```python
def DecoderBlock(x, encoder_output):
    # Causal Self-Attention
    attn_output = MultiHeadAttention(x, x, x, mask=causal_mask)
    x = LayerNorm(x + attn_output)
    
    # Cross-Attention with Encoder
    cross_attn_output = MultiHeadAttention(x, encoder_output, encoder_output)
    x = LayerNorm(x + cross_attn_output)
    
    # Feed Forward Network
    ffn_output = FFN(x)
    x = LayerNorm(x + ffn_output)
    
    return x
```

**因果掩码（Causal Mask）**：
- 在生成模式下，只能关注当前位置及之前的位置
- 防止模型"作弊"地看到未来的信息
- 实现方式：在 softmax 前，将未来位置的注意分数设为 $-\infty$

**交叉注意力（Cross-Attention）**：
- Q 来自解码器
- K, V 来自编码器
- 允许解码器"查看"编码器处理过的整个输入

### 5.4 信息流分析

对于一个位置的输出向量：

1. **自注意力**：聚合同一层的所有位置的信息
2. **前馈网络**：对每个位置独立应用非线性变换
3. **多层堆叠**：不同层可以学习不同的抽象级别

**接受域（Receptive Field）**：
- 第 1 层：每个位置可以看到所有其他位置（通过 Attention）
- 所以 1 层 Transformer 的接受域就是整个序列

**对比 CNN**：CNN 需要 $O(\log n)$ 层才能覆盖全序列；**Transformer 只需 1 层**

---

## 6. 前沿进展

### 6.1 Flash Attention

**问题**：标准 Attention 的瓶颈不是计算本身，而是内存读写（IO 操作）。

**原因**：
- 计算 $QK^T$（$n^2 d$）后，需要从高带宽内存（HBM）读取到片上内存
- 然后计算 softmax，再读取 $V$
- 多次 IO 操作导致效率低下

**Flash Attention 的优化**：
1. **块状处理**：将序列分成块，在块内完成 Attention 计算，减少 IO 次数
2. **在线 Softmax**：在计算 Attention 时，同时更新 softmax 的分母，避免重复读写

**性能提升**：
- 实际运行时间：**加速 2-4 倍**
- 内存使用：**减少一半**
- 精度：**完全相同**（数值精确）

### 6.2 Multi-Query Attention (MQA)

**问题**：在推理时，每个 Query 都需要完整的 K, V 缓存，内存占用很大。

**标准 Attention 的 KV 缓存**：
```
Q: (batch, seq_len, num_heads, head_dim)
K: (batch, seq_len, num_heads, head_dim)  <-- 重复 num_heads 次
V: (batch, seq_len, num_heads, head_dim)  <-- 重复 num_heads 次
```

**MQA 的想法**：
- 所有 Query 头共享同一个 K 和 V
- K, V 只有一份，而不是 num_heads 份
- 节省内存，加快推理

**计算**：
```
output_i = Attention(Q_i, K_shared, V_shared)
```

**优势**：
- ✅ 推理时 KV 缓存减少 num_heads 倍
- ✅ 推理速度提升（减少内存传输）
- ✓ 参数量减少

**缺点**：
- ✗ 模型性能下降（多头的多样性减少）
- ✗ 在中等规模模型上，性能损失明显

### 6.3 Grouped-Query Attention (GQA)

**想法**：MQA 太激进了，损失太大。何不让多个 Query 头共享一个 KV？

**结构**：
```
假设 num_query_heads = 32, num_kv_heads = 4
Query 头分成 8 组，每组 4 个头共享一个 KV
```

**性能**：
- 比 MQA 性能更好（多样性更强）
- 比标准 Attention 的 KV 缓存更小（8 倍）
- **参数量和计算量不变**

**应用**：
- LLaMA 2 采用了 GQA
- 成为推理优化的新标准

### 6.4 其他前沿进展

**Efficient Attention 方法**：
- **Sparse Attention**：不计算全部注意力，只计算特定模式（如块状、条纹等）
- **Approximate Attention**：用低秩近似降低复杂度
- **Kernel-based Attention**：用核函数替代 softmax

这些方法各有权衡，但在实际应用中，Flash Attention + GQA 的组合已经相当高效。

---

## 7. 总结与面试准备

### 7.1 关键知识点总结

| 概念 | 核心要点 | 面试重点 |
|-----|--------|--------|
| Attention | 加权聚合，相关性驱动 | 为什么使用 softmax |
| 缩放因子 | 稳定方差，防止梯度消失 | 为什么除以 $\sqrt{d_k}$ |
| 多头 | 多视角，并行处理 | 头数与维度的关系 |
| RoPE | 旋转编码相对位置 | 长文本泛化的原理 |
| Flash Attention | IO 优化，不改变计算结果 | 如何减少内存访问 |
| GQA | 共享 KV，推理优化 | 与 MQA 的区别 |

### 7.2 常见面试题与回答框架

**Q1: 解释 Attention 机制**

**良好的回答框架**：
```
1. 背景：为什么需要 Attention（RNN 的局限）
2. 核心思想：加权聚合，权重由相关性决定
3. 数学：Q, K, V，softmax，缩放
4. 为什么 softmax：归一化、梯度流、概率解释
5. 优势：长距离依赖、可并行、高效
```

**Q2: 为什么 Transformer 比 RNN 更好**

**框架**：
```
1. 长距离依赖：Attention 一次性看到全序列，RNN 需要多步
2. 并行性：Transformer 可以并行处理，RNN 必须顺序处理
3. 梯度流：Attention 有更好的梯度流，RNN 容易梯度消失
4. 实践：大规模预训练时，Transformer 更高效
```

**Q3: 为什么 RoPE 比绝对位置编码更好**

**框架**：
```
1. 绝对编码的问题：外推性差，不明确编码相对信息
2. RoPE 的核心：旋转矩阵自然编码相对位置
3. 优势：Q^T K 只依赖相对距离，天然适应长文本
4. 实践证明：已成为 GPT-3.5/4、LLaMA 等的标准
```

**Q4: 如何优化 Transformer 的推理速度**

**框架**：
```
1. 计算角度：GQA 减少 KV 缓存，MQA 进一步优化
2. 内存角度：Flash Attention 减少 IO
3. 模型角度：量化、蒸馏、剪枝
4. 调度角度：批处理、动态批处理、投机解码
```

### 7.3 深度追问准备

**可能的追问**：

1. **"为什么 softmax 比其他归一化方法好？"**
   - 指数的数学性质：强化高值
   - 导数性质：便于反向传播
   - 概率解释：信息论视角

2. **"多头注意力是否可以减少到单头？"**
   - 理论上可以（参数转移）
   - 但实际效果：多头更易学到多样化的模式
   - 计算效率：多头利用并行性更好

3. **"位置编码可以学习吗？"**
   - 可以，但不必要
   - 固定编码：参数少，外推性好
   - 学习编码：灵活，但需要更多参数
   - RoPE/ALiBi：最优的权衡

4. **"Attention 为什么不能替代所有层？"**
   - FFN 提供非线性变换和特征融合
   - Attention：聚合（线性）
   - FFN：转换（非线性）
   - 两者结合才能学习复杂函数

### 7.4 自我测试清单

完成以下项目，说明你已经掌握了这一周的内容：

- [ ] 能用公式推导 Attention 的完整计算过程吗？
- [ ] 理解为什么需要缩放因子吗？能解释方差分析吗？
- [ ] 了解多头注意力的并行性质吗？
- [ ] 能对比 4 种位置编码方式的优劣吗？
- [ ] 知道 RoPE 如何编码相对位置吗？（旋转矩阵性质）
- [ ] 理解 Flash Attention 的核心优化吗？（IO vs 计算）
- [ ] 知道 GQA 和 MQA 的区别吗？
- [ ] 完成了 qa/week1_qa.md 的所有问题吗？

---

## 📚 延伸阅读

### 论文
- **Attention is All You Need** (Vaswani et al., 2017) - Transformer 基础
- **RoPE: Rotary Position Embedding** - 最新位置编码
- **Flash-Attention: Fast and Memory-Efficient Exact Attention with IO-Awareness** - 推理优化
- **GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints** - 推理优化

### 代码参考
- HuggingFace Transformers 库
- PyTorch 官方教程
- DeepSeek/Qwen 等开源模型的实现

---

**🎯 学习完成后，请回答 `qa/week1_qa.md` 中的所有问题，确保深度理解每个概念。**
