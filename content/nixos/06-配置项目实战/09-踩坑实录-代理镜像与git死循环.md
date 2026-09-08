# 09 · 踩坑实录: 代理、镜像与 git 死循环

> 目标:记录一次真实的故障排查全流程——`nixos-rebuild switch` 卡死,
> 根因是代理对 git HTTP/2 的 TLS 握手失败。这篇的方法论
> (症状 → 定位 → 假设 → 验证 → 修复)对任何网络类问题都适用。

## 1. 事故描述

```
$ sudo nixos-rebuild switch --flake /home/loysan/nixos-config
warning: Git tree ... is dirty
building the system configuration...
(卡住不动, 几分钟无输出)
```

## 2. 排查方法论(关键步骤)

### 2.1 先看进程,别瞎等

```bash
ps aux | grep -E "nixos-rebuild|git-remote|git ls-remote"
```

发现:
```
root  git-remote-https https://github.com/Smithay/smithay.git   ← 99% CPU, 3 分钟+
```

**高 CPU 的 git 进程 = 死循环重试**(不是等待——等待时 CPU 很低)。

### 2.2 搞清楚它在干什么

`git ls-remote` 是在**求值阶段拉取 flake 输入**:
niri 的依赖 Smithay(git 仓库),之前的 fetch 缓存被 `nix-collect-garbage`
清掉了,现在要重新拉。

### 2.3 定位网络环节(逐段测试)

```bash
# 测试 1: 走代理的 git(与 nix-daemon 环境一致)
git ls-remote https://github.com/Smithay/smithay.git HEAD
# → 致命错误: TLS connect error: SSL routines::reason(1000)   ← 找到了!

# 测试 2: 分变量验证(HTTP 版本 / 代理开关)
git -c http.version=HTTP/1.1 ls-remote ...   # ✅ 通!
env -u https_proxy git ls-remote ...         # ✅ 也通(直连)
curl -sI https://github.com                   # ✅ 通
```

**结论矩阵**:
| 组合 | 结果 |
|---|---|
| HTTP/2 + 代理 | ❌ TLS 握手失败 |
| HTTP/1.1 + 代理 | ✅ |
| 直连 | ✅ |

→ 根因:**代理(mihomo)对 git 的 HTTP/2 协商有问题**。
git 的 libcurl 在 TLS 握手失败后疯狂重试,表现为高 CPU 卡死。

## 3. 修复(三层防护)

### 层 1: daemon 环境变量

```nix
systemd.services.nix-daemon.environment = {
  GIT_HTTP_VERSION = "HTTP/1.1";
};
```

### 层 2: 全局 gitconfig(兜底,最重要)

```nix
environment.etc."gitconfig".text = ''
  [http]
    version = HTTP/1.1
'';
```

**为什么必须全局?** 踩过第二次坑才知道:
- nix-daemon 的 env 只管 **daemon 内**的 fetch(构建时)
- 但**求值阶段的 git fetch 跑在 nixos-rebuild 客户端进程里**,不继承 daemon env
- 只有全局 git 配置能覆盖所有 git 进程

### 层 3: 网络层

- 切 Clash 全局代理模式也可绕过(实测 HTTP/2 恢复)
- 直连也通(本机网络环境允许时)

## 4. 其他网络类坑(本仓库实战)

### 4.1 换镜像不生效?

substituters 顺序 = 询问顺序。改配置后需要 rebuild 生效。
镜像挂了?`curl -I` 测连通,换个顺序或删掉。

### 4.2 下载慢

```bash
# 看实际走的哪个源
nix build ... --print-build-logs -v  # 或观察 nix-daemon 日志
journalctl -u nix-daemon -f
```

### 4.3 求值卡死 vs 构建卡死的区分

| 阶段 | 症状 | 看什么 |
|---|---|---|
| 求值卡死 | "building the system configuration..." 后无动静 | `git-remote` 进程(拉 flake 输入) |
| 构建卡死 | 有 `building '...drv'...` 行但不推进 | 该 drv 的依赖下载/编译 |

### 4.4 断网时怎么干活?

```bash
# 所有输入已在 store 时, 离线也能 build(不 fetch)
# 先确保 lock 的输入都在: nix flake lock --update-input ... 提前做
```

## 5. 教训总结

1. **卡住先看进程**,`ps` 一眼定位(高 CPU 的 git = 网络死循环)
2. **环境变量有作用域**:daemon env ≠ 客户端进程 env,全局配置才兜底
3. **代理对 HTTP 版本敏感**:TLS 握手失败时试试 HTTP/1.1 或直连,快速二分
4. **修复要三层**:daemon + 全局配置 + 网络层,缺一不可
5. **遇到相似问题先跑诊断命令**:
   ```bash
   git ls-remote https://github.com/Smithay/smithay.git HEAD
   # 通 → 网络正常; 不通 → 逐层二分(代理/版本/直连)
   ```

---

**下一篇**:[[10-日常维护手册-rebuild与系统管理|10 日常维护手册]]
