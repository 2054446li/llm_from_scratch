# DeepSeek-Prover-V1.5 阅读笔记

> 论文：DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search
> arXiv: 2408.08152v1, 2024年8月
> 机构：DeepSeek-AI
> 阅读视角：**后训练工程师（Post-Training Engineer）** —— 把本文当作一条「SFT → RLVR（GRPO）→ 推理时树搜索」的完整后训练流水线来读，重点理解**可验证奖励驱动的 RL**、**截断-续写如何把环境反馈注入训练与推理**、**奖励稀疏下的探索机制**。
> 脉络定位：[[deepseek_prover_reading_notes|DeepSeek-Prover V1]]（合成数据 + RFT 自举）→ **本文 V1.5**（加 RL/GRPO + MCTS）→ DeepSeek-R1（规则化可验证奖励做 RL 激发推理）。

---

## 0. 预备概念：什么是 tactic（看懂全文的前提）

**Lean 是"证明检查器"**：模型写的证明它逐行检查对错。证明不是直接写出最终对象，而是像下棋一样**一步步把待证目标化简，直到化简为"显然成立"**。每一步操作叫一个 **tactic（策略/招式）**。

- **tactic state（局面/证明状态）**：`⊢` 符号后面是"现在还要证什么"，前面是已知前提（如 `h₀ : 0 < x`）。
- **tactic（一招）**：对当前局面施加的变换，如 `rw`（改写）、`apply`（套用定理）、`nlinarith`（调用非线性算术求解器）。
- 一份 Lean 证明 = **一串 tactic**，每招把局面往前推一步，直到没有待证目标。

**真实例子**（miniF2F 的 `aime_1983_p9`，证 `(9x²sin²x+4)/(x·sinx) ≥ 12`）：

```lean
theorem aime_1983_p9 (x : ℝ) (h₀ : 0 < x ∧ x < Real.pi) :
    12 ≤ (9 * (x^2 * sin x^2) + 4) / (x * sin x) := by
  have h₁ : 0 < x * Real.sin x := by    -- 引入新事实：x·sinx>0
    apply mul_pos                         -- 用"正×正=正"
    exact h₀.1                            -- x>0 来自前提
    exact Real.sin_pos_of_pos_of_lt_pi h₀.1 h₀.2  -- sinx>0
  rw [le_div_iff h₁]                      -- 把"≥除法"改写成"≥乘法"
  -- 执行 rw 后 Lean 返回的新局面：⊢ 12*(x·sinx) ≤ 9·x²sin²x + 4（分母没了）
  nlinarith [sq_nonneg (3 * x * Real.sin x - 2)]  -- 提示左边是完全平方(3xsinx-2)²，证毕
```

---

## 1. 论文总结表格

| 维度 | 内容 |
|------|------|
| 论文标题 | DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for RL and Monte-Carlo Tree Search |
| 发表时间 | 2024年8月 |
| 研究背景 | LLM 自动写 Lean 4 形式化证明。**整证明生成（whole-proof）**计算高效但模型看不到中间真实局面 → **误差累积（compounding error）**；**证明步骤生成（proof-step）**能看到局面但通信开销大。需要兼得两者优点。 |
| 核心贡献 | ① **截断-续写（truncate-and-resume）**机制，用 Lean 返回的真实 tactic 状态纠正模型"脑补"；② 完整后训练流水线：预训练特化 → SFT（含 CoT 增强+tactic 状态辅助任务）→ **RLPAF（GRPO，验证器 0/1 奖励）**；③ **RMaxTS**：内在奖励驱动的 MCTS，解决证明搜索奖励稀疏问题。 |
| 模型规模 | DeepSeek-Prover-V1.5 **7B**，基于 DeepSeekMath-Base 7B |
| 方法创新 | 截断-续写把整证明生成与证明步骤生成统一为单一模型；CoT 注释嵌入 Lean 代码；tactic 状态作为 SFT 辅助预测任务；RMax 无奖励探索 + 折扣 UCB（DUCB）应对非平稳内在奖励 |
| 关键结果 | miniF2F-test **63.5%**（V1 为 50.0%）；ProofNet-test **25.3%**。均为当时 SOTA。 |
| 局限性 | 只做了 RL 的**探索（exploration）**面，未解决**利用（exploitation）**面（剪枝、partial-proof critic 缺失）；主要针对单定理，未充分处理多定理文件级证明 |
| 训练配置 | SFT: 9B token, bs2048, lr1e-4, ctx4096；RL(GRPO): SFT 作初始+参考模型, lr5e-6, KL系数0.02, 每题采样32, bs512 |

---

## 2. 全文意图（一句话 + 三件套）

