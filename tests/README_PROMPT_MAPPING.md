# Prompt-to-Tool Mapping Management

This document explains how to manage prompt-to-tool mappings using the CSV file for the product team.

## CSV File: `prompts_tool_mapping.csv`

The CSV file contains test cases that map user prompts to expected tools. The product team can manage this file in Excel, Google Sheets, or any CSV editor.

## CSV Format

The CSV has the following columns:

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `prompt` | Yes | The user's prompt/question | "Show me all the projects in SD Elements" |
| `expected_tools` | Yes | Comma-separated list of expected tools | `list_projects` or `list_projects,get_project` |
| `category` | No | Category for organization | `projects`, `surveys`, `countermeasures` |
| `description` | No | Description of the test case | "User wants to see all projects" |
| `priority` | No | Test priority | `high`, `medium`, `low` |

## Setup (One-Time)

**Before running tests, install the project and test dependencies:**

```bash
# From project root directory
cd /path/to/sde-mcp

# Install project + test dependencies
pip install -e ".[test-all]"
# OR with uv:
uv sync --all-extras

# Set up API key (for integration tests)
cp tests/.env.example .env
# Edit .env and add: OPENAI_API_KEY=your-key-here
```

## Adding New Test Cases

1. Open `tests/prompts_tool_mapping.csv` in Excel, Google Sheets, or a text editor
2. Add a new row with:
   - **prompt**: The exact user prompt you want to test
   - **expected_tools**: The tool(s) that should be triggered (comma-separated if multiple)
   - **category**: Optional category for grouping
   - **description**: Optional description
   - **priority**: `high`, `medium`, or `low` (defaults to `medium`)

### Example New Row

```csv
prompt,expected_tools,category,description,priority
"Create a project called My App in application 123",create_project,projects,"Create new project with name",high
```

## Available Tools

Here are the main tools available in the SD Elements MCP Server:

### Projects
- `list_projects` - List all projects
- `get_project` - Get project details
- `create_project` - Create a new project
- `update_project` - Update a project (name, description, status, risk_policy)
- `delete_project` - Delete a project
- `list_profiles` - List all available profiles
- `list_risk_policies` - List all available risk policies
- `get_risk_policy` - Get details of a specific risk policy

### Applications
- `list_applications` - List all applications
- `get_application` - Get application details
- `create_application` - Create a new application
- `update_application` - Update an application

### Surveys
- `get_project_survey` - Get project survey structure
- `get_survey_answers_for_project` - Get survey answers for a project
- `set_project_survey_by_text` - Set survey answers by text
- `add_survey_answers_by_text` - Add answers to survey
- `remove_survey_answers_by_text` - Remove answers from survey
- `commit_survey_draft` - Commit survey draft

### Countermeasures
- `list_countermeasures` - List countermeasures for a project
- `get_countermeasure` - Get countermeasure details
- `update_countermeasure` - Update countermeasure
- `add_countermeasure_note` - Add note to countermeasure

### Users & Business Units
- `list_users` - List all users
- `get_user` - Get user details
- `get_current_user` - Get current authenticated user
- `list_business_units` - List business units
- `get_business_unit` - Get business unit details

### Scans
- `list_scan_connections` - List repository scan connections
- `scan_repository` - Scan a repository
- `get_scan_status` - Get scan status
- `list_scans` - List all scans

### Reports
- `list_advanced_reports` - List available reports
- `get_advanced_report` - Get report details
- `run_advanced_report` - Run a report
- `create_advanced_report` - Create a new report

### Utilities
- `test_connection` - Test API connection
- `api_request` - Make generic API request

## Running Tests

**IMPORTANT:** 
- **Always run tests from the project root directory** (not from `tests/`)
- The project must be installed first (see [Setup](#setup-one-time) above)
- Tests must be run with `pytest`, not directly with `python`

### Validate CSV Structure

```bash
# From project root directory
cd /path/to/sde-mcp

# Validate CSV format
python tests/validate_csv.py --summary

# Or run the pytest test
pytest tests/test_prompt_mapping_from_csv.py::test_csv_structure -v
```

### Run All Prompt Mapping Tests

```bash
# From project root directory
cd /path/to/sde-mcp

# Requires OpenAI API key (set in .env file or OPENAI_API_KEY env var)
# Note: Use -m integration to run these tests (they're marked as integration tests)
pytest tests/test_prompt_mapping_from_csv.py -m 'integration and not unit' -v
```

**API Key Setup:**
The API key can be set in a `.env` file in the project root:
```bash
# Copy example and edit
cp tests/.env.example .env
# Edit .env and add: OPENAI_API_KEY=your-key-here
```

### Run Only High-Priority Tests

The test suite includes a test that runs all high-priority prompts:

```bash
# Note: Use -m integration to run integration tests
pytest tests/test_prompt_mapping_from_csv.py::test_all_high_priority_prompts -m 'integration and not unit' -v
```

## Best Practices

1. **Be specific**: Use clear, specific prompts that users would actually say
2. **Test variations**: Add multiple prompts that should trigger the same tool
3. **Use categories**: Group related prompts with categories
4. **Set priorities**: Mark critical user flows as `high` priority
5. **Multiple tools**: If a prompt should trigger multiple tools, list them comma-separated
6. **Keep it updated**: Update the CSV when adding new tools or changing tool names

## CSV Validation

The CSV file is automatically validated:
- Required columns must be present
- No empty prompts or expected_tools
- Proper CSV formatting

## Example CSV Entries

```csv
prompt,expected_tools,category,description,priority
"Show me all the projects",list_projects,projects,"Basic list request",high
"List projects",list_projects,projects,"Short form",high
"What projects do we have?",list_projects,projects,"Question form",medium
"Get project 123",get_project,projects,"Get by ID",high
"Show me project 456 details",get_project,projects,"Get details",high
"Create a project called My App",create_project,projects,"Create with name",high
"Test the connection",test_connection,connection,"Connection test",high
```

## Troubleshooting

**CSV won't load:**
- Check that the file is valid CSV (no unescaped quotes, proper commas)
- Ensure required columns are present
- Check for empty rows

**Tests fail:**
- Verify the tool name matches exactly (case-sensitive)
- Check that the prompt is clear and specific
- Review the LLM response in the test output

**Adding a new tool:**
1. Add the tool to the server code
2. Add test cases to the CSV
3. Update this documentation with the new tool name

