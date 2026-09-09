// 自动生成文件——由 duowei_export 从多维表格源生成，勿手改。
using System;
using System.Collections.Generic;
using KFramwork;
using UnityEngine;

public class FormationData : ActorData
{
    public string Shape;
    public List<Vector2> Offsets;

    public virtual void CopyInstance(FormationData target)
    {
        target.Name = Name;
        target.Shape = Shape;
        target.Offsets = Offsets;
    }
}
