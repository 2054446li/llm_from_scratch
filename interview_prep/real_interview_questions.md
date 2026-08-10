# 真实面试问题记录

> 用于记录实际面试中遇到的问题、完整回答与可继续追问的知识点。

## 第一题：为什么逻辑回归的损失函数不能使用线性回归替代？

### 回答

首先需要区分两个概念：

- **线性回归**通常使用 MSE（Mean Squared Error，均方误差）作为损失；
- **逻辑回归**通常使用 BCE（Binary Cross Entropy，二元交叉熵）作为损失。

因此，这个问题更准确地说是：

> **为什么逻辑回归通常不使用线性回归中的 MSE，而使用 BCE？**

原因主要有三个：**输出的概率含义、概率分布假设，以及优化性质**。

### 1. 二分类需要概率，而普通线性回归输出不满足概率约束

线性回归直接预测：

$$
z = w^T x + b
$$

其输出范围为：

$$
z \in (-\infty, +\infty)
$$

因此可能出现 $z=-0.5$ 或 $z=1.7$，这些值不能直接解释为概率。

逻辑回归在最后加入 Sigmoid：

$$
p = \sigma(z) = \frac{1}{1 + e^{-z}}
$$

使得 $p \in (0,1)$，并将其解释为：

$$
p = P(y=1 \mid x), \qquad P(y=0 \mid x)=1-p
$$

所以逻辑回归是在建模 $P(y=1 \mid x)$，而不是直接预测一个无约束的连续数值。

### 2. BCE 来自 Bernoulli 分布

由于 $y \in \{0,1\}$，对于一个样本，可以将两种情况统一写成：

$$
P(y \mid x) = p^y (1-p)^{1-y}
$$

当 $y=1$ 时，$P(y \mid x)=p$；当 $y=0$ 时，$P(y \mid x)=1-p$。这个式子表示模型给真实标签分配了多大的概率，正是 Bernoulli 分布的概率质量函数：

$$
Y \mid X=x \sim \operatorname{Bernoulli}(p),
\qquad p = \sigma(w^T x+b)
$$

### 3. 从最大似然估计推导 BCE

假设训练集有 $N$ 个独立样本：

$$
D = \{(x_i,y_i)\}_{i=1}^{N}
$$

对于第 $i$ 个样本：

$$
P(y_i \mid x_i)=p_i^{y_i}(1-p_i)^{1-y_i}
$$

假设样本之间独立，则整个数据集的似然函数为：

$$
L(w,b)=\prod_{i=1}^{N}p_i^{y_i}(1-p_i)^{1-y_i}
$$

最大似然估计的目标是：

$$
\max_{w,b} L(w,b)
$$

即找到一组参数 $w,b$，使实际观察到的这些标签出现的概率最大。为了方便优化，对似然函数取对数：

$$
\log L
=
\sum_{i=1}^{N}
\left[
y_i \log p_i+(1-y_i)\log(1-p_i)
\right]
$$

机器学习中通常写成最小化问题，因此：

$$
\max \log L \iff \min (-\log L)
$$

取平均后得到：

$$
\mathcal{L}_{\text{BCE}}
=
-\frac{1}{N}
\sum_{i=1}^{N}
\left[
y_i \log p_i+(1-y_i)\log(1-p_i)
\right]
$$

推导过程可以概括为：

$$
\text{Bernoulli Distribution}
\rightarrow
\text{Maximum Likelihood}
\rightarrow
\text{Log-Likelihood}
\rightarrow
\text{Negative Log-Likelihood}
\rightarrow
\text{BCE}
$$

因此，BCE 不是人为随意选择的，而是从逻辑回归的概率模型和最大似然估计自然推导出来的。

### 4. Sigmoid + MSE 能不能使用？

实际上，**可以使用，但通常优化效果不好**。

假设 $p=\sigma(z)$，使用 MSE：

$$
\mathcal{L}_{\text{MSE}}=(y-p)^2
$$

对 $z$ 求导：

$$
\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial z}
=
\frac{\partial \mathcal{L}}{\partial p}
\frac{\partial p}{\partial z}
$$

由于：

