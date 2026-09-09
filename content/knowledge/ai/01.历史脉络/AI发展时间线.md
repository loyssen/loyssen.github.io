---
tags: [历史, 时间线, 总览]
created: 2026-06-29
difficulty: 🟢入门
---

# 📜 AI 发展时间线

> 从图灵测试到 GPT-4，一张图看尽 AI 七十年的技术演进。

---

## 完整时间线

```mermaid
gantt
    title AI 技术发展时间线
    dateFormat  YYYY
    axisFormat  %Y

    section 符号主义时代
    图灵测试提出           :1950, 1950
    达特茅斯会议(AI诞生)    :1956, 1956
    感知机(Perceptron)      :1957, 1957
    ELIZA 聊天机器人        :1966, 1966
    第一次 AI 寒冬          :1974, 1980
    专家系统兴起            :1980, 1987
    第二次 AI 寒冬          :1987, 1993

    section 机器学习崛起
    SVM 支持向量机          :1995, 1995
    LSTM 长短期记忆网络     :1997, 1997
    ImageNet 数据集发布     :2009, 2009

    section 深度学习革命
    AlexNet 赢得 ImageNet  :2012, 2012
    GAN 生成对抗网络        :2014, 2014
    ResNet 残差网络         :2015, 2015
    AlphaGo 战胜李世石      :2016, 2016

    section 大模型时代
    Attention Is All You Need:2017, 2017
    BERT 发布              :2018, 2018
    GPT-2 发布（15亿参数） :2019, 2019
    GPT-3 发布（1750亿）   :2020, 2020
    InstructGPT / ChatGPT  :2022, 2022

    section Agent 探索时代
    AutoGPT 出现           :2023, 2023
    GPT-4 多模态           :2023, 2023
    LangChain/LangGraph    :2023, 2024
    Claude/DeepSeek 等爆发 :2024, 2025
    多模态 Agent 架构成熟  :2025, 2026
```

---

## 技术范式演进

```mermaid
flowchart LR
    A["🧠 符号主义<br/>规则引擎<br/>专家系统<br/>1950s-1980s"]
    B["📊 统计机器学习<br/>SVM/决策树<br/>特征工程驱动<br/>1990s-2010"]
    C["🧬 深度学习<br/>CNN/RNN/GAN<br/>端到端学习<br/>2012-2017"]
    D["🔮 预训练大模型<br/>Transformer/GPT<br/>Scaling Law<br/>2017-至今"]
    E["🤖 AI Agent<br/>自主规划执行<br/>多模态多智能体<br/>2023-至今"]

    A -->|"数据 + 算力"| B
    B -->|"GPU + 大数据"| C
    C -->|"Transformer + 互联网数据"| D
    D -->|"工具使用 + 推理能力"| E

    style E fill:#ffd93d,color:#333
    style D fill:#ff6b6b,color:#fff
```

---

## 各时代速览

| 时代 | 时间 | 核心技术 | 代表成果 | 详细笔记 |
|------|------|---------|---------|---------|
| 符号主义 | 1950s-1980s | 逻辑推理、专家系统、感知机 | ELIZA、MYCIN | [[1.1 符号主义时代]] |
| 机器学习崛起 | 1990s-2010 | SVM、决策树、集成学习 | IBM Watson、推荐系统 | [[1.2 机器学习的崛起]] |
| 深度学习革命 | 2012-2017 | CNN、RNN、GAN、ResNet | AlexNet、AlphaGo | [[1.3 深度学习的革命]] |
| 大模型时代 | 2017-2022 | Transformer、BERT、GPT | GPT-3、ChatGPT | [[1.4 大模型时代的开启]] |
| Agent 探索 | 2023-至今 | LLM Agent、多模态、多智能体 | AutoGPT、GPT-4 | [[1.5 Agent与AGI探索]] |

---

## 关键转折点

| 年份   | 事件                  | 意义                              |
| ---- | ------------------- | ------------------------------- |
| 1956 | 达特茅斯会议              | AI 概念正式诞生                       |
| 2012 | AlexNet 赢得 ImageNet | 深度学习革命的起点                       |
| 2017 | Transformer 论文发表    | **改变一切的架构**，现代 LLM 基石           |
| 2020 | GPT-3 发布            | 证明 Scaling Law，大模型的 "iPhone 时刻" |
| 2022 | ChatGPT 发布          | AI 走入大众视野，两个月破亿用户               |
| 2023 | LLM Agent 元年        | 从"聊天"到"行动"的质变                   |

---

## 学习建议

> 💡 历史不是孤立的知识点。理解「为什么 Transformer 会在 2017 年出现」、理解「为什么 RLHF 在 2022 年才成为标配」，能帮你建立技术取舍的直觉。

建议学习顺序：
1. 先读完这篇时间线总览
2. 逐个时代深入阅读详细笔记
3. 带着「每个时代解决了什么问题、留下了什么局限」的问题进入 ML 基础学习
