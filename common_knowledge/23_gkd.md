# GKD（Generalized Knowledge Distillation，广义知识蒸馏）

## 概述

**GKD（Generalized Knowledge Distillation）** 是 Google DeepMind 在论文《On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes》(ICLR 2024, Agarwal et al.) 中提出的一个**统一自回归语言模型蒸馏的框架**。它把"在哪些序列上训练"（数据分布）和"用什么损失训练"（散度）这两个设计维度**解耦**成两个可调超参数，从而把此前一系列蒸馏方法（监督 KD、SeqKD、on-policy KD、ImitKD、f-distill）统一为特例，并实例化出性能显著更优的 **on-policy 变体**。

一句话核心：**GKD = 让学生自己 on-policy 采样序列（消除训练/推理分布不匹配）+ 在这些序列上用可选散度对齐教师的 token 级分布 + 不对采样过程反向传播（因而比策略梯度式蒸馏更简单稳定）。**

> 注：GKD 是 [[21_on_policy_distillation]] 这一路线的**奠基论文之一**。21 号笔记从 Thinking Machines(2025) 的概念视角讲 OPD 的动机与直觉，本篇聚焦 GKD 论文本身的**统一框架、算法、散度选择与 RL 结合**的技术细节。

## 要解决的核心问题：训练-推理分布不匹配

自回归模型有一个经典缺陷——**exposure bias（暴露偏差）**：

- 传统蒸馏（监督 KD / SeqKD）用一批**固定序列**（ground-truth 或教师生成）训练学生。
- 训练时学生看到的是"正确前缀"，推理时却要基于**自己生成的、可能已跑偏的前缀**继续预测。
- 由于自回归每步依赖前面的步，早期一个小错会产生**级联效应（cascading error）**，最终生成质量崩坏。

GKD 的洞察是：**自回归蒸馏本质是一个带"交互式专家"的模仿学习问题**（对应 DAgger, Ross et al. 2011）。解法就是让学生在**自己生成的 on-policy 序列**上训练，由教师在这些序列的每个 token 上给出"正确分布"作为专家标签。

## 统一目标函数

GKD 最小化如下目标：

$$
\mathcal{L}_{GKD}(\theta) = (1-\lambda)\,\mathbb{E}_{(x,y)\sim(X,Y)}\big[\mathcal{D}(p_T\|p_S^\theta)(y|x)\big] + \lambda\,\mathbb{E}_{x\sim X}\,\mathbb{E}_{y\sim p_S(\cdot|x)}\big[\mathcal{D}(p_T\|p_S^\theta)(y|x)\big]
$$

其中 token 级散度定义为在序列所有位置上取平均：

$$
\mathcal{D}(p_T\|p_S^\theta)(y|x) := \frac{1}{L_y}\sum_{n=1}^{L_y} \mathcal{D}\big(p_T(\cdot|y_{<n},x)\,\|\,p_S^\theta(\cdot|y_{<n},x)\big)
$$

两个关键超参数：

- **$\lambda$（student data fraction，学生数据占比）** $\in[0,1]$：控制 on-policy 学生自生成序列所占比例。$\lambda=1$ 为纯 on-policy，$\lambda=0$ 为纯固定数据集，$\lambda=0.5$ 为混合。
- **$\mathcal{D}$（散度）**：可选前向 KL、反向 KL、广义 JSD 等。

**关键实现细节：不对学生的采样过程 $p_S(\cdot|x)$ 反向传播。** 生成阶段（自回归解码，顺序但 no_grad）与训练阶段（teacher-forcing，整条序列一次并行 forward+backward）分离，因此训练稳定、计算高效，且不会退化成 RNN 式的逐 token 反传。

## 算法流程（Algorithm 1）

```
给定：教师 p_T，学生 p_S^θ，数据集 (X,Y)
超参：学生数据占比 λ，散度 D，学习率 η
for k = 1..K:
    采样 u ~ Uniform(0,1)
    if u ≤ λ:   # on-policy 分支
        从 X 采 x，用学生生成 y ~ p_S^θ(·|x)，得到 batch B
    else:       # 固定数据集分支
        从 (X,Y) 采一个 batch B
    更新 θ 最小化 L_GKD：θ ← θ − η·(1/B)·Σ ∇_θ D(p_T‖p_S^θ)(y|x)
```

**备注**：GKD 假设学生已能生成足够质量的序列（论文从**已做过 SFT 的学生**开始），类似两阶段 RLHF（先 SFT 再 RL）。

## 散度选择：mode-seeking vs mean-seeking

散度的选择决定了"质量 vs 多样性"的权衡，且**最优散度是任务相关的**（也与采样温度相关）。

