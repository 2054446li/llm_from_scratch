# RLHF / 后训练 RL 学习 Plan（一个月）

> 目标：以**后训练工程师**视角，把 RLHF 完整流水线过一遍，重点打牢强化学习这一块——PPO → GRPO → DPO 及其变体 → OPD（On-Policy Distillation）。
> 形式：论文精读 → `code/` 下实现核心代码 → `common_knowledge/` 下沉淀知识点。本文件只做**规划与串联**，不含具体实现。
> 前置：SFT 已掌握（本 plan 不再展开），假设已理解 Transformer、AdamW、交叉熵、softmax。

---

## 0. 一张图看懂 RLHF 全景（先建立地图，再逐块深入）

RLHF 的本质：**用人类偏好信号，把 SFT 模型进一步对齐到「人更喜欢的输出分布」**。经典三段式（InstructGPT）：

```
预训练 (Pretrain)                    ← 能力上界的来源
      │
      ▼
①  SFT (监督微调)                     ← 已掌握，本 plan 跳过
      │  教模型「模仿」示范回答
      ▼
②  RM (奖励模型训练)                   ← 从人类偏好学一个打分器
      │  pairwise 比较 → 标量奖励
      ▼
③  RL (策略优化：PPO/GRPO/...)         ← 本 plan 重点
      │  用 RM 的分数当奖励，优化策略
      ▼
   对齐后的模型
```

**近两年的分叉**（本 plan 都要覆盖）：

1. **绕开显式 RM 与在线采样 → DPO 路线**：把「RM + RL」合并成一个对偏好数据的分类损失，无需在线 rollout。衍生 IPO / KTO / ORPO / SimPO 等。
2. **绕开 reward model 的主观性 → RLVR（可验证奖励）**：数学/代码这类有标准答案的领域，直接用规则/编译器/答案校验当奖励。这是 DeepSeek-R1、GRPO reasoning 的主线，也是当前最前沿。
3. **多领域能力融合 → OPD（On-Policy Distillation）**：先分域 RL 练强，再用 on-policy 蒸馏合一（DeepSeek-V4 后训练范式）。
4. **从单轮对齐 → Agentic RL（多轮+工具+长程）**：把 RL 扩展到多轮、与环境交互、会调工具的长程决策。复用 GRPO/RLVR 内核，叠加「长程信用分配 + 工具 token mask + 异步 off-policy rollout」三个增量维度。当前爆发方向，秋招高频。

**入门总纲（先读，建立全局观，反复回看）**：
- HuggingFace, *RLHF: Reinforcement Learning from Human Feedback*（图解博客，最佳一图入门）：https://huggingface.co/blog/rlhf
- Chip Huyen, *RLHF: Reinforcement Learning from Human Feedback*：https://huyenchip.com/2023/05/02/rlhf.html
- Nathan Lambert, *RLHF Book*（正在写的开源系统教材，本 plan 多处引用，强烈推荐通读）：https://rlhfbook.com/
- Lilian Weng, *Reward Hacking in RL*（贯穿全程的「奖励从哪来、如何被钻空子」总览）：https://lilianweng.github.io/posts/2024-11-28-reward-hacking/

**贯穿全程的核心矛盾**（每读一篇都回到这几个问题）：
- 优势（advantage）怎么估？要不要 Critic？→ PPO(要) vs GRPO(不要)
- KL 约束放哪、怎么算？→ reward 里 vs loss 里；k1/k2/k3 估计器
- on-policy 还是 off-policy？训练-推理一致性如何保证？→ 大规模 RL 的稳定性核心
- 奖励从哪来？RM / 规则 / 编译器 / 更强模型 → reward hacking 如何防

---

## 阶段总览（5 周 + 缓冲）

| 周 | 主题 | 主线问题 | 核心产出 |
|----|------|----------|----------|
| **Week 1** | RL 基础 + 奖励模型 | 策略梯度怎么来的？RM 怎么训？ | 知识点：策略梯度、RM；代码：BT-loss RM |
| **Week 2** | PPO 与 RLHF 经典范式 | PPO 为什么长这样？RLHF 四模型怎么转？ | 知识点：PPO/GAE/actor-critic；代码：mini-PPO |
| **Week 3** | GRPO + RLVR + reasoning RL | 去掉 Critic 后如何稳？可验证奖励如何激发推理？ | 已有 GRPO 笔记查漏补缺；代码：GRPO；串 DeepSeek-Math/R1 |
| **Week 4** | DPO 系列 + OPD + 稳定性前沿 | 能否绕开 RL？多领域能力如何融合？ | 知识点：DPO 及变体、OPD；代码：DPO |
| **Week 5** | Agentic RL（多轮+工具+长程） | 单轮 RL 如何扩展到多轮带工具的长程决策？ | 知识点：agentic_rl（三增量维度）；只读为主，代码可选 |
| 缓冲 | 综述串联 + 面试题 | 把五周串成一条叙事 | 综述文档 + QA |

> 已有资产（避免重复造轮子，直接复用/查漏）：
> - `common_knowledge/9_grpo.md` — GRPO 已较完整，Week 3 主要做查漏与代码
> - `common_knowledge/10_process_reward_model.md` — 过程奖励模型 PRM
> - `common_knowledge/13_unbiased_kl_estimate.md` — k1/k2/k3 KL 估计 + V3.2 离策略修正
> - `industry_reports/deepseek/` 下 Math / R1 / Prover / V3.2 / V4 阅读笔记

---

## Week 1 — RL 基础语言 + 奖励模型（打地基）

> **本周主线**：RL 不是黑盒。先把「策略梯度」这个所有算法的共同祖先推清楚，再理解 RLHF 里「奖励从哪来」——奖励模型 RM。搞懂这两件事，PPO/GRPO/DPO 才不是背公式。

### Day 1-2：强化学习最小必要基础

不需要啃完整本 Sutton，只取 RLHF 用得到的部分。**要逐条掌握的知识点**：
- MDP 五元组（状态、动作、转移、奖励、折扣）、轨迹、回报（return）、折扣因子 γ —— 但注意 LLM RLHF 里通常是**序列级 bandit 视角**（一整条回答=一个动作，token 级则是逐步 MDP），折扣常设为 1。
- **策略梯度定理**：`∇J(θ) = E[∇log π_θ(a|s) · R]`。要能自己从 `J(θ)=E_τ[R(τ)]` 推一遍（log-derivative trick：`∇p = p·∇log p`）。
- **baseline 降方差**：`∇J = E[∇log π · (R - b)]`，减 baseline 不改期望（因 `E[∇log π]=0`）但降方差。→ 后面 Critic / 组内均值 / GAE 的共同动机。
- **REINFORCE** 算法及其高方差痛点 → 引出 actor-critic。
- **Q / V / A 三个函数**的定义与关系：`A(s,a)=Q(s,a)-V(s)`，为「优势」概念铺垫。
- 折扣回报 vs TD（时序差分）：bootstrapping 的思想，为 GAE 铺垫。

