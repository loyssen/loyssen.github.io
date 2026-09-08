# 04 · Shell 与终端基本功

> 上一篇：[[03-文件系统与目录结构]] · 下一篇：[[05-用户与权限]]
> 终端是 Linux 的"控制面板"。这一篇覆盖日常 90% 的使用。

## 1. 概念澄清：终端 ≠ Shell

- **终端（terminal emulator）**：窗口程序本身。你用的 **kitty**
  （≈ Windows Terminal、cmd 窗口）
- **Shell**：终端里跑的解释器，解析你输入的命令。你用的 **bash**
  （≈ cmd / PowerShell 的角色）
- 提示符里跑着 **starship**（那个好看的提示符主题）

## 2. 命令的基本结构

```bash
命令  [选项]  [参数]
ls    -la     ~/Projects
│      │       └─ 参数：对谁操作
│      └─ 选项：怎么操作（-短选项 / --长选项）
└─ 命令：做什么
```

- `命令 --help`：任何命令的内置说明书
- `man 命令`：完整手册（q 退出）。太硬核？用 `tldr 命令`（简版示例）
- **Tab 补全**：按 Tab 自动补命令/路径，按两次列出候选——省一半打字量
- `Ctrl+C`：中断当前命令；`Ctrl+D`：退出 shell
- `!!`：重复上一条命令（`sudo !!` = 用 sudo 重跑上一条，超常用）

## 3. 管道 |：Unix 哲学的精髓

把上一个命令的**输出**当下一个命令的**输入**：
```bash
journalctl --user -u anime-wallpaper | grep -i error     # 日志里筛错误
ps aux | grep unity                                       # 进程里找 unity
history | grep rebuild                                    # 历史里搜命令
cat big.log | head -20                                    # 只看前 20 行
```
每个小程序只干一件事，管道把它们组合成流水线。这就是"小工具组合"哲学。

## 4. 重定向：输出去哪

```bash
命令 > 文件       # 输出写入文件（覆盖）
命令 >> 文件      # 追加
命令 2> 文件      # 只把错误写入文件（2 = 错误流）
命令 > 文件 2>&1  # 输出+错误都写入
命令 < 文件       # 从文件读输入
命令 | tee 文件   # 既显示又写文件（看 rebuild 日志用）
```

## 5. 环境变量：系统的"全局设置"

```bash
echo $PATH          # 命令搜索路径（最重要的变量）
echo $HOME          # 家目录
env                 # 列出全部环境变量
export FOO=bar      # 设置（仅当前 shell 会话）
```

**PATH 的工作方式**：你敲 `nvim`，shell 按 PATH 里的目录顺序找名为 nvim 的可执行文件。
你的 PATH：
```
/run/wrappers/bin
~/.nix-profile/bin
/etc/profiles/per-user/loysan/bin
/nix/var/nix/profiles/default/bin
/run/current-system/sw/bin     ← 系统软件都在这（符号链接农场）
```
`which nvim` 告诉你实际命中哪个。
**这就是 Unity 检测 nvim 的原理**（`which nvim`）——见 [[Unity开发踩坑]]。

永久设置环境变量：NixOS 里写 `environment.variables` 或 niri 的 environment 块
（不要乱写 ~/.bashrc，NixOS 有更声明式的方式）。

## 6. 你的现代化工具箱（已装好，比默认命令好用）

| 默认命令 | 你的替代品 | 亮点 |
|---|---|---|
| `ls` | `lsd` | 图标+颜色+目录优先 |
| `cat` | `bat` | 语法高亮+行号+git 标记 |
| `grep` | `rg 关键词` | 快 10 倍，自动跳过 .git |
| `find` | `fd 关键词` | 语法简单，默认忽略隐藏 |
| `cd` | `z 关键词` | zoxide：记住你去过的目录，`z unity` 直接跳 |
| 历史搜索 | `Ctrl+R` | fzf 模糊搜历史命令（超好用，必学） |
| 任务管理器 | `btop` | 漂亮的全屏监控 |
| 系统信息 | `fastfetch` | 开机晒图那个 |

## 7. 文件管理双雄

- **yazi**（TUI）：`yazi` 启动。hjkl 移动、回车进入、空格选中、
  `y`复制 `x`剪切 `p`粘贴 `d`删除、`q` 退出、`:shell` 执行命令
- **nautilus**（GUI）：鼠标党用。两者不冲突，按场景选。

## 8. 后台与任务控制

```bash
命令 &              # 后台运行
Ctrl+Z             # 暂停当前任务并挂到后台
jobs               # 看后台任务
fg                 # 拉回前台
nohup 命令 &       # 关掉终端也继续跑
```

## 9. 实用碎片

```bash
Ctrl+L             # 清屏（≈ cls）
Ctrl+A / Ctrl+E    # 光标到行首/行尾
Ctrl+W             # 删一个词
Ctrl+U             # 删整行
mkdir -p a/b/c     # 一次建多级目录
touch 文件          # 建空文件/刷新时间
ln -s 目标 链接名   # 建符号链接（≈ 快捷方式，但更底层）
tar -xf 包.tar.gz  # 解压 tar 系
7z x 包.7z         # 解压 7z（已装 p7zip）
```

## 10. 新手三大安全守则

1. `rm` 没有回收站。删前 `ls` 确认，批量删除先用 `echo` 试跑：
   `echo rm *.bak` → 确认展开对 → 去掉 echo 真跑
2. `sudo` 前三思。问"这条命令为什么要管理员？"
3. 网上的 `curl ... | sh` 别直接跑。先看脚本内容。
   NixOS 上优先找 nixpkgs 里有没有对应包。

下一篇：[[05-用户与权限]]。
