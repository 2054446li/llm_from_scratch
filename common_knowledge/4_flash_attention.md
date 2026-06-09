# Flash Attention

## 概述

Flash Attention 是一种 IO 感知（IO-aware）的精确注意力计算算法，通过分块计算（tiling）和核融合（kernel fusion）大幅减少 GPU HBM（高带宽内存）访问次数，在不牺牲精度的前提下显著加速注意力计算并降低显存占用。

## 前置知识：GPU 内存层次

```
┌─────────────────────────────┐
│        SRAM (On-chip)       │  ← 快但小
│   容量: ~20 MB (A100)       │
│   带宽: ~19 TB/s            │
└──────────────┬──────────────┘
               │  ← 这里是瓶颈（~10x 速度差）
┌──────────────▼──────────────┐
│        HBM (Off-chip)       │  ← 大但慢
│   容量: 40-80 GB (A100)     │
│   带宽: ~2 TB/s             │
└─────────────────────────────┘
```

现代 GPU 的计算速度远超内存带宽。对于注意力计算这类**计算密度低、访存量大**的操作，瓶颈不在计算而在数据搬运。Flash Attention 的核心就是减少 HBM ↔ SRAM 之间的数据搬运次数。

## 标准注意力的问题

标准注意力的计算：

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

### 标准实现的步骤（每步都要访问 HBM）

```
Step 1: S = Q × K^T          [从 HBM 读 Q,K → 计算 → 写 S(N×N) 到 HBM]
Step 2: P = softmax(S)       [从 HBM 读 S → 计算 → 写 P(N×N) 到 HBM]
Step 3: O = P × V            [从 HBM 读 P,V → 计算 → 写 O 到 HBM]
```

**问题**：中间矩阵 S 和 P 都是 $N \times N$（N=序列长度），必须完整存储在 HBM 中：
- 显存占用：$O(N^2)$
- HBM 读写量：$O(N^2 d)$（d 为头维度）
- 当 N=4096, d=128 时，S 矩阵 = 4096×4096×2bytes = 32MB **每个头每个样本**

## Flash Attention 的核心思想

### 思想1：分块计算（Tiling）

不一次性计算完整的 $N \times N$ 注意力矩阵，而是将 Q、K、V 分成小块，逐块在 SRAM 中完成计算：

```
Q 分块: Q₁, Q₂, ..., Q_Tr    每块大小 Br × d
K 分块: K₁, K₂, ..., K_Tc    每块大小 Bc × d
V 分块: V₁, V₂, ..., V_Tc    每块大小 Bc × d

Br, Bc 选择使得每块能放入 SRAM
```

### 思想2：在线 Softmax（Online Softmax）

分块计算的难点在于 softmax 需要整行的全局信息（max 和 sum）。Flash Attention 使用在线算法逐块更新，无需看到整行就能计算精确的 softmax 结果。

### 思想3：核融合（Kernel Fusion）

将 matmul → softmax → matmul 三步合并为一个 CUDA kernel，中间结果全程留在 SRAM，只在最后将输出 O 写回 HBM。

## 详细算法流程

### 输入

- Q, K, V ∈ ℝ^{N×d}，存储在 HBM 中
- 输出 O ∈ ℝ^{N×d}
- 块大小 Br（Q 的行方向）、Bc（K/V 的行方向）

### 算法伪代码

```
初始化: O = 0, l = 0 (行求和), m = -∞ (行最大值)     // 存在 HBM

// 外循环：遍历 Q 的块
for i = 1 to ⌈N/Br⌉:
    从 HBM 加载 Qᵢ, Oᵢ, lᵢ, mᵢ 到 SRAM

    // 内循环：遍历 K, V 的块
    for j = 1 to ⌈N/Bc⌉:
        从 HBM 加载 Kⱼ, Vⱼ 到 SRAM

        // ---- 以下全部在 SRAM 中完成 ----
        // 1. 计算局部注意力分数
        Sᵢⱼ = Qᵢ × Kⱼᵀ                    // Br × Bc 的小矩阵

        // 2. 更新 running max
        m_new = max(mᵢ, rowmax(Sᵢⱼ))

        // 3. 计算局部 softmax（用新的 max）
        P̃ᵢⱼ = exp(Sᵢⱼ - m_new)

        // 4. 更新 running sum
        l_new = exp(mᵢ - m_new) × lᵢ + rowsum(P̃ᵢⱼ)

        // 5. 修正旧输出 + 累积新贡献
        Oᵢ = (lᵢ × exp(mᵢ - m_new) / l_new) × Oᵢ
           + (1 / l_new) × P̃ᵢⱼ × Vⱼ

        // 6. 更新统计量
        mᵢ = m_new
        lᵢ = l_new

    // 内循环结束，写回 HBM
    将 Oᵢ, lᵢ, mᵢ 写回 HBM
```

