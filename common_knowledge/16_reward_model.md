# 奖励模型（Reward Model, RM）

> RLHF 的**偏好信号入口**。搞懂 RM 才知道 PPO/GRPO 到底在优化什么、为什么会被 hack。
> 前置：[[9_grpo]]（组内相对优势）、[[10_process_reward_model]]（过程奖励）、[[13_unbiased_kl_estimate]]（KL 约束）。
>
> **本笔记进度**：已依据 *RLHF Book* 第 07 章（Reward Models）+ Bradley-Terry 基础 + *Secrets of RLHF Part I*（RM 侧）+ *Constitutional AI*（§七 RLAIF）写成。
> 带 **【待补】** 标记的小节，等读完对应材料（Lilian Weng reward hacking）后再补全。

## 概述

奖励模型的任务：把**人类偏好**变成一个**可优化的标量信号** $r(x, y)$，作为 PPO/GRPO 的奖励来源。

一句话定位：RM 是 RLHF「三阶段」（SFT → RM → RL）里承上启下的一环——它把「人觉得哪个回答好」这种**离散、成对的比较**，压缩成一个**连续、可微的打分函数**，让强化学习有梯度可循。

奖励模型按**输出形式**分三大类：**判别式**（标量头，主流）、**生成式**（LLM-as-judge）、**隐式**（DPO，无独立 RM）。本章重点是判别式，尤其是 Bradley-Terry 路线。

## 一、Bradley-Terry 模型（RLHF 主流做法）

### 1.1 从偏好到概率

人类标注给出的是**成对偏好**：对同一个 prompt $x$，回答 $y_w$（winner，chosen）比 $y_l$（loser，rejected）更好，记作 $y_w \succ y_l$。

Bradley-Terry（BT）模型假设：每个回答有一个潜在「实力值」（这里就是奖励 $r$），**偏好概率由实力之差的 sigmoid 决定**：

$$
P(y_w \succ y_l \mid x) = \sigma\big(r(x, y_w) - r(x, y_l)\big) = \frac{1}{1 + e^{-(r_w - r_l)}}
$$

直觉：两个回答奖励差越大，人类越可能一致地偏好高分那个；奖励相等时概率 $=0.5$（完全随机）。

### 1.2 训练损失

对偏好数据做**最大似然**，即最大化 $P(y_w \succ y_l)$，取负对数得损失：

$$
\mathcal{L}(\theta) = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}}\Big[\log \sigma\big(r_\theta(x, y_w) - r_\theta(x, y_l)\big)\Big]
$$

纯文本形式，便于口述：

```
L = - E[ log sigmoid( r_w - r_l ) ]
```

逐项解释：
- `r_w = r_θ(x, y_w)`：RM 给 chosen 回答打的分。
- `r_l = r_θ(x, y_l)`：RM 给 rejected 回答打的分。
- `sigmoid(r_w - r_l)`：模型认为「chosen 确实更好」的概率。
- 训练目标 = 让这个概率尽量接近 1 → 即**拉大** `r_w - r_l`。

### 1.2.1 加一个 LM 模仿正则项（Secrets of RLHF 的做法）

*Secrets of RLHF Part I*（Zheng et al. 2023）在 RM 损失里额外挂了一个**语言建模（imitation）正则项**，只作用在 chosen 回答上：

$$
\mathcal{L}(\psi) = -\lambda\,\mathbb{E}_{(x, y_w, y_l)}\big[\log \sigma\big(r(x, y_w) - r(x, y_l)\big)\big] + \beta_{\text{rm}}\,\mathbb{E}_{(x, y_w)}\big[\mathcal{L}_{\text{LM}}(y_w \mid x)\big]
$$

纯文本：`L = -λ·E[ log σ(r_w - r_l) ] + β_rm·E[ LM_loss(y_w|x) ]`

