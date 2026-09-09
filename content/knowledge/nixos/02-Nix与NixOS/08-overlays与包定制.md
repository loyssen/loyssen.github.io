# 08 · Overlays 与包定制

> 上一篇：[[07-配置文件组织最佳实践]] · 下一篇：[[09-运行外来二进制-nix-ld与FHS]]

## 1. Overlay 是什么

**对 nixpkgs 打补丁**——不修改原仓库，而是叠加一层自己定义的规则。

典型场景：
- 换一个包的版本（用 unstable 的版本替代 stable）
- 改了某个包的编译选项
- 加一个 nixpkgs 没有的定制包（作为 overlay 而不是独立 flake input）

你系统上有一个 live overlay：
```nix
nixpkgs.overlays = [
  (final: prev: {
    unstable = import inputs.nixpkgs-unstable {
      system = prev.stdenv.hostPlatform.system;
      config.allowUnfree = true;
    };
  })
];
```

**final** = 加完当前 overlay 后的"最终" nixpkgs（能看到自己的修改）
**prev** = 上一个"版本的" nixpkgs（加当前 overlay 之前的那个）
**一般用 prev**（避免递归循环），除非非常明确需要 final。

> [!NOTE] overlay
> 这个的实现也很特殊，比较难理解
>
> **答**：用比喻理解——overlay 就像**俄罗斯套娃的中间层**。
>
> 想象两摞字典（attrset）：基础字典（nixpkgs）→ 你叠加一页自己的纸（overlay）→ 用户看到的最终字典。
>
> `(final: prev: { ... })` 中的两个参数：
> - `prev`（前一摞）：还没有你这一层的"上一版 nixpkgs"。
>   你的 overlay 里用 `prev.xxx` 来引用"我覆盖之前的原版"。
> - `final`（最终摞）：加上你这一层之后的"最终版"。
>   理论上可以引用自己修改后的结果，但**容易死循环，极少用**。
>
> 实际工作流：overlay 等价于"给 nixpkgs 这条流水线加一个中间过滤站"——
> 所有经过这个站的包查寻都可以被你拦截、修改或转发。
> 你的 unstable overlay 就是最简单的模式：把 `pkgs.unstable` 指向另一个 nixpkgs 实例，
> 这样任何地方写 `pkgs.unstable.xxx` 都是经 overlay 转发到 unstable nixpkgs。

## 2. 你的 overlay 详解

效果：之后所有模块里 `pkgs.unstable.qq` 就拿到 unstable 版本的 qq。

之前的坏做法（每个文件各自 `let unstable = ...`） → 改一个包要在多处搜 `unstable.`。
之后的统一做法 → **一处定义，全局生效**。

## 3. 常见 overlay 模式

### 模式 A：覆盖某个包的版本
```nix
(final: prev: {
  firefox = prev.firefox.override { privacySupport = false; };
  # 或者直接替换
  kitty = prev.unstable.kitty;    # 用 unstable 的 kitty 装进 stable 环境
})
```

### 模式 B：加一个自己写的包
```nix
(final: prev: {
  myCustomScript = prev.writeShellScriptBin "myscript" ''
    echo "hello from my overlay"
  '';
})
```
然后在 packages.nix 里直接用 `pkgs.myCustomScript`。

### 模式 C：给已有包加参数
```nix
(final: prev: {
  vim-full = prev.neovim.override {
    withPython3 = true;
    withRuby = true;
  };
})
```

## 4. apply 一个补丁的例子

```nix
(final: prev: {
  hello = prev.hello.overrideAttrs (old: {
    patches = (old.patches or []) ++ [ ./my-hello-fix.patch ];
  });
})
```
`overrideAttrs` 不改变依赖，只改构建属性（源码、补丁、构建脚本等）。
`override` 不改构建，只改依赖/参数。

## 5. 顺序关系

多个 overlay → 从左到右串行应用。每个 overlay 的 prev 是前一个 overlay 的输出。

## 6. 什么时候该用 overlay vs. 直接改模块

| 场景 | 用 overlay？ |
|---|---|
| "我要在所有用到 firefox 的地方都用 unstable 版" | ✅ 全局需求 |
| "我只在这一个模块里用 unst 版本的 kitty" | ❌ 直接在 `packages.nix` 写 `pkgs.unstable.kitty` |
| "我要永久改某个包的编译选项" | ✅ |
| "临时试一下某包的新版本" | ❌ `nix shell` 或 devShell |

## 7. 查 overlay 是否生效

```bash
nix eval --impure --expr 'import <nixpkgs> { overlays = [ (final: prev: {}) ]; }''
# 不对……直接 rebuild 试——你的 overlay 在 eval 阶段就会生效，
# 如果 overlay 写错了（语法错/attribute missing）rebuild 直接报错
```

## 8. 和你踩过的坑的关系

你在 [[nixpkgs软件包踩坑]] 里踩过"legacyPackages 不带 unfree 许可"——
就是因为 overlay 里 import nixpkgs 时需要**显式传 allowUnfree**。
同样道理，给 unstable 打 overlay 的第二个参数配置必须单独给。

## 9. 一句话

> Overlay = nixpkgs 的补丁层。你的 unstable 全局 overlay 是标准做法。

下一篇：[[09-运行外来二进制-nix-ld与FHS]]