> **核心矛盾**：模型在"脑补"中间局面，而 Lean 验证器知道"真相"。如何让模型用上真相？

整证明生成时模型一次性写完整串 tactic，**看不到每招执行后的真实局面**，只能基于猜测写下一招 → 第 3 招猜错后面全崩（compounding error）。论文用三件套解决：

| 阶段 | 机制 | 解决什么 |
|------|------|---------|
| **SFT**（2.2） | 截断-续写 + CoT 增强 + tactic 状态辅助任务 | 让模型学会"读懂 Lean 返回的真实局面"并续写 |
| **RL**（2.3） | RLPAF / GRPO，验证器 0/1 当奖励 | 用可验证奖励强化模型，更倾向生成能通过验证的证明 |
| **推理**（第3章） | RMaxTS（内在奖励驱动 MCTS） | 系统化探索证明路径，缓解奖励稀疏 |

**截断-续写**是贯穿全文的核心机制：模型先写完整证明→交 Lean 跑→在首个出错招处截断→把成功部分 + Lean 返回的真实 tactic 状态重新喂回→续写。相当于"闭眼下棋走错→裁判告诉你真实棋盘→睁眼继续"。

---

## 3. 第二章 模型训练（后训练核心）

### 3.1 预训练特化（§2.1）

在 DeepSeekMath-Base 7B 上**继续预训练**，用含代码+自然语言数学的高质量数据，聚焦 **Lean、Isabelle、Metamath** 等形式化语言，得到 **DeepSeek-Prover-V1.5-Base**。

### 3.2 监督微调 SFT（§2.2）★

在 V1 证明数据集基础上做三件事，最终数据集 **9,645k 条序列**：

**① 数据构建 —— expert iteration（RFT 自举）**
来源：Mathlib4、V1 合成定理、Lean Workbook、miniF2F/ProofNet 验证集。专家迭代闭环：生成证明→验证→用通过数据重训→再生成。每轮间用 DeepSeek-Coder V2 236B 标注思考过程注释。

**② 思维增强证明生成（CoT 蒸馏）**
V1 中发现自然语言推理与 Lean 形式证明有鸿沟（Lean 依赖高层 tactic 暴力求解，掩盖内部逻辑）。用 DeepSeek-Coder V2 236B 两种方式增强：证明块开头插完整自然语言方案；逐 tactic 交替插自然语言步骤。用 CoT / non-CoT 两种引导提示区分。
> 与 Lean-STaR（每步孤立 CoT）不同，本文把推理**直接嵌入 Lean 代码注释**。这是**推理能力激发 / CoT 蒸馏**——强模型生成高质量推理，蒸馏进 7B 证明模型。

**③ tactic 状态信息增强 prompt（截断-续写的训练基础）**
增强 Lean REPL + LeanDojo，抽取三元组（tactic 位置、应用前状态、应用后状态）。对有效证明的每个 tactic，插入 `/- tactic state: ... -/` 注释。
**Loss masking**：`/- tactic state: ` 之后的 token 计 SFT loss（response），之前的只作 prompt 不计 loss。
> 这是经典 **prompt/response loss masking** + 把环境（Lean）反馈作为辅助监督注入 SFT 的范例。

**训练配置**：9B token，bs2048，恒定 lr1e-4，100步 warmup，ctx4096。

### 3.3 RLPAF —— 基于证明助手反馈的强化学习（§2.3）★★

得到 **DeepSeek-Prover-V1.5-RL**。

**Prompts（课程/难度筛选）**：选 SFT 模型**成功率"中等"**的定理（难但可达），过滤后约 **4.5k** 条。每条加 CoT + non-CoT 提示。
> 太简单没梯度，太难全 0 奖励（稀疏）。这是 RLVR 绕不开的数据配比。

**Rewards（可验证奖励 RLVR）**：证明验证正确得 **1**，否则 **0**。二元奖励准确但稀疏。
> RLVR 核心论点：用形式系统/验证器替代奖励模型，**根除 reward hacking**——0/1 来自 Lean 而非可被骗分的神经打分器。

**算法 GRPO**：相比 PPO **无需 critic（价值网络）**，省一半显存/算力。对每题采样一**组**候选，用**组内相对奖励**优化。prompt 刻意选"有对有错"的，契合 GRPO 组相对本质。
> **为什么 prompt 要有对有错**：若一组 32 个采样全对/全错 → 组内奖励方差为 0 → 归一化 advantage 全为 0 → **无梯度**。故"中等成功率"筛选不仅缓解稀疏，更是 GRPO 数学上能产生梯度的前提。详见 [[9_grpo]]。

**训练配置**：SFT 同时作初始+参考模型（KL 惩罚），lr5e-6，KL系数0.02，每题采样32候选，max2048，bs512。

