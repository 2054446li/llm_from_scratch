# PPO（Proximal Policy Optimization，近端策略优化）

> RLHF 十年的**主力算法**，也是 GRPO / DPO「相对它做减法」的基准。前置：[[15_policy_gradient]]（策略梯度、baseline、Q/V/A）、[[16_reward_model]]（奖励从哪来）。
> 本文把 **TRPO→PPO 的动机链、clip 目标、重要性采样、GAE、actor-critic、RLHF 四模型协同**串成一条线，并**显式标注 GRPO 在哪几处做减法**（[[9_grpo]]）。
> 配套代码：`code/8_ppo.ipynb`（clip + GAE + Critic + KL-in-reward 的 LLM 最小实现）。

## 概述

PPO 要解决策略梯度最根本的痛点：**一步走大就崩**。朴素策略梯度（REINFORCE / A2C，见 [[15_policy_gradient]]）对步长极其敏感——学习率稍大，一次更新就让策略分布剧变，采样分布随之崩坏，再也拉不回来。

TRPO 用**信任域（trust region）**从理论上解决了这个问题，但工程太重（二阶、共轭梯度）。PPO 的贡献是：**用一个一阶、几行代码就能实现的 clip 裁剪，近似 TRPO 的信任域效果**——这就是它能统治 RLHF 的原因。

一句话定位：**PPO = 重要性采样（可复用旧数据多步更新）+ clip（限制单步更新幅度）+ GAE（低方差优势估计）+ actor-critic（Critic 估 V）。**

## 一、从 TRPO 到 PPO 的动机链

### 1.1 为什么不能直接用策略梯度

朴素策略梯度每步做 `θ ← θ + α·∇J`。问题在于：

- **步长敏感**：LLM 参数空间里，参数的小改动可能让输出分布大变。一步走过头 → 新策略采出的样本质量骤降 → 后续估计全错 → 训练崩溃且**不可恢复**（不像监督学习有固定数据集兜底）。
- **数据用一次就扔**：on-policy 要求样本必须来自当前策略，一批 rollout 更新一次就作废，样本效率极低。

TRPO 和 PPO 都在回答同一个问题：**如何在「更新得够多」和「别更新过头」之间取平衡。**

### 1.2 TRPO：硬约束的信任域

TRPO 最大化**代理目标（surrogate objective）**，同时用 KL 硬约束把新旧策略拉在信任域内：

$$
\max_\theta\ \mathbb{E}\Big[\, \rho\,\hat{A} \,\Big] \quad \text{s.t.}\quad \mathbb{E}\big[\mathrm{KL}(\pi_{\theta_{old}} \,\|\, \pi_\theta)\big] \le \delta
$$

其中重要性比 $\rho = \dfrac{\pi_\theta(a\mid s)}{\pi_{\theta_{old}}(a\mid s)}$。纯文本：`max E[ρ·Â]  s.t.  E[KL(π_old‖π_θ)] ≤ δ`。

- **理论漂亮**：能证明单调改进（每步真实回报不降）。
- **工程重**：KL 硬约束要解一个带约束优化，需算 Fisher 信息矩阵的二阶信息 + 共轭梯度 + 线搜索。对 LLM 这种参数量，几乎不可行。

### 1.3 PPO 的简化：把硬约束换成 clip

PPO 把「KL 硬约束」这件重活，换成对重要性比 $\rho$ 做**直接裁剪**：

$$
\mathcal{L}^{CLIP}(\theta) = \mathbb{E}\Big[\min\big(\rho\,\hat{A},\ \ \mathrm{clip}(\rho,\ 1-\varepsilon,\ 1+\varepsilon)\,\hat{A}\big)\Big]
$$

纯文本：`L = E[ min( ρ·Â, clip(ρ, 1-ε, 1+ε)·Â ) ]`，典型 `ε=0.2`。

直觉：只要 $\rho$ 落在 $[1-\varepsilon, 1+\varepsilon]$ 内，就是普通策略梯度；一旦跨出这个区间且**朝着让目标继续变大的方向**，`min` 会选中被裁剪的那一支 → 梯度归零 → **优化器被告知「这一步别再往这推了」**。这就用一阶操作近似出了 TRPO 的信任域。

