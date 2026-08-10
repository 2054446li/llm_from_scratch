# DeepSeek-V2（强大、经济、高效的 MoE 语言模型）

> DeepSeek-V2 知识入口卡。汇总这篇工作最重要的信息，作为快速回顾/面试索引。
> 📄 **完整阅读笔记**（逐节翻译、疑问解答、后训练视角）见 [industry_reports/deepseek/deepseek_v2_reading_notes.md](../industry_reports/deepseek/deepseek_v2_reading_notes.md)
> arXiv: 2405.04434, 2024 | DeepSeek-AI

## 一句话定位

236B 总参 / **21B 激活** / 128K 上下文的 MoE 模型，靠 **MLA + DeepSeekMoE** 两大架构创新，比 DeepSeek 67B **省 42.5% 训练成本、KV 缓存降 93.3%、生成吞吐 5.76×**，开源最强 MoE。

## 核心数据速记

| 维度 | 数值 |
|------|------|
| 总参数 / 激活 | 236B / 21B |
| 上下文 | 128K（YaRN 从 4K 扩展） |
| 预训练语料 | 8.1T tokens（中文 token 比英文多 ~12%） |
| 训练成本 | 172.8K GPU时/T token（67B 是 300.6K，省 42.5%） |
| KV 缓存 | 降 93.3% |
| 生成吞吐 | >50K tokens/s（67B 的 5.76×） |
| 对齐效果 | AlpacaEval 2.0 **38.9**、MT-Bench **8.97**、AlignBench **7.91**（中文超 GPT-4-0613） |

## 两大架构创新

### 1. MLA（多头潜在注意力）★ 最重要

**目的**：减少推理 KV 缓存（[[12_deepseek_v2]] 的核心卖点）。核心三招：

- **低秩 KV 联合压缩**：把 K、V 压成低维潜在向量 $\mathbf{c}_t^{KV}$（512 维），**只缓存它**，而非完整 K、V（16384 维）。
  $$\mathbf{c}_t^{KV} = W^{DKV}\mathbf{h}_t,\quad \mathbf{k}_t^{C}=W^{UK}\mathbf{c}_t^{KV},\quad \mathbf{v}_t^{C}=W^{UV}\mathbf{c}_t^{KV}$$
- **矩阵吸收**（最精妙）：上投影 $W^{UK},W^{UV}$ 是固定权重，靠矩阵乘法结合律离线折叠进 $W^Q,W^O$ → **推理时根本不解压 KV**，全程只用潜在向量。
- **解耦 RoPE**：RoPE 位置相关、破坏结合律无法吸收，故另用一路共享 key $\mathbf{k}^R$ 专门承载位置。最终缓存 $=(d_c+d_h^R)\cdot l$。

**效果（附录 D 消融）**：缓存仅为 MHA 的 4~14%，**性能反而更高** —— 不是性能换显存，是"免费午餐"。

> 补充：Q 也低秩压缩，但 Q 不进缓存，压它只为减**训练激活内存**，与 KV 缓存无关。

### 2. DeepSeekMoE

细粒度专家切分 + 共享专家隔离（每层 2 共享 + 160 路由，激活 6 个）。配套：
- **设备受限路由**：token 目标专家最多分布 $M=3$ 个设备，降通信成本。
- **三种负载均衡损失**：专家级（防路由坍缩，$\alpha_1$ 最小）/ 设备级（平衡算力）/ 通信级（平衡收发）。
- **Token 丢弃策略**：容量因子=1.0、丢最低亲和度 token、10% 序列永不丢，**保证训练/推理一致性**。

详见 [[7_mixture_of_experts]]、[[8_moe_load_balance]]。

## 后训练 Pipeline（后训练工程师重点）

```
Base ─① SFT（1.5M=1.2M helpful+0.3M safety, 2ep, lr=5e-6）→ Chat(SFT)
     ─② GRPO 在线 RL（两阶段）────────────────────────────→ Chat(RL)
```

**GRPO**：去 Critic 的 PPO 变体，组内均值当基线（详见 [[9_grpo]]）。奖励为**结果级（outcome-level）**，整条 response 一个标量，未用 PRM（[[10_process_reward_model]]）。

**两阶段 RL**：
1. **推理对齐**：$RM_{reasoning}$，代码用编译器反馈、数学用真值标签（RLVR 雏形）。
2. **偏好对齐**：多奖励 $r = c_1 RM_{helpful} + c_2 RM_{safety} + c_3 RM_{rule}$。

**系统优化**：混合引擎 + vLLM 大 batch 采样 + CPU offload，支撑在线 RL。

## 三条值得记住的讨论结论

1. **SFT 数据量可减不可消**：<10K 会让 IFEval 明显下降（反驳 LIMA "少即是多"）。
2. **对齐税**：RLHF 涨对话表现，却可能损害 BBH 等标准基准，需权衡。
3. **在线 > 离线**：on-policy RL 显著优于离线（如 DPO），故大力投入在线 RL 系统。

## 长上下文：YaRN

4K → 128K，仅在 32K 上训 1000 步。因 MLA 把位置解耦到 $\mathbf{k}^R$，YaRN **只需作用于这一路**。详见 [[11_yarn]]。

## 对后训练工程师的 takeaway

1. 完整 SFT → 两阶段 GRPO 是可复用的后训练范本。
2. **可验证奖励**（编译器/真值）是激发推理能力的关键路径。
3. MLA 让 RL rollout 能用大 batch（KV 缓存小），间接提升 RLHF 吞吐。
4. 训练/推理一致性是 on-policy RL 正确性的隐性前提。

## 相关知识点

- [[7_mixture_of_experts]] — DeepSeekMoE 的 MoE 基础
- [[8_moe_load_balance]] — 负载均衡损失详解
- [[9_grpo]] — GRPO 完整公式、vs PPO
- [[10_process_reward_model]] — PRM（V2 未用，对照）
- [[11_yarn]] — 长上下文扩展，仅作用于 MLA 的 $\mathbf{k}^R$
- [[4_flash_attention]] — 注意力计算加速（与 MLA 正交）

## 参考

- DeepSeek-AI, *DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model*, 2024.
- 📄 详细笔记：[deepseek_v2_reading_notes.md](../industry_reports/deepseek/deepseek_v2_reading_notes.md)
