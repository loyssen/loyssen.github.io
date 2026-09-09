# 01 · 仓库总览与 Flake 工作流

> 目标:读完本文,你清楚整个仓库的结构、Flake 的输入输出怎么运作、
> 改一个配置要经过哪些步骤。

## 1. 仓库结构一览

```
nixos-config/
├── flake.nix                    ← 配方书:声明输入与输出(入口)
├── flake.lock                   ← 锁定每个输入的确切版本(自动生成)
├── configuration.nix            ← 系统主配置:模块汇总处
├── hardware-configuration.nix   ← 硬件自动生成(勿手改)
├── modules/                     ← 功能模块(按领域拆分)
│   ├── audio.nix                ← PipeWire 音频
│   ├── nvidia.nix               ← NVIDIA 驱动与内核参数
│   ├── locale.nix               ← 中文环境(输入法/字体)
│   ├── desktop.nix              ← SDDM 登录/主题/环境变量
│   ├── niri.nix                 ← niri 合成器(键位/布局)
│   ├── noctalia-dms.nix         ← 桌面壳与顶栏
│   ├── portal.nix               ← xdg-desktop-portal
│   ├── packages.nix             ← 软件包清单
│   ├── security.nix             ← polkit/keyring/ssh
│   ├── unity.nix                ← Unity 开发环境
│   └── cheatsheet/              ← 自研快捷键速查工具
└── nixvim/                      ← Neovim 全 Nix 化
    ├── default.nix              ← nixvim 入口(imports 顺序有讲究)
    ├── options.nix              ← 基础选项
    └── plugins/                 ← 按插件分组(13 个文件)
```

**核心思想:一切皆模块。** `configuration.nix` 只是把各模块"组装"起来,
每个模块文件返回一个属性集,最终合并成一个完整的系统定义。

## 2. Flake 是什么(5 分钟版本)

Flake = **一份声明了"依赖什么"和"产出什么"的配方**。

```
inputs(输入)                          outputs(输出)
─────────────                          ──────────────
nixpkgs 25.11   ──┐
nixpkgs-unstable ─┤
niri             ─┼──►   flake.nix  ────►   nixosConfigurations.loysan
noctalia         ─┤                                    │
DMS + quickshell  ─┤                                    ▼
nixvim           ─┘                            一台完整的可启动系统
```

### inputs:你依赖什么

`flake.nix` 声明了 6 个输入,每个都是"外部代码仓库":

| 输入 | 用途 | 特点 |
|---|---|---|
| `nixpkgs` (25.11) | 系统基础:包、服务、模块 | 稳定,适合底座 |
| `nixpkgs-unstable` | 需要新版包时的补充 | 更新快,经 overlay 挂为 `pkgs.unstable` |
| `niri` | 平铺合成器 + NixOS 模块 | 提供 niri 二进制和 polkit 等集成 |
| `noctalia` | 桌面壳(launcher/锁屏/控制中心) | 与 niri 通过 IPC 通信 |
| `dankMaterialShell` + `quickshell` | 顶栏 + 其 UI 运行时 | DMS 依赖 Quickshell |
| `nixvim` | Neovim 全 Nix 化 | 提供 `programs.nixvim` 选项 |

注意 `inputs.nixpkgs.follows = "nixpkgs"`:**让子 flake 沿用本仓库的 nixpkgs**。
否则 niri 可能用一套 nixpkgs、系统用另一套,导致依赖不一致的混乱。

### outputs:你产出什么

`outputs` 函数接收所有输入,返回 `nixosConfigurations.loysan`:
- `system = "x86_64-linux"` — 目标架构
- `specialArgs = { inherit inputs; }` — 把输入传进模块,模块里就能写 `inputs.niri.packages...`
- `modules = [...]` — 三个模块: nixvim 的模块 + 主配置 + 硬件配置

### flake.lock:锁定版本

`flake.lock` 记录每个输入的**确切 commit**。
作用:别人 clone 你的仓库,`nixos-rebuild` 拉到的是一模一样的代码,可复现。
更新输入:`nix flake update`(全部)或 `nix flake update niri`(单个)。

## 3. 一次完整的改动流程

```
1. 改配置
   $ nvim modules/packages.nix          # 比如加个包

2. 验证能否构建(不应用到系统)
   $ nixos-rebuild build --flake /home/loysan/nixos-config
   # 构建成功会输出 /nix/store/xxx-nixos-system-loysan-...

3. 应用到系统(需要 sudo)
   $ sudo nixos-rebuild switch --flake /home/loysan/nixos-config

4. (可选)提交到 git
   $ git add -A && git commit -m "feat(...): ..."
```

**为什么不直接 switch?** 先 `build` 验证:如果配置有错,在 build 阶段就报错,
不会把系统弄坏。switch 和 build 的产物在缓存里是同一个,switch 会很快。

**注意**:flake 从 git 仓库取源时**只包含已跟踪的文件**。
新建的文件必须先 `git add`,否则构建找不到它(报 "path does not exist")。

## 4. 修改配置后哪里会报错

| 错误类型 | 症状 | 解决办法 |
|---|---|---|
| 语法错误 | build 立即报 `error: syntax error` | 检查大括号/引号,`nix-instantiate --parse` 验证 |
| 选项不存在 | `The option 'xxx' does not exist` | 拼写错误或模块没启用,`nixos-option` 查 |
| 包不存在 | `attribute 'xxx' missing` | 包名不对或不在这个 nixpkgs 版本 |
| 文件没跟踪 | `path '...' does not exist` | `git add` 新文件 |
| 网络卡死 | 卡在 building + git 高 CPU | 见 09 踩坑实录(代理/git) |

## 5. 常用命令速查

```bash
nixos-rebuild build --flake .      # 只构建不应用
sudo nixos-rebuild switch --flake . # 构建并切换(新系统立即生效)
nix flake update                    # 更新所有输入版本
nix flake lock                      # 刷新 lock(不更新版本)
nix-collect-garbage -d              # 清理旧代际与垃圾(先看 10 维护篇)
sudo nixos-rebuild switch --rollback # 回滚到上一个代际
```

---

**下一篇**:[[02-系统入口-configuration.nix逐块详解|02 系统入口:configuration.nix]]