**产出**：`common_knowledge/{N}_policy_gradient.md` — 策略梯度定理推导、baseline 降方差、log-derivative trick、REINFORCE→actor-critic 的动机链、Q/V/A 定义。这是后面所有 RL 笔记的锚点，务必扎实。

**推荐材料（按优先级）**：
- Lilian Weng, *Policy Gradient Algorithms*（公认最佳串讲，REINFORCE→A2C→TRPO→PPO 全谱系）：https://lilianweng.github.io/posts/2018-04-08-policy-gradient/
- OpenAI Spinning Up, *Intro to Policy Optimization*（含策略梯度完整推导 + 代码）：https://spinningup.openai.com/en/latest/spinningup/rl_intro3.html
- OpenAI Spinning Up, *Part 1: Key Concepts in RL*（MDP/Q/V/A 速览）：https://spinningup.openai.com/en/latest/spinningup/rl_intro.html
- （可选深挖）Sutton & Barto, *Reinforcement Learning: An Introduction* 第 13 章（策略梯度）：http://incompleteideas.net/book/the-book-2nd.html

### Day 3-5：奖励模型（Reward Model）

RLHF 的「偏好信号入口」。搞懂这个才知道 PPO/GRPO 优化的奖励到底是什么、为什么会被 hack。**要逐条掌握的知识点**：
- **Bradley-Terry 模型**：把 pairwise 偏好 `y_w ≻ y_l` 转成概率 `P(y_w≻y_l)=σ(r(y_w)-r(y_l))`，RM 训练损失即 `L=-log σ(r_w - r_l)`。要能纯文本写出并解释每一项。
- **RM 结构**：SFT 模型去掉 LM head，接一个标量输出头；只在**最后一个 token** 输出奖励。→ 联系 `9_grpo.md` 里「奖励只给最后 token 导致逐 token 价值难估」的痛点。
- **数据格式**：`(prompt, chosen, rejected)` 三元组；标注一致性、偏好数据来源（人工 vs AI）。
- **reward hacking / over-optimization**：Goodhart's law、长度偏置（越长分越高）、分布外脆弱、KL-reward 权衡曲线（over-optimize 后真实偏好反降）。→ 为 Week 3 RLVR / Week 4 SimPO 长度控制埋伏笔。
- **RLAIF**：用 AI 反馈替代人工标注（Constitutional AI）；与 RLHF 的异同。
- **过程奖励 vs 结果奖励**：直接复用已有 `10_process_reward_model.md`，本周回顾并与 RM 对照。
- **RM 的替代**：为什么后来 DPO 想干掉显式 RM、RLVR 想用规则替代 RM——本周先建立「RM 是瓶颈」的认知。

**产出**：
- `common_knowledge/{N+1}_reward_model.md` — BT 模型推导、损失、结构、数据格式、reward hacking 与缓解、RLAIF、与 PRM/RLVR 的关系。
- `code/reward_model_bt.ipynb` — 用小 backbone 实现 BT-loss pairwise RM 训练最小可跑版本。

**推荐材料（按优先级）**：
- InstructGPT, *Training language models to follow instructions with human feedback*（RLHF 奠基，RM 章节；Week 2 还会读它的 PPO 部分）：https://arxiv.org/abs/2203.02155
- Bradley & Terry 原始模型 + 讲解，见 RLHF Book 的 Reward Modeling 章：https://rlhfbook.com/c/07-reward-models.html
- *Scaling Laws for Reward Model Overoptimization*（Gao et al., 量化 over-optimization 与 KL 关系，必读）：https://arxiv.org/abs/2210.10760
- *Secrets of RLHF Part I: PPO*（reward hacking / 长度偏置的实证）：https://arxiv.org/abs/2307.04964
- Anthropic, *Constitutional AI: Harmlessness from AI Feedback*（RLAIF 视角，Week 4 呼应）：https://arxiv.org/abs/2212.08073
- Lilian Weng, *Reward Hacking in RL*（同上，本周精读缓解章节）：https://lilianweng.github.io/posts/2024-11-28-reward-hacking/

### Week 1 自检
- 能否不看公式推出策略梯度定理，并说清 baseline 为什么降方差？
- 能否写出 BT 损失，并解释 RM 为什么容易被 length hack、over-optimize？
- 能把「策略梯度的 baseline」和「GRPO 的组内均值」「PPO 的 Critic」在动机上连起来吗？

---

## Week 2 — PPO 与 RLHF 经典范式（吃透主力算法）

> **本周主线**：PPO 是 RLHF 十年的主力，也是 GRPO/DPO 全都在「相对它做减法」的基准。必须吃透它每一个设计为什么存在，后面的变体才能秒懂。

### Day 1-2：从 TRPO 到 PPO 的动机链

**要逐条掌握的知识点**：
- **为什么不能直接用策略梯度更新**：步长敏感，一步走大策略就崩（分布剧变）。→ TRPO 用信任域（KL 约束）限制每步更新幅度。
- **TRPO**：代理目标 + KL 硬约束，为什么理论漂亮但工程重（二阶、共轭梯度）。
- **PPO 的简化**：把 TRPO 硬约束换成 **clip 裁剪** 的重要性采样比 `ratio=π_θ/π_θ_old`。要能纯文本写出裁剪目标 `L=E[min(ratio·A, clip(ratio,1-ε,1+ε)·A)]`，并解释 clip 在 A>0 / A<0 时分别防止什么（A>0 防更新过头、A<0 防塌陷）。
- **PPO 两种形式**：clip 版 vs KL-penalty 版，为什么 clip 版成为主流。
- **重要性采样**：为什么 PPO 能用旧策略采的数据做多步 minibatch 更新（近似 on-policy）→ 理解「名义 on-policy 实际 off-policy」的起点，直连 `13_unbiased_kl_estimate.md`。
- **熵正则 / entropy bonus**：鼓励探索、防早熟收敛（埋到 DAPO 的 Clip-Higher 防熵坍缩）。

### Day 3-4：GAE 与 actor-critic

**要逐条掌握的知识点**：
- **优势函数 A(s,a)=Q-V**，为什么用优势而非直接用回报（降方差 + 表达「相对好坏」）。
- **GAE（广义优势估计）**：`Â_t = Σ (γλ)^l δ_{t+l}`，用 λ 在偏差-方差间插值。要能讲清 λ=0（=TD，低方差高偏差）和 λ=1（≈MC，高方差低偏差）两极。
- **Critic（Value 网络）训练**：MSE 回归到回报/TD target。→ 联系 `9_grpo.md`：GRPO 砍的正是这个 Critic。
- **value clipping / 归一化**、优势归一化等工程技巧（37 details 里的常见坑）。

### Day 5：RLHF 里的 PPO 全貌（四模型协同）

这是把前面拼成完整流水线的关键一天：

