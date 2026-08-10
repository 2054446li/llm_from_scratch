# 策略梯度（Policy Gradient）—— 所有 RL 后训练算法的共同祖先

> 后训练 RL 的**地基**。PPO / GRPO / DPO / actor-critic 全都从这里长出来，或在此基础上做减法。前置：softmax、交叉熵、期望与梯度。
> 本文目标：把「策略梯度定理」从头推一遍，讲清 **log-derivative trick**、**baseline 为什么降方差**、**REINFORCE 的痛点如何逼出 actor-critic**、以及 **Q/V/A 三函数**的定义与关系。相关：[[9_grpo]]、[[14_ppo]]、[[13_unbiased_kl_estimate]]。

---

## 0. 问题设定：我们到底在优化什么

强化学习的目标是找到一个策略 $\pi_\theta$（参数 $\theta$），使**期望回报**最大：

$$
J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\big[R(\tau)\big]
= \sum_\tau P(\tau; \theta)\, R(\tau)
$$

- $\tau = (s_0, a_0, s_1, a_1, \dots)$ 是一条**轨迹**（trajectory）。
- $R(\tau)$ 是这条轨迹的**回报**（return，通常是折扣奖励之和 $\sum_t \gamma^t r_t$）。
- $P(\tau;\theta)$ 是在策略 $\pi_\theta$ 下走出轨迹 $\tau$ 的概率。

**LLM 后训练的语境**：一个 prompt $q$ 是初始状态，模型逐 token 生成回答 $o=(o_1,\dots,o_T)$。常把「一整条回答 = 一个动作」看作 **序列级 bandit**，或按 token 展开成逐步 MDP；折扣 $\gamma$ 通常取 1。奖励 $R$ 往往只在回答末尾由奖励模型/验证器给出。

我们想用**梯度上升**更新 $\theta$：$\theta \leftarrow \theta + \alpha \nabla_\theta J(\theta)$。难点在于 $\nabla_\theta J$ 里的 $P(\tau;\theta)$ 依赖 $\theta$，而 $\tau$ 又是采样出来的——不能直接对采样求导。**策略梯度定理**就是来解决这个问题的。

---

## 1. 三个数学 trick（推导的全部工具）

整个策略梯度推导只用到三个小工具：

- **① log-derivative trick**：$\nabla_\theta \log z = \dfrac{1}{z}\nabla_\theta z$，即 $\nabla_\theta z = z\,\nabla_\theta \log z$。
- **② 期望展开**：$\mathbb{E}_{x\sim p(x)}[f(x)] = \sum_x p(x) f(x)$（或积分）。
- **③ 分数上下同乘**：$\dfrac{a}{b} = \dfrac{a\cdot p(x)}{b\cdot p(x)}$——用来「无中生有」造出一个概率 $p(x)$，好把式子凑回期望形式。

三者配合的**核心目的**：把「对参数求导」这个不能采样的操作，变形成「对 $\pi_\theta$ 采样求期望」的形式，从而能用 Monte Carlo 估计。

---

## 2. 策略梯度定理的推导

### 2.1 先看单个 transition（一步）

从单步目标 $\nabla_\theta \mathbb{E}_{a\sim \pi_\theta(a|s)}[r(a)]$ 出发（$r(a)$ 视为对 $\theta$ 不可微的常数）：

$$
\nabla_\theta \sum_a \pi_\theta(a|s)\, r(a)
= \sum_a \nabla_\theta \pi_\theta(a|s)\, r(a)
\quad(\text{trick ② 展开})
$$

$$
= \sum_a \pi_\theta(a|s)\,\frac{\nabla_\theta \pi_\theta(a|s)}{\pi_\theta(a|s)}\, r(a)
\quad(\text{trick ③ 上下同乘}\ \pi_\theta)
$$

$$
= \sum_a \pi_\theta(a|s)\,\big[\nabla_\theta \log \pi_\theta(a|s)\big]\, r(a)
\quad(\text{trick ①})
= \mathbb{E}_{a\sim \pi_\theta}\big[r(a)\,\nabla_\theta \log \pi_\theta(a|s)\big]
$$

**结论**：可以把 reward $r$ 放到梯度外面，只对 $\log\pi_\theta(a|s)$ 求梯度。

