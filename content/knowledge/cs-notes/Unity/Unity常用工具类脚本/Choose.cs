using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

#region 脚本信息
//*******************************
//文件名：	Choose.cs
//作者：		积极の咸鱼
//创建时间：	2022-04-17 10:59:53
//描述：    实现单选，多选效果
//*******************************
#endregion

public enum Mode
{
    single,
    mutiply
}

public class Choose : MonoBehaviour
{
    public Mode mode;
    public Toggle[] toggles;
    public Button btn_submit;


    // Start is called before the first frame update
    void Start()
    {
        UIBind.BindClick(btn_submit, OnClickSubmit);
        if (mode == Mode.mutiply)
        {
            foreach (var it in toggles)
            {
                it.group = null;
            }
        }
            
    }

    void OnClickSubmit()
    {
        foreach(var it in toggles)
        {
            if (it.isOn)
            {
                Debug.Log("已勾选——" + it.name);
            }
        }
        Debug.Log("已提交");
    }
}
