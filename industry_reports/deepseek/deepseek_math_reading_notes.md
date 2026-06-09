# DeepSeekMath 阅读笔记

> 论文：DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models
> arXiv: 2402.03300v3, 2024年4月
> 机构：DeepSeek-AI、清华、北大
> 阅读视角：**后训练工程师（Post-Training Engineer）** —— 重点放在 SFT / RL / GRPO

---

## 论文总结表格

| 维度 | 内容 |
|------|------|
| 论文标题 | DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models |
| 发表时间 | 2024年4月 |
| 研究背景 | 数学推理对 LLM 是高难任务；GPT-4 / Gemini-Ultra 闭源，开源模型差距大 |
| 核心贡献 | ① 从 Common Crawl 挖出 120B 高质量数学语料；② 提出 **GRPO**（去 Critic 的 PPO 变体）；③ 给出 SFT/RFT/DPO/PPO/GRPO 的**统一范式** |
| 方法创新（后训练） | GRPO：用**组内相对奖励**当基线，免训 Value 模型，省一半显存 |
| 关键结果 | DeepSeekMath-RL 7B 在 MATH 达 **51.7%**（self-consistency@64 达 60.9%），首个开源破 50% 的模型，接近 GPT-4 |
| 三段式 pipeline | Coder-Base-v1.5 7B →(预训练)→ Base(MATH 36.2%) →(SFT)→ Instruct(46.8%) →(RL/GRPO)→ RL(51.7%) |
| 局限性 | 几何/定理证明弱；受限于 7B 规模 few-shot 不如 GPT-4；RL 只提升 Maj@K 不提升 Pass@K（未注入新能力） |

---

## 整体 Pipeline（三段式）

```
DeepSeek-Coder-Base-v1.5 7B
   │  ① 继续预训练（500B token，其中 56% 为数学语料）   ← 背景，非重点
   ▼
DeepSeekMath-Base 7B        MATH 36.2%
   │  ② SFT（776K 数学指令样本）                      ← 后训练第一步
   ▼
DeepSeekMath-Instruct 7B    MATH 46.8%
   │  ③ RL（GRPO，144K 问题）                         ← 后训练第二步【核心】
   ▼
DeepSeekMath-RL 7B          MATH 51.7%  ★
```

**后训练贡献**：②→③ 把 MATH 从 36.2% 推到 51.7%；其中 **RL 单独贡献 +4.9pt（46.8→51.7）**，且只用 GSM8K/MATH 的 CoT 数据，就同时拉升了未训练过的域外任务（如 CMATH 84.6→88.8）。

---

## 一、SFT 阶段（②）

| 维度 | 做法 |
|------|------|
| 数据规模 | **776K** 样本，中英文混合 |
| 解答格式 | 三种：**CoT**（思维链）、**PoT**（程序思维链）、**Tool-Integrated**（工具集成推理） |
| 英文来源 | GSM8K/MATH 标注工具集成解答 + MathInstruct 子集 + Lila-OOD |
| 中文来源 | 自建 K-12 数学，76 个子主题，CoT 和工具格式双标注 |
| 训练配置 | batch 256，恒定 lr **5e-5**，仅 **500 步**，样本拼接到 4K 上下文 |

**工程要点**：
- 多解答格式混合 —— CoT 训练「推理表达」，PoT/工具训练「精确计算」，是数学 SFT 的标准配方。
- 中文数据自建，弥补了开源语料的英文偏置（论文实测中文基准因此明显领先）。

---

## 二、RL 阶段（③）—— **本笔记重点**

### 2.1 GRPO 动机：干掉 Critic

PPO 的两大痛点：
1. **Value/Critic 模型**与 Policy 同量级 → 显存、算力翻倍；
2. LLM 场景奖励通常只打在**最后一个 token** → 逐 token 价值函数难训准。

**GRPO 解法**：不要 Critic。对同一问题采样**一组（G 个）输出**，用**组内平均奖励**当基线。

流程：对问题 $q$ 采样 $G$ 个输出 → 奖励模型打分 $\{r_1, \dots, r_G\}$ → 组内归一化得优势 → 最大化 GRPO 目标。组内归一化（结果监督）：

