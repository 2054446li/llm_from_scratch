# 第 1 周 QA 题库：Transformer 架构与注意力机制

> 本文包含 45 个精心设计的问题，分为 5 个类别。请逐一回答，深入理解每个概念。
> **建议**：不要看答案提示，先独立思考 15-20 分钟，再对比参考答案。

---

## 📌 A. 概念理解题（10 题）

### A1: 注意力机制的核心目标是什么？

**参考答案框架**：
- 背景：为什么 RNN 不适合长序列
- 核心目标：让模型关注序列中最相关的位置
- 数学体现：通过相似度加权
- 与其他机制的区别

<details>
<summary>点击查看提示</summary>
考虑以下角度：
- 信息流方向（与 RNN 的差异）
- 相关性的计算方式
- 输出的含义
</details>

---

### A2: 为什么在 Attention 中使用 softmax 而不是其他归一化方式（如 ReLU、Tanh）？

**参考答案框架**：
1. softmax 的数学性质（指数函数）
2. 概率解释（和为 1）
3. 梯度性质（易于反向传播）
4. 其他方式的劣势

<details>
<summary>点击查看提示</summary>
- 指数函数如何强化高值？
- softmax 的导数是什么？
- ReLU 为什么不适合作为注意力权重？
</details>

---

### A3: Multi-Head Attention 中，每个头学习到什么？

**参考答案框架**：
1. 多头的作用（多视角）
2. 每个头可能学到的内容举例
3. 为什么需要多头而不是单头
4. 头数的选择标准

<details>
<summary>点击查看提示</summary>
- 语义关系、句法结构、指代关系
- 参数量与多头数量的关系
- 实际模型中的头数选择
</details>

---

### A4: RoPE（旋转位置嵌入）如何编码位置信息？

**参考答案框架**：
1. 为什么需要位置信息
2. 旋转矩阵的作用
3. 如何编码相对位置
4. 与绝对位置编码的根本区别

<details>
<summary>点击查看提示</summary>
- 旋转矩阵 R 的性质
- 为什么 Q'_m · K'_n 只依赖 m-n？
- 数学推导关键步骤
</details>

---

### A5: Flash Attention 解决了什么问题？为什么能加速？

**参考答案框架**：
1. 标准 Attention 的瓶颈
2. Flash Attention 的核心思想
3. 如何减少内存访问
4. 为什么计算结果完全相同

<details>
<summary>点击查看提示</summary>
- 计算密度 vs 内存访问延迟
- IO-aware 算法的概念
- 块状处理和在线 softmax
</details>

---

### A6: Transformer 的 Attention 是置换不变的，这意味着什么？

**参考答案框架**：
1. 置换不变的定义
2. 为什么这是个问题
3. 置换不变性对序列的影响
4. 如何解决（位置编码）

<details>
<summary>点击查看提示</summary>
- 改变输入顺序后，输出也改变顺序吗？
- 具体例子："猫咬狗" vs "狗咬猫"
</details>

---

### A7: 为什么需要除以 √d_k 这个因子？

**参考答案框架**：
1. 不缩放的问题（方差分析）
2. √d_k 的来源（统计学）
3. 为什么选择 √d_k 而不是 d_k 或 d_k²
4. 缩放后的效果

<details>
<summary>点击查看提示</summary>
- Q 和 K 的元素方差是多少？
- QK^T 中每个元素的期望方差？
- softmax 前后的数值范围变化
</details>

---

### A8: Layer Normalization 在 Transformer 中的作用是什么？

**参考答案框架**：
1. 归一化的必要性
2. Layer Norm vs Batch Norm 的区别
3. 在 NLP 任务中的优势
4. Pre-norm vs Post-norm 的影响

<details>
<summary>点击查看提示</summary>
- 为什么 Batch Norm 不适合 NLP？
- Layer Norm 是如何计算的？
- 位置的归一化 vs 特征的归一化
</details>

---

### A9: Residual Connection（残差连接）为什么重要？

**参考答案框架**：
1. 深层网络的训练困难
2. 残差连接的数学表达
3. 梯度流的改善
4. 与恒等映射的关系

