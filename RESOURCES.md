# SD Elements MCP Resources

This document describes the MCP resources provided by the SD Elements MCP server for serving security rules and guidelines to AI IDEs.

## Overview

The SD Elements MCP server now provides **resources** in addition to tools. Resources are read-only documents that AI IDEs can access to get security guidance when generating code.

### Resources vs Tools

- **Tools**: Interactive functions that perform actions (create projects, update tasks, etc.)
- **Resources**: Read-only documents that provide context and guidance (security rules, best practices)

## Available Resources

### 1. All Security Rules
**URI**: `sde://project/{project_id}/rules/all`

Get all security rules for a project as a comprehensive markdown document.

**Example**:
```
sde://project/31445/rules/all
```

**Use Case**: Load all security guidelines at once for comprehensive context.

### 2. Individual Task Rules
**URI**: `sde://project/{project_id}/tasks/{task_id}`

Get detailed guidance for a specific SD Elements task.

**Examples**:
```
sde://project/31445/tasks/T76
sde://project/31445/tasks/T151
sde://project/31445/tasks/21  (auto-converts to T21)
```

**Use Case**: Get specific guidance when implementing a particular security control.

### 3. Authentication & Session Management Rules
**URI**: `sde://project/{project_id}/rules/authentication`

Get rules related to authentication, passwords, sessions, and account security.

**Example**:
```
sde://project/31445/rules/authentication
```

**Covers**: Password management, session IDs, account lockout, MFA, credentials

### 4. Cryptography Rules
**URI**: `sde://project/{project_id}/rules/cryptography`

Get rules related to encryption, TLS, random numbers, and key management.

**Example**:
```
sde://project/31445/rules/cryptography
```

**Covers**: Encryption, TLS/SSL, random number generation, certificates, key management

### 5. Authorization & Access Control Rules
**URI**: `sde://project/{project_id}/rules/authorization`

Get rules related to API authorization, permissions, and access control.

**Example**:
```
sde://project/31445/rules/authorization
```

**Covers**: API authorization, RBAC, IDOR prevention, permission checks

### 6. Container Security Rules
**URI**: `sde://project/{project_id}/rules/container`

Get rules related to Docker, Kubernetes, and container security.

**Example**:
```
sde://project/31445/rules/container
```

**Covers**: Docker, Kubernetes, container images, registry security

### 7. CI/CD & Supply Chain Rules
**URI**: `sde://project/{project_id}/rules/cicd`

Get rules related to CI/CD pipelines, dependencies, and supply chain security.

**Example**:
```
sde://project/31445/rules/cicd
```

**Covers**: GitHub Actions, GitLab CI, dependencies, artifacts, supply chain

### 8. Input Validation & Injection Prevention Rules
**URI**: `sde://project/{project_id}/rules/input-validation`

Get rules related to input validation, SSRF, and injection attacks.

**Example**:
```
sde://project/31445/rules/input-validation
```

**Covers**: Input validation, SSRF, SQL injection, XSS, sanitization

## How AI IDEs Use Resources

### Cursor

Resources are automatically loaded when relevant to your code context. When you're working on authentication code, Cursor will load the authentication resources.

### Claude Desktop

Configure in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sdelements": {
      "command": "python",
      "args": ["-m", "sde_mcp_server"],
      "env": {
        "SDE_HOST": "https://cd.sdelements.com",
        "SDE_API_KEY": "your-api-key"
      }
    }
  }
}
```

Claude will automatically discover and load relevant resources.

### Continue.dev

Resources are loaded based on context when generating code.

## Resource Format

All resources return markdown documents with:

1. **Header**: Project ID, task ID, status
2. **Description**: What the security control does
3. **Implementation Guidance**: How to implement it
4. **Example Format**: Template for referencing the task
5. **Traceability**: Links to SD Elements task, problem, and CWE

### Example Resource Output

```markdown
# SD Elements Task T76: Do not hardcode passwords

**Project ID**: 31445
**Status**: Pass
**Problem**: P156

## Description
Hardcoded credentials can be extracted from code or binaries, allowing 
attackers to gain unauthorized access.

## Implementation Guidance

