# 03 · Nix 语言入门

> 上一篇：[[02-Nix核心思想-纯函数式部署]] · 下一篇：[[04-derivation与构建过程]]
> 读你配置所需的最小子集。不是完整语言教程，是"能看懂自己的 nixos-config"。

## 1. 这是一个纯函数式、惰性、动态类型的 DSL

- **纯函数式**：没有可变变量、没有副作用（在求值阶段）
- **惰性求值**：不用的东西不计算
- **动态类型 + 强类型**：可以 `1 + "a"` 吗？报错。（但变量不写类型声明）
- **语法像 JSON + 函数**

```nix
# 注释是 # 不是 //
```

## 2. 基本类型

```nix
42                     # 整数
3.14                   # 浮点
"hello ${name}"        # 字符串（支持插值 ${}）
''多行
  字符串''             # 双单引号多行字符串
true / false           # 布尔
null
./relative/path        # 路径（自动转为绝对路径的字符串）
```

## 3. 核心数据结构：Attrset（属性集）

Nix 最常用的结构，**字典/对象/命名空间——全用它**：
```nix
{
  name = "loysan";
  age = 25;
  home = "/home/loysan";
  packages = [ "vim" "firefox" ];
}
```
取属性：`set.name` 或 `set.${"n" + "ame"}`。
多层级：`config.boot.loader.systemd-boot.enable`。

**它是 NixOS 模块的构建块**——整个 NixOS 配置就是一个巨大的嵌套 attrset。

## 4. List

```nix
[ 1 2 3 ]     # 空格分隔，不用逗号
[ "a" "b" ]
```

## 5. Let 绑定

```nix
let
  x = 1 + 2;
  name = "world";
in
"hello ${name}, result = ${toString x}"
# 结果："hello world, result = 3"
```
这就是你在 `modules/packages.nix` 里用的模式（当时每个文件各自 let unstable）。

## 6. With 语句

```nix
with pkgs; [
  kitty
  firefox
  git
]
# 等价于 [ pkgs.kitty pkgs.firefox pkgs.git ]
```
你的 `packages.nix` 全篇用这模式：`environment.systemPackages = with pkgs; [ ... ]`。

> [!NOTE] with语句
> 这个语句很常用，用来打包多个内容来作为属性，有继承的效果
>
> **答**：理解偏了一个方向——`with` 不是"继承"，而是**命名空间展开**。
> `with pkgs; expr` 的意思是"在 expr 这段代码里，pkgs 的所有属性都能直接写名字，
> 不用前缀"。相当于把 pkgs 这个 attrset 的所有 key 临时注册为当前作用域里的变量。
>
> 类比：Python 的 `from module import *`（但不推荐）。`with` 纯粹是**减少打字**，
> 不改变数据流。你的 packages.nix 里 `with pkgs; [ kitty firefox ]` 就是省去
> 每个包名前的 `pkgs.` 前缀。

## 7. 函数

```nix
# 定义
add = a: b: a + b           # 柯里化（单参数函数的链）
addOne = add 1              # 部分应用 → b: 1 + b
addOne 5                    # → 6

# 单参数函数（模式匹配：解构 attrset）
greet = { name, age }: "Hello ${name}, you are ${toString age}"

# 带默认值
greet = { name ? "world", age ? 0 }: "Hello ${name}"

# 余下参数全收进 @ 后的名字——你在 flake.nix 见过这个
outputs = { self, nixpkgs, noctalia, ... }@inputs: {
  # inputs 包含了所有传进来的参数
}
```

Nix 函数是**纯函数**：相同输入 == 相同输出，无副作用。

