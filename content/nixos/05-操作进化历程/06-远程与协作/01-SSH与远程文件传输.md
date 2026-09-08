---
title: SSH 与远程文件传输
tags: [Linux, 进化历程, SSH, scp, rsync, mosh]
date: 2026-08-06
---

# SSH 与远程文件传输:telnet → SSH,scp → rsync

> [!info] 本页内容
> 为什么说 telnet 是"裸奔协议"?ssh/scp/rsync 各管什么?
> 远程开发场景下,SSH 怎么和 tmux 组合成日常标配。

## 一、进化史:明文 → 加密(1969 → 1995)

| 协议 | 出生 | 加密 | 现状 |
|---|---|---|---|
| **telnet** | 1969 | 无(密码明文裸奔) | 仅内网调试残留 |
| **rlogin** | 1983 | 无 | 被 ssh 淘汰 |
| **ssh-1** | 1995 | 有(算法脆弱) | 已废弃 |
| **ssh-2** | 1996 设计 / 2006 IETF 标准化 | 强加密,算法可协商 | **现役标准** |

telnet 时代的问题一句话讲完:登录时密码和内容全部明文在网络里传输,局域网里抓包就能拿到 root 密码。

1995 年,芬兰赫尔辛基理工大学的 **Tatu Ylönen** 在校园网遭遇密码嗅探攻击后,写出了 SSH(Secure Shell);1999 年 OpenBSD 推出开源的 **OpenSSH**,SSH 从此成为所有 Linux 服务器的标配——你 NixOS 上的 sshd 就是它的后代。

## 二、SSH 基础:三个必懂概念

**1. 密钥认证(替代密码)**

```bash
ssh-keygen -t ed25519 -C "loysan"   # 生成密钥对(一路回车即可)
ssh-copy-id user@server             # 把公钥装到服务器
ssh user@server                     # 从此免密登录
```

| 概念 | 说明 |
|---|---|
| 私钥 | 留在本地(`~/.ssh/id_ed25519`),永不外传 |
| 公钥 | 随便分发,放进服务器的 `~/.ssh/authorized_keys` |
| ed25519 | 现代推荐算法,比 rsa 短且快 |

**2. `~/.ssh/config` 主机别名**

```sshconfig
Host server
    HostName 192.168.1.10
    User loysan
    IdentityFile ~/.ssh/id_ed25519
```

之后 `ssh server` 一行搞定,不用再记 IP 和用户名。

**3. 文件传输三兄弟**

| 工具 | 出生 | 定位 |
|---|---|---|
| scp | 1995(随 SSH 出现) | 单次复制 |
| rsync | 1996 | 增量同步 |
| sftp | 1997 | 交互式浏览 |

## 三、常用命令表

| 场景 | 命令 |
|---|---|
| 登录远程 | `ssh server` |
| 带命令执行 | `ssh server "systemctl status"` |
| 复制文件到远程 | `scp file server:/home/loysan/` |
| 复制目录 | `scp -r dir server:/home/loysan/` |
| 增量同步目录 | `rsync -avz dir/ server:/home/loysan/dir/` |
| 同步前先演练 | `rsync -avzn --delete dir/ server:/home/loysan/dir/`(加 `n` 只试跑) |
| 端口转发 | `ssh -L 8080:localhost:80 server`(远程端口映射到本地) |

## 四、scp vs rsync

| | **scp** | **rsync** |
|---|---|---|
| 传输方式 | 整文件重传 | **增量:只传差异块**(delta 算法) |
| 断点续传 | 无 | 有 |
| 压缩 | `-C` | `-z` |
| 大量小文件 | 慢 | 快(先本地算差异) |
| 删除/权限/软链接同步 | 不支持 | `--delete --perms --links` 全支持 |
| 场景 | 偶尔拷一两个文件 | **重复同步、备份、部署** |

> [!note] 规律
> 和本系列其他篇章一样:新工具不是"更好用的 scp",而是**接口更通用、解决一类问题**——rsync 解决的是"让两边目录持续保持一致"。

## 五、tmux + SSH:远程开发标准组合

```
本地 kitty ──ssh──▶ 服务器 tmux 会话 ──▶ nvim / 构建任务
```

- 断线任务不丢:`tmux attach` 秒回现场
- 长时间任务(编译/下载/训练)挂着跑,本地关机都行
- 分屏在服务器侧,本地窗口关掉互不干扰;详见 [03-终端复用器](../01-终端/03-终端复用器.md)——核心结论:**本地日常不用 tmux,SSH 远程必用 tmux**

## 六、现今流行

- **mosh**(2012):UDP 协议,弱网/切换网络不断线,输入即时回显;代价是不支持端口转发
- **密钥认证 + ed25519 + ssh-agent**:服务器普遍禁用密码登录
- **ssh config 别名**:管几十台服务器的标配写法
- **Tailscale / ZeroTier**:组网后 `ssh hostname` 直连,不用记公网 IP
- **scp 的黄昏**:OpenSSH 9.0(2022)起 scp 默认改用 SFTP 协议,老 scp 协议已弃用

## 七、怎么选(你的环境)

你的 NixOS 已经开了 sshd(`security.nix` 里 `services.openssh.enable = true`),这台机器本身就能被远程登录:

| 场景 | 推荐 |
|---|---|
| 偶尔拷一两个文件 | scp |
| 反复同步目录 / 部署 | **rsync -avz** |
| 远程开发(SSH 到这台 NixOS 写代码) | SSH + tmux + 本地 kitty 分屏 |
| 多台机器管理 | `~/.ssh/config` 别名 + ed25519 密钥 |
| 跨网络(不在同一局域网) | Tailscale 组网后再 ssh |

> [!tip] 安全底线
> 公网机器务必:禁用密码登录(`PasswordAuthentication no`)+ 仅密钥认证 + 禁 root 直登(`PermitRootLogin no`)。
> 内网自用可以宽松些,但密钥认证一旦配好,就再也回不去密码了。
