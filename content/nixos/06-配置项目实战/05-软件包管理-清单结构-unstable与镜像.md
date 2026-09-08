# 05 · 软件包管理: 清单结构、unstable 与镜像

> 目标:理解 `modules/packages.nix` 的组织方式、`pkgs.unstable` 的正确用法、
> 包去哪了(镜像/缓存),以及常见"包问题"的解法。

## 1. 包清单的组织

```nix
environment.systemPackages = with pkgs; [
  kitty           # 终端
  firefox         # 浏览器
  fuzzel          # 启动器
  starship        # 提示符
  ...
];
```

**systemPackages = 装到系统 PATH 里的软件**。所有用户都能用,随系统回滚。

组织原则(这个仓库的做法):
- **按用途分组注释**:终端/浏览器/开发/网络/媒体/系统工具/办公/创作/娱乐…
- **每个包一行注释**:做什么 + 为什么选它(对比项写在注释里,如
  `bat = cat 增强`、`fd = find 的现代替代`)
- **有故事的包写详细注释**:如 `xwayland-satellite`(为什么不用整机 XWayland)、
  `crow-translate`(pot 被移除的替代)、`qq`(为什么必须 unstable)

**为什么注释比包本身重要?** 半年后回来改配置,看到包名猜不出用途;
有注释就能直接判断"这个还用不用"。

## 2. 三种取包方式(重要!)

```nix
kitty                          # 方式 1: 稳定版 nixpkgs(默认)
pkgs.unstable.qq               # 方式 2: 不稳定版 nixpkgs
inputs.noctalia.packages.${system}.default   # 方式 3: flake 输入里的包
```

| 方式 | 适用场景 | 风险 |
|---|---|---|
| 稳定版 | 绝大多数软件 | 版本旧(25.11 分支) |
| `pkgs.unstable` | 稳定版缺失/太旧/已下架(QQ) | 更新快,可能不稳定 |
| flake 输入 | 特殊项目包(Noctalia、niri、DMS) | 依赖上游仓库 |

**什么时候用 unstable?** 三条经验:
1. 稳定版里**没有**这个包(pi-coding-agent)
2. 稳定版里的包**坏了**(QQ 的 deb 被腾讯下架,源里 404)
3. 需要新版本特性(某些工具链)

`pkgs.unstable` 怎么来的?见 configuration.nix 的 overlays 段
(不稳定 nixpkgs 挂到 pkgs.unstable 名下)。

## 3. 包是从哪下载的?

```
nixos-rebuild switch
  └─ 需要的包已经在 /nix/store? ──是──► 直接用
  └─ 否 ──► 问二进制缓存(substituters)
              ├─ 清华镜像(快,国内)
              ├─ 中科大镜像(备用)
              └─ cache.nixos.org(官方兜底)
           ── 都没有 ──► 本地编译(慢)
```

- 镜像源顺序在 configuration.nix 的 `nix.settings.substituters`
- 没进缓存的包才本地编译(如 niri、DMS 这类 flake 包)
- **换镜像/加镜像不需要重装任何东西**,改配置 rebuild 即可

## 4. 常见"包问题"与解法

| 症状 | 原因 | 解法 |
|---|---|---|
| `attribute 'xxx' missing` | 包名不对/该版本没有 | `nix search nixpkgs xxx` 查正确名 |
| unfree 报错 | 没开 allowUnfree | configuration.nix 已全局开启,检查拼写 |
| 下载 404 | 上游下架(QQ 案例) | 换 `pkgs.unstable.xxx` 或换包 |
| 依赖冲突 | 两套 nixpkgs 混用 | 用 `follows` 统一(见 flake.nix) |
| 包行为异常 | 版本太旧 | 考虑 unstable 或等待稳定分支更新 |

## 5. 装包的正确流程

```bash
# 1. 搜索确认包名
nix search nixpkgs chromium

# 2. 加进 packages.nix(带注释!)
nvim modules/packages.nix

# 3. 构建验证 → 切换
nixos-rebuild build --flake /home/loysan/nixos-config
sudo nixos-rebuild switch --flake /home/loysan/nixos-config
```

**重要**:别用 `nix profile install` 装系统包——那样不受 systemPackages
管理,也不随系统回滚。一切包都从配置里声明。

## 6. 本仓库的特殊包

- **Noctalia / niri / DMS / quickshell**:flake 输入直接打包(比 nixpkgs 新)
- **DMS**:用 `pkgs.unstable` 构建(兼容 GOPROXY 传递)
- **xwayland-satellite**:按需启动的独立 XWayland(Unity 用),不常驻省资源
- **OCR 三件套**:grim(截图) + slurp(选区) + tesseract(识别) + wl-clipboard

---

**下一篇**:[[06-安全与开发环境-nix-ld与Unity|06 安全与开发环境]]
