# 02 · Nix 核心思想 —— 纯函数式部署

> 上一篇：[[01-为什么需要Nix-传统包管理的痛点]] · 下一篇：[[03-Nix语言入门]]
> 这一篇不写代码，建立 Nix 的四个核心概念的心智模型。

## 1. 核心一：Store 路径 = 输入的哈希

```
/nix/store/<hash>-<name>-<version>
/nix/store/c6mjnsxakwsg5w7ssrc7ajya13bw84sw-neovim-unwrapped-0.11.7
            └──────────────────┬──────────────────┘
                        32 个字符的哈希
```

这个哈希是对**所有构建输入**的指纹（源码、依赖、编译选项、系统架构……）。
任何输入变化 → 哈希完全不同 → 新路径 → 不影响旧路径。

**直接推论**：
- 两个版本的同一个软件可以共存（因为哈希不同）
- "安装"不会修改任何已有路径（只创建新路径 + 建符号链接）
- 两台机器上相同哈希的路径 → 内容逐字节一致（可复现构建）

## 2. 核心二：derivation —— 构建的"配方"

你想从源码编出 neovim，需要什么？
- 源码（tarball 或 git 某版本）
- 依赖（luajit、tree-sitter、libuv、gcc……）
- 构建脚本（cmake、meson……）
- 平台信息（x86_64-linux）

Nix 把这套配方抽象为 **derivation**（`.drv` 文件）。
derivation 是一个**纯数据结构**：

```
{ name = "neovim-unwrapped-0.11.7";
  system = "x86_64-linux";
  builder = "/nix/store/...-bash/bin/bash";           # 构建沙箱里的执行者
  args = [ "-c" "source $stdenv/setup; genericBuild" ];
  inputs = {
    src = "/nix/store/...-neovim-src.tar.gz";
    luajit = "/nix/store/...-luajit-2.1";
    # ... 所有依赖精确指向各自的 store 路径
  };
  env = { CMAKE_FLAGS = "..."; };
}
```

`nix-store --realise <drv>` → 在隔离沙箱里跑这个 builder → 产出 store 路径。
如果所有输入和上次一样，derivation 也一样 → Nix 直接用缓存（**无需重建**）。

## 3. 核心三：闭包 —— 完整的依赖树

推导出 neovim 的 store 路径不够——neovim 还依赖 luajit 的 .so，
luajit 又依赖 libuv……跑 neovim 需要整棵依赖树。

Nix 管一个包**加上它传递依赖的所有 runtime 依赖**叫**闭包**。
`nix-store -q --tree <路径>` 能看到整棵树。

所以 NixOS 上你不需要"装好运行时"——每个包的闭包都自完备。

## 4. 核心四：Profile 与代际 —— 原子切换

Package 装好了，怎么让 `which nvim` 找到它？

Nix 搞了一个**符号链接农场**：profile/代际。
```
/home/loysan/.nix-profile → /nix/store/<hash>-user-environment/ → /nix/var/nix/profiles/per-user/loysan/profile-<N>
/run/current-system         → /nix/store/<hash>-nixos-system-.../
```

**rebuild = 建一个新 profile 代际 + 重定向一级符号链接 + 跑 activation 脚本**
（创建 systemd 单元、etc 文件……）——整个过程**不到一秒**。

旧的 profile 文件还在 `/nix/var/nix/profiles/` 下，`nix-env --list-generations` 看得到。
开机时 systemd-boot 菜单里就是历代 profile → **滚回 = 选旧的，秒切**。

## 5. 这样构建出来的系统长什么样

```
/nix/store/
├── a1b2...-bash-5.3/
│   └── bin/bash
├── c3d4...-coreutils-9.5/
│   └── bin/ls, bin/cp, bin/mv...
├── e5f6...-glibc-2.40/
│   └── lib/libc.so.6
├── ...（几万个）
│
/run/current-system/     ← 就是一个符号链接，指向当前活跃的那一个 nixos-system
    └── sw/bin/ → 再链到各个包的 bin/（一堆符号链接）
```

你的 `ls` 命令的完整真实路径：
`/nix/store/...-coreutils-.../bin/ls`（经过 `/run/current-system/sw/bin/ls` 这个 symlink）。

## 6. 隔离性一览

| 层 | 怎么隔离 |
|---|---|
| 同一软件不同版本 | 哈希不同 → /nix/store 里不同路径 → 天然共存 |
| 不同用户的包 | 各自的 `~/.nix-profile` 符号链接，不互相干扰 |
| 构建过程 | 在 bubblewrap 沙箱里跑（无网络、只有声明的依赖、只写指定输出） |
| 临时试包 | `nix shell` 出来的包只在当前 shell 环境可见，退出就消失 |
| 运行时 | 两个项目需要不同版本的工具？各写一个 shell.nix/flake → `direnv` 自动切 |

## 7. 这东西不能解决的问题（诚实收尾）

- **要联网才能 build**（没缓存就只能下载/编译，不联网装不了包）
- **需要专用 GPU 的构建**不容易在纯净沙箱里做
- **闭源二进制**只好"偷渡"：下载 prebuilt 再打上 nix-ld wrapper
- **配置文件组织**没有唯一正确答案——见 [[07-配置文件组织最佳实践]]

## 8. 一句话

> Store 路径 = 哈希寻址 → 无冲突。Derivation = 构建配方 → 可复现。
> 闭包 = 自完备依赖树 → 零运行时缺失。Profile 代际 = 符号链接快照 → 原子切换+秒回滚。
> 这四个概念组合 = Nix 的全部威力。

下一篇：[[03-Nix语言入门]]（开始写代码）。
