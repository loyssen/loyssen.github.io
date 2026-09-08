# 07 · nixvim 体系(一): 模块化架构

> 目标:理解 nixvim 的定位、仓库里 nixvim 目录的组织方式、
> 插件声明与键位体系,以及 imports 顺序为什么"有讲究"。

## 1. 为什么 Neovim 也要 Nix 化?

传统 nvim 配置:lua 文件 + 插件管理器(lazy.nvim)自动下载插件。
问题:插件版本不锁定、配置不可复现、换机要重新装。

**nixvim 方案**:用 Nix 声明插件(精确到 commit)和配置,
`nixos-rebuild` 生成一个**完整的 nvim 二进制**——插件、配置、键位
全部固化在 /nix/store 里,随系统回滚。

好处:
- 插件版本锁定(flake.lock),彻底可复现
- 改配置 = 改 Nix 文件 = 不可变 + 可回滚
- 没有插件管理器(依赖关系在 Nix 层解决)

## 2. 目录结构

```
nixvim/
├── default.nix          ← 入口:启用 nixvim + imports 顺序(关键!)
├── options.nix          ← 编辑器基础选项(行号/缩进/主题…)
└── plugins/             ← 按功能分组, 每个文件一个主题
    ├── lsp.nix          ← LSP 服务器 + 键位 + C# 特调
    ├── completion.nix   ← 补全
    ├── formatting.nix   ← 格式化(conform)
    ├── linting.nix      ← 代码检查
    ├── editor.nix       ← 文件树/Oil/Telescope/Treesitter
    ├── git.nix          ← gitsigns/lazygit/diffview
    ├── ui.nix           ← 状态栏/启动页/通知
    ├── ai.nix           ← Avante + Pi/Claude 终端
    ├── debug.nix        ← DAP 调试
    ├── unity.nix        ← Unity 项目 autocmd
    ├── legendary.nix    ← 快捷键图鉴(自研集成)
    └── keyguide.nix     ← 速查浮动窗口(自研)
```

**设计思想与 modules/ 一致:按领域拆分文件**。
新增插件 = 新文件 + import 一行。

## 3. imports 顺序为什么有讲究

```nix
imports = [
  ./plugins/unity.nix
  ./plugins/keyguide.nix   # 必须在 legendary 之前!
  ./plugins/legendary.nix  # 必须最后!
];
```

**原因**:legendary 在启动时(setup)会**快照**所有已注册的、带 desc 的键位。
顺序决定了谁的键位进快照:

```
keyguide 注册 <leader>ck ──► 先进快照 ✓
legendary setup(快照) ──► 之后注册的进不了快照
legendary 包装 vim.keymap.set ──► 之后注册的键位虽然能用, 但图鉴看不到
```

所以:**需要出现在图鉴里的键位,必须注册在 legendary 之前**。
legendary 最后导入 = 所有键位都进快照。这是这个仓库排过坑的经验,
改 imports 顺序前先想清楚。

## 4. 插件声明三种形态

```nix
# 形态 1: nixvim 原生模块(推荐, 声明式)
plugins.telescope = {
  enable = true;
  keymaps."<leader>ff" = "find_files";   # 声明键位, nixvim 生成映射
};

# 形态 2: 纯 Lua 配置(需要自定义逻辑时)
extraConfigLua = ''
  local function toggle_ai(cmd) ... end
  vim.keymap.set("n", "<leader>ap", function() toggle_ai("pi") end, { desc = "Pi Agent 终端" })
'';

# 形态 3: 无原生模块的插件(如 legendary)
extraPlugins = with pkgs.vimPlugins; [ legendary-nvim ];
```

- **形态 1**:nixvim 官方支持的插件,选项齐全,优先用
- **形态 2**:escaped hatch——任何 nixvim 表达不了的逻辑(lua 函数)都走这里
- **形态 3**:nixpkgs 里有包但 nixvim 没模块,用 extraPlugins + 手动 setup

## 5. LSP 配置要点

```nix
plugins.lsp.servers = {
  nil_ls.enable = true;      # Nix
  ts_ls.enable = true;       # TypeScript/JS
  pyright.enable = true;     # Python
  rust_analyzer.enable = true;  # Rust(installCargo/Rustc 随包装)
  gopls.enable = true;       # Go
  lua_ls.enable = true;      # Lua
  bashls / jsonls / yamlls / marksman  # 常用小语言
};
plugins.lsp.keymaps = {     # 声明式 LSP 键位
  lspBuf = { "gd" = "definition"; "K" = "hover"; ... };
  diagnostic = { "<leader>k" = "open_float"; ... };
};
```

**C# 特殊处理**(`lsp.servers.roslyn_ls`):
- 用 Roslyn LS 替代 OmniSharp(更快、官方)
- `root_markers = [ "ProjectSettings" ".git" ]`:识别 Unity 项目根
  (用 vim.fs.find 不支持 glob,精确目录名才行——踩坑经验,见 04 踩坑记录)

## 6. 编辑器基础设施

| 组件 | 作用 |
|---|---|
| neo-tree + oil | 文件树 / 快速文件管理 |
| telescope + fzf-native | 模糊搜索(files/grep/buffers/键位…) |
| treesitter + textobjects | 语法高亮 / 智能文本对象 |
| conform + prettierd/black/… | 保存自动格式化(全部经 Nix 安装) |
| gitsigns + lazygit + diffview | Git 集成三件套 |
| lualine + which-key + noice + notify | 界面与提示 |
| blink.cmp + luasnip | 补全与代码片段 |

## 7. 修改键位的正确姿势

1. 原生模块支持 → 改模块的 keymaps 选项(声明式)
2. 需要 lua 函数 → extraConfigLua + `vim.keymap.set`(带中文 desc)
3. 想在图鉴里看到 → 确保注册在 legendary.nix 之前

所有 desc 用中文(which-key 和图鉴直接显示),这就是
[[08-nixvim体系二-图鉴汉化与速查窗实战|下一篇]]要讲的。

---

**下一篇**:[[08-nixvim体系二-图鉴汉化与速查窗实战|08 nixvim 体系(二)]]
