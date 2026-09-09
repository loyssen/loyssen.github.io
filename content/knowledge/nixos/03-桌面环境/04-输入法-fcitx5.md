# 04 · 输入法 —— fcitx5

> 上一篇：[[03-XDG门户portal与桌面集成]] · 下一篇：[[05-音频-PipeWire与MPRIS]]
> 相关：[[配置详解#modules/locale.nix]]

## 1. 你的输入法栈

```
fcitx5（输入法框架核心）
├── fcitx5-rime（Rime 引擎——中文主力）
│    └── 双拼/全拼/五笔 等方案（内置）
├── fcitx5-chinese-addons（拼音/双拼备选）
├── fcitx5-nord（nord 配色主题）
├── fcitx5-gtk（GTK 应用的输入法模块）
├── fcitx5-configtool（Qt GUI 配置器）
└── fcitx5.waylandFrontend = true（Wayland 原生 input-method 协议）
```

## 2. 为什么这些环境变量必须设

```bash
GTK_IM_MODULE="fcitx"     # GTK/GNOME 应用知道用 fcitx
QT_IM_MODULE="fcitx"      # Qt/KDE 应用知道用 fcitx
XMODIFIERS="@im=fcitx"    # XWayland 应用用 fcitx
```

这些在你 niri.nix 的 `environment` 块中声明，所有由 niri 启动的应用自动继承。
**这就是为什么你在 kitty/nautilus/wps/blender/微信/QQ 中都能直接切换中文**。

## 3. 怎么用
- **切换中英**：`Ctrl+Space`（默认），或 `Shift`（看你 Rime 配置）
- **GUI 配置**：fuzzel 搜 "fcitx5"，或在终端 `fcitx5-configtool`
  - 加/删输入法：拼音 → 双拼 / 五笔 / 仓颉
  - 换 Rime 方案：~/.local/share/fcitx5/rime/default.custom.yaml
  - 换皮肤：内置 nord 主题，更多在 `fcitx5-nord` 同目录
- **查输入法是否挂载**：`fcitx5-diagnose`（终端，打印完整环境检查报告）

## 4. 常见问题

| 症状 | 原因 | 修法 |
|---|---|---|
| 某个应用切不出中文 | 环境变量没传递到该应用 | 查该应用的启动方式 |
| 微信里输入法不工作 | 微信走 Qt，QT_IM_MODULE 有效 |
| 纯 Wayland 应用输入框位置不对（候选窗口飘到左上角） | 合成器的 input-method popup 支持不完全 | 降级方案：fcitx 经典界面模式 |
| 输入法图标不显示 | 没有托盘区（niri 无系统托盘）| 忽略，不影响功能，或看 fuzzel |
| gnome-keyring 冲突 | fcitx 和 gnome-keyring 争 ibus 启动 | 检查 `GTK_IM_MODULE` 只设 fcitx（你已经设好了） |

## 5. Rime 简介

Rime 是个**引擎**不是输入法——你需要选一个"方案"：
- `luna_pinyin`（朙月拼音·简化字）——默认全拼
- `double_pinyin`（双拼）——双键一字，更快
- `wubi86`（五笔）

Rime 的配置是 yaml 文件，改完后点 fcitx 面板里"重新部署"生效。
配置目录：`~/.local/share/fcitx5/rime/`
抄网上的配置注意缩进（Rime 对缩进敏感）。

## 6. 一句话

> fcitx5 + Rime = 全 Wayland 兼容的中文输入栈。
> 四行环境变量 = 所有 GUI 应用都能切输入法。
> Ctrl+Space = 中英切换，fcitx5-configtool = 配置中心。

下一篇：[[05-音频-PipeWire与MPRIS]]
