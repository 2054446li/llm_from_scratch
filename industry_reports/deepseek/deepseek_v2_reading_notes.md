# DeepSeek-V2 阅读笔记

> 论文：DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model
> arXiv: 2405.04434v5, 2024年6月
> 机构：DeepSeek-AI
> 阅读视角：**后训练工程师（Post-Training Engineer）** —— 重点放在 SFT / RL / GRPO，兼顾与后训练强相关的架构（MLA）与系统技术

---

## 论文总结表格

| 维度 | 内容 |
|------|------|
| 论文标题 | DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model |
| 发表时间 | 2024年6月 |
| 研究背景 | LLM 参数越大能力越强，但训练成本与推理吞吐成为瓶颈；MHA 的 KV 缓存是推理最大障碍，传统 MoE 专家专业化不足 |
| 核心贡献 | ① **MLA**（多头潜在注意力）——低秩 KV 联合压缩，砍 93.3% KV 缓存且性能反超 MHA；② **DeepSeekMoE**——细粒度+共享专家，经济训练；③ 完整 SFT + GRPO 在线 RL 对齐 pipeline |
| 模型规模 | 总参 **236B**，每 token 激活 **21B**，上下文 **128K** |
| 方法创新（后训练） | 两阶段 RL（先推理对齐、再偏好对齐）；GRPO 去 Critic；多奖励框架（helpful+safety+rule）；在线 RL 框架（混合引擎+vLLM） |
| 关键结果 | 比 DeepSeek 67B 省 **42.5%** 训练成本、KV 缓存降 **93.3%**、生成吞吐 **5.76×**；开源最强 MoE；Chat(RL) AlpacaEval 2.0 **38.9**、MT-Bench **8.97**、AlignBench **7.91**（中文超 GPT-4-0613） |
| 局限性 | 预训练后无持续知识更新、可能幻觉；主要支持中英文，其他语言弱；存在「对齐税」（RLHF 损害 BBH 等标准基准） |
| 数据/训练 | 8.1T tokens 预训练（中文 token 比英文多 ~12%）；**预训练全程未接触 SFT 数据** |

---

## 整体 Pipeline

```
预训练基座（8.1T tokens，4K 上下文）
   │  ① YaRN 长上下文扩展（4K→128K，仅 32K 上训 1000 步）   ← 见 §1.3，长文本对齐的能力基础
   ▼
DeepSeek-V2 Base
   │  ② SFT（1.5M 数据 = 1.2M helpful + 0.3M safety，2 epoch，lr=5e-6）  ← 后训练第一步
   ▼
DeepSeek-V2 Chat (SFT)
   │  ③ RL（GRPO，在线，两阶段）                          ← 后训练第二步【核心】
   ▼
DeepSeek-V2 Chat (RL)  ★  AlpacaEval 2.0: 30.0 → 38.9
```

**后训练贡献**：②→③ 中 RL 把 AlpacaEval 2.0 从 30.0 推到 38.9，是「对齐有效性」最直观的证据；中文 AlignBench 上 Chat(RL) 超越 GPT-4-0613 与 ERNIEBot 4.0。

---

## 一、架构（与后训练相关部分）

### 1.1 MLA（多头潜在注意力）★ 核心架构创新

**目的**：减少推理时的 **KV 缓存**（不是减参数，也不是减训练激活）。这是 MLA 的整个 motivation。

**两个独立压缩，目的完全不同**（本次阅读的关键疑问，见疑问解答 Q1/Q2）：

| | 压谁 | 真正目的 | 推理时是否真解压 |
|---|------|----------|------------------|
| KV 联合压缩 | K、V | **减少推理 KV 缓存**（核心卖点） | 否（矩阵吸收） |
| Query 压缩 | Q | 减少**训练激活内存** | —（Q 不缓存） |

**KV 压缩三步**：

$$\mathbf{c}_t^{KV} = W^{DKV} \mathbf{h}_t \quad\text{（下投影，压成 } d_c=512 \text{ 维潜在向量）}$$
$$\mathbf{k}_t^{C} = W^{UK} \mathbf{c}_t^{KV} \quad\text{（上投影"修复"出 K，推理时被吸收、不真算）}$$
$$\mathbf{v}_t^{C} = W^{UV} \mathbf{c}_t^{KV} \quad\text{（上投影"修复"出 V，推理时被吸收、不真算）}$$

