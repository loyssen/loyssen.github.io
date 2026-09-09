# 06 · NixOS 模块系统

> 上一篇：[[05-Flakes详解]] · 下一篇：[[07-配置文件组织最佳实践]]
> 这是 NixOS 最强大也最容易懵的概念。用你自己的 modules/ 逐例讲。

## 1. 什么是模块

NixOS 模块 = **一个返回 attrset 的函数**。所有模块的返回值被递归合并成一个巨大的
"系统选项树"。

```
模块函数(config, pkgs, lib, ...) → { networking.hostName = "loysan"; ... }
模块函数(config, pkgs, lib, ...) → { services.openssh.enable = true; ... }
模块函数(config, pkgs, lib, ...) → { environment.systemPackages = [ kitty ]; ... }
                     ↓ 全部合并（merge）
              { networking.hostName = "loysan";
                services.openssh.enable = true;
                environment.systemPackages = [ kitty ... ]; }
                     ↓ 求值 → nixosSystem
                       一个系统代际
```

## 2. 模块函数的签名

```nix
{ config, pkgs, lib, options, inputs, ... }:   # ← 系统注入的参数
{
  # ... 返回配置
}
```

| 参数 | 是什么 | 你哪用了 |
|---|---|---|
| `config` | 合并后的完整系统配置（查看"别人设了什么"） | configuration.nix 的 imports |
| `pkgs` | nixpkgs 包集合（装软件就用它） | `pkgs.kitty` 等 |
| `lib` | nixpkgs 工具函数库 | `lib.mkDefault` 等 |
| `options` | 所有可用 option 的元数据 | 几乎不用 |
| `inputs` | 从 flake specialArgs 传进来的 | `inputs.noctalia.packages...` |

## 3. options：模块的"声明式 API"

NixOS 的每个配置项都是预先**声明**好的 option。你能在 configuration.nix 里写
`networking.hostName = "loysan"`，是因为 nixpkgs 某处声明了：

```nix
options.networking.hostName = lib.mkOption {
  type = lib.types.str;            # 接受什么类型
  default = "nixos";               # 不写时默认值
  description = "The name of the machine.";
};
```

你写了 → 覆盖默认。没写 → 用默认。类型不匹配 → rebuild 时报错。

**这就是为什么 NixOS 配置不会"瞎生效"**：每个可以设的东西都显式声明了类型。
不是配置文件里的任意字段都能被识别——写错了名字直接报 attribute error。

## 4. 模块怎么合并（优先级系统）

多个模块可能设同一个 option（比如 `environment.systemPackages`），合并规则：

| 优先级 | 函数 | 用途 |
|---|---|---|
| 默认 | option 声明里的 `default` | 你没写就这个 |
| 低 | `lib.mkDefault value` | "我推荐这个但你可以覆盖"——hardware-configuration.nix 用它 |
| 中 | 普通 `= value`（你写的那种） | 用户配置 |
| 高 | `lib.mkForce value` | "听我的"——极少用 |
| 最高 | `lib.mkOverride 优先级值 value` | 更少见 |

你的 hardware-configuration.nix 里：
```nix
nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";
```
用了 `mkDefault`——意味着你的 configuration.nix 可以覆盖它（但没必要）。

**list 类型（如 packages）** 会**拼接**（不是覆盖）：
你 modules/packages.nix 的列表和 modules/unity.nix 的 unityhub
自动合并成一个长列表。所以各模块可以独立加包，不会互相覆盖。

## 5. 实例：你的 modules/audio.nix

```nix
{ pkgs, ... }:           # 只需要 pkgs，别的不用管
{
  services.pulseaudio.enable = false;    # 关 PulseAudio
  services.pipewire = {                  # 开 PipeWire
    enable = true;
    alsa.enable = true;
    pulse.enable = true;
  };
  security.rtkit.enable = true;          # 实时调度权限
}
```
这就是一个**自完备的模块**：声明"我要什么音频系统"，不做别的，
通过 option 系统跟其他模块合并。

## 6. 实例：你的 modules/niri.nix

```nix
{ config, pkgs, inputs, ... }:
{
  imports = [ inputs.niri.nixosModules.niri ];  # ← 导入外部模块（niri-flake 提供的）
  # config 自己声明各种 program.niri.*
}
```
这里的 `imports` 不是 Nix 语言的 import，而是 NixOS 模块系统的"我要加载那个模块"。
外部 flake（如 niri-flake）通过 `nixosModules.niri` 导出它自己的 NixOS 模块，
你 import 进来就能用 `programs.niri.enable`/`programs.niri.package` 等 option。

## 7. mkIf：条件模块（你还没用但值得知道）

```nix
{ config, lib, ... }:
{
  config = lib.mkIf config.services.xserver.enable {
    # 这一段只在启用 X 服务时才生效
    services.xserver.videoDrivers = [ "nvidia" ];
  };
}
```
避免配了互不兼容的选项纠缠在一起。

## 8. 查 option 的姿势

- 网页：`https://search.nixos.org/options`
- 命令行快速搜：`man configuration.nix`（你有个精简的 manual）
- 源码里找：`rg "programs.niri.enable" $(nix eval nixpkgs#path)`
- 看一个 option 的声明（文档+类型+默认值）：`nixos-option services.openssh.enable`

## 9. 一句话

> 模块 = 函数(config,pkgs,...) → attrset。系统 = 所有模块的合并结果。
> option 系统 = 配置的"类型安全的 API"——每个字段都声明了它能是什么、默认什么。
> 你的 10 个 modules/ 文件就是用这系统的一个个独立段落。

下一篇：[[07-配置文件组织最佳实践]]。