- **第一项**：标准 BT 排序损失（§1.2），`λ` 是其权重。
- **第二项**：对 chosen 回答做**下一 token 预测**的语言建模损失（即让 RM 的 backbone 仍能「照着 chosen 往下写」）。
- **为什么加**：RM 从 SFT backbone 初始化，一旦只用排序损失猛训，backbone 会**过拟合到「比大小」这一件事**、丢掉语言能力，反而更容易被策略钻空子（reward hacking）。这个模仿项把 backbone 锚在语言分布附近，起**正则**作用，稳住打分泛化性。
- **与 §6 的联系**：这是从**训练侧**给 RM「保真」，和 §6.2 从**使用侧**（归一化+裁剪、KL 惩罚）压制 hacking 是一套组合拳。

### 1.3 关键性质：只学「相对分」

损失里**只出现奖励之差** `r_w - r_l`，不出现绝对值。所以：

- RM 学到的奖励可以**整体平移任意常数**而不改变损失 → 绝对数值无意义，**只有相对高低有意义**。
- 这正是为什么 RLHF 里常对奖励做**中心化/白化**（减均值、除标准差）后再喂给 PPO——绝对尺度本就是自由的。
- 也解释了 [[9_grpo]] 用「组内平均」当基线为何天然合理：既然只有相对分有意义，直接用组内相对优势 $\hat A = (r - \mathrm{mean})/\mathrm{std}$ 就够了。

## 二、RM 的网络结构

标准判别式 RM 直接**复用 SFT 模型**改造：

```
SFT 模型（去掉 LM head，即去掉 vocab 大小的输出层）
  → backbone 输出每个位置的隐状态 h_t   (hidden_dim)
  → 新接一个线性标量头 value_head: hidden_dim → 1
  → 取【最后一个 token】的标量输出，作为整条回答的奖励 r(x, y)
```

要点：
- **backbone 用 SFT 权重初始化**：已有语言理解能力，只需学「打分」这件事，比从头训省得多。
- **只加一个标量头**：参数量几乎不变，改动极小。
- **为什么取最后一个 token**：自回归模型只有读完整条回答后，最后位置的隐状态才「看全了」上下文，用它代表整条序列质量最合理。

### 与 GRPO 痛点的联系

奖励只在**最后一个 token** 上产生 → 中间每个 token 没有直接奖励信号。这导致：**逐 token 的价值/优势很难精确估计**，Critic（价值网络）难训准。

这正是 [[9_grpo]] 里指出的 PPO 工程痛点之一。GRPO 的应对：干脆不训 Critic，用**组内相对奖励**绕过逐 token 价值估计问题。

## 三、数据格式

RM 训练数据是**三元组**：

```
(prompt, chosen, rejected)   即  (x, y_w, y_l)
```

- **来源**：
  - **人工标注**（RLHF）：人读两个回答，选更好的那个。InstructGPT 是奠基。
  - **AI 反馈**（RLAIF）：用一个强模型代替人来判偏好，见下面 §六。
- **标注一致性问题**：偏好是主观的，标注者之间一致率往往只有 60–75%。一致性低 → 数据噪声大 → RM 上限受限。
- **成对 vs K-wise**：除两两比较外，也可让标注者对 $K$ 个回答排序（Plackett-Luce 模型是 BT 的多元推广），一次采集更多偏好信息。

## 四、结果奖励模型（Outcome Reward Model, ORM）

> 出自 *RLHF Book* 第 07 章，源头是 Cobbe et al. 2021（GSM8K verifier）。

### 4.1 动机：为「有客观对错」的推理任务设计

BT 模型面向**开放式偏好**（无客观对错，靠人比较）。而**数学/代码**这类推理任务有**客观对错**——最终答案要么对要么错。ORM 就是利用这个 0/1 正确标签。

数据形式：

```
(prompt, 完整解答, 标签 r ∈ {0,1})
r = 1 → 最终答案正确
r = 0 → 最终答案错误
```

书里记作一对 $(y_c, y_{ic})$（correct / incorrect），但本质是每条解答带一个 0/1 标签，**不需要 BT 那种 chosen-rejected 配对结构**。

