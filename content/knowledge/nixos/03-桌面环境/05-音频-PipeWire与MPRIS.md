# 05 · 音频 —— PipeWire 与 MPRIS

> 上一篇：[[04-输入法-fcitx5]] · 下一篇：[[06-主题-字体-光标]]
> 相关：[[配置详解#modules/audio.nix]]

## 1. 音频栈的三层

```
应用（amberol / netease-cloud / mpv / Firefox）
    ↓ 通过 PulseAudio 兼容接口
PipeWire（核心——取代 PulseAudio + JACK + ALSA 用户层）
    ↓ 硬件抽象
ALSA（内核音频驱动——直接跟声卡说话）
    ↓
声卡硬件
```

**老世界**：PulseAudio + JACK（各有各的协议，互相打架，延迟高）
**新世界**：PipeWire 一个进程全搞定——低延迟（Pro Audio 级别）、兼容 PulseAudio/JACK/ALSA、
视频流（screen sharing 的 PipeWire 也走这个）。

你的配置就是"关 PulseAudio → 开 PipeWire + 三个桥"：
```nix
services.pulseaudio.enable = false;
services.pipewire = {
  enable = true;
  alsa.enable = true;     # ALSA 桥（让只看 ALSA 的老程序也能出声）
  pulse.enable = true;    # PulseAudio 桥（绝大多数应用走这）
  wireplumber.enable = true;  # 会话管理器（插拔耳机/蓝牙设备自动切输出）
};
security.rtkit.enable = true;  # 实时音频线程（低延迟）
```

## 2. WirePlumber 是什么

WirePlumber = PipeWire 的**会话管理器**：管设备的生命周期。
- 插 USB 耳机 → WirePlumber 检测到 → 自动创建 sink → 通知应用可切
- 蓝牙耳机配对 → WirePlumber 管配对流程 → 注音频 profile
- 默认输出设备的选择逻辑（"插耳机就自动切过去"）

配好后很少需要手动管——音量键直接调、DMS 面板显示。

## 3. 音量控制（你已有的）

- **键盘音量键**：`XF86AudioRaiseVolume` / `XF86AudioLowerVolume` / `XF86AudioMute`
  ——这些在 niri.nix 键位里，调 `wpctl set-volume`（WirePlumber 的音量控制 CLI）
- **DMS 顶栏**：通过 MPRIS 协议显示当前播放内容 + 音量滑块
- **终端**：`wpctl status`（看全部音频节点）、`wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.5+`

## 4. MPRIS：为什么 DMS 能自动显示播放信息

MPRIS (Media Player Remote Interfacing Specification) = 桌面环境跟任何播放器通信的标准协议。
播放器（amberol / mpv / Firefox / netease / spotify）通过 dbus 广播：
- 当前歌曲/专辑/艺术家
- 播放/暂停状态
- 专辑封面

DMS 作为 MPRIS 客户端 → 自动显示当前在播什么、上一首下一首、可视化频谱。

**你的任何 MPRIS 兼容播放器都会自动出现在 DMS 顶栏**。
这就是为什么"装完 nautilus 之前打开输出目录却弹出了 amberol"
的原因根——DMS 有 MPRIS 集成，点开乐曲打开播放器。

## 5. 音频问题排障

```bash
wpctl status                  # 音频节点列表 + 当前音量
pactl info                    # PulseAudio 兼容视角看服务信息
systemctl --user status wireplumber   # 会话管理器是否正常
wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.5+   # 手动调音量
wpctl set-default <sink-id>   # 设默认输出设备
```

| 症状 | 检查 |
|---|---|
| 没声音 | `wpctl status` 看默认 sink 对不对 + 音量是不是 0 |
| 插耳机不切 | WirePlumber 自动切换规则：某些 USB DAC 需手动设 |
| 蓝牙连不上 | `bluetoothctl` + `wpctl`，查 PipeWire 的 bluez 插件 |
| 某个应用静音 | `wpctl status` 看那个应用的 stream 是不是 mute 了 |

## 6. 一句话

> PipeWire = 一个进程替代四十年音频技术栈。WirePlumber = 设备管家。
> MPRIS = DMS 自动识别你在听什么的协议。音量键 + DMS 面板 + `wpctl` 三重控制。

下一篇：[[06-主题-字体-光标]]
