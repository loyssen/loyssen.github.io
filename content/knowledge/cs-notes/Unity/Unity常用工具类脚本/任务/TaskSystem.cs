using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

#region 脚本信息
//*******************************
//文件名：	TaskSystem.cs
//作者：		积极の咸鱼
//创建时间：	2022-05-21 17:25:14
//描述：      任务系统
//*******************************
#endregion

public class TaskSystem : MonoBehaviour
{
    public Button btnKill;
    public Button btnPick;
    public Text textAward;

    public GameObject taskItem;

    public TaskItem[] items;

    private int award = 0;
    private List<GameObject> objs = new List<GameObject>();

    // Start is called before the first frame update
    void Start()
    {
        GameObject content = GameObject.Find("Canvas/Panel/Scroll View/Viewport/Content");
        foreach (var it in items)
        {
            GameObject obj = Instantiate(taskItem, content.transform);
            objs.Add(obj);
            obj.transform.GetChild(0).GetComponent<Text>().text = it.taskName;
            obj.transform.GetChild(1).GetComponent<Text>().text = string.Format("{0:d} / {1:d}",it.taskNow,it.taskTarget);
            obj.transform.GetChild(2).GetComponent<Button>().onClick.AddListener(delegate ()
            {
                OnClickTask(it,obj);
            });
        }
        btnKill.onClick.AddListener(delegate ()
        {
            OnClickTest(0);
        });
        btnPick.onClick.AddListener(delegate ()
        {
            OnClickTest(1);
        });
    }
    private void OnClickTest(int i)
    {
        if(items[i].taskState == 1 && items[i].taskNow < items[i].taskTarget)
        {
            items[i].taskNow++;
            if (items[i].taskNow == items[i].taskTarget)
            {
                items[i].taskState = 2;
            }
            objs[i].transform.GetChild(1).GetComponent<Text>().text = string.Format("{0:d} / {1:d}", items[i].taskNow, items[i].taskTarget);
            if (items[i].taskState == 2)
            {
                objs[i].transform.GetChild(2).GetComponentInChildren<Text>().text = "领取奖励";

            }
        }
        
    }
    private void OnClickTask(TaskItem item,GameObject obj)
    {
        if(item.taskState == 0)
        {
            item.taskState = 1;
            obj.transform.GetChild(2).GetComponentInChildren<Text>().text = "待完成";
        }

        else if(item.taskState == 2)
        {
            award += item.taskAward;
            textAward.text = string.Format("金币：{0:d}", award);
            Destroy(obj);
        }
    }

}
