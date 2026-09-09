using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

#region 脚本信息
//*******************************
//文件名：	Inventory.cs
//作者：		积极の咸鱼
//创建时间：	2022-04-17 18:53:14
//描述：     背包制作
//*******************************
#endregion

public class Inventory : MonoBehaviour
{
    [Tooltip("拾取按钮")]
    public Button btn_pickup;
    [Tooltip("背包物品槽")]
    public GameObject item;
    [Tooltip("物品精灵图")]
    public Sprite[] sprites;

    //生成物品的父物体
    private GameObject content;

    //键：物品名称，值：物品数量
    private Dictionary<string, int> itemsDic = new Dictionary<string, int>();

    //键：物品名称，值：物品对象
    private Dictionary<string, GameObject> objsDic = new Dictionary<string, GameObject>();

    // Start is called before the first frame update
    void Start()
    {
        content = GameObject.Find("Canvas/Inventory/Viewport/Content");
        UIBind.BindClick(btn_pickup, OnClickPickUp); 
    }

    /// <summary>
    /// 拾取按钮绑定事件
    /// </summary>
    void OnClickPickUp()
    {
        //随机生成物品
        Sprite sprite = sprites[Random.Range(0,sprites.Length)];
        if (itemsDic.ContainsKey(sprite.name))
        {
            itemsDic[sprite.name]++;
            objsDic[sprite.name].transform.Find("num").GetComponent<Text>().text = "x" + itemsDic[sprite.name].ToString();
        }
        else
        {
            itemsDic.Add(sprite.name, 1);
            GameObject obj = Instantiate(item, content.transform);
            Image image = obj.transform.Find("slot").GetComponent<Image>();
            image.sprite = sprite;
            Text text = obj.transform.Find("num").GetComponent<Text>();
            text.text = "x" + itemsDic[sprite.name].ToString();
            obj.GetComponentInChildren<Button>().onClick.AddListener(delegate ()
            {
                OnClickUse(obj, sprite.name, text);
            });
            objsDic.Add(sprite.name, obj);
        }
    }

    /// <summary>
    /// 使用按钮绑定事件
    /// </summary>
    /// <param name="obj">使用物品对象</param>
    /// <param name="name">使用物品名称</param>
    /// <param name="text">剩余数量文本</param>
    void OnClickUse(GameObject obj, string name, Text text)
    {
        itemsDic[name]--;           //剩余数量减1
        if(itemsDic[name] <= 0)     //如果使用完
        {
            itemsDic.Remove(name);
            objsDic.Remove(name);
            Destroy(obj);
        }
        else                        //如果没有使用完
        {
            text.text = "x" + itemsDic[name].ToString();
        }
    }
}
