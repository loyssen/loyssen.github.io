# 10 · 日常维护手册: rebuild、回滚与系统管理

> 目标:日常维护的完整命令手册——改配置、更新、回滚、清理、
> 日志排错。这篇是"肌肉记忆"篇,记住这些命令就能独立维护系统。

## 1. 改配置的标准流程

```bash
# 1. 改文件(改完先看下 diff)
git diff                      # 改动前检查
nvim modules/packages.nix     # 改配置

# 2. 构建验证(不应用!)
nixos-rebuild build --flake /home/loysan/nixos-config

# 3. 应用
sudo nixos-rebuild switch --flake /home/loysan/nixos-config

# 4. 提交(保持工作区干净——flakes 从 git 取源, 干净树更稳)
git add -A && git commit -m "feat(xxx): ..."
```

**为什么要 build 一次再 switch?** build 失败不影响系统;
switch 里 build 失败会留下半状态(profile 已动)。先验证,后应用。

## 2. 更新系统

```bash
# 更新 flake 输入(nixpkgs 等)到最新
nix flake update              # 全部输入
nix flake update nixpkgs      # 只更新一个
nix flake update nixpkgs niri # 更新多个

# 然后照常 build → switch
sudo nixos-rebuild switch --flake /home/loysan/nixos-config
```

更新后出问题?回滚(见下节)。

## 3. 回滚

```bash
# 回滚到上一个代际(最常用)
sudo nixos-rebuild switch --rollback

# 查看代际列表(记住编号)
nix-env --list-generations -p /nix/var/nix/profiles/system

# 回滚到指定代际
sudo nix-env --switch-generation 42 -p /nix/var/nix/profiles/system
sudo nixos-rebuild switch --flake /home/loysan/nixos-config  # 重建引导项
```

**NixOS 回滚是真的回滚**:配置、软件、服务全部回到那个状态的快照。
日常改崩了,rollback 三秒回家。

## 4. 垃圾清理

```bash
# 查看占用
sudo du -sh /nix/store

# 清理旧代际(保底 3 代)与孤儿包
sudo nix-collect-garbage -d

# 只清理孤儿(保留所有代际, 回滚仍可用)
sudo nix-collect-garbage
```

**注意**:`-d` 会删除旧代际,删了就回不去了。想稳妥:
- 先 `nix-env --list-generations` 确认要留哪些
- 或者不加 `-d` 只清孤儿
- **清理后第一次 rebuild 可能要重新下载/编译**(缓存被清,见 09 的教训)

## 5. 日志与排错

```bash
# 本次开机错误日志
journalctl -b -p err

# 服务状态
systemctl status nix-daemon
systemctl --failed            # 失败的服务一览

# nix 构建详细日志
nixos-rebuild build --flake . --show-trace   # 求值错误完整堆栈
nixos-rebuild build --flake . -L             # 显示构建日志(卡住时看卡在哪)

# 实时观察 nix-daemon 下载/构建
journalctl -u nix-daemon -f

# 查看某包的信息/依赖
nix path-info /run/current-system          # 当前系统闭包
nix why-depends /run/current-system <pkg>  # 为什么装了它
```

## 6. 卡住时的急救流程(血的教训)

```
switch 卡住 → 别急着 Ctrl+C 等 30 秒
  ├─ 看进程: ps aux | grep -E "git-remote|nix build|curl"
  ├─ 有 git-remote-https 高 CPU → 网络 fetch 死循环(见 09)
  │    ├─ 测: git ls-remote https://github.com/Smithay/smithay.git HEAD
  │    ├─ 不通 → 检查代理(7897 端口活着?)/切全局代理
  │    └─ 通 → 杀进程重试: sudo pkill -f "nixos-rebuild"; 重跑
  ├─ 有正常构建输出 → 只是慢, 耐心等(首次构建大包可能很久)
  └─ 什么都没有 → 等, 或看 journalctl -u nix-daemon
```

## 7. 常用系统查询

```bash
fastfetch                # 系统信息速览
nixos-version            # 当前版本
nix flake metadata .     # flake 输入状态
nix store du --path /nix/store  # 大包占用
systemctl list-timers    # 定时任务(fstrim 等)
```

## 8. 安全提示

- **不要**顺手在 root 下 `nix profile install`——绕过声明式配置
- **不要**手改 /etc/nixos 下的生成文件(hardware-configuration.nix)
- **不要**把 stateVersion 改成新版本号
- **要**保持 git 树干净(flake 构建源=git 树,脏树会有 dirty 警告)
- **要**记住:系统一切状态 = 配置 + 代际,改配置是唯一正确路径

---

*系列完。祝维护愉快——NixOS 的美妙之处在于:坏不了,回滚就行。*