<details>
<summary>点击查看提示</summary>
- 梯度回传时的路径
- 为什么让梯度"直接通过"很重要？
- 深度和性能的关系
</details>

---

### A10: Feed Forward Network (FFN) 的作用是什么？为什么不只用 Attention？

**参考答案框架**：
1. Attention 的限制（线性聚合）
2. FFN 提供的功能（非线性变换）
3. FFN 的典型结构（两层，中间扩展）
4. Attention + FFN 的互补性

<details>
<summary>点击查看提示</summary>
- Attention 的输出是 V 的线性组合
- 为什么需要非线性？
- 典型的 FFN 维度选择（d_model -> 4*d_model -> d_model）
</details>

---

## 📊 B. 对比分析题（10 题）

### B1: RoPE vs ALiBi vs 绝对位置编码，各自的优劣？

**详细对比表**：
- 参数数量
- 可外推性
- 计算效率
- 实际效果
- 适用场景

<details>
<summary>点击查看提示</summary>
- 绝对编码外推性差的原因
- ALiBi 为什么能处理长文本？
- RoPE 的相对位置属性
</details>

---

### B2: Multi-Head Attention vs Single-Head Attention，何时选择哪个？

**对比维度**：
1. 参数量与计算量
2. 学习能力
3. 计算效率
4. 实际性能差异

<details>
<summary>点击查看提示</summary>
- 总参数量是否真的增加了？
- 多头如何改善学习能力？
- GPU 并行处理的优势
</details>

---

### B3: GQA vs MQA vs 标准 Multi-Head Attention，在推理时的权衡？

**对比角度**：
1. KV 缓存大小
2. 计算复杂度
3. 模型性能
4. 推理延迟

<details>
<summary>点击查看提示</summary>
- KV 缓存与哪个维度有关？
- MQA 为什么性能下降？
- GQA 如何平衡权衡？
</details>

---

### B4: Transformer Encoder vs Decoder 的主要区别？

**对比内容**：
1. Self-Attention 的差异
2. 是否有交叉注意力
3. 因果性考虑
4. 使用场景

<details>
<summary>点击查看提示</summary>
- Encoder 可以看到所有 token，Decoder 呢？
- 因果掩码的作用
- Cross-Attention 的目标
</details>

---

### B5: Flash Attention vs 标准 Attention 的主要差异？

**对比角度**：
1. 算法差异
2. 计算结果
3. 内存占用
4. 运行时间
5. 精度影响

<details>
<summary>点击查看提示</summary>
- 计算过程是否改变？
- 数值精度是否保证？
- IO 操作如何优化？
</details>

---

### B6: 因果掩码 vs 双向 Attention 的含义和影响？

**对比分析**：
1. 数学表达
2. 信息流方向
3. 训练 vs 推理的差异
4. 应用场景

<details>
<summary>点击查看提示</summary>
- 因果掩码如何实现？
- 为什么生成时需要因果掩码？
- 预训练时可以不用吗？
</details>

---

### B7: 不同的 Token 化方法（BPE、WordPiece、SentencePiece）有何区别？

**对比维度**：
1. 分割策略
2. 词表大小
3. 未登录词处理
4. 多语言支持

<details>
<summary>点击查看提示</summary>
- 字节级 vs 词级
- 合并策略如何实现？
- 语言适配性的差异
</details>

---

### B8: Pre-Norm vs Post-Norm 架构的影响？

**对比内容**：
1. 位置差异（图示）
2. 梯度流的区别
3. 模型的稳定性
4. 性能表现

<details>
<summary>点击查看提示</summary>
```
Post-Norm: x -> Attn -> + -> LayerNorm -> ...
Pre-Norm:  x -> LayerNorm -> Attn -> + -> ...
```
- 哪个更稳定？
- 哪个更深？
</details>

---

### B9: Attention Bias（偏置项）的作用？

**对比分析**：
1. 有偏置 vs 无偏置
2. 不同偏置的效果（ALiBi 等）
3. 计算成本
4. 性能影响

<details>
<summary>点击查看提示</summary>
- ALiBi 的偏置如何计算？
- T5Bias 是什么？
- 为什么加偏置能改善长文本能力？
</details>

---

### B10: 自注意力 vs 交叉注意力的应用场景？

