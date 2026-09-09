using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using LitJson;
using Newtonsoft.Json.Linq;

#region 脚本信息
//*******************************
//文件名：	JsonParser.cs
//作者：		积极の咸鱼
//创建时间：	2022-02-01 15:22:33
//描述：     json解析
//*******************************
#endregion

public class JsonParser : MonoBehaviour
{
    string strJson;   //json字符串
    void Start()
    {
        //读取json文件并转换为字符串
        strJson = File.ReadAllText("Assets/Scripts/test.json");
    }

    /// <summary>
    /// LitJson解析字符串
    /// </summary>
    /// <param name="str">json字符串</param>
    /// <returns></returns>
    JsonData LitJsonParser(string str)
    {
        return JsonMapper.ToObject(str);
    }

    /// <summary>
    /// Newtonsoft解析json
    /// </summary>
    /// <param name="str">json字符串</param>
    /// <returns></returns>
    JObject NewtonsoftParser(string str)
    {
        return JObject.Parse(str);
    }

    public void LitJsonTest()
    {
        JsonData json = LitJsonParser(strJson);
        Debug.Log("LitJson解析---"+json["info"][0]["name"]);
    }

    public void NewtonsoftTest()
    {
        JObject json = NewtonsoftParser(strJson);
        JArray array = JArray.Parse(json["info"].ToString());
        Debug.Log("Newtonsoft解析---" + array[0]["name"]);
    }
    
}
