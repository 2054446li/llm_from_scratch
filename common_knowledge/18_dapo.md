# DAPO：解耦裁剪与动态采样策略优化（Decoupled Clip and Dynamic sAmpling Policy Optimization）

> 字节 Seed + 清华 AIR，2025（arXiv:2503.14476）。**首个完整开源**（算法+代码+数据）的大规模 LLM RL 系统，在 Qwen2.5-32B 基座上于 AIME 2024 取得 **50 分**，只用 DeepSeek-R1-Zero-Qwen-32B（47 分）**一半的训练步数**。
> 一句话定位：**DAPO = 在朴素 GRPO 上打的四个补丁 + 删掉 KL + 数据整数化**。是理解 2025 后 reasoning RL 工程配方的核心论文。
> 前置：[[9_grpo]]（GRPO 本体）、[[14_ppo]]（clip 机制）、[[16_reward_model]]（reward hacking / RLVR）、[[17_test_time_scaling]]（长 CoT 目标能力）、[[13_unbiased_kl_estimate]]（KL 位置）。

## 概述

DAPO 要解决的问题：**朴素 GRPO 在 Qwen2.5-32B 基座上只能到 30 分**，远低于 DeepSeek 的 47 分。深入分析发现朴素 GRPO 有三大病：**熵坍缩、奖励噪声、训练不稳定**。而 o1 / R1 的技术报告都**隐藏了关键训练细节**，社区无法复现。DAPO 把这些细节全部公开，并用四项技术把 30 分推到 50 分。

**目标函数**（对每个问题 $q$ 采一组 $G$ 个输出 $\{o_i\}$）：

$$
\mathcal{J}_{\text{DAPO}}(\theta) = \mathbb{E}_{(q,a)\sim\mathcal{D},\ \{o_i\}\sim\pi_{\theta_{\text{old}}}}\Bigg[ \frac{1}{\sum_{i=1}^{G}|o_i|} \sum_{i=1}^{G}\sum_{t=1}^{|o_i|} \min\Big( r_{i,t}\hat A_{i,t},\ \mathrm{clip}(r_{i,t},\ 1-\varepsilon_{\text{low}},\ 1+\varepsilon_{\text{high}})\,\hat A_{i,t}\Big)\Bigg]
$$

$$
\text{s.t.}\quad 0 < \big|\{o_i \mid \texttt{is\_equivalent}(a, o_i)\}\big| < G
$$

其中 $r_{i,t}(\theta) = \dfrac{\pi_\theta(o_{i,t}\mid q, o_{i,<t})}{\pi_{\theta_{\text{old}}}(o_{i,t}\mid q, o_{i,<t})}$，$\hat A_{i,t} = \dfrac{R_i - \mathrm{mean}(\{R_i\})}{\mathrm{std}(\{R_i\})}$。

**对照 GRPO（[[9_grpo]] 式 5）看 DAPO 改了什么——四处一目了然：**

| 改动 | GRPO | DAPO | 对应技术 |
|---|---|---|---|
| 裁剪阈值 | 对称 $\varepsilon$ | 解耦 $\varepsilon_{\text{low}}, \varepsilon_{\text{high}}$ | Clip-Higher（§一） |
| 归一化分母 | $\frac{1}{G}\sum\frac{1}{|o_i|}$（样本级） | $\frac{1}{\sum|o_i|}$（token 级） | Token-Level Loss（§三） |
| 组约束 | 无 | $0<$ 正确数 $<G$ | Dynamic Sampling（§二） |
| KL 项 | $-\beta D_{\text{KL}}(\pi_\theta\|\pi_{\text{ref}})$ | **删除** | Removing KL（§五） |

## 一、Clip-Higher（抬高天花板 → 防熵坍缩）

**病**：朴素 PPO/GRPO 训练中熵迅速坍缩，同一组采样出的回答几乎雷同 → 探索不足、策略过早确定性化。

**根因**：对称裁剪的**上界**对低概率"探索型"token 太苛刻。设 $\varepsilon=0.2$、$\hat A>0$，两个 token 旧概率 $0.9$ 与 $0.01$：上界 $\pi_{\text{old}}(1+\varepsilon)$ 分别是 $1.08$ 与 $0.012$。高概率 token 几乎不受限就能涨到 0.999，低概率 token 最多只能到 0.012 —— **上界系统性压制了探索**。经验上被上界裁剪的 token 平均概率 $<0.2$。

**药**：把裁剪范围解耦成 $\varepsilon_{\text{low}}, \varepsilon_{\text{high}}$，**调高 $\varepsilon_{\text{high}}$**（实验用 0.28）给低概率 token 留增长空间。$\varepsilon_{\text{low}}$ 保持 0.2 不动——调高它会把 token 概率压到 0、导致采样空间坍缩。