**对比维度**：
1. 数据来源
2. 适用模型
3. 应用场景
4. 计算特性

<details>
<summary>点击查看提示</summary>
- 机器翻译中何处使用自注意力？何处使用交叉注意力？
- 编码器-解码器模型的结构
</details>

---

## 🔬 C. 原理推导题（10 题）

### C1: 推导 Attention 的反向传播公式

**任务**：给定前向公式，推导反向传播时的梯度流

$$\text{Output} = \text{softmax}(QK^T / \sqrt{d_k})V$$

求：$\frac{\partial L}{\partial Q}, \frac{\partial L}{\partial K}, \frac{\partial L}{\partial V}$

<details>
<summary>点击查看提示</summary>
- 使用链式法则
- softmax 的导数是什么？
- 矩阵求导的规则
</details>

---

### C2: 推导为什么 RoPE 能编码相对位置

**任务**：证明 $\text{RoPE}(m)^T \text{RoPE}(n) = \text{RoPE}(m-n)$

<details>
<summary>点击查看提示</summary>
- 旋转矩阵的性质
- 矩阵乘法的结合律
- 最终形式只依赖 m-n
</details>

---

### C3: 分析多头注意力的参数量

**任务**：
1. 标准单头 Attention 的参数量
2. 多头 Attention 的总参数量
3. 为什么总量不变？

<details>
<summary>点击查看提示</summary>
$$\text{Params}_{single} = 3d \times d = 3d^2$$
$$\text{Params}_{multi} = h \times (3 \times d/h \times d/h) \times W^O = ?$$
</details>

---

### C4: 推导缩放因子 √d_k 的必要性

**任务**：
1. Q 和 K 的元素分布假设
2. QK^T 的方差计算
3. 缩放后的方差
4. softmax 稳定性的影响

<details>
<summary>点击查看提示</summary>
- 假设 Q, K 的元素均值为 0，方差为 1
- E[QK^T_ij] = E[Σ_k Q_ik * K_jk]
- Var[QK^T_ij] = d_k (如果独立)
- softmax 前后的梯度变化
</details>

---

### C5: 推导 Layer Normalization 的计算公式

**任务**：
1. 写出 Layer Normalization 的完整公式
2. 与 Batch Normalization 的区别
3. 为什么适合 NLP

$$\text{LayerNorm}(x) = \gamma \odot \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} + \beta$$

其中 $\mu, \sigma^2$ 是什么的统计量？

<details>
<summary>点击查看提示</summary>
- 是对序列维度还是特征维度？
- Batch Norm 的选择？
- NLP 中序列长度可变的问题
</details>

---

### C6: 分析 Transformer 的计算复杂度

**任务**：
1. 每个 Attention 层的时间复杂度
2. 每个 FFN 层的时间复杂度
3. N 层 Transformer 的总复杂度
4. 与 RNN 的对比

<details>
<summary>点击查看提示</summary>
- Attention: QK^T (n² d) + softmax (n²) + A*V (n² d)
- FFN: 每位置独立，线性复杂度
- 总计: O(Nn²d) vs RNN O(Nnd)
</details>

---

### C7: 推导因果掩码的数学表达

**任务**：
1. 写出因果掩码矩阵（lower triangular）
2. 如何在 softmax 前应用
3. 数值上如何实现（使用 -∞）

<details>
<summary>点击查看提示</summary>
$$\text{Mask}_{ij} = \begin{cases} 0 & \text{if } i \geq j \\ -\infty & \text{if } i < j \end{cases}$$
- 在 softmax 前相加
- e^(-∞) = 0
</details>

---

### C8: 推导 Multi-Head 的输出形状变化

**任务**：
追踪张量形状的变化过程

```
Input: (batch, seq_len, d_model)
     ↓ Linear Proj
(batch, seq_len, d_model) -> 分成 h 头
     ↓
(batch, h, seq_len, d_k) 每个头
     ↓ Attention 计算
(batch, h, seq_len, d_k)
     ↓ Concatenate
(batch, seq_len, d_model)
     ↓ Output Proj
Output: (batch, seq_len, d_model)
```

验证每个步骤的维度

