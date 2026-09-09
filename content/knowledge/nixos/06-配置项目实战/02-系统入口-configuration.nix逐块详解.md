# 02 · 系统入口: configuration.nix 逐块详解

> 目标:把 `configuration.nix` 从头到尾过一遍,理解每块配置的意图。
> 建议对照代码文件阅读(代码已有详细中文注释)。

`configuration.nix` 是"总装车间":它不实现具体功能,而是
**决定装哪些模块、设哪些全局项**。所有功能逻辑都在 `modules/` 里。

## 1. 头部与模块导入

```nix
{ config, pkgs, inputs, ... }:
```

这是 Nix 函数的参数模式:模块系统把三样东西传进来——
- `config`:合并后的完整配置(可在模块里引用其他模块的值)
- `pkgs`:nixpkgs 包集合(用 `pkgs.xxx` 取包)
- `inputs`:flake 的全部输入(来自 `specialArgs`,所以这里能写 `inputs.niri`)

```nix
imports = [ ./hardware-configuration.nix ./modules/... ./nixvim/default.nix ];
```

**imports 就是组装清单。** 每行引入一个模块文件,模块系统会把所有文件的
配置合并。想停用某个功能,注释掉对应行即可(功能还在,只是不启用)。

## 2. 系统身份

```nix
boot.loader.systemd-boot.enable = true;
boot.loader.efi.canTouchEfiVariables = true;
```

- systemd-boot:简洁的 EFI 引导器,启动时显示代际列表(可回滚)
- canTouchEfiVariables:允许安装器写 EFI 变量(更新引导项需要)

```nix
networking.hostName = "loysan";          # 主机名
time.timeZone = "Asia/Shanghai";         # 时区
system.stateVersion = "25.11";           # 状态版本
```

**stateVersion 是 NixOS 的兼容性开关**:标记系统首次安装的版本。
升级 NixOS 后它保持旧值,让系统保持旧行为(比如旧的服务默认值)。
**永远不要把它改成新版本号**,那是迁移时才做的。

## 3. Nix 设置: 镜像与实验特性

```nix
nix.settings.experimental-features = [ "nix-command" "flakes" ];
```

现代 nix 命令(`nix build`、`nix run`)和 flakes 都要显式开启。

```nix
nix.settings.substituters = [
  "https://mirrors.tuna.tsinghua.edu.cn/nix-channels/store"  # 清华
  "https://mirrors.ustc.edu.cn/nix-channels/store"           # 中科大
  "https://cache.nixos.org/"                                 # 官方兜底
];
```

**substituters = 二进制缓存的"问路顺序"**。nix 下载预编译包时按顺序询问:
国内镜像快(直连),最后一个官方源兜底。这就是系统装软件快的原因。
`trusted-public-keys` 是缓存签名公钥,校验下载内容完整可信。

## 4. unfree 与 unstable overlay

```nix
nixpkgs.config.allowUnfree = true;
```

nixpkgs 默认不含 unfree 软件(微信/QQ/网易云/Clash 等商业软件),
开这个开关才能装。

```nix
nixpkgs.overlays = [(final: prev: {
  unstable = import inputs.nixpkgs-unstable {
    system = prev.stdenv.hostPlatform.system;
    config.allowUnfree = true;
  };
})];
```

**这是全仓库最常用的模式**:把不稳定版 nixpkgs 挂到 `pkgs.unstable` 名下。
之后任何模块都能写 `pkgs.unstable.qq` 取不稳定版的包。
- 为什么 QQ 用 unstable?25.11 源里的 deb 已被腾讯下架(404)
- 为什么必须 allowUnfree?legacyPackages 默认不带 unfree 许可,不写会报错

overlay 原理:它是"包集合的增量补丁",`final` 是结果、`prev` 是原集合,
你往里加属性,所有用 nixpkgs 的地方都能看到。

## 5. nix-daemon 环境与全局 gitconfig(踩坑的产物)

```nix
systemd.services.nix-daemon.environment = {
  GOPROXY = "https://goproxy.cn,direct";
  HTTPS_PROXY = "http://127.0.0.1:7897";
  ...
  GIT_HTTP_VERSION = "HTTP/1.1";
};
```

nix-daemon 是真正干活的进程(下载/构建)。给它配:
- **GOPROXY**:构建 Go 项目(如 DMS)时模块下载走 goproxy.cn(国内镜像)
- **代理**:所有网络请求走本地 clash(7897 端口)
- **GIT_HTTP_VERSION**:血泪教训——mihomo 代理对 git 的 HTTP/2 协商会失败,
  导致 TLS 握手死循环(git-remote-https 进程 99% CPU 永不结束)。
  强制 HTTP/1.1 后实测稳定。

```nix
environment.etc."gitconfig".text = ''
  [http]
    version = HTTP/1.1
'';
```

为什么还要全局 gitconfig?因为**求值阶段的 git fetch 跑在 nixos-rebuild
客户端进程里**(不在 daemon 内),daemon 的环境变量管不到它。
全局 git 配置是兜底,所有 git 进程统一 HTTP/1.1。

> 这个坑的完整故事和排查方法见 [[09-踩坑实录-代理镜像与git死循环|09 踩坑实录]]。

## 6. 用户

```nix
users.users.loysan = {
  isNormalUser = true;
  extraGroups = [ "wheel" "networkmanager" "video" "input" "audio" ];
  hashedPassword = "...";  # 哈希密码,不是明文
};
```

- `isNormalUser`:创建 home 目录、默认 shell 等
- 用户组含义:
  - `wheel` — sudo 提权
  - `networkmanager` — 允许管理网络(nmcli)
  - `video` — 显卡/背光设备(brightnessctl 调亮度需要)
  - `input` — 输入设备(数位板)
  - `audio` — 音频设备
- 密码是 `mkpasswd -m sha-512` 生成的哈希,不存明文

## 7. 如果我想加一个新功能模块?

```
1. 新建 modules/我的功能.nix
2. 在 imports 里加一行 ./modules/我的功能.nix
3. 在文件里写配置(nixos-option 查可用选项)
4. build 验证 → switch 应用
```

就这么简单——**加功能 = 加模块 + 声明 import**。
这就是 NixOS 模块化的日常。

---

**下一篇**:[[03-桌面栈-niri与Noctalia与DMS协作|03 桌面栈]]
