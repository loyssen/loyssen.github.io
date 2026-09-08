# 04 · Derivation 与构建过程

> 上一篇：[[03-Nix语言入门]] · 下一篇：[[05-Flakes详解]]
> 了解"你 rebuild 时背后发生了什么"。这一篇偏理论，看懂流程即可。

## 1. Nix 的两阶段执行

| 阶段 | 做什么 | 跑在哪 | 能联网吗 |
|---|---|---|---|
| **求值（Evaluation）** | 把你的 .nix 文件算出 derivation 列表 | 你的终端 | ✅ |
| **构建（Build/Realisation）** | 按每个 derivation 的配方在沙箱里编译/组装 | 隔离沙箱（bubblewrap） | ❌（除非声明 `__noChroot`） |

你跑 `nixos-rebuild switch` 时：
1. 先求值 → 算出一个 `nixos-system-...drv`
2. 再构建这个 drv →产出 `/nix/store/...-nixos-system-...`
3. 再 activation → 切 `/run/current-system` 符号链接 + 重启服务

> [!NOTE] rebuild switch 过程
> 还是不太清楚，我只能知道这个过程是在用符号链接去指向nix/store中的具体包，接着拿这个包套入derivation沙箱，感觉说的不够清楚
>
> **答**：顺序上你反了。正确流向是"三步走"，从头到尾：
>
> 以你 rebuild 为例——
> **第 1 步 · Evaluation（求值）**：Nix 读你的所有 .nix 文件，
> 把它们挨个"化简"成一棵树标好"需要的输入→预期的输出"的**配方表**
> （derivation 的列表）。这步在你的终端跑，有网络（能下载 nixpkgs 源码，
> 只是还没编译任何东西）。产物：一堆 `.drv` 文件存在 /nix/store。
>
> **第 2 步 · Build/Realisation（构建）**：按第一份配方的顺序，
> 逐个在**沙箱**里执行（下载源码→configure→make→install）。
> 产出的二进制落到 `/nix/store/<hash>-xxx/` 下。
> 这步没网络（沙箱无网）、只看得见配方里声明的依赖。
> 对于大多数包这步是**直接下载预编译缓存**（cache.nixos.org 已经替你 build 过了），
> 所以你的 rebuild 通常不编译而是下载 .nar。
> 对于你自己的 nixos-system drv，"构建"是把所有包组装进一个系统目录
> （在 `/nix/store/` 下生成 etc/ 文件、systemd 单元、profile 脚本等——不编译任何二进制）。
>
> **第 3 步 · Activation（激活）**：系统 drv 产出后，把 `/run/current-system` 符号链接
> 切到新的系统目录，跑 activation 脚本（生成 /etc 配置、reload 有变化的 systemd 服务）。
> 这一步不到一秒，你已经在用新系统了。
>
> 比喻：evaluation = 你下单菜单。build = 厨房做菜（大部分菜已做好放冷柜，直接加热）。
> activation = 服务员端上来换掉你桌上旧的盘子。符号链接 = 桌上的号码牌指向真正那盘菜的位置。

## 2. 构建的沙箱里有什么

- 只有你在 derivation 的 `inputs` 里声明的那些路径
- 没有网络（`nix-daemon` 不让连网）
- 没有家目录、没有 /usr、没有临时文件（除非显式 mount）
- 当前目录是空的临时目录（`/build`）

这保证构建结果不受"我的机器上恰好装了某某库"的影响。
**干净得极端**——这也是为什么 nixpkgs 贡献者要特意打补丁绕过网络下载/硬编码路径等。

> [!NOTE] derivation
> 这个有点认识模糊，关于这个derivation应该是属于声名了用哪些二进制包进行一个组装包
>
> **答**：理解方向对了，但有两种 derivation，用途不同：
>
> **1. 编译型 derivation**（如 `neovim-unwrapped.drv`）：
> 配方里声明了源码在哪、用什么编译器、依赖哪些库、执行什么构建命令。
> 沙箱跑完产出 **neovim 二进制本身**。
>
> **2. 组装型 derivation**（如你的 `nixos-system-loysan.drv`）：
> 配方里**不编译任何东西**。它只是声明"取以下所有已编好的包的 store 路径，
> 生成配置文件（/etc/xxx）、生成 systemd 单元、写 PATH 环境脚本……，
> 然后把这些文件放在一起打包成一个系统目录"。
> 你的整个系统就是一个"组装 derivation"——所有子模块已编好，现在只要拼成一个系统镜像。
>
> 所以"用哪些二进制包进行组装"基本对（对于系统 derivation），
> 但对于普通包 derivation 来说它是"从源码编译生成二进制"。

