// 自动生成文件——由 duowei_export 从多维表格源生成，勿手改。
using System;
using System.Collections.Generic;
using KFramwork;

public class QueueGroupData : GroupData
{
    public float EntryInterval;

    public override void CopyInstance(GroupData target)
    {
        base.CopyInstance(target);
        if (target is QueueGroupData t)
        {
            t.EntryInterval = EntryInterval;
        }
    }
}