<details>
<summary>点击查看提示</summary>
- d_k = d_model / h
- Concat 如何工作？
- Output Proj 的参数矩阵大小
</details>

---

### C9: 推导 GQA 相比标准 Attention 的 KV 缓存节省

**任务**：
1. 标准 Attention 的 KV 缓存大小
2. GQA 的 KV 缓存大小
3. 计算节省比例

<details>
<summary>点击查看提示</summary>
标准: batch * seq_len * num_heads * head_dim
GQA (num_kv_heads < num_heads):
batch * seq_len * num_kv_heads * head_dim
节省: num_heads / num_kv_heads 倍
</details>

---

### C10: 推导 Flash Attention 的 IO 复杂度改进

**任务**：
1. 标准 Attention 的 IO 操作次数
2. Flash Attention 的 IO 操作次数
3. 加速比的理论分析

<details>
<summary>点击查看提示</summary>
- 标准：读 QK (n²d) + 读 V (n²d) + 写输出 (n²d)
- Flash：块状处理，减少重复读写
- 利用片上内存（SRAM）的高带宽
</details>

---

## ⚙️ D. 实践问题题（8 题）

### D1: 如何在代码中选择位置编码方式？

**实际考虑**：
1. 模型大小与数据量
2. 要处理的最大序列长度
3. 是否需要泛化到更长序列
4. 计算资源约束

**场景分析**：
- 小模型，固定长度序列 → ?
- 大模型，需要处理变长序列 → ?
- 需要处理超长文本（32K+） → ?

<details>
<summary>点击查看提示</summary>
- 绝对编码：简单快速，但外推性差
- RoPE/ALiBi：现代选择，外推性强
- 成本与收益的权衡
</details>

---

### D2: 如何调整 Transformer 的深度和宽度？

**实际问题**：
- 模型大小 = 深度 × 宽度 × 头数
- 如何在有限资源下最大化性能？

**典型配置**：
| 模型 | d_model | num_heads | num_layers | FFN_dim |
|-----|---------|-----------|------------|---------|
| 小  | 768 | 12 | 12 | 3072 |
| 中  | 1024 | 16 | 24 | 4096 |
| 大  | 2048 | 32 | 48 | 8192 |

**问题**：
1. 为什么 FFN_dim 通常是 4*d_model？
2. 如何在深度和宽度间权衡？
3. 性能和参数数量的关系？

<details>
<summary>点击查看提示</summary>
- 计算量主要在 Attention 和 FFN
- 深度决定接受域
- 宽度决定表达能力
</details>

---

### D3: 如何诊断和解决 Attention 的数值不稳定问题？

**常见问题**：
1. 注意力权重完全集中在某一位置
2. 注意力权重均匀分布（无区分）
3. 梯度消失或爆炸

**诊断方法**：
- 监控 softmax 前的分数分布
- 观察注意力权重的熵
- 检查梯度的大小

**解决方案**：
1. 调整温度因子（softmax 前乘以/除以常数）
2. 检查初始化策略
3. 使用混合精度训练

<details>
<summary>点击查看提示</summary>
- 注意力权重集中 → 分数差异太大 → 缩放不足
- 权重均匀 → 分数都接近 0 → 缩放过度
- 梯度不稳定 → 学习率调整、初始化改进
</details>

---

### D4: 如何优化推理时的 Attention 计算？

**KV 缓存的管理**：
1. 预分配缓存大小
2. 只计算新 token 对所有 KV 的 Attention
3. 使用 GQA 减少缓存

**并发处理**：
1. 批处理多个请求
2. 动态批处理的实现
3. 避免缓存碎片

**加速方法**：
1. 量化（INT8、INT4）
2. 页式 Attention（类似虚拟内存）
3. 投机解码

<details>
<summary>点击查看提示</summary>
- 前向传递期间，只有当前 token 是新的
- 之前的 token 的 Attention 已经计算过
- 如何利用这个特性？
</details>

---

### D5: 如何在数据有限的情况下训练 Transformer？

**数据增强**：
1. 回译（Back-translation）
2. 降噪
3. 掩码语言建模

**正则化技术**：
1. Dropout（应用在哪些位置？）
2. Weight Decay
3. Layer Dropout

