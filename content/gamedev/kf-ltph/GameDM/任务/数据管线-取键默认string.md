---
type: task
status: done
requester: lead
start: 2026-09-04
end: 2026-09-04
depends: [数据管线-关联多选值形态判定]
milestone: false
---

# 数据管线：取键引用默认 string（>int 显式数字化）

## 背景与拍板

关联 Id 引用的输出类型现按目标表 Id 列**值形态无损推导**（'9101' 纯数字→int、'001' 前导零→string），导致 NextLevelIds=List&lt;int&gt; 而 PathIds=List&lt;string&gt;，且与 ActorData 基类 Id:string 自相矛盾（同一 Id 在 json 里一处 "9101" 一处 9104）。负责人拍板：**Id 是标识符非数值——取键一律默认 string**，需要数字用 `>int` 显式指定。与项目惯例对齐（NextLevelIds string[]、FishId/TriggerId string）。

## 交付物

1. `duowei_export.py`：`_plan_relation` key 分支取 `plan.key_ctype` 改为恒 "string"（`infer_id_ctype` 不再用于取键；若函数因此无调用方则删除）。`>类型` 硬指定覆盖机制已存在，`NextLevelIds>List<int>` 之类可随时数字化。
2. 重导出：`NextLevelIds→List<string>`、`FishId→int 改 string`、`TriggerId（GroupId@TriggerId/FishId@TriggerId 合并）→string`、`FormationId→string`、`TriggerEventIds` 维持 List&lt;string&gt;；json 取键值全为字符串形态；FAIL=0，WARN 数不变（2 条既有）。
3. 产物漂移：预期变化文件=FishWaveData.cs/.json、GroupData.cs/.json、FormationGroupData.cs、ConditionEvent.cs/.json、FishConditionEvent.cs（及 json 内嵌引用其记录处），其余不变；门禁 23 项复跑（若断言含上述成员类型/值形态则同步修正断言口径为 string）。
4. 头部注释「引用解析/引用解引用」段同步：取键默认 string、`>int` 可覆盖。

## 验收标准

- 全部 xxId/xxIds 成员类型为 string 或 List&lt;string&gt;（除显式 >类型 外）
- json 中引用值全字符串（"9104" 非 9104）
- 门禁全 PASS；导出可重复

## 验收记录

- 2026-09-04 队长验收：NextLevelIds→List<string>、FishId/TriggerId→string、FormationId 维持 string；漂移恰 8 文件（含 IConditionEvent.cs 接口成员必然变化）；门禁 23/23；复跑 md5 稳定；infer_id_ctype 已删除
- 期间观察到 8712 服务并发导出（工具页触发），原子落盘机制下产物终态一致，无冲突损害

## 关联

- 记忆：`duowei-export-rules-v2-2026-09-04`