### 3.4 评估（§2.4）

**基准**：miniF2F（高中竞赛，244验证+244测试，Lean4.9.0）；ProofNet（本科，185验证+186测试）。
**指标**：pass@K，单张 A100-40G，vLLM，temp1/top-p0.95/max2048，验证时限300秒。

**各训练阶段对比（Figure 3，Pass@128）**：

| 模型 | miniF2F-test | ProofNet-test |
|------|------|------|
| Base (3-shot) | 29.7% | 9.7% |
| SFT (non-CoT) | 49.8% | 15.9% |
| SFT (CoT) | 50.4% | 15.9% |
| RL (non-CoT) | 50.5% | 17.5% |
| **RL (CoT)** | **51.6%** | **18.2%** |

**关键结论 —— RL 是"激发"还是"增强"？★**
- SFT 相比 Base 大幅提升（miniF2F +2/3，ProofNet 翻倍）。
- RL 在**所有 K 值上都改善 Pass@K**。这与 DeepSeekMath"RL 主要把 TopK 里已有正确答案提上来"的发现**不同**——本文观察到**基础能力的真正增强**（小采样有效，大采样仍稳定）。
> 这是当前 RLVR 领域**"RL 是激发已有能力还是扩展能力边界"**的核心争论，面试高频考点。本文站"真正增强"一边。
- CoT 一致优于 non-CoT。

---

## 4. 第三章 探索导向的 MCTS

### 4.1 Tactic 层级树抽象（§3.1）

- **截断**：整证明交 Lean 解析→最早出错处截断→成功 tactic 切成片段，每段（tactic+CoT 注释）对应一条树边→转成节点路径。
- **续写**：不同 tactic 可达同一状态，每个节点存一组等价 tactic；扩展时随机选一条作提示（含不完整证明 + tactic 状态注释）喂模型。

**Figure 4 流程**：选节点→回溯证明前缀→模型基于前缀+状态注释生成→Lean 验证→无错终止/有错截断→tactic 转新节点入树→另选候选节点重复，直到证出或预算耗尽。

### 4.2 MCTS 四步（§3.2）

标准 MCTS：**选择→扩展→模拟→回传**，其中**模拟并入扩展**（整证明生成本身=一次 rollout）。

**选择（树策略）**：`TreePolicy(s) = argmax_a Q_UCB(s,a)`。动作 a 可走向子节点或扩展自身（特殊 token a=∅，用 **virtual node** 实现非叶节点持续扩展）。
`Q_UCB(s,a) = Q(s,a)[利用] + UCB(s,a)[探索]`。

**扩展**：续写选中节点→生成 tactic→Lean 验证。因整证明输出一整串 tactic，**每轮可插入一整条路径节点**（区别于围棋 MCTS 每轮只扩展一层）。

**回传**：沿轨迹更新 Q_UCB。外在奖励 `R_extrinsic=1`（证完）/`0`（未解）。

### 4.3 内在奖励 RMaxTS（§3.3）★★

形式证明外在奖励**极度稀疏**（只有证完才非零）——经典 **hard-exploration** 情形。

**RMax 用于 MCTS**：到达未见状态就自发最大奖励。证明场景类似 ZeroRMax，纯内在奖励驱动：
```
R_intrinsic(τ) = I[至少有一个新节点被加入搜索树]   （公式3）
```
优先扩展能通向多样 tactic 状态的节点，减少冗余生成。
> 本质是 **count-based / novelty-based exploration**（"发现新状态就奖励"），与 curiosity（Pathak）、RND 同源。任务正确率极低时让训练不停滞的关键，与 GRPO"组内要有对有错"是同一矛盾的两种应对。

**非平稳奖励的 DUCB**：公式3 的内在奖励**非平稳**（树越大越难发现新状态，期望衰减）。改用**折扣 UCB**，γ∈(0,1) 淡化过时反馈，越新反馈权重越大（公式7-9），**γ=0.99**。注意折扣施加在**树搜索迭代轮次**上，而非单轨迹内动作步时域。

### 4.4 并行化（§3.4）

- **根并行**：每节点 256 runner，每 GPU 一模型 bs512；Lean 经 REPL 在数千 CPU 核集群沙箱跑；生成与验证异步。
- **树并行**：每树 32 线程 worker。
- **虚拟损失**：进行中迭代临时赋 R(τ)=0，鼓励并发 worker 选不同节点。

### 4.5 与已有方法对比（§3.5）

