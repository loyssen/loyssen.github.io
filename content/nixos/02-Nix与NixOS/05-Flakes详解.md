# 05 · Flakes 详解

> 上一篇：[[04-derivation与构建过程]] · 下一篇：[[06-NixOS模块系统]]
> 拿你的 flake.nix 逐行讲——读完这篇就能自己改造它。

## 1. Flake 是什么

Flake 是 Nix 的**标准化项目/依赖管理单元**：
- 用 lock file（`flake.lock`）pin 死所有依赖的精确版本 → 可复现
- 替换旧的 `nix-channel`/`nix-env -f <expr>`/`builtins.fetchGit` 的混乱
- 每个 flake 有统一入口 `flake.nix` → 其他 flake 可以引用

你每次 `sudo nixos-rebuild switch --flake ~/nixos-config#loysan` 就是：
"用本地 flake，构建名为 loysan 的 nixosConfiguration 输出"。
如果在不同机器上跑同一条命令（git clone + flake.lock 一致）→ 出同样的系统。

## 2. 你的 flake.nix 逐行讲解

### description（一行元数据）
```nix
description = "loysan's NixOS configuration — niri + Noctalia + DMS";
```

### inputs：声明依赖（你想从哪拉代码）
```nix
inputs = {
  nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";        # 稳定版
  nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixpkgs-unstable"; # 滚动版

  niri = {                                                    # 第三方 flake
    url = "github:sodiboo/niri-flake";
    inputs.nixpkgs.follows = "nixpkgs";  # ← ★关键：共用 nixpkgs
  };
  # ... noctalia, dankMaterialShell, quickshell, nixvim 同理
};
```

`follows` 是说："你这个 flake 也依赖 nixpkgs——别自己拉一份，跟我共用我那份"。
如果 6 个 flake 各自拉一份 nixpkgs → 6 份 → flake.lock 爆炸 + 构建混乱。
`follows` 保证**全局一份 nixpkgs**。

输入不仅限 GitHub URL。你的 quickshell 就是 `git+https://git.outfoxxed.me/...`——
任意 flake-capable git 仓库都行。

### outputs：给定输入，产出什么

```nix
outputs = { self, nixpkgs, nixpkgs-unstable, noctalia, niri, nixvim,
            dankMaterialShell, quickshell, ... }@inputs:
{
  nixosConfigurations.loysan = nixpkgs.lib.nixosSystem {
    system = "x86_64-linux";
    specialArgs = { inherit inputs; };  # 把 inputs 全传进模块（让你能在模块里用 inputs.xxx）
    modules = [
      inputs.nixvim.nixosModules.nixvim
      ./configuration.nix
      ./hardware-configuration.nix
    ];
  };
};
```

`nixosConfigurations.<主机名>` 是 NixOS flake 的标准输出名。
你的主机叫 loysan，所以是 `nixosConfigurations.loysan`。
如果要配第二台机器（台式/server/笔记本），加一个 `nixosConfigurations.desktop = ...`。

`specialArgs` 是传给模块的额外参数。不加这行，模块函数里拿不到 `inputs`——
你就没法在 modules/ 里写 `inputs.noctalia.packages.xxx`。

modules 数组里**顺序无关紧要**（NixOS 模块系统会合并），
但习惯把外部模块（nixvim）放前面，自己的配置放后面。

## 3. flake.lock：依赖的"快照"

`flake.lock` 是个 JSON，记录了每个 input 的**精确 hash 和修订号**。
你 `git clone` 这个仓库到新机器，`flake.lock` 保证所有依赖拉的是完全相同的版本。
这是可复现性的物质基础。

**更新依赖**（如内核更新、nixpkgs 追新版）：
```bash
nix flake update --flake ~/nixos-config
# 或只更新某一个
nix flake lock --update-input nixpkgs --flake ~/nixos-config
```
这改 flake.lock → 下次 rebuild 用新依赖。

## 4. flake 与非 flake 的对比

| 特性 | 旧方式（channels） | Flakes |
|---|---|---|
| 依赖 pin | `nixos-version` 告诉你大分支 | flake.lock 颗级 pin |
| 三方依赖 | 手动 import 或 IFD（乱） | inputs.follows |
| 跨机可复现 | git 传配置，但 channels 状态不在 repo | git clone + rebuild == 同系统 |
| 纯洁性 | impurity（允许读 ~/.config/nixpkgs） | eval 纯净（不读系统环境） |

## 5. 实践：加一个新依赖

场景：你想用 nixpkgs 官方没有、别人 flake 里有的包。
1. 在 `inputs` 下加 `foo.url = "github:someone/foo"; inputs.nixpkgs.follows = "nixpkgs";`
2. `specialArgs` 里加上 `inherit foo;`（如果要在模块里用）
3. `modules/` 里通过 `inputs.foo.packages.xxx` 引用

## 6. 容易犯的错
- `follows` 写错：`nix flake lock` 会报"找不到目标"
- 忘了 `inherit inputs` → 模块里用 `inputs.xxx` 报 undefined
- flake.lock 手动改 → 别手改，用 `nix flake lock --update-input`
- flake 里直接跑 `import` 其他非 flake 仓库 → 优先看对方有没有提供 flake

## 7. 一句话

> flake.nix 声明"我要什么" + flake.lock 锁定"我要的是哪个版本" = 可复现的搭建蓝图。
> nixosSystem 函数把蓝图翻译成可 boot 的系统快照。
> 你整个系统的"配方"就是 flake.nix + flake.lock + modules/*.nix — 三件套。

下一篇：[[06-NixOS模块系统]]。