### 2.2 推广到整条轨迹

轨迹概率按马尔可夫分解（含初始分布、策略、转移）：

$$
p(\tau|\theta) = \underbrace{\mu(s_0)}_{\text{初始分布}} \prod_{t=0}^{T-1} \underbrace{\pi_\theta(a_t\mid s_t)}_{\text{策略,含}\theta}\ \underbrace{p(s_{t+1},r_t\mid s_t,a_t)}_{\text{环境转移,不含}\theta}
$$

同样三步（②③①），得到：

$$
\nabla_\theta \mathbb{E}_\tau[R(\tau)] = \mathbb{E}_\tau\big[R(\tau)\,\nabla_\theta \log p(\tau|\theta)\big]
$$

**展开 $\log p(\tau|\theta)$**：连乘取对数变求和，$\log(A\cdot B)=\log A+\log B$。其中初始分布 $\mu(s_0)$ 和转移 $p(s_{t+1},r_t|s_t,a_t)$ **都不含 $\theta$，求梯度为 0**，只剩策略项：

$$
\nabla_\theta \log p(\tau|\theta) = \sum_{t=0}^{T-1} \nabla_\theta \log \pi_\theta(a_t\mid s_t)
$$

**这一步的意义**：不需要知道环境的动力学模型（转移概率），只需对自己的策略求导——这就是策略梯度 **model-free** 的原因。代回得到策略梯度定理：

$$
\boxed{\ \nabla_\theta J(\theta) = \mathbb{E}_{\tau\sim\pi_\theta}\Big[R(\tau)\sum_{t=0}^{T-1} \nabla_\theta \log \pi_\theta(a_t\mid s_t)\Big]\ }
$$

序列级 bandit 视角下（一整条回答一个动作、一个回报 $R$），退化成最简洁的形式：

$$
\nabla_\theta J(\theta) = \mathbb{E}\big[\nabla_\theta \log \pi_\theta(a\mid s)\, R\big]
$$

**直觉**：$\nabla\log\pi_\theta(a|s)$ 是「让动作 $a$ 概率变大的方向」，乘上回报 $R$——**回报高就往这个方向多推（提高该动作概率），回报低就少推甚至反推**。这就是「好动作强化、坏动作抑制」的数学表达。

> 本节推导顺序（三 trick → 单 transition → 整条轨迹 → REINFORCE）参考自：https://www.cnblogs.com/moonout/p/18086974 ，baseline 与降方差部分见下节。

---

## 3. Baseline 降方差（后面 Critic / 组内均值 / GAE 的共同动机）

### 3.1 结论

在回报里减去一个**只依赖状态、不依赖动作**的基线 $b(s)$，梯度的**期望不变**，但**方差可以大幅下降**：

$$
\nabla_\theta J(\theta) = \mathbb{E}\big[\nabla_\theta \log \pi_\theta(a\mid s)\,(R - b(s))\big]
$$

### 3.2 为什么期望不变（无偏性证明）

核心是一个恒等式：**对数概率梯度的期望恒为 0**。

$$
\mathbb{E}_{a\sim\pi_\theta}\big[\nabla_\theta \log \pi_\theta(a\mid s)\big]
= \sum_a \pi_\theta(a|s)\,\frac{\nabla_\theta \pi_\theta(a|s)}{\pi_\theta(a|s)}
= \sum_a \nabla_\theta \pi_\theta(a|s)
= \nabla_\theta \sum_a \pi_\theta(a|s)
= \nabla_\theta 1 = 0
$$

因此减去 $b(s)$ 贡献的那一项：

$$
\mathbb{E}\big[\nabla_\theta \log \pi_\theta(a|s)\cdot b(s)\big]
= b(s)\,\underbrace{\mathbb{E}\big[\nabla_\theta \log \pi_\theta(a|s)\big]}_{=\,0}
= 0
$$

（$b(s)$ 与动作 $a$ 无关可提到期望外。）所以 $\mathbb{E}[\nabla\log\pi\cdot(R-b)] = \mathbb{E}[\nabla\log\pi\cdot R]$——**减 baseline 不引入偏差**。

### 3.3 为什么方差会下降（用 $\mathrm{Var}(x)=\mathbb{E}[x^2]-\mathbb{E}[x]^2$ 说明）

