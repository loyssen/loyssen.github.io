---
title: 声明式配置的终点:NixOS —— dotfiles 的终极形态
tags: [Linux, 进化历程, 配置管理, NixOS, home-manager, flake]
date: 2026-08-06
---

# 声明式配置的终点:NixOS —— dotfiles 的终极形态

> [!info] 本页内容
> 上篇的四代方案都在管"文件",但配置的另一半——装什么包、开什么服务、系统参数——
> 它们全都管不到。NixOS 把整台机器变成一份声明,dotfiles 问题被彻底吸收。
> 本篇只讲**生态横向对比**:NixOS 相比 stow/chezmoi 强在哪、你的配置库长什么样;
> flake 机制与模块系统原理不重复展开,文末链接直达。

## 一、为什么说 NixOS 是 dotfiles 的终极形态

| 传统 dotfiles | NixOS |
|---|---|
| 管"文件" | 管"机器状态" |
| 装包靠脚本(声明之外) | 包写在配置里,`rebuild` 一并解决 |
| 回滚靠 git revert | 原子代际回滚 |
| 复现 = 拷文件 | 复现 = 一份配置 + 一条命令,连内核参数都一致 |

三个关键词:

1. **配置即代码**:网络、包、服务、用户全是可读、可 diff、可 review 的声明
2. **原子回滚**:每次 `nixos-rebuild switch` 产生一个新代际,`--rollback` 一步回到上一代——比"配置坏了先想起备份"可靠得多(见 [[02-Nix与NixOS/12-系统维护-代际回滚-垃圾清理-更新]])
3. **可复现**:flake.lock 锁住所有输入,同一份配置任何时候构建,结果一致(见 [[02-Nix与NixOS/05-Flakes详解]])

## 二、你的 nixos-config 结构回顾

```
~/nixos-config/
├── flake.nix                  ← 输入清单 + 系统入口
├── flake.lock                 ← 全部输入版本锁
├── configuration.nix          ← imports 装配单 + 系统级配置
├── hardware-configuration.nix ← 硬件探测结果(装完自动生成)
├── modules/                   ← 按功能拆分:audio / nvidia / locale / desktop /
│                                niri / noctalia-dms / portal / packages /
│                                security / unity / cheatsheet
└── nixvim/                    ← 原 ~/.config/nvim,如今也在配置里
```

`configuration.nix` 的 imports 就是整台机器的"装配单":

```nix
imports = [
  ./hardware-configuration.nix
  ./modules/audio.nix
  ./modules/nvidia.nix
  ./modules/niri.nix
  ./modules/noctalia-dms.nix
  ./modules/packages.nix
  ...
  ./nixvim/default.nix
];
```

对照上篇:这些配置原本散落在 `~/.bashrc`、`~/.config/nvim`、`~/.config/kitty`、`/etc/...`;
现在全部在仓库里——**换机、重装、迁移 = clone + rebuild**。
模块怎么拆、什么时候该合,见 [[02-Nix与NixOS/07-配置文件组织最佳实践]]。

## 三、NixOS vs stow / chezmoi

| 维度 | stow | chezmoi | NixOS(+home-manager) |
|---|---|---|---|
| 管理对象 | 文件 | 文件 | 文件 + 包 + 服务 + 系统 |
| 环境可复现 | ❌ | ❌ | ✅ 整机级 |
| 回滚 | git revert | git revert | ✅ 原子代际回滚 |
| 多机差异 | 分支/手动 | 模板 + 变量 | ✅ 同一 flake 声明多台机 |
| 加密 | ❌ | ✅ age | ✅ agenix/sops |
| 安装成本 | 低 | 低 | 高(要换系统) |
| 生态 | 广 | 广 | 深度集成,包配置一步到位 |

一句话:**stow/chezmoi 解决"文件层",NixOS 连文件之外一起解决**;
代价是拥抱整个 Nix 生态——这正是 [[02-Nix与NixOS/01-为什么需要Nix-传统包管理的痛点]] 讲过的取舍。

## 四、home-manager 的作用

NixOS 管 `/etc`、系统包、服务;但 dotfiles 的领地还有一大块在 `$HOME`:
`~/.gitconfig`、`~/.bashrc`、用户级 systemd 服务、非系统级的软件配置。

**home-manager** 把声明式延伸到用户级,补齐最后一块(见 [[02-Nix与NixOS/11-home-manager入门]]):

| 层 | 管什么 | 入口 |
|---|---|---|
| NixOS (system) | /etc、包、服务、内核 | configuration.nix / modules |
| home-manager (user) | ~/.config、~/.gitconfig、用户服务 | home.nix |
| nixvim(你的特例) | 编辑器全家桶 | nixvim/ 模块 |

你已经在 nixvim 上体验过"配置即代码"的编辑器玩法——home-manager 就是把它推广到整个 `$HOME`。

## 五、现今流行(2026)

- **NixOS 用户**:dotfiles = 配置仓库,`git push` 私有远端,新机器 `clone + rebuild` 全量复现
- **生态继续扩张**:flakehub、NUR(第三方包集散地)让"别人的配置"也能直接复用
- **非 NixOS 用户两条路**:chezmoi 继续文件流;或单独装 home-manager 体验声明式
- **Guix** 是另一支声明式派系,依然小众;**stow/chezmoi 在非 NixOS 世界仍是主流**——NixOS 不是唯一答案,只是这条演化路的终点

## 六、怎么选

| 你 | 方案 |
|---|---|
| 已在 NixOS | 别回头;缺的用 home-manager 补 |
| 不想换系统 | chezmoi + 安装脚本(文件层最优解) |
| 想尝声明式 | 非 NixOS 上单装 home-manager |

> [!tip] 一条原则
> 你的 `~/nixos-config` 已经证明:能进配置库的,一律进配置库——
> 别再往 `~/.config` 里手写配置。配置进 git、机器变声明,才是这套玩法的全部收益。