推理时**只缓存 $\mathbf{c}_t^{KV}$**（512 维），而非完整 K、V（$n_h \cdot d_h = 16384$ 维）。

**解耦 RoPE**：RoPE 与低秩压缩不兼容（位置相关矩阵破坏结合律，无法吸收）。解法是额外引入小维度的 query $\mathbf{q}^R$ 和**共享 key $\mathbf{k}^R$**（每头维度 $d_h^R=64$）专门承载位置信息，$\mathbf{k}^R$ 也要进缓存。最终缓存 $= (d_c + d_h^R) \cdot l$。

**KV 缓存对比**（表1）：MLA ≈ 只有 2.25 组的 GQA，但性能强于 MHA。

**MLA vs MHA 消融（附录 D，表9）—— MLA 是"免费午餐"的硬证据**：

| | Small MoE MHA | Small MoE MLA | Large MoE MHA | Large MoE MLA |
|---|---|---|---|---|
| KV Cache/token | 110.6K | **15.6K** | 860.2K | **34.6K** |
| MMLU | 48.7 | **50.0** | 57.5 | **59.0** |
| BBH | 37.9 | **39.0** | 46.6 | **50.7** |

→ 缓存只有 MHA 的 14%（小）/4%（大），**性能反而更高**。不是用性能换显存。

> **后训练意义**：MLA 让 RL rollout 阶段能用同样显存跑大得多的 batch，且基座能力没被削弱 → 直接提升 RLHF/在线 RL 的采样吞吐。

### 1.2 DeepSeekMoE

沿用 DeepSeekMoE 架构（细粒度专家切分 + 共享专家隔离）。V2 配置：除第一层外全用 MoE，每层 2 共享 + 160 路由专家，每 token 激活 6 个路由专家。详见 [[7_mixture_of_experts]]、[[8_moe_load_balance]]。

**设备受限路由（Device-Limited Routing）**：专家并行下，一个 token 的目标专家若分散在很多设备上，all-to-all 通信成本就高。V2 限制每个 token 的目标专家**最多分布在 $M$ 个设备**上（先选亲和度最高的 $M$ 个设备，再在其上做 top-K）。实测 $M \geq 3$ 时性能与不受限 top-K 基本持平。V2 取 $M=3$、$D=8$（路由专家均匀部署在 8 个设备）。

#### 三种负载均衡损失（为什么需要 + 各自治什么）

为何要管均衡：① 负载不均会导致**路由坍缩**（routing collapse）——少数专家被反复选中、其余得不到训练；② 专家并行下负载不均直接拖慢**计算效率**（快的设备等慢的）。三种损失分别约束三个层面：

| 损失 | 治理对象 | 因子 | 直觉 |
|------|----------|------|------|
| 专家级 $\mathcal{L}_{ExpBal}$ | 防路由坍缩（专家间均衡） | $\alpha_1=0.003$（**小**） | 别让少数专家垄断 |
| 设备级 $\mathcal{L}_{DevBal}$ | 多卡计算均衡 | $\alpha_2=0.05$（大） | 每张卡算量相当 |
| 通信级 $\mathcal{L}_{CommBal}$ | 多卡通信均衡 | $\alpha_3=0.02$ | 每张卡收发量相当 |

三者形式统一，都是 $\mathcal{L} = \alpha \sum_i f_i P_i$ 的结构（$f_i$ 标记"过热"程度作为信号、$P_i$ 是可导的平均门控概率提供梯度）：

- **专家级**：$f_i$ = 专家 $i$ 被选中的频率，$P_i$ = 其平均门控概率。
  $$\mathcal{L}_{ExpBal} = \alpha_1 \sum_{i=1}^{N_r} f_i P_i,\quad f_i = \frac{N_r}{K_r T}\sum_{t=1}^{T}\mathbb{1}(\text{token } t \text{ 选 expert } i),\quad P_i = \frac{1}{T}\sum_{t=1}^{T} s_{i,t}$$