记单样本梯度估计量为 $g$。方差公式：

$$
\mathrm{Var}(g) = \mathbb{E}[g^2] - \big(\mathbb{E}[g]\big)^2
$$

- **减 baseline 不改 $\mathbb{E}[g]$**（§3.2 已证），所以公式右边第二项 $(\mathbb{E}[g])^2$ 是**固定的**。
- 因此 $\mathrm{Var}(g)$ 的变化**完全由第一项二阶矩 $\mathbb{E}[g^2]$ 决定**。

比较两种情形的二阶矩（$g = \nabla_\theta\log\pi_\theta(a|s)\cdot(R-b)$）：

$$
\mathbb{E}[g^2] = \mathbb{E}\Big[\big(\nabla_\theta\log\pi_\theta(a|s)\big)^2\,(R-b)^2\Big]
$$

**关键就在 $(R-b)^2$ 这个因子**：选一个贴近回报平均水平的 $b$，能让 $(R-b)^2$ 整体变小，从而压低 $\mathbb{E}[g^2]$、压低方差；而 $(\mathbb{E}[g])^2$ 纹丝不动。**这就是「不改期望、只降方差」在方差公式里的确切位置**——动的是 $\mathbb{E}[g^2]$，不是 $(\mathbb{E}[g])^2$。

> **常见困惑：方差公式里的 $-(\mathbb{E}[g])^2$ 不是已经在减均值了吗，为什么还要另减 $b$？**
> 两个「减」减的是不同东西：
> - $(\mathbb{E}[g])^2$ 里的 $\mathbb{E}[g]$ 是**梯度估计量自身的期望**（恒等于真实梯度，你改不动它），是方差公式在**结果层面**自动减的。
> - baseline $b$ 减在**回报上、且在乘 $\nabla\log\pi$ 之前**，减的是「同一状态下各动作共有的那部分回报高度」。
>
> 因为 $\mathbb{E}[\nabla\log\pi]=0$，减 $b$ 让 $\mathbb{E}[g]$ 不变、只压 $\mathbb{E}[g^2]$——在样本层面就表现为「把散得很开的样本挤到一起」。

> **更深一层的困惑：$\mathrm{Var}(R-b)=\mathrm{Var}(R)$，从随机变量里减常数方差不变，那减 $b$ 怎么可能降方差？**
> 这个反驳完全正确，但**减的对象搞错了**。梯度估计量不是 $R-b$，而是 $g = \nabla\log\pi\cdot(R-b)$。展开：
> $$ g = \underbrace{\nabla\log\pi\cdot R}_{A} - \underbrace{\nabla\log\pi\cdot b}_{C} $$
> 关键：$b$ 虽是常数，但 $C=\nabla\log\pi\cdot b$ **不是常数**——它随采样到的动作变化（例子里 $a_1$ 取 $2b$、$a_2$ 取 $-2b$）。所以你减掉的是一个**随机变量 $C$**，不是常数。而
> $$ \mathrm{Var}(A-C) = \mathrm{Var}(A) - 2\,\mathrm{Cov}(A,C) + \mathrm{Var}(C) $$
> $C$ 均值为 0（故无偏）但与 $A$ **正相关**，只要 $2\,\mathrm{Cov}(A,C) > \mathrm{Var}(C)$ 方差就下降——像差分对冲，把公共波动抵消掉。这与「从 $g$ 里直接减常数 9」是两回事（后者会把 $(20,-16)$ 变成 $(11,-25)$，方差确实不变，但那不是策略梯度在做的事）。

### 3.3.1 闭式推导：最优 baseline 与降方差区间（Williams 1992 / Sutton & Barto §13.4）

记 score $s=\nabla_\theta\log\pi_\theta(a|s)$，估计量 $g(b)=s\,(R-b)$。

**① 方差只由二阶矩决定。** $\mathbb{E}[g(b)]=\mathbb{E}[sR]-b\,\mathbb{E}[s]=\mathbb{E}[sR]$ 与 $b$ 无关，故

$$
\min_b \mathrm{Var}(g(b)) \iff \min_b \mathbb{E}[g(b)^2]
$$

**② 二阶矩是 $b$ 的开口向上抛物线。**

