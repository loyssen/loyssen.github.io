# 配置数据使用指南

> 本文件面向使用者（策划/工程师/负责人）：怎么改数据、怎么落地、坏了怎么查。管线技术细节见各脚本头部注释。
> 所有命令/路径均相对**文档库根**（本 README 所在的库根目录），整套工具自定位、无机器绑定，可随库整体迁移共享。

## 策划数据工作流（多维表格时代）

游戏数据的编辑源是 **Obsidian 多维表格**（`GameData/DuoWei/*.duowei`），需求表达采用**文表配合**：表格承载数据，GamePlan 文档承载规则与意图。

```
策划（多维表格定义数据 + GamePlan 文档描述需求）
    → 主程（根据文表需求设计实现，GameDD 设计）
    → 工程师（按设计落地）
数据落地管线：多维表格 → duowei_export 直出 → 游戏（策划可自助，或由工程侧执行）
```

- 「游戏数据」「游戏事件」两张字典表：策划可自由增加全局数据项 / 事件定义（供条件 propertyPath、监听 listenEvent 引用）
- 游戏物体数据（鱼种 / 群阵 / 关卡 + 事件时序等 11 表）：策划在多维表格直接编辑
- 策划机只需 Obsidian + git（编辑 .duowei → commit/push）；管线执行与机台部署集中在开发机——开发机跑管线前先 git pull 拿最新数据，策划改完 push 后知会开发侧

## 一页速查（文档库根执行）

```bash
# 日常落地直出（.duowei → json + C#，零中间表格；配置=GameData/tools/config.json）
uv run GameData/tools/Program/duowei_export.py
```

**导出范围 = 类名映射登记表**（`GameData/DuoWei/类名映射.duowei`）：登记了「表名→类名」的表即导出 json+C#（未登记表按明细/字典/记录类型等辅助分类消费）——新增导出表只需在映射表加一行，工具与配置零改动（config 的 `tables` 表名清单已废除）。

字段类型定制：多维表格字段名加 `>类型` 后缀可直接指定输出成员的 C# 类型（如 `Duration>float`、`Points>List<Vector2>`，json 值同步按该类型转换）；单选列（singleSelect）的 `>类型` 后缀以该名生成枚举（源列选项=枚举成员，如 `op>CompareOp`）；「游戏事件/游戏数据」表中的类型源列（singleSelect，选项含 整型/单精度小数 等基础类型词）决定成员类型——基础词映射基础类型、ASCII 标识符原样作为类型名。

> 日常配置编辑与导出推荐走**导出工具**：Obsidian 侧边栏 ▶「数据管线启动器」静默启动本地服务（或双击 `GameData/tools/Program/start.bat`；http://127.0.0.1:8712）——同一服务同时提供导出配置编辑（View/导出工具.html）、一键导出与阵型/路径点位编辑（编辑器经该服务读写 .duowei）。

## 日常编辑流程

### 场景 A：我想改鱼种/群阵/关卡/事件数据（数值/文本类）

1. **Obsidian 编辑多维表格**：打开 `GameData/DuoWei/` 对应表直接改行。11 表清单：

| 表 | 用途 |
|----|------|
| 鱼种 | 鱼基础属性（体积/概率/速度/等级/路径绑定/RefName 唯一标识） |
| 群阵 | 生成组（鱼种×数量×路径×速度×阵型引用） |
| 关卡 | 关卡参数（时长/场景/下一关/解锁人群/Profile 参数） |
| TImeline | 每关事件时间轴（关卡×事件×触发时刻） |
| 生成条件事件 | 事件主表（触发时间/循环/鱼种/组/Count/链式事件） |
| 事件条件 | 条件明细（propertyPath/op/compareValue/isOr，挂到事件行） |
| 事件监听 | 监听明细（listenEvent/propertyPath/op，连续段序 listenIndex） |
| 阵型 | 阵型点位（Name/Shape/Offsets 几何——阵型点集编辑器消费） |
| 路径 | 路径（Custom=Points 点位 / Random=内外边界+途经点数——路径点编辑器消费） |
| 游戏数据 | 数据字段路径字典（条件 propertyPath 的引用源） |
| 游戏事件 | 游戏事件路径字典（监听 listenEvent/propertyPath 的引用源） |

> 另有「类名映射」控制表（`DuoWei/类名映射.duowei`，不在上列数据表内）：登记「表名→类名」即控制该表是否导出及导出类名——加表/改类名在此操作。

