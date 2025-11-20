"""User-related tools"""
import json
from typing import Optional

from fastmcp import Context

from ..server import mcp, api_client, init_api_client


@mcp.tool()
async def list_users(ctx: Context, page_size: Optional[int] = None, active: Optional[bool] = None) -> str:
    """List all users"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    params = {}
    if page_size is not None:
        params["page_size"] = page_size
    if active is not None:
        params["is_active"] = active
    result = api_client.list_users(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_user(ctx: Context, user_id: int) -> str:
    """Get details of a specific user"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    result = api_client.get_user(user_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_current_user(ctx: Context) -> str:
    """Get current authenticated user"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    result = api_client.get_current_user()
    return json.dumps(result, indent=2)