```
RLHF-PPO 的四个模型：
  ① Policy (Actor)      —— 待训练，从 SFT 初始化
  ② Value  (Critic)     —— 估计 V(s)，与 Policy 同量级（GRPO 要砍的就是它）
  ③ Reward Model (冻结) —— Week 1 训好的 RM，给整条回答打分
  ④ Reference (冻结)    —— SFT 快照，算 KL 防止跑偏
```

- **奖励怎么组装**：`最终 reward = RM 分数 - β·KL(π_θ ‖ π_ref)`，KL 逐 token 加在 reward 上（对比 GRPO 把 KL 加进 loss——见 `9_grpo.md` 的三差异表）。
- 显存痛点：4 个模型里 2 个可训、要过前向，这就是 GRPO/DPO 存在的根本工程动机。

**产出**：
- `common_knowledge/{N}_ppo.md` — TRPO→PPO 动机、clip 目标、重要性采样、GAE、actor-critic、RLHF 四模型协同与 KL 位置。**显式对照 `9_grpo.md`，标注 GRPO 是在哪几处做的减法。**
- `code/ppo_minimal.ipynb` — 最小 PPO：clip 目标 + GAE + Critic。可先在玩具环境（如 CartPole 或一个 tiny LM 对齐任务）跑通，重点体会 clip 和 advantage 的作用。

**推荐材料（按优先级）**：
- Schulman et al., *Proximal Policy Optimization Algorithms*（PPO 原始论文，短而经典）：https://arxiv.org/abs/1707.06347
- Schulman et al., *Trust Region Policy Optimization*（TRPO，理解 PPO 的前身）：https://arxiv.org/abs/1502.05477
- Schulman et al., *High-Dimensional Continuous Control Using GAE*（GAE 原始论文）：https://arxiv.org/abs/1506.02438
- Huang et al., *The 37 Implementation Details of PPO*（ICLR blog，工程细节神文，面试常考的坑都在这）：https://iclr-blog-track.github.io/2022/03/25/ppo-implementation-details/
- Hugging Face, *Illustrating RLHF*（PPO 在 RLHF 中如何组装四模型，图解）：https://huggingface.co/blog/rlhf
- RLHF Book, *Policy Gradient Algorithms* 章（PPO/GAE 在 RLHF 语境的推导）：https://rlhfbook.com/c/11-policy-gradients.html
- InstructGPT PPO 部分（https://arxiv.org/abs/2203.02155）+ *Secrets of RLHF Part I*（PPO 稳定性调参实证，https://arxiv.org/abs/2307.04964）

### Week 2 自检
- 能纯文本默写 PPO clip 目标，并解释 A>0/A<0 时 clip 各防什么？
- 能画出 RLHF-PPO 四模型数据流，说清每个模型冻不冻、KL 加在哪？
- 能一句话说清 GRPO 相对 PPO 砍了什么、省了多少显存？（承上启下到 Week 3）

---

## Week 3 — GRPO + RLVR + Reasoning RL（当前主战场）

> **本周主线**：这是你作为后训练工程师最该吃透的一块——**去 Critic 的 RL + 可验证奖励，如何在推理任务上激发能力**。GRPO 笔记已较完整，本周做「查漏 + 代码落地 + 用 DeepSeek 系列串成一条工程叙事」。

### Day 1：GRPO 查漏（复用已有笔记）

`9_grpo.md` 已覆盖动机、公式、与 PPO 三差异、过程/结果监督、迭代式 GRPO、以及「RL 提升 Maj@K 不提升 Pass@K」这一关键认知。本日只做**查漏**，确认能回答：
- 组内归一化优势 `Â = (r - mean)/std` 为什么能替代 Critic？隐含假设是什么（组内可比、同 prompt）？
- KL 为什么改放进 loss、且用 k3 无偏估计？→ 交叉引用 `13_unbiased_kl_estimate.md`。
- **std 归一化的争议**：DAPO 指出除以 std 会引入难度偏置（简单题 std 小 → 优势被放大），埋到 Day 3 变体处理。

### Day 2：RLVR —— 可验证奖励（范式转折点）

RLHF 从「RM 打分」转向「规则/答案校验」的关键一跳，是 R1 能纯 RL 涌现推理的前提。**要逐条掌握的知识点**：
- **核心思想**：数学/代码有客观正确性，直接用「答案是否正确 / 单测是否通过 / Lean 是否编译」当 0-1 奖励，绕开 RM 的主观性与训练成本。
- **为什么 RLVR + GRPO 是绝配**：可验证奖励天然适合组内比较（同题多解、有对有错 → std 有意义），且无需训 RM。
- **格式奖励 vs 结果奖励**：R1 用 `<think>` 格式奖励 + 答案奖励的组合；格式奖励如何引导可读性。
- **局限**：只适用于有 verifier 的领域；开放域（写作、对话）仍需 RM 或 RLAIF。
- **RLVR 下的 reward hacking 转移**：不再是「拍马屁」，而是「猜答案不推理」「钻格式空子」「答案对但过程错」——引出过程奖励 PRM 的价值（复用 `10_process_reward_model.md`）。

**产出**：`common_knowledge/{N}_rlvr.md` — 可验证奖励定义、与 RM 的对比、适用边界、与 GRPO 的组合、reward hacking 在 RLVR 下如何转移。

**推荐材料**：
- DeepSeek-R1 论文（RLVR + GRPO 激发推理的典范）：https://arxiv.org/abs/2501.12948
- Lambert et al., *Tülu 3*（RLVR 一词的系统化提出与开源配方）：https://arxiv.org/abs/2411.15124
- RLHF Book, *Reasoning & RL* 相关章：https://rlhfbook.com/

### Day 3：GRPO 的变体（前沿必读）

理解社区在 GRPO 上打的补丁，面试高频。**核心心法：几乎所有变体都在改 GRPO 的三个轴——① 归一化方式（去长度/去 std 偏置）② 裁剪策略（阈值/粒度/软化）③ 损失聚合与信用分配粒度（token 级 vs 序列级）**。读的时候先问「它动了哪个轴、解决什么病」。

**第一梯队（必读，已成社区标准基线）：**
- **DAPO**（字节，2025）：四件套——① Clip-Higher（解耦上下裁剪阈值 ε_low/ε_high，放宽上界防熵坍缩）② 动态采样（过滤全对/全错的零梯度组）③ Token-level 损失（而非样本级平均，长回答不被稀释）④ 超长回答软惩罚 + 去 std 归一化。已成后续论文的「代表性基线」。论文：https://arxiv.org/abs/2503.14476
- **Dr. GRPO**（Sea AI Lab，*Understanding R1-Zero-Like Training*，2025）：指出 GRPO 的**长度偏置**（除以 |o| 让长回答被稀释）与**难度偏置**（除以 std 让简单题优势被放大），去掉这两个归一化，提升 token 效率。论文：https://arxiv.org/abs/2503.20783 ｜ 代码：https://github.com/sail-sg/understand-r1-zero
- **GSPO**（Qwen，*Group Sequence Policy Optimization*，2025）：把 token 级重要性比改为**序列级**，缓解长序列上 token-ratio 连乘的高方差，尤其**稳定 MoE 的 RL 训练**（Qwen3 采用）。论文：https://arxiv.org/abs/2507.18071 ｜ 博客：https://qwenlm.github.io/blog/gspo/

