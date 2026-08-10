# Agentic RL 与 Harness（智能体强化学习与运行框架）

## 概述

- **Harness（运行框架/挽具）**：套在模型外面、驱动它"跑起来"的那层脚手架——不是模型本身，而是模型之外的**环境 + 控制器 + IO**。负责维护 agent 循环、执行工具调用、管理 trajectory 上下文、与外部环境交互收集 observation、在 RL 场景下收集轨迹并算 reward。
- **Agentic RL（智能体强化学习）**：在"多轮 agent 交互循环"上做 RL，而非单轮 prompt→response。policy 在一个环境里多步行动（思考→调工具→看 observation→再思考→…→终止），reward 通常来自环境/最终结果，信用分配在 trajectory 层面。

一句话核心：**harness 就是 agentic RL 的 environment；agentic RL = "在 harness 这个环境里、对一整条 agent trajectory 做 RL"。没有 harness 就没有 agentic RL，harness 的设计直接决定 agentic RL 能不能跑、跑得多快、对不对。**

> 注：本篇是"工程架构 + 算法"交叉概念。算法侧见 [[14_ppo]]、[[9_grpo]]、[[15_policy_gradient]]；rollout 吞吐侧见 [[4_flash_attention]]、[[12_deepseek_v2]]（MLA/KV 压缩）；on-policy 一致性侧见 [[21_on_policy_distillation]]。

## 什么是 Harness

"Harness"原意是马具/挽具——套在马身上、控制它干活的皮带架子。借用到软件工程里，指**把被测对象包起来、驱动它运行的那层框架**（如测试 harness、eval harness）。在 LLM/agent 工程里，harness 指**模型之外的那层脚手架**，典型职责：

1. **维护 agent 循环**：思考 → 行动 → 观察 → 再思考 → … → 终止，决定何时停止、如何拼接 prompt。
2. **执行工具调用**：跑 shell、调浏览器、搜索、执行代码、查数据库，并把执行结果转成 observation 文本喂回模型。
3. **管理 context / trajectory**：拼 prompt、长上下文截断/压缩、管理 KV cache（直接影响 rollout 吞吐，见 [[4_flash_attention]]）。
4. **与外部环境交互**：决定 state 怎么来、action 怎么落地、episode 怎么结束。
5. **收集轨迹并算 reward**：在 RL 场景下，把整条 trajectory 落盘，并调用 reward 函数（结果奖励 / 规则奖励 / RM 打分）。

典型例子：SWE-bench 的 harness（Docker 沙箱 + 跑测试 + 评估）、SWE-agent 的 agent loop、各种 "agent scaffold"（如 OpenManus、DeepResearcher 的环境层）。一句话：**harness = 模型之外的"环境 + 控制器"**。

## 什么是 Agentic RL

传统 RLHF / PPO（见 [[14_ppo]]、[[16_reward_model]]）是**单轮**的：给一个 prompt，模型生成一条 response，reward model 给这条 response 打一个分，再回传做策略更新。

Agentic RL 把这个闭环放到**多轮 agent 循环**上：

- policy 在一个环境里**多步行动**：思考 → 调工具 → 看 observation → 再思考 → … → 终止。
- reward 通常来自**环境反馈 / 最终结果**（结果奖励 result reward），而非每条 response 单独打分。例如"修好这个 bug 的测试是否通过""搜到的答案对不对"。
- **信用分配在 trajectory 层面**：一整条多轮 token 序列共享一个/一组 advantage，不是单轮逐条。

形式上，一条轨迹 $\tau = (s_0, a_0, o_0, s_1, a_1, o_1, \dots, s_T)$，其中 $s_{t+1}$ 与 observation $o_t$ 由 **harness（环境）** 产生，$a_t$ 由 policy 产生。agentic RL 的目标是最大化轨迹回报：

$$
J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta,\,\mathcal{H}}\Big[\,R(\tau)\,\Big]
$$

其中 $\mathcal{H}$ 表示 harness（环境）。其策略梯度为：

$$
\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta,\,\mathcal{H}}\Big[\sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t \mid s_t)\, A_t\Big]
$$

