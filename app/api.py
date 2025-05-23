@app.post("/run")
async def run_orchestration(request: Request):
    print("DEBUG: Requête /run reçue")
    try:
        data = await request.json()
        print("DEBUG: Données reçues:", data)
        prompt = data.get("prompt", "")
        if not prompt.strip():
            print("DEBUG: Prompt vide")
            return {"error": "Empty prompt."}
        print("DEBUG: Création agent Manus...")
        agent = await Manus.create()
        print("DEBUG: Agent créé, exécution...")
        await agent.run(prompt)
        print("DEBUG: Execution terminée")
        return {"result": "OK"}
    except Exception as e:
        print("DEBUG: Exception capturée:", e)
        return {"error": str(e)}