**第二梯队（前沿扩展，按「改哪个轴」归类记忆）：**

*轴②裁剪策略 —— 重要性权重怎么裁、在哪个粒度裁：*
- **CISPO**（MiniMax-M1，2025）：不裁「token 的更新」，而是**裁重要性采样权重本身**，让低概率 token 也能贡献梯度，降方差、稳 off-policy 微调。论文：https://arxiv.org/abs/2506.13585
- **GMPO**（Geometric-Mean PO，2025）：把 token 级奖励的**算术平均换成几何平均**，对离群 token 更不敏感、把 ratio 稳在更小范围。论文：https://arxiv.org/abs/2507.20673 ｜ 代码：https://github.com/callsys/GMPO
- **Clip-Higher / Clip-Lower / Clip-Tighter 家族**：系统研究上下裁剪阈值对熵的非对称影响（放宽上界防熵坍缩 vs 收紧下界防负优势 token 被过压）。综述见「熵坍缩」一节。

*轴③信用分配 —— 打破「同一回答所有 token 共享一个奖励」的粗粒度：*
- **GTPO / GRPO-S**（*Token and Sequence-Level Reward Shaping with Policy Entropy*，2025）：用**熵加权**给每个 token 分配不同奖励（GTPO token 级 / GRPO-S 序列级），改善长 CoT 的稳定性。论文：https://arxiv.org/html/2508.04349
- **ASPO**：非对称重要性加权，缓解优化偏置与不稳定。

*正交主题 —— 熵坍缩（entropy collapse，几乎所有变体的共同敌人）：*
- RLVR 训练中策略熵会快速坍缩→过早失去探索。这是 Clip-Higher 等一系列裁剪技巧的共同动机。综述：*Understanding and Preventing Entropy Collapse in RLVR*（https://aclanthology.org/2026.findings-acl.879.pdf）、*Revisiting Entropy in RL for Large Reasoning Models*（https://arxiv.org/abs/2511.05993）

> **速览版图（2026）**：三个轴 = **归一化偏置**（Dr.GRPO）×**裁剪**（DAPO/CISPO/GMPO/Clip-家族）×**信用分配粒度**（GSPO/GTPO/GRPO-S），共同敌人是**熵坍缩**。面试只需记住第一梯队 DAPO/Dr.GRPO/GSPO + 会用「三个轴」把任何新变体归位即可。综述可读 Turing Post *Reasoning RL in 2026* 与 Sebastian Raschka *State of RL for LLM Reasoning*。

**产出**：新建 `common_knowledge/{N}_grpo_variants.md`——按「三个轴 + 熵坍缩」组织，每个变体一行说清「改了哪个轴、治什么病」，第一梯队详写、第二梯队列表。交叉引用 [[9_grpo]]、[[14_ppo]]、[[13_unbiased_kl_estimate]]。

### Day 4：Reasoning RL 的完整流水线（串 DeepSeek）

把算法放进真实工程管线，复用已有阅读笔记：
- **DeepSeek-Math**：GRPO 起源，读 `deepseek_math_reading_notes.md`。论文：https://arxiv.org/abs/2402.03300
- **DeepSeek-R1**：冷启动 SFT → 推理 RL → 拒绝采样 SFT → 最终对齐 RL 的四段式；R1-Zero 纯 RL 涌现。读 `deepseek-R1_reading_notes.md`。论文：https://arxiv.org/abs/2501.12948
- **DeepSeek-V3.2**：可扩展 RL 的稳定性配方（离策略修正、路由保持、采样掩码），读 `deepseek_v32_reading_notes.md` + `13_unbiased_kl_estimate.md`。论文：https://arxiv.org/abs/2512.02556
- 重点想清楚：**为什么 reasoning RL 要「SFT 冷启动 + RL」而非纯 RL**？（R1-Zero 可读性/语言混杂问题）

### Day 5：代码落地

**产出**：`code/grpo_minimal.ipynb` — 最小 GRPO：组采样 → 组内归一化优势 → clip 目标 + KL(k3)。用一个可验证奖励的玩具任务（如「生成算式并校验结果」），亲手体会「无 Critic」和「组内基线」。对照 Week 2 的 mini-PPO，直观看到砍掉 Critic 后代码少了哪一块。

**参考实现（读代码用，不必自己造全套）**：
- HuggingFace TRL `GRPOTrainer`：https://huggingface.co/docs/trl/main/en/grpo_trainer
- veRL（火山引擎，工业级 RL 框架，DAPO 官方实现基于它）：https://github.com/volcengine/verl
- OpenRLHF：https://github.com/OpenRLHF/OpenRLHF

### Week 3 自检
- 能说清 RLVR 相对 RM 的本质区别，及各自适用边界？
- DAPO 的 Clip-Higher 解决什么问题？为什么 std 归一化有难度偏置？
- 能默画 R1 四段式训练流程，并解释每段目的？

---

## Week 4 — DPO 系列 + OPD + 稳定性前沿（收口与融合）

> **本周主线**：两个方向收口。其一，**能否绕开在线 RL？**——DPO 把「RM+RL」压成一个离线分类损失，及其变体谱系。其二，**多领域能力如何融合？**——OPD（on-policy 蒸馏），DeepSeek-V4 的后训练范式。

### Day 1-2：DPO —— 直接偏好优化（离线路线的奠基）

**要逐条掌握的知识点**：
- **核心洞察**：RLHF（KL 正则的 reward 最大化）有闭式最优解 `π*(y|x) ∝ π_ref(y|x)·exp(r(x,y)/β)`，反解出 `r(x,y)=β·log(π*/π_ref)+β·log Z(x)`。
- **消掉奖励**：把上式代回 BT 模型，配分函数 `Z(x)` 在 pairwise 差中抵消，得到只依赖策略的分类损失——不需显式 RM，也不需在线采样。
- **DPO 损失**：`L=-log σ(β·[log(π_θ(y_w)/π_ref(y_w)) - log(π_θ(y_l)/π_ref(y_l))])`，要能纯文本写出并解释「拉高 y_w、压低 y_l」的直觉。
- **隐式奖励与隐式 KL**：`β·log(π_θ/π_ref)` 就是隐式奖励；β 控制隐式 KL 约束强度。
- **DPO vs PPO 权衡**：DPO 简单稳定省资源，但**离线**（无法探索偏好数据外的新回答），对偏好数据分布敏感、易过拟合、有长度偏置。理解「on/off-policy」主线在 DPO 上的体现——这是 DPO 与 GRPO 的根本分野。
- **DPO 的失效点**：分布偏移（π_ref 与偏好数据不匹配时）、likelihood 双降现象（chosen 概率也可能下降）。

