# ch06 — 预训练与评估

> 这章偏背景知识，面试中作为铺垫，重点是 Scaling Law 和 perplexity 的理解。

---

## Q1 Tokenizer 的主流方案？BPE vs WordPiece vs SentencePiece？
- **BPE（Byte Pair Encoding）**：从字符开始，反复合并频率最高的相邻对，直到词表大小达标。GPT 系列使用。
- **WordPiece**：类似 BPE，但合并标准是最大化语言模型似然（而非频率）。BERT 使用。
- **SentencePiece**：语言无关，直接在原始 Unicode 字节上做 BPE 或 Unigram，不依赖空格分词。Llama / Qwen / DeepSeek 使用。
- **Byte-level BPE**：在字节（256个基础 token）上做 BPE，无 OOV 问题。GPT-2/3/4 使用。

**追问：词表大小的影响？** 词表大 → 序列更短（推理更快）但 embedding 层参数更多；词表小 → 序列更长。主流 LLM 词表 32K-150K。

---

## Q2 ⭐ Scaling Law 的核心结论？
**Chinchilla Scaling Law（Hoffmann 2022）**：给定计算预算 C（FLOPs），最优的模型参数量 N 和训练 token 数 D 满足 `N ≈ D`（大致 1:1），即**模型和数据应同步扩大**。

- 之前 GPT-3 等模型训练 token 数相对参数量偏少（欠训练）。
- Chinchilla 结论：**20B 模型训 400B token ≈ 70B 模型训 1.4T token**，前者更高效。
- 现代 LLM（Llama 2/3）进一步推进：小模型训更多 token（推理友好），Llama-3 8B 训了 15T token。

**追问：Scaling Law 对后训练的启示？** 预训练数据质量和规模决定能力上界，后训练只能激发/对齐，不能凭空注入新知识（这也是"RL 提升 Maj@K 不提升 Pass@K"的根本原因）。

---

## Q3 ⭐ Perplexity（困惑度）是什么？怎么理解它？
**定义**：`PPL = exp(-1/N · Σ log P(x_t | x_{<t}))`，即模型对测试集的平均负对数似然的指数。

**直觉**：PPL=10 意味着模型平均每步在"10个等可能选项"中选择，越低越好。

**局限**：
- PPL 只衡量语言建模能力，不直接反映下游任务表现（一个 PPL 低的模型不一定 instruction following 好）。
- 对 tokenizer 敏感（不同 tokenizer 的 PPL 不可直接比较）。
- 后训练后 PPL 可能略升（因为分布偏移），但下游任务表现提升。

---

## Q4 预训练数据配比的原则？
- **多样性**：网页（CommonCrawl）+ 代码（GitHub）+ 书籍 + 学术论文 + 多语言。
- **质量过滤**：去重（MinHash）、质量分类器过滤低质量网页、去除 PII。
- **配比影响能力**：代码比例高 → 推理能力强（DeepSeek 发现代码数据对数学推理有迁移）；数学数据 → 数学能力。
- **后训练数据不能弥补预训练缺陷**：预训练没见过的知识，SFT/RLHF 无法注入。

---

## 一句话速记
- Chinchilla：最优训练 N≈D（参数量≈token数），现代 LLM 倾向小模型多训练。
- PPL：越低越好，但不直接等于下游任务好，后训练后可能略升。
- 代码数据：对推理能力有正迁移，是预训练配比的重要组成。