- **设备级**：把专家分成 $D$ 组（每组一张卡），约束的是"每组"的平均频率与概率，粒度更粗 → 约束更松，**保住专家专业化的同时平衡算力**。
  $$\mathcal{L}_{DevBal} = \alpha_2 \sum_{i=1}^{D} f'_i P'_i,\quad f'_i = \frac{1}{|\mathcal{E}_i|}\sum_{j\in\mathcal{E}_i} f_j,\quad P'_i = \sum_{j\in\mathcal{E}_i} P_j$$
- **通信级**：设备受限路由只保证每张卡**发送**有界（最多 $MT$ 个隐藏态），但若某卡**接收**远多于其他卡，通信仍不均。该损失鼓励每卡接收约 $MT$ 个，平衡 all-to-all 的另一端。
  $$\mathcal{L}_{CommBal} = \alpha_3 \sum_{i=1}^{D} f''_i P''_i,\quad f''_i = \frac{D}{MT}\sum_{t=1}^{T}\mathbb{1}(\text{token } t \text{ 发往 device } i)$$

> **为何专家级因子最小**：专家级管得太死会强行打散路由、压制专业化（伤性能）；而设备级/通信级直接关系训练速度，可以管得相对紧。这是 [[8_moe_load_balance]] 里"专家级小、设备级大"原则的体现。

#### Token 丢弃策略（Token-Dropping）

均衡损失只是"鼓励"均衡，不能**保证**严格均衡 → 仍有计算浪费。V2 在训练时引入设备级 token 丢弃作为兜底：

1. 按平均计算预算给每张卡设**容量因子 = 1.0**；
2. 每张卡上**丢弃亲和度分数最低的 token**，直到压回预算内；
3. 但保证约 **10% 的训练序列所属 token 永不丢弃**。

意义：① 直接削减负载不均带来的计算浪费，提速；② **保证训练/推理一致性**——推理时可按效率需求灵活决定是否丢弃，且与训练行为一致。这一点对 on-policy RL 的采样正确性是隐性前提（训练和 rollout 的 token 处理方式不能错位）。

### 1.3 YaRN 长上下文扩展（4K → 128K）

预训练在 4K 上下文完成后，用 **YaRN**（Yet another RoPE extensioN）把窗口外推到 128K。完整原理见 [[11_yarn]]，这里只记 V2 相关要点。

**为什么需要**：RoPE 给不同维度施加不同频率的旋转，训练只见过 0~4K 的位置；直接外推到 100K 时旋转角度超出训练范围（位置 OOD），注意力崩坏。YaRN 用**分段插值**（高频维度保精度、低频维度做外推）+ **注意力温度缩放**（校正外推后升高的注意力熵）解决。

**V2 的具体设置**：

| 项目 | 设置 |
|------|------|
| 缩放 | $s=40$，$\alpha=1$，$\beta=32$，目标最大长度 160K |
| 温度因子 | $\sqrt{t} = 0.0707 \cdot \ln(s) + 1$（原版是 $0.1\ln s + 1$；因 MLA 注意力机制不同而重调，以最小化困惑度） |
| 作用对象 | **仅作用于解耦的共享 key $\mathbf{k}^R$** —— MLA 中只有它承载 RoPE，压缩潜在向量 $\mathbf{c}^{KV}$ 不含位置信息 |
| 微调成本 | 仅在 **32K 序列**上额外训 **1000 步**（batch 576） |
| 效果 | 128K"大海捞针"（NIAH）测试全长度表现良好（图4） |

> **与 MLA 的呼应**：标准 RoPE 作用于全部 K，而 MLA 把位置解耦到单独的 $\mathbf{k}^R$，所以 YaRN 只需调这一路 —— 这是 MLA「解耦 RoPE」设计带来的便利。
>
> **与后训练的关联**：128K 窗口是长 CoT、长文档 RLHF、多轮对齐的能力基础；YaRN 几乎免训练，是低成本撑大窗口的标准手段。

---

## 二、SFT 阶段（②）

| 维度 | 做法 |
|------|------|
| 数据规模 | **1.5M** = 1.2M helpfulness + 0.3M safety |
| 数据改进 | 提升质量以**缓解幻觉回复**、**增强写作能力** |
| 训练配置 | **2 epoch**，学习率 **5e-6** |
| 评估 | 标准基准 + IFEval（指令遵循）+ LiveCodeBench + MT-Bench/AlpacaEval/AlignBench |

**SFT 效果**：相比基座，在 GSM8K、MATH、HumanEval 上显著提升（SFT 数据含大量数学/代码）。

