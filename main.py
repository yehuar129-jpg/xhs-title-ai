} fastapi 从
快速API
从 pydantic 导入 BaseModel
导入 os
导入 请求

应用 = FastAPI()

# 输入结构
类 请求( BaseModel):
    关键词: str


# ===== AI调用函数 =====
定义 调用人工智能(关键词: 字符串):
    api_key = "将你的API_KEY放这里"

    url = "https://openrouter.ai/api/v1/chat/completions"

    头部 = {
        "授权": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"'''
你是一个小红书爆款标题专家。

请围绕关键词「{keyword}」生成10条爆款标题：

要求：
- 强情绪
- 强吸引力
- 有点击欲望
- 像小红书真实爆款
- 可以带数字 / 对比 / 反差

只输出标题列表，不要解释
"""

    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()

    return result["choices"][0]["message"]["content"]


# ===== API =====
@app.get("/")
def root():
    返回 {"状态": "正常", "消息": "AI 小红书标题生成器正在运行"}


@app.post("/generate")
定义 生成(请求: Request):
    结果 = 调用人工智能(请求.关键词)

    return {
        "keyword": req.keyword,
        "result": result
    }
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

class Request(BaseModel):
    keyword: str


def call_ai(keyword: str):
    api_key = "你的API_KEY"

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"""
你是小红书爆款标题专家，请围绕「{keyword}」生成10条爆款标题，要强吸引力、强情绪、强点击欲望。
"""

    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    res = requests.post(url, headers=headers, json=data)
    return res.json()["choices"][0]["message"]["content"]


# ===== API接口 =====
@app.post("/generate")
def generate(req: Request):
    result = call_ai(req.keyword)
    return {"result": result}


# ===== 🌐 网页页面（重点）=====
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>小红书AI爆款标题生成器</title>
        <style>
            body {
                font-family: Arial;
                background: #f5f5f5;
                text-align: center;
                padding-top: 80px;
            }
            input {
                width: 300px;
                padding: 10px;
                font-size: 16px;
            }
            button {
                padding: 10px 20px;
                font-size: 16px;
                background: #ff2442;
                color: white;
                border: none;
                cursor: pointer;
                margin-left: 10px;
            }
            #result {
                margin-top: 30px;
                white-space: pre-wrap;
                background: white;
                padding: 20px;
                width: 60%;
                margin-left: auto;
                margin-right: auto;
                border-radius: 10px;
            }
        </style>
    </head>

    <body>
        <h1>🔥 小红书AI爆款标题生成器</h1>

        <input id="keyword" placeholder="输入关键词，例如：美甲店" />
        <button onclick="generate()">生成爆款标题</button>

        <div id="result"></div>

        <script>
            async function generate() {
                let keyword = document.getElementById("keyword").value;

                let res = await fetch("/generate", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({keyword})
                });

                let data = await res.json();

                document.getElementById("result").innerText = data.result;
            }
        </script>
    </body>
    </html>
    """
