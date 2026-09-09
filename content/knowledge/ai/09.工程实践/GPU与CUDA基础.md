---
tags: [工程, GPU, CUDA, 硬件]
created: 2026-06-29
difficulty: 🟡进阶
---

# GPU 与 CUDA 基础

> 理解硬件才能写出高效代码。

---

## 为什么 GPU

```
CPU: 几个大核，擅长复杂逻辑和串行任务
GPU: 几千个小核，擅长简单计算和大规模并行
```

深度学习 = 大量矩阵乘法 = 天然适合 GPU。

---

## 显存估算

### 全精度（FP32/BF16）

$$\text{显存} \approx \text{参数数量} \times 2\text{ bytes} \times 2\text{ (优化器+梯度)}$$

| 模型 | 参数 | FP16 权重 | 训练需要（含优化器） |
|------|------|----------|-------------------|
| 7B | 70亿 | ~14 GB | ~56 GB |
| 13B | 130亿 | ~26 GB | ~104 GB |
| 70B | 700亿 | ~140 GB | ~560 GB |

### 量化后

| 精度 | 70B 模型 | 可训练？ |
|------|---------|---------|
| FP16 | 140 GB | ✅ 需多卡 |
| INT8 | 70 GB | ✅ 需 2× A100 |
| INT4 (QLoRA) | 35 GB | ✅ 单卡 RTX 4090 |

---

## 显卡选择

| 显卡 | 显存 | 适合 |
|------|------|------|
| **RTX 4090** | 24 GB | 推理 + QLoRA 微调 7B/13B ⭐ |
| RTX 3090 | 24 GB | 同上（二手的很划算） |
| A100 | 40/80 GB | 专业训练 |
| H100 | 80 GB | 顶级训练 |
| M2 Ultra (Mac) | 192 GB (统一) | 推理 70B 模型 |
| RTX 4060 Ti 16GB | 16 GB | 推理 7B，QLoRA 勉强 |

---

## CUDA 需要知道什么

### 你不用写 CUDA 代码

PyTorch 自动处理 GPU 计算。你只需要知道：
- 数据/模型移到 GPU 上
- 不要 GPU-CPU 频繁搬运数据
- 显存不够时用梯度累积/量化/模型并行

### 硬件名词

| 名词 | 含义 |
|------|------|
| **CUDA** | NVIDIA 的 GPU 编程平台 |
| **cuDNN** | NVIDIA 的深度学习库（卷积优化等） |
| **Tensor Core** | GPU 中专门做矩阵乘法的硬件单元 |
| **FP16/BF16** | 半精度浮点，加速训练 |
| **HBM** | GPU 的高速显存 |

---

## 常用命令

```bash
# 查看 GPU 状态
nvidia-smi

# 查看 PyTorch 是否识别 GPU
python -c "import torch; print(torch.cuda.is_available())"

# 查看 GPU 信息
python -c "import torch; print(torch.cuda.get_device_name(0))"
```
