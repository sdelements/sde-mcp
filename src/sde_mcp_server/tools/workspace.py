"""
Workspace configuration tools for SD Elements
"""

import json
from pathlib import Path
from typing import Optional

from fastmcp import Context

from ..server import mcp


AGENTS_MD_CONTENT = """# Project Instructions

**CRITICAL**: Before implementing ANY code, you MUST check SD Elements security guidance from @sdelements MCP server.

## Step 1: Check Configuration
Call the `check_project_configuration` tool from @sdelements to verify setup.

If not configured, the tool will tell you to:
- Ask the user if they want to create an SD Elements project
- If yes, call `create_project_from_code` tool to set up automatically
- **CRITICAL**: After creating the project, immediately create a `.sdelements.yaml` file in the project root with the project_id from the response

## Step 2: Create .sdelements.yaml File
After project creation, immediately create `.sdelements.yaml` in the project root:
```yaml
# SD Elements Project Configuration
project:
  id: <project_id_from_response>
  name: <project_name>
  url: <project_url_from_response>
```

This file links the codebase to SD Elements and enables automatic security guidance.

## Step 3: Get Security Guidance
Once configured, check relevant security rules before implementing:
- Use @sdelements resources for security guidance
- Available categories: authentication, cryptography, authorization, input-validation, container, cicd

## Step 4: Reference Tasks
Always reference SD Elements task IDs in code comments:
- Format: `// SD Elements Task T21: Implement password hashing with bcrypt`
"""


@mcp.tool()
async def setup_workspace_instructions(ctx: Context, workspace_path: Optional[str] = None) -> str:
    """
    Create or update AGENTS.md file with SD Elements instructions for AI agents.
    
    This ensures AI agents working on the project know to:
    1. Check SD Elements configuration before implementing code
    2. Create .sdelements.yaml file after project creation
    3. Get security guidance from SD Elements resources
    4. Reference SD Elements task IDs in code comments
    
    Args:
        workspace_path: Optional path to workspace root. If not provided, uses current context.
    
    Returns:
        JSON with status and file path
    """
    try:
        # Determine workspace root
        if workspace_path:
            root_path = Path(workspace_path)
        else:
            # Try to get from context
            try:
                roots = await ctx.list_roots()
                if roots and len(roots) > 0:
                    first_root = roots[0]
                    if hasattr(first_root, 'uri'):
                        uri = first_root.uri
                        if uri.startswith('file://'):
                            root_path = Path(uri[7:])
                        else:
                            root_path = Path.cwd()
                    else:
                        root_path = Path.cwd()
                else:
                    root_path = Path.cwd()
            except Exception:
                root_path = Path.cwd()
        
        agents_md_path = root_path / "AGENTS.md"
        
        # Check if file exists
        if agents_md_path.exists():
            # Read existing content
            existing_content = agents_md_path.read_text()
            
            # Check if SD Elements instructions are already present
            if "@sdelements" in existing_content and "check_project_configuration" in existing_content:
                return json.dumps({
                    "success": True,
                    "action": "skipped",
                    "message": "AGENTS.md already contains SD Elements instructions",
                    "file_path": str(agents_md_path)
                })
            
            # File exists but doesn't have SD Elements instructions - append them
            updated_content = existing_content.rstrip() + "\n\n" + AGENTS_MD_CONTENT
            agents_md_path.write_text(updated_content)
            
            return json.dumps({
                "success": True,
                "action": "updated",
                "message": "Added SD Elements instructions to existing AGENTS.md",
                "file_path": str(agents_md_path)
            })
        else:
            # Create new file
            agents_md_path.write_text(AGENTS_MD_CONTENT)
            
            return json.dumps({
                "success": True,
                "action": "created",
                "message": "Created AGENTS.md with SD Elements instructions",
                "file_path": str(agents_md_path)
            })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        })

