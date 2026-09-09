---
type: task
status: done
requester: lead
start: 2026-09-04
end: 2026-09-04
depends: []
milestone: false
---

# 数据管线：删除 config.tables 清单（导出集合=类名映射登记项）

## 背景与拍板

config.json 的 `tables` 表名清单与类名映射表信息重复且属硬编码——负责人裁定删除：**有映射登记（表名→类名）的表即导出**。策划加新表只需在 Obsidian 类名映射表加一行，工具零改动。

## 交付物

1. `duowei_export.py`：main 的 json 导出集合从 `cfg["tables"]` 改为「Store 全部表中 classify=mapped 者」（即类名映射登记项，遍历 DuoWei 目录自动发现）；config 的 `tables` 键不再读取（存在亦忽略，无需删文件键，但 config.json 里顺手移除该键）。注意保持既有 json 输出名冲突检测与原子落盘逻辑不变。
2. 重导出：**7 个 json**（新增 FishData.json=72 条）+ 类型树（FishData.cs : ActorData，12 成员：RefName/Id/Name/Volume/Probability/Level/Speed/Description/ImagePath/DeathRotationAngle/PathId/Hp——具体类型按推导，PathId 取键 string）；FAIL=0，WARN 维持 2 条既有（不得新增）。
3. 鱼种表现状供参考：Id 为 number 列（值 2005 形态，actordata 基类强制 Id/Name string 输出）、DeathRotationAngle text "60.00"（数值文本推导）、PathId relation 单值。若导出暴露该表问题（断链/推导异常）如实报告，不擅自改表。
4. 头部注释与 GameData/README.md 同步：导出范围=映射登记表（tables 清单已废除）。
5. 验证：复跑两次 md5 稳定；既有 6 json+类型与改动前一致（仅新增 FishData 相关文件，无其他漂移）。

## 验收标准

- config 无 tables 键、导出器不读它；7 json 全绿可重复
- 类名映射加/删一行即可控制导出集合（自测：不动表、仅在汇报中说明机制即可）

## 验收记录

- 2026-09-04 队长验收：config 无 tables 键；7 json（FishData 72 条新增）FAIL=0 WARN=2 既有；其余 39 既有产物字节级不变；复跑确定性稳定；映射登记即导出机制成立（类名映射为导出集合唯一事实源）

## 关联

- 记忆：`duowei-export-rules-v2-2026-09-04`
