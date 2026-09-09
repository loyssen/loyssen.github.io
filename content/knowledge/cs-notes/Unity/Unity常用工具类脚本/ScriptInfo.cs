using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Text.RegularExpressions;

#region 脚本信息
//*******************************
//文件名：		#ScriptName#
//作者：		#AuthorName#
//创建时间：	#CreateTime#
//描述：
//*******************************
#endregion

public class ScriptInfo : UnityEditor.AssetModificationProcessor
{
    private static void OnWillCreateAsset(string path)
    {
        path = path.Replace(".meta", "");
        if (path.EndsWith(".cs"))
        {
            string info = File.ReadAllText(path);
            string fileName = Regex.Match(path, @"[^/]*$").Value;
            info = info.Replace("#ScriptName#", fileName)
                .Replace("#AuthorName#", "积极の咸鱼")
                .Replace("#CreateTime#", System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            File.WriteAllText(path, info);
        }
    }
}
