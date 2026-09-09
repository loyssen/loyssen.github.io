// 自动生成文件——由 duowei_export 从多维表格源生成，勿手改。
using System;
using System.Collections.Generic;
using KFramwork;

public class FishData : ActorData
{
    public int Volume;
    public float Probability;
    public int Level;
    public float Speed;
    public string Description;
    public string ImagePath;
    public float DeathRotationAngle;
    public string PathId;
    public int Hp;

    public virtual void CopyInstance(FishData target)
    {
        target.Name = Name;
        target.Volume = Volume;
        target.Probability = Probability;
        target.Level = Level;
        target.Speed = Speed;
        target.Description = Description;
        target.ImagePath = ImagePath;
        target.DeathRotationAngle = DeathRotationAngle;
        target.PathId = PathId;
        target.Hp = Hp;
    }
}
