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

# SerialControlSystem 串口输出系统

> 本文档描述 SerialControlSystem 的设计。继承 `BaseControlSystem<SerialDevice>`，维护发送队列，每帧发送一包，自动组装包头和 XOR 校验。

---

## 一、系统概述

### 1.1 所属 Module

| 项目 | 内容 |
|------|------|
| 所属 Module | DeviceModule |
| 挂载位置 | `Device/Serial` |
| 获取方式 | `this.GetModule<DeviceModule>().GetControlSystem<SerialControlSystem>()` |

### 1.2 关键依赖

| 依赖项 | 类型 | 说明 |
|--------|------|------|
| `SerialDevice` | IDevice | 串口硬件包装器 |
| `SerialProtocolConfig` | ScriptableObject | 发送协议格式配置 |

---

## 二、公开 API

| API | 返回类型 | 说明 |
|------|---------|------|
| `Enqueue(byte[])` | void | 入队数据 |
| `SendImmediate(byte[])` | void | 立即发送（跳过队列） |
| `SendControl(byte[])` | void | 组包发送（加包头+校验） |

---

## 三、核心实现

### 3.1 发送流程

```
OperationMap → SendControl(commandData)
  → 读取 send.headerHex + 校验方式
  → 组包: [包头 N字节] + [commandData 可变] + [XOR 校验 N字节]
  → Enqueue → Update() 每帧一包 → SerialDevice.Send(packet)
```

### 3.2 输出通道

命令数据由 `OperationMapConfig.outputChannels` 模板或自定义委托 `ControlSerializer.CustomSerializerRegistry` 生成。

| 命令 | 操作码 | 说明 |
|------|--------|------|
| lottery | 0x01 | 彩票结算（2 字节值） |
| clear fault | 0x02 | 清除故障 |
| clear fault to lottery | 0x03 | 清除故障+切换 |
| clear coin fault | 0x04 | 清除硬币故障 |
| clear coins | 0x80 | 清除硬币 |

---

## 四、数据来源

| 数据 | 来源 | 说明 |
|------|------|------|
| `SerialProtocolConfig` | Inspector 拖入 | `send.headerHex`, `send.verifyType`（XOR） |

---

## 五、相关文档

- [设备](设备输入输出系统.md)
- [SerialInputSystem系统](SerialInputSystem系统.md)
- [设备协议配置说明](设备协议配置说明.md)
