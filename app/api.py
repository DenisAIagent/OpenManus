import asyncio
from fastapi import FastAPI, Request
from app.agent.manus import Manus
from app.logger import logger

app = FastAPI()

@app.post("/run")
async def run_orchestration(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    if not prompt.strip():
        logger.warning("Empty prompt provided.")
        return {"error": "Empty prompt."}

    logger.warning("Processing your request...")
    # Crée et utilise l'agent Manus comme dans main.py
    agent = await Manus.create()
    try:
        await agent.run(prompt)
        logger.info("Request processing completed.")
        # Ici, adapte le retour selon ce que produit ton agent,
        # par exemple si agent.run() retourne un résultat :
        # result = await agent.run(prompt)
        # return {"result": result}
        return {"result": "OK"}  # Placeholder
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}
    finally:
        await agent.cleanup()

# Pour le run local (inutile sur Railway, mais pratique en dev)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)