**微调技巧**：
1. 学习率选择
2. 预热（Warmup）策略
3. 提前停止

<details>
<summary>点击查看提示</summary>
- Dropout 在 Attention 后、FFN 后应用
- 为什么需要预热？
- 小数据集时的过拟合问题
</details>

---

### D6: 如何处理超长序列的 Attention 计算？

**方案 1：局部 Attention（Local Attention）**
- 只计算窗口内的 Attention
- 时间复杂度：O(n * w²)，其中 w 是窗口大小
- 缺点：全局信息丢失

**方案 2：稀疏 Attention（Sparse Attention）**
- 只计算特定位置对的 Attention
- 模式：块、条纹、混合等
- 实现复杂，但计算量减少显著

**方案 3：低秩近似（Low-Rank Approximation）**
- 用低秩矩阵近似 Attention 矩阵
- 基于核方法或随机投影

**方案 4：递归结构**
- 分块处理，递归聚合

<details>
<summary>点击查看提示</summary>
- 权衡：准确性 vs 计算效率
- 不同方案的应用场景
- 与长文本位置编码的结合
</details>

---

### D7: 如何评估 Attention 头的重要性？

**诊断方法**：

1. **注意力权重分析**
   - 是否有冗余的头（权重分布相似）
   - 是否有病态的头（权重完全集中或均匀）

2. **梯度贡献**
   - 计算每个头的梯度范数
   - 低梯度 = 低贡献度

3. **消融实验**
   - 移除单个头，观察性能下降
   - 计算重要性分数

4. **表示学习分析**
   - 每个头学到的特征是什么？
   - 不同头间的互补性

**应用**：
- 模型剪枝（移除低重要性的头）
- 知识蒸馏（优先保留重要的头）

<details>
<summary>点击查看提示</summary>
- 可视化注意力权重
- 分析头部分布的多样性
- 计算特征的相似度
</details>

---

### D8: 实现一个高效的 Masked Multi-Head Attention 模块

**要求**：
1. 支持因果掩码
2. 支持自定义掩码
3. 与 Flash Attention 兼容
4. 支持 GQA（可选）

**关键设计点**：
1. 如何应用掩码（什么时候、在哪里）
2. 如何处理不同的序列长度
3. 梯度的正确流向
4. 与 KV 缓存的交互

<details>
<summary>点击查看提示</summary>
- 掩码在 softmax 前应用
- 考虑 batch 维度的处理
- 注意数值稳定性（-inf 的处理）
</details>

---

## 🌟 E. 前沿进展题（7 题）

### E1: Flash Attention v2 相比 v1 有哪些改进？

**主要改进**：
1. 工作分分割的优化
2. warp-level 的并行化
3. 块大小的自适应选择
4. 更好的内存层次利用

**性能提升**：
- 相比 v1：2-3 倍加速
- 内存占用进一步减少

<details>
<summary>点击查看提示</summary>
- v1 的瓶颈是什么？
- v2 如何克服这些瓶颈？
- GPU 架构特性的利用
</details>

---

### E2: 最新的高效 Attention 方法有哪些？

**方案汇总**：
1. **Flash Attention** 系列 - IO 优化
2. **页式注意力（Paged Attention）** - 内存管理
3. **多查询注意力（GQA/MQA）** - KV 缓存优化
4. **核方法（Kernel-based）** - 数学替代
5. **稀疏注意力（Sparse Attention）** - 选择性计算

**对比与应用**：
- 各方法的权衡
- 可以组合使用吗？
- 实际部署中的选择

<details>
<summary>点击查看提示</summary>
- 这些方法是否互斥？
- 如何在实际系统中组合？
- 性能收益与复杂度的平衡
</details>

---

### E3: 长文本 Attention 的最新进展（如 LongContext, Structured State Spaces 等）

**新方法**：
1. **分段递归处理**
   - 将长序列分段处理
   - 递归地聚合信息

2. **状态空间模型（SSM）**
   - Mamba 等模型
   - 参数化的状态转移
   - 线性复杂度

3. **混合注意力**
   - 组合不同类型的注意力
   - 全局 + 局部

4. **位置插值（Position Interpolation）**
   - 在预训练上下文外推到更长序列
   - 旋转角度缩放

