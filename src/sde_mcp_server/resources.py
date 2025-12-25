"""
SD Elements MCP Resources

Provides security rules and guidelines as MCP resources that can be consumed
by AI IDEs (Cursor, Claude Desktop, Cody, Continue.dev, etc.)
"""

from typing import Dict, List, Optional
from fastmcp import Context

from .server import mcp, api_client, init_api_client


# Resource URI format: sde://project/{project_id}/rules/{category}
# or: sde://project/{project_id}/tasks/{task_id}


@mcp.resource("sde://project/{project_id}/rules/all")
async def get_all_security_rules(ctx: Context, project_id: int) -> str:
    """
    Get all security rules for a project as a comprehensive markdown document.
    
    This resource provides complete security guidelines from SD Elements
    countermeasures, formatted for AI IDE consumption.
    """
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    try:
        # Fetch all countermeasures for the project
        countermeasures = await api_client.list_countermeasures(
            project_id=project_id,
            risk_relevant=True
        )
        
        # Generate comprehensive markdown
        markdown = f"""# SD Elements Security Rules - All

**Project ID**: {project_id}
**Generated**: {countermeasures.get('_metadata', {}).get('timestamp', 'N/A')}

This document contains all security rules and guidelines from SD Elements.
When implementing security features, always reference the SD Elements task ID.

---

"""
        
        # Group countermeasures by category
        for task in countermeasures.get('results', []):
            task_id = task.get('slug', 'Unknown')
            title = task.get('title', 'Untitled')
            text = task.get('text', 'No description available')
            problem = task.get('problem', '')
            
            markdown += f"""
## {task_id}: {title}

**SD Elements Task**: {task_id}
**Problem**: {problem}

### Description
{text}

### When to Apply
Reference this task when implementing features related to: {title.lower()}

### Traceability
- **SD Elements Task**: {task_id}
- **Problem ID**: {problem}

---

"""
        
        return markdown
        
    except Exception as e:
        return f"Error fetching security rules: {str(e)}"


@mcp.resource("sde://project/{project_id}/tasks/{task_id}")
async def get_task_rule(ctx: Context, project_id: int, task_id: str) -> str:
    """
    Get security rule for a specific SD Elements task.
    
    Returns detailed guidance for implementing a specific security control.
    """
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    try:
        # Normalize task ID (handle T21, 21, or 31445-T21 formats)
        if task_id.isdigit():
            task_id = f"T{task_id}"
        if not task_id.startswith(f"{project_id}-"):
            full_task_id = f"{project_id}-{task_id}"
        else:
            full_task_id = task_id
        
        # Fetch specific countermeasure
        countermeasure = await api_client.get_countermeasure(
            project_id=project_id,
            countermeasure_id=full_task_id,
            risk_relevant=True
        )
        
        task_slug = countermeasure.get('slug', task_id)
        title = countermeasure.get('title', 'Untitled')
        text = countermeasure.get('text', 'No description available')
        problem = countermeasure.get('problem', '')
        status = countermeasure.get('status', {}).get('name', 'Unknown')
        
        markdown = f"""# SD Elements Task {task_slug}: {title}

**Project ID**: {project_id}
**Status**: {status}
**Problem**: {problem}

## Description
{text}

## Implementation Guidance

When implementing this security control:

1. **Reference the task**: Start your implementation with "Following SD Elements Task {task_slug}"
2. **Add code comments**: Include `# SD Elements {task_slug}: {title}` in your code
3. **Explain the requirement**: Document what vulnerability this prevents
4. **Provide traceability**: Link code to this task for compliance

## Example Format

```
Following SD Elements Task {task_slug}: {title}

This prevents [vulnerability description].

Implementation:

# SD Elements {task_slug}: {title}
[Your secure code here]

This addresses:
- SD Elements Task: {task_slug}
- Problem: {problem}
```

## Traceability
- **SD Elements Task**: {task_slug}
- **Problem ID**: {problem}
- **Project**: {project_id}

---

*For more details, visit SD Elements project #{project_id}*
"""
        
        return markdown
        
    except Exception as e:
        return f"Error fetching task {task_id}: {str(e)}"