---

## 三、RL 阶段（③）—— **本笔记重点**

### 3.1 GRPO（组相对策略优化）

源自 DeepSeekMath，去 Critic 的 PPO 变体，对同一问题采样一组输出、用组内均值当基线。详见 [[9_grpo]]。

优势计算（结果监督）：
$$A_i = \frac{r_i - \mathrm{mean}(\{r_1,\dots,r_G\})}{\mathrm{std}(\{r_1,\dots,r_G\})}$$

> **奖励粒度**：V2 用 **结果级（outcome-level）奖励**，整条 response 一个标量，同一回复内所有 token 共享同一 advantage（见疑问解答 Q3）。**没有用过程奖励 PRM**。

### 3.2 两阶段 RL 训练策略 ★

发现：推理类数据（代码/数学）的 RL 与通用数据特性不同，数学/代码能力能在**更长训练步**中持续提升。故分两阶段：

**阶段一 · 推理对齐**：训练 $RM_{reasoning}$，奖励 $r_i = RM_{reasoning}(o_i)$。
- 代码偏好数据 = **编译器反馈**；数学偏好数据 = **真值标签**（天然 outcome 级可验证信号，即 RLVR 雏形）

**阶段二 · 人类偏好对齐**：多奖励框架
$$r_i = c_1 \cdot RM_{helpful}(o_i) + c_2 \cdot RM_{safety}(o_i) + c_3 \cdot RM_{rule}(o_i)$$
- 奖励模型用 **DeepSeek-V2 Chat (SFT) 初始化**，point-wise 或 pair-wise 损失训练

### 3.3 在线 RL 的系统工程优化（后训练系统要点）

| 优化 | 说明 |
|------|------|
| 混合引擎 hybrid engine | 训练/推理用不同并行策略，提升 GPU 利用率 |
| vLLM 推理后端 | 大 batch 加速 rollout 采样 |
| CPU offload 调度 | 模型在 CPU/GPU 间卸载/加载，平衡速度与显存 |

> 这套优化对应 §3.2.3 的高推理吞吐——**在线 RL 需训练中持续采样新数据，吞吐是实际瓶颈**。

---

## 四、关键讨论（4.4，后训练核心认知）★★

### 4.1 SFT 数据量：反驳 LIMA

LIMA 等认为 <10K SFT 数据即够，但 V2 实验：**<10K 会让 IFEval 明显下降**。结论：数据量可随模型增大而**减少，但不能消除**；SFT 质量也关键（尤其写作/开放式任务）。

### 4.2 对齐税（Alignment Tax）

RLHF 提升开放式生成，但**负面影响某些标准基准**（如 BBH）。V2 在数据处理和训练策略上努力，取得「可容忍的权衡」。「不损通用性能地对齐」是开放方向。

### 4.3 在线 vs 离线

**在线（on-policy）显著优于离线（off-policy，如 DPO）**。DeepSeek 明确押注 online RL，解释了为何在系统层面（混合引擎+vLLM）大力投入。

---

## 五、训练与推理效率（系统侧，与后训练相关）

| 指标 | DeepSeek 67B | DeepSeek-V2 |
|------|--------------|-------------|
| 训练成本（GPU 时/T token） | 300.6K | **172.8K**（省 42.5%） |
| 生成吞吐 | 基准 | **>50K tokens/s（5.76×）** |
| 部署优化 | — | FP8 + KV 缓存量化到 6-bit |

---

## 六、对后训练工程师的 takeaway

1. **完整后训练 pipeline 范本**：SFT(1.5M) → 两阶段 GRPO（推理对齐 + 偏好对齐），值得整体复用。
2. **GRPO 去 Critic** + **在线 RL**：省显存、on-policy 更值钱；配套系统优化（混合引擎/vLLM/offload）是规模化 RLHF 标配。
3. **可验证奖励（RLVR 雏形）**：代码用编译器、数学用真值——激发推理能力的关键路径。
4. **结果级奖励**：V2 用 outcome-level，未用 PRM；想做 step-level 看 DeepSeekMath/R1。
5. **对齐税真实存在**：RLHF 涨对话、可能掉 BBH，必须权衡。
6. **SFT 数据量可减不可消**：<10K 掉 IFEval，反驳「少即是多」。
7. **MLA 对后训练的间接价值**：KV 缓存降 93.3% → RL rollout 可用大 batch，基座能力还更强。
8. **训练/推理一致性**（token 丢弃策略）：on-policy RL 正确性的前提。

