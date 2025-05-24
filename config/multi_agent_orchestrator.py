import toml
import httpx
import asyncio
import json
import os
import re
from typing import Optional, Dict, Any

# Charge la configuration (chemin relatif à adapter si besoin)
config = toml.load("config/config.toml")

def mask_api_keys(text: str) -> str:
    """Masque les clés API dans les messages/logs/réponses."""
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

class AgentLLM:
    def __init__(self, conf: Dict, name: str):
        self.model = conf["model"]
        self.base_url = conf["base_url"]
        self.api_key = os.getenv(conf["api_key"].replace("${", "").replace("}", ""))
        self.max_tokens = conf.get("max_tokens", 4096)
        self.temperature = conf.get("temperature", 0.0)
        self.name = name
        
    async def run(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Appel API réel selon le modèle configuré, masquage d'erreur"""
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
            return mask_api_keys(f"[{self.name}] Erreur lors de l'appel API: {str(e)}")
    
    async def _call_claude(self, prompt: str, context: Optional[Dict] = None) -> str:
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

# Instanciation des agents (objets globaux pour fallback)
agent_claude = AgentLLM(config["llm_claude"], "Chef de projet")
agent_gemini = AgentLLM(config["llm_gemini"], "Rédacteur/Reviewer")
agent_openai = AgentLLM(config["llm_openai"], "Développeur")

async def run_with_fallback_gemini(prompt, context=None):
    """
    Appelle Gemini, fallback sur GPT-4o en cas d'erreur 429/rate limit.
    """
    try:
        return await agent_gemini.run(prompt, context)
    except Exception as e:
        e_str = str(e)
        if "429" in e_str or "Too Many Requests" in e_str:
            # Fallback sur GPT
            return await agent_openai.run(prompt, context)
        return mask_api_keys(f"[Reviewer/Gemini] Erreur: {e_str}")

async def multi_agent_iteration(task: str, context: Dict[str, Any], agents: Dict[str, AgentLLM], n_iter: int = 3) -> str:
    """
    Orchestration principale avec fallback Gemini.
    """
    output = await agents["chef"].run(task, context)
    for i in range(2, n_iter + 1):
        critique_prompt = f"Voici la version actuelle : {output}\n\nPropose des améliorations concrètes ou corrige les erreurs. Sois constructif et précis."
        critique = await run_with_fallback_gemini(critique_prompt, context)
        improvement_prompt = f"Améliore ce livrable selon ces suggestions :\n\nLivrable actuel:\n{output}\n\nSuggestions:\n{critique}\n\nFournis la version améliorée complète."
        output = await agents["specialist"].run(improvement_prompt, context)
    return mask_api_keys(output)

async def run_orchestration(task: str, context: Optional[Dict[str, Any]] = None, n_iter: int = 3) -> Dict[str, Any]:
    """Entrée principale API orchestration multi-agent."""
    if context is None:
        context = {}
    try:
        agents = {
            "chef": agent_claude,        # Chef de projet (Claude)
            "reviewer": agent_gemini,    # Reviewer (Gemini, fallback géré)
            "specialist": agent_openai   # Spécialiste (GPT-4)
        }
        result = await multi_agent_iteration(task, context, agents, n_iter)
        return {
            "success": True,
            "result": mask_api_keys(result),
            "iterations": n_iter,
            "agents_used": list(agents.keys())
        }
    except Exception as e:
        return {
            "success": False,
            "error": mask_api_keys(str(e)),
            "result": None
        }

# À importer dans api.py :
__all__ = ["run_orchestration"]