$$
\mathbb{E}[g(b)^2] = \mathbb{E}\big[s^2(R-b)^2\big] = \mathbb{E}[s^2R^2] - 2b\,\mathbb{E}[s^2R] + b^2\,\mathbb{E}[s^2]
$$

**③ 求导置零 → 最优 baseline。**

$$
\frac{d}{db}\mathbb{E}[g(b)^2] = -2\,\mathbb{E}[s^2R] + 2b\,\mathbb{E}[s^2] = 0
\quad\Longrightarrow\quad
\boxed{\ b^* = \frac{\mathbb{E}[s^2 R]}{\mathbb{E}[s^2]}\ }
$$

即「以 $s^2=(\nabla\log\pi)^2$ 为权重对回报 $R$ 求加权平均」。工程上近似成 $V(s)$，这就是 actor-critic 里 **Critic 的理论出处**。

**④ 「减 $b$ 降方差」的确切条件。** 与不减（$b=0$）相比，因均值相同直接比二阶矩：

$$
\mathrm{Var}(g(b)) - \mathrm{Var}(g(0)) = b\big(b\,\mathbb{E}[s^2] - 2\,\mathbb{E}[s^2R]\big) < 0
\iff
0 < b < 2b^*
$$

结论：**baseline 落在 $(0,\,2b^*)$ 才降方差**，在 $b=b^*$ 处方差最小（抛物线顶点），取太大（$>2b^*$）反而比不减更差。

**⑤ 最优时的降幅。** 把 $b^*$ 代回：

$$
\mathbb{E}[g(0)^2] - \mathbb{E}[g(b^*)^2] = \frac{(\mathbb{E}[s^2R])^2}{\mathbb{E}[s^2]} \ge 0
$$

恒非负 → **最优 baseline 永不使方差变大**；仅当 $\mathbb{E}[s^2R]=0$（$R$ 与 $s^2$ 无关）时降幅为 0、减 $b$ 白减。这也说明：**baseline 有用，正是因为它通过 $s^2$ 与 $R$ 相关**。

**用 §3.4 的数字验证**（$s=(+2,-2)$，$R=(10,8)$，各 50%）：$\mathbb{E}[s^2]=4$，$\mathbb{E}[s^2R]=0.5\cdot4\cdot10+0.5\cdot4\cdot8=36$，故 $b^*=36/4=9$（正是例子取的 9），降幅 $36^2/4=324$——方差从 324 降到 0，完全吻合。

### 3.4 相对优势的直觉（为什么减 $b$ = 算「相对好坏」）

设某状态 $s$ 很好，其上**所有动作的回报都很高**（比如都落在 $[8,10]$）：

- **不减 baseline**：每个采样动作的系数 $R\in[8,10]$ 都是大正数，于是**每个动作都被往上推**，只是好动作推得多、差动作推得少。梯度方向被回报的「绝对高度」主导——采到哪个动作都往同一个方向猛推，反映的是「这个 state 有多好」，而**不是「这个 action 相对同 state 其它 action 好还是差」**。甚至会去鼓励那个回报只有 8 的次差动作。
- **减去 $b\approx 9$（该状态平均水平）**：系数变成 $R-b\in[-1,1]$。回报 10 的动作 → $+1$，**被鼓励**；回报 8 的动作 → $-1$，**被惩罚**。这才符合「奖励相对更好的、惩罚相对更差的」。

这就是 baseline 的本质作用：**把「绝对回报」重新中心化成「相对该状态平均水平的优劣」**，也就是 §5 的优势 $A=R-b\approx Q-V$。减掉的正是「跟动作无关、只制造噪声、却被 $\nabla\log\pi$ 放大」的公共高度，保留真正区分动作好坏的信号 → 方差自然降。

**最小数值例子**（把上面两点变成数字）：某状态两动作各 50%，令 $\nabla\log\pi(a_1)=+2,\ \nabla\log\pi(a_2)=-2$（满足 $\mathbb{E}[\nabla\log\pi]=0$），回报 $R(a_1)=10,\ R(a_2)=8$。