**产出**：`common_knowledge/{N}_dpo.md` — 从 RLHF 最优解到 DPO 损失的完整推导、隐式奖励、β 含义、与 PPO/GRPO 的 on/off-policy 对比、局限与失效点。

**推荐材料（按优先级）**：
- Rafailov et al., *Direct Preference Optimization: Your Language Model is Secretly a Reward Model*（DPO 原始论文，推导必须逐行看懂）：https://arxiv.org/abs/2305.18290
- RLHF Book, *Direct Alignment Algorithms* 章（DPO 推导 + 变体谱系的最佳系统讲解）：https://rlhfbook.com/c/12-direct-alignment.html
- HuggingFace TRL `DPOTrainer` 文档（实现视角）：https://huggingface.co/docs/trl/main/en/dpo_trainer

### Day 3：DPO 变体谱系（面试高频对比）

按「改了 DPO 的哪一处」组织记忆——**核心三问：要不要 ref 模型、要不要成对数据、如何处理长度偏置**。逐条掌握：
- **IPO**（*A General Theoretical Paradigm...*）：加正则防 DPO 对确定性偏好过拟合。论文：https://arxiv.org/abs/2310.12036
- **KTO**（Kahneman-Tversky Optimization）：用前景理论，**只需二元「好/坏」标签**（不需成对），数据更易得。论文：https://arxiv.org/abs/2402.01306
- **ORPO**（Odds Ratio PO）：把 SFT 与偏好对齐**合成一步**、**无需 ref 模型**，加 odds-ratio 惩罚。论文：https://arxiv.org/abs/2403.07691
- **SimPO**：**去掉 ref 模型**，用长度归一的平均对数概率当隐式奖励 + target margin，直接解决 DPO 的长度偏置。论文：https://arxiv.org/abs/2405.14734 ｜ 代码：https://github.com/princeton-nlp/SimPO
- 一句话串：DPO 变体主要在动三样——ref 模型、成对数据、长度偏置。

**产出**：`common_knowledge/{N+1}_dpo_variants.md` 或在 dpo 笔记追加对比表（IPO/KTO/ORPO/SimPO 各改了什么、解决什么、是否需 ref/成对）。

### Day 4：OPD —— On-Policy Distillation（能力融合前沿）

你点名要重点的部分，也是 DeepSeek-V4 的后训练核心。**要逐条掌握的知识点**：
- **是什么**：学生自己采样（on-policy），教师在**学生的输出分布上**打分/给 token 级监督（通常 reverse-KL 损失），把知识蒸给学生。区别于离线蒸馏（学生学教师采的固定数据）。
- **为什么 on-policy 更好**：训练-推理分布一致（呼应贯穿全程的一致性主线），避免离线蒸馏的**曝光偏差 exposure bias**；reverse-KL 的 mode-seeking 特性防止学生把概率质量摊到教师认为不可能的区域。
- **与 RL / 离线蒸馏的定位**：OPD = 「on-policy 采样（像 RL）+ 教师密集 token 级信号（像蒸馏）」，信号比稀疏奖励 RL 更密、比离线蒸馏更 on-policy。
- **DeepSeek-V4 的「分而治之 + OPD 统一」范式**：先用 SFT+GRPO 把各领域专家分别练强 → 再用 OPD 把多个专家合并进单一模型，解决多领域 RL 互相干扰、能力此消彼长。读 `deepseek_v4.pdf` 后训练章节（`deepseek_technical_details.md` L494-500 已有摘要）。
- **GKD**：Agarwal 的 Generalized KD，OPD 的理论框架（on/off-policy 数据插值 + 多种散度）。

**产出**：`common_knowledge/{N}_on_policy_distillation.md` — OPD 定义、reverse-KL、vs 离线蒸馏（曝光偏差）、vs RL（信号密度）、训练-推理一致性动机、V4 分域+统一范式、GKD 框架。交叉引用 `9_grpo.md`、`13_unbiased_kl_estimate.md`。

**推荐材料（按优先级）**：
- Thinking Machines Lab (Kevin Lu et al.), *On-Policy Distillation*（最佳入门，含 Tinker 复现 Qwen3 结果）：https://thinkingmachines.ai/blog/on-policy-distillation/
- Agarwal et al., *On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes (GKD)*（ICLR 2024，理论奠基）：https://arxiv.org/abs/2306.13649
- Gu et al., *MiniLLM: Knowledge Distillation of LLMs*（首次为 LLM 形式化 reverse-KL 的 OPD）：https://arxiv.org/abs/2306.08543
- DeepSeek-V4 论文后训练章：https://arxiv.org/abs/2606.19348
- awesome-on-policy-distillation（论文/框架合集）：https://github.com/chrisliu298/awesome-on-policy-distillation

### Day 5：代码 + 稳定性收尾

**产出**：
- `code/dpo_minimal.ipynb` — 最小 DPO：给定偏好对，实现 DPO 损失、计算隐式奖励、对比 chosen/rejected logprob 变化。对比 Week 3 GRPO，直观感受「离线无采样」的差异。
- 回顾大规模 RL 稳定性配方（复用 `13_unbiased_kl_estimate.md`）：离策略修正、KL 强度按领域调（可验证域弱 KL）、训练-推理一致性。这是把四周所有算法落到生产的共同底座。

### Week 4 自检
- 能推导 DPO 损失从何而来（最优解闭式 → 代入 BT → 消掉奖励）？
- DPO 为什么是 off-policy？相比 GRPO 的取舍是什么？
- OPD 为什么比离线蒸馏好？V4 为什么要「先分域 RL 再 OPD 统一」？

---

## Week 5 — Agentic RL（多轮 + 工具 + 长程，当前爆发方向）

> **本周主线**：把 RL 从「单轮生成一段回答」扩展到「多轮、与环境交互、会调工具的长程决策」。**核心认知：Agentic RL 不推翻你已学的 GRPO/RLVR 内核，而是在其上叠三个增量维度——① 多轮长程信用分配 ② 工具结果 token mask（训练-推理一致性）③ 长轨迹的 off-policy / 异步吞吐。** 目标是「了解流程 + 讲清面试要点」，本周以只读为主（无卡、不碰数据），代码可选做最小 rollout 骨架。