> 联系 [[14_ppo]] §二"clip 是单向 cap"：DAPO 发现上界这一侧对 $\hat A>0$ 的低概率 token 过严，单独放宽。**属"裁剪策略"轴的改造。**

## 二、Dynamic Sampling（动态采样 → 消除零梯度）

**病**：当某 prompt 的所有输出全对（准确率=1）时，组内奖励相同 → 优势 $\hat A = (r-\mathrm{mean})/\mathrm{std} = 0$ → **零策略梯度**。随训练推进，全对样本越来越多 → 每个 batch 有效 prompt 数递减、梯度方差变大。

**药**：**过采样 + 过滤掉准确率为 1 或 0 的 prompt**（约束 $0<$ 正确数 $<G$，即一组内**必须有对有错**才有非零组内优势），训练前持续采样直到 batch 填满"有对有错"的样本。

**代价可控**：RL 同步执行时生成��间被长尾样本主导，过滤不显著增加总时间；反因所需训练步数更少，**收敛甚至更快**（图 6）。

> 直接回应 [[9_grpo]] 的"全对/全错 → 组内优势为 0"痛点。DAPO 不改优势公式，而是**在数据侧过滤零梯度组**——纯工程但增益最大（+8 分）。**属"采样策略"轴。**

## 三、Token-Level Policy Gradient Loss（token 级损失 → 长 CoT 再平衡）

**病**：原始 GRPO 用**样本级损失**（先序列内平均、再跨样本平均），每个样本等权 → **长回答里的 token 被稀释**，两个恶果：① 高质量长样本的推理模式学不进去；② 低质量长样本（胡言乱语、重复）无法被有效惩罚 → 熵与长度不健康增长。

**药**：归一化分母从"样本数"改成"总 token 数"（$\frac{1}{\sum|o_i|}$），使**长序列对梯度影响更大**。单 token 视角：无论所在回答多长，某生成模式只要影响奖励，就被等量激励/抑制。

**注意**：性能增益小（+1），但**主要贡献是训练稳定性 + 让长度健康增长**。

> 这正是 [[9_grpo]] 变体对比里"损失聚合粒度轴"的核心案例；也是 GSPO 序列级 ratio 的对照物。

## 四、Overlong Reward Shaping（超长奖励塑形 → 去噪）

**病**：生成设最大长度（20480 token），超长样本被截断。默认给截断样本 **−1 惩罚**会引入**奖励噪声**——一个推理**过程正确**、只是太长没写完的样本被判负，等于告诉模型"你推理错了"，让模型困惑、回避正确的长推理。

**两个方案（递进替代 / 可配合）：**

1. **Overlong Filtering（超长过滤）**：**屏蔽截断样本的损失**（loss mask=0，完全不计入梯度）。简单粗暴，去噪，+6 分。缺点：把"该简洁"的信号也一并扔了。
2. **Soft Overlong Punishment（软超长惩罚，式 13）**：长度感知的**渐进软惩罚**，把硬 −1 断崖磨成平滑斜坡：

$$
R_{\text{length}}(y) = \begin{cases} 0, & |y| \le L_{\max} - L_{\text{cache}} \\ \dfrac{(L_{\max} - L_{\text{cache}}) - |y|}{L_{\text{cache}}}, & L_{\max} - L_{\text{cache}} < |y| \le L_{\max} \\ -1, & L_{\max} < |y| \end{cases}
$$

配置 $L_{\max}=20480,\ L_{\text{cache}}=4096$：$\le 16384$ 不罚；缓冲区内惩罚从 0 线性降到 −1；超 20480 固定 −1。**关键**：在样本被截断**之前**、于缓冲区内**提前渐进**发出"该收尾"信号，无断崖 → 无噪声，又保住长度约束。

> 联系 [[16_reward_model]] §六 reward hacking 的镜像：那边是"错误的高奖励"诱导钻空子，这边是"错误的低奖励（把长当错）"污染训练。**核心都是：奖励信号必须干净，噪声比缺失更有害。**

## 五、Removing KL Divergence（删除 KL 惩罚）

DAPO **直接删掉了 KL 项**。理由：KL 用来约束在线策略不过度偏离参考策略，这在 RLHF（对齐）里必要；但**训练长 CoT 推理模型时，模型分布本就应大幅偏离初始模型**，KL 约束没有必要。

