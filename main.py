import os
import httpx
from typing import Any
from mcp.server.fastmcp import FastMCP

# Configuration
THEIRSTACK_API_KEY = os.getenv("THEIRSTACK_API_KEY")
THEIRSTACK_API_URL = "https://api.theirstack.com/v1/companies/technologies"

# Créer le serveur MCP avec Streamable HTTP
mcp = FastMCP(
    "TheirStack Technographics",
    stateless_http=True,
    json_response=True
)

@mcp.tool()
async def get_company_technologies(
    company_domain: str | None = None,
    company_name: str | None = None,
    company_linkedin_url: str | None = None
) -> dict[str, Any]:
    """
    Récupère les technologies utilisées par une entreprise via TheirStack.
    
    Args:
        company_domain: Le nom de domaine de l'entreprise (ex: google.com)
        company_name: Le nom de l'entreprise (ex: Google)
        company_linkedin_url: L'URL LinkedIn de l'entreprise
    """
    if not THEIRSTACK_API_KEY:
        return {"error": "THEIRSTACK_API_KEY n'est pas configurée"}
    
    if not any([company_domain, company_name, company_linkedin_url]):
        return {"error": "Vous devez fournir au moins un identifiant d'entreprise"}
    
    # Construction du payload
    payload = {}
    if company_domain:
        payload["company_domain"] = company_domain
    if company_name:
        payload["company_name"] = company_name
    if company_linkedin_url:
        payload["company_linkedin_url"] = company_linkedin_url
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                THEIRSTACK_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {THEIRSTACK_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                technologies = data.get("data", [])
                metadata = data.get("metadata", {})
                
                # Grouper par catégorie pour un meilleur affichage
                by_category = {}
                for tech in technologies:
                    category = tech["technology"].get("parent_category", "Autres")
                    if category not in by_category:
                        by_category[category] = []
                    
                    by_category[category].append({
                        "name": tech["technology"]["name"],
                        "subcategory": tech["technology"].get("category", ""),
                        "confidence": tech["confidence"],
                        "jobs": tech["jobs"],
                        "first_date": tech.get("first_date_found", "N/A"),
                        "last_date": tech.get("last_date_found", "N/A")
                    })
                
                return {
                    "total": metadata.get("total_results", len(technologies)),
                    "technologies_by_category": by_category
                }
            
            elif response.status_code == 402:
                return {"error": "Crédits API insuffisants sur TheirStack"}
            
            else:
                return {
                    "error": f"Erreur API TheirStack ({response.status_code})",
                    "detail": response.text
                }
                
    except httpx.TimeoutException:
        return {"error": "Timeout lors de l'appel à l'API TheirStack"}
    except Exception as e:
        return {"error": f"Erreur inattendue: {str(e)}"}

# Point d'entrée pour Cloud Run
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