> **本周主教材（跟读主线）**：小red（美团 M17 基座 agent 后训练）整理的开源系列 **Agentic-RL-Most-Detailed-Intro**：https://github.com/XiaoRed5/Agentic-RL-Most-Detailed-Intro
> 在线阅读（GitHub Pages，无需 clone）：https://xiaored5.github.io/Agentic-RL-Most-Detailed-Intro/
> 该仓库分三条线：**① 论文阅读入门系列 1-6**（本周逐篇跟读，作为下面 5 天的骨架）、**② 代表工作深读**（LongCat 2.0 / GLM-5.2 长程 RL / Kimi-K3，放到 Day 5）、**③ agentic-tau-rl 代码实战**（可运行可单测的多轮 rollout+信用分配+策略优化实现，Day 5 可选跑）。
> **读法**：入门系列每篇作为当天的「先导材料」先读，读完再回到本 plan 的「三增量维度」框架做归位——即每读一篇都问「它落在①信用分配 / ②token mask 一致性 / ③off-policy 吞吐 哪个维度」。下面每天标注了对应仓库篇目。
>
> **入门系列 → 本周天数映射（一览）**：
> | 仓库篇目 | 对应本周 | 落在哪个增量维度 |
> |----------|----------|------------------|
> | 入门1 基础、代码 | Day 1 | 问题设定（bandit→MDP） |
> | 入门2 信用分配 | Day 2 | ①长程信用分配（核心） |
> | 入门4 Credit 错分与算法接口 | Day 2 | ①信用分配的失效与接口 |
> | 入门6 多轮工具调用 | Day 3 | ②TIR + token mask |
> | 入门3 transformer 架构 | Day 4 | 长上下文/长轨迹的架构支撑 |
> | 入门5 Skill-based Agentic RL | Day 4 | 技能/分层视角 |
> | 代表工作（LongCat/GLM-5.2/Kimi-K3） | Day 5 | 三维度在真实系统中的落地 |
> | agentic-tau-rl 代码实战 | Day 5（可选） | ①②③ 全串 |

### Day 1：问题设定的变化 —— 从 bandit 回到真 MDP

> **先读**：仓库《Agentic RL 入门1：基础、代码》——建立 agent RL 的基本语言与最小代码心智。

**要逐条掌握的知识点**：
- **视角切换**：前四周的 RLHF 是**序列级 bandit**（一整条回答=一个动作，末端打一个分）；Agentic RL 回到**多步 MDP**——一个 action 可能是「调一次工具 / 执行一段代码 / 发一次搜索 query / 点一次网页」，环境每步返回 observation。
  ```
  state_0 →（思考+动作 a_0）→ 环境返回 obs_0 → state_1 → a_1 → obs_1 → ... → 终态(成败)
  ```
- **奖励极度稀疏**：往往整条 trajectory 只有末端一个 0-1 信号——这正是 **RLVR 天然适配 agent** 的原因（答案对不对 / 单测过没过 / 任务完没完成）。稀疏奖励 + 长程，直接引出 Day 2 的信用分配难题。
- **trajectory 的基本单元是 step 而非 token**：agent 轨迹通常表示为一串结构化的 step-level trace（每次 agent-环境交互算一步），这与你之前「token 级序列」的心智不同，是读框架源码时的第一个认知门槛。

### Day 2：长程信用分配（credit assignment）—— 最核心的新问题

> **先读**：仓库《Agentic RL 入门2：信用分配》+《入门4：Credit 错分与算法接口》——这两篇是整个仓库的核心，前者讲怎么分、后者讲分错了会怎样以及各算法在信用分配上的「接口」差异。读完用下面的「粒度轴」框架归位。

一条 agent trajectory 可能几十步，只有末端一个奖励，如何把功劳/责任分到中间步骤？**要逐条掌握的三条路线**：
- **outcome-only + GRPO 组内基线**（最省事）：把最终奖励广播给整条轨迹所有 token，靠组内多条 rollout 的相对比较**隐式**分配信用——DeepSeek-R1 式做法向 agent 的直接延伸。优点是无需额外模型，缺点是长程下方差大。
- **过程奖励 / step-level reward**：给中间步骤显式打分（复用 `10_process_reward_model.md`），但 agent 场景 PRM 更难训、更易被 hack。
- **turn-level advantage**：把优势估计粒度从 token 抬到「轮/步」级——这与你在 GSPO 学的「序列级 ratio」是同一思路的延伸，是理解 agent RL 信用分配的关键接口。
- **归位框架**：信用分配可按**分配粒度（token / segment / step / turn / multi-agent）× 方法论（MC / TD / 模型 / 博弈 / 信息论）**做二维分类。面试讲 agent RL 时用这个「粒度轴」即可把任何新方法归位（延续 DAPO/GSPO 的 token 级 vs 序列级之争）。

### Day 3：Tool-Integrated Reasoning（TIR）与 token mask —— 工程正确性关键

> **先读**：仓库《Agentic RL 入门6：多轮工具调用》——多轮 rollout 循环与工具结果拼接的具体形态，正好对应本节的 TIR + loss mask。

**要逐条掌握的知识点**：
- **TIR 是什么**：agent 把**工具/环境返回结果拼回 context** 再继续生成（搜索结果、代码执行输出、网页内容）。这是「多轮」在实现上的具体形态。
- **loss mask（面试高频坑）**：工具/环境返回的 token **不是模型生成的**，计算 loss 时必须 **mask 掉**——否则等于让模型去「学习模仿环境输出」，破坏训练-推理一致性。这一点直连贯穿全程的**训练-推理一致性**主线，也直连 `13_unbiased_kl_estimate.md`。
- **代表工作**：Search-R1（多轮检索）、ReTool / ToRL（代码解释器 / 策略性工具调用）。读它们主要看两处——rollout loop 怎么循环、loss mask 怎么构造。

### Day 4：多轮 rollout 的采样与吞吐 + agentic RLVR

> **先读**：仓库《Agentic RL 入门3：transformer 架构》（长上下文/长轨迹为什么吃架构，KV cache 与吞吐）+《入门5：Skill-based Agentic RL》（技能/分层视角看长程任务分解）。这两篇支撑本节的「长轨迹吞吐」与「任务结构」认知。

**要逐条掌握的知识点**：
- **长度方差巨大**：有的任务 2 步结束、有的 50 步，batch 内 rollout 时间严重不均 → **异步 rollout / partial rollout**。verl 用 asyncio 协程异步执行每个 rollout 请求，避免等工具调用时 GPU 空转。
- **更 off-policy**：长 trajectory 让采样与更新之间延迟更大 → 需要离策略修正、重要性采样（直连 `13_unbiased_kl_estimate.md` 的 V3.2 离策略配方）。
- **吞吐瓶颈转移**：从 GPU 前向转移到**环境交互**（真实调 API、跑代码沙箱、检索），这是 agent RL 系统设计的新约束。
- **agentic RLVR**：RLVR 从「答案校验」扩展到「环境状态校验」——网页任务到达目标页、SWE 任务测试通过、任务完成度。
- **reward hacking 的新形态**：agent 会「钻环境空子」——改测试而非改代码、走捷径绕过验证、答案对但过程无效，比单轮更隐蔽。

### Day 5（可选代码）：最小 rollout 骨架 + 典型任务域 + 代表工作深读

