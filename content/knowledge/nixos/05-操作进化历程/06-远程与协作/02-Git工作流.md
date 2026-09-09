---
title: Git 工作流
tags: [Linux, 进化历程, Git, lazygit, GitHub]
date: 2026-08-06
---

# Git 工作流:集中式 → 分布式,命令行 → TUI

> [!info] 本页内容
> git 为什么诞生?工作区/暂存区/仓库是什么关系?
> merge 和 rebase 怎么选?lazygit 到底要不要用。

## 一、背景:2005 年那两个星期

Linux 内核一直用 BitKeeper(商业分布式版本控制)管理代码。2005 年 4 月授权被收回,Linus Torvalds 花了两周写出 git,两个设计目标直接决定了它的形态:

| 目标 | 实现 |
|---|---|
| 快 | 内核体量下也要秒级操作 |
| 分布式 | 每个克隆都是完整仓库,离线可提交 |

**集中式 vs 分布式**:

| | **CVS(1986)/ SVN(2000)** | **git(2005)** |
|---|---|---|
| 仓库 | 只有服务器一份 | 每个克隆都是完整仓库 |
| 提交 | 必须联网 | 本地提交,随时可做 |
| 分支 | 慢、贵(拷贝目录) | 快如切指针 |
| 离线工作 | 不行 | 完全可行 |
| 现状 | 历史遗留 | **事实标准** |

## 二、核心概念:三个区域 + 提交链

```
工作区(你改的文件)──git add──▶ 暂存区(挑好的变更)──git commit──▶ 仓库(提交历史)
                                                          ▲
              git restore(还原) ◀─────────────────────────┘
```

| 概念 | 说明 |
|---|---|
| 工作区 | 磁盘上的真实文件 |
| 暂存区(index) | 决定"这次提交包含什么",支持挑着提交 |
| 仓库(.git) | 全部历史,内容寻址,不会丢 |
| 提交(commit) | 一次快照 + 作者 + 信息,`HEAD` 指向最新 |
| 分支(branch) | 指向某次提交的**指针**,创建/切换几乎零成本 |

## 三、日常命令流

| 命令 | 作用 |
|---|---|
| `git init` | 把目录变成仓库(一次) |
| `git status` | 看三个区域的状态(用得最多) |
| `git add 文件` / `git add -p` | 加入暂存区 / 逐块挑选 |
| `git commit -m "信息"` | 生成提交 |
| `git log --oneline --graph` | 看提交历史(带分支图) |
| `git diff` / `git diff --staged` | 看改动 / 看已暂存改动 |
| `git push` / `git pull` | 推送 / 拉取(含合并) |
| `git switch -c 新分支` | 新建并切换分支 |

> [!note] 新命令
> `git switch` / `git restore` 是 2019 年(git 2.23)新增,**替代**语义混乱的 `git checkout`——新写法只做一件事:切分支 / 还原文件。

## 四、分支工作流

**feature branch(最通用的流程)**:

```
main ──●──●────────────●──(合并)
         └── feat/xxx ──●──●──●   ← 开发完 merge 回来
```

1. 从 main 切分支:`git switch -c feat/xxx`
2. 小步提交,随时 push 到远端
3. 完成:GitHub 上发起 Pull Request,或本地 `git merge`

**merge vs rebase**:

| | **merge** | **rebase** |
|---|---|---|
| 历史 | 保留分叉,新增合并节点 | 重放提交,历史变直线 |
| 安全性 | 永远安全 | 改写历史,**只用于未推送的分支** |
| 团队协作 | 默认选择 | 个人整理用 |
| 命令 | `git merge feat/xxx` | `git rebase main` |

> [!warning] 铁律
> 已 push 到共享分支的提交**永远不要 rebase**(会改写他人已拉取的历史)。
> 最简单的团队规则:主线用 merge,自己的分支上用 rebase 保持整洁。

## 五、现今流行

- **lazygit**(2018):终端里的 git 可视化——一键 stage/commit/branch/merge,不用背命令(你已装)
- **diffview**:nvim 插件,看 diff、审变更的现代选择(你已装)
- **GitHub Flow / PR**:小步分支 + PR 评审成为团队协作标准;GitLab/Gitea 同模式
- **conventional commits**:`feat:` / `fix:` 前缀,配合 changelog 自动生成
- **git switch / restore**:新命令普及,旧 checkout 用法逐渐退场
- **AI 写提交信息**:Copilot / Claude 自动生成 commit message,减轻"起名字"负担

## 六、怎么选(你的环境)

你的 `nixos-config` 本身就是 git 仓库,`nixvim/plugins/git.nix` 里 lazygit 和 diffview 都已启用——工具齐了,差的只是习惯:

| 场景 | 做法 |
|---|---|
| 日常提交(改配置) | lazygit:改完 → stage → commit,全程可视化 |
| 看这次改了什么 | nvim 里 `:DiffviewOpen`,或终端 `git diff` |
| 改错想回退 | `git log --oneline` 找到提交 → `git revert`(不要硬删历史) |
| 多文件大改 | 开分支 + 小步提交,便于回滚 |
| 推送到 GitHub | 配好 remote 后 `git push`;PR 流程见第四节 |

> [!tip] 给你的最小工作流
> 1. 提交信息写"做了什么",固定一种语言(中文/英文都行)
> 2. 配置改动前先 `git status` 确认干净,改完 `git diff` 检查再提交
> 3. lazygit 当日常入口,命令行 git 用来做 lazygit 没有的操作
> 另外:你的 notes 库还没纳入 git——`git init` 后每天 commit,等于免费的历史备份。
