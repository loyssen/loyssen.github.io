# 03 · XDG Portal 与桌面集成

> 上一篇：[[02-niri与平铺合成器]] · 下一篇：[[04-输入法-fcitx5]]
> 相关：[[配置详解#modules/portal.nix]] · [[使用说明#软件对照]]

## 1. 问题：Wayland 不让应用直接碰别的应用

X11 下任何程序可以截图屏幕、读剪贴板、弹文件对话框——安全噩梦但功能全。
Wayland 下沙箱化 → 需要**一个安全的中间人**代理这些原生能力。

Portal = **应用向系统说"我想要做 X"，系统在自己的安全域里代劳，
然后把结果给应用**。

## 2. 你的 portal 栈

```nix
xdg.portal = {
  enable = true;
  xdgOpenUsePortal = true;
  config.common.default = "gtk";          # GTK 做默认 portal backend
  extraPortals = with pkgs; [
    xdg-desktop-portal-gtk               # 文件对话框
    xdg-desktop-portal-gnome             # 录屏/截屏（niri 需要 gnome 的 screencast）
  ];
};
```

- **xdg-desktop-portal**：核心——接收请求，分发给具体 backend
- **xdg-desktop-portal-gtk**：文件选择器、打印、app chooser（默认后端）
- **xdg-desktop-portal-gnome**：**屏幕录制/截屏**（niri 没有自己实现 screencast portal，
  用 GNOME 的来做桥）

你亲历的场景：Unity 打包完选 Build 文件夹时，Unity 内部调用 `GtkFileChooserNative`
→ portal 收到请求 → xdg-desktop-portal-gtk 弹出 GTK 文件对话框 → 结果传回 Unity。

你看到的 `GLib-GIO-CRITICAL: g_dbus_proxy_call_sync_internal: assertion 'G_IS_DBUS_PROXY (proxy)' failed`
就是 Unity 的 GTK 和 portal 之间的 dbus 通信偶发异常（非致命，不影响使用）。

## 3. portal 覆盖的场景

| 操作 | 用哪个 portal |
|---|---|
| 打开/保存文件 | `org.freedesktop.portal.FileChooser` |
| 截图 | `org.freedesktop.portal.Screenshot` |
| 屏幕录制 | `org.freedesktop.portal.ScreenCast` |
| 打印 | `org.freedesktop.portal.Print` |
| 打开 URI | `org.freedesktop.portal.OpenURI` |
| 读剪贴板 | `org.freedesktop.portal.Clipboard` |
| 通知 | `org.freedesktop.portal.Notification` |

`xdgOpenUsePortal = true` → `xdg-open`（哪个程序打开文件）也走 portal。

## 4. 为什么 niri 需要 gnome portal backend（又不需要 KDE/GNOME 整个桌面）

niri 是合成器——它实现了 wlr-screencopy 协议，但 portal 的 **ScreenCast** 和后端通信
需要合成器的 PipeWire stream。GNOME 的 portal backend 能用 niri 导出的 PipeWire 节点做流。

如果哪天 niri 有了自己的 portal backend（或 wlr portal 稳定了），可以切掉 gnome 的。

## 5. 文件选择器在各应用中的表现

| 应用 | 选择器来源 |
|---|---|
| Unity Editor (GTK) | portal → gtk file chooser |
| Firefox | portal（XDG 原生） |
| kitty（终端中的 cli 工具） | 没有文件选择器，纯路径 |
| wechat/qq（Electron） | portal，可能走 KDE/GNOME 的外观 |
| WPS | portal gtk |
| blender/krita | 自带文件浏览器（不用系统文件对话框） |

## 6. portal 不是完美的

- **文件筛选器失效**：某些应用声明了文件类型过滤（"只显示 .png"），
  portal GTK 后端偶尔丢掉过滤器 → 显示所有文件
- **dbus 超时**：portal 通信走 dbus，响应慢时 `GLib-GIO-CRITICAL`
- **截屏在少数合成器上取不到**：你的 niri 目前走得通（通过 gnome backend）

## 7. 一句话

> Portal 是 Wayland 安全模型的"中间人"——安全地代理原生桌面能力。
> 你有 GTK（默认）+ GNOME（niri screencast 必须），portal 服务正常运行中。
> 文件对话框偶尔 dbus warning 没实质影响。

下一篇：[[04-输入法-fcitx5]]
