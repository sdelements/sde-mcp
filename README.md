> **Warning**
> This project is a **work in progress**. Use at your own risk.

### SD Elements MCP Server

MCP server for **SD Elements API v2** (STDIO only). Use it from MCP clients to manage projects, surveys, countermeasures, scans, reports, diagrams, and users.

### Quick start

```bash
npm ci
npm run start
```

### Required configuration

- **`SDE_HOST`**: `https://your-sdelements-instance.com`
- **`SDE_API_KEY`**: `your-api-key-here`

### HTTP setup

Use HTTP mode when you want a long-running server instead of STDIO.

```bash
npm run start:http
```

- **Credentials**: do **not** set `SDE_HOST` or `SDE_API_KEY` in the server process. The HTTP server refuses to start if either is set (including `SDE_API_KEY`). Each client request must provide credentials instead.
- **Instance allowlist (required)**: set `MCP_SDE_INSTANCE_ALLOWLIST` to a comma-separated list of allowed SDE hosts (for example `https://sde.example.com,https://sde2.example.com`). Requests with `SDE_HOST` outside this list are rejected.
- **Port/host**: configure with `MCP_PORT` (default `3000`) and `MCP_HOST` (default `127.0.0.1`).
- **Per-request auth**: send `SDE_HOST` and `SDE_API_KEY` as headers (or `sde_host` / `sde_api_key` in the initialize request body).

### HTTPS unsafe mode

By default, the server rejects non-HTTPS `SDE_HOST` values. For local/dev instances that only serve HTTP, set:

```bash
SDE_ALLOW_INSECURE_HTTP=true
```

This allows `http://` hosts. Use only in trusted environments.

Example initialize request:

```bash
curl -sS http://127.0.0.1:3000/mcp \
  -H "Content-Type: application/json" \
  -H "SDE_HOST: https://your-sdelements-instance.com" \
  -H "SDE_API_KEY: your-api-key-here" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"example","version":"0.0.0"}}}'
```

### Client setup (Cursor + Claude Desktop)

Both clients use the same `mcpServers` object — the only difference is **where you paste it**.

- **Cursor**: add this under MCP settings (Cursor “MCP Servers” / `mcpServers`).
- **Claude Desktop**: add this to `claude_desktop_config.json`.

Pick one execution style:

- **Option A (recommended)**: run from the GitHub repo via `npx` (builds on install)

```json
{
  "mcpServers": {
    "sdelements": {
      "command": "npx",
      "args": ["-y", "github:sdelements/sde-mcp"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

- **Option B**: run from a local checkout (build output)

```json
{
  "mcpServers": {
    "sdelements": {
      "command": "node",
      "args": ["/absolute/path/to/sde-mcp/dist/main.js"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### HTTP client setup (Cursor)

Start the HTTP server (`npm run start:http`) and set `MCP_SDE_INSTANCE_ALLOWLIST` as described above. Then configure Cursor with an HTTP MCP server entry:

```json
{
  "mcpServers": {
    "sdelements-http": {
      "url": "http://127.0.0.1:3000/mcp",
      "headers": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Build

```bash
npm run build
```

### Local checkout build (for Option B)

```bash
npm ci
npm run build
```

### Tools

- **Toolset selection**: default is **compact**. Set `SDE_TOOLSET=full` to expose the legacy toolset.
- **Note**: diagrams and reporting tools are not exposed.
- **Compact tools (default)**:
  - `project`, `application`, `business_unit`, `project_survey`, `project_countermeasures`, `library_search`
  - plus **Generic**: `test_connection`, `api_request`
- **Legacy tools (when `SDE_TOOLSET=full`)**:
  - **Projects**: `list_projects`, `get_project`, `create_project`, `update_project`, `create_project_from_code`
  - **Library search**: `library_search` (supports countermeasures, threats, components, weaknesses, profiles, risk policies, answers, countermeasure statuses, countermeasure how-tos)
  - **Applications**: `list_applications`, `get_application`, `create_application`, `update_application`
  - **Business units**: `list_business_units`, `get_business_unit`, `create_business_unit`, `update_business_unit`
  - **Countermeasures**: `list_countermeasures`, `get_countermeasure`, `update_countermeasure`, `add_countermeasure_note`, `get_task_status_choices`
  - **Surveys**: `get_project_survey`, `get_survey_answers_for_project`, `update_project_survey`, `find_survey_answers`, `set_project_survey_by_text`, `add_survey_answers_by_text`, `remove_survey_answers_by_text`, `commit_survey_draft`, `add_survey_question_comment`
  - **Scans**: `list_scan_connections`, `scan_repository`, `get_scan_status`, `list_scans`
  - **Users**: `list_users`, `get_user`, `get_current_user`
  - **Library**: `library_search`
  - **Generic**: `test_connection`, `api_request`

### Notes

- **Missing env vars**: tools will fail if `SDE_HOST` / `SDE_API_KEY` aren’t set.
