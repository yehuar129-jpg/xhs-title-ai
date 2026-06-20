from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Req(BaseModel):
    keyword: str


@app.post("/generate")
def generate(req: Req):

    api_key = os.getenv("DEEPSEEK_API_KEY")  # 🔥 放环境变量

    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [{
            "role": "user",
            "content": f"生成10条小红书爆款标题：{req.keyword}"
        }]
    }

    res = requests.post(url, headers=headers, json=data)

    result = res.json()["choices"][0]["message"]["content"]

    return {"result": result}
