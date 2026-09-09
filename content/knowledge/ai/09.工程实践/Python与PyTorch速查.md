---
tags: [工程, Python, PyTorch, 速查]
created: 2026-06-29
difficulty: 🟢入门
---

# Python 与 PyTorch 速查

> AI 开发的必备工具速查表。

---

## Python 核心技能

| 技能 | 重要性 | 说明 |
|------|--------|------|
| NumPy | ⭐⭐⭐ | 数组操作、矩阵运算 |
| Pandas | ⭐⭐⭐ | 数据处理、CSV读写 |
| Matplotlib/Seaborn | ⭐⭐ | 数据可视化 |
| pathlib / os | ⭐⭐ | 文件路径管理 |
| argparse | ⭐ | 命令行参数 |
| typing | ⭐⭐ | 类型标注（提升代码可读性） |

### NumPy 速查

```python
import numpy as np

# 创建
a = np.array([1, 2, 3])
b = np.zeros((3, 4))
c = np.random.randn(2, 3)

# 运算
d = a @ b.T          # 矩阵乘法
e = np.dot(a, b.T)   # 同上
f = a * b            # 逐元素乘

# 变形
g = c.reshape(3, 2)
h = c.T              # 转置
```

---

## PyTorch 核心概念

### 张量（Tensor）

```python
import torch

# 创建
x = torch.tensor([1., 2., 3.])
y = torch.randn(3, 4)        # 正态分布随机
z = torch.zeros(2, 3)
w = torch.ones(3)

# 设备切换
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
x = x.to(device)

# 运算（和 NumPy 几乎一样）
r = x @ y.T
s = torch.matmul(x, y.T)
t = x * y

# 梯度
x = torch.tensor([2.0], requires_grad=True)
loss = x ** 2
loss.backward()     # ∂loss/∂x = 2x = 4
print(x.grad)       # 4.0
```

### 标准训练模板

```python
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# 1. 数据
class MyDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y
    def __len__(self):
        return len(self.X)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

dataset = MyDataset(X_train, y_train)
loader = DataLoader(dataset, batch_size=32, shuffle=True)

# 2. 模型
model = nn.Sequential(
    nn.Linear(10, 64),
    nn.ReLU(),
    nn.Linear(64, 1),
)

# 3. Loss + Optimizer
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 4. 训练循环
for epoch in range(100):
    for x_batch, y_batch in loader:
        optimizer.zero_grad()
        y_pred = model(x_batch)
        loss = criterion(y_pred, y_batch)
        loss.backward()
        optimizer.step()
```

### 常用层

| 层 | 用途 |
|-----|------|
| `nn.Linear(in, out)` | 全连接 |
| `nn.Conv2d(in, out, k)` | 2D卷积 |
| `nn.LSTM(in, hidden)` | LSTM |
| `nn.Embedding(vocab, dim)` | 词向量 |
| `nn.BatchNorm2d(n)` | Batch Norm |
| `nn.LayerNorm(n)` | Layer Norm |
| `nn.Dropout(p)` | Dropout |

---

## 环境管理

```bash
# 创建虚拟环境
python -m venv ai_env
source ai_env/bin/activate  # Windows: ai_env\Scripts\activate

# 安装核心包
pip install torch torchvision torchaudio
pip install transformers datasets accelerate peft trl
pip install numpy pandas matplotlib seaborn scikit-learn
pip install jupyter notebook
```
