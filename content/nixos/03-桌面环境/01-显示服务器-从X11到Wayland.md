# 01 · 显示服务器 —— 从 X11 到 Wayland

> 上一篇：[[12-系统维护-代际回滚-垃圾清理-更新]] · 下一篇：[[02-niri与平铺合成器]]
> 相关：[[配置详解#modules/niri.nix]] · [[使用说明#niri 键位]]

## 1. X11（1984）与 Wayland（2008）的本质区别

**X11**（X Window System，第 11 版）：
- 1984 年设计，**网络透明**是核心卖点（远程显示一个窗口）
- **X Server** 一个超级进程：管输入、管输出、管窗口装饰、管合成、管字体……
- 客户端通过 X 协议跟它通信
- 性能路径冗长（一个窗口要经过多层拷贝）
- 安全模型≈无（任何 X 客户端可以偷看别的窗口的按键）

**Wayland**：
- 2010 起（Kristian Høgsberg），专门为**现代桌面**重新设计
- 没有"超级 Server"——**合成器**集成了显示服务器（= Wayland compositor = 合成器 + Server）
- 客户端直接渲染到自己的缓冲区 → 合成器一次组装 → 上屏（零拷贝路径）
- 安全模型：每个应用只能看自己的输入
- 没有网络透明（需要的话用 pipewire+portal 重新实现）

## 2. 谁赢了（2026 年的答案）

**Wayland 是桌面 Linux 的事实标准**。证据：
- Fedora/Ubuntu/RHEL 默认 Wayland
- KDE/GNOME 在 Wayland 下开发优先于 X11
- NVIDIA 从 2021-2023 的抗拒转为 2024 的全面支持（GBM+explicit sync）
- XWayland（X11 兼容层）无缝跑旧应用

**还没解决/边缘的问题**：
- 远程桌面不如 X11 原生，但 pipewire+portal 方案已成型（你的 remmina 用 portal 就可以）
- 某些极老企业级软件（医学图像、CAD）只有 X11
- 平铺管理器生态 Wayland 上更碎片化（没有统一的 WM 协议）

## 3. 你的组合：niri（Wayland 合成器）+ xwayland-satellite（X11 兼容）

你的显示栈长这样：

```
Wayland 原生应用（kitty, firefox, nautilus, blender...）
       ↘
   niri 合成器（Wayland compositor + 窗口管理）
       ↗
XWayland 桥 → xwayland-satellite →  X11 应用（Unity Editor, 打包的游戏）
```

- `GDK_BACKEND=wayland`（你 niri.nix 的 environment 块）→ GTK 应用通过 Wayland 渲染
- `NIXOS_OZONE_WL=1` → Electron 应用通过 Wayland
- `MOZ_ENABLE_WAYLAND=1` → Firefox 通过 Wayland
- `QT_QPA_PLATFORM=wayland` → Qt 应用（微信、QQ）通过 Wayland

但 Unity Editor 是 X11 程序（Unity 自己渲染走 X11），流程：
niri 屏幕 ← xwayland-satellite ← Unity ← GLX ← Mesa GLVND ← nvidia EGL

## 4. 为什么你的"forceFullCompositionPipeline"是无意义的

那是 X11 专有选项——X11 合成器需要 force pipeline 来避免撕裂。
Wayland 合成器**天然无撕裂**（每帧完全渲染后才上屏），强制 pipeline 什么也不变。
已从 nvidia.nix 删除。

## 5. `xwayland-satellite` vs `xwayland`

传统 `xwayland` 是个 rootful X 服务器，跑起来就给整个 X 屏幕。
`xwayland-satellite` 是无根模式：每个 X 窗口是一个独立的 Wayland surface，
合成器可以单独管理（像原生 Wayland 窗口一样平铺/浮动）。
这正是 niri 需要的——如果用的传统 xwayland，X 窗口全在一个大框里没法单独平铺。

## 6. 哪些应用在走 XWayland（看你系统上跑的）

```bash
# 随便跑一个 X 应用看一下：
xlsclients -l 2>/dev/null  # 可能需要 xorg.xlsclients
```
Unity Editor、Unity 打包产物、某些旧的 wine 都走 XWayland。
大多数现代 GUI 应用已经是 Wayland 原生。你不知道某个应用走什么：
用 `xeyes` 或 `xwininfo` 测试——鼠标悬停在上面会有反应就是 X11。

## 7. 出了问题怎么判断是显示栈的哪一层

- 某个应用窗口不出来，但后台跑着 → 查 XWayland（`pgrep xwayland-satellite`）
- 所有窗口都不出来 → 合成器（niri）本身挂了，`journalctl --user -u niri`
- 图形花屏/撕裂 → NVIDIA 驱动层（nvidia-smi，查驱动版本和模式设置）
- Wayland 原生应用不显示 → portal/EGL 问题
- X11 应用不显示 → DISPLAY 环境变量被错误覆盖（你删掉硬编码那一步就是防这个）

## 8. GPU 加速和 offload

你的 nvidia.nix 配置：
```nix
boot.kernelParams = [ "nvidia_drm.modeset=1" "nvidia_drm.fbdev=1" ];
```
→ modeset 启用内核模式设置（Wayland 需要这个）
→ fbdev 让 nvidia 作为 framebuffer console（启动 logo 不出雪花）

`hardware.graphics.enable32Bit = true` → Steam Proton/32 位游戏需要。

## 9. 一句话

> X11 做了太多事，Wayland 让合成器重新中心化。你的系统是 100% Wayland 原生 +
> xwayland-satellite 做 X11 桥。现代 GUI 生态的主航道已经换了方向。

下一篇：[[02-niri与平铺合成器]]
