# MLA（多头潜在注意力，Multi-head Latent Attention）

> DeepSeek-V2 提出的注意力机制，KV Cache 压缩的 SOTA 方案。面试高频。前置：理解标准 MHA、KV Cache（[[12_kv_cache]]）、RoPE。
> 后训练关联：KV 缓存降 93.3% → RL rollout 阶段可用大得多的 batch 做在线采样，且基座能力不降反升，直接提升 RLHF 吞吐。

## 概述

MLA 通过**低秩键值联合压缩（low-rank key-value joint compression）**，把每个 token 要缓存的 K、V 压成一个低维**潜在向量（latent vector）**，从而大幅减少推理时的 KV Cache。

核心卖点：**既显著省 KV 缓存（DeepSeek-V2 降 93.3%），性能还反超标准 MHA** —— 不是用性能换显存，而是"免费午餐"。

## 解决什么问题

标准 MHA 推理时每 token 每层要缓存完整的 K、V，共 $2 n_h d_h l$ 个元素，是长上下文/大并发的头号瓶颈（见 [[12_kv_cache]]）。已有方案 MQA/GQA 靠减少 KV 头数来压缓存，但**普遍掉点**。MLA 的目标是兼得"小缓存"与"强性能"。

## 核心原理

### 1. 低秩 KV 联合压缩（省缓存的关键）

把输入 $\mathbf{h}_t$ 先**下投影**成一个低维潜在向量 $\mathbf{c}_t^{KV}$（维度 $d_c \ll n_h d_h$），需要时再**上投影**还原 K、V：

$$\mathbf{c}_t^{KV} = W^{DKV}\mathbf{h}_t \qquad (\text{压缩，}d_c=512)$$
$$\mathbf{k}_t^{C} = W^{UK}\mathbf{c}_t^{KV}, \qquad \mathbf{v}_t^{C} = W^{UV}\mathbf{c}_t^{KV}$$

**推理时只缓存 $\mathbf{c}_t^{KV}$**（512 维），而非完整 K、V（DeepSeek-V2 中 $n_h d_h = 128\times128 = 16384$ 维）。

### 2. 矩阵吸收（推理时不需真的解压）★ 最精妙处

关键洞察：上投影矩阵 $W^{UK}, W^{UV}$ 是**训练完固定不变**的权重，可借矩阵乘法**结合律**离线折叠掉。注意力分数（无位置部分）展开：

$$\text{score}_{ij} = (W^{UK}_i \mathbf{c}_j^{KV})^\top (W^{UQ}_i \mathbf{c}_t^Q) = (\mathbf{c}_j^{KV})^\top \underbrace{[(W^{UK}_i)^\top W^{UQ}_i]}_{\text{固定，可预先合并}} \mathbf{c}_t^Q$$

合并后公式里**只剩缓存的潜在向量**，$\mathbf{k}^C$（16384 维解压后的 K）**从未被算出**。即论文所说 "$W^{UK}$ can be absorbed into $W^Q$, $W^{UV}$ into $W^O$"。于是既享受小缓存，又免去每步重新解压全尺寸 KV 的开销。

### 3. 解耦 RoPE（Decoupled RoPE）—— 必要的补丁

**冲突**：RoPE 是位置相关的旋转矩阵，若施加在 $\mathbf{k}^C$ 上，会夹在 $W^Q$ 和 $W^{UK}$ 之间，而该旋转矩阵随位置变化、**不是固定的**，破坏了上面的结合律 → $W^{UK}$ 无法再吸收，每步要重算所有前缀 token 的 key，效率崩塌。

**解法**：把位置信息**解耦**出来，单独用一路承载——额外的多头 query $\mathbf{q}_t^R$ 和一个**所有头共享的 key $\mathbf{k}_t^R$**（每头维度 $d_h^R$）专门走 RoPE：

$$\mathbf{q}_{t,i} = [\mathbf{q}_{t,i}^C; \mathbf{q}_{t,i}^R], \qquad \mathbf{k}_{t,i} = [\mathbf{k}_{t,i}^C; \mathbf{k}_t^R]$$

注意力在拼接后的向量上计算。$\mathbf{k}^R$ 也要进缓存，所以**最终 KV 缓存 $= (d_c + d_h^R)\cdot l$**。

> Q 也做了低秩压缩（$\mathbf{c}_t^Q = W^{DQ}\mathbf{h}_t$），但目的不同：Q 不进缓存，压缩它只为**减少训练时的激活内存**，与省 KV 缓存无关。

## KV 缓存对比（DeepSeek-V2，表1）

| 机制 | 每 token KV 缓存 | 能力 |
|------|------------------|------|
| MHA | $2 n_h d_h l$ | 强 |
| GQA | $2 n_g d_h l$ | 中 |
| MQA | $2 d_h l$ | 弱 |
| **MLA** | $(d_c + d_h^R) l \approx \frac{9}{2} d_h l$ | **更强** |

DeepSeek-V2 设 $d_c = 4d_h$、$d_h^R = d_h/2$，缓存量 ≈ **只有 2.25 组的 GQA**，性能却强于 MHA。

## MLA vs MHA 消融（DeepSeek-V2 附录 D，实证"免费午餐"）

| | Small MoE MHA | Small MoE MLA | Large MoE MHA | Large MoE MLA |
|---|---|---|---|---|
| KV Cache/token | 110.6K | **15.6K** | 860.2K | **34.6K** |
| MMLU | 48.7 | **50.0** | 57.5 | **59.0** |
| BBH | 37.9 | **39.0** | 46.6 | **50.7** |

→ 缓存仅为 MHA 的 14%（小）/ 4%（大），**性能反而更高**。

## 与相关方法对比

| 方法 | 压缩思路 | KV 缓存 | 性能 |
|------|----------|---------|------|
| MHA | 不压 | 基准（最大） | 强 |
| MQA | 所有头共享 1 组 KV | 最小 | 掉点明显 |
| GQA | 分组共享 KV | 中 | 折中 |
| **MLA** | **低秩联合压缩 + 矩阵吸收** | 接近 GQA（2.25 组） | **强于 MHA** |

## 优势

1. **缓存小**：DeepSeek-V2 降 93.3%，长上下文与大并发可行。
2. **性能不降反升**：低秩压缩可能起到类似瓶颈正则的作用，实测优于 MHA。
3. **推理高效**：矩阵吸收使全程不解压 KV，省算又省存。
4. **训练省激活**：Q 也低秩压缩，降训练激活内存。

## 在大模型中的应用

- **DeepSeek-V2 / V3 / R1** 的核心注意力机制，是其低成本推理与长上下文（128K）能力的基石。
- 与 KV Cache 量化（6-bit）叠加，使 DeepSeek-V2 生成吞吐达 67B 的 5.76×。
- 长上下文扩展时，YaRN 只需作用于解耦的 $\mathbf{k}^R$（见 [[11_yarn]]）。

## 参考文献

- DeepSeek-AI, *DeepSeek-V2 Technical Report*, 2024（§2.1, 附录 C/D）.
- Su et al., *RoFormer: Enhanced Transformer with Rotary Position Embedding*（RoPE）, 2024.
- Ainslie et al., *GQA*, 2023；Shazeer, *MQA*, 2019.

## 相关知识点

- [[12_kv_cache]] — KV Cache 基础与各类优化方向（MLA 的问题背景）
- [[11_yarn]] — 长上下文扩展，仅作用于 MLA 解耦的 $\mathbf{k}^R$
- [[4_flash_attention]] — 注意力计算加速（与 MLA 正交）
- [[7_mixture_of_experts]] — DeepSeek-V2 的另一支柱 DeepSeekMoE
