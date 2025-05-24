from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

# Import de votre orchestrateur
from config.multi_agent_orchestrator import run_orchestration

app = FastAPI(
    title="OpenManus Multi-Agent API",
    description="API pour orchestration multi-agents avec Claude, GPT et Gemini",
    version="1.0.0"
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modèle de données pour les requêtes
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

# **NOUVEAU** : modèle pour run/simple
class SimpleTaskRequest(BaseModel):
    task: str

@app.get("/")
def root():
    return {
        "message": "OpenManus Multi-Agent API",
        "status": "active",
        "endpoints": {
            "orchestration": "/run",
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
    """
    Lance une orchestration multi-agents
    
    - **task**: La tâche à accomplir (obligatoire)
    - **context**: Contexte additionnel pour les agents (optionnel)
    - **iterations**: Nombre d'itérations (défaut: 3)
    """
    try:
        logger.info(f"Nouvelle requête d'orchestration: {request.task[:100]}...")
        
        # Validation de base
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
        
        # Lance l'orchestration
        result = await run_orchestration(
            task=request.task,
            context=request.context,
            n_iter=request.iterations or 3
        )
        
        logger.info(f"Orchestration terminée avec succès: {result['success']}")
        
        return OrchestrationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'orchestration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors de l'orchestration: {str(e)}"
        )

# 🚀 VERSION MODERNE : task reçu dans le BODY (JSON) pour /run/simple
@app.post("/run/simple")
async def simple_orchestration(request: SimpleTaskRequest):
    """
    Version simplifiée pour tests rapides (paramètre dans le body JSON)
    """
    try:
        result = await run_orchestration(task=request.task, n_iter=2)
        return {"result": result["result"] if result["success"] else result["error"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Middleware pour logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Requête reçue: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Réponse envoyée: {response.status_code}")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