## 二、clip 目标：外层为什么还要取 min（核心机制）

裁剪目标里有两层：内层 `clip(ρ,1-ε,1+ε)`，外层再对「裁剪 / 未裁剪」两支取 `min`。这两层是**分工的两件事**，理清分工是搞懂 PPO 的关键：

- **clip 负责「限制步子」**：把 ρ 摁在 $[1-\varepsilon, 1+\varepsilon]$ 内，防止单步更新过大。
- **min 负责「让这个 cap 只朝一个方向咬合」**：把 clip 那个**对称、advantage-盲**的限制，改造成**单向**的——只拦「顺着 advantage 冲过头」，放行「冲反了需要纠错」。

逐 token 目标（最大化）：

$$
\mathcal{L}(\theta) = \min\Big(\, \rho\,\hat{A},\ \ \mathrm{clip}(\rho,\ 1-\varepsilon,\ 1+\varepsilon)\,\hat{A} \,\Big),
\qquad \rho = \frac{\pi_\theta(o_t \mid q, o_{<t})}{\pi_{\theta_{\text{old}}}(o_t \mid q, o_{<t})}
$$

### 2.1 只用 clip 会坏在哪：它分不清「冲过头」和「冲反了」

`clip` 本身**不看 $\hat A$ 的符号**，ρ 一越界（无论上界下界）就饱和成常数、梯度归零。但「限制步子」这件事，**只应该在 ρ 顺着 $\hat A$ 想要的方向冲过头时生效**。clip 分不清这个，两侧一视同仁摁死——于是「冲反了、本该纠错」的方向也被误杀。

只用 `clip(ρ)·Â`（不套 min）对比诚实的 `ρ·Â`（最大化，看谁更大）：

| 格子 | 含义 | unclip=$\rho\hat A$ | clip-only | 谁更大 | 问题 |
|---|---|---|---|---|---|
| $\hat A>0,\ \rho>1+\varepsilon$ | 好动作**冲过头** | 大 | $(1+\varepsilon)\hat A$ | clip 更小 | ✓ 该摁，clip 对 |
| $\hat A>0,\ \rho<1-\varepsilon$ | 好动作**冲反了** | 小 | $(1-\varepsilon)\hat A$ | clip 更大 | ✗ 目标反而更优、梯度=0 |
| $\hat A<0,\ \rho>1+\varepsilon$ | 坏动作**冲反了** | 小(更负) | $(1+\varepsilon)\hat A$ | clip 更大 | ✗ 目标反而更优、梯度=0 |
| $\hat A<0,\ \rho<1-\varepsilon$ | 坏动作**冲过头** | 大(更负) | $(1-\varepsilon)\hat A$ | clip 更小 | ✓ 该摁，clip 对 |

看两个 ✗ 格：只用 clip 时目标值**比诚实的 unclip 还大、且梯度=0**。翻译成人话——上个 minibatch 把一个坏动作的概率抬高了（$\hat A<0$ 却 $\rho>1+\varepsilon$），只用 clip 的话优化器会觉得「没事发生」，**你再也压不回去了**。这就是致命处：clip 单用不仅摁死该摁的，还杀掉了纠错梯度。

### 2.2 min 干的事：把 clip 改成单向 cap（回捞纠错）

min 取**更小的那支**（悲观下界），净效果正好修好上表两个 ✗：

| | $\rho > 1+\varepsilon$ | $\rho < 1-\varepsilon$ |
|---|---|---|
| **$\hat A>0$** | 冲过头 → $\min=(1+\varepsilon)\hat A$（取裁剪项，**梯度=0**，摁住） | 冲反了 → $\min=\rho\hat A$（取未裁剪项，**满梯度**，救回） |
| **$\hat A<0$** | 冲反了 → $\min=\rho\hat A$（取未裁剪项，**满梯度**，救回） | 冲过头 → $\min=(1-\varepsilon)\hat A$（取裁剪项，**梯度=0**，摁住） |

**关键澄清（谁清零、谁回捞）：**
- **所有的「梯度=0」都是 clip 干的**（饱和）；min 从不制造新的零。
- **min 的唯一作用是「回捞」**：在两个「冲反了」的格子里改选 unclip 支，把 clip 本会误杀的纠错梯度救回来。

