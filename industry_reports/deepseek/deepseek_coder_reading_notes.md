# DeepSeek-Coder 阅读笔记

> 论文：DeepSeek-Coder: When the Large Language Model Meets Programming - The Rise of Code Intelligence
> arXiv: 2401.14196v2, 2024年1月
> 机构：DeepSeek-AI、北大（PKU MOE HCST 重点实验室）
> 阅读视角：**代码 LLM / 数据工程师**

---

## 论文总结表格

| 维度 | 内容 |
|------|------|
| 论文标题 | DeepSeek-Coder: When the Large Language Model Meets Programming - The Rise of Code Intelligence |
| 发表时间 | 2024年1月 |
| 研究背景 | 闭源代码模型（Codex、GPT-3.5/4）主导代码智能，限制了开放研究；开源代码模型与闭源存在显著性能差距 |
| 核心贡献 | 开源 DeepSeek-Coder 系列（1.3B/6.7B/33B，base + instruct），从零训练 2T tokens，宽松许可可商用 |
| 方法创新 | ① **仓库级数据构建**（依赖解析 + 拓扑排序排列文件）；② **FIM 中间填充**（50% PSM 率）；③ 16K 长上下文 |
| 关键实验结果 | Base 33B 开源 SOTA（HumanEval 50.3% / MBPP 66.0%）；Instruct 33B 超 GPT-3.5-Turbo；Base 6.7B≈CodeLlama 34B（小 5 倍） |
| 局限性 | 长上下文理论 64K 但实测仅 16K 可靠；LeetCode 数据污染无法完全排除；纯代码训练使 v1 自然语言/数学偏弱（v1.5 修复） |
| 与同期工作对比 | vs StarCoder / CodeLlama 全面领先；首次将仓库级数据构建引入预训练；FIM 沿用 Bavarian 2022 并系统消融 |

---

## 研究背景与动机（重点）

### 核心问题
代码智能被庞大的**闭源模型**（Codex、GPT-3.5/4、Gemini）主导，研究者和开发者因专有性无法使用；**开源 vs 闭源存在显著性能差距**。

### 解决思路
开源一整套不同规模（1.3B→33B）的代码模型，每个规模都含 base + instruct，从零在 **2T tokens / 87 种语言**上训练，并以宽松许可允许**无限制商用**。

---

## 方法创新（核心）

### 创新 1：仓库级数据构建 (Repository-Level Data Construction)

以往代码 LLM 在**文件级**源码上训练，忽略项目内文件间依赖，难以扩展到项目级场景。本文首次在预训练阶段引入仓库级数据：

- **依赖解析**：用正则提取调用关系（Python `import`、C# `using`、C `include`）
- **拓扑排序排列**（算法 1）：确保每个文件的依赖上下文排在该文件**之前**
- **改进的拓扑排序**：选入度**最小**（非为零）的节点，以处理依赖图中的**环（cycles）**
- **不相连子图**分别排序后拼接成单个训练样本
- 每个文件开头加**路径注释**，保留路径信息
- **效果**：消融显示移除仓库级预训练后，Java/TS/C# 跨文件补全性能下降（表 7）

### 创新 2：FIM 中间填充 (Fill-in-the-Middle)

仅靠 next token prediction 学不会"根据上下文填空"的代码补全能力。引入 FIM：把文本切三段、打乱顺序、用特殊字符连接。

| 模式 | 排列顺序 | 说明 |
|------|----------|------|
| **PSM** (Prefix-Suffix-Middle) | Prefix, Suffix, Middle | 中间段被前后缀夹住（本文采用） |
| **SPM** (Suffix-Prefix-Middle) | Suffix, Prefix, Middle | 不同结构挑战 |

- **消融结论（图 3）**：100% FIM 率在 HumanEval-FIM 峰值但代码补全最弱 → 存在 FIM vs 补全的**权衡**；50% PSM 优于 MSP（T5 式遮蔽片段）
- **最终选择 50% PSM 率**，在文档级、打包前实现
- **训练样本格式**：
  ```
  <｜fim_start｜>f_pre<｜fim_hole｜>f_suf<｜fim_end｜>f_middle<|eos_token|>
  ```
- 引入 3 个哨兵 token

### 创新 3：16K 长上下文 (Long Context)

