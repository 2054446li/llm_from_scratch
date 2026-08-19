# Kimi-K3 Medium 与 Max：Reasoning 长度和入库率对比

更新时间：2026-08-17

## 1. 统计对象

本报告比较两组结果：

- **Medium**：现有 SFT 入库数据中的 Kimi-K3 thinking=on、reasoning_effort=medium 结果。
- **Max**：从现有 SFT 中按 131 个场景各抽一条、使用 `kimi-k3-offical` 和 reasoning_effort=max 重新计算的结果。

输入文件：

- Medium 基线：`synth/sopmaze_answer_first_gemini_stage_kimi_canary_v1.jsonl`
- Max 成功结果：`synth/sopmaze_answer_first_kimi_max_redistill_sample_v1.jsonl`
- Max 失败记录：`synth/sopmaze_answer_first_kimi_max_redistill_sample_v1.failures.jsonl`

长度比较只使用 **87 个 medium 与 max 都有成功结果的同一 query 配对样本**。这样不会因为两组 query 不同而混淆长度差异。

## 2. Reasoning Content 长度分布

统一按 Python `len(reasoning_content)` 统计字符数。这个指标包含中文、英文、数字、标点和换行，不等同于 tokenizer token 数。

| 指标 | Medium | Max |
|---|---:|---:|
| 配对样本数 | 87 | 87 |
| 最小值 | 65 | 158 |
| P10 | 242 | 476 |
| P25 | 489 | 896 |
| 中位数 P50 | 952 | 2,116 |
| 平均值 | 1,627 | 3,613 |
| P75 | 2,157 | 4,687 |
| P90 | 3,842 | 9,186 |
| 最大值 | 8,956 | 20,846 |

按长度区间统计：

| Reasoning 字符数 | Medium | Max |
|---|---:|---:|
| 少于 500 | 24（27.6%） | 11（12.6%） |
| 500–999 | 21（24.1%） | 13（14.9%） |
| 1,000–1,999 | 19（21.8%） | 17（19.5%） |
| 2,000–3,999 | 15（17.2%） | 19（21.8%） |
| 4,000–7,999 | 6（6.9%） | 15（17.2%） |
| 至少 8,000 | 2（2.3%） | 12（13.8%） |

配对结果：

- 67/87（77.0%）的 query 上，max reasoning 比 medium 更长。
- 20/87（23.0%）的 query 上，max reasoning 反而更短。
- max reasoning 总字符量是 medium 的 **2.22 倍**。
- 逐 query 计算长度倍数后，其中位数是 **1.58 倍**。
- max 成功结果的 reasoning token 中位数为 691，P75 为 1,456，最大值为 6,640。

因此，max 会显著增加推理长度，但不是每一条都会增加。

## 3. 本次 Max 重蒸入库率

| 最终状态 | 数量 | 占 131 条比例 |
|---|---:|---:|
| 成功入库 | 87 | 66.4% |
| 非纯 JSON，严格解析失败 | 36 | 27.5% |
| JSON 可解析，但 Schema/required 验证失败 | 8 | 6.1% |
| 最终 API、超时或限流失败 | 0 | 0% |

原始端到端入库率为：

```plain text
87 / 131 = 66.4%
```

如果只考察能够解析为 JSON 的 95 条结果，则答案验证通过率为：

```plain text
87 / (87 + 8) = 91.6%
```

这两个比例回答的是不同问题：

- **66.4%** 表示按照当前严格解析和验证代码，最终有多少能直接进入训练集。
- **91.6%** 表示排除输出格式问题后，可解析答案中有多少通过 Schema 和 required 字段验证。

36 条非纯 JSON 不是 token 为 0，也不是没有调用 API。对应失败请求中有 86 次 HTTP 200，合计：

- `prompt_tokens = 361,994`
- `completion_tokens = 105,409`
- `total_tokens = 467,403`

供应商响应里的兼容字段 `input_tokens` 和 `output_tokens` 为 0，但真实用量记录在 `prompt_tokens` 和 `completion_tokens`。

## 4. Medium 原始生产入库率

现有 Medium 数据来自两个历史运行目录。按当前目录中所有带 `sample_number` 的样本统计：

| Medium 生产批次 | 成功入库 | 总样本 | 入库率 |
|---|---:|---:|---:|
| Kimi Input 批次 | 3,781 | 4,102 | 92.2% |
| Gemini Input、Kimi Answer 批次 | 11,864 | 15,720 | 75.5% |
| 两批合计 | 15,645 | 19,822 | 78.9% |

两批成功数合计比最终 SFT 多 1 条，是因为最终导出时对重复 query 做了去重；最终 SFT 有 15,644 条唯一 query。

Medium 的失败率受输入来源、历史脚本版本、验证方式和运行阶段影响，因此 78.9% 只能作为历史生产观测值，不能直接归因于 reasoning_effort=medium。

## 5. Medium 与 Max 入库率如何比较

存在两个可用但含义不同的比较口径。

### 5.1 本次抽样集口径

本次 131 条 medium 基线是从已经成功入库的 SFT 中抽出的，因此：

| 模式 | 入库数 | 分母 | 表面入库率 |
|---|---:|---:|---:|
| Medium | 131 | 131 | 100.0% |
| Max | 87 | 131 | 66.4% |

这里 medium 的 100% 是**抽样条件造成的**，不是 medium 模型从原始 query 开始运行的真实成功率。因此不能据此断言 max 的真实入库能力只有 medium 的 66.4%。

### 5.2 历史生产观测口径

若把 max 的 66.4% 与 medium 两批历史合计 78.9% 直接相比：

```plain text
66.4% / 78.9% = 0.84
```

即 max 当前端到端入库率约为 medium 历史观测值的 84%。但两者不是同一批 query、同一脚本和同一解析条件下的随机对照实验，这个比例只能用于工程容量估算，不能作为严谨的模型能力结论。

## 6. 结果解释

当前可以确认：

1. max 确实显著延长了 reasoning，字符总量约为 medium 的 2.22 倍。
2. 在 87 个成功配对样本中，60 条（69.0%）最终 Answer 与 medium 完全相同。
3. max 当前主要损失来自输出格式，而不是 API 未调用或 token 不足。
4. 对可解析的 max 答案，Schema/required 验证通过率为 91.6%。
5. 要严谨比较 medium 和 max 的真实入库率，应对同一批未过滤 query，分别独立运行 medium 和 max，并使用完全相同的解析器和验证器。

因此，下一轮全量分片重蒸应同时保存原始 final content、reasoning content、HTTP 状态和 token usage。即使解析失败，也不能丢弃原始返回，否则无法区分代码围栏、解释前缀、截断或真正无答案。
