from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def root():
    return {"hello": "world"}

@app.post("/run")
async def run_orchestration(request: Request):
    return {"result": "API OK"}
