---
type: task
status: done
requester: task
start: 2026-09-05
end: 2026-09-05
depends: []
milestone: false
---

# 彩票值 HUD 显示对接（LotteryText）

## 背景

负责人已在 PlayerCannon.prefab 的 ScoreText 同级加了 LotteryText 节点；彩票分（LotteryValue）当前在 Play 中不可见。事件与刷新模式现成：`LotteryValueChangedEvent{PlayerId, LotteryValue}`（击杀入账/出票扣减/清零各处已发），积分参照链=ScoreRefreshEvent → SceneFlow 注册 → ViewStatus.SetScore。

## 交付物

1. ViewStatus（自查实际类名/路径）：加 LotteryText 文本引用（绑定方式与 ScoreText 同构——序列化字段 + prefab YAML 参照注入，镜像 ScoreText 的 m_ 绑定行；禁止运行时 Find）+ `SetLottery(int)` 方法（镜像 SetScore 的格式化/刷新逻辑）。
2. 事件接线：在 ScoreRefreshEvent 注册处（SceneFlow.cs 约 99 行模式）同址注册 `LotteryValueChangedEvent` → `ViewStatus(e.PlayerId).SetLottery(e.LotteryValue)`；初始显示（进游戏/视图打开时显示当前值）按 SetScore 的既有初始口径对齐补齐。
3. PlayerCannon.prefab：给 ViewStatus 组件（或持有 ScoreText 的组件）注入 LotteryText 参照（YAML fileID 镜像 ScoreText 绑定行；改后 prefab 可解析）。
4. 双 csproj 0 error。

## 验收

- Play 中击杀鱼彩票值实时上涨、出票后清零显示正确（负责人复验）
- 无 Find/FindObjectOfType 运行时调用；只改 ViewStatus/SceneFlow/prefab 三处

## 验收记录

- 2026-09-05 队长验收：ViewStatus.SetLottery(long)（彩票值为 long，精灵文本逐位转换镜像积分模式）+ SceneFlow 同址订阅 LotteryValueChangedEvent + prefab lotteryText 参照注入 1 行（pyyaml 解析校验过）；初始显示经既有事件链自动正确（初始化 ResetStatus 0.2s 后必发一次）；双 csproj 0 error
- 待负责人 Play 复验：击杀上涨/出票扣减/退场清零

## 关联

- 彩票机经济口径：任务/彩票机经济口径落地.md
