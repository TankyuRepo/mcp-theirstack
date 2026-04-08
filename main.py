import os
import httpx
from mcp.server.fastmcp import FastMCP


# Initialisation du serveur MCP
# Ce nom aide à identifier ton serveur dans les logs
mcp = FastMCP("TheirStack Technographics")

@mcp.tool()
async def get_company_technologies(
    company_domain: str | None = None,
    company_name: str | None = None,
    company_linkedin_url: str | None = None
) -> str:
    """
    Récupère la liste des technologies utilisées par une entreprise via l'API TheirStack.
    Tu dois fournir EXACTEMENT UN de ces trois paramètres: company_domain, company_name, ou company_linkedin_url.
    Attention: Cette action consomme 3 crédits API par recherche aboutie.
    """
    # Validation stricte des arguments d'entrée (exactement 1 argument attendu)
    inputs = [company_domain, company_name, company_linkedin_url]
    if sum(1 for x in inputs if x) != 1:
        return "Erreur: Tu dois fournir exactement UN paramètre parmi company_domain, company_name, ou company_linkedin_url."
    
    api_key = os.getenv("THEIRSTACK_API_KEY")
    if not api_key:
        return "Erreur interne: La clé API THEIRSTACK_API_KEY n'est pas configurée sur le serveur Cloud Run."

    url = "https://api.theirstack.com/v1/companies/technologies"
    
    # En-têtes HTTP avec la clé API (à vérifier si TheirStack utilise bien Bearer Token dans leur console)
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {}
    if company_domain:
        payload["company_domain"] = company_domain
    elif company_name:
        payload["company_name"] = company_name
    elif company_linkedin_url:
        payload["company_linkedin_url"] = company_linkedin_url
        
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                return f"Erreur de l'API TheirStack: {response.status_code} - {response.text}"
            
            # On retourne la réponse JSON brute sous forme de string. 
            # Les modèles LLM de Dust sont excellents pour lire et interpréter cette structure (confiance, jobs, etc).
            return response.text
            
        except Exception as e:
            return f"Erreur de connexion à l'API TheirStack: {str(e)}"


# ... le reste de ton code (imports, @mcp.tool, etc.) ...

if __name__ == "__main__":
    # Cloud Run injecte la variable d'environnement PORT (par défaut 8080)
    port = int(os.environ.get("PORT", "8080"))
    
    # On lance FastMCP en forçant l'hôte sur 0.0.0.0
    mcp.run(transport="sse", host="0.0.0.0", port=port)
