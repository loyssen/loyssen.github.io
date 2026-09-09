---
类型: 系统设计
关联模块:
  - 对象模块
关联系统: []
关联数据:
  - FishData
  - FishGroupData
  - RandomPathConfig
  - CustomPathConfig
  - FormationData
状态: 已实现
版本: 4
更新日期: 2026-09-05
---

# SplinePathSystem 路径系统

> 本文档描述 SplinePathSystem 的设计。基于 Unity Splines 的路径生成系统，管理 SplinePath 对象池，供鱼移动策略消费。
> **同时是路径/阵型独立 JSON 配置（RandomPathConfig / CustomPathConfig / FormationData）的统一加载与提供者**，按 GUID 持有私有字典，不进概率云 WaterDict。

---

## 一、系统概述

### 1.1 所属 Module

| 项目 | 内容 |
|------|------|
| 所属 Module | 对象模块（PawnModule） |
| 挂载位置 | `Pool/FishPath` |
| 获取方式 | `this.GetSystem<SplinePathSystem>()` |

### 1.2 关键依赖

| 依赖项 | 类型 | 说明 | 获取方式 |
|--------|------|------|---------|
| `PawnModule` | Module | SplinePath 对象池 | `this.GetModule<PawnModule>()` |

---

## 二、公开 API

| API | 返回类型 | 说明 |
|------|---------|------|
| `AllocateSplinePath()` | GameObject | 从池取 SplinePath（含 SplineContainer） |
| `RecycleSplinePath(GameObject)` | void | 回收 SplinePath |
| `GetSpline(GameObject)` | SplineContainer | 获取路径对象的 SplineContainer |
| `CreateBounds(Vector2, Vector2)` | KFramwork.Bounds | 创建出界检测边界 |
| `BuildPathById(container, pathId, ...)` | bool | 按 PathId 统一构建路径（随机/自定义分派） |
| `BuildFishPath(container, entry, exit, ...)` | void | 按显式起终点构建路径 |
| `BuildSpacedPath(...)` | int | 完整路径生成：入口→中间点→出口（多重重载） |
| `SteerPoint(current, prev, angleRange, distRange)` | Vector2 | 方向偏转+距离步进 |
| `ResolvePathEndpoint(point)` | Vector2 | 解析路径终点到边界带 |
| `DetectSide(worldPos, halfSize)` | int | 判定点位于哪一侧 |
| `GenerateFormationPoints(...)` | void | 为 FishGroup 生成阵形入口/出口 |

---

## 三、核心实现

### 3.1 独立配置加载（PathId / FormationId）

SplinePathSystem 统一加载路径/阵型独立 JSON 配置，供 `FishData.PathId`、`FishGroupData.PathId/FormationId` 引用：

| 配置 | 文件位置 | 键 | 说明 |
|------|---------|-----|------|
| `RandomPathConfig` | `PathConfig/RandomPathConfig/*.json` | GUID Id | 随机路径：内外边界 `BoundInner/BoundOuter` + 途经点数 `WaypointCount` |
| `CustomPathConfig` | `PathConfig/CustomPathConfig/*.json` | GUID Id | 纯 2D 路径点 `Points[]`（含起终点），由关卡编辑器从场景 SplineContainer 导出 |
| `FormationData` | `FormationData/{Custom\|形状}/*.json` | GUID Id | 纯 2D 位置偏移 `Offsets[]`（相对锚点每鱼偏移），长度须与群 Count 一致 |

**加载方式：** `OnInit → LoadConfigs()` 用 `SearchOption.AllDirectories` 递归扫描各文件夹，Newtonsoft.Json 反序列化数组，按 `Id`(GUID) 存入私有字典。

**获取 API：**

| API | 返回类型 | 说明 |
|------|---------|------|
| `GetRandomPath(string id)` | `RandomPathConfig` | 按 GUID 取随机路径配置（空/未找到返回 null） |
| `GetRandomPathBounds(string id)` | `(Vector2, Vector2)` | 解析 PathId 指向配置的内外边界；空 PathId 返回 zero（默认 HalfSize 边界） |
| `GetCustomPath(string id)` | `CustomPathConfig` | 按 GUID 取自定义路径配置 |
| `GetFormation(string id)` | `FormationData` | 按 GUID 取阵型偏移配置 |

> **关键约定：** 路径/阵型配置**均不进概率云 WaterDict**，由 SplinePathSystem 私有持有，与概率计算解耦。`FishGroupConfig`（图形参数）仅编辑器工具用其生成 Offsets，不 Json 化。

### 3.2 边界体系

| 参数             | 默认值       | 说明          |
| -------------- | --------- | ----------- |
| `BoundSize`    | (15, 8.5) | 基准半宽高       |
| `ActiveMargin` | (-2, -2)  | 活动边界缩进      |
| `CenterPull`   | 0.6       | 中心拉力强度(0~1) |

| 范围 | 公式 | 用途 |
|------|------|------|
| 内边界 | `HalfSize + BoundInner` | 出界检测 |
| 外边界 | `HalfSize + BoundOuter` | 入口/出口生成区 |
| 活动范围 | `HalfSize + ActiveMargin` | 中间点约束 |

### 3.3 路径生成流程

`BuildSpacedPath(container, innerOffset, outerOffset, waypointCount, segMin, segMax, bendAngle)`:
1. `EmitEndpoint(spline, innerHalf, outerHalf, bendAngle)` — 生成入口点
2. `SteerPoint` 循环生成中间路径点（受 `ActiveMargin` 约束 + `CenterPull` 向中心拉回）
3. `EmitEndpoint(spline, innerHalf, outerHalf, bendAngle)` — 生成出口点
4. `SplitSegment` — 分割过长段确保段距均匀

### 3.4 SteerPoint 算法

以前一点方向为基准，在 `angleRange` 角度区间内偏转，`distRange` 距离区间内步进。贴边时限制角度范围为朝向中心的 1/4 半角区间。

---

## 四、相关文档

- [鱼](鱼/鱼.md)
- [FishSpawnSystem系统](FishSpawnSystem系统.md)
- [框架设计文档](../框架设计文档.md)