| | 样本 $g(a_1)$ | 样本 $g(a_2)$ | $\mathbb{E}[g]$ | $\mathrm{Var}(g)=\mathbb{E}[g^2]-(\mathbb{E}[g])^2$ |
|---|---|---|---|---|
| **不减 $b$** | $2\cdot10=20$ | $-2\cdot8=-16$ | $0.5\cdot20+0.5\cdot(-16)=2$ | $\tfrac{20^2+16^2}{2}-2^2=328-4=324$ |
| **减 $b=9$** | $2\cdot1=2$ | $-2\cdot(-1)=2$ | $0.5\cdot2+0.5\cdot2=2$ | $\tfrac{2^2+2^2}{2}-2^2=4-4=0$ |

**读表**：期望都是 2（真实梯度不变，$(\mathbb{E}[g])^2=4$ 固定）；而 $\mathbb{E}[g^2]$ 从 328 降到 4，方差随之从 324 崩到 0——**这就是 baseline 的全部魔力**。

### 3.4 最优 baseline

理论上使方差最小的 $b$ 是「以 $\|\nabla\log\pi\|^2$ 加权的回报均值」；工程上常直接用**状态价值 $V(s)$**（回报的期望）作近似，因为 $R-V(s)$ 恰好就是「优势」的直觉。**由此引出下一节。**

---

## 4. REINFORCE 及其痛点 → 逼出 actor-critic

### 4.1 REINFORCE（最朴素的策略梯度算法）

用蒙特卡洛采样直接估计策略梯度：跑完整条轨迹，用**实际回报** $G_t=\sum_{k\ge t}\gamma^{k-t}r_k$ 当权重：

$$
\nabla_\theta J \approx \frac{1}{N}\sum_i \sum_t \nabla_\theta \log \pi_\theta(a_t^i\mid s_t^i)\,\big(G_t^i - b(s_t^i)\big)
$$

流程：**采样整条轨迹 → 算回报 → 沿 $\nabla\log\pi\cdot(G-b)$ 更新**。简单、无偏。

### 4.2 痛点：高方差

- **蒙特卡洛回报 $G_t$ 本身方差极大**：它是一整条轨迹上所有随机性（动作采样 + 环境转移）的累积，越长的序列噪声越大。
- **必须等整条轨迹结束**才能更新（无法 bootstrapping），样本效率低。
- baseline 只能缓解、不能根治——因为 $G_t$ 这个「目标信号」自身就抖。

### 4.3 解法：用函数逼近替代蒙特卡洛回报 → actor-critic

既然 $G_t$ 太抖，就**训练一个网络去估计它的期望**，用低方差的估计值替代高方差的采样值：

- **Actor（策略 $\pi_\theta$）**：还是那个要优化的策略，负责「选动作」。
- **Critic（价值网络 $V_\phi(s)$）**：单独训练，估计状态价值 $V(s)=\mathbb{E}[G_t|s]$，负责「评估好坏」。

用 Critic 同时干两件事：
1. **当 baseline**：$b(s)=V_\phi(s)$，降方差（§3）。
2. **当 bootstrapping 目标**：用 $r_t+\gamma V_\phi(s_{t+1})$（TD target）替代整条 $G_t$，不必等轨迹结束、方差更低（引入少量偏差换大量方差下降，**偏差-方差权衡**）。

于是权重从「蒙特卡洛回报 $G_t$」升级为「**优势** $A(s,a)$」：

$$
\nabla_\theta J = \mathbb{E}\big[\nabla_\theta \log \pi_\theta(a\mid s)\,A(s,a)\big],\qquad A(s,a)=Q(s,a)-V(s)
$$

**动机链一句话总结**：
$$
\text{策略梯度定理} \xrightarrow{\text{加 baseline 降方差}} \text{REINFORCE} \xrightarrow{G_t\ \text{方差仍太大}} \text{用}\ V_\phi\ \text{替代回报} \Rightarrow \textbf{actor-critic}
$$

---

## 5. Q / V / A 三函数（优势概念的地基）

在策略 $\pi$ 下定义：

| 函数 | 定义 | 含义 |
|------|------|------|
| **状态价值 $V^\pi(s)$** | $\mathbb{E}_\pi[G_t \mid s_t=s]$ | 在状态 $s$、之后照策略走，能拿到的期望回报——**这个状态有多好** |
| **动作价值 $Q^\pi(s,a)$** | $\mathbb{E}_\pi[G_t \mid s_t=s, a_t=a]$ | 在 $s$ 先**强制**做 $a$、之后照策略走的期望回报——**在这个状态做这个动作有多好** |
| **优势 $A^\pi(s,a)$** | $Q^\pi(s,a) - V^\pi(s)$ | 动作 $a$ **相对该状态平均水平**好多少——**这个动作比「随大流」好还是差** |