注意 $s_t$（含历史 observation 与工具结果）的转移由 harness 决定、对 $\theta$ 不可导，因此 agentic RL 把"环境交互"与"参数更新"分离成 **rollout 阶段（在 harness 里跑轨迹）** 与 **update 阶段（对整条轨迹做 PPO/GRPO 更新）** 两个交替阶段——这正是 RAGEN 的 StarPO 架构。

代表项目：Search-R1（带搜索工具的 RL）、SWE-bench RL（修 bug）、tool-use RL、RAGEN、AgentGym，以及 verl 上的 multi-turn tool-calling recipe。

## 两者的联系

**harness 就是 agentic RL 的 environment / Env**——RL 三要素 state / action / reward 中的 environment 本身。具体：

| 维度 | 单轮 RLHF/PPO | Agentic RL |
|------|---------------|------------|
| rollout 单位 | 一条 response | 一整条 agent trajectory（多轮 + 工具调用） |
| state 来源 | 单轮 prompt（固定） | harness 拼接的历史 context + observation |
| action 落地 | 文本 token | 文本 token + 工具调用（harness 执行） |
| reward 来源 | RM 给单条 response 打分 | 环境/最终结果（结果奖励，通常稀疏） |
| 信用分配 | response 级 | trajectory 级 |
| 关键风险 | reward hacking | 长轨迹、训练-推理不一致、rollout 吞吐 |

更深层的耦合——**harness 的设计直接决定 agentic RL 的可行性、吞吐、正确性**：

1. **训练-推理一致性是 on-policy 正确性的前提**：训练 rollout 用的 harness 必须和推理/部署时完全一致（同样的工具、同样的 context 拼法、同样的截断），否则"采样自当前策略 $\pi_\theta$"这一 on-policy 假设被破坏，importance ratio 失真，更新方向出错（这正是 [[21_on_policy_distillation]] 强调的分布不匹配问题在 agentic 场景的放大版）。
2. **rollout 吞吐**：agentic RL 一条 trajectory 多轮生成，KV cache 体量大、墙钟时间长。KV 压缩（MLA 见 [[12_deepseek_v2]]、PagedAttention 见 [[4_flash_attention]]）直接决定 rollout 吞吐，进而决定 RL 的样本效率与单步成本——这也是为什么 DeepSeek 系架构对 RL rollout 友好。
3. **轨迹级显存与并发**：多轮 trajectory 要在 GPU 上常驻 KV 直到回传，显存占用远高于单轮；工具调用若串行（如等搜索结果）会拉长 rollout，需要并发/异步设计。
4. **reward 的可计算性**：harness 必须能把"环境结果"翻译成标量 reward（跑测试、判答案、规则校验），这一步错了再好的算法也白搭。

简言之：**agentic RL 的工程难度，一大半在 harness 而不在算法。** 算法（PPO/GRPO 见 [[9_grpo]]、[[14_ppo]]）相对成熟，难的是"在多轮、长轨迹、带工具、要一致性、要高吞吐"的 harness 上把 rollout 跑对跑快。

## 优势与挑战

**优势**：
- 能学"过程"而非只学"答案"——通过工具与环境交互，policy 能学到**何时调用什么工具**、**如何利用 observation 修正推理**，这类能力单轮 SFT/RLHF 难以获得。
- reward 来自真实环境结果（测试通过、答案正确、任务完成），比 RM 打分更难被 reward hacking，且更贴近下游真实任务。
- 与 test-time scaling（见 [[17_test_time_scaling]]）天然耦合：训练时学到的"多想几步、会用工具"的能力，在推理时直接转化为更长的有效计算。

**挑战**：
- 长轨迹 + 稀疏结果 reward → 信用分配难、方差大（RAGEN-2 用 SNR-Adaptive Filtering 按 reward 方差过滤 rollout 来降噪）。
- **reasoning collapse / 模板坍塌**：多轮训练容易让 policy 退化成复读固定模板（RAGEN-2 用互信息代理指标做诊断）。
- rollout 成本高：一条 trajectory 要多轮 LLM 调用 + 工具执行，单样本成本远高于单轮 RLHF。
- 一致性维护重：harness 任何改动（工具行为、context 截断）都可能破坏 on-policy 假设。

## 在大模型中的应用与推荐学习项目

理解"agentic RL + harness"**两者同时**，最推荐按下列顺序：

