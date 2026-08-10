# LLM 工程师面试突击计划 (12 周密集学习)

## 📚 项目概览

这是一份为即将毕业的计算机硕士制备的详细学习计划，旨在帮助获得大型科技公司（如 Google、Microsoft、OpenAI 等）的优质 offer。

**学习模式**：理论第一 → 深度 QA → 论文精读 → 面试强化

**时间投入**：12 周，每周 40-50 小时

**学习成果**：
- ✅ 掌握 Transformer 及其所有变体的核心原理
- ✅ 深入理解大模型预训练、微调、对齐的全流程
- ✅ 理解强化学习在 LLM 中的应用（RLHF、DPO 等）
- ✅ 掌握 Agent 架构与推理系统设计
- ✅ 学习业界领先公司的技术细节（DeepSeek、Qwen、Llama 等）
- ✅ 做好面试技术题的充分准备

---

## 🧭 交互式复习台（推荐入口）

直接打开 [深度学习 × SFT × DeepSeek 复习台](interview_prep/sft_deepseek_review.html)，可以在浏览器中按题进行主动回忆和面试复习。该页面是零外部依赖的单文件 HTML，无需安装服务或联网。

当前题库共 **130 道题**：

| 模块 | 题数 | 主要内容 |
|------|------|----------|
| 通用深度学习 | 34 | 反向传播、优化器、损失函数、正则化、评测指标、CNN/RNN、生成模型、模型压缩与训练排障 |
| SFT | 36 | 数据构造、loss mask、chat template、packing、LoRA/QLoRA、遗忘、知识更新、推理蒸馏与故障诊断 |
| RL 前置 | 18 | Attention、KV Cache、RoPE/YaRN、MoE、混合精度、并行训练与 rollout 系统 |
| DeepSeek 系列 | 22 | DeepSeek LLM、MoE、V2、V3、R1、V3.2 的架构与后训练演进 |
| DeepSeek-V4 | 20 | Specialist training、GRM、reasoning effort、multi-teacher OPD、FP4 QAT、百万 token RL 与 DSec |

每道题包含面试速答、详细解释、公式、易错点、自检追问和对应的本地材料链接。支持：

- 先记录自己的答案，再揭晓标准答案；
- 按“不会 / 模糊 / 掌握”记录学习状态；
- 按模块、掌握状态或关键词筛选；
- 随机抽取薄弱题；
- 收起左侧目录，让题目区域占满屏幕；
- 导出和导入学习进度及个人答案。

常用快捷键：

| 快捷键 | 功能 |
|--------|------|
| `/` | 聚焦搜索框 |
| `[` | 收起或展开左侧目录 |
| `Space` | 揭晓或收起答案 |
| `J` / `K` | 下一题 / 上一题 |
| `1` / `2` / `3` | 标记为不会 / 模糊 / 掌握 |

### 跨电脑使用

复制整个仓库并保持相对目录结构，复习台及其 Markdown/PDF 材料链接可以在其他电脑上继续使用。题库、样式和交互均已嵌入 HTML，不依赖当前电脑的绝对路径。

学习进度默认保存在浏览器本地，不会随着仓库自动迁移。离开旧电脑前点击页面顶部的“导出”，将生成的 JSON 文件一并复制；在新电脑打开页面后点击“导入”即可恢复。若只复制 HTML 文件，题库和交互仍可使用，但指向仓库其他材料的链接将失效。

---

## 📁 项目结构

