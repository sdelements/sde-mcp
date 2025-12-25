# Project Instructions

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

