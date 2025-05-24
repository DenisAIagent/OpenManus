import toml
import httpx
import asyncio
import json
from typing import Optional, Dict, Any
import os

# Charge la configuration
config = toml.load("config/config.toml")

class AgentLLM:
    def __init__(self, conf: Dict, name: str):
        self.model = conf["model"]
        self.base_url = conf["base_url"]
        self.api_key = os.getenv(conf["api_key"].replace("${", "").replace("}", ""))
        self.max_tokens = conf.get("max_tokens", 4096)
        self.temperature = conf.get("temperature", 0.0)
        self.name = name
        
    async def run(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Appel API réel selon le modèle configuré"""
        try:
            if "claude" in self.model.lower():
                return await self._call_claude(prompt, context)
            elif "gpt" in self.model.lower() or "openai" in self.base_url:
                return await self._call_openai(prompt, context)
            elif "gemini" in self.model.lower():
                return await self._call_gemini(prompt, context)
            else:
                return f"[{self.name}] Modèle non supporté: {self.model}"
        except Exception as e:
            return f"[{self.name}] Erreur lors de l'appel API: {str(e)}"
    
    async def _call_claude(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Appel à l'API Claude (Anthropic)"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        messages = [{"role": "user", "content": prompt}]
        if context:
            context_str = f"Contexte: {json.dumps(context, indent=2)}\n\n"
            messages[0]["content"] = context_str + prompt
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]
    
    async def _call_openai(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Appel à l'API OpenAI/GPT"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = [{"role": "user", "content": prompt}]
        if context:
            context_str = f"Contexte: {json.dumps(context, indent=2)}\n\n"
            messages[0]["content"] = context_str + prompt
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _call_gemini(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Appel à l'API Gemini (Google)"""
        full_prompt = prompt
        if context:
            context_str = f"Contexte: {json.dumps(context, indent=2)}\n\n"
            full_prompt = context_str + prompt
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "temperature": self.temperature
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]

# Instanciation des agents
agent_claude = AgentLLM(config["llm_claude"], "Chef de projet")
agent_gemini = AgentLLM(config["llm_gemini"], "Rédacteur/Reviewer")
agent_openai = AgentLLM(config["llm_openai"], "Développeur")

async def multi_agent_iteration(task: str, context: Dict[str, Any], agents: Dict[str, AgentLLM], n_iter: int = 5) -> str:
    """Fonction d'orchestration avec itérations automatiques"""
    print(f"Mission initiale : {task}\n")
    
    # 1ère version par le chef de projet
    output = await agents["chef"].run(task, context)
    print(f"Version 1 (Chef de projet) :\n{output}\n")
    
    for i in range(2, n_iter + 1):
        # Reviewer (Gemini) critique/améliore
        critique_prompt = f"Voici la version actuelle : {output}\n\nPropose des améliorations concrètes ou corrige les erreurs. Sois constructif et précis."
        critique = await agents["reviewer"].run(critique_prompt, context)
        print(f"Feedback {i-1} (Reviewer) :\n{critique}\n")
        
        # Spécialiste (OpenAI) applique les suggestions
        improvement_prompt = f"Améliore ce livrable selon ces suggestions :\n\nLivrable actuel:\n{output}\n\nSuggestions:\n{critique}\n\nFournis la version améliorée complète."
        output = await agents["specialist"].run(improvement_prompt, context)
        print(f"Version {i} (Spécialiste) :\n{output}\n")
    
    print("Livrable final :\n" + output)
    return output

async def run_orchestration(task: str, context: Optional[Dict[str, Any]] = None, n_iter: int = 3) -> Dict[str, Any]:
    """Point d'entrée principal pour l'orchestration"""
    if context is None:
        context = {}
    
    try:
        # Mapping des rôles
        agents = {
            "chef": agent_claude,        # Chef de projet (Claude)
            "reviewer": agent_gemini,    # Reviewer (Gemini)
            "specialist": agent_openai   # Spécialiste (GPT-4)
        }
        
        # Lance les itérations
        result = await multi_agent_iteration(task, context, agents, n_iter)
        
        return {
            "success": True,
            "result": result,
            "iterations": n_iter,
            "agents_used": list(agents.keys())
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "result": None
        }

if __name__ == "__main__":
    # Exemple de test
    async def test_orchestration():
        mission = "Rédige une newsletter pour le lancement du site web du client TechCorp. Le ton doit être dynamique et professionnel."
        context = {
            "client": "TechCorp",
            "product": "Site web e-commerce",
            "target": "PME et startups",
            "deadline": "Fin de semaine"
        }
        
        result = await run_orchestration(mission, context, n_iter=3)
        print(f"Résultat final: {result}")
    
    # Lance le test
    asyncio.run(test_orchestration())