### 2.3 一句话记忆：抬过头就摁，冲反了就救

同一个动作，**越界方向不同、处理相反**：

- **$\hat A>0$（好动作）**：$\rho>1+\varepsilon$ 概率已抬过头 → 摁（别一次喂太猛）；$\rho<1-\varepsilon$ 概率反而掉下去了（冲反了）→ 救（保留满梯度拉回来）。
- **$\hat A<0$（坏动作）**：$\rho<1-\varepsilon$ 概率已压够低 → 摁（别压塌陷）；$\rho>1+\varepsilon$ 概率反而涨了（冲反了）→ 救（保留满梯度继续压）。

**为什么「救回」不是因为数据珍贵，而是因为方向反了**：ρ<1−ε 的好动作不是「更值钱」，而是它的移动方向和 advantage 想要的方向**相反**（好动作概率却在降）。clip 的使命只是「拦住往对的方向冲过头」，这里根本不是冲过头、是冲反了，没有理由拦 → 梯度必须留着纠错。把「救回」理解成**纠错通道**，比「珍贵数据」更贴机制。

**总结**：clip 给了一个**对称的、advantage-盲的 cap**；min 借 $\hat A$ 的符号（哪支更小）把它改成**单向 cap**——只掐「顺着 advantage 冲过头」，放行「冲反了要纠错」。没有 min，clip 会连纠错一起摁死，你就无法撤销上一步的越界。

### 与 GRPO / DeepSeek-V3.2 的关系

- **GRPO**（[[9_grpo]]）：`min+clip` 机制与 PPO **完全一致**，逐字照搬。GRPO 的减法在别处（见 §七）——不在 clip 上。
- **DAPO 的 Clip-Higher**：把上下裁剪阈值解耦成 $\varepsilon_{low}, \varepsilon_{high}$，放宽上界防止低概率 token 被过度裁剪导致的熵坍缩。是对这张 2×2 表右上/左下格子的精细化。
- **DeepSeek-V3.2 / 离策略修正**：当 $\rho$ 因训练-推理不一致而系统性偏移时，需要额外的重要性修正，见 [[13_unbiased_kl_estimate]]。

## 三、重要性采样：为什么 PPO 能复用旧数据

朴素策略梯度是严格 on-policy（数据必须来自当前 $\pi_\theta$）。PPO 通过**重要性采样（importance sampling）**放宽这一点：

$$
\mathbb{E}_{a\sim\pi_\theta}[\hat A] = \mathbb{E}_{a\sim\pi_{\theta_{old}}}\Big[\frac{\pi_\theta(a)}{\pi_{\theta_{old}}(a)}\hat A\Big] = \mathbb{E}_{a\sim\pi_{\theta_{old}}}[\rho\,\hat A]
$$

- 用**旧策略 $\pi_{\theta_{old}}$ 采一批数据**，就能对**当前 $\pi_\theta$** 做多步 minibatch 更新（通常 1 批数据跑几个 epoch）——大幅提升样本效率。
- 代价：$\pi_\theta$ 更新几步后就离 $\pi_{\theta_{old}}$ 越来越远，$\rho$ 偏离 1，重要性采样方差爆炸、估计失真。**clip 正是给 $\rho$ 上界的那道闸**——它同时保证了重要性采样的有效性。

**「名义 on-policy、实际 off-policy」**：PPO 用旧数据做多步更新，这一刻起它就不是纯 on-policy 了。这是理解大规模 RL 训练-推理一致性问题的起点，直连 [[13_unbiased_kl_estimate]]（k1/k2/k3 KL 估计、离策略修正）。

## 四、GAE：偏差-方差可调的优势估计

### 4.1 为什么用优势而非回报

优势 $A(s,a) = Q(s,a) - V(s)$（见 [[15_policy_gradient]]）：用**优势**而非直接用回报 $R$ 做权重，有两个好处——① **降方差**（减去基线 $V$，不改期望但压方差）；② 表达「相对好坏」（这个动作比该状态的平均水平好多少）。

### 4.2 GAE 的插值思想

单步 TD 误差：$\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)$。GAE（广义优势估计）是 TD 误差的指数加权和：

$$
\hat A_t^{GAE(\gamma,\lambda)} = \sum_{l=0}^{\infty} (\gamma\lambda)^l\,\delta_{t+l}
$$