### 4.2 核心反直觉点：逐 token 二分类，而非序列级打分

**名字里的 "outcome" 指监督信号只来自最终结果，不是指「只在最后打一个分」。** 实现上它更像语言建模：

- 对解答的**每一个 token**，模型都输出一个「这条最终会不会对」的概率 $p_\theta(s)$。
- 监督目标：把整条解答的最终标签 $r$（0 或 1）**复制到每一个 token 上**。
- prompt 部分的 token 用 `-100` mask 掉，不参与损失。

损失是**逐 token 的二元交叉熵**（following Lyu et al. 2025）：

$$
\mathcal{L}_{\text{CE}}(\theta) = -\mathbb{E}_{(s, r) \sim \mathcal{D}}\Big[r \log p_\theta(s) + (1-r)\log\big(1 - p_\theta(s)\big)\Big]
$$

纯文本：

```
L_CE = - E[ r·log p(s) + (1-r)·log(1 - p(s)) ]
```

- `r ∈ {0,1}`：这条解答最终对错标签。
- `p(s)`：模型在某 token 位置预测「这条会正确」的概率。
- `r=1` → 只剩 `-log p`，逼 p 往 1；`r=0` → 只剩 `-log(1-p)`，逼 p 往 0。

Cobbe et al. 2021 的原版还**联合语言建模目标**一起训（标量头 per-token，仅用一个 bias + 一个 gain 参数）。「Let's Verify Step by Step」（Lightman et al.）用了同类 ORM 但**去掉了 LM 那部分**，纯交叉熵。

### 4.3 三个易混边界（书里特意点出）

| 对比 | 关键区别 |
|---|---|
| **ORM vs BT** | BT：序列级、对比损失、EOS 打分。ORM：逐 token、交叉熵、更像 LM 损失。**拿「对/错」配对去训一个 BT 模型，那仍是 BT，不是 ORM**——区别在损失形式，不在数据是否有对错。 |
| **ORM vs PRM** | ORM 每个 token 都只被「**最终答案**」这一个信号监督 → **抓不到中间推理错误**（过程全错、蒙对答案照样标 1）。PRM 在**每个推理步骤末尾**给独立步骤级标签，能定位到哪一步错。详见 [[10_process_reward_model]]。 |
| **术语的坑** | 「ORM」业内用法不统一：有人严守 Cobbe 2021 原义（含 LM 联合目标），有人泛指「任何预测整条解答对错的 verifier」。 |

### 4.4 使用方式与现状

- **推理时**：取最后 token 的 $p$（或对 token 取平均）当「解答正确置信度」，经典用法是 **best-of-N**——采 N 条解答用 ORM 挑最高分。
- **现状**：ORM 的**思想（只看最终结果对错）**极其主流，其直接继承者是 **RLVR（可验证奖励）**——数学用答案匹配、代码用单测，直接给 0/1，连 RM 都不训。但 Cobbe 2021 的**具体训法**（per-token BCE + LM 头）已较少原样照抄，更多作为历史锚点。演进链：**ORM →（细粒度）PRM /（去模型）RLVR**。

## 五、生成式 RM 与隐式 RM（简述）

- **生成式 RM / LLM-as-judge**：不接标量头，让模型**用文字生成判断**（可先写 CoT 评价理由再给结论）。可解释性强、能处理复杂标准；缺点是推理慢、结论需解析、数值稳定性差。是 RLAIF 的技术基础。
- **隐式 RM（DPO 路线）**：**不训独立 RM**。DPO 证明最优策略与奖励有闭式关系 $r(x,y) = \beta \log \frac{\pi_\theta(y|x)}{\pi_{\text{ref}}(y|x)}$，直接用隐式奖励做偏好优化，省掉「先训 RM 再跑 RL」两阶段。**DPO 想干掉的正是显式 RM**（详见后续 DPO 笔记）。

## 六、reward hacking / over-optimization

