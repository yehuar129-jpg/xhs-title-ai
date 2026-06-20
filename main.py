} fastapi 从
 fastapi 
from pydantic import BaseModel
import os
import requests

app = FastAPI()

# ===== 输入结构 =====
class Request(BaseModel):
    keyword: str


# ===== AI调用函数 =====
def call_ai(keyword: str):
    api_key = "你的API_KEY放这里"

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"""
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
    return {"status": "ok", "msg": "AI xiaohongshu title generator running"}


@app.post("/generate")
def generate(req: Request):
    result = call_ai(req.keyword)

    return {
        "keyword": req.keyword,
        "result": result
    }