### 图示：一次内循环迭代

```
        HBM                           SRAM
 ┌──────────────┐              ┌─────────────────┐
 │  Q₁ Q₂ ... │──── Qᵢ ────→│                 │
 │  K₁ K₂ ... │──── Kⱼ ────→│  Sᵢⱼ = Qᵢ×Kⱼᵀ │
 │  V₁ V₂ ... │──── Vⱼ ────→│  P̃ = exp(S-m)  │
 │             │              │  O += P̃ × Vⱼ   │
 │  O₁ O₂ ... │←─── Oᵢ ─────│  update m, l    │
 └──────────────┘              └─────────────────┘
     (慢,大)                       (快,小)

 读入: Qᵢ(Br×d) + Kⱼ(Bc×d) + Vⱼ(Bc×d)
 写出: Oᵢ(Br×d)   ← 中间的 N×N 矩阵从不存在于 HBM!
```

## Online Softmax 详解

这是 Flash Attention 最关键的数学技巧。

### 问题

标准 softmax 需要两遍扫描：

$$\text{softmax}(x_i) = \frac{e^{x_i - \max(x)}}{\sum_j e^{x_j - \max(x)}}$$

- 第一遍：找 max 和 sum
- 第二遍：计算每个元素的归一化值

**但分块计算时，我们一次只能看到一部分 $x$，max 和 sum 会随着新块的到来而变化！**

### 解决方案：逐块修正

维护两个 running 统计量：
- $m$：已见所有块的行最大值
- $l$：已见所有块的 $\sum e^{x-m}$

当新块到来时：

```
已有: m_old, l_old, O_old（基于旧统计量的输出）
新块: S_new（当前块的注意力分数）

Step 1: m_new = max(m_old, max(S_new))

Step 2: l_new = l_old × exp(m_old - m_new)     ← 修正旧的 sum
              + sum(exp(S_new - m_new))          ← 新块的贡献

Step 3: O_new = O_old × [l_old × exp(m_old - m_new) / l_new]  ← 缩放旧输出
              + [exp(S_new - m_new) / l_new] × V_new           ← 新贡献
```

### 为什么这是精确的

数学证明（以两块为例）：

```
标准 softmax: softmax([a, b])_i = exp(a_i - max(a,b)) / [Σexp(a-max) + Σexp(b-max)]

在线计算:
  处理块 a 后: m=max(a), l=Σexp(a-m), O=softmax_partial(a)×V_a
  处理块 b 后:
    m_new = max(max(a), max(b)) = max(a,b)     ← 与标准一致
    l_new = Σexp(a-m_new) + Σexp(b-m_new)      ← 与标准分母一致
    O_new 经过修正后 = 标准 softmax × V        ← 精确！
```

关键等式：$e^{x - m_{old}} = e^{x - m_{new}} \cdot e^{m_{new} - m_{old}}$

旧的结果只需要乘以 $e^{m_{old} - m_{new}}$ 就能修正为基于新 max 的结果。

### 数值例子

```
行向量 x = [2, 4, 1, 5, 3, 2]，分两块处理

块1: [2, 4, 1]
  m₁ = 4
  l₁ = exp(2-4) + exp(4-4) + exp(1-4) = 0.135 + 1 + 0.050 = 1.185
  P₁ = [0.114, 0.844, 0.042]  (局部归一化)

块2: [5, 3, 2]
  m_new = max(4, 5) = 5
  l_new = 1.185 × exp(4-5) + [exp(5-5) + exp(3-5) + exp(2-5)]
        = 1.185 × 0.368 + 1 + 0.135 + 0.050
        = 0.436 + 1.185
        = 1.621
  O 按新的 l_new 重新归一化 → 结果与一次性计算完全一致
```

## IO 复杂度分析

| 方法 | HBM 读写量 | 显存占用 |
|------|-----------|---------|
| 标准注意力 | $O(N^2 d + N^2)$ | $O(N^2)$ |
| Flash Attention | $O(N^2 d^2 / M)$ | $O(N)$ |

其中 $M$ 为 SRAM 大小，$d$ 为头维度。

**为什么 Flash Attention 更快**：
- A100 的 SRAM = 20MB，d = 128
- $M / d^2 = 20×10^6 / (128^2×2) ≈ 610$
- 所以 HBM 访问减少约 $\min(M/d^2, N/d)$ 倍

## 反向传播：重计算而非存储

标准实现保存 $P$（$N \times N$）用于反向传播 → 显存 $O(N^2)$。

Flash Attention 的做法：
- 前向时只保存 $O$、$l$（logsumexp）、$m$
- 反向时从 Q、K、V 重新计算 $P$ 的每个块（recomputation）
- 用少量额外计算换取 $O(N^2) → O(N)$ 的显存节省

