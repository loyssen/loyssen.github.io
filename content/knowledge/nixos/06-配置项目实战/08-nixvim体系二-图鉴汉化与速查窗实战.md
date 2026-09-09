# 08 · nixvim 体系(二): 图鉴汉化与速查窗实战

> 目标:深入理解仓库里两个"自研集成"——legendary 快捷键图鉴(含中文汉化
> 机制)和 keyguide 速查浮动窗口。这两块是本仓库踩坑最多、最能体现
> nixvim 定制能力的部分。

## 1. 两套工具的分工

| 工具 | 键位 | 定位 |
|---|---|---|
| **legendary 图鉴** | `<leader>?` | 全量、可搜索:所有已注册键位,回车直接执行 |
| **keyguide 速查窗** | `<leader>ck` | 浓缩、分类:日常操作速查,一屏全显 |

用哪个?想"查"用图鉴(搜索),想"背"用速查窗(分类记忆)。

## 2. legendary 集成(legendary.nix)

### 2.1 为什么用 extraPlugins?

nixvim 没有 legendary 原生模块(验证过源码,插件列表里没有)。
通用做法:

```nix
extraPlugins = with pkgs.vimPlugins; [ legendary-nvim ];
```

然后手动 `require("legendary").setup({...})`。

### 2.2 快照机制: 图鉴怎么"看到"所有键位

legendary 本身只捕获 **setup 之后**通过 `vim.keymap.set` 注册的键位。
但你的键位大部分是 nixvim 声明式生成的(在 extraConfigLua 之前就注册了),
所以要在 setup 时**主动快照**:

```lua
keymaps = function()
  local out = {}
  for _, mode in ipairs({ "n", "v" }) do
    for _, m in ipairs(vim.api.nvim_get_keymap(mode)) do
      -- 只收带 desc 的(没说明的键位进图鉴没意义)
      out[#out+1] = { m.lhs, m.rhs or m.callback, mode = mode, desc = m.desc }
    end
  end
  return out
end,
```

**关键坑 1: 打包版的格式是 v1 位置式** `{键名, 动作, desc=…}`
不是新版的 `{key=…, action=…}`。写错字段 legendary 直接启动报错
(`E5113: expected string, got nil`),这就是本仓库修过的 bug。

**关键坑 2: 顺序**——快照发生在 setup 瞬间,所以
**想进图鉴的键位必须注册在 legendary.nix 之前**(见 07 的 imports 顺序)。

### 2.3 汉化机制: 词典 + 翻译包装器

插件自带的 desc 全是英文,没有插件能统一翻译(搜过,不存在)。
方案:**包一层 vim.keymap.set,注册时把英文 desc 翻译成中文**:

```lua
local zh = {
  ["Lsp buf definition"] = "跳转定义",
  ["Lsp buf hover"] = "悬浮文档",
  ["Gitsigns next_hunk"] = "下一个变更块",
  ...
}
local function tr(desc) return zh[desc] or desc end

require("legendary").setup({...})   -- 先 setup

-- 包装器必须装在最外层: 任何键位注册先过翻译器再进 legendary/which-key
local original_set = vim.keymap.set
vim.keymap.set = function(mode, lhs, rhs, opts)
  if opts and opts.desc then opts.desc = tr(opts.desc) end
  return original_set(mode, lhs, rhs, opts)
end
```

**为什么包装器必须在 setup 之后安装?** 因为 legendary 的捕获包装器
在 setup 时接管了 vim.keymap.set。你的翻译器要套在它**外面**
(先翻译、再被 legend 捕获),顺序反了图鉴记到的就是英文。

**副产品**:nvim 的键位表里 desc 也变成中文了,which-key 提示同步汉化。
遇到新的英文键位,把原文加进 `zh` 表就行(一处维护,处处生效)。

## 3. keyguide 速查窗(keyguide.nix)

### 3.1 设计目标

- 仿 quickref.cn:分类分块 + 双列对开 + 中文说明
- **一屏全显,不用滚动**(100 列终端)
- 随用随关:q/Esc/再按 `<leader>ck` 关闭

### 3.2 结构

```
sections 数据表(11 类 × 65 条)
  ↓ render_section()  每类 → 标题行 + 条目行
  ↓ layout()          双栏(贪心高度平衡) 或 单栏
  ↓ open_guide()      浮动窗口 + extmark 高亮 + buffer 键位
```

### 3.3 双栏布局的三个坑(都是修过的 bug)

**坑 1: flatten 返回 `{lines=…, marks=…}`,取行必须 `.lines`**
`flat[1][i]` 取到的是 nil(写成 `flat[1].lines[i]`)。

**坑 2: 行必须真的 push 进数组**
双栏循环里算了 `line` 却忘了 `lines[#lines+1] = line` → 窗口全空白。

**坑 3(最经典): 字节偏移 vs 显示宽度**
```lua
-- 中文行字节数 < 显示宽度!
-- "左 下 上 右" 显示 11 格, 字节却是 15(CJK 每字 3 字节)
-- 右栏偏移必须用 #pad_left(字节), 不能写死 col_w + COLGAP(显示格)
local base = #pad_left + COLGAP
```
用显示宽度当字节偏移 → extmark 越界崩溃(`Invalid 'col': out of range`)。
**经验:CJK 环境下,extmark 的 col 永远是字节偏移,别拿显示宽度算。**

**坑 4: trunc_cells 必须匹配完整 UTF-8 字符**
`gmatch("[^\128-\191]")` 匹配的是"单字节",截断时只拼了每个汉字的首字节
→ 输出 `<e4><e4><e4>` 乱码。正确模式:`"[^\128-\191][\128-\191]*"`
(首字节 + 全部续字节 = 完整字符)。

### 3.4 一屏全显的取舍

| 手段 | 效果 |
|---|---|
| 压缩列宽(键 20 + 说明 20) | 双栏总宽 89,100 列终端可双栏(行数减半) |
| 精简数据(130→65 条) | 砍冷门项,全量键位去图鉴查 |
| 高度 95% + 无分隔线 | 双栏 44 行 < 窗口 48 行 |

**教训:一屏全显和内容量是零和的**,设计数据时先定行数预算
(11 标题 + 33 条目行 + 1 hint ≈ 45 行)。

### 3.5 调试接口

```lua
vim.g.keyguide = {
  toggle = toggle_guide,
  is_open = ...,
  buf = ...,
  sections = sections,
}
```

无头模式验证:`nvim --headless -c "lua vim.g.keyguide.toggle()" ...`
(注意:headless 下浮窗不自动聚焦,按键模拟有局限,程序化调用可验证)

## 4. 这套机制教会我们什么

1. **nixvim 的 escape hatch(extraConfigLua)足以实现任意插件级功能**,
   不一定要找现成插件
2. **中文体验是可以从数据层解决的**:desc 汉化词典 + 集中维护
3. **CJK 布局的坑是普遍的**:字节/显示宽度、UTF-8 截断,写一次记一辈子
4. **测试先行**:headless + 调试接口,验证渲染再上机

---

**下一篇**:[[09-踩坑实录-代理镜像与git死循环|09 踩坑实录]]