> [!NOTE] nix的函数
> 貌似跟其他语言的函数很不同，大括号就是一个函数，也是整个属性集合的结构
> 不过outputs这个语句的情况还是不太懂
>
> **答**：你说的"大括号就是一个函数，也是整个属性集合的结构"恰好点中了 Nix 的核心设计——
> **每个 .nix 文件都是一个函数**（它的参数由调用者注入），**这个函数的返回值必须是一个 attrset**。
>
> `{ config, pkgs, ... }: { ... }` 中：
> - 冒号左边是参数（用大括号做模式匹配 / 解构）← 这看起来像函数签名
> - 冒号右边是返回值（一个 attrset）← 这看起来像 JSON
>
> `outputs` 是 **flake 的唯一入口函数**。每个 flake.nix 必须导出 `outputs`，
> flake 系统把 `inputs`（你在 flake.nix 顶部声明的所有依赖）作为参数传给 `outputs`，
> `outputs` 根据这些输入返回一个约定格式的 attrset：
> ```nix
> {
>   nixosConfigurations.主机名 = ...;   # 对这个 flake 来说"NixOS 系统怎么构建"
>   packages.架构.包名 = ...;          # 这个 flake 可以输出自己的包
>   devShells.架构.default = ...;      # 开发环境
> }
> ```
> 类比：`outputs` ≈ 程序的 `main()` 函数——flakes 框架只认 outputs 的返回值；
> 别的名字写了也没用。你在 rebuild 时不写 `--flake ~/nixos-config#loysan` 吗？
> `#loysan` 就是指"取 outputs.nixosConfigurations.loysan 这个构建蓝图"。

## 8. Import

```nix
import ./configuration.nix       # 求值另一个 .nix 文件并返回结果（通常是函数）
imports = [ ./modules/audio.nix ./modules/niri.nix ];  # NixOS 模块系统的 import
```

注意：`imports`（复数 s）是 NixOS 模块系统的**关键字**，跟语言级的 `import`（单数）不同。
`imports` 是"把其他模块的函数结果合并进来"，这是 NixOS 模块系统特有的，
见 [[06-NixOS模块系统]]。

## 9. 递归属性集（rec）

```nix
rec {
  x = 1;
  y = x + 2;    # y 能引用同 obj 里的 x（需要 rec）
}
```

## 10. 你 flake.nix 里的实际 Nix 表达一览

```nix
{
  description = "…";                           # 字符串

  inputs = {                                    # attrset（嵌套）
    nixpkgs.url = "github:NixOS/nixpkgs/…";
    niri = {
      url = "github:sodiboo/niri-flake";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, ... }@inputs: {    # 函数（带 @ pattern）
    nixosConfigurations.loysan = nixpkgs.lib.nixosSystem {  # 大型 attrset
      system = "x86_64-linux";
      specialArgs = { inherit inputs; };        # inherit = 同名传递
      modules = [ ./configuration.nix ./hardware-configuration.nix ];
    };
  };
}
```

`inherit inputs;` 等价于 `inputs = inputs;`，就是把外层变量传入内部。

> [!NOTE] inherit 的同名传递
> 指将上一层作用域的同名属性赋值到当前作用域
>
> **答**：完全正确。`inherit x;` 是 `x = x;` 的语法糖（同名字段简写）。
> `inherit (src) x y;` 是 `x = src.x; y = src.y;` 的语法糖。
> 它只能在 attrset 构造内部使用。你的 flake.nix 里
> `specialArgs = { inherit inputs; };` 就是把外面传来的 inputs 原样传给下面的模块。

> [!NOTE] outputs 的作用是什么？
> 答：见上方"nix的函数"附答——outputs 是 flake 向外部暴露的唯一接口，
> Nix 工具链（nixos-rebuild、nix run、nix develop）都只认 outputs 下的标准键名。

## 11. 不涉及但你可能听过的

- `builtins`：内置函数集（`builtins.map`、`builtins.toString`、`builtins.readFile`……）
- `pkgs.lib`：Nixpkgs 工具库（`lib.mkOption`、`lib.mkIf`、`lib.mkDefault`……）
  ——见 [[06-NixOS模块系统]]
- `...`（省略模式）："还有别的参数我不管"，在函数参数和解构中表示不关心剩余部分
- `?` 运算符：`attrset ? key` 测试键是否存在

## 12. 你就是这么写的：最小实操

打开你的 `~/nixos-config/configuration.nix`：
```nix
{ config, pkgs, inputs, ... }:   # ← 函数定义（参数从模块系统传入）
{
  imports = [ ./modules/... ];    # ← modules 的 attrset（带 imports 关键字）
  networking.hostName = "loysan"; # ← 系统 option 的值
  nixpkgs.config.allowUnfree = true;

  users.users.loysan = {          # ← 用户配置（嵌套 attrset）
    isNormalUser = true;
    extraGroups = [ "wheel" "video" ];
  };
}
```
现在你应该能逐行看懂上面是什么了。

下一篇：[[04-derivation与构建过程]]。