一旦把 RM 分数当优化目标，它就不再是好的质量度量（**Goodhart's law**：当度量变成目标，它就不再是好度量）。策略会去钻 RM 的空子——**代理（proxy）奖励继续涨，但真实质量掉头向下**，这就是**过度优化（overoptimization）**。

常见 hacking 形态：
- **长度偏置**：RM 倾向给更长的回答打高分 → 策略学会「废话变长」刷分。为 Week 4 SimPO 长度控制埋伏笔。
- **分布外脆弱**：策略在训练中漂移到 RM 没见过的分布，RM 打分失真。

### 6.1 过度优化的缩放律（Gao et al. 2022）

> *Scaling Laws for Reward Model Overoptimization*（Gao, Schulman, Hilton, OpenAI 2022）。详细阅读笔记见 `post_training/reward_model/`。

**核心方法——合成设置**：用一个大的 **gold RM（6B）冒充「真人/真值」**，由它生成偏好标签训练 **proxy RM（3M–3B）**；proxy 被 RL/BoN 优化后，再用 gold RM 打分当「真实质量」。这样真实质量可**免费、无限测量**，才能拟合出缩放律。

**两条实证公式**（gold 分数 R 关于优化距离 $d=\sqrt{\mathrm{KL}(\pi\|\pi_{init})}$）：

$$
R_{\text{bon}}(d) = d\,(\alpha_{\text{bon}} - \beta_{\text{bon}}\, d), \qquad
R_{\text{RL}}(d) = d\,(\alpha_{\text{RL}} - \beta_{\text{RL}}\log d)
$$

纯文本：`R_bon = d·(α − β·d)`（抛物线，先升后降）；`R_RL = d·(α − β·log d)`（衰减更缓）。

- **第一项 `α·d`（收益）**：优化初期真实质量随力度线性涨；**α = 前期收益效率**。
- **第二项（惩罚，负）**：BoN 是 `−β·d²`、RL 是 `−β·d·log d`，d 大后吃掉收益，R 掉头 → 过度优化被量化；**β = RM 多容易被钻空子**。
- BoN 惩罚（d²）比 RL（d·log d）增长快 → **BoN 过度优化更快、掉得更狠**。

**关键结论（面试高频）：**

| 维度 | 结论 | 意义 |
|---|---|---|
| **RM 参数量** | RM 越大 → α↑β↓ → **越扛过度优化、峰值越高**，系数平滑可预测 | RM 大小是抗 hack 的关键杠杆 |
| **RM 数据量** | 越多越好，但 **<2000 条比较几乎无效**；稳健性由 **验证损失（val loss）** 决定，与「大模型+少数据/小模型+多数据」的组合无关；靠**数据多样性而非重复训练**（4 epoch = 1 epoch，4×数据显著更好） | 采数据先过 2000 门槛、重多样性 |
| **策略规模** | 大策略获益少，但**过度优化程度不更高**，峰值 KL 几乎相同 | 放心 scale policy，不会加剧 hack |
| **RL vs BoN** | **RL 花 KL 远多于 BoN**（BoN~log n 局部搜索，RL~步数² 每步推远）；但按 proxy 分看二者相似 | **KL 不是跨方法比较优化量的好尺子** |
| **KL 惩罚** | **KL 惩罚 ≈ 提前停止（early stopping）**，只让 gold 分更早收敛，**不改善 KL–gold 前沿** | 光靠 KL 惩罚救不了过度优化 → 动机指向换 RM/RLVR |

**最该记住的两条：**
1. **「KL 惩罚 ≈ early stopping」**：加 KL 惩罚不能真正抬高真实质量上限，只是让你早点停。→ 这解释了为什么后来要从「换掉可被 hack 的 RM」根子上解决（RLVR），而非靠 KL 打补丁。→ 联系 [[13_unbiased_kl_estimate]]。
2. **「RL 与 BoN 花 KL 的方式截然不同」**：不能用 KL 直接比较两种方法优化了多少。

