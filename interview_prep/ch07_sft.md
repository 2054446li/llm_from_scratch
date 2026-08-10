# ch07 — SFT 监督微调

> SFT 是后训练的第一步，面试必考数据构造、loss mask、灾难性遗忘三个点。

---

## Q1 ⭐ SFT 的目标是什么？和预训练有什么区别？
- **预训练**：next-token prediction，学习语言分布，无监督。
- **SFT**：在指令-回复对上做 next-token prediction，但**只对回复部分计算 loss**（loss mask 掉 prompt），让模型学会"按指令回复"的格式和风格。
- **本质**：SFT 不注入新知识，而是激发预训练中已有的能力，并对齐输出格式与人类期望。

---

## Q2 ⭐ Loss Mask 是什么？为什么要 mask 掉 prompt？
- 训练时输入是 `[system + user prompt + assistant response]`，只对 **assistant response** 部分的 token 计算交叉熵 loss，prompt 部分 mask 为 0。
- **原因**：① prompt 是条件，不是要学的输出；② 若对 prompt 也算 loss，模型会被优化去"预测用户输入"，偏离目标；③ 避免模型在推理时重复 prompt。

---

## Q3 ⭐ Chat Template 是什么？为什么重要？
- 把多轮对话格式化为模型可识别的字符串，例如 Llama 的 `[INST]...[/INST]` 或 ChatML 的 `<|im_start|>user\n...<|im_end|>`。
- **重要性**：训练和推理必须用**完全相同**的 template，否则分布不匹配，模型行为异常（如不知道何时停止生成）。
- 特殊 token（`<|im_start|>`、`<|im_end|>`、`<|eot_id|>`）在 tokenizer 中有专用 id，不能被普通文本覆盖。

---

## Q4 ⭐ 灾难性遗忘（Catastrophic Forgetting）是什么？如何缓解？
- **问题**：SFT 在小数据集上微调时，模型会"忘记"预训练学到的通用能力（如多语言、代码、常识）。
- **缓解方法**：
  1. **混入预训练数据**：SFT 数据中加入少量预训练语料（通常 5-10%），保持通用能力。
  2. **小学习率**：SFT 用比预训练小 1-2 个数量级的 LR（如 1e-5 vs 1e-4）。
  3. **LoRA / PEFT**：只微调少量参数，主干权重变化小，遗忘少。
  4. **数据多样性**：SFT 数据覆盖多种任务类型，不过度集中于单一领域。

---

## Q5 LoRA 的原理？为什么适合 SFT？
- **核心**：假设权重更新矩阵 ΔW 是低秩的，用两个小矩阵 A（d×r）和 B（r×d）近似：`ΔW = BA`，r << d。
- 只训练 A 和 B，冻结原始权重 W，参数量从 d² 降到 2dr。
- **适合 SFT 的原因**：① 显存占用小（梯度只对 A/B 计算）；② 遗忘少（主干不变）；③ 可合并回原始权重（推理无额外开销）。
- **QLoRA**：在 LoRA 基础上把基础模型量化为 4-bit，进一步省显存，单卡可微调 70B 模型。

---

## Q6 SFT 数据质量 vs 数量？
- **质量 >> 数量**：LIMA 论文（2023）表明 1000 条高质量数据的 SFT 效果可媲美数万条低质量数据。
- **高质量标准**：指令多样（覆盖不同任务）、回复准确（无幻觉）、格式规范、难度适中（太简单无益）。
- **数据飞轮**：用强模型生成数据 → 人工过滤 → 训练弱模型 → 弱模型生成更多数据（Self-Instruct / Alpaca 路线）。

---

## Q7 🔥（进阶）为什么 SFT 比 RL 更容易造成灾难性遗忘？
- **现象**：同等目标任务表现下，**RL 比 SFT 遗忘更少**（跨 Llama/Qwen 一致）。
- **原因（主流假说）**：RL 用**近似 on-policy 数据**（模型自己采样），mode-seeking，参数更新保守，倾向保留原有"能力电路"；SFT 在 **off-policy 数据**（外部标注）上优化，分布偏移大，更易破坏已有电路。遗忘程度与"到 base 策略的 KL 距离"正相关。
- **"spurious forgetting" nuance**：有时表现下降不是真忘了知识，而是模型不再把 prompt 识别为旧任务——能力还在，只是"入口"变了。
- **实践启示**：想减少遗忘——① replay（混原分布数据）② 用 on-policy 数据 ③ 迭代式 SFT（在 RL 生成的数据上 SFT）④ 冻结 RL 关键参数 + 只在高熵 token 算 loss。
- **面试价值**：这是 2025-2026 的热点发现，能讲清 on-policy 与遗忘的关系很加分。

---

## Q8 SFT 常见超参与坑？
- **学习率**：1e-5 ~ 2e-5（比预训练小 1-2 个数量级），过大易遗忘/崩溃。
- **epoch**：通常 1-3 轮，过多会过拟合 + 遗忘（SFT overtraining 还会加剧后续 RLVR 的熵坍缩）。
- **packing**：把多条短样本拼成一条长序列提高效率，但要注意 attention mask 隔离（不让样本间互相看到），否则污染。
- **special token**：template 的特殊 token 必须正确注册，训练/推理一致。

---

## 一句话速记
- SFT：只对 response 算 loss，激发能力而非注入知识。
- Loss mask：mask 掉 prompt，只学回复。
- 灾难性遗忘：混预训练数据 + 小 LR + LoRA 缓解；RL 比 SFT 遗忘少（on-policy mode-seeking）。
- LoRA：低秩分解 ΔW=BA，省显存、少遗忘。