2. **落地**：文档库根 `uv run GameData/tools/Program/duowei_export.py`（直出自带全链校验，PASS 且 FAIL=0 才算过）
3. **验证**：直出输出无 FAIL；进 Play 模式实测；产物随 commit 提交

### 场景 B：我想改阵型/路径点位（几何类）

1. **先启服务**：Obsidian 侧边栏 ▶「数据管线启动器」（静默后台，推荐）；或双击 `GameData/tools/Program/start.bat`（独立最小化窗口 + 自检，手动等价：`uv run GameData/tools/Program/server.py`，默认 `127.0.0.1:8712`，`-p 端口` 换端口）
2. **打开编辑器**：`GameData/tools/View/` 下的 阵型点集编辑器.html 或 路径点编辑器.html（Obsidian HTML Reader 或系统浏览器 file:// 直开；数据通路纯 .duowei）
3. 点「**连接桥**」→ 下拉选条目 →「**载入**」→ 画布拖点编辑（拖点/框选/微调/撤销重做/双击加点/右键删点）
4. 「**保存到多维表格**」——服务端最小手术写回（只改几何字段+revision+updatedAt），可回 Obsidian 刷新核对
5. **落地**：编辑器内点「**应用数据到游戏**」（duowei_export 直出 .duowei→json+C#，绿色/红色状态条直接回显结果），或同场景 A 第 2~3 步（直出 → Play）

### 场景 C：我想在 Unity 内单条快速测试（不改源头）

1. Unity 菜单 `游戏配置/角色编辑器` →「Luban 鱼种测试」（或 `游戏配置/关卡编辑器` →「Luban 关卡测试」）
2. 改单条参数 →「保存此条」——只写 `StreamingAssets/luban/`，**不动 .duowei/xlsx 源头**
3. Play 验证 → 顶部横幅会提示测试态 →「一键还原」回干净基线
4. 满意的改动回场景 A/B 落到源头（源头是唯一事实，测试态不持久）

### 场景 D：我想圈定测试关卡子集

1. `游戏配置/关卡编辑器` 勾选目标关卡 → 生成 Test/ 子集
2. ⚠ 留意 Unity Console 日志确认生成范围（避免误圈全量）
3. 测试完清除勾选还原

## 数据流向图

```
Obsidian 多维表格                        直出产物                                              运行时
────────────────                       ──────────                                           ──────────
GameData/DuoWei/*.duowei  ──直出──▶  GameData/Export/*.json + Export/Generated/*.cs 五目录  ──▶  游戏
（唯一编辑源）            duowei_export（零中间表格；直出内置校验，FAIL=0 才算过）
```

> **唯一编辑源警示**：`.duowei` 是唯一源头；Export / Generated 全是生成物，手改会被下次生成覆盖。改数据一律回 DuoWei/（点位类经编辑器+本地服务，其余直接 Obsidian）。
> **Xlsx 目录**：旧中间表格管线（.duowei → xlsx → Luban gen）的派生产物，直出管线不经过也不更新它；目录仅作历史参照留存，删除不影响直出链路。

## 工具清单

| 工具 | 用途 | 启动 | 输入 → 输出 |
|------|------|------|------------|
| `GameData/tools/Program/duowei_export.py` | 直出器（.duowei → json + C#，零项目知识，规则全通用） | `uv run GameData/tools/Program/duowei_export.py`（任意 cwd，配置默认=tools/config.json） | .duowei → GameData/Export/*.json + Generated/*.cs 五目录（直出内置校验，FAIL=0 才算过） |
| `GameData/tools/Program/server.py` | 本地一体化后端（config.json 读写 + 一键直出 + .duowei 点位编辑，纯标准库，路径自定位） | `uv run GameData/tools/Program/server.py`（默认 127.0.0.1:8712；停：`POST /shutdown`） | 导出工具.html ⇄ config.json（最小手术写回）；POST /export、/apply → 直出导出；/list、/record → 点位编辑器读写 .duowei |
| `GameData/tools/Program/start.bat` | 本地服务守护启动器（独立最小化窗口+自检，不随终端死；**同时服务导出配置与点位编辑**） | 双击运行 | 启动 server.py → 自检就绪/失败原因 |
| Obsidian 数据管线启动器插件 | 侧边栏 ▶/■ 静默启停服务（路径按当前库根自定位，跨机器通用） | 设置→第三方插件启用后用侧边栏图标或命令面板 | 同 start.bat（无窗口） |
| `GameData/tools/View/导出工具.html` | 导出配置编辑 + 一键导出页面（统计回显） | 服务启动后打开（http://127.0.0.1:8712 或 HTML Reader） | config.json ⇄ 表单；一键 `uv run Program/duowei_export.py` |
| `GameData/tools/View/阵型点集编辑器.html` | 阵型点位拖拽编辑（多组/硬校验/撤销重做） | 浏览器/HTML Reader 直接打开（连本地服务 8712） | 阵型.duowei ⇄ 画布（经 server.py；含「应用数据到游戏」直出） |
| `GameData/tools/View/路径点编辑器.html` | 路径点位与随机参数编辑（Custom/Random 双形态） | 浏览器/HTML Reader 直接打开（连本地服务 8712） | 路径.duowei ⇄ 画布（经 server.py；含「应用数据到游戏」直出） |
| Unity 角色编辑器（Luban 鱼种测试） | 单条快速测试 | Unity 菜单 `游戏配置/角色编辑器` | StreamingAssets 直改 + 一键还原 |
| Unity 关卡编辑器（Luban 关卡测试） | 单关快速测试 + Test 子集 | Unity 菜单 `游戏配置/关卡编辑器` | 同上 |