### 6.2 从使用侧压制 hacking：奖励重参数化（Secrets of RLHF Part I）

> *Secrets of RLHF Part I: PPO*（Zheng et al. 2023，复旦 NLP + 字节）。系统梳理了 PPO 训练不稳的诱因，并提出 **PPO-max**（一套稳定化配方）。这里只收录**与 RM 使用直接相关**的部分——奖励怎么加工再喂给 PPO；GAE、value clipping 等 PPO 内部机制留到后续 PPO 章节。

**问题现象——pattern collapse（模式崩溃）**：策略不是真变好，而是发现了 RM 的**系统性偏置**并疯狂利用它，导致 proxy reward 飙升、真实质量崩塌。论文实证的两种典型：
- **长度偏置**：RM 偏爱长回答 → 策略输出越写越长刷分（与 §6 埋的 SimPO 长度控制伏笔同源）。
- **低困惑度偏置**：策略漂向 RM 打高分的低 perplexity 模式。

**核心手段——score reparameterization（对 RM 打分做重参数化）**，论文比较了三种：

| 手段 | 做法 | 结论 |
|---|---|---|
| **Reward Scaling（只缩放）** | reward 除以其运行标准差 `r/σ` | 单独用**几乎无效**，不解决稳定性 |
| **Reward Normalization + Clipping（归一化+裁剪，式 18）** | 用历史滑动均值方差归一化后再裁剪 | **有效**，PPO-max 采用 |
| **Advantage Normalization（优势归一化）** | 在 minibatch 内对优势白化 `(A-mean)/std` | 近乎通用、PPO-max 采用（属 PPO 侧，见后续章节） |

**Reward Normalization + Clipping（式 18）**：

$$
\tilde r(x, y) = \mathrm{clip}\!\left(\frac{r(x,y) - \bar r}{\sigma(r)},\ -\delta,\ \delta\right)
$$

纯文本：`r̃ = clip( (r - r̄)/σ(r), -δ, +δ )`

- `r̄, σ(r)`：**历史 reward 的滑动均值与标准差**（不是单个 batch 的），逐步更新。
- **`/σ`（缩放）**：把 reward 尺度稳定住，等价于给 PPO 一个自适应步长——**不改变奖励方向**，无害。
- **`-r̄`（中心化）**：本身受 BT「只有相对分有意义」保护（§1.3），且优势 `A = R̂ - V` 对整体平移常数具**不变性**（常数同时进入回报与基线、相互抵消）→ 中心化对策略方向**理论上无害**。
- **`clip(·, -δ, δ)`（裁剪）**：砍掉极端 reward，防个别离群打分主导梯度 → 这才是压制 hacking 的关键非线性。

**关键工程结论（呼应 §6.1）：**
1. **Token-level KL-Penalty 是稳定性的真正关键**，权重不能太小。Anthropic 用 0.001 时「没发现显著影响」，但本文发现**适当权重（λ=0.05）的 token 级 KL 惩罚对 PPO 长期不崩至关重要**，还能支持训练步数放大。这与 §6.1「KL 惩罚 ≈ early stopping」**并不矛盾**：Gao 说的是 KL 救不了「真实质量上限」，本文说的是 KL 救「训练动力学的稳定性」——两个层面。
2. **critic 预训练** > lr warmup：PPO 前先把 critic 单独训到 value loss≈0，再开始联合优化，能给出更好的优势估计（属 PPO 侧，后续展开）。
3. **SFT 是 policy 的硬前提**：裸预训练模型直接 PPO 会语言能力退化、训崩。
4. **效果**：PPO-max 在 harmless 上收益远大于 helpful（英文 harmless RLHF 胜率 62% vs SFT 5%；helpful 44% vs 30%）——对后训练**数据配比**有直接启示：防有害的边际收益更高。

**一句话**：RM 打分不能裸喂 PPO——要**归一化+裁剪**稳尺度、**token 级 KL 惩罚**稳动力学；但这些都是「压制 hacking 的补丁」，治本仍要靠换掉可被 hack 的 RM（RLVR）。

