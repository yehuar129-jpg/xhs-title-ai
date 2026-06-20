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

    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{
            "role": "user",
            "content": f"生成10条小红书爆款标题，关键词：{keyword}"
        }]
    }

    res = requests.post(url, headers=headers, json=data)
    return res.json()["choices"][0]["message"]["content"]


# ===== API =====
@app.post("/generate")
def generate(req: Request):
    return {"result": call_ai(req.keyword)}


# ===== 🌐 网页（重点！）=====
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <meta charset="utf-8">
        <title>小红书AI标题生成器</title>
    </head>

    <body style="text-align:center; font-family:Arial; margin-top:80px;">

        <h1>🔥 小红书AI爆款标题生成器</h1>

        <input id="kw" placeholder="输入关键词" style="padding:10px; width:300px;">
        <button onclick="go()" style="padding:10px 20px;">生成</button>

        <pre id="res" style="margin-top:30px; white-space:pre-wrap;"></pre>

        <script>
            async function go(){
                let keyword = document.getElementById('kw').value;

                let res = await fetch('/generate', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({keyword})
                });

                let data = await res.json();

                document.getElementById('res').innerText = data.result;
            }
        </script>

    </body>
    </html>
    """
