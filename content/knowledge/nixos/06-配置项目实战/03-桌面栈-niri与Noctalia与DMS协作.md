# 03 · 桌面栈: niri × Noctalia × DMS

> 目标:理解三个程序各自干什么、怎么协作,以及 niri 键位体系的设计思路。

## 1. 分工: 谁管什么

| 程序 | 类型 | 管什么 | 配置文件 |
|---|---|---|---|
| **niri** | 平铺合成器 | 窗口管理、键位、工作区、布局 | `modules/niri.nix`(生成 `/etc/niri/config.kdl`) |
| **Noctalia** | 桌面壳 | 应用启动器、锁屏、控制中心、壁纸、系统设置 | `modules/noctalia-dms.nix` + niri 启动项 |
| **DMS** | 顶栏 | 状态栏:时间/音量/音乐/系统监控 | 同上(DMS 由 niri 启动) |

**协作方式**:
- niri 是底层,只管窗口;**外观和系统 UI 是 Noctalia/DMS 的事**
- 三者通过 **IPC 通信**:niri 的键位 `spawn "noctalia" "msg" "lock"` 就是给
  Noctalia 发命令(锁屏、开控制中心、开 launcher)
- 分工原则:"合成器不做 UI,外壳不做窗口"

## 2. 启动链

```
niri 启动(登录后)
 ├─ spawn-at-startup "noctalia"              # 桌面壳(壁纸/launcher 服务)
 ├─ spawn-at-startup "sh -c sleep 2 && noctalia msg bar-hide"   # 2 秒后隐藏 bar(让出空间)
 ├─ spawn-at-startup "dms run --session --daemon"               # DMS 顶栏
 └─ spawn-at-startup "sh -c /home/loysan/.local/bin/ocr-clipboard-daemon"  # OCR 剪贴板后台
```

注意 `config.kdl` 通过 `environment.etc` 写入系统 —— 这是 NixOS 管理
配置文件的通用手法:**配置文件也成为声明式配置的一部分,可回滚**。

## 3. niri 配置分段

### 3.1 输入(键盘/触摸板/鼠标)

```kdl
input {
    keyboard { xkb { layout "us" } repeat-delay 300 repeat-rate 30 }
    touchpad { tap; natural-scroll; }
    mouse { accel-profile "flat" }        // 鼠标无加速,定位精确
    focus-follows-mouse max-scroll-amount="0%"
}
```

- 键盘美式布局(中文输入法接管输入,键盘布局只需 us)
- 触摸板支持轻点 + 自然滚动
- **focus-follows-mouse**:鼠标移到哪个窗口焦点就跟过去
  (`max-scroll-amount="0%"` 防止滚动时焦点乱跳)

### 3.2 环境变量(Wayland 全家桶)

```kdl
environment {
    MOZ_ENABLE_WAYLAND "1"      // Firefox 原生 Wayland
    XDG_SESSION_TYPE "wayland"
    GDK_BACKEND "wayland"       // GTK 应用走 Wayland
    TERM "kitty"  TERMINAL "kitty"
    QT_QPA_PLATFORMTHEME "qt6ct"  // Qt 应用主题
    GTK_IM_MODULE "fcitx"  QT_IM_MODULE "fcitx"  XMODIFIERS "@im=fcitx"  // 输入法
    HTTPS_PROXY "http://127.0.0.1:7897"  ...   // 全局代理
}
```

**这些变量是 niri 会话的全局环境**,图形应用都继承。
为什么 GUI 应用能用代理?因为 niri 在这里统一注入。

### 3.3 布局

```kdl
layout {
    gaps 5                        // 窗口间距
    background-color "transparent"
    default-column-width { proportion 0.5 }   // 默认半屏宽
    preset-column-widths { proportion 0.5 0.66667 1.0 }  // Mod+R 循环的三种宽度
    focus-ring { width 1.5 active-color "#7fc8ff" }      // 焦点窗口蓝色描边
}
```

