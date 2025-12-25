# Quick Start: SD Elements MCP Resources

## What's New

Your SD Elements MCP server now serves **security rules as resources** that AI IDEs can automatically access when generating code!

## Quick Test

### 1. Set Environment Variables

```bash
export SDE_HOST=https://cd.sdelements.com
export SDE_API_KEY=your-api-key-here
export SDE_PROJECT_ID=31445  # Optional, defaults to 31445
```

### 2. Test Resources

```bash
cd sde-mcp
python test_resources.py
```

You should see output like:

```
╔══════════════════════════════════════════════════════════════╗
║  SD Elements MCP Resources - Test Suite                     ║
╚══════════════════════════════════════════════════════════════╝

Configuration:
  Host: https://cd.sdelements.com
  Project ID: 31445

======================================================================
TEST 1: Get All Security Rules
======================================================================
✅ Success! Retrieved 15234 characters

Preview (first 500 chars):

# SD Elements Security Rules - All

**Project ID**: 31445
**Generated**: 2025-12-24

This document contains all security rules and guidelines from SD Elements...
```

### 3. Start the MCP Server

```bash
python -m sde_mcp_server
```

The server will start and resources will be available at:
- `sde://project/31445/rules/all`
- `sde://project/31445/tasks/T76`
- `sde://project/31445/rules/authentication`
- etc.

## Configure Your AI IDE

### Cursor

The SD Elements MCP server will automatically be discovered if configured in Cursor's MCP settings.

Resources will load automatically when relevant to your code.

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

## Available Resources

| Resource URI | Description |
|--------------|-------------|
| `sde://project/{id}/rules/all` | All security rules |
| `sde://project/{id}/tasks/{task_id}` | Specific task (e.g., T76) |
| `sde://project/{id}/rules/authentication` | Authentication & sessions |
| `sde://project/{id}/rules/cryptography` | Encryption & TLS |
| `sde://project/{id}/rules/authorization` | Access control |
| `sde://project/{id}/rules/container` | Docker & Kubernetes |
| `sde://project/{id}/rules/cicd` | CI/CD & supply chain |
| `sde://project/{id}/rules/input-validation` | Input validation & SSRF |

## How It Works

1. **You write code** in your AI IDE
2. **IDE detects context** (e.g., you're working on authentication)
3. **IDE loads relevant resources** (e.g., `sde://project/31445/rules/authentication`)
4. **AI generates secure code** following SD Elements guidelines
5. **Code includes task references** (e.g., `# SD Elements T76: Do not hardcode passwords`)

## Example Usage

### Before (without resources):
```python
# AI generates insecure code
API_KEY = "sk-1234567890"
```

### After (with resources):
```python
# Following SD Elements Task T76: Do not hardcode passwords
# SD Elements T76: Use environment variables for credentials
import os
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")
```

## Benefits

✅ **Automatic security guidance** - No need to manually reference SD Elements  
✅ **Always up-to-date** - Fetches latest from SD Elements API  
✅ **Compliance traceability** - All code references SD Elements tasks  
✅ **Works everywhere** - Any MCP-compatible AI IDE  

## Troubleshooting

### "Authentication failed"
- Check your `SDE_API_KEY` is correct
- Verify you have access to the project

### "Resources not appearing"
- Restart your AI IDE after configuring MCP
- Check the MCP server is running
- Verify the project ID is correct

### "Empty resources"
- Ensure the project has countermeasures
- Check the project is not archived
- Verify API permissions

## Next Steps

1. ✅ Test resources with `python test_resources.py`
2. ✅ Start MCP server with `python -m sde_mcp_server`
3. ✅ Configure your AI IDE
4. ✅ Try generating security-related code
5. ✅ Verify SD Elements task references appear

## Documentation

- **Full Resources Guide**: See `RESOURCES.md`
- **MCP Server README**: See `README.md`
- **SD Elements API**: https://docs.sdelements.com/api/

---

**Version**: 0.2.0-alpha (with resources support)  
**Branch**: add-resources-support  
**Based on**: 0.1.0-alpha

