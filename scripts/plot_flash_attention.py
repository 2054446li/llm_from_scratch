"""
绘制 Flash Attention 工作原理图：
1. GPU 内存层次结构（HBM vs SRAM）
2. 标准注意力 vs Flash Attention 的内存访问对比
3. 分块计算（Tiling）过程示意
4. Online Softmax 算法流程

生成图片保存至 assets/flash_attention_explained.png

运行: python scripts/plot_flash_attention.py
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig = plt.figure(figsize=(16, 20))

# ============================================================
# 图1: GPU 内存层次结构
# ============================================================
ax1 = fig.add_subplot(4, 1, 1)
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 4)
ax1.axis('off')
ax1.set_title('1. GPU Memory Hierarchy (A100)', fontsize=14, fontweight='bold', pad=10)

# SRAM
sram_box = FancyBboxPatch((0.5, 2.5), 3, 1.2, boxstyle="round,pad=0.1",
                           facecolor='#FF6B6B', edgecolor='black', linewidth=2)
ax1.add_patch(sram_box)
ax1.text(2, 3.1, 'SRAM (On-chip)', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
ax1.text(2, 2.7, '~20MB | ~19 TB/s', ha='center', va='center', fontsize=10, color='white')

# HBM
hbm_box = FancyBboxPatch((0.5, 0.5), 3, 1.5, boxstyle="round,pad=0.1",
                          facecolor='#4ECDC4', edgecolor='black', linewidth=2)
ax1.add_patch(hbm_box)
ax1.text(2, 1.5, 'HBM (Off-chip)', ha='center', va='center', fontsize=12, fontweight='bold')
ax1.text(2, 1.0, '40-80 GB | ~2 TB/s', ha='center', va='center', fontsize=10)

# Arrow between
ax1.annotate('', xy=(2, 2.5), xytext=(2, 2.0),
            arrowprops=dict(arrowstyle='<->', color='black', lw=2))
ax1.text(2.8, 2.25, 'Bottleneck!\n(~10x slower)', ha='left', va='center', fontsize=10, color='red')

# 右侧说明
ax1.text(5.5, 3.5, 'Standard Attention:', fontsize=11, fontweight='bold')
ax1.text(5.5, 3.0, '• 计算 S = QK^T (N×N) → 写入 HBM', fontsize=10)
ax1.text(5.5, 2.5, '• 从 HBM 读取 S → 计算 softmax → 写入 HBM', fontsize=10)
ax1.text(5.5, 2.0, '• 从 HBM 读取 P → 计算 PV → 写入 HBM', fontsize=10)
ax1.text(5.5, 1.5, '• 总计: 3 次读写完整 N×N 矩阵', fontsize=10, color='red')

ax1.text(5.5, 0.8, 'Flash Attention:', fontsize=11, fontweight='bold')
ax1.text(5.5, 0.3, '• 分块加载到 SRAM → 计算 → 只写最终 O 到 HBM', fontsize=10, color='green')

# ============================================================
# 图2: 标准注意力 vs Flash Attention
# ============================================================
ax2 = fig.add_subplot(4, 1, 2)
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 4)
ax2.axis('off')
ax2.set_title('2. Standard Attention vs Flash Attention (Memory Access)', fontsize=14, fontweight='bold', pad=10)

# Standard Attention - 左边
ax2.text(2.5, 3.7, 'Standard Attention', ha='center', fontsize=12, fontweight='bold', color='red')

# Q, K 矩阵
for i, (label, x, y) in enumerate([('Q', 0.3, 2.5), ('K^T', 1.5, 2.5)]):
    rect = plt.Rectangle((x, y), 0.8, 1, facecolor='#FFE66D', edgecolor='black')
    ax2.add_patch(rect)
    ax2.text(x+0.4, y+0.5, label, ha='center', va='center', fontsize=10, fontweight='bold')

ax2.text(2.6, 3.0, '→', fontsize=16)

# S = QK^T (大矩阵)
rect_s = plt.Rectangle((2.9, 2.3), 1.4, 1.4, facecolor='#FF6B6B', edgecolor='black', alpha=0.7)
ax2.add_patch(rect_s)
ax2.text(3.6, 3.0, 'S\n(N×N)', ha='center', va='center', fontsize=10, fontweight='bold')
ax2.text(3.6, 2.1, '↕ HBM', ha='center', fontsize=8, color='red')

ax2.text(4.5, 3.0, '→ softmax →', fontsize=9, ha='center')

# Flash Attention - 右边
ax2.text(7.5, 3.7, 'Flash Attention', ha='center', fontsize=12, fontweight='bold', color='green')

# 分块的Q, K, V
colors_block = ['#A8E6CF', '#88D8A8', '#69C98E']
for i in range(3):
    rect = plt.Rectangle((5.8, 2.5 + i*0.35), 0.6, 0.3, facecolor=colors_block[i], edgecolor='black')
    ax2.add_patch(rect)
for i in range(3):
    rect = plt.Rectangle((6.6, 2.5 + i*0.35), 0.6, 0.3, facecolor=colors_block[i], edgecolor='black')
    ax2.add_patch(rect)

ax2.text(6.1, 2.3, 'Q blocks', ha='center', fontsize=8)
ax2.text(6.9, 2.3, 'K blocks', ha='center', fontsize=8)

# SRAM 计算
sram = FancyBboxPatch((7.5, 2.4), 1.8, 1.2, boxstyle="round,pad=0.05",
                       facecolor='#FF6B6B', edgecolor='black', linewidth=1.5, alpha=0.3)
ax2.add_patch(sram)
ax2.text(8.4, 3.2, 'SRAM', ha='center', fontsize=9, fontweight='bold')
ax2.text(8.4, 2.8, 'block × block\n→ local softmax\n→ accumulate O', ha='center', fontsize=8)

# 底部对比
ax2.text(2.5, 0.8, 'HBM 读写: O(N²d)', ha='center', fontsize=11, color='red', fontweight='bold')
ax2.text(2.5, 0.3, '显存: O(N²)', ha='center', fontsize=11, color='red')
ax2.text(7.5, 0.8, 'HBM 读写: O(N²d²/M)', ha='center', fontsize=11, color='green', fontweight='bold')
ax2.text(7.5, 0.3, '显存: O(N)', ha='center', fontsize=11, color='green')

# ============================================================
# 图3: Tiling 过程详细示意
# ============================================================
ax3 = fig.add_subplot(4, 1, 3)
ax3.set_xlim(0, 10)
ax3.set_ylim(0, 5)
ax3.axis('off')
ax3.set_title('3. Tiling Process (分块计算过程)', fontsize=14, fontweight='bold', pad=10)

# 画注意力矩阵分块
block_size = 0.6
n_blocks = 4
start_x, start_y = 0.5, 1.5

# 完整注意力矩阵
ax3.text(start_x + n_blocks*block_size/2, 4.5, 'Attention Matrix (N×N) 分块处理',
         ha='center', fontsize=11, fontweight='bold')

colors_matrix = plt.cm.Blues(np.linspace(0.2, 0.8, 4))
for i in range(n_blocks):
    for j in range(n_blocks):
        alpha = 0.3
        color = '#E0E0E0'
        if i == 1 and j == 2:  # 高亮当前块
            color = '#FF6B6B'
            alpha = 0.8
        rect = plt.Rectangle((start_x + j*block_size, start_y + (n_blocks-1-i)*block_size),
                             block_size, block_size, facecolor=color, edgecolor='black',
                             alpha=alpha, linewidth=0.5)
        ax3.add_patch(rect)

# 标注
ax3.text(start_x - 0.3, start_y + n_blocks*block_size/2, 'Q\nblocks', ha='center', va='center', fontsize=9)
ax3.text(start_x + n_blocks*block_size/2, start_y + n_blocks*block_size + 0.2, 'K blocks',
         ha='center', fontsize=9)
ax3.text(start_x + 2*block_size + block_size/2, start_y + 2*block_size + block_size/2,
         'current\nblock', ha='center', va='center', fontsize=7, color='white', fontweight='bold')

# 右侧：算法步骤
step_x = 4.0
ax3.text(step_x, 4.5, 'Algorithm (外循环: Q blocks, 内循环: K,V blocks):', fontsize=10, fontweight='bold')

steps = [
    'for i = 1 to ⌈N/Br⌉:                    # 外循环遍历 Q 的块',
    '    Load Q_i from HBM to SRAM',
    '    for j = 1 to ⌈N/Bc⌉:                # 内循环遍历 K,V 的块',
    '        Load K_j, V_j from HBM to SRAM',
    '        S_ij = Q_i × K_j^T              # 在 SRAM 中计算',
    '        m_new = max(m_old, rowmax(S_ij)) # 更新最大值',
    '        P_ij = exp(S_ij - m_new)        # 局部 softmax',
    '        l_new = exp(m_old-m_new)×l_old + rowsum(P_ij)',
    '        O_i = rescale(O_i) + P_ij × V_j # 累积输出',
    '    Write O_i to HBM                     # 只写最终结果',
]

for idx, step in enumerate(steps):
    color = 'black'
    if 'Load' in step:
        color = '#4ECDC4'
    elif 'Write' in step:
        color = '#FF6B6B'
    elif 'SRAM' in step or 'softmax' in step or 'rescale' in step:
        color = '#2D5B9E'
    ax3.text(step_x, 3.8 - idx*0.38, step, fontsize=8.5, fontfamily='monospace', color=color)

# ============================================================
# 图4: Online Softmax 原理
# ============================================================
ax4 = fig.add_subplot(4, 1, 4)
ax4.set_xlim(0, 10)
ax4.set_ylim(0, 5)
ax4.axis('off')
ax4.set_title('4. Online Softmax Trick (在线 Softmax 核心技巧)', fontsize=14, fontweight='bold', pad=10)

# 标准 softmax
ax4.text(0.3, 4.5, 'Standard Softmax (需要完整行):', fontsize=10, fontweight='bold', color='red')
ax4.text(0.3, 4.0, r'softmax(x_i) = exp(x_i - max(x)) / Σ exp(x_j - max(x))', fontsize=10, fontfamily='monospace')
ax4.text(0.3, 3.5, '问题: 必须先看到整行所有值才能计算 max 和 Σ', fontsize=10, color='red')

# Online softmax
ax4.text(0.3, 2.8, 'Online Softmax (逐块更新):', fontsize=10, fontweight='bold', color='green')

online_steps = [
    '处理第 j 个块时，维护两个统计量:',
    '  m = 当前已见所有块的最大值 (running max)',
    '  l = 当前已见所有块的 exp 之和 (running sum)',
    '',
    '当新块 S_new 到来:',
    '  m_new = max(m_old, max(S_new))           # 更新全局最大值',
    '  l_new = l_old × exp(m_old - m_new)       # 修正旧的 sum',
    '         + sum(exp(S_new - m_new))          # 加上新块的贡献',
    '  O_new = O_old × (l_old/l_new)×exp(m_old - m_new)  # 修正旧输出',
    '         + (1/l_new) × exp(S_new - m_new) × V_new   # 加新贡献',
]

for idx, step in enumerate(online_steps):
    color = 'black'
    if 'm_new' in step or 'l_new' in step or 'O_new' in step:
        color = '#2D5B9E'
    ax4.text(0.5, 2.3 - idx*0.28, step, fontsize=9, fontfamily='monospace', color=color)

# 关键洞察
ax4.text(6.5, 4.5, '关键洞察:', fontsize=10, fontweight='bold')
insight_text = [
    '• 当新块最大值更大时，旧结果需要',
    '  乘以 exp(m_old - m_new) < 1 缩小',
    '• 这个修正是精确的，不是近似!',
    '• 最终结果与标准 softmax 完全一致',
    '',
    '为什么可以这样做:',
    '  exp(x-m_old)/l_old',
    '  = exp(x-m_old)×exp(m_old-m_new) / (l_old×exp(m_old-m_new))',
    '  = exp(x-m_new) / l_new_partial',
]
for idx, text in enumerate(insight_text):
    ax4.text(6.5, 4.0 - idx*0.3, text, fontsize=9, fontfamily='monospace')

plt.tight_layout()
plt.savefig('assets/flash_attention_explained.png', dpi=150, bbox_inches='tight')
print("图片已保存至 assets/flash_attention_explained.png")
