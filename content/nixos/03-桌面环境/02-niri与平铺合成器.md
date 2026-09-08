# 02 · niri 与平铺合成器

> 上一篇：[[01-显示服务器-从X11到Wayland]] · 下一篇：[[03-XDG门户portal与桌面集成]]
> 相关：[[配置详解#modules/niri.nix]] · [[使用说明#niri 键位]]

## 1. 什么是平铺窗口管理器

**传统（堆叠）**：窗口像纸一样叠放、拖来拖去、用鼠标调整大小位置。

**平铺（tiling）**：窗口自动排列、不重叠、用键盘快捷键操纵。
典型：i3、Sway、Hyprland、Qtile、dwm……

平铺管理器 = 高信息密度（所有窗口同时可见）+ 键盘驱动（手不离开键盘区）。

## 2. niri：滚动平铺新范式

niri 不是传统的"窗口网格平铺"，它是**无限横向滚动的工作区**：

```
┌─────────┬─────────┬─────────┬─────────┬ ... → 右侧延续（新建窗口开新列）
│  窗口1  │  窗口3  │  窗口5  │         │
│         │         │─────────│         │
│         │         │  窗口6  │         │
│─────────│─────────│         │         │
│  窗口2  │  窗口4  │         │         │
└─────────┴─────────┴─────────┴─────────┴ ...
列内多窗口上下堆积，列之间水平滚动。
```

**跟传统平铺对比**：
- Sway/i3：窗口全是完整瓷砖，多了切 workspace。方向感弱。
- Hyprland：美化版平铺，理念同 i3。
- niri：**空间连续性**——窗口在一条横轴上，你直觉知道"vim 在 Firefox 右边，终端在最左边"。

滚轮或键位切列时，画面水平平移而不是瞬间跳变——很直觉。

## 3. 你的 niri 布局配置（modules/niri.nix 关键参数）

```kdl
gaps 5                            # 窗口间 5px 间距
center-focused-column "never"     # 焦点列不居中（你选了手动的）
default-column-width { proportion 0.5; }  # 新列默认占 50% 屏幕宽度
preset-column-widths { proportion 0.5; proportion 0.66667; proportion 1.0; }
# ↑ Mod+R 循环 50%/66%/100%
focus-ring { width 1.5; active-color "#7fc8ff"; inactive-color "#505050"; }
# ↑ 焦点列边框：活跃=柔和蓝 非活跃=暗灰
border { off }                     # 窗口各自不画边框
window-rule { geometry-corner-radius 6; clip-to-geometry true; }
# ↑ 所有窗口 6px 圆角（挺现代的）
```

## 4. 你的键位设计哲学

核心原则：**vim hjkl** 统一方向（`H←  J↓  K↑  L→`）。
不加修饰符 = **导航**（focus: 切焦点）
加 `Ctrl` = **移动**（move column: 搬列/窗）
加 `Shift` = **跨屏幕/跨 workspace**（更大的跳转）
加 `Ctrl+Shift` = **跨屏幕移动**（搬窗口到另一个显示器）

**这个模式一旦记住，不需要背键位表**——知道方向键+修饰符的语义就够了。

实际键位（只列"左"的做示例，其他方向同理）：

| 修饰符 | 作用 | 键位示例 |
|---|---|---|
| Mod | 切换焦点 | `Mod+H` ← |
| Mod+Ctrl | 移动窗口 | `Mod+Ctrl+H` ← |
| Mod+Shift | 切显示器 | `Mod+Shift+H` ← |
| Mod+Ctrl+Shift | 窗口搬到另一显示器 | `Mod+Ctrl+Shift+H` ← |

**滚轮映射**（和键盘语义一一对应）：
- 滚轮上/下 = 切 workspace
- 滚轮左/右 = 切列
- 修饰符同上

Firefox 特殊规则：`open-on-workspace "3"; open-maximized true`
→ 启动或窗口创建时自动跳到 workspace 3 并最大化。

## 5. 启动链原理

```kdl
spawn-at-startup "noctalia"
spawn-at-startup "sh" "-c" "sleep 2 && noctalia msg bar-hide"
spawn-at-startup "dms" "run" "--session" "--daemon"
spawn-at-startup "sh" "-c" "/home/loysan/.local/bin/ocr-clipboard-daemon"
```
noctalia 先起来（管壁纸+锁屏+launcher），2 秒后发出 bar-hide 指令
（隐藏 noctalia 自带的 bar，因为顶栏用 DMS 管），
然后 DMS 以 daemon 模式启动（顶栏+系统监控），
最后 OCR 剪贴板守护（后台看剪贴板有没有图片）。

**环境变量**就是在这里设置的：
- Wayland 相关 `MOZ_ENABLE_WAYLAND/GDK_BACKEND/...` → 所有 niri 启动的进程都继承
- 代理 `HTTPS_PROXY=127.0.0.1:7897` → 子进程的网络请求走 clash
- fcitx5 注入 `GTK_IM_MODULE/...` → GTK/Qt 应用自动启动输入法

## 6. 怎么修改 niri 配置

1. 编辑 `modules/niri.nix` 的 `environment.etc."niri/config.kdl".text` 块
2. `nixos-rebuild build` 验证 → switch
3. 新配置立即生效（niri 热重载，或手动 `niri msg reload`）

**注意**：修改的是 NixOS 配置里的 KDL 字符串，不是
`~/.config/niri/config.kdl`（那个文件会被 `environment.etc` 覆盖）。

## 7. niri 和你的软件生态的配合

| 组件 | 怎么配合 |
|---|---|
| Noctalia | spawn-at-startup，提供 launcher/锁屏/控制中心/壁纸 |
| DMS | 顶栏，通过 Noctalia 的 MPRIS/系统信息暴露到 niri 的 wayland 层 |
| xwayland-satellite | 无根 X 桥，让 Unity Editor 窗口能独立平铺 |
| fuzzel | Mod+D 启动，Wayland 原生 launcher |
| flameshot | Mod+Shift+S 截图，走 wlr-screencopy 协议 |

## 8. 一句话

> niri = 滚动平铺+Wayland。你的键位核心是 hjkl + 修饰符 = 导航/移动/跨屏。
> 启动链是 noctalia→DMS→后台守护，环境变量全在这初始化。

下一篇：[[03-XDG门户portal与桌面集成]]
