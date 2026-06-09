# RMS Norm (Root Mean Square Layer Normalization)

## 概述

RMSNorm 是 Layer Normalization 的简化变体，去除了均值中心化步骤，仅保留缩放操作。

## 公式

$$\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum_{i=1}^{n}x_i^2 + \epsilon}} \cdot \gamma$$

其中：
- $x$ 为输入向量
- $n$ 为向量维度
- $\epsilon$ 为防止除零的小常数
- $\gamma$ 为可学习的缩放参数

## 与 Layer Norm 的对比

| 特性 | Layer Norm | RMS Norm |
|------|-----------|----------|
| 均值中心化 | 有 | 无 |
| 方差归一化 | 有 | 仅RMS |
| 可学习参数 | γ, β | 仅 γ |
| 计算开销 | 较高 | 较低 |

## 优势

1. **计算效率高**：省去均值计算和偏移参数，减少约 10-15% 的归一化计算量
2. **性能相当**：实验表明在大多数场景下与 Layer Norm 性能相当
3. **训练稳定性**：在大模型训练中表现出良好的稳定性

## 为什么 RMS Norm 有效

### 1. 归一化的核心作用是"缩放"而非"中心化"

Layer Norm 做两件事：① 减去均值（中心化）② 除以标准差（缩放）。RMSNorm 的核心洞察是：**归一化之所以有效，主要靠的是缩放（re-scaling），而非中心化（re-centering）**。

原论文通过实验证明：
- 去掉均值中心化后，模型性能几乎不变
- 去掉缩放操作后，模型性能严重下降

这说明归一化层真正防止的是激活值的**幅度爆炸/消失**，而不是分布偏移。

### 2. 隐式学习中心化

虽然 RMSNorm 没有显式的均值中心化步骤，但模型可以通过可学习参数 $\gamma$ 和后续层的权重**隐式实现中心化效果**。网络有足够的自由度自行调整分布的中心位置，不需要归一化层强制执行。



### 4. 为什么在大模型中特别有效

| 因素 | 说明 |
|------|------|
| 高维空间中均值趋于零 | 维度越高（如d=8192），随机向量的均值越接近0，中心化越冗余 |
| 计算节省在大规模下放大 | 省去均值计算 + 减少一个参数矩阵，在数十亿参数下节省可观 |
| 与Pre-Norm结构协同 | Pre-Norm中每层输入已经是残差连接的输出，分布相对稳定，中心化需求更小 |
| 并行友好 | 少一次 reduce 操作（均值计算需要全维度归约），张量并行时通信开销更小 |

### 5. 与 Pre-Norm 的协同

现代大模型普遍使用 Pre-Norm（归一化放在 Attention/FFN 之前）而非 Post-Norm：

```
Post-Norm: x + Norm(Sublayer(x))     ← 残差路径被归一化截断
Pre-Norm:  x + Sublayer(Norm(x))     ← 残差路径畅通无阻
```

Pre-Norm 保证了残差路径的梯度可以不受阻碍地回传，而 RMSNorm 作为其中的归一化操作，以最小的计算代价维持了每层输入的尺度稳定。两者组合 = 稳定训练 + 高效计算。

## 应用场景

- LLaMA、DeepSeek LLM 等主流开源大模型均采用 RMSNorm
- 通常配合 Pre-Norm 结构使用（归一化放在注意力/FFN之前）

## 实现代码

### PyTorch 基础实现

```python
import torch
import torch.nn as nn


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))  # 可学习缩放参数 γ

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, seq_len, dim]
        rms = torch.sqrt(x.pow(2).mean(dim=-1, keepdim=True) + self.eps)
        x_normed = x / rms
        return x_normed * self.weight
```

### LLaMA 官方实现（等价但数值更稳定）

```python
class LlamaRMSNorm(nn.Module):
    def __init__(self, hidden_size: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        input_dtype = hidden_states.dtype
        # 转为 float32 计算，避免 bf16/fp16 下的精度问题
        hidden_states = hidden_states.to(torch.float32)
        variance = hidden_states.pow(2).mean(-1, keepdim=True)
        hidden_states = hidden_states * torch.rsqrt(variance + self.eps)
        return self.weight * hidden_states.to(input_dtype)
```

### 对比 Layer Norm 实现

```python
class LayerNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))   # γ
        self.bias = nn.Parameter(torch.zeros(dim))    # β（RMSNorm没有这个）

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        mean = x.mean(dim=-1, keepdim=True)           # RMSNorm省去了这步
        var = x.var(dim=-1, keepdim=True, unbiased=False)
        x_normed = (x - mean) / torch.sqrt(var + self.eps)
        return x_normed * self.weight + self.bias
```

### 关键实现细节

| 细节 | 说明 |
|------|------|
| `torch.rsqrt` | 用 $1/\sqrt{x}$ 代替先 sqrt 再除，单次操作更快 |
| float32 计算 | bf16 精度不足以准确计算方差，需上转精度再转回 |
| `mean(-1, keepdim=True)` | 沿最后一维（hidden dim）计算，保持广播维度 |
| 初始化 `weight=ones` | 初始时不改变输入幅度，等价于恒等映射 |
| 无 bias 参数 | RMSNorm 去掉了 β，减少参数且不影响性能 |

### 在 Transformer 中的使用位置（Pre-Norm）

```python
class TransformerBlock(nn.Module):
    def __init__(self, dim, n_heads, ffn_dim, eps=1e-6):
        super().__init__()
        self.attn_norm = RMSNorm(dim, eps)       # attention 前的归一化
        self.ffn_norm = RMSNorm(dim, eps)        # FFN 前的归一化
        self.attn = MultiHeadAttention(dim, n_heads)
        self.ffn = FeedForward(dim, ffn_dim)

    def forward(self, x):
        # Pre-Norm: 归一化 → 子层 → 残差连接
        x = x + self.attn(self.attn_norm(x))
        x = x + self.ffn(self.ffn_norm(x))
        return x
```

## 参考文献

- Zhang, B., & Sennrich, R. (2019). Root Mean Square Layer Normalization.
