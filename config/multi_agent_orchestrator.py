import toml

# Charge la configuration
config = toml.load("config/config.multi-llm.toml")

# Classe agent générique (à adapter pour les vrais appels API)
class AgentLLM:
    def __init__(self, conf, name):
        self.model = conf["model"]
        self.name = name

    def run(self, prompt, context=None):
        # Ici tu branches l'appel API réel selon self.model
        return f"[{self.name}] {self.model} répond à : {prompt}"

# Instanciation des agents
agent_claude = AgentLLM(config["llm_claude"], "Chef de projet")
agent_gemini = AgentLLM(config["llm_gemini"], "Rédacteur/Reviewer")
agent_openai = AgentLLM(config["llm_openai"], "Développeur")

# Fonction d'orchestration avec itérations automatiques
def multi_agent_iteration(task, context, agents, n_iter=5):
    print(f"Mission initiale : {task}\n")
    # 1ère version par le chef de projet
    output = agents["chef"].run(task, context)
    print(f"Version 1 (Chef de projet) :\n{output}\n")
    for i in range(2, n_iter + 1):
        # Reviewer (Gemini) critique/améliore
        critique = agents["reviewer"].run(
            f"Voici la version actuelle : {output}\nPropose des améliorations ou corrige les erreurs.", context)
        print(f"Feedback {i-1} (Reviewer) :\n{critique}\n")
        # Spécialiste (OpenAI) applique les suggestions
        output = agents["specialist"].run(
            f"Améliore ce livrable selon ces suggestions : {critique}", context)
        print(f"Version {i} (Spécialiste) :\n{output}\n")
    print("Livrable final :\n" + output)
    return output

if __name__ == "__main__":
    # Exemple de mission
    mission = "Rédige une newsletter pour le lancement du site web du client X. Le ton doit être dynamique et professionnel."
    context = {}  # Ajoute ici des infos de contexte si besoin

    # Mapping des rôles
    agents = {
        "chef": agent_claude,        # Chef de projet (Claude)
        "reviewer": agent_gemini,    # Reviewer (Gemini)
        "specialist": agent_openai   # Spécialiste (GPT-4o)
    }

    # Lance 5 itérations automatiques
    multi_agent_iteration(mission, context, agents, n_iter=5)
