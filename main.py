from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os

app = FastAPI(title="TheirStack MCP Server")

THEIRSTACK_API_KEY = os.getenv("THEIRSTACK_API_KEY")
THEIRSTACK_API_URL = "https://api.theirstack.com/v1/companies/technologies"
MCP_SERVER_TOKEN = os.getenv("MCP_SERVER_TOKEN", "")

class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class ListToolsResponse(BaseModel):
    tools: List[Tool]

class CallToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]

def verify_token(authorization: Optional[str] = Header(None)):
    if MCP_SERVER_TOKEN and authorization != f"Bearer {MCP_SERVER_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/mcp/list-tools", response_model=ListToolsResponse)
async def list_tools(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    
    tools = [
        Tool(
            name="get_company_technologies",
            description=(
                "Récupère les technologies utilisées par une entreprise via TheirStack. "
                "Retourne pour chaque technologie : le nom, la catégorie, le niveau de confiance "
                "(low/medium/high), le nombre de jobs mentionnant la technologie, "
                "et les dates de première et dernière mention."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "company_domain": {
                        "type": "string",
                        "description": "Le nom de domaine de l'entreprise (ex: google.com)"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Le nom de l'entreprise (ex: Google)"
                    },
                    "company_linkedin_url": {
                        "type": "string",
                        "description": "L'URL LinkedIn de l'entreprise"
                    }
                },
                "oneOf": [
                    {"required": ["company_domain"]},
                    {"required": ["company_name"]},
                    {"required": ["company_linkedin_url"]}
                ]
            }
        )
    ]
    
    return ListToolsResponse(tools=tools)

@app.post("/mcp/call-tool")
async def call_tool(
    request: CallToolRequest,
    authorization: Optional[str] = Header(None)
):
    verify_token(authorization)
    
    if request.name == "get_company_technologies":
        return await get_company_technologies(request.arguments)
    else:
        raise HTTPException(status_code=404, detail=f"Tool '{request.name}' not found")

async def get_company_technologies(arguments: Dict[str, Any]) -> Dict[str, Any]:
    if not THEIRSTACK_API_KEY:
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Erreur: THEIRSTACK_API_KEY n'est pas configurée"}]
        }
    
    company_domain = arguments.get("company_domain")
    company_name = arguments.get("company_name")
    company_linkedin_url = arguments.get("company_linkedin_url")
    
    if not any([company_domain, company_name, company_linkedin_url]):
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Erreur: Vous devez fournir au moins un identifiant d'entreprise"}]
        }
    
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
                
                if not technologies:
                    result_text = "Aucune technologie trouvée pour cette entreprise."
                else:
                    result_text = f"## Technologies utilisées\n\n**Total:** {metadata.get('total_results', len(technologies))} technologies\n\n"
                    
                    by_category = {}
                    for tech in technologies:
                        category = tech["technology"].get("parent_category", "Autres")
                        if category not in by_category:
                            by_category[category] = []
                        by_category[category].append(tech)
                    
                    for category, techs in sorted(by_category.items()):
                        result_text += f"\n### {category}\n\n"
                        for tech in techs:
                            tech_info = tech["technology"]
                            name = tech_info["name"]
                            subcategory = tech_info.get("category", "")
                            confidence = tech["confidence"]
                            jobs = tech["jobs"]
                            first_date = tech.get("first_date_found", "N/A")
                            last_date = tech.get("last_date_found", "N/A")
                            
                            confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🟠"}.get(confidence, "⚪")
                            
                            result_text += f"- **{name}** ({subcategory}) {confidence_emoji}\n"
                            result_text += f"  - Confiance: {confidence}\n"
                            result_text += f"  - Mentions dans {jobs} offres d'emploi\n"
                            result_text += f"  - Première mention: {first_date} | Dernière: {last_date}\n\n"
                
                return {"content": [{"type": "text", "text": result_text}]}
            
            elif response.status_code == 402:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": "Erreur 402: Crédits API insuffisants sur TheirStack"}]
                }
            else:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Erreur API TheirStack ({response.status_code}): {response.text}"}]
                }
                
    except httpx.TimeoutException:
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Erreur: Timeout lors de l'appel à l'API TheirStack"}]
        }
    except Exception as e:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Erreur inattendue: {str(e)}"}]
        }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {
        "name": "TheirStack MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "list_tools": "/mcp/list-tools",
            "call_tool": "/mcp/call-tool",
            "health": "/health"
        }
    }