> **先读（代表工作，三维度在真实系统的落地，任选感兴趣的）**：
> - 仓库《如何在 5 万张国产芯片训练出 1.6T 万亿参数模型？》（LongCat 2.0）——大规模 agent 后训练的系统视角。
> - 仓库《GLM-5.2 长程任务的 RL 怎么做？》——**长程任务 RL 的实战配方**，与本周「长程信用分配 + off-policy」主线最贴。
> - 仓库《Kimi-K3 为什么这么强？》+《Kimi K3 百万 token 的 agentic RL 怎么做？》——**百万 token 级长轨迹 agentic RL**，off-policy/吞吐维度的极致案例。
> 读法：每篇只需提取「它在①信用分配/②token mask/③off-policy 吞吐 上做了什么工程选择」，填进本周的三维度框架。

**典型任务域**（面试会问「你怎么训一个 X agent」，各记一句）：
- **Search / Deep Research agent**：多轮检索+推理（Search-R1）
- **Code / SWE agent**：改真实仓库、跑测试（SWE-bench 类，ReTool）
- **Computer / Browser use**：GUI 操作
- **Math with tools（TIR）**：调代码解释器算数值

**产出**：`common_knowledge/{N}_agentic_rl.md` —— 按「三增量维度」组织：① 多步 MDP 与稀疏奖励、② 长程信用分配（粒度轴 + 三路线）、③ TIR 与 loss mask（一致性）、④ 异步 rollout 与 off-policy、⑤ agentic RLVR 与 reward hacking 新形态。交叉引用 [[9_grpo]]、[[13_unbiased_kl_estimate]]、[[10_process_reward_model]]。**代码可选**：跑仓库自带的 `agentic-tau-rl代码实战`（可运行可单测，覆盖多轮 rollout/信用分配/策略优化/行为塑形，附离线→真机迁移指南），或读 Search-R1 的 rollout + mask 实现即可，不必自跑（无卡）。

**推荐材料（按优先级，本周以只读为主）**：

*第一层 — 本周主教材（跟读主线）：*
- **Agentic-RL-Most-Detailed-Intro**（小red，美团 M17 基座 agent 后训练；中文、体系化、贴工业实践，本周骨架）：https://github.com/XiaoRed5/Agentic-RL-Most-Detailed-Intro ｜ 在线阅读：https://xiaored5.github.io/Agentic-RL-Most-Detailed-Intro/
  - 入门 1-6（基础/信用分配/transformer 架构/Credit 错分与算法接口/Skill-based/多轮工具调用）→ 按上面「篇目→天数映射」逐篇跟读。
  - 代表工作（LongCat 2.0 / GLM-5.2 长程 RL / Kimi-K3 双篇）→ Day 5 深读。
  - agentic-tau-rl 代码实战 → Day 5 可选跑。

*第二层 — 建地图（配合主教材，补全学术 taxonomy）：*
- *The Landscape of Agentic Reinforcement Learning for LLMs*（2025 最系统综述，当字典/地图用，看 taxonomy 归位子问题）：https://arxiv.org/abs/2509.02547
- *Credit Assignment in RL for LLMs*（信用分配专项综述，粒度×方法论二维分类，直接可用作面试框架）：https://arxiv.org/html/2604.09459v1
- （可选）Cameron Wolfe, *Agentic RL: Frameworks and Best Practices*（工程视角，把系统拆成工具执行/轨迹存储/RL 更新三块，提出 step 而非 token 作为轨迹单元）：https://substack.com/@cwolferesearch/posts

*第三层 — 代表工作源码（读 README + 论文，不跑）：*
- Search-R1（多轮检索 agent，基于 verl，看 rollout + mask 最干净）：https://github.com/PeterGriffinJin/Search-R1 ｜ 论文 https://arxiv.org/abs/2503.09516
- awesome-RLVR（含 agentic RLVR 分节，找齐代表工作的总入口）：https://github.com/opendilab/awesome-RLVR
- Agentic-RL-Training-Recipes（训练配方 survey repo，按 GRPO/信用分配/search 组织）：https://github.com/blacksnail789521/Agentic-RL-Training-Recipes

*第四层 — verl 的 agent 抽象层（只读这三页，跳过 Ray/Megatron 分布式）：*
- Agentic RL Training 总览：https://verl.readthedocs.io/en/latest/start/agentic_rl.html
- Agent Loop（多轮 rollout 循环核心抽象）：https://verl.readthedocs.io/en/latest/advance/agent_loop.html
- Multi-turn Rollout Support：https://verl.readthedocs.io/en/v0.4.0/sglang_multiturn/multiturn.html
- 读这三页只盯三件事：① 多轮循环怎么写 ② 工具返回 token 怎么 mask ③ 为什么用 asyncio 异步 rollout（避免等工具时 GPU 空转）。

### Week 5 自检
- 能说清 Agentic RL 相对单轮 RLHF 多了哪三个新维度？为什么它复用 GRPO/RLVR 内核？
- 为什么工具/环境返回的 token 必须 mask 掉？不 mask 会破坏什么？
- 长程信用分配有哪几条路线？「粒度轴」如何把 GSPO/turn-level advantage 归位？
- 为什么 agent RL 更 off-policy、更需要异步 rollout？吞吐瓶颈从哪转到哪？

---

## 缓冲周 — 串联与面试

> 前五周是「点」，这周把它们连成「线」，形成可复述的叙事。

### 1. 写一篇串联综述
在 `post_training/` 下新建 `rlhf_overview.md`，用一条主线串起全部算法：

```
策略梯度（祖先）
   ├─ + baseline 降方差 ─→ actor-critic ─→ PPO（clip + GAE + Critic）
   │                                          │
   │                            砍 Critic，组内均值当 baseline
   │                                          ▼
   │                                        GRPO ──+ 可验证奖励(RLVR)──→ R1 reasoning
   │                                          │        └─ 变体：DAPO/GSPO/Dr.GRPO
   │                                          │        └─ + 多轮/工具/环境 ──→ Agentic RL(Search-R1/ReTool)
   │                                          │
   └─ 换个思路：偏好的闭式最优解 ─→ DPO（离线，无 RM 无采样）
                                        └─ 变体：IPO/KTO/ORPO/SimPO
                                        
   能力融合：分域(SFT+GRPO) ─→ OPD on-policy 蒸馏统一（V4）
```

四条贯穿线索，每个算法都放到这四个坐标上定位：
1. **优势估计**：Critic / 组内均值 / 隐式（DPO 无显式优势）/ 长程信用分配（agent：token→turn 粒度）
2. **KL 约束**：位置（reward/loss/隐式）+ 估计（k1/k2/k3）
3. **on/off-policy**：在线采样 vs 离线数据，训练-推理一致性（agent：工具 token mask + 异步 rollout 的离策略修正）
4. **奖励来源**：RM / 规则(RLVR) / 偏好对 / 教师模型(OPD) / 环境状态(agentic RLVR)

