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

- **Projects / profiles / risk policies**: `list_projects`, `get_project`, `create_project`, `update_project`, `delete_project`, `create_project_from_code`, `list_profiles`, `list_risk_policies`, `get_risk_policy`
- **Applications**: `list_applications`, `get_application`, `create_application`, `update_application`
- **Business units**: `list_business_units`, `get_business_unit`
- **Countermeasures**: `list_countermeasures`, `get_countermeasure`, `update_countermeasure`, `add_countermeasure_note`, `get_task_status_choices`
- **Surveys**: `get_project_survey`, `get_survey_answers_for_project`, `update_project_survey`, `find_survey_answers`, `set_project_survey_by_text`, `add_survey_answers_by_text`, `remove_survey_answers_by_text`, `commit_survey_draft`, `add_survey_question_comment`
- **Scans**: `list_scan_connections`, `scan_repository`, `get_scan_status`, `list_scans`
- **Diagrams**: `list_project_diagrams`, `get_diagram`, `create_diagram`, `update_diagram`, `delete_diagram`
- **Reports / Cube**: `list_advanced_reports`, `get_advanced_report`, `update_advanced_report`, `run_advanced_report`, `create_advanced_report`, `execute_cube_query`
- **Users**: `list_users`, `get_user`, `get_current_user`
- **Generic**: `test_connection`, `api_request`

### Notes

- **Missing env vars**: tools will fail if `SDE_HOST` / `SDE_API_KEY` aren’t set.
