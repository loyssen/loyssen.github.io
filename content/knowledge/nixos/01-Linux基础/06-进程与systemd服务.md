# 06 · 进程与 systemd 服务

> 上一篇：[[05-用户与权限]] · 下一篇：[[07-软件包管理的演进]]
> 对应 Windows 的"任务管理器 + 服务 (services.msc)"，但强大得多。

## 1. 进程：运行中的程序

```bash
btop                 # 你的"任务管理器"（全屏可视化，必会）
ps aux | head        # 进程快照
pgrep -af unity      # 按名字找进程（-a 显示完整命令行，排查神器）
kill PID             # 礼貌结束（发 SIGTERM）
kill -9 PID          # 强制杀死（SIGKILL，最后手段）
pkill -x 名字         # 按精确进程名杀
killall 名字          # 杀掉所有同名（已装）
```

**信号常识**：
- SIGTERM（15）："请你退出"——程序有机会存盘清理
- SIGKILL（9）："立即死"——没商量，可能丢数据/留 swap 文件
  （你在 nvim 遇到的 swap 提示就是这个原因：nvim 被强杀留了 .swp）
- `Ctrl+C` = SIGINT（2）：终端里的"打断"

⚠️ 亲身踩过的坑：`pkill -f xxx` 匹配**完整命令行**——如果你的 shell 命令行里
也含 xxx 字样，会把自己杀了。优先用 `pkill -x` 或先 `pgrep -af` 看会匹配到什么。

## 2. 前台/后台

```bash
命令 &        # 直接在后台启动
Ctrl+Z       # 暂停并挂后台
jobs / fg / bg
nohup 命令 &  # 终端关了继续跑
```

## 3. systemd：系统的"总管家"

systemd 是 Linux 的 init 系统（1 号进程），管：开机启动什么、服务生命周期、
日志、定时器、设备挂载…… Windows 对应物≈服务管理器+任务计划+事件查看器合体。

### 单元（unit）的类型
| 类型 | 作用 | 例子 |
|---|---|---|
| `.service` | 一个服务 | sshd、NetworkManager |
| `.timer` | 定时触发（≈ 任务计划） | anime-wallpaper.timer |
| `.socket` | 套接字激活 | pipewire.socket |
| `.target` | 一组单元的集合点（≈ 运行级别） | graphical-session.target |

### 两个世界：系统服务 vs 用户服务
```bash
systemctl ...              # 系统服务（root 管，开机就有）
systemctl --user ...       # 你的用户服务（登录后才有，不需 sudo）
```
你系统里的例子：
- 系统：nix-daemon、NetworkManager、sshd、sddm
- 用户：opentabletdriver、anime-wallpaper、lxqt-policykit-agent、pipewire

## 4. systemctl 日常命令

```bash
systemctl status 服务名        # 状态+最近日志（第一诊断命令）
systemctl start/stop 服务名    # 启停（当前生效）
systemctl restart 服务名       # 重启
systemctl enable 服务名        # 开机自启（下次开机生效）
systemctl disable 服务名
systemctl enable --now 服务名  # 自启+立刻启动（一步到位）
systemctl daemon-reload       # 改了服务文件后重新加载
systemctl --failed            # ★ 看谁挂了（系统体检）
systemctl --user --failed     # ★ 用户级体检
systemctl list-timers         # 看所有定时任务
systemctl reset-failed 服务名  # 清除失败标记
```

你亲历的应用：anime-wallpaper 服务老报 failed → 脚本把"搜索无结果"
当失败退出 → 改 exit 0 → `reset-failed` 清状态 → `--failed` 恢复干净。

## 5. journalctl：日志中心

所有 systemd 管的程序，日志都进 **journal**（二进制日志，不用翻 /var/log 文件）：

```bash
journalctl -b                 # 本次启动以来的全部日志
journalctl -b -p err          # 只看 error 以上级别
journalctl -u 服务名           # 某服务的日志
journalctl --user -u 服务名    # 用户服务日志
journalctl -f                 # 实时滚动（≈ tail -f）
journalctl --since "10 min ago"  # 最近 10 分钟
journalctl -k                 # 内核日志（驱动/硬件问题）
```

**排障套路**：服务起不来 → `systemctl status` 看退出码 →
`journalctl -u` 看详细输出 → 修 → `daemon-reload` → `restart`。

## 6. NixOS 声明服务（不用手写 unit 文件）

传统发行版要手写 /etc/systemd/system/xxx.service。
NixOS 直接在配置里声明（你的 security.nix 就是活例子）：

```nix
systemd.user.services.lxqt-policykit-agent = {
  description = "LXQt PolicyKit Authentication Agent";
  wantedBy = [ "graphical-session.target" ];   # 图形会话起来时启动
  after = [ "graphical-session.target" ];
  serviceConfig = {
    Type = "simple";
    ExecStart = "${pkgs.lxqt.lxqt-policykit}/bin/lxqt-policykit-agent";
    Restart = "on-failure";
  };
};
```
rebuild 后 systemd 单元自动生成。**配置即文档**。

## 7. 查看开机为什么慢（备用）

```bash
systemd-analyze              # 总耗时
systemd-analyze blame        # 各环节耗时排行
systemd-analyze critical-chain  # 关键路径
```

## 8. 一句话总结

> 进程用 `btop`/`pgrep` 看，服务用 `systemctl` 管，日志用 `journalctl` 查。
> 三件套记牢，Linux 上 90% 的"程序怎么了"都能自己定位。

下一篇：[[07-软件包管理的演进]]。
