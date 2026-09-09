---
tags: [项目, LLM, 部署, API, 实战]
created: 2026-06-29
difficulty: 🔴高级
estimated_time: 2-4 小时
---

# 🛠️ 项目：部署个人 LLM 服务

> 把你的模型变成 API 服务，让任何应用都能调用。

---

## 方案对比

| 方案 | 难度 | 适合场景 |
|------|------|---------|
| **Ollama** | 🟢 极简 | 个人使用、快速体验 |
| **vLLM** | 🟡 中等 | 高并发生产环境 |
| **llama.cpp** | 🟡 中等 | CPU/混合推理 |
| **Transformers + FastAPI** | 🟡 中等 | 自定义需求 |

---

## 方案 A：Ollama（推荐入门）

### 安装与运行

```bash
# 安装 Ollama（支持 Windows/Mac/Linux）
# 官网: https://ollama.com 下载安装包

# 拉取模型
ollama pull qwen2:7b

# 运行
ollama run qwen2:7b
# > 你好！
# 你好！有什么可以帮你的？
```

### 使用自己的微调模型

```bash
# 1. 创建 Modelfile
cat > Modelfile << 'EOF'
FROM ./my_merged_model  # 或者 GGUF 文件路径
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
SYSTEM """你是一个有帮助的AI助手。"""
EOF

# 2. 导入
ollama create my-model -f Modelfile

# 3. 运行
ollama run my-model
```

### API 调用

```python
import requests
import json

def chat_ollama(prompt, model="qwen2:7b", system=None):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
    )
    return response.json()["message"]["content"]

# 测试
print(chat_ollama("什么是机器学习？"))
```

---

## 方案 B：vLLM（高并发生产）

### 安装与启动

```bash
pip install vllm

# 启动 API 服务
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9
```

### OpenAI 兼容的 API 调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # vLLM 不验证 key
)

response = client.chat.completions.create(
    model="Qwen/Qwen2-7B-Instruct",
    messages=[
        {"role": "user", "content": "解释 Transformer"}
    ],
    temperature=0.7,
    max_tokens=512,
)

print(response.choices[0].message.content)
```

> 💡 vLLM 的 API 与 OpenAI 完全兼容，直接替换 `base_url` 即可。

---

## 方案 C：FastAPI 自定义服务

```python
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import uvicorn

app = FastAPI(title="My LLM API")

# 加载模型
model_name = "./my_merged_model"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

class ChatRequest(BaseModel):
    messages: list[dict]
    temperature: float = 0.7
    max_tokens: int = 512

class ChatResponse(BaseModel):
    content: str

@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # 应用 chat template
    text = tokenizer.apply_chat_template(
        request.messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=request.temperature > 0,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    response = tokenizer.decode(
        outputs[0][inputs.input_ids.shape[1]:], 
        skip_special_tokens=True
    )
    
    return ChatResponse(content=response)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 前端接入示例

```html
<!DOCTYPE html>
<html>
<head><title>AI Chat</title></head>
<body>
    <div id="chat"></div>
    <input id="input" type="text" placeholder="输入消息...">
    <button onclick="send()">发送</button>

    <script>
    async function send() {
        const input = document.getElementById('input');
        const msg = input.value;
        input.value = '';
        
        const resp = await fetch('http://localhost:11434/api/chat', {
            method: 'POST',
            body: JSON.stringify({
                model: 'qwen2:7b',
                messages: [{role: 'user', content: msg}],
                stream: false,
            })
        });
        const data = await resp.json();
        document.getElementById('chat').innerHTML 
            += `<p><b>你:</b> ${msg}</p>`
            + `<p><b>AI:</b> ${data.message.content}</p>`;
    }
    </script>
</body>
</html>
```

---

## 性能优化备忘

| 优化项 | 做法 | 收益 |
|--------|------|------|
| 量化 | INT4/INT8 加载 | 显存减半 |
| Flash Attention | 安装 flash-attn 包 | 加速 + 省显存 |
| KV-Cache | 默认开启 | 推理加速 |
| Continuous Batching | vLLM 自动 | 吞吐量翻倍 |
| GPU 选择 | BF16 比 FP16 稳定 | 质量提升 |

---

## 总结

| 场景 | 推荐方案 |
|------|---------|
| 个人体验 | Ollama |
| 小团队 API | Ollama + FastAPI 代理 |
| 生产高并发 | vLLM |
| CPU 环境 | llama.cpp / Ollama CPU 模式 |
| 边缘设备 | llama.cpp + INT4 |

---

## → 下一步

→ [[../07.RAG检索增强生成/7.1 RAG原理与架构|RAG：检索增强生成]]