$$
\frac{\partial \mathcal{L}}{\partial p}=2(p-y),
\qquad
\frac{\partial p}{\partial z}=p(1-p)
$$

因此：

$$
\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial z}
=2(p-y)p(1-p)
$$

这里多出了 $p(1-p)$。当 Sigmoid 进入饱和区时，这一项会非常小。

例如真实标签为 $y=1$，但模型非常自信地预测 $p=0.001$，那么：

$$
p(1-p)=0.001 \times 0.999 \approx 0.001
$$

因此：

$$
\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial z}
=2(0.001-1)(0.001)(0.999)
\approx -0.002
$$

模型明明错得非常严重，但梯度却非常小。也就是说，使用 Sigmoid + MSE 时，模型在非常自信地预测错误时，反而可能很难被纠正。

### 5. BCE 为什么没有这个问题？

对于单个样本，BCE 为：

$$
\mathcal{L}
=-left[y\log p+(1-y)\log(1-p)\right]
$$

并且 $p=\sigma(z)$。首先对 $p$ 求导：

$$
\frac{\partial \mathcal{L}}{\partial p}
=-\frac{y}{p}+\frac{1-y}{1-p}
=\frac{p-y}{p(1-p)}
$$

而：

$$
\frac{\partial p}{\partial z}=p(1-p)
$$

根据链式法则：

$$
\frac{\partial \mathcal{L}}{\partial z}
=
\frac{p-y}{p(1-p)}\cdot p(1-p)
$$

最终：

$$
\boxed{
\frac{\partial \mathcal{L}}{\partial z}=p-y
}
$$

Sigmoid 导数中的 $p(1-p)$ 正好被抵消。仍然考虑 $y=1$、$p=0.001$：

$$
\frac{\partial \mathcal{L}}{\partial z}=0.001-1=-0.999
$$

如果模型非常自信地预测错了，BCE 会给予很强的纠正信号。相比之下：

$$
\left|
\frac{\partial \mathcal{L}_{\text{BCE}}}{\partial z}
\right| \approx 0.999,
\qquad
\left|
\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial z}
\right| \approx 0.002
$$

二者相差约 $500$ 倍。

### 6. 更本质的区别：两种损失对应不同的概率模型

线性回归通常假设：

$$
y=w^T x+b+\epsilon,
\qquad
\epsilon \sim \mathcal{N}(0,\sigma^2)
$$

因此：

$$
Y \mid X \sim \mathcal{N}(w^T x+b,\sigma^2)
$$

即使用 Gaussian 分布建模。对 Gaussian 分布进行最大似然估计，最终可以推导出 MSE：

$$
\text{Gaussian}
\xrightarrow{\text{MLE}}
\text{MSE}
$$

逻辑回归处理的是二分类问题：

$$
Y \mid X=x \sim \operatorname{Bernoulli}(p),
\qquad
p=\sigma(w^T x+b)
$$

对 Bernoulli 分布进行最大似然估计，则得到 BCE：

$$
\text{Bernoulli}
\xrightarrow{\text{MLE}}
\text{BCE}
$$

### 总结

逻辑回归并不是**绝对不能**使用 MSE，而是 BCE 更符合逻辑回归问题本身的概率模型。逻辑回归假设：

$$
Y \mid X=x \sim \operatorname{Bernoulli}(p),
\qquad
p=\sigma(w^T x+b)
$$

基于 Bernoulli 分布进行最大似然估计，可以自然得到：

$$
\mathcal{L}_{\text{BCE}}
=-left[y\log p+(1-y)\log(1-p)\right]
$$

同时，BCE 与 Sigmoid 结合后具有简洁的梯度：

$$
\boxed{
\frac{\partial \mathcal{L}}{\partial z}=p-y
}
$$

而使用 MSE 时：

$$
\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial z}
=2(p-y)p(1-p)
$$

会额外受到 Sigmoid 饱和项 $p(1-p)$ 的影响，导致模型在“非常自信但预测错误”时梯度过小。因此，逻辑回归选择 BCE 而不是 MSE 的核心原因可以概括为：

$$
\boxed{
\text{概率模型匹配}
+
\text{最大似然解释}
+
\text{更好的梯度性质}
}
$$
