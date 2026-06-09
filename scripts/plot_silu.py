"""
绘制 SiLU (Swish) 函数及其导数，与 ReLU / GELU 对比。
生成图片保存至 assets/silu_curve.png

运行: python scripts/plot_silu.py
"""

import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.size'] = 11
plt.rcParams['axes.unicode_minus'] = False

x = np.linspace(-5, 5, 500)

# 激活函数
sigmoid = 1 / (1 + np.exp(-x))
silu = x * sigmoid
relu = np.maximum(0, x)
gelu = x * 0.5 * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

# 导数
silu_grad = sigmoid * (1 + x * (1 - sigmoid))
relu_grad = (x > 0).astype(float)
gelu_grad = np.gradient(gelu, x)

fig, axes = plt.subplots(2, 2, figsize=(12, 9))

# 左上: SiLU 函数
ax = axes[0, 0]
ax.plot(x, silu, 'b-', linewidth=2.5, label='SiLU(x)')
ax.plot(x, x, 'k--', alpha=0.3, label='y = x')
ax.axhline(0, color='gray', linewidth=0.5)
ax.axvline(0, color='gray', linewidth=0.5)
ax.scatter([-1.28], [-0.278], color='red', s=50, zorder=5, label='min ≈ (-1.28, -0.278)')
ax.set_title('SiLU (Swish) Function', fontweight='bold')
ax.set_xlabel('x')
ax.set_ylabel('SiLU(x)')
ax.legend(loc='upper left')
ax.set_xlim(-5, 5)
ax.set_ylim(-1, 4)
ax.grid(True, alpha=0.3)

# 右上: SiLU 导数
ax = axes[0, 1]
ax.plot(x, silu_grad, 'r-', linewidth=2.5, label="SiLU'(x)")
ax.axhline(0, color='gray', linewidth=0.5)
ax.axhline(1, color='gray', linewidth=0.5, linestyle='--', alpha=0.5)
ax.axvline(0, color='gray', linewidth=0.5)
ax.scatter([0], [0.5], color='blue', s=50, zorder=5, label="SiLU'(0) = 0.5")
ax.set_title("SiLU' (Derivative)", fontweight='bold')
ax.set_xlabel('x')
ax.set_ylabel("SiLU'(x)")
ax.legend(loc='upper left')
ax.set_xlim(-5, 5)
ax.set_ylim(-0.2, 1.2)
ax.grid(True, alpha=0.3)

# 左下: 三种激活函数对比
ax = axes[1, 0]
ax.plot(x, relu, 'g-', linewidth=2, label='ReLU', alpha=0.8)
ax.plot(x, gelu, 'm-', linewidth=2, label='GELU', alpha=0.8)
ax.plot(x, silu, 'b-', linewidth=2.5, label='SiLU')
ax.axhline(0, color='gray', linewidth=0.5)
ax.axvline(0, color='gray', linewidth=0.5)
ax.set_title('Activation Functions Comparison', fontweight='bold')
ax.set_xlabel('x')
ax.set_ylabel('f(x)')
ax.legend(loc='upper left')
ax.set_xlim(-5, 5)
ax.set_ylim(-1, 4)
ax.grid(True, alpha=0.3)

# 右下: 三种导数对比
ax = axes[1, 1]
ax.plot(x, relu_grad, 'g-', linewidth=2, label="ReLU'", alpha=0.8)
ax.plot(x, gelu_grad, 'm-', linewidth=2, label="GELU'", alpha=0.8)
ax.plot(x, silu_grad, 'r-', linewidth=2.5, label="SiLU'")
ax.axhline(0, color='gray', linewidth=0.5)
ax.axhline(1, color='gray', linewidth=0.5, linestyle='--', alpha=0.3)
ax.axvline(0, color='gray', linewidth=0.5)
ax.set_title("Derivatives Comparison", fontweight='bold')
ax.set_xlabel('x')
ax.set_ylabel("f'(x)")
ax.legend(loc='upper left')
ax.set_xlim(-5, 5)
ax.set_ylim(-0.3, 1.3)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('assets/silu_curve.png', dpi=150, bbox_inches='tight')
print("图片已保存至 assets/silu_curve.png")
