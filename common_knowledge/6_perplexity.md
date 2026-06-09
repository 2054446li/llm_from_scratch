# Perplexity（困惑度）

## 概述

困惑度（Perplexity, PPL）是评估语言模型质量的核心指标，衡量模型对测试文本的"困惑程度"。直觉上，困惑度越低，模型对文本的预测越准确，语言建模能力越强。

## 数学定义

对于一个测试序列 $W = w_1, w_2, \ldots, w_N$，语言模型的困惑度定义为：

$$\text{PPL}(W) = P(w_1, w_2, \ldots, w_N)^{-\frac{1}{N}}$$

等价于交叉熵的指数形式：

$$\text{PPL} = 2^{H(W)} = 2^{-\frac{1}{N}\sum_{i=1}^{N}\log_2 P(w_i | w_1, \ldots, w_{i-1})}$$

或使用自然对数：

$$\text{PPL} = \exp\left(-\frac{1}{N}\sum_{i=1}^{N}\ln P(w_i | w_1, \ldots, w_{i-1})\right)$$

## 直觉理解

- **PPL = 1**：模型完美预测每个 token，毫无困惑
- **PPL = V**（V 为词表大小）：等同于均匀随机猜测
- **PPL = 10**：平均而言，模型在每个位置"犹豫"于 10 个等可能的选项

## 与交叉熵和 BPB 的关系

| 指标 | 公式 | 说明 |
|------|------|------|
| 交叉熵 (CE) | $H = -\frac{1}{N}\sum \log_2 P(w_i \mid \text{context})$ | 每 token 平均信息量 (bits/token) |
| 困惑度 (PPL) | $\text{PPL} = 2^H$ | 交叉熵的指数形式 |
| Bits-per-byte (BPB) | $\text{BPB} = \frac{\text{CE (nats)} \times N_{tokens}}{N_{bytes} \times \ln 2}$ | 每字节平均比特数，跨分词器可比 |

**DeepSeek LLM 论文中使用 BPB 而非 PPL**，因为 BPB 不受分词器影响，更适合跨模型比较。

## 计算方式

### Token 级别计算（最常见）

```python
import torch

# logits: [batch, seq_len, vocab_size]
# labels: [batch, seq_len]
loss_fn = torch.nn.CrossEntropyLoss()
loss = loss_fn(logits.view(-1, vocab_size), labels.view(-1))
perplexity = torch.exp(loss)
```

### 基于困惑度的多选题评估

DeepSeek LLM 论文中对选择题的评估方法：

1. 对每个候选选项，计算模型在给定题目条件下生成该选项的困惑度
2. 选择困惑度最低的选项作为模型预测
3. 归一化方式：
   - **长度归一化**：除以 token 数，避免短选项天然有优势
   - **无条件归一化**：减去选项在无条件下的 log 概率（用于 ARC、OpenBookQA）

### 滑动窗口计算（长文本）

对于超过模型上下文窗口的长文本：
1. 使用固定步长的滑动窗口
2. 每次仅计算窗口内新增部分的 loss
3. 拼接所有窗口的结果计算整体 PPL

## 使用注意事项

| 注意点 | 说明 |
|--------|------|
| 不可跨分词器比较 | 不同分词器切分的 token 数不同，PPL 不可直接比较 |
| BPB 可跨模型比较 | 归一化到字节级别，消除分词器差异 |
| 训练集越大 PPL 越低 | 不代表模型真的更好，可能是记忆 |
| PPL 低 ≠ 生成质量高 | PPL 衡量预测准确性，不直接反映对话/推理能力 |

## 在模型评估中的角色

- **预训练阶段**：PPL/BPB 是核心优化指标，用于缩放定律拟合和性能预测
- **SFT/RLHF 阶段**：PPL 不再是主要指标，转向任务准确率和人类偏好
- **模型选择**：PPL 可作为快速筛选手段，但最终需结合下游任务表现

## 参考文献

- Bengio, Y., et al. (2003). A Neural Probabilistic Language Model.
- Meister, C., & Cotterell, R. (2021). Language Model Evaluation Beyond Perplexity.
