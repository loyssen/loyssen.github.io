# 04 · 中文环境: 输入法、字体与 locale

> 目标:理解中文环境的三件套(locale/输入法/字体)各自管什么,以及
> `modules/locale.nix` 的设计。顺便覆盖 audio/nvidia 两个小模块。

## 1. 三件套的分工

| 组件 | 管什么 | 不存在的后果 |
|---|---|---|
| **locale** | 系统语言、数字/日期/货币格式 | 乱码、英文界面 |
| **输入法(fcitx5)** | 中文输入(拼音/五笔/手写) | 打不了中文 |
| **字体(fontconfig)** | 界面/代码的中文字形与默认字体 | 中文显示为方块(豆腐) |

## 2. locale 配置

```nix
i18n.defaultLocale = "zh_CN.UTF-8";
```

系统默认区域:语言、时间格式等全部中文。

```nix
i18n.supportedLocales = [ "zh_CN.UTF-8/UTF-8" "en_US.UTF-8/UTF-8" ];
```

**重要**:NixOS 默认只生成 en_US locale,必须显式声明 zh_CN 才会生成。
这里保留了 en_US,是因为很多软件(终端/日志)用英文更不易乱码,
两者并存,需要时用 `LANG=en_US.UTF-8` 临时切换。

```nix
extraLocaleSettings.LC_* = "zh_CN.UTF-8";
```

把日期、货币、数字格式等全部设为中文(LC_ 系列是 POSIX 的区域设置分类)。

## 3. 输入法: fcitx5 + rime

```nix
i18n.inputMethod = {
  enable = true;
  type = "fcitx5";
  fcitx5.addons = with pkgs; [
    fcitx5-gtk               # GTK 应用支持
    fcitx5-rime              # Rime 输入法引擎(拼音/自定义词库)
    qt6Packages.fcitx5-chinese-addons   # Qt 应用支持
    qt6Packages.fcitx5-configtool       # 图形配置工具
    fcitx5-nord              # 主题(配合 nord/catppuccin 风格)
  ];
  fcitx5.waylandFrontend = true;   # Wayland 前端(本系统全 Wayland)
};
```

**为什么 Rime?** Rime 是高度可定制的输入引擎:词库、方案、快捷键全部
文本配置,和 NixOS 的哲学一致。nord 主题让输入法候选窗和桌面风格统一。

**Wayland 集成三件套**(在 niri 的环境变量里):
```
GTK_IM_MODULE=fcitx   QT_IM_MODULE=fcitx   XMODIFIERS=@im=fcitx
```
这是 GTK/Qt 应用与输入法通信的协议通道,Wayland 下 fcitx5 用
`waylandFrontend`(输入法协议)工作,三件套是给 XWayland 应用兜底的。

## 4. 字体方案

```nix
fonts.packages = with pkgs; [
  noto-fonts              # 基础西文
  noto-fonts-cjk-sans     # 中文黑体(界面)
  noto-fonts-cjk-serif    # 中文宋体(阅读)
  noto-fonts-color-emoji  # 彩色 Emoji
  nerd-fonts.jetbrains-mono  # 代码字体(带图标)
  cascadia-code           # 微软开源等宽字体
  source-han-sans         # 思源黑体
];
```

**默认字体映射**(fontconfig 决定"没指定字体时用什么"):

```nix
fontconfig.defaultFonts = {
  sansSerif = [ "Noto Sans CJK SC" "DejaVu Sans" ];     # 界面默认
  serif     = [ "Noto Serif CJK SC" "DejaVu Serif" ];    # 文档阅读
  monospace = [ "JetBrainsMono Nerd Font" "Cascadia Code" "Noto Sans Mono CJK SC" ];
  #           └─ 代码优先 JetBrainsMono ─┘ └─ 兜底 Cascadia ─┘ └─ 中文等宽兜底 ─┘
};
```

**monospace 是重点**:代码编辑器里英文用 JetBrainsMono(带 Nerd Font 图标),
中文自动落到 Noto Sans Mono CJK——这样编辑器里中英文都清晰对齐。
**顺序即优先级**,第一个装不上自动用第二个。

## 5. 顺带: audio.nix 与 nvidia.nix

### 音频(PipeWire)

```nix
services.pulseaudio.enable = false;   # 禁用旧方案
services.pipewire = {
  enable = true;
  alsa.enable = true;          # ALSA 应用(老软件)走 PipeWire
  alsa.support32Bit = true;    # 32 位 ALSA(游戏等)
  pulse.enable = true;         # PulseAudio 兼容(大多数应用)
  wireplumber.enable = true;   # 音频设备管理(音量/设备切换)
};
security.rtkit.enable = true;  # 实时调度权限(低延迟音频)
```

**一句话**:PipeWire 统一接管音频,兼容 ALSA 和 PulseAudio 两套老接口,
所有应用不用改代码就能出声。rtkit 给音频进程实时优先级,防止卡顿。

### NVIDIA(Wayland 兼容的关键)

```nix
boot.kernelParams = [
  "nvidia_drm.fbdev=1"                    # 帧缓冲(开机早期画面)
  "nvidia_drm.modeset=1"                  # 内核模式设置(Wayland 必需)
  "nvidia.NVreg_OpenRmEnableUnsupportedGpus=1"  # open 内核模块允许所有 GPU
  "nvidia.NVreg_PreserveVideoMemoryAllocations=1" # 挂起/恢复保留显存
];
boot.initrd.kernelModules = [ "nvidia" "nvidia_modeset" "nvidia_uvm" "nvidia_drm" ];
```

**`modeset=1` 是 Wayland 能跑的前提**(内核接管显卡显示模式)。
initrd 阶段就加载 nvidia 模块:防止开机到登录的闪屏/黑屏。

```nix
hardware.nvidia = {
  modesetting.enable = true;       # 模式设置(与内核参数一致)
  open = true;                     # 用 NVIDIA 开源内核模块(新驱动推荐)
  nvidiaSettings = true;           # 安装 nvidia-settings 图形面板
  package = config.boot.kernelPackages.nvidiaPackages.latest;
};
hardware.graphics.extraPackages = [ nvidia-vaapi-driver ];  # 视频硬解(VDPAU→VAAPI)
```

**open = true**:NVIDIA 的开源内核模块(仅新驱动支持),与 Wayland 兼容更好。
`nvidia-vaapi-driver` 让浏览器/播放器能用 NVIDIA 硬件解码视频。

---

**下一篇**:[[05-软件包管理-清单结构-unstable与镜像|05 软件包管理]]
