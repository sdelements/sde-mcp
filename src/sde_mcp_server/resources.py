"""
SD Elements MCP Resources

Provides security rules and guidelines as MCP resources that can be consumed
by AI IDEs (Cursor, Claude Desktop, Cody, Continue.dev, etc.)
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from fastmcp import Context

from .server import mcp, api_client, init_api_client


# Resource URI format: sde://project/{project_id}/rules/{category}
# or: sde://project/{project_id}/tasks/{task_id}


async def get_context_from_roots(ctx: Context) -> Optional[str]:
    """
    Extract workspace root path from MCP roots.
    
    Returns the first root's file path, or None if roots not available.
    """
    try:
        roots = await ctx.list_roots()
        if roots and len(roots) > 0:
            first_root = roots[0]
            if hasattr(first_root, 'uri'):
                uri = first_root.uri
                if uri.startswith('file://'):
                    return uri[7:]  # Remove 'file://' prefix
    except Exception:
        pass
    return None


def get_project_id_from_config(context_path: Optional[str] = None) -> Optional[int]:
    """
    Find .sdelements.yaml by searching upwards from context_path.
    
    For mono repos with multiple .sdelements.yaml files, this searches upwards
    from the current file/directory context to find the nearest config.
    
    Args:
        context_path: Path to start searching from (e.g., current file being edited).
                     If None, uses MCP server's cwd.
    
    Returns:
        project_id from the nearest .sdelements.yaml, or from SDE_PROJECT_ID env var
    """
    # First try environment variable
    env_project_id = os.getenv('SDE_PROJECT_ID')
    if env_project_id:
        try:
            return int(env_project_id)
        except ValueError:
            pass
    
    # Determine starting point for search
    if context_path:
        # Start from the provided context (e.g., file being edited)
        start_path = Path(context_path).resolve()
        if start_path.is_file():
            start_path = start_path.parent
    else:
        # Fall back to MCP server's cwd parent (project root)
        start_path = Path.cwd().parent
    
    # Search upwards for .sdelements.yaml
    current = start_path
    while True:
        config_file = current / '.sdelements.yaml'
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                    if config and 'project_id' in config:
                        return int(config['project_id'])
            except Exception:
                pass
        
        # Stop at filesystem root
        if current.parent == current:
            break
        current = current.parent
    
    return None


@mcp.resource("sde://project/{project_id}/rules/all")
async def get_all_security_rules(ctx: Context, project_id: Optional[int] = None) -> str:
    """
    Get all security rules for a project as a comprehensive markdown document.
    
    This resource provides complete security guidelines from SD Elements
    countermeasures, formatted for AI IDE consumption.
    
    For mono repos: Automatically finds the nearest .sdelements.yaml by searching
    upwards from the current context (file being edited or workspace root).
    """
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    # Auto-detect project_id if not provided
    if project_id is None:
        # Try to get context from MCP roots (workspace folders)
        context_path = await get_context_from_roots(ctx)
        project_id = get_project_id_from_config(context_path)
        if project_id is None:
            return "Error: No project_id provided and no .sdelements.yaml file found"
    
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
async def get_authentication_rules(ctx: Context, project_id: Optional[int] = None) -> str:
    """
    Get authentication and session management security rules.
    
    Includes rules for passwords, sessions, account security, MFA, login, logout,
    password reset, account lockout, credential storage, and user authentication.
    """
    if project_id is None:
        context_path = await get_context_from_roots(ctx)
        project_id = get_project_id_from_config(context_path)
        if project_id is None:
            return "Error: No project_id provided and no .sdelements.yaml file found"
    
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Authentication & Session Management",
        keywords=[
            "password", "passwords", "passwd",
            "authentication", "authenticate", "auth",
            "session", "sessions", "cookie", "cookies",
            "login", "logout", "sign-in", "signin",
            "account", "accounts", "user",
            "mfa", "multi-factor", "2fa", "two-factor",
            "credential", "credentials", "creds",
            "reset", "forgot", "forgotten",
            "lockout", "lock-out", "brute-force", "bruteforce",
            "token", "tokens"
        ]
    )


@mcp.resource("sde://project/{project_id}/rules/cryptography")
async def get_cryptography_rules(ctx: Context, project_id: Optional[int] = None) -> str:
    """
    Get cryptography security rules.
    
    Includes rules for encryption, decryption, TLS/SSL, random number generation,
    hashing, key management, certificates, ciphers, and secure communication.
    """
    if project_id is None:
        context_path = await get_context_from_roots(ctx)
        project_id = get_project_id_from_config(context_path)
        if project_id is None:
            return "Error: No project_id provided and no .sdelements.yaml file found"
    
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Cryptography",
        keywords=[
            "encrypt", "encryption", "encrypted", "encrypting",
            "decrypt", "decryption", "decrypted", "decrypting",
            "tls", "ssl", "https",
            "crypto", "cryptographic", "cryptography",
            "random", "randomness", "prng", "rng",
            "certificate", "certificates", "cert", "certs",
            "key", "keys", "keystore",
            "hash", "hashing", "hashes", "digest",
            "cipher", "ciphers", "algorithm",
            "aes", "rsa", "sha", "md5",
            "secure", "security"
        ]
    )


@mcp.resource("sde://project/{project_id}/rules/authorization")
async def get_authorization_rules(ctx: Context, project_id: Optional[int] = None) -> str:
    """
    Get authorization and access control security rules.
    
    Includes rules for API authorization, permissions, role-based access control (RBAC),
    insecure direct object references (IDOR), privilege escalation, and access checks.
    """
    if project_id is None:
        context_path = await get_context_from_roots(ctx)
        project_id = get_project_id_from_config(context_path)
        if project_id is None:
            return "Error: No project_id provided and no .sdelements.yaml file found"
    
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Authorization & Access Control",
        keywords=[
            "authorization", "authorize", "authorized",
            "access", "accessing", "accessible",
            "permission", "permissions", "privilege", "privileges",
            "rbac", "role", "roles",
            "idor", "direct object",
            "api", "endpoint", "endpoints", "rest", "restful",
            "acl", "access control",
            "forbidden", "deny", "denied",
            "admin", "administrator",
            "elevate", "escalation"
        ]
    )


@mcp.resource("sde://project/{project_id}/rules/container")
async def get_container_rules(ctx: Context, project_id: Optional[int] = None) -> str:
    """
    Get container security rules.
    
    Includes rules for Docker, Kubernetes, container images, registries, pods,
    Dockerfiles, orchestration, and container runtime security.
    """
    if project_id is None:
        context_path = await get_context_from_roots(ctx)
        project_id = get_project_id_from_config(context_path)
        if project_id is None:
            return "Error: No project_id provided and no .sdelements.yaml file found"
    
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Container Security",
        keywords=[
            "docker", "dockerfile",
            "container", "containers", "containerized",
            "kubernetes", "k8s", "pod", "pods",
            "image", "images",
            "registry", "registries",
            "orchestration", "orchestrator",
            "helm", "chart",
            "compose", "docker-compose"
        ]
    )


@mcp.resource("sde://project/{project_id}/rules/cicd")
async def get_cicd_rules(ctx: Context, project_id: Optional[int] = None) -> str:
    """
    Get CI/CD and supply chain security rules.
    
    Includes rules for CI/CD pipelines, GitHub Actions, GitLab CI, dependencies,
    package management, artifact signing, SBOM, and supply chain security.
    """
    if project_id is None:
        context_path = await get_context_from_roots(ctx)
        project_id = get_project_id_from_config(context_path)
        if project_id is None:
            return "Error: No project_id provided and no .sdelements.yaml file found"
    
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="CI/CD & Supply Chain",
        keywords=[
            "pipeline", "pipelines", "ci", "cd", "cicd", "ci/cd",
            "github", "actions", "workflow", "workflows",
            "gitlab", "jenkins", "circleci", "travis",
            "dependency", "dependencies", "package", "packages",
            "artifact", "artifacts",
            "supply", "supply-chain", "supply chain",
            "npm", "pip", "maven", "gradle",
            "build", "builds", "builder",
            "sbom", "bill of materials",
            "signing", "signature", "sign",
            "repository", "repo"
        ]
    )


@mcp.resource("sde://project/{project_id}/rules/input-validation")
async def get_input_validation_rules(ctx: Context, project_id: Optional[int] = None) -> str:
    """
    Get input validation and injection prevention rules.
    
    Includes rules for input validation, SSRF, SQL injection, XSS, command injection,
    sanitization, encoding, and secure data handling.
    """
    if project_id is None:
        context_path = await get_context_from_roots(ctx)
        project_id = get_project_id_from_config(context_path)
        if project_id is None:
            return "Error: No project_id provided and no .sdelements.yaml file found"
    
    return await _get_rules_by_keywords(
        project_id=project_id,
        category="Input Validation & Injection Prevention",
        keywords=[
            "input", "inputs", "user input",
            "validation", "validate", "validated", "validating",
            "ssrf", "server-side request forgery",
            "injection", "inject", "injected",
            "sanitize", "sanitization", "sanitized",
            "xss", "cross-site scripting", "script",
            "sql", "sqli", "sql injection",
            "command", "command injection", "shell",
            "path", "traversal", "directory",
            "url", "uri", "request",
            "encode", "encoding", "escape", "escaping",
            "filter", "filtering"
        ]
    )


def _stem_word(word: str) -> str:
    """
    Simple stemming - remove common suffixes.
    Not perfect but good enough for keyword matching.
    """
    word = word.lower()
    # Remove common suffixes
    for suffix in ['ing', 'ed', 'ion', 'tion', 'ation', 's', 'es']:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]
    return word


def _keyword_matches(text: str, keywords: List[str]) -> bool:
    """
    Check if any keyword (or its stem) appears in text.
    More inclusive matching with stemming.
    """
    text_lower = text.lower()
    text_words = set(text_lower.split())
    text_stems = {_stem_word(w) for w in text_words}
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        keyword_stem = _stem_word(keyword_lower)
        
        # Direct match
        if keyword_lower in text_lower:
            return True
        
        # Stem match
        if keyword_stem in text_stems:
            return True
        
        # Word boundary match
        if any(keyword_lower in word for word in text_words):
            return True
    
    return False


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
        
        # Filter by keywords with stemming
        filtered_tasks = []
        for task in countermeasures.get('results', []):
            title = task.get('title', '')
            text = task.get('text', '')
            
            # Check if any keyword matches (with stemming)
            if _keyword_matches(title, keywords) or _keyword_matches(text, keywords):
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