## 版本演进

| 版本 | 主要改进 | 加速比 |
|------|---------|--------|
| Flash Attention v1 (2022) | 分块计算 + 核融合 + 重计算 | 2-4x vs PyTorch |
| Flash Attention v2 (2023) | 减少非矩阵运算、优化 warp 并行、交换内外循环 | 约2x vs v1 |
| Flash Attention v3 (2024) | Hopper 架构优化（H100），异步 + FP8 + wgmma | 约1.5x vs v2 |

### v2 的关键改进

1. **交换内外循环**：外循环遍历 K/V 块，内循环遍历 Q 块 → 减少对 O 的 HBM 写回次数
2. **减少非矩阵运算**：softmax rescaling 的标量运算占比高，v2 将其移出内循环
3. **更好的 warp 并行**：v1 中不同 warp 计算同一行的不同部分（需要同步），v2 让不同 warp 计算不同行（无需同步）

## 实现代码（简化版 PyTorch）

```python
import torch
import math


def flash_attention_forward(Q, K, V, block_size=64):
    """
    Flash Attention 前向传播的简化 Python 实现
    实际实现是 CUDA kernel，这里展示算法逻辑

    Q, K, V: [batch, n_heads, seq_len, head_dim]
    """
    B, H, N, d = Q.shape
    O = torch.zeros_like(Q)
    l = torch.zeros(B, H, N, 1, device=Q.device)  # running sum
    m = torch.full((B, H, N, 1), float('-inf'), device=Q.device)  # running max

    Bc = block_size  # K/V block size
    Br = block_size  # Q block size

    # 外循环：遍历 Q 的块
    for i in range(0, N, Br):
        Qi = Q[:, :, i:i+Br, :]           # [B, H, Br, d]
        Oi = O[:, :, i:i+Br, :]
        li = l[:, :, i:i+Br, :]
        mi = m[:, :, i:i+Br, :]

        # 内循环：遍历 K, V 的块
        for j in range(0, N, Bc):
            Kj = K[:, :, j:j+Bc, :]       # [B, H, Bc, d]
            Vj = V[:, :, j:j+Bc, :]

            # 1. 计算局部注意力分数
            Sij = Qi @ Kj.transpose(-2, -1) / math.sqrt(d)  # [B, H, Br, Bc]

            # 2. 更新 running max
            m_new = torch.maximum(mi, Sij.max(dim=-1, keepdim=True).values)

            # 3. 局部 exp（用新 max 归一化）
            P_tilde = torch.exp(Sij - m_new)

            # 4. 更新 running sum
            l_new = li * torch.exp(mi - m_new) + P_tilde.sum(dim=-1, keepdim=True)

            # 5. 修正旧输出 + 累积新贡献
            Oi = Oi * (li * torch.exp(mi - m_new) / l_new) + (P_tilde / l_new) @ Vj

            # 6. 更新统计量
            mi = m_new
            li = l_new

        # 写回
        O[:, :, i:i+Br, :] = Oi
        l[:, :, i:i+Br, :] = li
        m[:, :, i:i+Br, :] = mi

    return O
```

### 实际使用（调用已优化的实现）

```python
# PyTorch 2.0+ 内置
from torch.nn.functional import scaled_dot_product_attention
output = scaled_dot_product_attention(Q, K, V, is_causal=True)

# 或直接使用 flash-attn 库
from flash_attn import flash_attn_func
output = flash_attn_func(Q, K, V, causal=True)
```

## 优势

1. **精确计算**：结果与标准注意力完全一致，非近似方法
2. **显存节省**：无需存储 $N \times N$ 注意力矩阵，显存从 $O(N^2)$ 降为 $O(N)$
3. **速度提升**：减少 HBM 访问，典型加速 2-4 倍
4. **支持更长序列**：显存节省使得长上下文训练成为可能

## 局限性

| 局限 | 说明 |
|------|------|
| 需要 CUDA 实现 | 纯 Python 无法体现优势，必须写自定义 kernel |
| 对 head_dim 敏感 | d 很大时 SRAM 装不下，需要对 d 也分块 |
| Causal mask 复杂 | 需要特殊处理上三角 mask，增加实现复杂度 |
| 反向传播较慢 | 重计算带来约 20% 额外计算开销（但节省的显存更值得）|

## 应用场景

- 几乎所有现代大模型训练和推理框架均已集成
- DeepSeek LLM、LLaMA 2/3、GPT-4 等均使用

## 参考文献

- Dao, T., et al. (2022). FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness.
- Dao, T. (2023). FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning.
- Milakov, M., & Gimelshein, N. (2018). Online Normalizer Calculation for Softmax.