### 1. 首选：RAGEN（github.com/RAGEN-AI/RAGEN）

为"理解 agentic RL 训练到底怎么工作"而设计，最适合建立心智模型：

- **自带 diagnostics**：推理坍塌检测（互信息代理指标）、SNR-Adaptive Filtering（reward 方差过滤）——直接看到 agentic RL 训练的失败模式。
- **harness 切得很干净**：三模块 = Environment State Manager + Context Manager + Agent Proxy，正好对应 harness 的三大职责，读代码就能看清"harness 是什么、由什么组成"。
- **内置 10 个环境**（Sokoban / WebShop / SearchQA / Lean / Countdown / Sudoku …），方便对比"harness 变了、RL 算法不变"时的行为差异。
- **算法 = StarPO**（State-Thinking-Actions-Reward Policy Optimization），支持 PPO（token-level + value）与 GRPO（trajectory-level）两种变体，正好对应 [[14_ppo]] 与 [[9_grpo]]。
- **训练底座是 verl 子模块**——读 RAGEN = 同时看到 harness 层（RAGEN）与 RL 训练层（verl），一次把两层都摸到。

### 2. 生产级：verl（github.com/volcengine/verl，22.9k star）

RAGEN 的训练底座、agentic RL 的工业层：

- **HybridFlow 论文**：rollout worker 与训练后端解耦——vLLM/SGLang 做 rollout，FSDP/Megatron 做训练，3D-HybridEngine 在生成↔训练间 reshard 权重，正是"harness 推理引擎"与"RL 训练引擎"的工业级拼接。
- 明确支持 **multi-turn tool calling + 搜索工具 + Sandbox Fusion**；2026.5 推出 **uni-agent**（统一 agent 框架）与 **verl-agent**（长程 agent 训练）。
- 是 RAGEN / Search-R1 / DeepResearcher / OpenManus-RL 的**共同底座**——理解它即理解 agentic RL 生态的"地基"。

### 3. 纯 harness 理解：SWE-agent + SWE-bench

只想看清"harness 本身"（暂不看 RL 训练）时最经典：纯 agent harness，构成最清晰的"模型 → 环境（Docker + 测试）→ reward"闭环。

**学习路径**：先读 RAGEN（小、清楚、带诊断）建立"harness + agentic RL"的完整心智模型 → 再读 verl 看工业级如何把 rollout 与训练拼起来、如何保证一致性 → 用 SWE-agent 补全"harness 单独"的工程直觉。

## 与后训练的关联

agentic RL 是后训练的前沿主线之一：它把 [[15_policy_gradient]] 的闭环从"单条 response"扩到"agent trajectory"，把 [[16_reward_model]] 的稀疏 reward 换成更难被 hacking 的环境结果 reward，并与 [[17_test_time_scaling]] 形成训练-推理的能力闭环。其工程难点主要落在 harness：训练-推理一致性（[[21_on_policy_distillation]] 的核心前提在 agentic 场景被放大）、rollout 吞吐（[[4_flash_attention]]、[[12_deepseek_v2]] 的 KV/MLA 压缩直接惠及 RL rollout）。算法本体仍是 [[9_grpo]] / [[14_ppo]]，只是作用单位从 response 变成 trajectory。

## 参考文献

- RAGEN: "RAGEN: Understanding Multi-Turn Agent RL", github.com/RAGEN-AI/RAGEN（StarPO 框架、推理坍塌诊断）。
- verl / HybridFlow: Sheng et al., "HybridFlow: A Flexible and Efficient RLHF Framework", 2024, github.com/volcengine/verl。
- Search-R1: github.com/PeterGriffinjin/Search-R1（带搜索工具的 agentic RL）。
- SWE-agent / SWE-bench: Yang et al., "SWE-agent", 2024; Jimenez et al., "SWE-bench", ICLR 2024（经典 agent harness + eval）。
- AgentGym / AgentTrek: OpenRLI, "AgentGym: Evolving LLM-Based Agents", 2024（通用 agent 训练平台，harness + RL）。
- DeepSeek-R1 / DeepSeek-V3: DeepSeek-AI（GRPO + 推理 RL，与 agentic RL 的训练-推理一致性实践）。