| 类别 | 特点 | 代表 |
|------|------|------|
| 多遍证明步骤生成 | 一次一 tactic+验证，树搜索 | GPT-f、Thor、ReProver、HTPS、InternLM2-StepProver |
| 单遍整证明生成 | 一次整段，错则重来 | DSP、Subgoal-Prover、LEGO-Prover、Lyra、miniCTX |

**本文 = 两者桥梁**：整证明起步 + 截断-续写扩展，单个模型近乎相同训练目标同时支持两策略。

---

## 5. 第四章 实验结果

### 5.1 主结果

**miniF2F-test（Table 1）**：
- 单遍：RL **60.2%**（V1 为 50.0%，+10.2pt）。仅 3200 次采样达 54.9%，超 InternLM2-StepProver 的 54.5%（后者用 64×3200 树搜索）。
- 树搜索：**RL + RMaxTS = 63.5%**（32×6400 混合策略），SOTA。

**ProofNet-test（Table 2）**：RL 单遍 25.3%；RL+RMaxTS 验证集 25.4%。超 ReProver(13.8%)、InternLM2-StepProver(18.1%)。

### 5.2 大规模采样下重审训练策略（§4.2）

- **RL 普遍增强**：RL 在所有生成设定下一致超 SFT，且与 RMaxTS 收益**正交可叠加**。RL+CoT+RMaxTS = 62.7%，比 SFT +3.7pt。
- **CoT/non-CoT/混合（Table 3）**：CoT 优势随采样预算增大而放大（CoT 利于多样化规划）；non-CoT 利于 Lean 自动化能解的计算题。**混合策略**（半预算 CoT + 半 non-CoT）= **63.5%**。

### 5.3 RMaxTS 消融（§4.3，Figure 5）

| 变体 | 结论 |
|------|------|
| UCT（无内在奖励） | 退化到接近非搜索方法 |
| RMaxTS（DUCB→UCB1） | 退化到接近 UCT（UCB1 假设大样本下穷尽探索） |
| RMaxTS（无 tactic 状态） | 增益变弱，尤其难题 → **编译器信息是树搜索必要组件** |
| **完整 RMaxTS** | 最优 60.7%(16×6400) |

> **后训练 takeaway**：内在奖励 + 折扣 UCB **缺一不可**——内在奖励提供探索信号，DUCB 加速非平稳奖励的价值传播、防止被访问次数主导。

---

## 6. 第五章 结论与未来方向

- **AlphaZero 式流水线**：expert iteration + 合成数据 = RL 的试错循环，**编译器 oracle 作为 world model 提供环境监督**，树搜索模块推进超人表现。
- **局限**：只做了 RL 的**探索**面，**利用**面（剪枝、partial-proof critic）未解决。未来方向：训练 **partial-proof critic** 评估不完整证明、剪枝——隐式做**时序信用分配（temporal credit assignment）**，把证明级反馈分解为步级价值差。
- 从单定理证明走向**多定理文件级证明**（minictx 方向）。

---

## 7. 对后训练工程师的 takeaway

1. **一条完整后训练流水线**：预训练特化 → SFT（CoT 蒸馏 + 截断-续写辅助任务）→ RLVR（GRPO）→ 推理时 MCTS。是 R1 类推理模型的前身。
2. **可验证奖励（RLVR）**：Lean 0/1 替代奖励模型，根除 reward hacking。与 [[deepseek_prover_reading_notes|V1]] 的可验证奖励、[[9_grpo]] 一脉相承。
3. **GRPO 无 critic + 组相对**：prompt 必须"有对有错"才有梯度 → 难度筛选既缓解稀疏又是数学前提。
4. **环境反馈三处复用**：SFT 辅助监督（tactic 状态）、RL 奖励（0/1）、推理搜索反馈（截断-续写）。"有能判对错的环境，就能把对错转成训练信号"。
5. **奖励稀疏的探索**：RMax 内在奖励（novelty）+ 折扣 UCB，对应 RL 中 hard-exploration 难题。
6. **RL "激发 vs 增强"之争**：本文站"真正增强"（Pass@K 全 K 上移），是面试高频争论点。
7. **截断-续写 = 把"脑补"换成"环境真值"**：训练-推理一致性的关键——模型推理时拿到的是 Lean 真实局面而非自己想象的局面（呼应 CLAUDE.md 强调的训练/推理一致性是 on-policy RL 正确性前提）。

---

## 相关知识点

- [[deepseek_prover_reading_notes]] —— V1：合成数据 + RFT 自举（本文前身）
- [[9_grpo]] —— GRPO 算法细节（本文 RL 所用）
- [[deepseek_math_reading_notes]] —— DeepSeekMath：GRPO 出处、"RL 提升 TopK"观点（本文对照对象）
- [[10_process_reward_model]] —— 过程奖励 / partial-proof critic（本文未来方向）
