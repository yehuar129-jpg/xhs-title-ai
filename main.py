from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Request(BaseModel):
    keyword: str

@app.get("/")
def root():
    return {"status": "ok", "msg": "xiaohongshu title api running"}

@app.post("/generate")
def generate(req: Request):
    keyword = req.keyword

    titles = [
        f"{keyword}真的别乱做，90%的人都踩坑了",
        f"我靠{keyword}直接翻身了，方法很简单",
        f"{keyword}新手必看：3天起号实操",
        f"普通人做{keyword}，怎么月入1万？",
        f"{keyword}爆火的秘密，其实就这1点"
    ]

    return {
        "keyword": keyword,
        "titles": titles
    }
