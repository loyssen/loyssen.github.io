---
类型: 系统设计
关联模块:
  - 对象模块
关联系统:
  - WaveSystem
  - SplinePathSystem
  - LayerManager
关联数据:
  - FishData
  - FishGroupData
状态: 已实现
版本: 3
更新日期: 2026-09-05
---

# FishSpawnSystem 鱼生成系统

> 本文档描述 FishSpawnSystem 的设计。Wave\<FishEvent\>.Execute 通过此系统完成实际的鱼/鱼群对象生成，数据缓存在首次使用时惰性构建。

---

## 一、系统概述

### 1.1 所属 Module

| 项目 | 内容 |
|------|------|
| 所属 Module | FlowModule |
| 获取方式 | `this.GetSystem<FishSpawnSystem>()` |

### 1.2 关键依赖

| 依赖项 | 类型 | 说明 | 获取方式 |
|--------|------|------|---------|
| `PawnModule` | Module | Fish/FishGroup 对象池 | `this.GetModule<PawnModule>()` |
| `LayerManager` | Module | Z 层级分配 | `this.GetModule<LayerManager>()` |
| `CloudModule` | Module | FishData 缓存数据源 | `this.GetModule<CloudModule>()` |

---

## 二、公开 API

| API | 返回类型 | 可见性 | 说明 |
|------|---------|--------|------|
| `Spawn(string targetId, int count)` | int | public | 统一生成入口。1000~4999=个体鱼，5000~6999=鱼群。返回鱼群 Volume |
| `BuildFishDataCache()` | void | private | 从 CloudModule 构建 `FishData.Name → FishData` 缓存（首次 Spawn 时惰性调用，见 `EnsureInitialized()`） |
| `RegisterFishGroupPrototypes()` | void | private | 将鱼群原型注册到 PawnModule 对象池（惰性调用） |

---

## 三、核心实现

### 3.1 生成链路

```
WaveFish.Execute(FishEvent)
  → FishSpawnSystem.Spawn(targetId, count)
    → EnsureInitialized() 惰性构建缓存
    → SpawnFishById(fishId, count):
        PawnModule.Spawn<Fish>(fishName) × count
        → LayerManager.AllocateLayer(min, max)
        → fish.SetData(fishData) → ChangeState(Swim)
    → SpawnGroupById(groupId):
        PawnModule.Spawn<FishGroup>(groupName)
        → fishGroup.OnSpawn 内部 SpawnMembers
```

### 3.2 惰性初始化

`EnsureInitialized()` 在首次 `Spawn` 调用时执行：`BuildFishDataCache()` + `RegisterFishGroupPrototypes()`。确保 PawnModule 已完成注册。

### 3.3 数据缓存

`m_FishDataCache` : `FishData.Name → FishData` 映射，从 CloudModule 的 WaterDict 构建。`m_FishIdToName` : `数字Id → 鱼预制体名` 映射，用于 ID 方式生成时的名称查找。

---

## 四、数据来源

| 数据 | 来源 | 说明 |
|------|------|------|
| `FishData` | `CloudModule.Cloud.Model.WaterDict` | 按 Name 索引缓存 |
| `FishGroupData` | 同上 | 原型注册用 |
| Fish 预制体名 | `m_FishIdToName` | 数字 ID→预制体名 映射 |

---

## 五、相关文档

- [WaveSystem系统](../流程与视觉/流程/场景流程/WaveSystem系统.md)
- [鱼](鱼/鱼.md)
