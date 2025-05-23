print(">>>> app/api_hello_world.py is being loaded <<<<")
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/run")
async def run_orchestration():
    return {"result": "Hello World from /run endpoint"}

# Pour le run local (inutile sur Railway, mais pratique en dev)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api_hello_world:app", host="0.0.0.0", port=8000, reload=True)
