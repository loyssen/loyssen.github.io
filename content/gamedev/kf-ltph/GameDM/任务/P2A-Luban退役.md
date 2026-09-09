---
type: task
status: done
requester: lead
start: 2026-09-04
end: 2026-09-04
depends: []
milestone: false
---

# P2-A：Luban 旧管线退役（目录删除 + 装载点暂空，编译闭环）

## 背景与拍板

P2 数据类替换前置步。负责人拍板：Luban 没用了就删；数据装载下一任务走 KJson（导出直出 StreamingAssets/KJson + GameModel 适配）。本任务**不动任何手写数据类**——只摘除 Luban 体系，保持编译通过，为 P2-B 提供干净基线。

## 交付物

1. 删除 `Assets/Scripts/Luban/` 整目录（Generated/Loader/Mapper/ConfigPaths/Editor 菜单等）及对应 .meta。
2. 删除依赖 Luban 运行时的编辑器测试工具：`Assets/Scripts/Editor/Luban/`（LubanTestState/LubanLevelTestView 等「Luban 鱼种/关卡测试」面板）及菜单注册残留；相关 .meta 一并删。
3. `Data/GameModel.cs` 装载点（约 105-108 行）：LubanTablesLoader.Load()/LubanDataMapper.FillTemplates 调用摘除，改为暂空实现 + 一行日志（如「[GameModel] 数据装载待接 KJson（P2-C）」）；`GameplayModule.DataFiller` 赋值处保持类型可编译（delegate 空实现或不再赋值，以编译与不破坏 GameplayModule 结构为准）。
4. 全仓 grep 清零：`LubanTablesLoader|LubanDataMapper|Luban.BeanBase|cfg\.|Editor/Luban` 无残留引用（注释性提及可保留但建议顺手清理 FishData.cs:16 这类注释）。
5. 编译验收：`dotnet build Assembly-CSharp.csproj`（仓库根，若该 csproj 不含 Editor 程序集则同时 build Assembly-CSharp-Editor.csproj）0 error。Unity 侧由负责人开编辑器复验。
6. 同步：`StreamingAssets/luban/` 旧数据目录本次**不删**（KJson 装载落地后一并清理，避免误伤回滚需要）；`Assets/Scripts/Editor/DataConditionDrawer.cs` 等暂不动（P2-B 处理）。

## 验收标准

- 两 csproj 编译 0 error；Luban 引用清零；手写数据类零改动（git diff 仅删除文件 + GameModel + 注释清理）

## 验收记录

- 2026-09-04 队长验收：Luban grep 0 命中；Assembly-CSharp / Editor csproj 均 0 error；ConfigPaths 迁移至 Data/（手写类依赖，合理处置）；SplinePathSystem/WaveSystem 两处额外装载点一并暂空（待接 KJson）；遗留：ConfigPaths.GameDataRoot 指向旧目录（P2-B/C 重指向）、Packages 内 3 处 Luban 注释（主程择机）

## 关联

- 后继：`P2-B 数据类全量替换`（depends 本任务）、`P2-C KJson 装载层`（负责人排期）
