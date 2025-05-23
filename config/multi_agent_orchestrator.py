import toml

# Charge la config multi-LLM
config = toml.load("config.toml")

class AgentLLM:
    def __init__(self, conf):
        self.model = conf["model"]
        self.base_url = conf["base_url"]
        self.api_key = conf["api_key"]
        self.max_tokens = conf.get("max_tokens", 4096)
        self.temperature = conf.get("temperature", 0.0)
        # Ajoute ici la logique d'appel API selon le provider

    def run(self, prompt, context=None):
        # Place ici la logique API pour chaque provider
        # (ex: requests.post pour OpenAI, Anthropic, Google)
        return f"[{self.model}] Réponse simulée à '{prompt}'"

# Instancie les agents
agent_claude = AgentLLM(config["llm_claude"])
agent_gemini = AgentLLM(config["llm_gemini"])
agent_openai = AgentLLM(config["llm_openai"])

class TeamLeaderAgent:
    def __init__(self, agents):
        self.agents = agents

    def dispatch(self, task, context=None):
        # Logique simple d'aiguillage (à personnaliser selon ton besoin)
        task_lower = task.lower()
        if "newsletter" in task_lower or "contenu" in task_lower:
            return self.agents["gemini"].run(task, context)
        elif "code" in task_lower or "développement" in task_lower:
            return self.agents["openai"].run(task, context)
        else:
            # Pour une mission complexe, découpage et dispatch
            return self.agents["claude"].run(f"Planifie et répartis la mission suivante : {task}", context)

# Utilisation
team_leader = TeamLeaderAgent({
    "claude": agent_claude,
    "gemini": agent_gemini,
    "openai": agent_openai
})

# Exemple d'appel
if __name__ == "__main__":
    mission = "Créer un site web pour le client X avec une newsletter et un back-end automatisé."
    print(team_leader.dispatch(mission))
    print(team_leader.dispatch("Rédige une newsletter pour la campagne d'été"))
    print(team_leader.dispatch("Développe un script d'automatisation pour les emails"))
