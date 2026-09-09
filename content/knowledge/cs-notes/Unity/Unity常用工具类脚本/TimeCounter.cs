using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using System;

#region 脚本信息
//*******************************
//文件名：	TimeCounter.cs
//作者：		积极の咸鱼
//创建时间：	2022-02-25 19:36:18
//描述：    计时器
//*******************************
#endregion

public class TimeCounter : MonoBehaviour
{
    public Text timeText;
    public Button btnStart;
    public Button btnRestart;

    private bool isCounting = false;  //是否计时
    private float countTime = 0;      //当前时间

    // Start is called before the first frame update
    void Start()
    {
        UIBind.BindClick(btnStart, StartTime);
        UIBind.BindClick(btnRestart, RestartTime);
    }

    // Update is called once per frame
    void Update()
    {
        if (isCounting)
        {
            countTime += Time.deltaTime;
            timeText.text = TimeFormatter(countTime);
        }
    }

    string TimeFormatter(float time)
    {
        int hour = (int)time / 3600;
        int min = (int)(time - hour * 3600) / 60;
        int sec = (int)(time - hour * 3600 - min * 60);
        return hour.ToString("D2") + ":" + min.ToString("D2") + ":" + sec.ToString("D2");
    }

    void StartTime()
    {
        isCounting = !isCounting;
    }

    void RestartTime()
    {
        countTime = 0;
        isCounting = true;
    }
}
