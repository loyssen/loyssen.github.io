using System.Collections;
using System.Collections.Generic;
using UnityEngine;

#region 脚本信息
//*******************************
//文件名：	TaskItem.cs
//作者：		积极の咸鱼
//创建时间：	2022-05-21 17:09:09
//描述：
//*******************************
#endregion

[CreateAssetMenu(fileName ="taskItem",menuName ="CreateItem/taskItem")]
public class TaskItem : ScriptableObject
{
    public string taskName;
    public int taskTarget;
    public int taskNow;
    public int taskAward;
    public int taskState;
}