- 重配 **RoPE**：线性缩放，缩放因子 1→4，基础频率 10000→100000
- 额外训练 1000 步，batch 512，序列长度 16K
- 理论支持 **64K**，但**实测 16K 内最可靠**

---

## 数据收集与处理（数据工程视角重点）

### 数据配比
| 成分 | 占比 |
|------|------|
| 源代码 | 87% |
| 英文代码相关 NLP（GitHub Markdown + StackExchange） | 10% |
| 中文 NLP（与代码无关） | 3% |

### 五步数据流水线
1. **数据爬取**：GitHub 2023 年 2 月前的公开仓库，保留 87 种语言
2. **规则过滤**（沿用 StarCoder 规则）：平均行长 >100 / 最大行长 >1000 / 字母字符 <25% 等过滤 → 缩减至原始 **32.8%**
3. **依赖解析**：见创新 1
4. **仓库级去重**：在**仓库级**（非文件级）做近似去重，避免破坏仓库结构
5. **质量筛查 + 去污染**：编译器 + 质量模型 + 启发式规则；**n-gram 过滤**防测试集泄漏（10-gram 完全匹配则剔除；3~10 gram 用精确匹配）

### 最终数据规模
- **798 GB，6.03 亿文件**，87 种语言
- 占比 Top：Java 18.63% / Python 15.12% / C++ 11.39% / TypeScript 7.60% / PHP 7.38% / C# 7.34% / JavaScript 6.75%

---

## 训练设置要点

### 模型架构（表 2）
| 配置 | 1.3B | 6.7B | 33B |
|------|------|------|------|
| 激活函数 | SwiGLU | SwiGLU | SwiGLU |
| hidden size | 2048 | 4096 | 7168 |
| 中间维度 | 5504 | 11008 | 19200 |
| 层数 | 24 | 32 | 62 |
| 注意力头 | 16 | 32 | 56 |
| 注意力机制 | Multi-head | Multi-head | **GQA (组=8)** |
| 最大学习率 | 5.3e-4 | 4.2e-4 | 3.5e-4 |

- decoder-only Transformer + RoPE + FlashAttention v2
- 仅 33B 用 GQA（提升训练/推理效率）

### 训练配置
- 分词器：BPE，词表 **32000**
- 优化器：AdamW（β₁=0.9, β₂=0.95）
- 学习率：**三阶段策略**，2000 warmup，末段为初始 10%，每阶段 ×√(1/10)
- 框架：HAI-LLM（张量并行 + ZeRO 数据并行 + PipeDream 流水线并行）
- 硬件：A100 + H800 集群，节点内 NVLink/NVSwitch，节点间 InfiniBand

### 指令微调（DeepSeek-Coder-Instruct）
- Alpaca 格式，`<|EOT|>` 分隔对话轮次
- 余弦调度，100 warmup，初始 lr 1e-5，batch 4M tokens，总 2B tokens

---

## 关键实验结果（重点）

### 代码生成（表 3，HumanEval/MBPP 多语言）
| 模型 | 规模 | HumanEval Avg | MBPP |
|------|------|---------------|------|
| CodeLlama-Base | 34B | 41.0% | 55.2% |
| **DeepSeek-Coder-Base** | 6.7B | 44.7% | 60.6% |
| **DeepSeek-Coder-Base** | 33B | **50.3%** | **66.0%** |
| GPT-3.5-Turbo | - | 64.9% | 70.8% |
| **DeepSeek-Coder-Instruct** | 33B | **69.2%** | 70.0% |

→ Base 33B 比同级 CodeLlama-34B 高 **+9% / +11%**；**6.7B 已超 34B**；Instruct 33B（Python 79.3%）超 GPT-3.5-Turbo（76.2%）

### DS-1000 数据科学（表 4）
DeepSeek-Coder-Base 33B 平均 **40.2%**，领先所有同规模开源模型，证明真实数据科学库使用能力强。

### LeetCode Contest（表 5，竞赛级真实题）
| 模型 | Overall | +CoT |
|------|---------|------|
| GPT-3.5-Turbo | 23.3% | 23.3% |
| **DeepSeek-Coder-Instruct 33B** | 27.8% | **28.9%** |
| GPT-4-Turbo | 40.6% | 41.8% |

