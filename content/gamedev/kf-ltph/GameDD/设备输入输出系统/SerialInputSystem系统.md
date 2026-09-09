---
类型: 系统设计
关联模块:
  - DeviceModule
关联数据:
  - SerialProtocolConfig
状态: 已实现
版本: 2
更新日期: 2026-09-02
---

# SerialInputSystem 串口输入系统

> 本文档描述 SerialInputSystem 的设计。继承 `BaseInputSystem<SerialDevice>`，负责串口字节流接收、协议拆包和分发。

---

## 一、系统概述

### 1.1 所属 Module

| 项目 | 内容 |
|------|------|
| 所属 Module | DeviceModule |
| 挂载位置 | `Device/Serial` |
| 获取方式 | `this.GetModule<DeviceModule>().GetInputSystem<SerialInputSystem>()` |

### 1.2 关键依赖

| 依赖项 | 类型 | 说明 |
|--------|------|------|
| `SerialDevice` | IDevice | 串口硬件包装器 |
| `SerialProtocolConfig` | ScriptableObject | 协议格式配置 |
| `OperationMap` | Controller | 映射编排器 |

---

## 二、公开 API

| API | 返回类型 | 说明 |
|------|---------|------|
| `RegisterHandler(Interval, Action<byte[]>)` | void | 注册区间数据回调 |
| `UnregisterHandler(Interval)` | void | 移除回调 |
| `ParsePackets()` | void | 协议拆包主循环 |
| `DispatchPacket(...)` | void | 分发单个数据包 |

---

## 三、核心实现

### 3.1 串口参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `OpenMethod` | USB | 打开方式 |
| `BaudRate` | 115200 | 波特率 |
| `ReadProtocol` | BinaryStreaming | 读取协议 |
| `VendorID` / `ProductID` | "1234" | USB 设备识别 |
| `PortOrSerial` | — | 端口号/序列号过滤 |

### 3.2 数据流

```
SerialDevice.OnReadComplete()
  → SerialInputSystem.ParsePackets()
    → 扫描包头(headerHex) → 按协议格式拆包
    → DispatchPacket()
      → 命令区间(Id=-1) → OperationMap.OnCommandData()
      → 玩家区间(Id=0~9) → OperationMap.OnPlayerData(pid, data)
```

### 3.3 协议包结构

`[包头 N字节] [命令段 N字节] [玩家段 M×10字节] [固定段 N字节] [校验段 N字节]`

解析参数（包头hex/命令长度/玩家长度/总长度/校验方式）从 `SerialProtocolConfig.receive` 读取。

---

## 四、数据来源

| 数据 | 来源 | 说明 |
|------|------|------|
| `SerialProtocolConfig` | Inspector 拖入 | `receive.headerHex`, `commandLength`, `playerLength`, `totalLength`, `verifyType` |

---

## 五、相关文档

- [设备](设备输入输出系统.md)
- [SerialControlSystem系统](SerialControlSystem系统.md)
- [设备协议配置说明](设备协议配置说明.md)