$$\hat{A}_{i,t} = \tilde{r}_i = \frac{r_i - \mathrm{mean}(\mathbf{r})}{\mathrm{std}(\mathbf{r})}$$

### 2.2 GRPO vs PPO（面试高频，必记三差异）

| | PPO | GRPO |
|---|---|---|
| 基线 baseline | Value 模型估计 | **组内平均奖励**（去 Critic） |
| KL 位置 | 加在 reward 里（逐 token 惩罚） | **直接加进 loss**，不污染优势计算 |
| KL 估计 | 普通 | **无偏估计量**（Schulman 2020），保证恒正 |
| 额外模型 | 需 Critic（≈Policy 大小） | **无需 Critic**，省一半显存 |

GRPO 目标函数：

$$\mathcal{J}_{GRPO}(\theta) = \mathbb{E}\Bigg[\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}\sum_{t=1}^{|o_i|}\min\Big(\rho_{i,t}\,\hat{A}_{i,t},\ \mathrm{clip}(\rho_{i,t},\,1-\varepsilon,\,1+\varepsilon)\,\hat{A}_{i,t}\Big) - \beta\,\mathbb{D}_{KL}\big[\pi_\theta \| \pi_{ref}\big]\Bigg]$$

其中重要性比率 $\rho_{i,t} = \dfrac{\pi_\theta(o_{i,t} \mid q, o_{i,<t})}{\pi_{\theta_{old}}(o_{i,t} \mid q, o_{i,<t})}$。

> 直觉：奖励模型本就是在「同一问题不同回答的两两比较」上训练的，GRPO 用组内相对奖励，天然契合奖励模型的比较本质。

### 2.3 两种奖励监督粒度

- **结果监督（Outcome Supervision, OS）**：奖励只在输出末尾，整条序列所有 token 共享同一归一化奖励作优势。
- **过程监督（Process Supervision, PS）**：奖励打在**每个推理步骤末尾**；某 token 的优势 = 其**后续所有步骤**归一化奖励之和，即 $\hat{A}_{i,t} = \sum_{\mathrm{index}(j)\geq t} \tilde{r}_i^{\,\mathrm{index}(j)}$。复杂数学题更优（实验中 GRPO+PS > GRPO+OS）。

### 2.4 迭代式 RL（Algorithm 1）

奖励模型会随策略漂移而过时 → 用策略新采样**持续重训奖励模型**（带 **10% 历史数据的 replay**），再把参考模型更新为当前策略。实验显示**迭代能进一步涨点，尤其第一轮迭代提升最大**。

### 2.5 RL 训练配方（可直接复用）

| 参数 | 值 |
|------|----|
| RL 数据 | 144K（仅 GSM8K+MATH 的 CoT 问题） |
| 每题采样数 G | **64** |
| Policy lr | **1e-6** |
| Reward model lr | 2e-5（基于 Base 7B 训） |
| KL 系数 β | **0.04** |
| max length / batch | 1024 / 1024 |
| 更新节奏 | 每个探索阶段后**只更新一次**（接近 on-policy） |

---

## 三、统一范式（Discussion 5.2，后训练工程师的认知框架）★

论文把所有训练方法的梯度统一写成：

$$\nabla_\theta \mathcal{J}_{\mathcal{A}}(\theta) = \mathbb{E}_{\underbrace{(q,o)\sim \mathcal{D}}_{\text{数据源}}}\Bigg[\frac{1}{|o|}\sum_{t=1}^{|o|}\underbrace{GC_{\mathcal{A}}(q,o,t,\pi_{rf})}_{\text{梯度系数}}\ \nabla_\theta \log \pi_\theta(o_t \mid q, o_{<t})\Bigg]$$

**三个关键组件**（统一 SFT / RFT / DPO / Online RFT / PPO / GRPO）：

| 方法 | 数据源 | 奖励函数 | 梯度系数特点 |
|------|--------|----------|--------------|
| SFT | 人工标注 | 无 | 恒为 1 |
| RFT | SFT模型采样+规则过滤（**离线**） | Rule | 对正确答案均匀强化 |
| DPO | SFT模型采样的成对数据（**离线**） | Rule | pairwise 偏好 |
| Online RFT | **实时策略**采样+规则（**在线**） | Rule | 正确答案均匀强化，**不惩罚错误** |
| PPO | 实时策略采样（**在线**） | **Model** | 按奖励值差异化强化/惩罚 |
| GRPO | 实时策略采样 G 个（**在线**） | **Model** | **按奖励值 + 步级**差异化（最细粒度） |