---

## 疑问解答（本次阅读积累的疑问）

### Q1：MLA 为什么要对 KV 压缩再"修复"？是为了减少激活内存吗？

**不是。** KV 压缩的目的是减少**推理时的 KV 缓存**（不是激活内存、不是参数量）。

- 自回归生成时，历史 token 的 K、V 要缓存以避免重算。MHA 每 token 每层缓存 $2 \cdot n_h \cdot d_h \approx 32768$ 个元素，长序列/大 batch 直接爆显存，限制最大 batch 和序列长度。
- MLA 只缓存 512 维的 $\mathbf{c}^{KV}$，而非完整 K、V。
- "减少激活内存"那套直觉用在 **Q 压缩**上才对：Q 不进缓存（每步只算当前 token），压缩 Q 纯粹为减少训练激活，对 KV 缓存无帮助。

### Q2：MLA 推理时为什么不需要把 KV 解压出来？（矩阵吸收）

因为上投影矩阵 $W^{UK}$、$W^{UV}$ 是**训练完固定不变**的权重，可靠矩阵乘法**结合律**离线折叠掉。

注意力分数（压缩/无位置部分）展开：
$$\text{score}_{ij} = (W^{UK}_i \mathbf{c}_j^{KV})^\top (W^{UQ}_i \mathbf{c}_t^Q) = (\mathbf{c}_j^{KV})^\top \underbrace{[(W^{UK}_i)^\top W^{UQ}_i]}_{\text{固定，可预先合并}} \mathbf{c}_t^Q$$

合并后公式里**只剩缓存的 $\mathbf{c}^{KV}$ 和 $\mathbf{c}^Q$**，$\mathbf{k}^C$（16384 维解压后的 K）从未被算出。即论文所说 "$W^{UK}$ can be absorbed into $W^Q$, $W^{UV}$ into $W^O$"（附录 C 原文佐证）。

**RoPE 部分例外**：$\mathbf{k}^R$ 含位置相关旋转矩阵，随位置 $j$ 变化、非固定，无法吸收（破坏结合律）。所以 MLA 额外用解耦的共享 $\mathbf{k}^R$ 承载位置，且它也要进缓存。最终缓存 $= (d_c + d_h^R) \cdot l$。

为什么 Q 不能这样省缓存：缓存对象是历史 token 的 K/V（下标 $j$ 遍历所有历史），吸收 $W^{UK}$ 直接省这部分；而 $\mathbf{c}^Q$ 只有当前 token（下标 $t$），不进缓存，对它吸收对"缓存"无意义。

### Q3：RL 时奖励是针对整个 response 还是针对 step？

**针对整个 response（结果级 / outcome-level）**，论文未用过程奖励（PRM）。

- 奖励函数自变量始终是 $o_i$（一条完整输出）：$r_i = RM_{reasoning}(o_i)$、$r_i = c_1 \cdot RM_{helpful} + c_2 \cdot RM_{safety} + c_3 \cdot RM_{rule}$。
- advantage $A_i$ 在**一组完整回复之间**做归一化（组内比较），是典型 outcome supervision。
- 同一回复内**所有 token 共享同一个 $A_i$**，整段分数平摊到每个生成步。
- 对照概念：V2 用的是 **ORM**（Outcome Reward Model），非 **PRM**（Process Reward Model，见 [[10_process_reward_model]]）。代码=编译器反馈、数学=真值标签，天然 outcome 级。
- 补充：GRPO 出处 DeepSeekMath 曾对比过 PS vs OS（且 PS 更优），但 V2 对齐部分用的是结果级。

---

## 相关知识点

- [[7_mixture_of_experts]] — MoE 总参数 vs 激活参数
- [[8_moe_load_balance]] — 专家级/设备级/通信级均衡损失
- [[9_grpo]] — GRPO 完整公式、vs PPO 三差异
- [[10_process_reward_model]] — PRM（过程奖励，V2 未用，对照概念）
- [[11_yarn]] — YaRN 长上下文扩展（V2 用其 4K→128K）