| 散度 | 行为 | 特点 |
|------|------|------|
| **前向 KL** $D_{KL}(p_T\|p_S)$ | mean-seeking（覆盖式） | 要求学生覆盖教师分布的整个支撑集；学生容量不足时可能把概率分给教师认为低概率的 token → **幻觉/低质量生成**（尤其温度采样下） |
| **反向 KL** $D_{KL}(p_S\|p_T)$ | mode-seeking（寻峰） | 聚焦教师高概率的 token，避免低质量生成，但**多样性下降** |
| **广义 JSD($\beta$)** | 在两者间插值 | 有界（KL 可能无界）；$\beta\to0$ 近似前向 KL，$\beta\to1$ 近似反向 KL；实验中常是折中最优 |

广义 JSD 定义（$0<\beta<1$）：

$$
\mathcal{D}_{JSD(\beta)}(P\|Q) = \beta D_{KL}\big(P\,\|\,\beta P+(1-\beta)Q\big) + (1-\beta)D_{KL}\big(Q\,\|\,\beta P+(1-\beta)Q\big)
$$

**经验规律**：
- **指令微调**：反向 KL 明显最好——mode-seeking 让模型聚焦指令的主要意图，忽略次要细节。
- **摘要/翻译（贪心采样）**：前向 KL 也不错；温度采样下 mode-seeking 更优。
- **学生越大**，不同散度间的差距越小。

## GKD + RL 微调

GKD 可与 RLHF/RLAIF **无缝结合**（因为都只需要学生的输出样本），得到带正则的 RL 目标：

$$
\mathbb{E}_{x\sim X}\Big[(1-\alpha)\underbrace{\mathbb{E}_{y\sim p_S^\theta}[r(y)]}_{\text{RL 目标}} - \alpha\underbrace{\mathbb{E}_{y\sim p_S}[\mathcal{D}(p_T\|p_S^\theta)(y|x)]}_{\text{广义 on-policy 蒸馏}}\Big]
$$

- **创新点**：传统 RLHF 把策略正则化到"初始 SFT 模型"，GKD 把正则方向改为"贴近**教师**策略"——这是首个同时做蒸馏 + RL 微调的工作。
- **作用**：既最大化 reward，又靠蒸馏保住通用能力，**减小对齐税（alignment tax）**。
- 论文用 RLAIF + on-policy GKD 缓解摘要幻觉（reward = 文本蕴含分数 RLEF），同时提升摘要质量。
- **建议**：与 RL 结合时用反向 KL 或 JSD(0.9)。

## 与相关方法的关系（都是 GKD 的特例）

| 方法 | 对应 GKD 配置 |
|------|--------------|
| **监督 KD** (Hinton/Sanh) | 前向 KL + $\lambda=0$ |
| **on-policy KD** | 前向 KL + $\lambda=1$ |
| **ImitKD** (Lin 2020) | 前向 KL + $\lambda$ 非递增调度（如 0.5） |
| **f-distill** (Wen 2023) | 全变差距离 + $\lambda=0.5$ |
| **SeqKD** (Kim&Rush) | 在教师生成序列上做 SFT |

- **对比 MiniLLM**（Gu et al. 2023，同期）：MiniLLM 在序列级用**策略梯度**优化反向 KL，需要多种稳定化技巧（应对高方差、reward hacking、长度偏差）；GKD **不对采样反传**，更接近监督训练、更简单稳定，且散度可选（有时前向 KL / JSD 比反向 KL 更好）。

## 关键实验结论

1. **on-policy（$\lambda=1$）几乎总是最优**：三个任务（摘要 XSum / 翻译 WMT / 推理 GSM8K）一致证明学生自生成序列优于固定数据集；只要 ≥25% 数据是 on-policy，性能随比例持续提升。
2. **数据效率极高**：5% 子采样数据 + **无 ground-truth** 的 on-policy GKD，超过用全量数据 + ground-truth 的监督 KD 和 ImitKD。
3. **可扩展性**：用小 7000 倍的 T5 模型超过 PaLM(540B) 的少样本性能；处理的学生规模是 ImitKD 的约 26 倍。
4. **任务无关蒸馏**：FLAN T5-XL→Base，on-policy GKD + 反向 KL 在留出的 MMLU/BBH 上大幅领先。

## 与后训练的关联

GKD 处在 SFT 与 RL 之间的谱系上，是理解 [[21_on_policy_distillation]] 的技术基础：它用教师分布替代 [[16_reward_model]] 的稀疏奖励，用 on-policy 采样保证 [[15_policy_gradient]] 式的分布正确性，比 [[9_grpo]] 在有强教师时更样本高效。其"正则方向从初始策略改为教师策略"的思路，与 [[22_dpo]]、RLHF 的 KL 正则一脉相承。KL 方向与估计方式可参考 [[13_unbiased_kl_estimate]]。

## 参考文献

- Agarwal et al., "On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes" (GKD), ICLR 2024.
- Gu et al., "Knowledge Distillation of Large Language Models" (MiniLLM), 2023.
- Lin et al., "Autoregressive Knowledge Distillation through Imitation Learning" (ImitKD), 2020.
- Ross et al., "A Reduction of Imitation Learning..." (DAgger), 2011.
- Huszár, "How (not) to train your generative model" (JSD 梯度分析), 2015.
