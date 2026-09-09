using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using System;

#region 脚本信息
//*******************************
//文件名：	UIBind.cs
//作者：		积极の咸鱼
//创建时间：	2022-02-25 19:27:14
//描述：     UI绑定
//*******************************
#endregion

public class UIBind
{
    public static void BindClick(Button button, UnityEngine.Events.UnityAction callback)
    {
        button.onClick.AddListener(callback);
    }

    public static void BindSelected(Toggle tg, UnityEngine.Events.UnityAction<bool> callback)
    {
        tg.onValueChanged.AddListener(callback);
    }

    public static void BindInputed(InputField input, UnityEngine.Events.UnityAction<string> callback)
    {
        input.onEndEdit.AddListener(callback);
    }

    public static void BindInputChanged(InputField input, UnityEngine.Events.UnityAction<string> callback)
    {
        input.onValueChanged.AddListener(callback);
    }

    public static void BindDropDown(Dropdown drop, UnityEngine.Events.UnityAction<int> callback)
    {
        drop.onValueChanged.AddListener(callback);
    }
}
