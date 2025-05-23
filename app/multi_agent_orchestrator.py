from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

# ... (toute la logique d'orchestration/itérations ici)

@app.post("/run")
async def run_orchestration(request: Request):
    data = await request.json()
    mission = data.get("mission", "Rédige une newsletter pour le lancement du site web du client X.")
    context = data.get("context", {})
    agents = {
        "chef": agent_claude,
        "reviewer": agent_gemini,
        "specialist": agent_openai
    }
    result = multi_agent_iteration(mission, context, agents, n_iter=5)
    return {"result": result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
