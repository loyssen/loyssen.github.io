# 09 · 运行外来二进制 —— nix-ld 与 FHS

> 上一篇：[[08-overlays与包定制]] · 下一篇：[[10-开发环境-devShell与direnv]]
> 这是你在 Unity 开发中亲历的核心问题：从网上下载的绿色版程序为什么跑不了。

## 1. 问题：外来二进制期望一个"标准 Linux"

任何预编译的 Linux 二进制（Unity Editor、Unity 打包产物、AppImage、某些 SDK）
在链接时硬编码了一条路径作为**动态加载器（interpreter）**：
```bash
readelf -l Unity | grep interpreter
# [Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]
```

然后加载器默认搜 /usr/lib、/lib64 找 .so。你的 NixOS **没有这些路径**。

```
标准 Linux：      /usr/lib/libGL.so.1         ← 有
                  /lib64/ld-linux-x86-64.so.2  ← 有
NixOS (无 nix-ld)： 啥都没有                   ← 报错！
NixOS (有 nix-ld)：  /run/current-system/sw/share/nix-ld/lib/ld.so  ← 只有这
```

没有加载器 → 执行程序时报 `No such file or directory`
（不是"文件找不到"，而是**加载器**找不到——这迷惑了无数新人）。
有加载器但缺 .so → dlopen 失败，日志里 `Error getting num native displays`。

> [!NOTE] 二进制加载器链接程序
> 命令运行出错了，不过这个的意思是会显示一些依赖的路径，这些标准linux都会在这个路径有这些依赖，但是nixos里面的依赖都在share/nix-ld/里面指向了对应的/nix/store/的依赖
> [loysan@loysan:~]$ readelf -l Unity | grep interpreter
readelf：错误：'Unity' is not an ordinary file
>
> **答**：理解完全正确。报错是因为当前目录的 `Unity` 是个符号链接或目录。
> 应指向实际的 ELF 二进制：
> ```bash
> readelf -l ~/Unity/Hub/Editor/2022.3.62f3c1/Editor/Unity | grep interpreter
> # 打包产物
> readelf -l ~/Projects/Unity/TestLinux/Builds/Test/TestGame.x86_64 | grep interpreter
> ```
> 看运行时依赖（比 ldd 更准确，不会实际加载）：
> ```bash
> readelf -d <二进制> | grep NEEDED
> ```
> 你归纳的 "nixos里面的依赖都在 share/nix-ld/ 里指向对应 /nix/store/ 的依赖"
> 完全正确——nix-ld 的 loader 在 `NIX_LD_LIBRARY_PATH` 下逐项搜，
> 每个 .so 都是一个指向 /nix/store 中具体包的符号链接。




## 2. nix-ld：桥接器

`programs.nix-ld.enable = true` 做了两件事：
1. 把 `/lib64/ld-linux-x86-64.so.2` 指向 nix-ld 提供的 loader 符号链接
2. 把 `NIX_LD_LIBRARY_PATH` 设为 `/run/current-system/sw/share/nix-ld/lib`

nix-ld 的 loader 会从 `NIX_LD_LIBRARY_PATH` 搜索 .so，而不是传统 FHS 路径。
而 `NIX_LD_LIBRARY_PATH` 指向的目录里有什么？——看 `programs.nix-ld.libraries`。
它的默认值（系统自动给的基础库）：zlib、zstd、curl、openssl、systemd……
**不含 X11/Wayland/GL**。

这就是你 `modules/unity.nix` 做了的事：
```nix
programs.nix-ld.libraries = with pkgs; [
  libglvnd mesa        # GL
  xorg.libX11 ...      # X11 客户端
  wayland libxkbcommon # Wayland 客户端
  dbus
];
```

追加后，外来二进制就能通过 loader → 搜 NIX_LD_LIBRARY_PATH → 找到 libX11.so.6 等 → 正常运行。

## 3. nix-ld.libraries 追加 vs 覆盖

nixpkgs 模块里的 option 定义是 `listOf packages` ——
你的追加和默认集合自动合并。所以不会丢掉系统基础库。

## 4. 另一个方案：FHS 环境（buildFHSEnv / steam-run）

nix-ld 对"加载器+库"问题管用，但有些程序需要**整个 FHS 的文件布局**：
- 硬编码了 `/usr/share/xxx`
- 依赖 `/etc/ld.so.conf`
- 有自己的一套 dlopen 插件系统

这时用**沙箱化的伪装传统 Linux**：

```nix
# unityhub 的例子（nixpkgs 官方就是这么包的）：
appimage-run <二进制>            # 对 AppImage
steam-run <二进制>                # 通用 game/3D 软件 FHS 环境
buildFHSEnv { name = "my-fhs"; targetPkgs = pkgs: [ 需要的库... ]; }
```

你的 Unity Hub 就是 nixpkgs 用 `buildFHSEnv` + bubblewrap 做的——
`which unityhub` 看到的那个 wrapper 脚本就是入口。

## 5. nix-ld vs FHS env 怎么选

| 场景 | 用什么 |
|---|---|
| 你打包的 Unity 游戏，只想双击运行 | nix-ld ✅（已配好） |
| 从 Hub 启动 Unity Editor | FHS env（Hub 自带）✅ |
| 终端直启 Unity Editor | 要用 `unityhub-fhs-env` wrapper |
| 网上下载的 AppImage | `appimage-run` / nix-ld 多数够 |
| 闭源 SDK（无根游戏引擎等） | 先试 nix-ld，失败再写 buildFHSEnv |
| 需要特定 /usr/share 的软件 | 必须 FHS env |

## 6. 排查"跑不起来"的标准流程

1. 先看报错：`No such file or directory`（文件存在且权限 OK）
   → **缺 loader**：查 `programs.nix-ld.enable`
2. 报错含具体 .so 名（如 `libX11.so.6: cannot open`）→ **缺具体库**：
   ```bash
   strace -f -e trace=openat 程序 2>&1 | grep "ENOENT.*\.so" | sort -u
   ```
   缺啥补到 nix-ld.libraries
3. 不报错但功能不正常（窗口不出来、音频无声）
   → 看程序日志（Unity: Player.log）
4. 以上都不行 → 写 buildFHSEnv 或 `steam-run` 试一把

## 7. 一句话

> "外来二进制跑不起来"是 NixOS 的入门仪式。nix-ld 给 loader + 库；
> FHS env 给完整的伪文件系统。你现在已经把两块都打通了。

> [!NOTE] nix-ld和FHS env的组织
> 目前只有unity.nix使用了nix-ld.enable=true,如果这种应用多了
> 是不是应该建一个独立文件夹存放nix-ld和FHS env模块来用
>
> **答**：思路很对。目前只有 Unity 需要这些库，`unity.nix` 里一起管是合理的。
> 信号：当你要给**第二个、第三个独立应用**加类似配置（比如以后加某个需要 X/GL 库
> 的工具、另一个需要 FHS env 的闭源软件），就应该拆出独立文件去重。具体做法可参照
> [[07-配置文件组织最佳实践#原则二：什么该合？什么该拆？]]。
>
> 拆法示例：
> ```
> modules/compat/
> ├── nix-ld-libs.nix       # 所有 nix-ld.libraries 集中一处
> ├── unity-editor-fhs.nix  # unityhub 的 FHS wrapper（如果有需要定制的话）
> ```
> 目前**不值得拆**——只有一个消费者，拆了反而过度工程设计。


下一篇：[[10-开发环境-devShell与direnv]]
