# KV Cache（键值缓存）

> LLM 推理优化的核心概念，理解一切注意力压缩技术（MQA/GQA/MLA）、量化、PagedAttention 的前置基础。
> 后训练关联：RL rollout / 在线采样的吞吐瓶颈往往就是 KV 缓存的显存占用，直接决定能开多大 batch。

## 概述

KV Cache 是自回归生成时**缓存历史 token 的 Key 和 Value**，避免每生成一个新 token 都重算前文，从而把生成复杂度从 $O(n^2)$ 每步降到 $O(n)$ 每步。代价是**显存占用随序列长度和 batch 线性增长**，成为长文本/大并发部署的头号瓶颈。

## 为什么需要（动机）

自回归生成逐 token 进行。生成第 $t$ 个 token 时，注意力需要当前 query 与**前面所有 token 的 K、V** 做交互：

$$\text{Attention}(\mathbf{q}_t, \mathbf{K}_{1:t}, \mathbf{V}_{1:t}) = \sum_{j=1}^{t} \text{Softmax}_j\!\left(\frac{\mathbf{q}_t^\top \mathbf{k}_j}{\sqrt{d_h}}\right)\mathbf{v}_j$$

历史 token 的 $\mathbf{k}_j, \mathbf{v}_j$ 在后续每一步都会重复用到。若不缓存，每步都要把整段前文重新过一遍投影 → 计算量爆炸。**缓存它们，用空间换时间。**

## 显存占用

标准 MHA 每个 token、每一层需缓存 K 和 V 各一份：

$$\text{KV Cache} = \underbrace{2}_{K,V} \times n_h \times d_h \times l \times \underbrace{b \times s}_{\text{batch}\times\text{seq}} \times \underbrace{2}_{\text{bytes(fp16)}}$$

其中 $n_h$ 头数、$d_h$ 每头维度、$l$ 层数、$b$ batch、$s$ 序列长度。

- 关键特性：**与 $b \times s$ 成正比**。序列越长、并发越大，缓存越爆。
- 例：DeepSeek 67B 量级，长上下文 + 大 batch 时 KV 缓存可达数十 GB，**直接限制最大 batch size 和序列长度**，是部署时比模型权重更棘手的显存压力。

## 为什么是瓶颈

| 维度 | 说明 |
|------|------|
| 显存墙 | KV 缓存与权重争抢显存；权重是固定的，KV 随负载膨胀 |
| 带宽瓶颈 | decode 阶段是 **memory-bound**——每步都要把整个 KV 缓存从显存读出，算力闲置、带宽打满 |
| 限制并发 | 缓存越大，能同时服务的请求（batch）越少，吞吐越低 |

## 主流优化方向

| 方向 | 代表方法 | 思路 | 代价 |
|------|----------|------|------|
| **减少 KV 头数** | MQA | 所有 query 头共享 1 组 KV | 掉点明显 |
| | GQA | query 头分组，每组共享 1 组 KV | 折中，主流 |
| **低秩压缩** | **MLA** | 把 KV 联合压成低维潜在向量，推理靠矩阵吸收不解压 | 几乎无损甚至涨点（见 [[12_mla]]） |
| **量化** | KV Cache 量化 | 把缓存元素从 fp16 降到 8/6/4-bit | 轻微精度损失 |
| **显存管理** | PagedAttention (vLLM) | 像 OS 分页一样管理 KV 显存，消除碎片 | 实现复杂 |
| **稀疏/淘汰** | H2O、StreamingLLM | 只保留重要/近期 token 的 KV | 可能丢远距离信息 |

## 与相关概念对比

| 概念 | 关注点 | 与 KV Cache 关系 |
|------|--------|------------------|
| FlashAttention | **训练/prefill** 阶段的注意力计算加速（IO 感知） | 互补：FA 优化算，KV Cache 优化存（见 [[4_flash_attention]]） |
| MQA/GQA/MLA | **减小 KV Cache 大小** | 都是 KV Cache 的压缩方案 |
| 量化 | 减小每个元素的比特数 | KV Cache 的正交优化 |

## 在大模型中的应用

- 几乎所有自回归 LLM 推理框架（vLLM、TensorRT-LLM、SGLang）都以 KV Cache 管理为核心。
- DeepSeek-V2 用 **MLA** 把 KV 缓存砍 **93.3%**，再叠加 **6-bit 量化**，使生成吞吐达 DeepSeek 67B 的 **5.76×**。
- 长上下文（128K）场景下，KV Cache 优化是可行性的前提——否则显存根本放不下。

## 参考文献

- Shazeer, *Fast Transformer Decoding: One Write-Head is All You Need*（MQA）, 2019.
- Ainslie et al., *GQA: Training Generalized Multi-Query Transformer Models*, 2023.
- Kwon et al., *Efficient Memory Management for LLM Serving with PagedAttention*（vLLM）, 2023.
- DeepSeek-AI, *DeepSeek-V2 Technical Report*, 2024.

## 相关知识点

- [[12_mla]] — 多头潜在注意力，KV Cache 压缩的 SOTA 方案
- [[4_flash_attention]] — 注意力计算加速（与 KV Cache 互补）