`preset-column-widths` + `Mod+R` = 快速切换列宽(半屏→2/3→全屏),平铺效率核心。

### 3.4 窗口规则

```kdl
window-rule {
    geometry-corner-radius 6        // 全局圆角
    clip-to-geometry true
}
window-rule { match title="Firefox" open-on-workspace "3" open-maximized true }
window-rule { match app-id="cheatsheet" open-floating true ... }  // 速查窗浮动
```

- Firefox 固定开在工作区 3 并最大化 —— "浏览器专用工作区"
- cheatsheet 窗口浮动 + 固定尺寸 —— 快捷键速查弹出即用

## 4. 键位体系(核心中的核心)

设计哲学:**`Mod`(Super)是万能前缀,方向键与 HJKL 双套并存**。

### 4.1 启动与系统

| 键位 | 动作 |
|---|---|
| `Mod+Return` | kitty 终端 |
| `Mod+D` | fuzzel 启动器 |
| `Mod+B` | Firefox |
| `Mod+Space` | Noctalia launcher |
| `Mod+S` / `Mod+,` | 控制中心 / Noctalia 设置 |
| `Super+Alt+L` | 锁屏 |
| `Mod+F1` | 快捷键速查(cheatsheet) |
| `Mod+Shift+/` | niri 热键总览 |
| `Mod+Shift+O` | 截图 OCR |
| `Mod+Shift+S` | flameshot 截图 |
| `Mod+Shift+E` | 退出 niri |

### 4.2 焦点与移动(HJKL = 方向键双套)

| 键位 | 动作 |
|---|---|
| `Mod+H/J/K/L` 或 `Mod+←↓↑→` | 切换焦点(列左/下/上/右) |
| `Mod+Ctrl+H/J/K/L` | 移动窗口/列 |
| `Mod+Shift+H/J/K/L` | 切换显示器 |
| `Mod+Shift+Ctrl+H/J/K/L` | 移动列到其他显示器 |
| `Mod+Home/End` | 跳到最左/最右列 |

### 4.3 工作区

| 键位 | 动作 |
|---|---|
| `Mod+1..5` | 切工作区(5 个) |
| `Mod+Ctrl+1..5` | 窗口移到工作区 |
| `Mod+U/I` / `PageUp/Down` | 上/下工作区 |
| `Mod+滚轮` | 滚轮切工作区 |
| `Mod+Shift+U/I` | 移动整个工作区 |

### 4.4 窗口操作

| 键位 | 动作 |
|---|---|
| `Mod+Q` | 关闭窗口 |
| `Mod+F` / `Mod+Shift+F` | 最大化列 / 真全屏 |
| `Mod+V` / `Mod+Shift+V` | 浮动切换 / 焦点切到浮动窗 |
| `Mod+C` | 居中列 |
| `Mod+R` | 循环列宽(50%→66%→100%) |
| `Mod+O` | Overview 任务总览 |
| `Mod+[/]` | 吞入/吐出窗口 |

### 4.5 媒体键(锁屏也可用)

`XF86AudioRaiseVolume` 等音量/亮度键 `allow-when-locked=true`,
用 `wpctl`(PipeWire 官方控制)和 `brightnessctl`。

## 5. 想改键位?

改 `modules/niri.nix` 里 `binds` 段 → build → switch → 验证。

改完可以**热重载**不重启会话:
```
niri msg reload
```
(niri 支持大部分配置热重载;但 spawn-at-startup 等需要重启会话)

## 6. 与 cheatsheet 的联动

`Mod+F1` 打开的速查窗会**读取当前聚焦窗口的 app-id**,显示对应应用的
快捷键(如聚焦 kitty 显示终端快捷键)。它的实现细节见 cheatsheet 模块,
是一个"kitty 窗口 + Python 渲染 + JSON 数据"的组合。

---

**下一篇**:[[04-中文环境-输入法字体与locale|04 中文环境]]
