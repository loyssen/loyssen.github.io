using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using LitJson;
using Newtonsoft.Json.Linq;

#region 脚本信息
//*******************************
//文件名：	JsonPacker.cs
//作者：		积极の咸鱼
//创建时间：	2022-02-07 19:33:23
//描述：     Json封装
//*******************************
#endregion

public class JsonPacker : MonoBehaviour
{
    public void LitJsonPacker()
    {
        JsonData litJsonInfo = new JsonData();
        JsonData info1 = new JsonData();
        JsonData info2 = new JsonData();

        info1["name"] = "peter";
        info1["age"] = "21";

        info2["name"] = "bob";
        info2["age"] = "22";

        JsonData infos = new JsonData();
        infos.SetJsonType(JsonType.Array);
        infos.Add(info1);
        infos.Add(info2);

        litJsonInfo["infos"] = infos;

        Debug.Log("LitJson封装---" + litJsonInfo["infos"][1]["name"]);

    }

    public void newtonsoftPacker()
    {
        JObject newtonsoftInfo = new JObject();
        JObject info1 = new JObject();
        JObject info2 = new JObject();

        info1["name"] = "peter";
        info1["age"] = "21";

        info2["name"] = "bob";
        info2["age"] = "22";

        JArray infos = new JArray();
        infos.Add(info1);
        infos.Add(info2);

        newtonsoftInfo["infos"] = infos;

        Debug.Log("Newtonsoft封装---" + newtonsoftInfo["infos"][1]["name"]);
    }
}