## 七、RLAIF 与 Constitutional AI

> 依据 Anthropic *Constitutional AI: Harmlessness from AI Feedback*（Bai et al. 2022，arXiv:2212.08073）写成。阅读笔记见 `post_training/reward_model/`。
> 一句话定位：**把「谁来给偏好打标签」从人换成 AI**——用一套显式「宪法原则」+ LLM-as-judge 生成偏好对，PM 训练与 RLHF 完全一致。这是生成式 RM（§五）的落地，也是 RM 高成本瓶颈（§八）的一条解法。

### 7.1 动机：RLHF 的三个痛点

标准 RLHF 的无害性依赖**数万条人类标注**，带来三个问题：**贵**（多一套红队标注）、**不透明**（几万条私有偏好没人能概括成「到底学了什么」）、**回避（evasive）**——标注者把「我不能回答」当作对有害输入的合格回应给了奖励，训出的模型遇敏感问题就闪躲，牺牲 helpfulness。

CAI 的目标：**只用约十几条自然语言原则、零无害性人类标签**，训出 **helpful 且 harmless 且不回避**的助手。

### 7.2 两阶段方法

**阶段一：Constitutional SL（critique → revision → SFT）**

```
helpful 模型对有害 prompt 生成回复
  → 自我批评（按随机抽取的一条宪法原则指出哪里有害）
  → 自我修订（据批评重写，去掉有害内容）
  → 可迭代多轮 → 用最终修订版做 SFT，得 SL-CAI
```

- 本质是**用模型自己生成 SFT 数据**（数据构造层面的自我改进）。
- 真正作用**不是「教会无害」，而是把策略分布拉到 on-distribution**、降低阶段二 RL 的探索成本——与「SFT 是 PPO 硬前提」（见 Secrets of RLHF §6.2 第 3 条）同一逻辑。
- 「先批评再修订」比「直接修订」无害性略好，且**推理过程更透明**，能帮模型发现更微妙的危害。

**阶段二：RLAIF（RL from AI Feedback）**

```
SL-CAI 对 prompt 生成一对回复 (y_A, y_B)
  → 交给「反馈模型」做多选题：按某条原则，哪个更无害？
  → 取 (A)/(B) 的归一化对数概率作【软标签】
  → 构造偏好比较样本 → 训偏好模型 PM
  → 用 PM 作奖励跑 PPO，得 RL-CAI
```

- **关键分工**：harmlessness 全用 **AI 标签**，helpfulness 仍用**人类标签**——PM 是二者混合训练。
- 从 PM 训练往后（PM + RL）**与 RLHF 完全相同**，唯一变化是无害标签来源。

### 7.3 让 AI 反馈可用的三个关键 trick（面试高频）

| trick | 做法 | 为什么 |
|---|---|---|
| **软标签 > 硬标签** | 用反馈模型的**归一化对数概率**（而非 0/1）作 PM 目标 | 多选题输出**校准良好**，软标签保留了「有多确定」的信息 |
| **原则集成（ensembling）** | 每条比较从 16 条原则**随机抽一条**，而非固定单条 | 集成显著提升 PM 鲁棒性 |
| **CoT 概率钳制到 40-60%** | 用 CoT 生成标签时，把概率**钳制**进 40-60% 区间 | CoT 会让模型**过度自信**（概率逼近 0/1）→ 软标签失真；钳制救回校准，否则 RL-CAI 学会输出更极端回复 |

> CoT 还有个独立价值：**让 AI 判断质量随规模逼近人类 PM**（>52B 时开始有竞争力）。思维链在这里不是推理技巧，而是**提升 AI 反馈质量**的杠杆。

### 7.4 结论与风险

