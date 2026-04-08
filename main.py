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