## 在 Obsidian 中使用点位编辑器（推荐方式）

安装社区插件 **html view**（或同类支持无限制模式的 HTML 查看器），在插件设置中开启 **Unrestricted Mode**——之后直接在 Obsidian 中打开 `tools/View/` 下的编辑器 html 即可正常连接本地服务使用（无需系统浏览器）。

编辑器采用**实测连接**策略：任何环境都先尝试连接服务，连不上才提示原因（服务未启动 / 宿主沙箱限制）。

## 打包后更新机台数据

机台数据部署工具随旧中间表格管线一并退役——当前直出管线产物在 `GameData/Export`（json + Generated C#），机台同步方式待负责人定夺后在此登记。

## 常见问题

- **uv 报缺依赖？** 脚本头部 PEP 723 声明的依赖 `uv run` 会自动安装（仅需先装 uv）；系统 PATH 无 python 也能跑。
- **本地服务怎么正确启动/判断还活着？** 首选 Obsidian 侧边栏 ▶「数据管线启动器」（静默后台，日志在插件目录 launcher.log）；或双击 `GameData/tools/Program/start.bat`——独立最小化窗口守护启动，不随启动它的终端关闭而死，启动器自检输出就绪 127.0.0.1:8712 或失败原因（关闭该窗口=服务停止）。判断服务是否活着：浏览器开 `http://127.0.0.1:8712/ping`，返回 `{"ok":true,...}` 即活（含 formation/path 表条数）。手动启动 `uv run GameData/tools/Program/server.py`；换端口 `-p <端口>`，页面侧用 `?dwport=<端口>` 或 `localStorage.dwBridgePort` 覆盖。file:// 页面 fetch localhost 无需额外浏览器设置（服务已开 CORS）；若被安全插件拦截，改用无插件浏览器窗口。
- **在 Obsidian 内置浏览器（webviewer）打开编辑器，永远连不上服务？** Obsidian webviewer 沙箱 CSP 拦截页面向 http://127.0.0.1 的 fetch，属平台限制、服务侧无解。编辑器实测探测连不上时会在底部状态栏提示原因——复制本文件路径用系统浏览器（Chrome/Edge）打开即可正常连接。
- **Obsidian 里符号名/中文表名显示异常？** 联系队长（有反转预案，勿自行改名）。
- **顶部横幅「测试态」？** 表示 StreamingAssets 被 Unity 编辑器直改、与干净基线不一致——「一键还原」即可恢复。
- **滑轮缩放后页面不重排/右边被裁？** 三个工具页内置缩放自适应（zfit）：HTML Reader 的滑轮缩放是视觉放大（视口宽度不变），页面会读取缩放值主动重排为恰好铺满可见区（放大→自动减列/侧栏下移，可滚动）；若个别页面未刷新，重开该页即可。
- **服务写后 Obsidian 没刷新？** 回到该多维表格笔记重新打开/切换视图即可（服务每次请求重读文件，无缓存竞争）。

---

> **给 AI 会话的提示**：工作区策略已是宽松文件模式时，调用文件/命令工具**不必附 sandbox_permissions 参数**——附了反而触发"无意义升级"自动拒绝（噪音，非权限问题）。