### 2. 高频面试题自测（选摘，可扩展到 QA 库）
- PPO 的 clip 在 A>0/A<0 时各防什么？为什么用重要性采样？
- GRPO 为什么能去掉 Critic？组内 std 归一化有什么副作用（DAPO 视角）？
- 为什么 RL 提升 Maj@K 却不提升 Pass@K？这对「RL 能否注入新能力」意味着什么？
- DPO 损失怎么推出来的？它和 PPO 的根本区别（on/off-policy）？
- RLVR 相比 RM 的优劣与适用边界？reward hacking 在两种设定下如何表现？
- OPD 为什么比离线蒸馏好？训练-推理一致性为什么对 on-policy RL 正确性是前提？
- KL 的 k1/k2/k3 估计器区别？为什么 GRPO/PPO 默认 k3？
- Agentic RL 相比单轮 RLHF 多了哪三个新维度？为什么工具/环境返回的 token 必须 mask？长程稀疏奖励怎么做信用分配？

---

## 产出清单汇总（便于跟踪）

**知识点（`common_knowledge/`，编号接续现有最大值）**：
- [ ] 策略梯度 policy_gradient
- [ ] 奖励模型 reward_model
- [ ] PPO ppo
- [ ] RLVR 可验证奖励 rlvr
- [ ] GRPO 变体 grpo_variants（或并入 9_grpo.md）
- [ ] DPO dpo
- [ ] DPO 变体 dpo_variants（或并入 dpo.md）
- [ ] On-Policy Distillation on_policy_distillation
- [ ] Agentic RL agentic_rl（三增量维度：长程信用分配 / 工具 token mask / 异步 off-policy rollout）
- （已有，查漏复用）9_grpo、10_process_reward_model、13_unbiased_kl_estimate

**代码（`code/`）**：
- [ ] reward_model_bt.ipynb（BT-loss RM）
- [ ] ppo_minimal.ipynb（clip + GAE + Critic）
- [ ] grpo_minimal.ipynb（组内基线，无 Critic）
- [ ] dpo_minimal.ipynb（离线偏好损失）

**综述**：
- [ ] post_training/rlhf_overview.md（四线索串联全谱系）

> 编号原则遵循 CLAUDE.md：新建知识点文件时查 `common_knowledge/` 当前最大数字前缀 N，依次 N+1。公式在 `.md` 里用 LaTeX，终端交互回答用纯文本。

---

## 附录：核心论文与资源总表（按主题）

### 综述 / 教材
| 资源 | 链接 |
|------|------|
| RLHF Book（Nathan Lambert，系统教材） | https://rlhfbook.com/ |
| HuggingFace, Illustrating RLHF | https://huggingface.co/blog/rlhf |
| Lilian Weng, Policy Gradient Algorithms | https://lilianweng.github.io/posts/2018-04-08-policy-gradient/ |
| Lilian Weng, Reward Hacking in RL | https://lilianweng.github.io/posts/2024-11-28-reward-hacking/ |
| OpenAI Spinning Up | https://spinningup.openai.com/ |

### RL 基础 / PPO 线
| 论文 | 链接 |
|------|------|
| TRPO (Schulman 2015) | https://arxiv.org/abs/1502.05477 |
| GAE (Schulman 2015) | https://arxiv.org/abs/1506.02438 |
| PPO (Schulman 2017) | https://arxiv.org/abs/1707.06347 |
| InstructGPT (Ouyang 2022) | https://arxiv.org/abs/2203.02155 |
| RM Overoptimization (Gao 2022) | https://arxiv.org/abs/2210.10760 |
| Constitutional AI / RLAIF (Bai 2022) | https://arxiv.org/abs/2212.08073 |
| Secrets of RLHF Part I (Zheng 2023) | https://arxiv.org/abs/2307.04964 |
| 37 Implementation Details of PPO | https://iclr-blog-track.github.io/2022/03/25/ppo-implementation-details/ |

### GRPO / RLVR / Reasoning 线
| 论文 | 链接 |
|------|------|
| DeepSeekMath (GRPO 起源, 2024) | https://arxiv.org/abs/2402.03300 |
| DeepSeek-R1 (2025) | https://arxiv.org/abs/2501.12948 |
| DeepSeek-V3.2 (可扩展 RL, 2025) | https://arxiv.org/abs/2512.02556 |
| Tülu 3 (RLVR 系统化, 2024) | https://arxiv.org/abs/2411.15124 |
| DAPO (字节, 2025) | https://arxiv.org/abs/2503.14476 |
| Dr. GRPO / Understanding R1-Zero (Sea AI Lab, 2025) | https://arxiv.org/abs/2503.20783 |
| GSPO (Qwen, 2025) | https://arxiv.org/abs/2507.18071 ｜ 博客 https://qwenlm.github.io/blog/gspo/ |

### DPO / 离线对齐线
| 论文 | 链接 |
|------|------|
| DPO (Rafailov 2023) | https://arxiv.org/abs/2305.18290 |
| IPO (Azar 2023) | https://arxiv.org/abs/2310.12036 |
| KTO (Ethayarajh 2024) | https://arxiv.org/abs/2402.01306 |
| ORPO (Hong 2024) | https://arxiv.org/abs/2403.07691 |
| SimPO (Meng 2024) | https://arxiv.org/abs/2405.14734 |

### OPD / 蒸馏融合线
| 资源 | 链接 |
|------|------|
| On-Policy Distillation (Thinking Machines, 2025) | https://thinkingmachines.ai/blog/on-policy-distillation/ |
| GKD (Agarwal, ICLR 2024) | https://arxiv.org/abs/2306.13649 |
| MiniLLM (Gu 2023) | https://arxiv.org/abs/2306.08543 |
| DeepSeek-V4 (2026) | https://arxiv.org/abs/2606.19348 |
| awesome-on-policy-distillation | https://github.com/chrisliu298/awesome-on-policy-distillation |

### 工程框架（读源码 / 跑实验）
| 框架 | 链接 |
|------|------|
| HuggingFace TRL（PPO/GRPO/DPO Trainer） | https://github.com/huggingface/trl |
| veRL（火山引擎，工业级 RL） | https://github.com/volcengine/verl |
| OpenRLHF | https://github.com/OpenRLHF/OpenRLHF |

### Agentic RL 线（Week 5 主教材 + 代表工作）
| 资源 | 链接 |
|------|------|
| Agentic-RL-Most-Detailed-Intro（小red，中文体系化教材，Week 5 主线） | https://github.com/XiaoRed5/Agentic-RL-Most-Detailed-Intro ｜ 在线 https://xiaored5.github.io/Agentic-RL-Most-Detailed-Intro/ |
| The Landscape of Agentic RL for LLMs（综述） | https://arxiv.org/abs/2509.02547 |
| Credit Assignment in RL for LLMs（信用分配综述） | https://arxiv.org/html/2604.09459v1 |
| Search-R1（多轮检索 agent） | https://github.com/PeterGriffinJin/Search-R1 ｜ 论文 https://arxiv.org/abs/2503.09516 |
| verl Agentic RL 文档 | https://verl.readthedocs.io/en/latest/start/agentic_rl.html |


