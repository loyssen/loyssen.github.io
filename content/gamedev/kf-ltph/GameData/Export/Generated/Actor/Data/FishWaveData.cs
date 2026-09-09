// 自动生成文件——由 duowei_export 从多维表格源生成，勿手改。
using System;
using System.Collections.Generic;
using KFramwork;

public class FishWaveData : ActorData
{
    public float Duration;
    public string SceneId;
    public int VolumeForNext;
    public List<string> NextLevelIds;
    public List<DataCondition> UnlockConditions;
    public List<TimelineEntry> Timeline;
    public int Volume;

    public virtual void CopyInstance(FishWaveData target)
    {
        target.Name = Name;
        target.Duration = Duration;
        target.SceneId = SceneId;
        target.VolumeForNext = VolumeForNext;
        target.NextLevelIds = NextLevelIds;
        target.UnlockConditions = UnlockConditions;
        target.Timeline = Timeline;
        target.Volume = Volume;
    }
}