→ 唯一超 GPT-3.5-Turbo 的开源模型；**CoT 提示显著提升**（强烈推荐复杂任务用 CoT）；但距 GPT-4-Turbo 仍有差距

### FIM 单行填充（表 6）
DeepSeek-Coder-Base 33B 平均 **81.2%**；**1B（70.4%）已超更大的 StarCoder 与 CodeLlama** → 归功于预训练数据质量；推荐 **6.7B 部署于代码补全工具**（效率/准确率平衡）

### 跨文件补全（表 7，CrossCodeEval）
DeepSeek-Coder-Base 6.7B + Retrieval 四语言全面领先；**移除仓库级预训练后 Java/TS/C# 下降** → 验证仓库级预训练有效性（数据来自 2023.3-6，避免泄漏）

### 程序辅助数学推理（表 8，PAL 方法）
DeepSeek-Coder-Base 33B 七基准平均 **65.8%**，领先所有基线，展示数学计算潜力。

---

## 第 5 章：从通用 LLM 继续预训练（DeepSeek-Coder-v1.5）

**动机**：增强 v1 偏弱的自然语言理解与数学推理。

- 从 **DeepSeek-LLM-7B Base** 出发，额外训练 **2T tokens** → DeepSeek-Coder-v1.5 7B
- 仅用 next token prediction，上下文 4K（**不用 FIM**）
- 数据配比：源码 70% / Markdown+StackExchange 10% / 代码相关 NLP 7% / 数学相关 NLP 7% / 中英双语 6%

**对比结果（表 10）**：
| 模型 | HumanEval | MBPP | GSM8K | MATH | MMLU | BBH |
|------|-----------|------|-------|------|------|------|
| Base | 44.7% | 60.6% | 43.2% | 19.2% | 36.6% | 44.3% |
| **Base-v1.5** | 43.2% | 60.4% | **62.4%** | **24.7%** | **49.1%** | **55.2%** |

→ **编码略降，但数学推理与自然语言大幅提升** → 印证"最强的代码 LLM 应建立在强大的通用 LLM 之上"

---

## 一句话总结

DeepSeek-Coder 通过**仓库级数据构建**（依赖解析 + 拓扑排序）、**FIM 中间填充**（50% PSM）和 **16K 长上下文**三大手段，从零训练出开源 SOTA 代码模型，33B 超越 GPT-3.5-Turbo、6.7B 媲美 5 倍大的 CodeLlama-34B，核心命题是"**高质量项目级数据 + 填空训练 = 开源可商用的强代码智能**"。

---

## 对代码 LLM / 数据工程师的关键启示

1. **仓库级 > 文件级**：用依赖解析 + 拓扑排序把相关文件按依赖顺序拼接，显著提升跨文件补全（尤其强类型语言 Java/TS/C#）
2. **拓扑排序要能处理环**：选最小入度而非零入度，应对真实代码的循环依赖
3. **FIM 率是权衡**：100% FIM 伤补全能力，**50% PSM 是甜点**；在文档级、打包前实现
4. **数据质量 > 模型规模**：1B 模型靠高质数据就能在 FIM 上超更大模型 → 数据清洗（5 步流水线）是核心竞争力
5. **去污染必做**：n-gram 过滤（10-gram 完全匹配 + 3-10 gram 精确匹配）防 HumanEval/MBPP/GSM8K/MATH 泄漏
6. **长上下文理论 ≠ 实测**：RoPE 缩放理论 64K，但实测 16K 才可靠，部署时别盲信理论上限
7. **复杂任务用 CoT**："先写提纲再写代码"显著提升难题表现
8. **代码模型应建立在通用 LLM 上**：v1.5 从通用 base 继续训练，数学/NL 大涨而代码仅微降 → 通用底座是更优范式
9. **部署选型**：代码补全工具推荐 6.7B（效率/准确率平衡），追求极致能力用 33B

---

## 相关知识点

- [[1_rope]] — RoPE 旋转位置编码（长上下文线性缩放的基础）
- [[fill_in_the_middle]] — FIM / PSM / SPM 填空训练范式（待补充）
- 关联论文：[[deepseek_llm_reading_notes]]（v1.5 的通用底座）、[[deepseek_moe_reading_notes]]（同期 DeepSeek 架构工作）