纯文本：`Â_t = Σ_l (γλ)^l · δ_{t+l}`。用 $\lambda$ 在偏差-方差间连续插值：

| $\lambda$ | 退化为 | 偏差 | 方差 |
|---|---|---|---|
| $\lambda=0$ | 单步 TD：$\hat A_t = \delta_t$ | 高（依赖 Critic 准） | 低 |
| $\lambda=1$ | 蒙特卡洛：$\hat A_t = \sum \gamma^l r_{t+l} - V(s_t)$ | 低（不靠 Critic 外推） | 高 |

- $\lambda$ 越小，越信任 Critic 的 bootstrap（偏差来自 Critic 不准）；$\lambda$ 越大，越信任真实采样回报（方差来自采样随机）。RLHF 里常用 $\lambda\approx0.95$、$\gamma\approx1$（序列级 bandit 视角，几乎不折扣）。

## 五、actor-critic：Critic 怎么训

PPO 是 actor-critic 结构，两个网络：

- **Actor（Policy）**：待训练的策略 $\pi_\theta$，用 $\mathcal{L}^{CLIP}$ 更新。
- **Critic（Value）**：估计 $V(s)$，用于算 GAE。训练目标是**回归到回报 / TD target 的 MSE**：

$$
\mathcal{L}^{V}(\phi) = \mathbb{E}\big[(V_\phi(s_t) - \hat R_t)^2\big], \qquad \hat R_t = \hat A_t + V_{\phi_{old}}(s_t)
$$

**常用工程技巧（37 details 里的坑）**：
- **value clipping**：对 Critic 的更新也做类似 clip，防 value 跳变。
- **优势归一化**：minibatch 内对 $\hat A$ 白化 `(A-mean)/std`，稳梯度尺度（呼应 [[16_reward_model]] §6.2）。
- **reward / return 归一化**：稳住奖励尺度，等价自适应步长。
- **entropy bonus（熵正则）**：在目标里加 $+c\cdot H(\pi_\theta)$ 鼓励探索、防早熟收敛（埋到 DAPO 的 Clip-Higher 防熵坍缩）。

> **Critic 正是 GRPO 要砍掉的那一块**——它与 Policy 同量级，显存/算力直接 ×2，且 LLM 里奖励只给最后 token，逐 token 价值难估准。见 §六、§七。

## 六、RLHF 里的 PPO 全貌：四模型协同

这是把前面拼成完整流水线的关键。RLHF-PPO 同时在内存里有**四个模型**：

```
① Policy (Actor)      —— 待训练，从 SFT 初始化              【可训】
② Value  (Critic)     —— 估 V(s)，与 Policy 同量级          【可训】← GRPO 要砍的就是它
③ Reward Model (冻结) —— 训好的 RM，给整条回答打标量分       【冻结】
④ Reference (冻结)    —— SFT 快照，算 KL 防策略跑偏          【冻结】
```

### 6.1 奖励怎么组装：KL 加在 reward 上

每个 token 的最终奖励 = **只有最后一个 token 拿到 RM 分数**，**每个 token 都减去一项 KL 惩罚**：

$$
r_t = \underbrace{r_{RM}(x,y)\cdot\mathbb{1}[t=T]}_{\text{仅末 token}} \;-\; \beta\,\underbrace{\log\frac{\pi_\theta(o_t\mid\cdot)}{\pi_{ref}(o_t\mid\cdot)}}_{\text{逐 token KL}}
$$

纯文本：`r_t = RM分数·(t是末token) − β·log(π_θ/π_ref)`。

- **RM 分数（末 token）**：Week 1 训好的冻结 RM 给整条回答的质量分。
- **KL 惩罚项（逐 token）**：防止策略为了刷 RM 分而漂离 SFT 分布太远（reward hacking / over-optimization 的第一道闸，见 [[16_reward_model]] §六）。$\beta$ 控制约束强度。
- **注意这里有两个 KL，别混**：这个 $\pi_\theta$–$\pi_{ref}$ 的 KL 是**约束跑偏**（进 reward）；PPO 内部还有 $\pi_\theta$–$\pi_{\theta_{old}}$ 的信任域（由 clip 负责）。二者各管一件事。

