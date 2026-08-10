# ch14 — Agentic RL

> 2025-2026 爆发方向，秋招高频。核心：复用 GRPO/RLVR 内核，叠加三个增量维度——多轮长程信用分配、工具 token mask、异步 off-policy rollout。

---

## Q1 🔥 Agentic RL 和单轮 RLHF 的本质区别？
- **单轮 RLHF**：序列级 bandit——一整条回复 = 一个动作，末端打一个分。
- **Agentic RL**：多步 MDP——一个 action 可能是"调工具/执行代码/搜索/点网页"，环境每步返回 observation，直到终态。
```
state_0 →(思考+动作 a_0)→ obs_0 → state_1 → a_1 → obs_1 → ... → 终态(成败)
```
- **多出的三个维度**：① 长程信用分配 ② 工具结果 token mask ③ 长轨迹 off-policy/异步吞吐。
- **好消息**：算法内核仍是 GRPO + RLVR，只是加了"多轮 + 环境 + mask"。

---

## Q2 🔥 Agent Loop 的代码实现？（面试可能让手写）
```python
messages = [{"role": "user", "content": query}]
while True:
    response = model.generate(messages)          # 模型生成一次
    messages.append({"role": "assistant", "content": response})
    tool_calls = extract_tool_calls(response)
    if not tool_calls:
        break                                     # 无工具调用 → 最终答案，退出
    for call in tool_calls:                       # 同一轮内独立 call 可并行
        result = execute_tool(call)
        messages.append({"role": "tool", "content": result, "tool_call_id": call.id})
    # 回到循环顶部，把工具结果连同历史再喂给模型
return messages[-1]
```
- **单轮内并行**：一次生成可发多个独立 tool call（并行执行）。
- **跨轮串行**：若下一个 call 依赖上一个结果，必须等结果拼回后再生成。
- **终止条件**：模型输出不含 tool_call（纯文本）即结束。

---

## Q3 ⭐🔥 为什么工具/环境返回的 token 必须 mask 掉？
- agent 轨迹里 `role: "tool"` 的 token 是**环境返回的，不是模型生成的**（搜索结果、代码输出、网页内容）。
- 计算 loss 时必须 **mask 掉这些 token**，否则等于让模型去"学习模仿环境输出"，破坏**训练-推理一致性**（推理时环境输出是外部给的，模型不该去预测它）。
- 这是 agent RL 最高频的工程正确性考点，直连 SFT 的 loss mask 思想和训练-推理一致性主线。

---

## Q4 🔥 长程信用分配怎么做？（agentic RL 最核心的新问题）
一条 trajectory 几十步只有末端一个奖励，如何分给中间步骤？三条路线：
1. **outcome-only + GRPO 组内基线**（最省事）：末端奖励广播给整条轨迹所有 token，靠组内多条 rollout 相对比较隐式分配。R1 式做法的直接延伸。
2. **过程奖励 / step-level reward**：给中间步骤显式打分（PRM），但 agent 场景 PRM 更难训、更易 hack。
3. **turn-level advantage**：把优势估计粒度从 token 抬到"轮/步"级——GSPO"序列级 ratio"思路的延伸。
- **归位框架**：按分配粒度（token/segment/step/turn/multi-agent）× 方法论（MC/TD/模型/博弈）二维分类。

---

## Q5 🔥 为什么 Agentic RL 更 off-policy？异步 rollout 解决什么？
- **长度方差巨大**：有的任务 2 步结束、有的 50 步，batch 内 rollout 时间严重不均。
- **更 off-policy**：长 trajectory 让采样与更新之间延迟更大，需要离策略修正（重要性采样，直连 k1/k2/k3 KL 估计和 DeepSeek-V3.2 离策略配方）。
- **异步 rollout**：工具调用（真调 API/跑代码沙箱）很慢，同步等待会让 GPU 空转。verl 用 **asyncio 协程**让多条 trajectory 的工具调用并发执行，避免 GPU 空转，提升吞吐。
- **吞吐瓶颈转移**：从 GPU 前向转移到环境交互。

---

## Q6 🔥 Agentic RLVR 和典型任务域？
- **agentic RLVR**：RLVR 从"答案校验"扩展到"环境状态校验"——网页任务到达目标页、SWE 任务测试通过、任务完成度。
- **reward hacking 新形态**：agent 会"钻环境空子"——改测试而非改代码、走捷径绕过验证、答案对但过程无效，比单轮更隐蔽。
- **典型任务域**：
  - Search / Deep Research agent（多轮检索，Search-R1）
  - Code / SWE agent（改真实仓库跑测试，ReTool）
  - Computer / Browser use（GUI 操作）
  - Math with tools / TIR（调代码解释器）

---

## 一句话速记
- Agentic RL = GRPO/RLVR 内核 + 三增量（长程信用分配 / 工具 token mask / 异步 off-policy rollout）。
- Agent loop：生成→检查 tool_call→执行→拼回→再生成，直到无 tool_call。
- 工具返回 token 必须 mask（训练-推理一致性）。
- 异步 rollout：asyncio 并发工具调用，防 GPU 空转。