```
.
├── README.md                    # 本文件
├── LEARNING_GUIDE.md           # 详细学习指南与进度检查
├── docs/                       # 教学笔记（每周 3000+ 字）
│   ├── week1_transformer_basics.md
│   ├── week2_pretraining_fundamentals.md
│   ├── week3_training_optimization.md
│   ├── week4_sft_methods.md
│   ├── week5_alignment_techniques.md
│   ├── week6_sft_engineering.md
│   ├── week7_rl_fundamentals.md
│   ├── week8_llm_rl.md
│   ├── week9_agent_architecture.md
│   ├── week10_paper_reading.md
│   ├── week11_system_design.md
│   └── week12_interview_prep.md
│
├── industry_reports/           # 开源公司技术报告解读
│   ├── deepseek_technical_details.md      # DeepSeek 系列深度分析
│   ├── qwen_architecture.md               # Qwen 系列架构设计
│   ├── meta_llama_report.md              # Llama/Llama 2 技术细节
│   ├── anthropic_claude_report.md        # Claude & Constitutional AI
│   ├── mistral_7b_analysis.md            # Mistral 轻量化方案
│   └── other_models_comparison.md        # 其他开源模型对比
│
├── qa/                         # 深度 QA 题库（每周 30-50 题）
│   ├── week1_qa.md            # Transformer & 注意力机制
│   ├── week2_qa.md            # 预训练与大模型设计
│   ├── week3_qa.md            # 训练优化与并行策略
│   ├── week4_qa.md            # SFT 微调方法
│   ├── week5_qa.md            # 模型对齐技术
│   ├── week6_qa.md            # 工程实战与最佳实践
│   ├── week7_qa.md            # 强化学习基础
│   ├── week8_qa.md            # LLM 中的强化学习
│   ├── week9_qa.md            # Agent 架构与推理
│   ├── week10_qa.md           # 论文理解与前沿进展
│   ├── week11_qa.md           # 系统设计与权衡
│   └── week12_qa.md           # 综合面试题库（60+ 题）
│
├── interview_prep/             # 面向面试的聚合课程与主动回忆题库
│   ├── sft_deepseek_review.html # 本地交互式复习台（130 题）
│   ├── ch01_..._ch07_...md     # RL 前的模型、训练系统和 SFT 基础
│   └── ch08_..._ch17_...md     # RLHF、GRPO、DPO、OPD、Agent 与推理
│
└── papers/                     # 论文精读笔记（第 10 周）
    └── key_papers_index.md     # 10-15 篇关键论文索引
```

---

## 📖 学习内容速览

### 第一阶段：基础理论 (第 1-3 周)
- **Week 1**：Transformer 架构、注意力机制、位置编码演进
- **Week 2**：预训练基础、GPT 演进、开源模型对比
- **Week 3**：训练优化、并行策略、稳定性问题

### 第二阶段：微调与对齐 (第 4-6 周)
- **Week 4**：SFT 方法、LoRA/QLoRA、数据构建
- **Week 5**：DPO、IPO、KTO、奖励模型
- **Week 6**：工程实战、开源模型微调、最佳实践

### 第三阶段：强化学习与 Agent (第 7-9 周)
- **Week 7**：RL 基础、MDP、策略梯度、PPO
- **Week 8**：LLM 中的 RL、RLHF、KL 正则化
- **Week 9**：Agent 架构、ReAct、工具使用、推理优化

### 第四阶段：综合与面试 (第 10-12 周)
- **Week 10**：论文精读（10-15 篇关键论文）
- **Week 11**：系统设计、架构权衡、推理优化
- **Week 12**：面试题库、参考答案、面试技巧

---

## 🎯 学习方法论

### 每周学习流程
1. **读笔记** (4-6 小时)
   - 理解核心概念和原理
   - 记录疑惑点和深入思考
   
2. **深度 QA** (6-8 小时)
   - 回答 30-50 个精心设计的问题
   - 从不同角度理解知识
   - 为面试题做准备
   
3. **论文精读** (2-4 小时，第 10 周后)
   - 阅读相关论文
   - 整理核心方法和贡献
   
4. **自我检查** (1-2 小时)
   - 用自己的话讲解核心概念
   - 对比不同方法的优劣

### QA 问题分类

每个 QA 文件包含 5 类问题：

- **概念理解题**：为什么、是什么 → 测试理论掌握
- **对比分析题**：A vs B、权衡分析 → 测试深度思考  
- **原理推导题**：数学推导、原理解析 → 测试理论基础
- **实践问题题**：怎么解决、工程细节 → 测试应用能力
- **前沿进展题**：最新方法、业界动向 → 测试知识深度

---

## 🚀 快速开始

### 第一步：打开交互式复习台

直接打开 [`interview_prep/sft_deepseek_review.html`](interview_prep/sft_deepseek_review.html)，先从“通用深度学习”或“SFT”模块开始逐题作答。

### 第二步：浏览学习指南
```
阅读 LEARNING_GUIDE.md，了解详细的周度计划和检查清单
```

