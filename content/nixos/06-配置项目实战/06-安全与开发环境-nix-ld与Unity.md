# 06 · 安全与开发环境: nix-ld、Unity 与系统服务

> 目标:理解 `modules/security.nix` 和 `modules/unity.nix`,
> 重点是 nix-ld(FHS 兼容层)的原理——这是 NixOS 上跑"普通 Linux 软件"
> (Unity、闭源二进制)的核心机制。

## 1. 安全相关系统服务

```nix
security.polkit.enable = true;                    # 图形授权框架
services.gnome.gnome-keyring.enable = true;       # 密钥环(密码/SSH 密钥)
services.openssh.enable = true;                   # SSH 服务(远程登录)
```

- **polkit**:图形程序需要提权时(如文件管理器挂载磁盘)的授权框架
- **gnome-keyring**:集中保管密码、SSH 密钥、Chromium 的密码(登录后自动解锁)

### 为什么 niri 要手动启动 polkit 代理?

```nix
systemd.user.services.lxqt-policykit-agent = { ... };
```

**polkit 代理 = 弹出的"输入密码"对话框**。GNOME/KDE 桌面自带代理,
但 niri 是 wlroots 系合成器,**不负责桌面 UI**——所以必须手动启动一个
代理(lxqt-policykit-agent),否则"允许/拒绝"弹窗出不来,提权操作会卡住。

## 2. nix-ld: NixOS 跑外来二进制的关键

### 问题:NixOS 上跑不了"普通 Linux 程序"?

在 Ubuntu 上,`./Unity` 直接就能跑:它需要 `libGL.so.1`、`libX11.so.6` 等
系统库里。但 **NixOS 没有 /usr/lib**,库都在 /nix/store 各自的包里,
普通二进制按固定路径 `/usr/lib/...` 找库 → 找不到 → 崩溃。

### 解法: nix-ld 提供标准库路径

```nix
programs.nix-ld.enable = true;                    # 启用 FHS 兼容层
programs.nix-ld.libraries = with pkgs; [
  libglvnd       # libGL/EGL/GLX(OpenGL 调度层)
  mesa           # GL 驱动实现
  xorg.libX11    # X11 基础库(Unity 窗口需要)
  xorg.libXcursor / libXext / libXi / libXinerama / libXrandr / libXxf86vm
  xorg.libXScrnSaver
  wayland        # Wayland 客户端库
  libxkbcommon   # 键盘布局
  dbus           # 进程通信
];
```

**原理**:nix-ld 是一个加载器,让程序按 `/usr/lib` 找库时重定向到
`/nix/store` 里这些包的库。你追加的 `libraries` 就是"允许程序看到的库"。

**为什么缺库的症状这么诡异?** Unity 报
`"Video subsystem has not been initialized"`——不是显卡坏了,
是 libGL 找不到,引擎初始化视频子系统失败。**缺库的报错往往在深层**,
排查思路:报错 → 查它 dlopen 什么库 → 加进 libraries。

### chromiumSuidSandbox

```nix
security.chromiumSuidSandbox.enable = true;
```

Unity/Chromium 内嵌的 chrome-sandbox 需要 setuid 权限才能做沙箱隔离。
NixOS 默认禁 setuid,NixOS 模块把它重新挂上。

### inotify 调优

```nix
boot.kernel.sysctl."fs.inotify.max_user_instances" = 4096;
```

Roslyn(C# 语言服务器)在大型项目上监控大量文件,默认 inotify 实例数不够
会报错。这是"给某个软件的运行环境打补丁"的典型写法。

## 3. Unity 开发环境整体方案

```
Unity Editor(普通 Linux 二进制)
  ├─ nix-ld        → 提供标准库路径(缺什么加什么)
  ├─ xwayland-satellite → X11 程序在 Wayland 下运行
  ├─ chromiumSuidSandbox → 沙箱权限
  ├─ unityhub      → 版本管理/安装
  └─ .NET 工具链(dotnet-sdk_9 / roslyn-ls / netcoredbg / csharpier)
      └─ 配 nixvim 的 C# LSP + DAP(见 08 nixvim)
```

**这套方案的通用性**:以后遇到任何"下载的 .tar.gz 跑不起来"的程序,
先跑 `ldd 程序` 看缺什么库,加到 `programs.nix-ld.libraries` 即可。
这就是 NixOS 社区跑闭源软件的标准姿势。

## 4. OpenTabletDriver(数位板)

```nix
hardware.opentabletdriver.enable = true;
```

Wacom 等数位板驱动:模块自动配置 udev 规则(设备权限)+ 用户服务。
属于"硬件支持"类模块,与显卡/蓝牙同类。

## 5. 桌面模块小件

`modules/desktop.nix` 还包含:
- SDDM(Wayland 模式)+ catppuccin 主题 + 自动登录
- 光标主题(Bibata-Modern-Ice)与尺寸
- `NIXOS_OZONE_WL=1`:强制 Electron/Chromium 应用走 Wayland
  (没有它 Chrome 等应用会以 XWayland 运行,缩放/输入法体验差)
- `QT_QPA_PLATFORM=wayland`:Qt 应用原生 Wayland

---

**下一篇**:[[07-nixvim体系一-模块化架构|07 nixvim 体系(一)]]
