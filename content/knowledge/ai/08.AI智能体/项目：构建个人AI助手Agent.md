---
tags: [项目, Agent, ReAct, 实战]
created: 2026-06-29
difficulty: 🔴高级
estimated_time: 4-6 小时
---

# 🛠️ 项目：构建个人 AI 助手 Agent

> 用 ReAct 模式构建一个能搜索、算数、执行代码的个人 AI 助手。

---

## 项目目标

实现一个 ReAct 循环的 Agent，能自主使用工具完成用户的复杂任务。

---

## 完整实现

```python
import json
import re
from openai import OpenAI

# ============================================
# 工具定义
# ============================================
def search_web(query: str) -> str:
    """模拟搜索（实际接搜索引擎 API）"""
    # TODO: 接入真实的搜索 API
    return f"搜索结果: 关于'{query}'的相关信息..."

def calculate(expression: str) -> str:
    """安全计算数学表达式"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

def read_file(path: str) -> str:
    """读取文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f"文件内容:\n{f.read()[:2000]}"
    except Exception as e:
        return f"读取失败: {str(e)}"

def write_file(path: str, content: str) -> str:
    """写入文件"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"已写入 {path}"
    except Exception as e:
        return f"写入失败: {str(e)}"

TOOLS = {
    "search": search_web,
    "calculate": calculate,
    "read_file": read_file,
    "write_file": write_file,
}

# ============================================
# Agent 核心循环
# ============================================
class ReactAgent:
    def __init__(self, model="gpt-4", max_steps=10):
        self.client = OpenAI()  # 或本地模型
        self.model = model
        self.max_steps = max_steps
        self.history = []  # 保存 (thought, action, observation)
    
    def run(self, task: str) -> str:
        prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": task}
        ]
        
        for step in range(self.max_steps):
            print(f"\n{'='*50}")
            print(f"Step {step+1}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
            )
            
            text = response.choices[0].message.content
            print(f"💭 {text}")
            
            # 解析 Thought / Action / Final Answer
            thought, action_type, action_input = self._parse(text)
            
            if action_type == "FINAL":
                return action_input
            
            # 执行工具
            if action_type in TOOLS:
                observation = TOOLS[action_type](action_input)
                print(f"👁️ {observation}")
                
                self.history.append({
                    "thought": thought,
                    "action": f"{action_type}({action_input})",
                    "observation": observation,
                })
                
                # 将结果反馈给 LLM
                messages.append({"role": "assistant", "content": text})
                messages.append({
                    "role": "user",
                    "content": f"工具返回: {observation}\n请继续思考。"
                })
            else:
                messages.append({
                    "role": "user",
                    "content": f"没有叫 {action_type} 的工具。可用工具: {list(TOOLS.keys())}"
                })
        
        return "达到最大步数限制。"
    
    def _build_system_prompt(self):
        return f"""你是一个 ReAct Agent，可以使用工具来完成用户的请求。

可用工具:
{json.dumps({name: fn.__doc__ for name, fn in TOOLS.items()}, ensure_ascii=False, indent=2)}

回答格式（严格遵守）:

Thought: [你的思考过程]
Action: [工具名]([参数])
---或---
Thought: [你的思考过程]
Final Answer: [最终答案]

注意:
1. 每次只能调用一个工具
2. 必须等工具返回结果后再继续
3. 不要假装有结果，必须真的调用工具
"""

    def _parse(self, text):
        thought_match = re.search(r'Thought:\s*(.+?)(?=\n(?:Action:|Final))', text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""
        
        action_match = re.search(r'Action:\s*(\w+)\((.+?)\)', text)
        if action_match:
            return thought, action_match.group(1), action_match.group(2).strip('"').strip("'")
        
        final_match = re.search(r'Final Answer:\s*(.+)', text, re.DOTALL)
        if final_match:
            return thought, "FINAL", final_match.group(1).strip()
        
        return thought, "UNKNOWN", text

# ============================================
# 运行测试
# ============================================
if __name__ == "__main__":
    agent = ReactAgent()
    
    tasks = [
        "请帮我计算 (1234 * 5678) / 2 的结果",
        "搜索 '2024年AI最新突破'，然后将结果保存到 ai_news.txt",
    ]
    
    for task in tasks:
        print(f"\n{'#'*60}")
        print(f"📋 任务: {task}")
        print(f"{'#'*60}")
        
        result = agent.run(task)
        print(f"\n✅ 最终结果: {result}")
```

---

## 添加更多工具

```python
# 天气
def get_weather(location: str) -> str:
    """获取天气信息。参数: location=城市名"""
    import requests
    # 接入真实 API: https://wttr.in
    resp = requests.get(f"https://wttr.in/{location}?format=3")
    return resp.text

# Python 执行
def execute_python(code: str) -> str:
    """在沙箱中执行 Python 代码"""
    import subprocess
    result = subprocess.run(
        ["python", "-c", code],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout or result.stderr

TOOLS.update({
    "get_weather": get_weather,
    "execute_python": execute_python,
})
```

---

## 总结模板

```markdown
## 项目总结：个人 AI 助手 Agent

### 实现了什么
- ReAct 循环
- ___ 个工具
- 平均 ___ 步完成任务

### 遇到的问题
- 【工具解析不准确，优化了正则】
- 【LLM 有时跳过工具直接回答】

### 改进方向
- 记忆系统（历史对话）
- 异步工具调用
- 安全沙箱
```

---

## → 下一步

→ [[项目：多Agent协作系统]] — 多 Agent 协作