### 第三步：第 1 周开始
1. 阅读 `docs/week1_transformer_basics.md`
2. 回答 `qa/week1_qa.md` 中的所有问题
3. 对比阅读 `industry_reports/` 中相关公司的技术细节
4. 检查理解：能否用自己的话解释每个核心概念？

### 第四步：持续推进
- 每周末评估学习进度
- 记录重点和疑惑
- 为面试准备建立个人笔记库

---

## 📚 关键参考资源

### 开源公司技术报告
- [DeepSeek 官方报告](https://arxiv.org) - DeepSeek-LLM, DeepSeek-MoE
- [Qwen 技术文档](https://huggingface.co/Qwen) - Qwen-7B/14B/72B
- [Meta Llama 2 论文](https://arxiv.org) - Llama 2: Open Foundation and Fine-Tuned Chat Models
- [Anthropic Claude 报告](https://www.anthropic.com) - Constitution AI 对齐方法
- [Mistral 模型卡](https://huggingface.co/mistralai) - 轻量化高效设计

### 核心论文 (第 10 周详细)
1. Attention is All You Need (Vaswani et al., 2017)
2. GPT-3: Language Models are Few-Shot Learners
3. Llama 2: Open Foundation and Fine-Tuned Chat Models
4. Direct Preference Optimization (DPO)
5. ... 以及其他 10-12 篇关键论文

### 优秀学习资源
- HuggingFace 官方文档
- arxiv.org 最新论文
- 各公司技术博客
- 开源模型实现参考

---

## 💡 面试准备建议

### 技术面试关键领域
1. **模型理论**：能否深入讲解 Transformer？
2. **预训练方法**：预训练数据如何选择和清洗？
3. **微调策略**：何时用 LoRA，何时全量微调？
4. **对齐方法**：为什么需要对齐？DPO 如何工作？
5. **推理优化**：如何让模型推理更快更省资源？
6. **系统设计**：如何设计一个大规模 LLM 服务？

### 模拟面试
- 第 10 周后，每周进行 1-2 次模拟面试
- 使用 `week12_qa.md` 中的 60+ 题进行练习
- 记录常出错的地方，重点复习

---

## ⏱️ 时间投入建议

**每周 40-50 小时**

| 活动 | 时间 | 备注 |
|-----|------|------|
| 阅读笔记 | 4-6 小时 | 理解核心概念 |
| 深度 QA | 6-8 小时 | 回答 30-50 题 |
| 论文精读 | 2-4 小时 | 第 10 周后 |
| 复习总结 | 4-6 小时 | 消化理论 |
| 其他准备 | 8-10 小时 | 面试、资源查找等 |

---

## 📝 进度跟踪

完成每一周的学习后，在本文件中更新进度：

- [ ] Week 1: Transformer 基础理论
- [ ] Week 2: 预训练基础与行业对比
- [ ] Week 3: 训练优化与并行策略
- [ ] Week 4: SFT 微调方法
- [ ] Week 5: 模型对齐技术
- [ ] Week 6: 工程实战与最佳实践
- [ ] Week 7: 强化学习基础
- [ ] Week 8: LLM 中的强化学习
- [ ] Week 9: Agent 架构与推理
- [ ] Week 10: 论文精读与前沿进展
- [ ] Week 11: 系统设计与权衡
- [ ] Week 12: 面试准备与模拟

---

## 🎓 预期学习成果

完成 12 周学习后，你应该能够：

✅ 从数学原理层面理解 Transformer 的每个组件
✅ 深入讲解大模型的完整生命周期（预训练 → 微调 → 对齐）
✅ 对比不同微调策略（全量、LoRA、QLoRA、Prefix Tuning 等）的优劣
✅ 解释强化学习在 LLM 中的应用与挑战
✅ 设计 Agent 系统和推理框架
✅ 分析行业领先公司（OpenAI、DeepSeek、Qwen 等）的技术亮点
✅ 应对大公司的技术面试题
✅ 在面试中清晰、深入地讨论复杂的技术问题

---

## 📞 使用建议

- **每周末**：总结学习心得，更新进度
- **两周一次**：进行自我测试，回顾核心概念
- **第 10 周后**：每周进行 1-2 次模拟面试
- **遇到疑惑**：回到对应章节深入理解，不要跳过任何内容

---

**开始学习日期**：______
**预计完成日期**：______

祝你学习顺利！💪
