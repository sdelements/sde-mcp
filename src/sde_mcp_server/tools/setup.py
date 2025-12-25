"""
SD Elements Setup and Configuration Tools
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastmcp import Context

from ..server import mcp, api_client, init_api_client


@mcp.tool()
async def check_project_configuration(ctx: Context) -> str:
    """
    Check if SD Elements is configured for this workspace.
    
    Use this tool at the start of any coding session to verify SD Elements security
    guidance is available. If not configured, this tool will guide you through setup.
    
    **IMPORTANT**: Always call this tool before implementing security-related features.
    """
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    # Try to find .sdelements.yaml
    try:
        roots = await ctx.list_roots()
        context_path = None
        if roots and len(roots) > 0:
            first_root = roots[0]
            if hasattr(first_root, 'uri'):
                uri = first_root.uri
                if uri.startswith('file://'):
                    context_path = uri[7:]
    except Exception:
        context_path = None
    
    # Search for .sdelements.yaml
    project_id = None
    config_file_path = None
    
    if context_path:
        start_path = Path(context_path)
    else:
        start_path = Path.cwd().parent
    
    current = start_path
    while True:
        config_file = current / '.sdelements.yaml'
        if config_file.exists():
            try:
                import yaml
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                    if config and 'project_id' in config:
                        project_id = int(config['project_id'])
                        config_file_path = str(config_file)
                        break
            except Exception:
                pass
        
        if current.parent == current:
            break
        current = current.parent
    
    # Check environment variable
    env_project_id = os.getenv('SDE_PROJECT_ID')
    
    # Build response
    result = {
        "configured": False,
        "project_id": None,
        "config_source": None,
        "config_file_path": None,
        "workspace_root": str(start_path) if context_path else None,
        "message": "",
        "next_steps": []
    }
    
    if project_id:
        # Verify project exists
        try:
            project = api_client.get_project(project_id)
            result["configured"] = True
            result["project_id"] = project_id
            result["config_source"] = "file"
            result["config_file_path"] = config_file_path
            result["project_name"] = project.get('name', 'Unknown')
            result["message"] = f"✅ SD Elements is configured! Using project '{project.get('name')}' (ID: {project_id})"
            result["next_steps"] = [
                "You can now access security rules via resources:",
                "  - sde://project/{project_id}/rules/all",
                "  - sde://project/{project_id}/rules/authentication",
                "  - sde://project/{project_id}/rules/cryptography",
                "  - etc."
            ]
        except Exception as e:
            result["message"] = f"⚠️ Found .sdelements.yaml with project_id {project_id}, but project not accessible: {str(e)}"
            result["next_steps"] = [
                "Verify the project exists in SD Elements",
                "Check your API credentials (SDE_HOST and SDE_API_KEY)"
            ]
    elif env_project_id:
        try:
            project_id = int(env_project_id)
            project = api_client.get_project(project_id)
            result["configured"] = True
            result["project_id"] = project_id
            result["config_source"] = "environment"
            result["project_name"] = project.get('name', 'Unknown')
            result["message"] = f"✅ SD Elements is configured via environment variable! Using project '{project.get('name')}' (ID: {project_id})"
            result["next_steps"] = [
                "Consider creating a .sdelements.yaml file for this project:",
                f"  echo 'project_id: {project_id}' > .sdelements.yaml"
            ]
        except Exception as e:
            result["message"] = f"⚠️ SDE_PROJECT_ID environment variable is set to {env_project_id}, but project not accessible: {str(e)}"
            result["next_steps"] = [
                "Verify the project exists in SD Elements",
                "Check your API credentials"
            ]
    else:
        result["message"] = "❌ No SD Elements project configured for this workspace"
        result["next_steps"] = [
            "**RECOMMENDED**: Create an SD Elements project by calling the 'create_project_from_code' tool",
            "  - This will analyze your codebase",
            "  - Create an SD Elements project",
            "  - Generate a .sdelements.yaml file",
            "  - Provide security countermeasures",
            "",
            "**Alternative**: Manually create .sdelements.yaml:",
            "  1. Create a project in SD Elements",
            "  2. Create .sdelements.yaml in project root",
            "  3. Add: project_id: YOUR_PROJECT_ID",
            "",
            "**Alternative**: Set environment variable:",
            "  export SDE_PROJECT_ID=YOUR_PROJECT_ID"
        ]
    
    return json.dumps(result, indent=2)