### 关系与直觉

- $V(s) = \mathbb{E}_{a\sim\pi}[Q(s,a)]$：状态价值是动作价值按策略的加权平均。
- 由此 $\mathbb{E}_{a\sim\pi}[A(s,a)] = 0$：**优势在同一状态下均值为 0**——正好呼应 §3 的 baseline（用 $V(s)$ 当 baseline，回报就中心化成了优势）。
- **为什么用 $A$ 而非 $Q$ 或 $G$ 当权重**：$A$ 已经把「状态本身有多好」这个与动作无关的公共项（$V(s)$）减掉了，只留「动作的相对优劣」，**方差最低、且符号直接表达该更新方向**（$A>0$ 强化，$A<0$ 抑制）。

### 贝尔曼关系（bootstrapping 的来源，为 GAE 铺垫）

$$
Q^\pi(s,a) = r(s,a) + \gamma\, \mathbb{E}_{s'}\big[V^\pi(s')\big]
$$

于是**单步 TD 残差**恰好是优势的一个（有偏但低方差）估计：

$$
\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t) \approx A(s_t, a_t)
$$

- $\lambda=0$（纯 TD，用单步 $\delta_t$）：低方差、高偏差。
- $\lambda=1$（纯蒙特卡洛，用 $G_t-V$）：高方差、低偏差。
- **GAE**（广义优势估计）用 $\hat A_t=\sum_l (\gamma\lambda)^l \delta_{t+l}$ 在两极之间插值，是 PPO 的标配。详见 PPO 笔记。

---

## 6. 承上启下：这张地基如何长出后面所有算法

| 后续算法 | 它在策略梯度上做的事 |
|----------|----------------------|
| **actor-critic** | 用 $V_\phi(s)$ 当 baseline + bootstrapping，把 $G_t$ 换成 $A$ |
| **PPO**（见 [[14_ppo]]） | 优势用 GAE 估计；用重要性采样 + clip 限制单步更新幅度，可复用旧数据多步更新 |
| **GRPO**（见 [[9_grpo]]） | **砍掉 Critic**，改用「同一 prompt 采一组回答、组内均值/标准差」当 baseline——本质是 §3 baseline 思想的另一种实现 |
| **DPO** | 换个思路：不做在线策略梯度，直接对偏好数据的闭式最优解做分类损失（无显式优势/采样） |

**四条贯穿主线**（每个算法都可定位到这四坐标）：
1. **优势怎么估**：Critic（PPO）/ 组内均值（GRPO）/ 隐式（DPO）——都在回答 §3「baseline 取什么最好」。
2. **KL 约束放哪**：reward 里 / loss 里 / 隐式（见 [[13_unbiased_kl_estimate]]）。
3. **on/off-policy**：在线采样 vs 离线数据，训练-推理一致性。
4. **奖励来源**：RM / 规则(RLVR) / 偏好对 / 教师模型。

---

## 参考文献

- Sutton & Barto, *Reinforcement Learning: An Introduction*, 第 13 章（策略梯度定理原始推导）：http://incompleteideas.net/book/the-book-2nd.html
- Lilian Weng, *Policy Gradient Algorithms*（REINFORCE→A2C→TRPO→PPO 全谱系串讲）：https://lilianweng.github.io/posts/2018-04-08-policy-gradient/
- OpenAI Spinning Up, *Intro to Policy Optimization*（含完整推导 + 代码）：https://spinningup.openai.com/en/latest/spinningup/rl_intro3.html
- OpenAI Spinning Up, *Part 1: Key Concepts in RL*（MDP / Q / V / A 速览）：https://spinningup.openai.com/en/latest/spinningup/rl_intro.html
- Williams, *Simple Statistical Gradient-Following Algorithms (REINFORCE)*, 1992
- Schulman et al., *High-Dimensional Continuous Control Using GAE*：https://arxiv.org/abs/1506.02438
