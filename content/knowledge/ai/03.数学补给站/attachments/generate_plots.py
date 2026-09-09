"""
生成 AI 学习数学笔记所需的函数曲线图
运行: cd 03.数学补给站/attachments && python generate_plots.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 全局设置
# ============================================================
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'Noto Sans SC', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'figure.dpi': 150,
    'figure.facecolor': 'white',
    'axes.facecolor': '#f8f9fa',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.spines.top': False,
    'axes.spines.right': False,
})


def savefig(name):
    path = os.path.join(OUTPUT_DIR, name)
    plt.savefig(path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  [OK] {name}")


# ============================================================
# 1. 激活函数对比: ReLU / Sigmoid / Tanh / GELU
# ============================================================
def plot_activation_functions():
    x = np.linspace(-5, 5, 500)
    relu = np.maximum(0, x)
    sigmoid = 1 / (1 + np.exp(-x))
    tanh = np.tanh(x)
    # 近似 GELU
    gelu = 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, relu, 'b-', linewidth=2.5, label='ReLU\nf(x)=max(0,x)')
    ax.plot(x, sigmoid, 'g-', linewidth=2.5, label='Sigmoid\nσ(x)=1/(1+e⁻ˣ)')
    ax.plot(x, tanh, 'orange', linewidth=2.5, label='Tanh\ntanh(x)')
    ax.plot(x, gelu, 'r-', linewidth=2.5, alpha=0.8, label='GELU\nx·Φ(x) (LLM 标配)')

    ax.axhline(y=0, color='gray', linewidth=0.8)
    ax.axvline(x=0, color='gray', linewidth=0.8)
    ax.set_xlim(-5, 5)
    ax.set_ylim(-1.5, 5)
    ax.set_xlabel('x')
    ax.set_ylabel('f(x)')
    ax.set_title('常见激活函数对比', fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, loc='upper left', framealpha=0.9)

    # 标注关键区域
    ax.annotate('ReLU: x<0 时梯度为 0', xy=(-2, 0.5), fontsize=8, color='b',
                ha='center')
    ax.annotate('GELU: 允许少量负值通过\n→ 梯度不消失', xy=(-3, -0.3), fontsize=8, color='r',
                ha='center')

    savefig('activation_functions.png')


# ============================================================
# 2. 激活函数导数对比
# ============================================================
def plot_activation_derivatives():
    x = np.linspace(-5, 5, 500)
    eps = 1e-7

    # ReLU 导数
    relu_deriv = np.where(x > 0, 1.0, 0.0)
    # Sigmoid 导数: σ(1-σ)
    sig = 1 / (1 + np.exp(-x))
    sigmoid_deriv = sig * (1 - sig)
    # Tanh 导数: 1 - tanh²
    th = np.tanh(x)
    tanh_deriv = 1 - th**2
    # GELU 近似导数
    sqrt_2pi = np.sqrt(2 / np.pi)
    gelu_approx = 0.5 * (1 + np.tanh(sqrt_2pi * (x + 0.044715 * x**3)))
    gelu_deriv = gelu_approx  # 近似

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, relu_deriv, 'b-', linewidth=2.5, label="ReLU'")
    ax.plot(x, sigmoid_deriv, 'g-', linewidth=2.5, label="Sigmoid' = σ(1-σ)")
    ax.plot(x, tanh_deriv, 'orange', linewidth=2.5, label="Tanh' = 1-tanh²(x)")
    ax.plot(x, gelu_deriv, 'r--', linewidth=2, alpha=0.7, label="GELU' (近似)")

    ax.axhline(y=0, color='gray', linewidth=0.8)
    ax.axvline(x=0, color='gray', linewidth=0.8)
    ax.set_xlim(-5, 5)
    ax.set_ylim(-0.1, 1.2)
    ax.set_xlabel('x')
    ax.set_ylabel("f'(x)")
    ax.set_title('激活函数导数对比 —— 梯度消失问题的根源', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='upper left', framealpha=0.9)

    ax.annotate('Sigmoid: 两端梯度 → 0\n→ 深层网络学不动', xy=(4, 0.15), fontsize=8, ha='center', color='g')
    ax.annotate('ReLU: x>0 梯度恒为 1\n→ 缓解梯度消失', xy=(2.5, 0.85), fontsize=8, ha='center', color='b')

    savefig('activation_derivatives.png')


# ============================================================
# 3. 正态分布曲线 (不同 μ, σ 的钟形曲线)
# ============================================================
def plot_normal_distribution():
    x = np.linspace(-8, 12, 500)

    distributions = [
        (0, 0.5, 'b-', 'N(0, 0.5) 窄而尖'),
        (0, 1.0, 'g-', 'N(0, 1.0) 标准正态'),
        (0, 2.0, 'orange', 'N(0, 2.0) 宽而扁'),
        (3, 1.0, 'r-', 'N(3, 1.0) 中心偏移'),
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    for mu, sigma, color, label in distributions:
        y = (1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
        ax.plot(x, y, color, linewidth=2.5, label=label)

    # 68-95-99.7 规则标注
    std_x = np.linspace(-1, 1, 200)
    std_y = (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * std_x ** 2)
    ax.fill_between(std_x, std_y, alpha=0.2, color='g', label='μ±σ: ~68%')
    ax.fill_between(np.linspace(-2, 2, 200),
                    (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * np.linspace(-2, 2, 200) ** 2),
                    alpha=0.1, color='g', label='μ±2σ: ~95%')

    ax.set_xlim(-6, 10)
    ax.set_ylim(0, 0.85)
    ax.set_xlabel('x')
    ax.set_ylabel('概率密度 f(x)')
    ax.set_title('正态分布 —— 不同参数的影响', fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, framealpha=0.9)

    savefig('normal_distribution.png')


# ============================================================
# 4. 熵的对比: 均匀分布 vs 集中分布
# ============================================================
def plot_entropy_comparison():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    categories = ['类别 A', '类别 B', '类别 C', '类别 D']
    x_pos = np.arange(len(categories))

    # 高熵：均匀分布
    uniform = np.array([0.25, 0.25, 0.25, 0.25])
    h_uniform = -np.sum(uniform * np.log2(uniform + 1e-10))

    # 低熵：集中分布
    concentrated = np.array([0.85, 0.08, 0.05, 0.02])
    h_concentrated = -np.sum(concentrated * np.log2(concentrated + 1e-10))

    colors_uniform = ['#6bcb77'] * 4
    colors_conc = ['#ff6b6b' if i == 0 else '#ffd93d' for i in range(4)]

    axes[0].bar(x_pos, uniform, color=colors_uniform, width=0.5, edgecolor='white', linewidth=1.5)
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(categories)
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel('概率 P')
    axes[0].set_title(f'高熵: 均匀分布\nH = {h_uniform:.2f} bits', fontsize=12, fontweight='bold')
    for i, v in enumerate(uniform):
        axes[0].text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=11)

    axes[1].bar(x_pos, concentrated, color=colors_conc, width=0.5, edgecolor='white', linewidth=1.5)
    axes[1].set_xticks(x_pos)
    axes[1].set_xticklabels(categories)
    axes[1].set_ylim(0, 1)
    axes[1].set_ylabel('概率 P')
    axes[1].set_title(f'低熵: 概率集中在「类别 A」\nH = {h_concentrated:.2f} bits', fontsize=12, fontweight='bold')
    for i, v in enumerate(concentrated):
        axes[1].text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=11)

    plt.suptitle('熵 H(P) = -∑P(x)log₂P(x) —— 不确定性度量', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    savefig('entropy_comparison.png')


# ============================================================
# 5. 梯度下降路径: 2D等高线 + 优化路径
# ============================================================
def plot_gradient_descent():
    # 构建一个简单的 Loss 曲面: f(x,y) = x² + 2y² (椭圆抛物面)
    x = np.linspace(-3, 3, 100)
    y = np.linspace(-3, 3, 100)
    X, Y = np.meshgrid(x, y)
    Z = X**2 + 2 * Y**2

    # 模拟梯度下降路径（从 (2.5, 2.5) 开始）
    def gradient(x, y):
        return 2*x, 4*y

    lr = 0.1
    n_steps = 30
    path_x, path_y = [2.5], [2.5]
    for _ in range(n_steps):
        gx, gy = gradient(path_x[-1], path_y[-1])
        new_x = path_x[-1] - lr * gx
        new_y = path_y[-1] - lr * gy
        path_x.append(new_x)
        path_y.append(new_y)

    path_z = np.array(path_x)**2 + 2 * np.array(path_y)**2

    fig, ax = plt.subplots(figsize=(8, 7))
    contours = ax.contour(X, Y, Z, levels=20, cmap='viridis', linewidths=0.8, alpha=0.7)
    ax.clabel(contours, inline=True, fontsize=8, fmt='%.1f')

    # 绘制路径
    colors = plt.cm.hot(np.linspace(0.2, 1, len(path_x)))
    for i in range(len(path_x) - 1):
        ax.plot(path_x[i:i+2], path_y[i:i+2], 'r-', linewidth=2, alpha=0.6)
    ax.scatter(path_x, path_y, c=range(len(path_x)), cmap='hot', s=20, zorder=5, alpha=0.8)

    # 起点和终点
    ax.scatter([path_x[0]], [path_y[0]], c='red', marker='s', s=100, zorder=10, label='起点', edgecolors='white')
    ax.scatter([path_x[-1]], [path_y[-1]], c='green', marker='*', s=200, zorder=10, label='终点 (最优解)', edgecolors='white')

    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_xlabel('参数 θ₁')
    ax.set_ylabel('参数 θ₂')
    ax.set_title('梯度下降路径可视化\nLoss 等高线 + 优化轨迹', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.set_aspect('equal')

    # 添加标注
    ax.annotate('每步沿梯度反方向\n等高线最陡处下降', xy=(path_x[5], path_y[5]),
                xytext=(0, 1.5), fontsize=9, ha='center',
                arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

    savefig('gradient_descent.png')


# ============================================================
# 6. 学习率对比: 不同 LR 的收敛曲线
# ============================================================
def plot_learning_rate_comparison():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    # 模拟不同学习率下优化 Rosenbrock 风格的 1D 函数
    def loss_fn(x):
        return x**2 + 0.1 * np.sin(3 * x) + 0.5

    def gradient(x):
        return 2 * x + 0.3 * np.cos(3 * x)

    scenarios = [
        (0.01, '学习率太小 (α=0.01)', 'b-', [1.8]),
        (0.3, '学习率合适 (α=0.3)', 'g-', [1.8]),
        (1.5, '学习率太大 (α=1.5)', 'r-', [1.8]),
    ]

    for idx, (lr, title, color, start) in enumerate(scenarios):
        ax = axes[idx]
        x_vals = np.linspace(-2, 2, 300)
        y_vals = loss_fn(x_vals)
        ax.plot(x_vals, y_vals, 'gray', linewidth=1.5, alpha=0.5, label='Loss 曲线')

        # 模拟训练
        x = start[0]
        xs, ys = [], []
        for step in range(50):
            xs.append(x)
            ys.append(loss_fn(x))
            grad = gradient(x)
            x = x - lr * grad

        ax.plot(xs, ys, color, linewidth=2, marker='o', markersize=3, label='优化轨迹')
        ax.scatter([xs[0]], [ys[0]], c='orange', s=50, zorder=5, label='起点')
        ax.scatter([xs[-1]], [ys[-1]], c='red', s=80, zorder=5, label='终点')

        ax.set_xlim(-2.2, 2.2)
        ax.set_ylim(min(y_vals)-0.2, max(y_vals)+0.2)
        ax.set_xlabel('参数 θ')
        ax.set_ylabel('Loss')
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.legend(fontsize=7, loc='upper right')
        ax.text(0.02, 0.95, f'终值: {loss_fn(x):.4f}', transform=ax.transAxes,
                fontsize=9, verticalalignment='top', color='red')

    plt.suptitle('学习率对训练的影响 —— 最重要的超参数', fontsize=14, fontweight='bold')
    plt.tight_layout()
    savefig('learning_rate_comparison.png')


# ============================================================
# 7. L1 vs L2 正则化: 几何约束 + 等高线
# ============================================================
def plot_l1_l2_regularization():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Loss 等高线: 偏离原点的椭圆
    theta = np.linspace(0, 2 * np.pi, 100)
    x = np.linspace(-3, 3, 200)
    y = np.linspace(-3, 3, 200)
    X, Y = np.meshgrid(x, y)
    # 椭圆 Loss 曲面: 最优解在 (2, 0.5)
    Z = 0.5 * (X - 2)**2 + 2 * (Y - 0.5)**2

    for idx, (ax, reg_type) in enumerate(zip(axes, ['L2', 'L1'])):
        # Loss 等高线
        contours = ax.contour(X, Y, Z, levels=15, cmap='viridis', linewidths=0.8, alpha=0.6)

        # 约束区域
        if reg_type == 'L2':
            # 圆形约束
            theta_c = np.linspace(0, 2 * np.pi, 100)
            cx, cy = np.cos(theta_c), np.sin(theta_c)
            ax.fill(cx, cy, alpha=0.2, color='steelblue', label='L2 约束: w₁²+w₂² ≤ 1')
            ax.plot(cx, cy, 'b-', linewidth=2)
        else:
            # 菱形约束
            diamond_x = [0, 1, 0, -1, 0]
            diamond_y = [1, 0, -1, 0, 1]
            ax.fill(diamond_x, diamond_y, alpha=0.2, color='coral', label='L1 约束: |w₁|+|w₂| ≤ 1')
            ax.plot(diamond_x, diamond_y, 'r-', linewidth=2)

        # 找到等高线与约束区域的切点
        if reg_type == 'L2':
            opt_x, opt_y = 1.0, 0.25  # 近似切点 (圆形)
            ax.scatter([opt_x], [opt_y], c='red', s=120, zorder=10, marker='*', edgecolors='white')
            ax.annotate('最优解: 各权重\n缩小但不为 0', (opt_x, opt_y),
                       xytext=(1.8, 0.8), fontsize=9, ha='center',
                       arrowprops=dict(arrowstyle='->', color='darkblue', lw=1.5))
        else:
            opt_x, opt_y = 0.8, 0.0  # 近似切点 (菱形尖角)
            ax.scatter([opt_x], [opt_y], c='red', s=120, zorder=10, marker='*', edgecolors='white')
            ax.annotate('最优解在尖角!\nw₂=0 → 自动特征选择', (opt_x, opt_y),
                       xytext=(1.5, -1.2), fontsize=9, ha='center',
                       arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))

        ax.set_xlim(-3, 3)
        ax.set_ylim(-3, 3)
        ax.set_xlabel('w₁')
        ax.set_ylabel('w₂')
        ax.set_title(f'{reg_type} 正则化几何解释', fontsize=13, fontweight='bold')
        ax.legend(fontsize=9, loc='upper right')
        ax.set_aspect('equal')
        ax.axhline(y=0, color='gray', linewidth=0.5)
        ax.axvline(x=0, color='gray', linewidth=0.5)

    title_note = (
        'L1 (Lasso): 菱形尖角 → 稀疏解（部分权重=0）\n'
        'L2 (Ridge): 圆形边界 → 权重均匀缩小'
    )
    plt.suptitle('L1 vs L2 正则化: 为什么 L1 产生稀疏解？', fontsize=14, fontweight='bold')
    fig.text(0.5, -0.02, title_note, ha='center', fontsize=11,
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.8))
    plt.tight_layout()
    savefig('l1_l2_regularization.png')


# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    print("正在生成数学函数曲线图...\n")

    print("1/7 激活函数对比...")
    plot_activation_functions()

    print("2/7 激活函数导数对比...")
    plot_activation_derivatives()

    print("3/7 正态分布曲线...")
    plot_normal_distribution()

    print("4/7 熵的对比...")
    plot_entropy_comparison()

    print("5/7 梯度下降路径...")
    plot_gradient_descent()

    print("6/7 学习率对比...")
    plot_learning_rate_comparison()

    print("7/7 L1 vs L2 正则化...")
    plot_l1_l2_regularization()

    print(f"\n🎉 全部生成完毕！图片保存在: {OUTPUT_DIR}")
    print("共生成 7 张 PNG 图片")