- **效果**：RL-CAI 显著比 RLHF/SL-CAI 更无害，helpfulness 代价很小，在无害-有用平面上实现对标准 RLHF 的**帕累托改进**；**几乎从不回避**。
- **过度优化 → Goodhart**（呼应 §6.1、§6.2）：RL-CAI 被过训后会**反应过激**、对多数红队 prompt **复读安抚模板**（如「you are valued, valued, and cared for」）——这正是 reward hacking 的又一形态：PM 偏好某种模式，策略就疯狂利用它。
- **评估标准即对齐设计**：本文让标注者**偏好「深思的拒绝」而非「回避」**，直接改变了 helpful/HH 模型的相对 Elo——提醒**偏好数据的标注指南本身就是一种对齐决策**（对数据构建/配比有直接启示）。
- **dual-use**：降低「按意图对齐 AI」门槛的同时，也降低了「训出有害系统」的门槛。

### 7.5 与本笔记其他部分的关系

- 属**生成式 RM / LLM-as-judge**（§五）的工业级落地——不接标量头，用「多选题+原则」让模型判偏好。
- 是 RM **高成本瓶颈**（§八）的一条解法：**用 AI 标签替代人类无害标注**，与 DPO（去显式 RM）、RLVR（规则替代）、GRPO（去 Critic）并列。
- reward hacking 表现与 [[16_reward_model]] §六、Gao et al. §6.1、Secrets of RLHF §6.2 一脉相承——**只要把 RM/PM 分数当目标，就会被钻空子**。

## 八、RM 是瓶颈：为什么后来想替代它

本周核心认知——**显式 RM 是 RLHF 流水线的瓶颈**：

| 瓶颈 | 后续应对 |
|---|---|
| 训练/维护贵（多一个大模型 + 一套标注） | **DPO**：闭式隐式奖励，去掉显式 RM |
| 会被 hack、over-optimize | **RLVR**：用规则/验证器给可验证奖励，不留 RM 空子 |
| 逐 token 价值难估、Critic 贵 | **GRPO**：组内相对优势，去 Critic（[[9_grpo]]） |
| 只看结果、抓不到过程错误 | **PRM**：过程奖励（[[10_process_reward_model]]） |

## 一句话总结

RM = **SFT backbone + 标量头、取最后 token、用 Bradley-Terry pairwise loss `L = -log σ(r_w - r_l)` 训练**的打分器；它只学**相对分**，是 PPO/GRPO 奖励信号的来源。ORM 是面向「有客观对错」任务的变体——**用最终对错标签做逐 token 二元交叉熵**（名字讲来源、实现是逐 token）。RM 的高成本与可被 hack，催生了 DPO（去显式 RM）、RLVR（规则替代）、GRPO（去 Critic）、PRM（细化到过程）等一系列后续路线。

## 参考文献

- Ouyang et al., 2022. *Training language models to follow instructions with human feedback (InstructGPT).* arXiv:2203.02155.（RLHF/RM 奠基）
- Bradley & Terry, 1952. *Rank analysis of incomplete block designs.*（BT 模型原始）
- *RLHF Book*, Ch. 07 Reward Models. https://rlhfbook.com/c/07-reward-models.html
- Cobbe et al., 2021. *Training Verifiers to Solve Math Word Problems (GSM8K).*（ORM 源头）
- Lightman et al., 2023. *Let's Verify Step by Step.*（ORM/PRM 对照）
- Gao et al., 2022. *Scaling Laws for Reward Model Overoptimization.* arXiv:2210.10760.（过度优化缩放律，§6.1；阅读笔记见 `post_training/reward_model/`）
- Zheng et al., 2023. *Secrets of RLHF in Large Language Models Part I: PPO.* arXiv:2307.04964.（PPO-max、奖励重参数化、长度/低困惑度偏置实证；§1.2.1、§6.2）
- Bai et al., 2022. *Constitutional AI: Harmlessness from AI Feedback.* arXiv:2212.08073.（RLAIF、宪法原则、critique-revision、软标签/原则集成/CoT 钳制；§七）
- 【待读】Lilian Weng, 2024. *Reward Hacking in RL.*
