# DPO（Direct Preference Optimization，直接偏好优化）

## 概述

**DPO（Direct Preference Optimization，直接偏好优化）** 是 Rafailov 等人（Stanford，NeurIPS 2023）提出的一种从人类偏好数据中对齐语言模型的后训练方法。它的核心贡献是：**用一个简单的二元分类损失，直接优化策略网络，从而完全绕过 RLHF 中「先训练奖励模型、再用 PPO 做强化学习」这两个复杂步骤**。

论文标题「Your Language Model is Secretly a Reward Model（你的语言模型其实暗藏一个奖励模型）」点出了关键洞见：通过对 RLHF 最优解的数学变换，**奖励函数可以用策略本身闭式表达出来**，于是不需要单独的奖励模型，语言模型自身就隐式地承担了奖励模型的角色。

DPO 稳定、轻量、易实现，是当前偏好对齐的主流基线方法之一。

## 核心原理与公式

### 1. RLHF 的目标（DPO 的出发点）

标准 RLHF 在 RL 阶段优化的是「带 KL 约束的奖励最大化」目标：

$$
\max_{\pi_\theta}\ \mathbb{E}_{x\sim\mathcal{D},\,y\sim\pi_\theta(y|x)}\big[r_\phi(x,y)\big]\ -\ \beta\, D_{KL}\big[\pi_\theta(y|x)\,\|\,\pi_{ref}(y|x)\big]
$$

其中 $\beta$ 控制与参考策略 $\pi_{ref}$（即 SFT 模型）的偏离程度。KL 约束防止模型偏离奖励模型准确的分布太远、并避免坍缩到单一高奖励答案。

### 2. 关键推导：奖励可用策略表达

上述带 KL 约束的目标有**闭式最优解**：

$$
\pi_r(y|x)=\frac{1}{Z(x)}\,\pi_{ref}(y|x)\exp\!\Big(\tfrac{1}{\beta}r(x,y)\Big)
$$

其中 $Z(x)$ 是配分函数，估计代价极高、难以直接使用。但对上式取对数、反解出奖励 $r$：

$$
r(x,y)=\beta\log\frac{\pi_r(y|x)}{\pi_{ref}(y|x)}+\beta\log Z(x)
$$

### 3. 配分函数被抵消

关键一步：Bradley-Terry 偏好模型只依赖两个回复的**奖励之差** $p^*(y_1\succ y_2)=\sigma(r^*(x,y_1)-r^*(x,y_2))$。把上面的奖励表达式代入，难算的 $\beta\log Z(x)$ 项在做差时**完全抵消**，于是偏好概率可以只用策略表达。

### 4. DPO 损失

最终得到 DPO 的目标——一个二元交叉熵（分类）损失：

$$
\mathcal{L}_{DPO}(\pi_\theta;\pi_{ref})=-\mathbb{E}_{(x,y_w,y_l)\sim\mathcal{D}}\Big[\log\sigma\Big(\beta\log\frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)}-\beta\log\frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}\Big)\Big]
$$

其中 $y_w$ 是被偏好回复、$y_l$ 是不被偏好回复。本质上是把奖励建模损失（式 2）里的显式奖励 $r_\phi$ 替换成了**隐式奖励** $\hat r_\theta(x,y)=\beta\log\frac{\pi_\theta(y|x)}{\pi_{ref}(y|x)}$。

### 5. 梯度的直观含义

$$
\nabla_\theta\mathcal{L}_{DPO}=-\beta\,\mathbb{E}\Big[\underbrace{\sigma(\hat r_\theta(x,y_l)-\hat r_\theta(x,y_w))}_{\text{排错越严重权重越大}}\big(\underbrace{\nabla_\theta\log\pi(y_w|x)}_{\text{提高}\,y_w}-\underbrace{\nabla_\theta\log\pi(y_l|x)}_{\text{降低}\,y_l}\big)\Big]
$$

即：**提高被偏好回复的概率、压低不被偏好回复的概率**，并按「隐式奖励把回复排错的程度」自适应加权。论文实验证明这个加权项至关重要——去掉它（朴素概率比目标）会导致模型退化（degeneration）。

## 与相关方法对比

| 维度 | RLHF (PPO) | **DPO** |
|------|-----------|---------|
| 奖励模型 | 显式单独训练 | **隐式，融入策略** |
| 训练阶段 | 两阶段（奖励+RL） | **单阶段** |
| 是否需 RL 采样 | 需要（在线 rollout） | **不需要（离线数据）** |
| 优化目标 | 策略梯度 / actor-critic | **二元交叉熵分类损失** |
| 稳定性 | 较不稳定、需调参 | **稳定** |
| baseline/价值函数 | 需要（降方差） | **不需要** |
| 计算开销 | 高 | **低** |

## 优势

1. **实现简单**：只需一个分类损失，几十行代码即可实现，无需奖励模型、无需 PPO 的复杂 rollout 循环。
2. **稳定、无需调参**：避免了 actor-critic 的高方差策略梯度，也不需要价值函数或 baseline。
3. **计算轻量**：训练时无需在线从模型采样，直接用离线偏好数据集。
4. **理论完备**：等价于拟合一个重参数化的 Bradley-Terry 模型，享有一致性等理论性质（定理 1 证明该重参数化不损失奖励模型的一般性）。
5. **效果好**：在情感控制、摘要、单轮对话上达到或超过 PPO-based RLHF。

## 局限性

1. **离线（off-policy）**：只在固定偏好数据集上训练，不像在线 RL 能持续探索新分布，容易过拟合偏好数据、对分布外样本泛化受限。
2. **对参考模型敏感**：$\pi_{ref}$ 选择不当会影响效果；且 $y_w, y_l$ 的采样分布若与 $\pi_{ref}$ 不匹配会引入偏移。
3. **可能过度优化**：实践中会出现「$y_w$ 和 $y_l$ 概率同时下降」的现象（只要相对差变大即可降低损失），可能压低整体生成质量。
4. **依赖成对偏好数据**：需要人工标注的偏好对，数据构建成本仍在。

## 在大模型中的应用

- **对齐主流基线**：Zephyr、Llama、Qwen 等大量开源模型的对齐流程中采用 DPO 或其变体。
- **衍生方法众多**：IPO（缓解过拟合）、KTO（无需成对偏好，用单条好/坏样本）、ORPO（合并 SFT 与偏好优化）、SimPO（去掉参考模型）等，都是在 DPO 框架上的改进。
- **RLHF 的轻量替代**：在算力受限或追求训练稳定性时，常用 DPO 替代 PPO。

## 与后训练的关联

DPO 是**后训练偏好对齐**谱系中的关键一环，直接对应 RLHF 三阶段中的第三阶段（RL 优化），但把它简化为监督式的分类问题。理解 DPO 需要先掌握 [[16_reward_model]]（Bradley-Terry 建模与奖励损失）和 [[14_ppo]]（它要替代的 RL 方法），KL 约束部分可参考 [[13_unbiased_kl_estimate]]。与 [[9_grpo]]、[[18_dapo]] 等在线 RL 方法相比，DPO 走的是离线、无奖励模型的路线——这也是理解「on-policy vs off-policy 对齐」的核心分界点（参见 [[21_on_policy_distillation]]）。

## 参考文献

- Rafailov, Sharma, Mitchell, Ermon, Manning, Finn, "Direct Preference Optimization: Your Language Model is Secretly a Reward Model" (NeurIPS 2023, arXiv:2305.18290).
- Christiano et al., "Deep Reinforcement Learning from Human Preferences" (2017).
- Bradley & Terry, "Rank Analysis of Incomplete Block Designs" (1952).
