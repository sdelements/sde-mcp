"""Repository scanning tools"""
import json
from typing import Optional

from fastmcp import Context

from ..server import mcp, api_client, init_api_client


@mcp.tool()
async def list_scan_connections(ctx: Context) -> str:
    """List repository scan connections"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    result = api_client.list_team_onboarding_connections()
    return json.dumps(result, indent=2)


@mcp.tool()
async def scan_repository(ctx: Context, project_id: int, connection_id: int, repository_url: str) -> str:
    """Scan a repository"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    data = {"project": project_id, "connection": connection_id, "repository_url": repository_url}
    result = api_client.create_team_onboarding_scan(data)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_scan_status(ctx: Context, scan_id: int) -> str:
    """Get status of a repository scan"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    result = api_client.get_team_onboarding_scan(scan_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_scans(ctx: Context, project_id: Optional[int] = None) -> str:
    """List repository scans"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    params = {}
    if project_id is not None:
        params["project"] = project_id
    result = api_client.list_team_onboarding_scans(params)
    return json.dumps(result, indent=2)

