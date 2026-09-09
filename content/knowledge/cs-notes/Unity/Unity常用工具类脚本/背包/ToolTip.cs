using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

#region 脚本信息
//*******************************
//文件名：	ToolTip.cs
//作者：		积极の咸鱼
//创建时间：	2022-04-17 19:56:36
//描述：      背包信息提示
//*******************************
#endregion

public class ToolTip : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
{
    public GameObject tip;

    public void OnPointerEnter(PointerEventData eventData)
    {
        tip.SetActive(true);
        tip.GetComponentInChildren<Text>().text = GetComponent<Image>().sprite.name;
    }

    public void OnPointerExit(PointerEventData eventData)
    {
        tip.SetActive(false);
    }

    
}
