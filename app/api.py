from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/run")
async def run_orchestration(request: Request):
    return {"result": "API OK"}
