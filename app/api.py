print(">>>> app/api.py is being loaded <<<<")

# Imports standards
import sys
import traceback
from fastapi import FastAPI, Request
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")
logger.setLevel(logging.INFO)

# Création de l'application FastAPI
app = FastAPI()

# Route de santé basique
@app.get("/health")
async def health():
    return {"status": "ok"}

# Wrapper pour les imports potentiellement problématiques
try:
    logger.info("Tentative d'import des modules personnalisés...")
    from app.agent.manus import Manus
    from app.logger import logger as app_logger
    
    # Remplacer le logger standard par celui de l'application
    logger = app_logger
    
    CUSTOM_IMPORTS_SUCCESS = True
    logger.info("Imports personnalisés réussis")
except Exception as e:
    CUSTOM_IMPORTS_SUCCESS = False
    error_msg = f"ERREUR D'IMPORT: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    print(error_msg, file=sys.stderr)

# Endpoint principal avec gestion d'erreur
@app.post("/run")
async def run_orchestration(request: Request):
    # Vérifier si les imports personnalisés ont réussi
    if not CUSTOM_IMPORTS_SUCCESS:
        return {
            "error": "Configuration error: Custom modules could not be imported. Check logs for details.",
            "status": "error"
        }
    
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        if not prompt.strip():
            logger.warning("Empty prompt provided.")
            return {"error": "Empty prompt."}

        logger.info("Processing request...")
        # Crée et utilise l'agent Manus
        agent = await Manus.create()
        try:
            await agent.run(prompt)
            logger.info("Request processing completed.")
            return {"result": "OK"}
        except Exception as e:
            error_msg = f"Error during agent execution: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
        finally:
            await agent.cleanup()
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {"error": str(e), "details": error_msg}

# Pour le run local
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)
