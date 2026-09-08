# Unity 开发踩坑记录

> 2026-07-26 配置 Unity 2022.3.62f3c1 + Neovim 工作流的完整踩坑过程。
> 每一个坑都花了实际时间排查，症状→根因→修法全记录。

## 坑 1：Unity 设置每次重启全部丢失

**症状**：External Script Editor、窗口布局等设置，关闭 Unity 重开后全部重置。

**排查**：strace 跟踪 Unity 启动，发现：
```
openat("~/.local/share/unity3d/prefs", O_RDONLY) = ENOENT          # 读不到
openat("~/.local/share/unity3d/prefs", O_WRONLY|O_CREAT) = ENOENT  # 写也失败！
```

**根因**：**两层**。
1. EditorPrefs 在 Linux 上的真实路径是 `~/.local/share/unity3d/prefs`
   （不是 `~/.config/unity3d/prefs`！后者是 Unity Hub 自己的。
   网上很多资料写错，官方文档才是准的）
2. `~/.local/share/unity3d/` **目录本身不存在**，Unity 不会自动创建它
   → 每次退出保存 EditorPrefs 都静默失败。这是 ArchWiki 记载的已知 bug。

**修法**：
```bash
mkdir -p ~/.local/share/unity3d
```
一劳永逸。此后设置正常持久化。

**教训**：Linux 上"设置不保存"类问题，先 strace 看进程实际读写哪个文件：
```bash
strace -f -e trace=openat -o /tmp/trace.log <程序>
grep prefs /tmp/trace.log
```

## 坑 2：walcht neovim 包检测不到终端，下拉没有 Neovim

**症状**：装了 `com.walcht.ide.neovim` 包，但 Unity 的 External Script Editor
下拉里没有 Neovim，Editor.log 报 `no valid terminal launcher is available`。

**根因**：读包源码（`Library/PackageCache/com.walcht.ide.neovim@*/Editor/NeovimCodeEditor.cs`）
发现 Linux 下硬编码终端列表只有 `gnome-terminal/alacritty/ptyxis/xterm/ghostty` ——
**kitty 只在 macOS 列表里**（作者笔误或疏忽）。
检测失败 → `SetDefaults()` return false → 静态构造函数提前返回 →
`CodeEditor.Register()` 永远执行不到 → 下拉永远空。
连锁反应：点 Regenerate project files 也报 NullReferenceException
（`s_Generator` 在 SetDefaults 成功后才创建）。

**修法**：预写 EditorPrefs 绕过检测（在 Unity 关闭时写
`~/.local/share/unity3d/prefs`）：
- `NvimUnityConfigJson`：TermLaunchCmd 用**绝对路径** `/run/current-system/sw/bin/kitty`
  （跳过 `which` 检测），nvim 路径 `/run/current-system/sw/bin/nvim`
  （稳定符号链接，**勿用 /nix/store 实际路径**，rebuild 后会变）
- `kScriptsDefaultApp` = nvim 路径（预选外部编辑器）
- prefs XML 里 string 值是 **base64(UTF-8)** 编码

**教训**：Unity 包出问题，源码就在 `Library/PackageCache/` 里，直接读。
Editor.log（`~/.config/unity3d/Editor.log`）是第一现场。

## 坑 3：nvim 里 C# LSP 永远不 attach

**症状**：roslyn_ls 配了但 `:LspInfo` 无客户端。

**根因（两个叠加）**：
1. Unity 没生成 .sln/.csproj（坑 2 导致 csproj 生成功能没启用）
2. nixvim 配置写了 `root_markers = [ "*.sln" "*.csproj" ".git" ]` ——
   **nvim 0.11 的 root_markers 走 `vim.fs.find()`，只匹配精确文件名，不支持 glob**。
   `*.sln` 永远匹配不到 `TestLinux.sln`。项目不是 git 仓库时 `.git` 也没有 → 全灭。

**修法**：每个 Unity 项目根必有 `ProjectSettings/` 目录（精确名）：
```nix
root_markers = [ "ProjectSettings" ".git" ];
```

