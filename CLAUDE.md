# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **12-week LLM Engineer interview preparation plan** (in Chinese). It is a pure documentation/learning-material repository with no source code, build system, or tests. All content is Markdown.

## User Goal & Focus

用户的职业目标是成为一名 **后训练工程师（Post-Training Engineer）**。在总结论文、解释概念、生成学习材料时，**重点放在后训练（post-training）相关内容上**：SFT、RLHF/RLAIF、奖励模型、偏好优化（DPO/PPO/GRPO 等）、数据构建与配比、对齐技术、推理能力激发等。预训练/架构等内容可适当精简，作为背景铺垫即可。

**架构与系统技术也值得关注**：虽然用户聚焦后训练，但架构设计与训练系统技术（如注意力机制/MLA、MoE 负载均衡损失、token 丢弃策略、训练-推理一致性、显存与吞吐优化等）往往与后训练强相关——例如 KV 缓存压缩影响 RL rollout 吞吐、训练/推理一致性是 on-policy RL 正确性的前提。因此在翻译/总结这类内容时，不要一笔带过，应解释清楚其原理，并显式点出它与后训练（SFT/RLHF/RL）的关联。

## Repository Structure

- `docs/` — Weekly teaching notes (Weeks 1-3 detailed, Weeks 4-12 in a single overview file)
- `qa/` — Question banks (30-50 questions per week) plus a 60+ question comprehensive interview set
- `industry_reports/` — Technical analyses of major open-source LLM projects (DeepSeek, Qwen, Llama)
- Top-level guides: `README.md`, `LEARNING_GUIDE.md`, `START_HERE.md`, `PROJECT_STATUS.md`

## Content Conventions

- All prose is written in Chinese (Simplified)
- QA questions are categorized by type: conceptual understanding (A), comparative analysis (B), derivation (C), practical engineering (D), frontier research (E)
- Weeks 1-3 have full standalone notes; Weeks 4-12 share a single condensed overview (`docs/weeks_4-12_overview.md`)
- **公式书写规范**：写入 `.md` 文件时，数学公式一律使用 **LaTeX**（行内 `$...$`，独立公式 `$$...$$`）；在**终端交互界面**回答时，公式使用**可读的纯文本形式**（如 `ratio = π_θ / π_θ_old`），方便在终端直接阅读。

## 自动行为识别（论文阅读辅助）

在与用户对话时，自动识别以下三类意图并执行对应操作，无需用户输入特殊命令：

### 1. 知识点记录（触发词：解释/介绍/什么是/记录知识点）

当用户要求解释某个通用技术概念（如 RoPE、LoRA、KV Cache 等），自动在 `common_knowledge/` 下创建编号文件：

- 查看目录下已有文件的最大数字前缀 N，新文件编号 N+1
- 文件名：`{N+1}_{知识点小写下划线}.md`
- 内容结构：概述、核心原理/公式、与相关方法对比（表格）、优势、在大模型中的应用、参考文献
- 全部中文撰写

### 2. 疑问记录（触发条件：用户在论文阅读过程中提出疑问/困惑）

当用户在阅读论文过程中提出疑问（如"为什么..."、"...指的是什么"、"这里不太理解..."），自动追加到对应论文的临时疑问文件：

- 文件位置：与论文同目录，命名为 `reading_questions_{论文名}.md`
- 自动确定当前正在阅读的论文（根据对话上下文判断）
- 追加格式：`### Q{编号}: {疑问}`，包含具体描述和记录日期
- 如果文件不存在则先创建
- 追加完成后简要告知用户已记录

### 3. 论文总结（触发词：总结论文/生成总结/回答疑问）

当用户要求总结某篇论文或回答积累的疑问时：

- 读取论文 PDF 和临时疑问文件
- 在阅读笔记文件中生成总结表格（标题、时间、核心贡献、方法创新、关键结果、局限性、对比）
- 逐一回答疑问文件中的所有问题，基于论文原文
- 将回答写入阅读笔记的"疑问解答"部分

### 判断规则

- 如果用户的消息是一个关于论文内容的疑问/困惑 → 执行行为2（记录疑问）
- 如果用户要求解释一个通用技术概念且希望记录 → 执行行为1（知识点）
- 如果用户要求总结或回答疑问 → 执行行为3（总结）
- 如果用户只是在正常讨论/闲聊/提问期望直接回答 → 正常回答，不触发任何自动行为
- **关键区分**：用户的疑问如果期望立即得到回答（比如一般性技术讨论），则正常回答；如果是论文阅读中的标记性疑问（希望先记下来稍后统一解答），则记录到文件中。当无法区分时，先回答问题，同时询问用户是否需要记录到疑问文件。

## When Editing or Extending

- Maintain the existing Chinese writing style and Markdown formatting
- New weekly notes should follow the depth and structure of `docs/week1_transformer_basics.md` (3000+ words, section headers, concrete examples)
- New QA files should include all five question categories with 30-50 questions total
- Industry reports should cover: architecture choices, training strategy, performance benchmarks, and comparison with peers
