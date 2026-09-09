// 自动生成文件——由 duowei_export 从多维表格源生成，勿手改。
using System;
using System.Collections.Generic;
using KFramwork;

public class ConditionEvent : IConditionEvent
{
    public string Name { get; set; }
    public string Id { get; set; }
    public float TriggerTime { get; set; }
    public bool Loop { get; set; }
    public float LoopInterval { get; set; }
    public bool StopOnCondition { get; set; }
    public float EventDelay { get; set; }
    public List<string> TriggerEventIds { get; set; }
    public List<EventListener> ListenEvents { get; set; }
    public List<DataCondition> DataConditions { get; set; }
    public string TriggerId { get; set; }
}
