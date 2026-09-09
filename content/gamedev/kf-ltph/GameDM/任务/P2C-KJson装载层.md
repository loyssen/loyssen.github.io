---
type: task
status: done
requester: lead
start: 2026-09-04
end: 2026-09-05
depends: [P2B-数据类全量替换]
milestone: false
---

# P2-C：KJson 装载层（StreamingAssets/KJson → 新数据类 → 三装载点接通）

## 背景

负责人已把导出目录配到 `Assets/StreamingAssets/KJson/`（7 json：GroupData 1220 / TimelineEntry 864 / ConditionEvent 556 / PathConfig 81 / FishWaveData 40 / FormationData 329 / FishData 72）。P2-A 留下三个暂空装载点待接：GameModel.OnConfigInit（GameplayModule.DataFiller）、SplinePathSystem.LoadConfigs（三注册表）、WaveSystem.OnInit（条件事件库）。P2-B 后数据类已与 json 结构完全同构（全局命名空间，ActorData 基类 Id/Name string）。

## 交付物

1. **KJson 装载基建**（位置就近 GameModel 或 Data/ 下新文件，命名如 KJsonLoader）：
   - `Application.streamingAssetsPath + "/KJson"` File 读 json（Windows 机台直读文件即可）
   - **`__type` 子类分发**：带 `__type` 的记录反序列化到对应子类（GroupData→School/Formation/QueueGroupData；PathConfig→Custom/RandomPathConfig），无标记记录归基类；实现方式自选（JArray 预分组 or Newtonsoft JsonConverter），模板按具体类型归桶
   - ConditionEvent.json 平铺记录：含 `Count` 键的记录装载为 FishConditionEvent（struct），其余为 ConditionEvent
   - Vector2/向量数组依赖 Newtonsoft 对 public 字段的反射直读（项目现有 Newtonsoft 包即可），装载后抽样校验非空
2. **三装载点接通**：
   - GameModel.OnConfigInit → DataFiller 灌 GameplayModule 模板域（ActorData 系类型按具体类型归桶灌入；FishWaveData 内嵌 TimelineEntry/UnlockConditions 随 json 直接成活）
   - SplinePathSystem.LoadConfigs → 路径/阵型三注册表（Custom/RandomPathConfig、FormationData）
   - WaveSystem.OnInit → 条件事件库（ConditionEvent/FishConditionEvent 556 条；与 RegisterSceneConditionEvents 的既有关系保持）
   - 各装载点装载后打一条计数日志（如 `[KJson] GroupData 1220（School 168/Formation 955/Queue 80/基类 17）`）
3. **ConfigPaths 重指向**：GameDataRoot 旧路径（项目根\GameData 已不存在）改为 StreamingAssets/KJson 口径；LevelConfigHelper / FishConditionEvent.GetTargetIds 等旧键 `"EventId"` 扫描逻辑适配新键名/新目录（其用途自查：下拉源/提示），保持功能等价
4. **验收**：双 csproj 0 error；装载代码不引入 Resources.Load/Find 违规；运行时行为由负责人 Unity Play 复验（日志计数即可初判）

## 约束

- 不改数据类结构（P2-B 成果）；不动 LTPHDoc 导出配置与 .duowei；json 由导出管线再生，装载侧只读
- WaveSystem/模板域接线中语义不明处（如条件事件库的消费者期望形态）列出待负责人确认，按最小合理实现

## 验收记录

- 2026-09-05 队长验收：KJsonLoader（LoadList/LoadHierarchy __type 分发/LoadConditionEvents Count 分型，双层容错）+ 三装载点接通带计数日志 + ConfigPaths 七文件口径 + 旧键 EventId→Id 全量适配；双 csproj 0 error；数据完整性预检 0 缺失/0 重复
- 待负责人 5 项确认：①TimelineEntry.json 独立表未装载（内嵌 857 已全覆盖，另 7 条无引用扁平行）②通用 ConditionEvent class 桶现无记录（分型已支持）③群 Hp 双未配 24 条告警（与旧管线一致）④基类 GroupData 17 条入模板、基类 PathConfig 0 条 ⑤Unity 刷新生成 KJsonLoader.meta 后 Play 看三条 [KJson] 日志复验

## 关联

- 前置：P2A/P2B；记忆：`p2-pipeline-replacement-2026-09-04`、`duowei-export-rules-v2-2026-09-04`（__type/平铺子类/嵌套语义）
