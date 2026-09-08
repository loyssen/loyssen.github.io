# 11 · Home Manager 入门

> 上一篇：[[10-开发环境-devShell与direnv]] · 下一篇：[[12-系统维护-代际回滚-垃圾清理-更新]]
> 扩展点——这是你配置里目前没有、但迟早会想要的东西。

## 1. 问题：系统管不到你家里

`nixos-rebuild switch` 管 `/etc`、`/run/current-system`、systemd 单元。
但它**不管**你家目录 `~/.config/*`、用户 systemd 服务、GNOME 扩展配置等。

你的 `dconf.enable = true` (desktop.nix) 只开了 GTK 主题的 hook，
nvim 的配置走了 nixvim（NixOS 模块），但其他"家目录级别的软件配置"还是手动或脚本的。

**Home Manager** 把声明式管理延伸到 `$HOME`：
~/.gitconfig、~/.config/gtk-3.0、用户 systemd timer、firefox 扩展……

## 2. 它和 NixOS 的关系

| 维度 | NixOS (system) | Home Manager (user) |
|---|---|---|
| 管什么 | 系统（/etc, services, packages） | 用户家目录（~/.config, ~/.local） |
| 生效范围 | 全机器 | 只有你的用户 |
| sudo | 要 | 不要 |
| 能不能只在一台机器上用 | ❌（NixOS） | ✅（也可以装在非 NixOS 上） |

你可以二选一（只用 NixOS），也可以组合（NixOS 管系统 + HM 管家目录）。

## 3. 它能做什么（你系统上的应用场景）

| 现在（手动/脚本/分散） | HM 后（声明式） |
|---|---|
| `~/.config/systemd/user/anime-wallpaper.service` 手写 | HM 里声明+自动生成 |
| `~/.config/mimeapps.list` 手动改 | HM 直接声明默认应用 |
| `~/.local/bin/anime-wallpaper` 脚本手动 | HM 的 `home.file` 自动部署 |
| `~/.gitconfig` 手写（如果有的话） | HM 里 `programs.git` 自动生成 |
| GTK/Firefox 配置分散 | HM 统一管理 |
| nvim 配置（你现在用的是 nixvim 模块） | HM 可管的更细（lazy.nvim 的用户插件列表） |

**目前不必急——你现在的配置组织已经很好了。当以下信号出现时考虑上 HM**：
- 开始手动改 `~/.config` 的文件并且`git diff`不到它们（在 git 外）
- 想在多台机间共享用户配置（HM 配置可以单独成一个 flake output，跨机复用）
- 开始频繁写 systemd 用户 service（anime-wallpaper、ocr daemon 等）
- 家目录脚本越来越多（`~/.local/bin` 已经 5 个+）

## 4. 怎么加（预备知识）

1. flake.nix 加 `home-manager` input
2. 加 `home-manager.nixosModules.home-manager` 模块
3. 配置写在 `home-manager.users.loysan = { ... }` 里
4. HM 配置和 NixOS 配置**统一 rebuild**→系统+家目录一起切

## 5. 目前不必动的理由

- 学习成本：又多一层抽象（HM 有自己的模块系统、option 集合）
- 当前家目录配置很轻（几个脚本、mimeapps 文件、wallpaper 服务）
- 出问题排错链变长（是 NixOS 模块还是 HM 模块的哪个 option 冲突了？）

## 6. 一句话

> Home Manager = 把声明式配置延伸到你的家目录。
> 目前不需要，但"有东西在 ~/ 下改来改去"越来越多了就该上了。

> [!NOTE] HomeManager
> 还是需要把配置做到用户级的，不过先完整了解 情况再说
>
> **答**：对的，不急。当前 NixOS 模块已经管了你绝大多数配置。
> 当以下三个条件**同时**满足时再上 Home Manager：
> 1. `~/.config` 下手动文件超过 10 个，不想手动维护了
> 2. 想在新机器上秒建完全一样的桌面体验（不只是系统，而是连终端字体/fcitx5 皮肤/
>    GTK 主题/mime 关联都一行 rebuild 搞定）
> 3. 你对 NixOS 模块系统已经熟悉到能同时调试两层合并的报错
>
> 目前你就在第 3 步的学习中——先把手上的模块系统学扎实再往上加层。


下一篇：[[12-系统维护-代际回滚-垃圾清理-更新]]