When implementing this security control:

1. **Reference the task**: Start with "Following SD Elements Task T76"
2. **Add code comments**: Include `# SD Elements T76: Do not hardcode passwords`
3. **Explain the requirement**: Document what vulnerability this prevents
4. **Provide traceability**: Link code to this task for compliance

## Example Format

\`\`\`
Following SD Elements Task T76: Do not hardcode passwords

This prevents CWE-798 (Use of Hard-coded Credentials).

Implementation:

# SD Elements T76: Do not hardcode passwords
import os
DB_PASSWORD = os.getenv('DB_PASSWORD')

This addresses:
- SD Elements Task: T76
- Problem: P156
\`\`\`

## Traceability
- **SD Elements Task**: T76
- **Problem ID**: P156
- **Project**: 31445
```

## Benefits

### For Developers
- ✅ **Automatic security guidance** when writing code
- ✅ **Context-aware** - only relevant rules are shown
- ✅ **Traceability** - always references SD Elements tasks
- ✅ **Compliance** - ensures security requirements are met

### For Security Teams
- ✅ **Centralized rules** - single source of truth
- ✅ **Automatic updates** - rules sync from SD Elements
- ✅ **Audit trail** - all code references SD Elements tasks
- ✅ **Consistent enforcement** - same rules across all projects

### For AI IDEs
- ✅ **Standard protocol** - works with any MCP-compatible IDE
- ✅ **Rich context** - detailed security guidance
- ✅ **Dynamic** - fetches latest from SD Elements
- ✅ **Categorized** - easy to find relevant rules

## Testing Resources

### Using curl

```bash
# List all resources
curl -X POST http://localhost:8080/mcp/v1/resources/list

# Read a specific resource
curl -X POST http://localhost:8080/mcp/v1/resources/read \
  -H "Content-Type: application/json" \
  -d '{"uri": "sde://project/31445/tasks/T76"}'
```

### Using Python

```python
import asyncio
from mcp import ClientSession

async def test_resources():
    async with ClientSession("sdelements") as session:
        # List resources
        resources = await session.list_resources()
        print(f"Found {len(resources)} resources")
        
        # Read a resource
        content = await session.read_resource("sde://project/31445/tasks/T76")
        print(content)

asyncio.run(test_resources())
```

## Implementation Details

### Resource Registration

Resources are registered using the `@mcp.resource()` decorator:

```python
@mcp.resource("sde://project/{project_id}/tasks/{task_id}")
async def get_task_rule(ctx: Context, project_id: int, task_id: str) -> str:
    # Fetch from SD Elements
    countermeasure = await api_client.get_countermeasure(...)
    
    # Generate markdown
    return markdown_content
```

### Dynamic Filtering

Category resources (authentication, cryptography, etc.) dynamically filter countermeasures by keywords:

```python
async def _get_rules_by_keywords(project_id, category, keywords):
    # Fetch all countermeasures
    countermeasures = await api_client.list_countermeasures(project_id)
    
    # Filter by keywords
    filtered = [
        task for task in countermeasures
        if any(keyword in task['title'].lower() or keyword in task['text'].lower() 
               for keyword in keywords)
    ]
    
    return generate_markdown(filtered)
```

## Next Steps

1. **Test the resources**: Use curl or Python to test resource access
2. **Configure your IDE**: Set up MCP connection in your AI IDE
3. **Try it out**: Ask your AI to implement security features
4. **Verify traceability**: Check that generated code references SD Elements tasks

## Troubleshooting

### Resources not appearing
- Ensure the MCP server is running
- Check that your IDE supports MCP resources
- Verify the project ID is correct

### Empty resources
- Check that the project has countermeasures
- Verify API credentials are correct
- Ensure the project is accessible

### Outdated content
- Restart the MCP server to fetch latest from SD Elements
- Check that the API key has proper permissions

## Resources

- **MCP Specification**: https://modelcontextprotocol.io
- **FastMCP Documentation**: https://github.com/jlowin/fastmcp
- **SD Elements API**: https://docs.sdelements.com/api/

---

**Version**: 0.2.0-alpha  
**Last Updated**: 2025-12-24

