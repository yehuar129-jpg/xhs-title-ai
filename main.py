from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/generate")
def generate():
    return {"msg": "hello"}