**教训**：LSP 不 attach 先查 root_dir 检测：
`:lua print(vim.inspect(vim.lsp.get_clients()))`

## 坑 4：打包的游戏风扇狂转但不出窗口

**症状**：双击 `TestGame.x86_64`，进程起来了（风扇转），无窗口。
Player.log（`~/.config/unity3d/<公司名>/<项目名>/Player.log`）：
`Error getting num native displays: Video subsystem has not been initialized`

**排查**：strace 发现一堆 ENOENT：
```
libX11.so.6, libXcursor.so.1, libXrandr.so.2, libwayland-client.so.0,
libxkbcommon.so.0, libdbus-1.so.3 ... 全部找不到
```
注意 `libGL.so.1` 反而不在缺失列表早期——它连显示服务器客户端库都没加载到。

**根因**：NixOS 没有 `/usr/lib`。外来二进制靠 nix-ld 找库，但 nix-ld 默认库集合
（zlib/openssl/systemd 等）**不含 X11/Wayland 客户端库**。
GL 另有一层：`/run/opengl-driver/lib` 只有 GLVND **vendor** 库
（libGLX_nvidia/libEGL_mesa），调度层 `libGL.so.1` 本体来自 nixpkgs `libglvnd`。

**修法**（modules/unity.nix）：
```nix
programs.nix-ld.libraries = with pkgs; [
  libglvnd mesa
  xorg.libX11 xorg.libXcursor xorg.libXext xorg.libXi
  xorg.libXinerama xorg.libXrandr xorg.libXScrnSaver xorg.libXxf86vm
  wayland libxkbcommon dbus
];
```
追加语义（自动合并默认集合）。此后外来二进制双击即跑。

**教训**：NixOS 上外来二进制跑不起来，99% 是缺库。诊断套路：
```bash
strace -f -e trace=openat <程序> 2>&1 | grep "ENOENT.*\.so" | sort -u
```
缺什么往 nix-ld.libraries 补什么。

## 坑 5：Unity Hub 启动的 Editor 和普通 shell 环境不同

**根因**：nixpkgs 的 unityhub 在 **bubblewrap FHS 沙箱**里运行
（有自己的 /usr、/etc/ld.so.cache），Editor 由 Hub 启动、继承沙箱视图。
所以直接在终端跑 Editor 二进制会报 `libGL.so.1: cannot open shared object file`，
而从 Hub 启动就正常。另外 Unity Hub 3.x 会**丢弃部分环境变量**（已知 Unity 侧问题）。

**修法**：正常用 Hub 启动即可。如需命令行直启 Editor：
```bash
LD_LIBRARY_PATH=/usr/lib \
  /nix/store/...-unityhub-fhs-env-*/bin/unityhub-fhs-env \
  ~/Unity/Hub/Editor/<版本>/Editor/Unity -projectpath <项目>
```

## 坑 6：打包对话框"保存"按钮是灰的

**症状**：Build 后选好文件夹，保存按钮灰色不可点。

**根因**：不是 bug——Unity 的打包对话框是**保存文件**对话框，
必须在顶部"名称"框**输入可执行文件名**（如 `TestGame.x86_64`），按钮才亮。

## 坑 7：打包完自动打开 amberol 音乐播放器

**根因**：Unity 打包完调用 `xdg-open <输出目录>` 展示产物。
系统没装文件管理器时，`inode/directory` 的默认关联落到了 Amberol
（音乐播放器注册了"打开音乐文件夹"）。

**修法**：装 nautilus + `xdg-mime default org.gnome.Nautilus.desktop inode/directory`。

## 坑 8：pkill 误杀自己（Claude 侧）

**症状**：`pkill -f TestGame` 后整个 shell 会话死掉，exit 144。

**根因**：`pkill -f` 匹配完整命令行——当前 shell 的命令行里恰好含 "TestGame"
字样（在 eval 字符串里），把自己杀了。

**修法**：用 `pkill -x <精确进程名>`，或先 `pgrep -af` 确认匹配范围。
