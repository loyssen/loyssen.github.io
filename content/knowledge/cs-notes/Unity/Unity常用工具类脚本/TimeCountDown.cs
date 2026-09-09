using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using UnityEngine.UI;
using DG.Tweening;

#region 脚本信息
//*******************************
//文件名：	TimeCountDown.cs
//作者：		积极の咸鱼
//创建时间：	2022-02-26 21:07:39
//描述：    倒计时
//*******************************
#endregion

public class TimeCountDown : MonoBehaviour
{
    public GameObject timeText; //显示文本
    public int totalTime;       //倒计时时间

    // Start is called before the first frame update
    void Start()
    {
        StartCoroutine(TimeCounter());  //开始倒计时
    }

    IEnumerator TimeCounter()
    {
        while(totalTime > 0)
        {
            timeText.GetComponent<Text>().text = totalTime.ToString();
            yield return new WaitForSeconds(1);
            totalTime--;
            if(totalTime == 3)      //在第三秒时变色且增加动画
            {
                timeText.GetComponent<Text>().color = Color.red;
                StartCoroutine(MoveText(totalTime));
            }
            if(totalTime == 0)      //倒计时结束
            {
                timeText.GetComponent<Text>().text = "game over!";
            }
        }
    }

    IEnumerator MoveText(int time)  //文本动画协程
    {
        while(time >= 0)
        {
            time--;
            timeText.transform.DOScale(5, 1).From();
            timeText.GetComponent<Text>().DOFade(0, 1).From();
            yield return new WaitForSeconds(1);
        }
    }
}
