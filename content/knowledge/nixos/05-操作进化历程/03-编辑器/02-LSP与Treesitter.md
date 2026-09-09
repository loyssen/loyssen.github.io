---
title: LSP 与 Treesitter
tags: [Linux, 进化历程, 编辑器, LSP, treesitter]
date: 2026-08-06
---

# LSP 与 Treesitter:编辑器生态的两大基石

> [!info] 本页内容
> LSP 是什么协议?为什么它是编辑器对抗 IDE 的最大武器?
> Treesitter 和正则高亮差在哪?

## 一、LSP:Language Server Protocol(2016)

### 背景:重复造轮子的时代

在 LSP 出现之前,每个编辑器都要为每种语言单独写"补全、跳转、诊断"支持:

```
VS Code     写了 TS/Java/Python 的补全...
vim         也要写一遍 TS/Java/Python 的补全...
Emacs       还要写一遍...
```

N 个编辑器 × M 种语言 = N×M 份重复劳动,而且质量参差。

### 协议:把"懂语言"抽成独立服务

微软 2016 年提出 LSP——**编辑器不再懂语言,只负责界面**:

```
┌─────────────┐    JSON-RPC    ┌──────────────────┐
│ 编辑器(客户端) │ ←——————————→ │ 语言服务器(服务端) │
│ 只管 UI/键盘  │               │ 只懂一种语言       │
└─────────────┘               └──────────────────┘
    nvim / VS Code                 pyright / gopls / ts_ls
```

- **语言服务器**写一次(pyright 懂 Python),所有支持 LSP 的编辑器直接用
- 编辑器之间零重复;语言服务器是独立进程,崩溃不影响编辑器

### 语言服务器生态(你在用的)

| 服务器 | 语言 | 说明 |
|---|---|---|
| pyright | Python | 微软出品,补全/诊断/重构 |
| gopls | Go | 官方 |
| ts_ls | TypeScript/JS | 前身 tsserver |
| nil_ls | Nix | 你的 NixOS 配置靠它 |
| roslyn_ls | C# | Unity 开发靠它 |
| rust-analyzer | Rust | 公认最强服务器之一 |

### 在 nvim 里对应什么(你的配置)

| LSP 能力 | 你的键位 |
|---|---|
| 跳转定义 | `gd` |
| 查找引用 | `gr` |
| 悬浮文档 | `K` |
| 重命名 | `<leader>rn` |
| 代码操作 | `<leader>ca` |
| 诊断 | `<leader>k` / `[d` `]d` |

> [!note] 平行概念:DAP
> 调试也有同样的协议:**DAP**(Debug Adapter Protocol,2018)——调试器写一次,
> 所有编辑器通用。你配置里的 `netcoredbg` 就是 C# 的调试适配器。

## 二、Treesitter(2018)

### 传统语法高亮:正则的极限

```regex
\b(def|class)\b  ← 靠正则猜"这是关键字"
```

- 正则**猜**语法:字符串里的 `def` 也会被高亮成关键字
- 嵌套结构(字符串里的注释、注释里的引号)全部误判

### Treesitter:真正的语法树

Treesitter 是增量解析器(源自 Neovim 团队,2018 集成)——把代码解析成**语法树**:

```
function hello() { return 1; }
        ↓ 解析
function_declaration
├── name: hello
├── parameters: ()
└── body: { return_statement: 1 }
```

- 编辑器知道"这是函数名、这是参数、这是返回语句"——**不再是猜**
- 带来:精确高亮、智能选择(`<leader>ts` 选整个函数)、折叠、代码块导航
- 增量解析:每秒解析上千次也不卡(输入时实时更新语法树)

### 对比

| | 正则高亮 | Treesitter |
|---|---|---|
| 原理 | 模式匹配 | 语法树解析 |
| 误判 | 字符串里的关键字会误判 | 精确 |
| 能力 | 只有颜色 | 高亮 + 选择 + 折叠 + 导航 |
| 速度 | 快 | 增量后同样快 |

## 三、两大基石的关系

```
LSP(懂语义)      → 补全、跳转、诊断、重构     ← 语言服务器(慢而准,按需调用)
Treesitter(懂语法) → 高亮、选择、折叠、解析      ← 本地解析(快,常驻)
```

- LSP 回答"这个符号是什么、从哪来"
- Treesitter 回答"这段代码的结构是什么"
- 两者互补:一个管语义,一个管结构——这就是现代编辑器的"内功"

> [!tip] 记忆法
> 视频里听到"LSP"→ 语言智能(补全/跳转);"Treesitter"→ 语法高亮/选择。
> 你的 nvim 里 `<leader>?` 图鉴中 gd/K/rn 那一组都是 LSP 的功劳。