**三条核心实验结论**：
1. **在线 > 离线**：Online RFT 显著优于 RFT。早期二者接近（策略≈SFT），后期策略漂移大，实时采样优势凸显 → **on-policy 数据更值钱**。
2. **差异化梯度系数 > 均匀强化**：GRPO 用奖励模型的连续分值做差异化强化（还惩罚错误），优于 Online RFT 的「正确答案一刀切」。
3. **过程监督 > 结果监督**：GRPO+PS > GRPO+OS，细粒度步级信号更有效。

---

## 四、RL 为什么有效？（Discussion 5.2.2）★★ 后训练核心洞察

实验对比 SFT 模型 vs RL 模型的 **Pass@K** 与 **Maj@K**（K=候选数）：

> **RL 提升 Maj@K，但几乎不提升 Pass@K。**

含义（极其重要的后训练认知）：
- **Pass@K**（K 次里至少 1 次对）几乎不变 → RL **没有注入新能力 / 新知识**，模型的「能力上界」由 SFT/预训练决定。
- **Maj@K**（多数投票）提升 → RL 把**已有的正确答案在分布里排得更靠前**，让输出分布更鲁棒。

> 一句话：**RL 的本质是「对齐 / 分布锐化」，不是「能力注入」**。它纠正的是 SFT 模型的 **misalignment**（正确答案存在但概率不够高）。这与「弱到强对齐」「偏好对齐能提升推理」的研究一脉相承。

---

## 五、如何做更有效的 RL？（Discussion 5.2.3，未来方向）

按统一范式的三组件给出方向：

| 组件 | 现状局限 | 未来方向 |
|------|----------|----------|
| **数据源 Data Source** | 只用了 SFT 阶段的问题 + 朴素 nucleus 采样 → 只提升 Maj@K | OOD 问题 prompt；**树搜索等高级解码**；高效推理（提升策略探索效率） |
| **算法 Algorithm** | 完全 TRUST 奖励信号；但奖励永远不可能 100% 可靠（PRM800K 这种精标数据集仍有 ~20% 误标） | 对**噪声奖励鲁棒**的算法；**weak-to-strong** 对齐 |
| **奖励函数 Reward Function** | 神经奖励模型泛化有限 | ① 提升奖励模型**泛化**（应对 OOD）；② 表达**不确定性**（连接 weak-to-strong）；③ 高效构建高质量**过程奖励模型 PRM** |

---

## 六、对后训练工程师的 takeaway

1. **GRPO = 去 Critic 的 PPO**：省一半显存、工程更简单，是后续 DeepSeek-R1 等推理模型 RL 的基石 —— 公式与「三大差异」必须吃透。
2. **KL 放 loss 而非 reward** + **无偏 KL 估计**：稳定训练的小而关键改动。
3. **on-policy > off-policy，差异化梯度 > 均匀强化，过程监督 > 结果监督**：统一范式给出的三条可迁移结论。
4. **RL 只提 Maj@K 不提 Pass@K** → 后训练 RL 是「对齐 / 排序」而非「涨能力」；想提上界要回到 SFT/预训练或更强探索。
5. **奖励模型会漂移 + 会有噪声** → 迭代重训 + replay 是实战必备；噪声鲁棒与 weak-to-strong 是前沿。
6. **少量高质量 RL 数据 + 大采样数（G=64）** 即可显著泛化 → 后训练中「采样多样性/在线性 > 数据堆量」。

---

## 附：其他实验结论（预训练侧，了解即可）

- **代码训练有益数学推理**：先 code 再 math 两阶段训练，比先 general 再 math 效果好；one-stage 混训能缓解灾难性遗忘。部分回答了「code 是否提升 reasoning」—— 至少对数学是肯定的。
- **arXiv 数据意外无效**：仅用 arXiv 训练在各数学基准上无明显提升甚至退化（在本文设置与模型规模下）。