> **贯穿主线——"KL 放哪"的三种态度：**
> - **PPO**：KL 放 **reward**（有 GAE 逐 token 摊开，[[14_ppo]]）
> - **GRPO**：KL 放 **loss**（砍了 Critic，进 reward 会污染组内归一化，[[9_grpo]]、[[13_unbiased_kl_estimate]]）
> - **DAPO**：**直接删除**（RLVR 有可验证奖励兜底、鼓励探索，不怕跑偏）
> 这是理解 RLVR 与 RLHF 差异的关键：RLHF 怕跑偏（对齐），RLVR 不怕跑偏。

## 六、规则奖励与数据（RLVR）

- **Rule-based Reward**：不用 RM（怕 reward hacking），直接用可验证任务的最终正确性：$R=+1$ 若答案等价、否则 $-1$。这就是 **RLVR**，正面回应 [[16_reward_model]] §八"RM 是瓶颈"——用规则/验证器不留 RM 空子。
- **Dataset Transformation**：把数学答案统一**变换成整数**（易解析、减少 formula parser 错误）。例如答案 $\frac{a+\sqrt b}{c}$ → 改写题目使期望答案变成 $a+b+c$。得 **DAPO-Math-17K**（17K prompt，每个配整数答案）。

## 七、实验结果

**逐项消融（表 1，面试必背）**——朴素 GRPO 30 → DAPO 50，超过 R1-Zero 的 47：

| 模型 | AIME24 (avg@32) | 增益 |
|---|---|---|
| DeepSeek-R1-Zero-Qwen-32B | 47 | — |
| Naive GRPO | 30 | 基线 |
| + Overlong Filtering | 36 | +6 |
| + Clip-Higher | 38 | +2 |
| + Soft Overlong Punishment | 41 | +3 |
| + Token-level Loss | 42 | +1 |
| + Dynamic Sampling（**DAPO**） | **50** | **+8** |

**关键训练配置**：verl 框架；AdamW，恒定 lr $1\times10^{-6}$，20 步 warmup；prompt batch 512，每 prompt 采 16 个（$G=16$）；$\varepsilon_{\text{low}}=0.2,\ \varepsilon_{\text{high}}=0.28$；生成上限 20480 token；评估 avg@32、temperature=1.0、top-p=0.7。

**训练动力学监控指标（§4.3，工程经验）**：
- **长度**：增长 = 探索空间变大，但不总是上升（会停滞/下降，R1 也如此），需配合验证准确率一起看。
- **奖励**：训练集奖励稳定增长，但**与验证准确率相关性低 → 警惕过拟合**。
- **熵**：需维持恰当区间——过低 = 熵坍缩失去探索；过高 = 过度探索（胡言乱语）。**熵缓慢上升有利于性能**（Clip-Higher 起效的证据）。

**涌现现象（§4.4 Case Study）**：训练早期模型几乎不检查/反思，随训练推进**涌现出反思（reflection）与回溯（backtracking）**——中途写出 "However, wait a moment, let's rethink..." 主动质疑自己的解法。纯 +1/−1 规则奖励下**自发涌现**，是 [[17_test_time_scaling]]"RL 激发 self-verification / iterative refinement"的直接实证。

## 八、三条贯穿主线（复习锚点）

1. **PPO → GRPO → DAPO 的"减法"演进**：clip 目标不变，逐步砍——GRPO 砍 Critic/GAE，DAPO 再砍 KL、改 token-level。
2. **KL 放哪的三种态度**：reward（PPO）/ loss（GRPO）/ 删除（DAPO）。
3. **RLVR + 涌现**：纯规则奖励（+1/−1）训出反思/回溯 → test-time scaling 目标能力被 RL 训出来的活样本。

## 一句话总结

DAPO = **在朴素 GRPO 上叠四个补丁（Clip-Higher 防熵坍缩 / Dynamic Sampling 消零梯度 / Token-Level Loss 再平衡长 CoT / Overlong Shaping 去截断噪声）+ 删 KL + 规则奖励 + 数据整数化**，把 Qwen2.5-32B 基座从 30 分推到 50 分（超 R1-Zero 47 分、省一半步数），并**完整开源算法/代码/数据**。四个补丁分别落在 reasoning RL 的四个改造轴（裁剪 / 采样 / 聚合粒度 / 奖励塑形）上，是理解 GRPO 变体版图的核心样本。

## 参考文献

- Yu et al., 2025. *DAPO: An Open-Source LLM Reinforcement Learning System at Scale.* arXiv:2503.14476.
- 项目页：https://dapo-sia.github.io/ ｜ 代码：https://github.com/volcengine/verl
- Shao et al., 2024. *DeepSeekMath (GRPO 起源).* arXiv:2402.03300.（[[9_grpo]]）
- DeepSeek-AI, 2025. *DeepSeek-R1.* arXiv:2501.12948.（对照基线、长度停滞现象）
