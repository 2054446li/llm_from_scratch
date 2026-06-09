# YaRN（Yet another RoPE extensioN，RoPE 上下文窗口扩展）

> 长上下文扩展的主流方法，源自 Peng et al. (2023)。DeepSeek-V2、LLaMA 等用它把窗口从几 K 扩到 128K。前置：理解 RoPE（旋转位置编码）。
> 后训练关联：长上下文是长 CoT、长文档 RLHF / 多轮对齐的前提；YaRN 几乎免训练，是低成本撑大窗口的标准手段。

## 概述

YaRN 是一种**免训练或仅需极少量微调**就能把基于 RoPE 的模型上下文窗口**外推数十倍**的技术。它是「位置插值（PI）→ NTK-aware → YaRN」这条演进链的集大成者，核心贡献是 **NTK-by-parts 分段插值** + **注意力温度缩放** 两个创新。

一句话：**对 RoPE 的不同频率维度采取不同的插值强度，并对注意力做温度校正，从而在不破坏局部位置精度的前提下大幅外推上下文长度。**

## 为什么 RoPE 需要扩展（动机）

RoPE 对 query/key 的第 $i$ 对维度施加旋转，旋转频率为：

$$\theta_i = b^{-2i/d}, \quad i = 0, 1, \dots, d/2-1$$

其中 $b$ 是 base（常取 10000），$d$ 是每头维度。

- **高维（$i$ 大）→ 频率低 → 旋转慢 → 波长长**，编码"全局/远距离"位置。
- **低维（$i$ 小）→ 频率高 → 旋转快 → 波长短**，编码"局部/相邻"位置。

训练时模型只见过位置 $0 \sim L_{train}$（如 4K）。推理到位置 100K 时，旋转角度 $m\theta_i$ 远超训练见过的范围 → **位置分布外（OOD）**，注意力 logits 异常，性能崩坏。这就是位置外推问题。

## 三代方法演进

| 方法 | 做法 | 缺陷 |
|------|------|------|
| **位置插值 PI**（Chen et al.） | 把所有位置 $m \to m/s$（$s=L_{target}/L_{train}$），等价于所有频率统一压扁 | **高频维度被压垮**，丢失相邻 token 的精细区分能力 |
| **NTK-aware** | 不改位置而改 base：$b \to b \cdot s^{d/(d-2)}$，高频少插值、低频多插值 | 整体偏经验，分配不够精细 |
| **YaRN** | NTK-by-parts 分段 + 注意力温度缩放 | 当前主流，需引入 $\alpha,\beta,t$ 等超参 |

## 核心原理与公式

### 1. NTK-by-parts（分段插值）—— 核心创新一

按"维度的**波长** $\lambda_i = 2\pi/\theta_i$ 与上下文长度 $L$ 的关系"把维度分三类，用比值 $r_i = L / \lambda_i$（每个维度在窗口内转了几圈）判断：

- **高频维度**（$\lambda_i \ll L$，转很多圈）：**完全不插值**，保留局部位置精度。
- **低频维度**（$\lambda_i \gtrsim L$，转不到一圈）：**完全插值**，行为同 PI，负责外推。
- **中间维度**：用**斜坡函数 ramp $\gamma(r_i)$** 在两者间平滑过渡，由超参 $\alpha$、$\beta$ 控制边界：

$$\gamma(r_i) = \begin{cases} 0, & r_i < \alpha \\ 1, & r_i > \beta \\ \dfrac{r_i - \alpha}{\beta - \alpha}, & \text{otherwise} \end{cases}$$

插值后的频率是"原频率"与"PI 压扁频率"按 $\gamma$ 的混合，从而**该插值的低频插值、该保留的高频保留**。

### 2. 注意力温度缩放 —— 核心创新二

外推后序列变长，注意力分布的**熵升高**（注意力变得过于分散），损害性能。YaRN 给 softmax 前的 logits 乘以温度 $1/t$：

$$\text{softmax}\!\left(\frac{q^\top k}{t \cdot \sqrt{d}}\right)$$

工程上等价于把 $q$、$k$ 各乘 $1/\sqrt{t}$，**无需改动注意力实现**。缩放因子随外推倍数 $s$ 变化，原版 YaRN 的推荐式为：

$$\sqrt{t} = 0.1 \cdot \ln(s) + 1$$

这一步把注意力熵拉回正常水平，显著降低长序列困惑度。

## DeepSeek-V2 中的具体应用

| 项目 | 设置 / 说明 |
|------|------------|
| 窗口扩展 | 4K → 128K（目标最大长度设 160K） |
| 超参 | $s=40$，$\alpha=1$，$\beta=32$ |
| 温度因子 | 改为 $\sqrt{t} = 0.0707 \cdot \ln(s) + 1$（因 MLA 注意力机制不同，重调以最小化困惑度） |
| 作用对象 | **仅作用于解耦的共享 key $k^R$**——MLA 中只有它承载 RoPE，压缩潜在向量 $c^{KV}$ 不带位置信息 |
| 微调成本 | 仅在 **32K 序列**上额外训 **1000 步**（batch 576），即可在 128K"大海捞针"（NIAH）测试中表现良好 |

> 注意 MLA 的特殊性：标准 RoPE 作用于全部 K，而 MLA 把位置信息**解耦**到单独的 $k^R$，所以 YaRN 只需调这一路，是 MLA「解耦 RoPE」设计带来的便利。

## 优势

- **几乎免训练**：少量微调（甚至零样本）即可外推，远比从头训长上下文便宜。
- **保局部精度**：分段插值不牺牲高频维度，相邻 token 区分能力不受损。
- **困惑度低**：温度缩放校正注意力熵，长序列质量优于 PI / NTK-aware。
- **实现简单**：只改频率和一个温度标量，不动注意力主体结构。

## 与相关方法对比

| 方法 | 是否需训练 | 高频精度 | 注意力熵校正 | 外推能力 |
|------|-----------|---------|------------|---------|
| 直接外推 | 否 | — | 无 | 极差（OOD 崩坏） |
| 位置插值 PI | 需微调 | 差（被压垮） | 无 | 中 |
| NTK-aware | 可免训练 | 较好 | 无 | 中上 |
| **YaRN** | 极少微调 | **好（分段保留）** | **有** | **强** |

## 参考文献

- Peng et al., *YaRN: Efficient Context Window Extension of Large Language Models*, 2023.
- Chen et al., *Extending Context Window of Large Language Models via Positional Interpolation*（PI）, 2023.
- Su et al., *RoFormer: Enhanced Transformer with Rotary Position Embedding*（RoPE）, 2024.
- DeepSeek-AI, *DeepSeek-V2 Technical Report*, 2024（§3.1.4 Long Context Extension）.
