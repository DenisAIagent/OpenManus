from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import os
import re

# Import orchestrateur (adapté à ton arborescence)
from config.multi_agent_orchestrator import run_orchestration

app = FastAPI(
    title="OpenManus Multi-Agent API",
    description="API pour orchestration multi-agents avec Claude, GPT et Gemini",
    version="1.0.0"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Masquage des clés API ---
def mask_api_keys(text: str) -> str:
    api_keys = [
        os.environ.get("GEMINI_API_KEY", ""),
        os.environ.get("OPENAI_API_KEY", ""),
        os.environ.get("CLAUDE_API_KEY", ""),
    ]
    for key in api_keys:
        if key:
            text = text.replace(key, "****REDACTED_API_KEY****")
    text = re.sub(r'key=[A-Za-z0-9_\-]+', 'key=****REDACTED_API_KEY****', text)
    return text

# --- Modèles de données ---
class OrchestrationRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    iterations: Optional[int] = 3

class OrchestrationResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    iterations: Optional[int] = None
    agents_used: Optional[list] = None

class SimpleTaskRequest(BaseModel):
    task: str

# --- Endpoints ---

@app.get("/")
def root():
    return {
        "message": "OpenManus Multi-Agent API",
        "status": "active",
        "endpoints": {
            "orchestration": "/run",
            "simple": "/run/simple",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "agents": ["Claude", "GPT", "Gemini"],
        "version": "1.0.0"
    }

@app.post("/run", response_model=OrchestrationResponse)
async def run_orchestration_endpoint(request: OrchestrationRequest):
    try:
        logger.info(f"Nouvelle requête d'orchestration: {mask_api_keys(request.task[:100])}...")
        if not request.task or len(request.task.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="La tâche doit contenir au moins 10 caractères"
            )
        if request.iterations and (request.iterations < 1 or request.iterations > 10):
            raise HTTPException(
                status_code=400,
                detail="Le nombre d'itérations doit être entre 1 et 10"
            )
        # Utilise le fallback Gemini→GPT dans l'orchestration si besoin
        result = await run_orchestration(
            task=request.task,
            context=request.context,
            n_iter=request.iterations or 3
        )
        logger.info(f"Orchestration terminée avec succès: {result['success']}")
        # Masque les clés dans la réponse finale aussi
        result["result"] = mask_api_keys(result.get("result", ""))
        result["error"] = mask_api_keys(result.get("error", "")) if result.get("error") else None
        return OrchestrationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error_message = mask_api_keys(str(e))
        logger.error(f"Erreur lors de l'orchestration: {error_message}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors de l'orchestration: {error_message}"
        )

@app.post("/run/simple")
async def simple_orchestration(request: SimpleTaskRequest):
    """
    Version simplifiée pour tests rapides (paramètre dans le body JSON)
    """
    try:
        # Utilise le fallback Gemini→GPT aussi pour ce mode simple !
        result = await call_agent_with_fallback(gemini_agent, gpt_agent, task=request.task, n_iter=2)
        return {"result": mask_api_keys(result["result"] if result["success"] else result["error"])}
    except Exception as e:
        error_message = mask_api_keys(str(e))
        raise HTTPException(status_code=500, detail=error_message)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Requête reçue: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Réponse envoyée: {response.status_code}")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
