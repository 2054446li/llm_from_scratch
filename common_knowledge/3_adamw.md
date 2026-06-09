# AdamW (Adam with Decoupled Weight Decay)

## 概述

AdamW 是 Adam 优化器的改进版本，将权重衰减（weight decay）从梯度更新中解耦出来，使正则化效果更加正确和有效。

## 算法步骤

给定学习率 $\eta$、权重衰减系数 $\lambda$、动量参数 $\beta_1, \beta_2$：

1. 计算梯度：$g_t = \nabla f(\theta_{t-1})$
2. 更新一阶矩估计：$m_t = \beta_1 m_{t-1} + (1-\beta_1) g_t$
3. 更新二阶矩估计：$v_t = \beta_2 v_{t-1} + (1-\beta_2) g_t^2$
4. 偏差修正：$\hat{m}_t = \frac{m_t}{1-\beta_1^t}$，$\hat{v}_t = \frac{v_t}{1-\beta_2^t}$
5. 参数更新：$\theta_t = \theta_{t-1} - \eta \left( \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon} + \lambda \theta_{t-1} \right)$

## Adam vs AdamW 的关键区别

**Adam + L2正则化：**
$$\theta_t = \theta_{t-1} - \eta \cdot \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}$$
其中梯度 $g_t$ 已包含 L2 项 $\lambda \theta_{t-1}$，导致权重衰减被自适应学习率缩放。

**AdamW（解耦权重衰减）：**
权重衰减直接作用于参数，不经过自适应学习率的缩放，正则化效果更纯粹。

## 大模型中的典型配置

| 参数 | 典型值 | 说明 |
|------|--------|------|
| β₁ | 0.9 | 一阶矩衰减率 |
| β₂ | 0.95 | 二阶矩衰减率（LLM常用，比默认0.999小） |
| weight_decay | 0.1 | 权重衰减系数 |
| ε | 1e-8 | 数值稳定性常数 |

## 为什么大模型偏好 β₂=0.95

- 默认 β₂=0.999 对二阶矩的记忆时间过长
- 大模型训练中数据分布变化快，较小的 β₂ 能更快适应梯度方差变化
- 有助于训练稳定性

## 参考文献

- Loshchilov, I., & Hutter, F. (2017). Decoupled Weight Decay Regularization.
