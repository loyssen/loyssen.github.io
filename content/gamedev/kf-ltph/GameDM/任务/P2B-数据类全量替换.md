---
type: task
status: done
requester: lead
start: 2026-09-04
end: 2026-09-04
depends: [P2A-Luban退役]
milestone: false
---

# P2-B：项目数据类全量替换（对齐生成结构，注解保真，编译收敛）

## 背景与拍板

负责人拍板：项目手写数据类**同步更换**为生成结构——只换类名/字段/属性/继承/嵌套，**Odin 注解（LabelText/ValueDropdown/Tooltip）与 XML 注释保真**；CompareOp 用框架版（生成 CompareOp.cs 不引入 Assets）；事件 13 个 struct 不动；SceneData/UnlockData 运行时 Model 不动（已拍板）。规格来源：`LTPHDoc/GameData/Export/Generated/`（34 类）。

## 替换清单（以生成结构为准绳，逐类 diff 后迁移）

| 项目现状 | 迁移到 | 要点 |
|---|---|---|
| Data/Config/PathConfig 三类 | 已 MATCH | 验证即可，预期零改动 |
| Data/Config/FormationData.cs | Shape + Offsets:List<Vector2> | 对齐生成（当前项目形态以 diff 为准） |
| Data/Fish/FishData.cs | 生成 FishData 10 字段 | 注解保留；Volume/Probability/Level/Speed/Hp/RefName/ImagePath/DeathRotationAngle/PathId(string) |
| Data/Fish/FishWaveData.cs + FishTimelineEntry | 生成 FishWaveData（7 字段）+ TimelineEntry 独立类 | Timeline List<TimelineEntry>；NextLevelIds List<string>；UnlockConditions List<DataCondition>；Volume int |
| Data/Fish/FishGroupData.cs | GroupData + School/Formation/Queue 三子类 | 全部 FishGroupData 消费方迁移（9 文件）；KillMode 保留 |
| Data/Condition/DataCondition.cs | class + isOr + compare:PropertyCompare | struct→class；消费方 dc.op→dc.compare.op 等（14 文件） |
| Data/Condition/EventFieldCompare.cs | PropertyCompare（改名/重建） | op:CompareOp（框架版） |
| Data/Condition/EventCondition.cs | EventListener（isOr/listenEvent/compare） | 11 文件消费方 |
| Data/Condition/FishEvent.cs | FishConditionEvent struct | 10 文件消费方 |
| Data/Condition/IConditionEvent.cs | 生成 11 属性数据契约接口 | EventId→Id 等成员名迁移 |

## 交付物

1. 上述类文件迁移（保留 Odin 注解/XML 注释；生成新增字段无注解则裸成员）。
2. 全部消费方迁移：FishGroupData→GroupData 族（WaveSystem 等）、EventCondition/EventFieldCompare/FishEvent/DataCondition 改名与结构路径（dc.compare.op）、数组↔List<string>、EventId→Id、FishTimelineEntry→TimelineEntry、Editor 工具（DataConditionDrawer/EventConditionHelper/PathConfigHelper 等）适配。
3. 编译验收：dotnet build Assembly-CSharp.csproj + Assembly-CSharp-Editor.csproj 0 error；对 34 生成类逐类 diff 项目版（字段/类型/继承一致=PASS），比对脚本产出报告附汇报。
4. 有疑问的结构分歧（如消费方语义不明）逐条列出向负责人回报，不擅自定语义。

## 验收标准

- 两 csproj 0 error；类结构 diff 全 PASS 或已列分歧待裁定；Odin 注解零丢失（迁移文件前后特性清单对照）

## 验收记录

- 2026-09-04 队长验收：双 csproj 0 error；迁移范围 18/18 类结构 diff 通过（排除=CompareOp 框架版/SceneData/UnlockData/13 事件 struct 按拍板）；Odin 注解保真审计通过（发现并补回 1 处漏拷）；消费方 16 文件编译收敛；ConditionEvent 裸类新增为 P2-C 装载目标
- 待负责人裁定的 9 条语义决策（worker 按最小合理迁移处理）见会话汇报：①FixedFormationFishData 移除后 FishSpawnSystem 判据改 Resources 同名预制体启发式（无预制体静默跳过）②EventListener 单 compare（多字段 AND 需拆多条）③Core 类自动属性补 [field: SerializeField] 保序列化面 ④propertyPath 下拉在 EventListener 上下文内容不对口 ⑤Volume 错挂注解移位至 Duration ⑥PathIds[0] 单路径语义延续 ⑦克隆改 Activator+CopyInstance ⑧JSON 旧键名/旧路径未动（P2-C）⑨事件注释文案残留待清理

## 关联

- 前置：P2A-Luban退役；后继：P2-C KJson 装载层（导出直出 StreamingAssets/KJson + GameModel 适配读取）