## 3. 二进制缓存（Binary Cache / Substitutor）

构建完整链要数小时甚至数天。Nix 解决它：
**如果别的机器用同个 derivation 已经构建过，你直接下载产物即可**。

- `cache.nixos.org`：nixpkgs 官方 CI 为绝大多数包的 cache
- `mirrors.tuna.tsinghua.edu.cn`：你在 configuration.nix 里配的清华镜像
- Nix 先查 cache → 命中就下载（仅几 kb 的 .narinfo + 实际包体）
  → 不命中才本地构建

**为什么不是 100% cache hit**：
- 你的配置是"独一无二的哈希"（没人配过一模一样的 nixos-system）
  但里面的**子模块**（各软件包）大概率有 cache
- `nixpkgs-unstable` 的 cache 覆盖率不如 stable
- 带 unfree 且需要下载外部文件的包（qq、wpsoffice 等需要拉官方 deb）
  没有 nix binary cache（但有自己的"下载→解包"步骤而不是构建）

## 4. 什么是"构建失败"

`nixos-rebuild switch` 报错时，失败的可能是任一步：
- **parse 阶段**：.nix 文件有语法错误（少个 `}`） → 立即报，行号精确
- **eval 阶段**：无限递归、缺少 attribute → 报 `error: attribute ... missing`
- **build 阶段**：下载源码失败（404）、编译报错、check phase 失败 → 报错带完整日志路径

practical takeaway：报错先看**阶段**。语法/求值 → 查 .nix 文件。构建 → `nix log <drv-path>` 看沙箱日志。

> [!NOTE] rebuild switch 三阶段
> 构建的时候应该是有三个阶段，但并没有说明这些阶段是在干嘛，我猜parse是语法检测，eval是在计算属性值，build是根据这些值编译链接
>
> **答**：完全正确！补充一句——严格说是"两步求值+一步构建+一步激活"共四步，
> 只不过 parse 和 eval 合并称为"evaluation 阶段"，对外呈现就是三阶段。
>
> - **Parse**：纯语法检查——多一个 `}`、少一个分号在这里立即报错，行号精确；
>   连值都没算，纯语法树。
> - **Eval**：惰性求值——追每个属性到最底层，算出所有 derivation 的完整属性树；
>   无限递归、属性缺失在这里报错。
> - **Build**：derivation 进沙箱执行（编译或下载缓存）。
> - **Activation**：切符号链接 + 重启受影响的服务。
>
> Parse 和 Eval 的拆分在报错信息里很明显：syntax error（parse）vs
> `attribute ... missing` / `infinite recursion`（eval）——定位效率差很远。

## 5. fixed-output derivation

正常 derivation 的哈希**由输入决定**（输入变 → 哈希变）。
但有些东西（比如下载一个外部 tarball）没法预先知道哈希。

**fixed-output derivation**（FOD）是特例：输出哈希**预先指定**，构建只负责下载并验证。
`fetchurl`、`fetchgit` 都是 FODs。
你的 qq 包就是用 FOD 下载腾讯 deb——腾讯删了 deb → hash 不对 → 404，见 [[nixpkgs软件包踩坑]]。

## 6. 在你的系统上的直观体现

当你 `nixos-rebuild switch` 时看到的输出：

```
building '/nix/store/...-nixos-system-loysan-....drv'...
```
这是你**系统级 derivation**的构建——它本身不编译代码，而是**组装**
（收集所有包的路径、生成 etc/ 文件、生成 systemd 单元……）。

系统 derivation 的"输入"包括你的配置文件和它链接的所有包的 store 路径。
所以改配置 → 系统哈希变 → 新代际 → 原子切换。

## 7. 一句话

> 求值算出配方（drv），构建在沙箱里执行配方。缓存让这个流程 99% 是下载不是编译。
> 你的系统就是这些配方的最终产物——一个哈希确定的原子快照。

下一篇：[[05-Flakes详解]]。