@mcp.resource("sde://project/{project_id}/rules/authentication")
async def get_authentication_rules(ctx: Context, project_id: int) -> str:
    """
    Get authentication and session management security rules.
    
    Includes rules for passwords, sessions, account security, and MFA.
    """
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Authentication & Session Management",
        keywords=["password", "authentication", "session", "login", "account", "mfa", "credential"]
    )


@mcp.resource("sde://project/{project_id}/rules/cryptography")
async def get_cryptography_rules(ctx: Context, project_id: int) -> str:
    """
    Get cryptography security rules.
    
    Includes rules for encryption, TLS, random numbers, and key management.
    """
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Cryptography",
        keywords=["encrypt", "decrypt", "tls", "ssl", "crypto", "random", "certificate", "key"]
    )


@mcp.resource("sde://project/{project_id}/rules/authorization")
async def get_authorization_rules(ctx: Context, project_id: int) -> str:
    """
    Get authorization and access control security rules.
    
    Includes rules for API authorization, permissions, and access control.
    """
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Authorization & Access Control",
        keywords=["authorization", "access", "permission", "rbac", "idor", "api"]
    )


@mcp.resource("sde://project/{project_id}/rules/container")
async def get_container_rules(ctx: Context, project_id: int) -> str:
    """
    Get container security rules.
    
    Includes rules for Docker, Kubernetes, and container image security.
    """
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Container Security",
        keywords=["docker", "container", "kubernetes", "image", "registry"]
    )


@mcp.resource("sde://project/{project_id}/rules/cicd")
async def get_cicd_rules(ctx: Context, project_id: int) -> str:
    """
    Get CI/CD and supply chain security rules.
    
    Includes rules for pipelines, dependencies, and artifact management.
    """
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="CI/CD & Supply Chain",
        keywords=["pipeline", "cicd", "github", "gitlab", "dependency", "artifact", "supply"]
    )


@mcp.resource("sde://project/{project_id}/rules/input-validation")
async def get_input_validation_rules(ctx: Context, project_id: int) -> str:
    """
    Get input validation and injection prevention rules.
    
    Includes rules for SSRF, injection attacks, and input sanitization.
    """
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Input Validation & Injection Prevention",
        keywords=["input", "validation", "ssrf", "injection", "sanitize", "xss", "sql"]
    )


async def _get_rules_by_keywords(project_id: int, category: str, keywords: List[str]) -> str:
    """
    Helper function to get rules filtered by keywords.
    
    Args:
        project_id: SD Elements project ID
        category: Category name for the rules
        keywords: List of keywords to filter by
        
    Returns:
        Markdown document with filtered rules
    """
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    try:
        # Fetch all countermeasures
        countermeasures = await api_client.list_countermeasures(
            project_id=project_id,
            risk_relevant=True
        )
        
        # Filter by keywords
        filtered_tasks = []
        for task in countermeasures.get('results', []):
            title = task.get('title', '').lower()
            text = task.get('text', '').lower()
            
            # Check if any keyword matches
            if any(keyword.lower() in title or keyword.lower() in text for keyword in keywords):
                filtered_tasks.append(task)
        
        # Generate markdown
        markdown = f"""# SD Elements Security Rules - {category}

**Project ID**: {project_id}
**Category**: {category}
**Rules Found**: {len(filtered_tasks)}

This document contains security rules related to {category.lower()}.

---

"""
        
        for task in filtered_tasks:
            task_id = task.get('slug', 'Unknown')
            title = task.get('title', 'Untitled')
            text = task.get('text', 'No description available')
            problem = task.get('problem', '')
            
            markdown += f"""
## {task_id}: {title}

**SD Elements Task**: {task_id}
**Problem**: {problem}

### Description
{text}

### Implementation Note
When implementing this control, reference SD Elements Task {task_id} in your code comments and documentation.

---

"""
        
        if not filtered_tasks:
            markdown += "\n*No rules found for this category in the current project.*\n"
        
        return markdown
        
    except Exception as e:
        return f"Error fetching {category} rules: {str(e)}"