**比较与选择**：
- 精度与速度的权衡
- 对不同任务的适用性

<details>
<summary>点击查看提示</summary>
- 为什么状态空间模型能达到线性复杂度？
- 与 Attention 的本质区别
- 在长文本上的实际表现
</details>

---

### E4: 多模态 Attention（如 Vision Transformer, ViT）的特点

**特点分析**：
1. **Patch 嵌入**
   - 将图像分块
   - 每块作为一个 token

2. **2D 位置编码**
   - 如何编码 2D 位置？
   - 学习 vs 固定编码

3. **Hybrid 方法**
   - 结合 CNN 和 Attention
   - 何时混合最有效

4. **跨模态 Attention**
   - 图像-文本融合
   - 对齐机制

<details>
<summary>点击查看提示</summary>
- ViT 为什么分块？
- 位置编码对 2D 数据的处理
- 与 CNN 的计算量对比
</details>

---

### E5: 条件 Attention（如 Conditional Computation）的应用

**概念**：
- 根据输入动态选择计算
- 不是所有 token 都参与完整计算

**实现方式**：
1. **路由机制**
   - 哪些 token 对相互重要
   - 跳过不重要的计算

2. **MoE（混合专家）**
   - 不同专家处理不同 token
   - 动态路由

3. **自适应计算**
   - 基于置信度决定计算量
   - 动态推理

**优势与挑战**：
- 计算效率提升
- 实现复杂性
- 训练难度

<details>
<summary>点击查看提示</summary>
- 如何决定哪些对需要计算？
- 梯度如何通过路由机制？
- 与稀疏注意力的区别
</details>

---

### E6: Transformer 的理论分析进展

**理论问题**：
1. **表达能力**
   - Transformer 能表示什么函数类？
   - 与 MLP 的对比

2. **优化景观**
   - 为什么 Transformer 易于训练？
   - 梯度流的理论分析

3. **泛化性**
   - 为什么预训练能泛化到下游任务？
   - 需要多少样本？

4. **缩放律**
   - 模型规模与性能的关系
   - 计算最优的设置

<details>
<summary>点击查看提示</summary>
- Transformer vs RNN 的理论优劣
- 大模型缩放律的启示
- 过度参数化的优势
</details>

---

### E7: 下一代模型架构（超越 Transformer）的探索

**前沿方向**：
1. **状态空间模型（Mamba, S4）**
   - 线性复杂度
   - 参数化状态转移

2. **混合架构**
   - 结合 Attention 和递归
   - 各取所长

3. **图神经网络**
   - 处理结构化数据
   - 与 Attention 的关系

4. **新的基础操作**
   - 替代矩阵乘法
   - 更高效的聚合

**评估标准**：
- 理论效率
- 实际运行速度
- 泛化能力
- 易实现性

<details>
<summary>点击查看提示</summary>
- Transformer 的本质瓶颈是什么？
- 下一代模型需要解决什么问题？
- 如何验证新架构的有效性？
</details>

---

## 📝 自我评估

完成所有问题后，进行以下自我测试：

### 知识理解深度测试

1. **能否用图表解释 Multi-Head Attention 的完整计算过程？**
2. **能否推导出 RoPE 编码相对位置的数学原理？**
3. **能否对比 5 种位置编码方式的优劣？**
4. **能否解释 Flash Attention 如何减少 IO 操作？**
5. **能否从梯度流的角度解释残差连接的重要性？**

### 实践应用测试

1. **给定一个模型配置，能否计算其参数量和计算复杂度？**
2. **面对一个 Attention 数值不稳定问题，能否诊断和解决？**
3. **能否设计一个高效的长序列 Attention 方案？**
4. **能否对比不同模型的 Attention 实现细节？**

### 前沿知识测试

1. **能否解释 3 种最新的高效 Attention 方法？**
2. **能否讨论 Transformer 的理论属性和局限？**
3. **能否预测下一代模型架构的发展方向？**

---

**🎯 当你能够独立回答所有问题，并能用自己的语言清晰地解释各个概念时，说明你已经掌握了 Transformer 的核心知识。**

**下一步**：准备面试，预期会被问到的深层问题。
