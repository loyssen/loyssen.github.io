---
type: task
status: done
requester: lead
start: 2026-09-04
end: 2026-09-04
depends: [P2B-数据类全量替换]
milestone: false
---

# P2-B 补丁：FixedFormationFish 移除 + PathIds 轮换消费

## 背景与拍板（负责人 2026-09-04）

P2-B 待确认清单两条裁定：
- ① FixedFormationFish 与 FormationGroupData 行为一致且当前不使用——**整体去掉**；且 FishSpawnSystem 从 Resources 探测同名预制体的行为**不允许**（对象生成一律走对象模块/PawnModule），该启发式连同 FixedFormation 特判一并删除。
- ⑥ PathIds 多路径消费默认**轮换**（多次生成同一群时依次循环取路径）。

## 交付物

1. 移除 FixedFormationFish：Actor 类文件、FishSpawnSystem 中的特判与 Resources 探测、类型注册/引用（如 GameplayModule.UsedActorTypes）、相关注释；Resources/Actor 下的 FixedFormationFish 预制体与 .meta 如存在则一并删除（列进汇报）。
2. FishGroup 的 PathIds 消费改轮换：现 `PathIds[0]` 改为按生成实例循环取路径（单路径时行为不变；空列表防御保持既有口径）。实现位置以 FishGroup.CalcOffsets 及其调用链为准，轮换计数归属与生命周期在汇报中说明（如静态轮询索引 vs 实例字段）。
3. 编译验收：双 csproj 0 error；grep `FixedFormationFish` 清零。

## 验收标准

- FixedFormationFish 全仓 0 残留；PathIds 轮换逻辑可解释；不引入 Resources.Load 等违规访问

## 验收记录

- 2026-09-04 队长验收：FixedFormationFish 全仓 0 残留（cs/meta/prefab，Resources 探测行为移除）；PathIds 轮换=模板级静态索引（按还原模板 Id 分桶，池克隆不影响推进；单路径行为不变）；双 csproj 0 error
- 负责人 Unity 侧遗留：HPBeta.unity/beta.unity 两处场景摆位与 GameManager_Damage.prefab 的 m_TypeGroupList 条目将现 missing 引用需手动清；StreamingAssets/luban 旧数据 6001 行（策划侧定夺删否，新逻辑已跳过不报错）

## 关联

- 前置：P2B-数据类全量替换（待确认清单 ①⑥ 就此闭环）
