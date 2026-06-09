# 混合专家架构(Mixture-of-Experts, MoE)

> MoE 的基础概念(多专家 + 路由、稀疏激活)略。本笔记只记真正有信息量的部分:**怎么对比、有什么优势、哪些是定论。**

## 核心:MoE 该和谁比

MoE 把**总参数**(决定容量/显存)和**激活参数**(决定算力/速度)解耦。所以对比时**看的是激活参数**:

> 一个总参数 16B、激活 2.8B 的 MoE,常拿来和 **2.8B~7B 量级的 Dense 模型**(即激活参数相近者)对比。

**优势(一句话)**:达到相同性能,MoE 的**激活参数更少**,而**计算量(FLOPs)与激活参数相近的 Dense 持平或略高**——因为算力由激活参数决定,不由总参数决定。即"用小模型的算力,拿到更强的性能"。

## 性能落在什么范围(关键定论)

16B/激活2.8B 的 MoE,性能**介于 7B Dense 和 16B Dense 之间**:

| 对比对象 | 结果 | 说明 |
|---|---|---|
| **同激活量 Dense(~7B)** | MoE **更强** | 多出的总参数=额外容量,真实有效;算力却差不多 → MoE 的主场 |
| **同总参数 Dense(16B)** | MoE **够不到** | Dense 全参数参与运算,是 MoE 的**性能上界** |

依据:DeepMind《Unified Scaling Laws for Routed LMs》(Clark et al., 2022)——MoE 的"等效 Dense 规模"是激活参数与总参数之间的中间值,偏向激活参数那端。

## 实例(DeepSeekMoE,论文实测)

- 16B(激活 2.8B):仅约 **40% 计算量**,性能 ≈ LLaMA2 7B(激活参数约其 2.5 倍)。
- 145B:约 **28.5%(甚至 18.2%)计算量**,性能 ≈ DeepSeek 67B。

## 代价(为什么不是免费午餐)

- **显存按总参数算**:16B 全部加载,省的是算力不是显存。
- **训练显存/通信更贵**:全专家的梯度+优化器状态都要存;多卡专家间 all-to-all 通信。
- **负载不均衡**:需额外 balance loss。

## 一个易混点:Dense Model / Dense MoE / Sparse MoE

| | Dense Model(稠密模型) | Dense MoE(稠密混合专家) | Sparse MoE(稀疏混合专家) |
|---|---|---|---|
| 有没有专家? | ❌ 无,FFN 一整块 | ✅ 有 N 个专家 | ✅ 有 N 个专家 |
| 每 token 激活几个? | —(不适用) | **全部 N 个** | **只 top-K 个**(K≪N) |
| 路由器作用 | ❌ 无 | ✅ 仅决定**权重**,不筛选 | ✅ **选择**哪些专家参与 |
| 激活参数 vs 总参数 | 相等 | **相等**(全激活) | **远小于**(稀疏激活) |
| 计算量 | 标准 | **比 Dense 还高**(N 个全算) | **低**(只算 K 个) |
| 典型代表 | LLaMA、GPT | 少见,多用于研究/对照 | Mixtral、DeepSeekMoE、Switch |

- 平时说的 "MoE" **99% 指 Sparse MoE**;Dense MoE 算力比普通 Dense 还高,几乎不部署,仅作上界参考。
- DeepSeekMoE 论文里的 "dense counterpart" 指 **Dense Model**,不是 Dense MoE。

## 参考文献

- Dai et al., 2024. *DeepSeekMoE.*
- Clark et al., 2022. *Unified Scaling Laws for Routed Language Models.*
