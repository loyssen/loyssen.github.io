# 10 · 开发环境 —— devShell 与 direnv

> 上一篇：[[09-运行外来二进制-nix-ld与FHS]] · 下一篇：[[11-home-manager入门]]
> Nix 不仅是系统配置工具，它是最好的"项目级开发环境管理器"。

## 1. 动机：项目之间不应该互相污染

你 Unity 项目里要 dotnet-9 SDK。另一个 Rust 项目要特定版本的 rustc。
全局装吗 → 冲突。每个项目 venv → 要记 activate / 不同工具的 venv 语法。

Nix 的方案：**每个项目目录一个 `shell.nix` 或 `flake.nix`**，
进目录自动加载环境，出目录自动还原。

## 2. nix shell：临时进某个环境

```bash
nix shell nixpkgs#nodejs_22    # 单独一个包
nix shell nixpkgs#nodejs_22 nixpkgs#typescript  # 一堆包
# 退出：exit 或 Ctrl+D
```
包只在这个 shell 里可见，退出就没了。**试包神器**——试试某版本会不会出问题、
试一下小工具一次性用。

你的 `nix shell nixpkgs#mkpasswd -c mkpasswd -m sha-512 '密码'` 就是这用法。

## 3. nix develop（devShell）：正式开发环境

在项目根目录写一个 `flake.nix`（或 `shell.nix`）：

```nix
{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  outputs = { nixpkgs, ... }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = [
        pkgs.dotnet-sdk_9
        pkgs.nodejs_22
        pkgs.roslyn-ls
      ];
      shellHook = ''
        echo "Unity dev environment ready"
        export DOTNET_ROOT="${pkgs.dotnet-sdk_9}"
      '';
    };
  };
}
```

然后 `cd` 到项目目录，`nix develop` → 进带 dotnet-9 的环境。
（direnv 能让这个变成自动化——不用手动敲命令，见下。）

## 4. direnv + nix-direnv：全自动环境切换

装好 `direnv` + `nix-direnv` 后，在项目根加一个 `.envrc`：
```bash
use flake   # 或 use nix
```

`cd` 到该目录 → direnv 自动加载 flake 的 devShell。
出目录 → 自动还原。**零手动操作**，像什么都没发生但环境已经准备好了。

（系统上还没装，想加我可以一行配。）

> [!NOTE] 全自动环境
> 这个东西看起来能很优雅的切换环境，应该会需要
>
> **答**：对。以后当你有项目需要特定版本的 SDK 时（比如不同 Unity 版本对应不同
> dotnet SDK、老项目需要旧 Python），直接给那个项目加个 `flake.nix` + `.envrc`
> 即可。安装 direnv 和 nix-direnv 只要在 packages.nix 加两行。现在不急——
> 你的全局方案（packages.nix 全装上）对当前工作流够用。

## 5. 你的系统中的等价物

你现在的配置没有用 devShell（模块直接声明全局包），是"全局靠谱，啥都够"的暴力方案。
优点是不用操心，代价是全局包列表在膨胀。

以后如果某项目需要仅在该项目下才能用的特殊工具（比如不同版本的 dotnet SDK、
旧版 python、riscv 交叉编译器），就可以给那个项目写一个 flake devShell，
而不污染全局 packages.nix。

## 6. 一句话

> `nix shell` = 随手尝鲜。`nix develop` = 项目专属开发环境。
> `direnv` = 忘掉"激活环境"这回事。你的系统目前走"全能全局方案"——记住 devShell 是备选武器。

下一篇：[[11-home-manager入门]]
