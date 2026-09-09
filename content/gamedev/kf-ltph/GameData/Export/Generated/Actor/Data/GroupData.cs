// 自动生成文件——由 duowei_export 从多维表格源生成，勿手改。
using System;
using System.Collections.Generic;
using KFramwork;

public class GroupData : ActorData
{
    public int Count;
    public KillMode KillMode;
    public float Speed;
    public string Description;
    public List<string> PathIds;
    public string FishId;
    public int Hp;
    public int Volume;

    public virtual void CopyInstance(GroupData target)
    {
        target.Name = Name;
        target.Count = Count;
        target.KillMode = KillMode;
        target.Speed = Speed;
        target.Description = Description;
        target.PathIds = PathIds;
        target.FishId = FishId;
        target.Hp = Hp;
        target.Volume = Volume;
    }
}