### 6.2 显存痛点 = GRPO/DPO 的存在动机

四个模型里，**2 个可训（Policy+Critic）都要过前向+反向**，Critic 与 Policy 同量级 → 显存/算力压力巨大。这正是后续算法的根本工程动机：

- **GRPO** 砍掉 **② Critic**：用组内平均奖励当 baseline，省约一半显存。
- **DPO** 更激进，砍掉 **② Critic + ③ RM + 在线采样**：把「RM+RL」压成对偏好数据的离线分类损失。

## 七、显式对照 GRPO：减法减在哪

| 维度 | PPO | GRPO（做的减法） |
|---|---|---|
| **优势 $\hat A$** | Critic 估 V + GAE | **组内归一化** `(r-mean)/std`，去 Critic |
| **额外模型** | 需 Critic（≈Policy 大小） | **无 Critic**，省约一半显存 |
| **KL 位置** | 加在 **reward** 里（逐 token） | 直接加进 **loss**，不污染优势 |
| **KL 估计** | 普通 | **k3 无偏估计**，恒正（[[13_unbiased_kl_estimate]]） |
| **clip 机制** | `min+clip` | `min+clip`（**完全相同**，见 §二） |

一句话：**GRPO 只动了「优势怎么来」和「KL 放哪」两处，clip 内核原封不动。**

## 八、PPO 两种形式：clip vs KL-penalty

TRPO 软化成 PPO 有两条路，clip 版胜出：

| | clip 版（主流） | KL-penalty 版 |
|---|---|---|
| 做法 | `min(ρÂ, clip(ρ)Â)` | `ρÂ − β·KL`，β 自适应调 |
| 超参 | 只有一个 ε，且不敏感（0.1~0.3 都行） | 需启发式动态调 β，脆弱易震荡 |
| 行为 | 一阶移除越界激励，近似硬约束 | 软惩罚，A 大时拦不住偏移 |
| 计算 | 无需显式算 KL | 每步显式算 KL（大词表有开销） |

**为什么 clip 成主流**：① PPO 原论文实测 clip 更优（Sec 6.1）；② 少一个难调的 β；③ 行为更接近硬约束；④ 计算更省。这四点在「单次实验极贵」的 LLM 场景被放大。

> 注意区分：这里说的是**信任域**的 KL（$\pi_\theta$–$\pi_{\theta_{old}}$）用 clip；RLHF reward 里那个 $\pi_\theta$–$\pi_{ref}$ 的 KL 惩罚（§6.1）几乎总是保留。InstructGPT = **clip 做信任域 + reward 里加 $\pi_{ref}$ 的 KL**，两者并存。

## 一句话总结

PPO = **用一阶的 clip 近似 TRPO 的信任域**：重要性采样让旧数据可多步复用，clip 给 $\rho$ 上下界防单步更新过头（`Â>0` 防更新过头、`Â<0` 防塌陷），GAE 用 $\lambda$ 在偏差-方差间插值估优势，Critic 回归 V。在 RLHF 里它协同**四模型**（Policy/Critic/RM/Ref），KL 加在 reward 上防跑偏。它的 **Critic 显存痛点**催生了 GRPO（去 Critic）与 DPO（去 RL）。

## 参考文献

- Schulman et al., 2017. *Proximal Policy Optimization Algorithms.* arXiv:1707.06347.（PPO 原始，clip vs KL-penalty 对比在 Sec 6.1）
- Schulman et al., 2015. *Trust Region Policy Optimization (TRPO).* arXiv:1502.05477.（信任域硬约束，PPO 前身）
- Schulman et al., 2015. *High-Dimensional Continuous Control Using GAE.* arXiv:1506.02438.（GAE 原始）
- Ouyang et al., 2022. *InstructGPT.* arXiv:2203.02155.（RLHF-PPO 四模型经典范式）
- Huang et al., 2022. *The 37 Implementation Details of PPO.* ICLR blog.（工程细节，面试常考坑）
- Zheng et al., 2023. *Secrets of RLHF Part I: PPO.* arXiv:2307.04964.（PPO-max 稳定化、奖励重参数化）
- Schulman, 2020. *Approximating KL Divergence.*（k1/k2/k3 KL 估计，见 [[13_unbiased_kl_estimate]]）
