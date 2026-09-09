using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;

#region 脚本信息
//*******************************
//文件名：	ButtonExt.cs
//作者：		积极の咸鱼
//创建时间：	2022-01-25 13:37:09
//描述：     按钮功能扩展
//*******************************
#endregion 

public class ButtonExt : MonoBehaviour,IPointerClickHandler,IPointerDownHandler,IPointerExitHandler,IPointerUpHandler
{
    [Header("鼠标检测时间")]
    public float pressDurationTime = 1;             //按压检测时间
    public float doubleClickIntervalTime = 0.5f;    //双击检测时间

    [Header("按钮事件")]
    public UnityEvent onDoubleClick;                //三种按钮事件
    public UnityEvent onPress;
    public UnityEvent onClick;

    private bool isDown;                            //是否按下
    private bool isPress;                           //是否按压
    private float downTime;                         //按压时间
    private float clickIntervalTime = 0;            //双击间隔时间
    private int clickTimes = 0;                     //单击次数


    public void OnPointerClick(PointerEventData eventData)  //鼠标点击
    {
        if (!isPress)
        {
            clickTimes += 1;
        }
        else
        {
            isPress = false;
        }
    }

    public void OnPointerDown(PointerEventData eventData)   //鼠标按下
    {
        isDown = true;
        downTime = 0;
    }

    public void OnPointerExit(PointerEventData eventData)   //鼠标移出
    {
        isDown = false;
        isPress = false;
    }

    public void OnPointerUp(PointerEventData eventData)     //鼠标抬起
    {
        isDown = false;
    }

    

    // Update is called once per frame
    void Update()
    {
        if (isDown)
        {
            downTime += Time.deltaTime;
            if(downTime > pressDurationTime && !isPress)
            {
                isPress = true;
                onPress.Invoke();
            }

        }
        if(clickTimes >= 1)
        {
            clickIntervalTime += Time.deltaTime;
            if(clickIntervalTime >= doubleClickIntervalTime)
            {
                if(clickTimes >= 2)
                {
                    onDoubleClick.Invoke();
                }
                else
                {
                    onClick.Invoke();
                }
                clickTimes = 0;
                clickIntervalTime = 0;
            }
        }
    }

    //测试
    public void Click()
    {
        Debug.Log("鼠标单击");
    }
    public void DoubleClick()
    {
        Debug.Log("鼠标双击");
    }
    public void Press()
    {
        Debug.Log("鼠标按压");
    }
}
