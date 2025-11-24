# SD Elements MCP Server

A Model Context Protocol server that provides **SD Elements API integration**. This server enables LLMs to interact with SD Elements security development lifecycle platform.

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

</div>

## Available Tools

### Project Management
* `list_projects` - List all projects with optional filtering
* `get_project` - Get detailed project information
* `create_project` - Create a new project
* `create_project_from_code` - Create application and project in SD Elements. Returns the project survey structure with all available questions and answers. **IMPORTANT:** The AI client must review the survey structure, determine appropriate answers based on the project context, set them using `add_survey_answers_by_text` or `set_project_survey_by_text`, and then commit the survey draft using `commit_survey_draft` to publish the survey and generate countermeasures.
* `update_project` - Update project details (name, description, status, risk_policy)
* `delete_project` - Delete a project
* `list_profiles` - List all available profiles
* `list_risk_policies` - List all available risk policies
* `get_risk_policy` - Get details of a specific risk policy

### Application Management
* `list_applications` - List all applications
* `get_application` - Get application details
* `create_application` - Create a new application
* `update_application` - Update application information

### Countermeasures
* `list_countermeasures` - List countermeasures for a project
* `get_countermeasure` - Get countermeasure details
* `update_countermeasure` - Update countermeasure status or details
* `add_countermeasure_note` - Add a note to an existing countermeasure (convenience tool for adding notes only)

**Important Note on Adding Notes:**
- `update_countermeasure` with the `notes` parameter sets a `status_note`, which is only saved when the status actually changes
- If a countermeasure already has the target status, use `add_countermeasure_note` instead to ensure the note is saved
- Alternatively, you can change the status to a different value first, then back to the target status to trigger saving the `status_note`

### Project Surveys
* `get_project_survey` - Get the complete survey structure for a project
* `get_survey_answers_for_project` - Get the survey answers that are currently selected/assigned for a project in readable format
* `update_project_survey` - Update project survey answers with answer IDs
* `find_survey_answers` - Find answer IDs by searching for answer text (e.g., "Java", "Web Application")
* `set_project_survey_by_text` - Set survey using answer text directly instead of IDs
* `add_survey_answers_by_text` - Add answers to survey without removing existing ones (e.g., add "Python")
* `remove_survey_answers_by_text` - Remove specific answers from survey (e.g., remove "Java")

### Repository Scanning
* `list_scan_connections` - List available repository scan connections (GitHub/GitLab)
* `scan_repository` - Scan a repository to automatically populate project survey
* `get_scan_status` - Get status and results of a repository scan
* `list_scans` - List all repository scans for a project

### Project Diagrams
* `list_project_diagrams` - List diagrams for a project
* `get_diagram` - Get a specific diagram with its data
* `create_diagram` - Create a new project diagram
* `update_diagram` - Update an existing diagram
* `delete_diagram` - Delete a project diagram

**Note:** The Project Diagrams feature requires enablement by your Customer Success Manager. Contact your CSM if this feature is not available on your instance.

### Advanced Reports
* `list_advanced_reports` - List all advanced reports
* `get_advanced_report` - Get report configuration
* `run_advanced_report` - Execute a report and get the data (JSON/CSV)
* `create_advanced_report` - Create a new advanced report
* `execute_cube_query` - Execute Cube API queries directly for advanced analytics

## Quick Start

### Using uvx (recommended)

#### Option 1: From GitHub (Current)
```bash
uvx git+https://github.com/geoffwhittington/sde-mcp.git
```

#### Option 2: From PyPI (Future - when published)
```bash
uvx sde-mcp-server
```

### Using uv

#### Install from GitHub
```bash
uv pip install git+https://github.com/geoffwhittington/sde-mcp.git
sde-mcp-server
```

#### Install from PyPI (when available)
```bash
uv pip install sde-mcp-server
sde-mcp-server
```

### Using pip

#### Install from GitHub
```bash
pip install git+https://github.com/geoffwhittington/sde-mcp.git
sde-mcp-server
```

#### Install from PyPI (when available)
```bash
pip install sde-mcp-server
sde-mcp-server
```

## Configuration

The server requires two environment variables:

- `SDE_HOST`: Your SD Elements instance URL (e.g., `https://your-sdelements-instance.com`)
- `SDE_API_KEY`: Your SD Elements API key

### Setting Environment Variables

#### Option 1: Environment Variables
```bash
export SDE_HOST="https://your-sdelements-instance.com"
export SDE_API_KEY="your-api-key-here"
```

#### Option 2: .env File
Create a `.env` file in your working directory:
```env
SDE_HOST=https://your-sdelements-instance.com
SDE_API_KEY=your-api-key-here
```

### Getting Your API Key

1. Log into your SD Elements instance
2. Go to **Settings** > **API Tokens**
3. Generate a new API token
4. Copy the token value for use as `SDE_API_KEY`

## MCP Client Configuration

### Claude Desktop

Add this to your Claude Desktop configuration file:

#### Option 1: From GitHub (Current)
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "uvx",
      "args": ["git+https://github.com/geoffwhittington/sde-mcp.git"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Option 2: From PyPI (Future)
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "uvx",
      "args": ["sde-mcp-server"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Cline

Add this to your Cline MCP settings:

#### From GitHub (Current)
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "uvx",
      "args": ["git+https://github.com/geoffwhittington/sde-mcp.git"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Continue

Add this to your Continue configuration:

#### From GitHub (Current)
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "uvx",
      "args": ["git+https://github.com/geoffwhittington/sde-mcp.git"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Cursor

Add this to your Cursor configuration file:

#### Option 1: From GitHub (Current)
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "uvx",
      "args": ["git+https://github.com/geoffwhittington/sde-mcp.git"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Option 2: Using local installation
If you have the package installed locally:
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "sde-mcp-server",
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Option 3: Using Python module directly
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "python",
      "args": ["-m", "sde_mcp_server"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Development

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed
- Python 3.10 or higher

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd sde-mcp-server

# Create virtual environment and install dependencies
uv sync

# Run in development mode
uv run python -m sde_mcp_server
```

### Testing Locally

### Testing

**Setup (one-time):**
```bash
# Install project + test dependencies
pip install -e ".[test-all]"
# OR with uv:
uv sync --all-extras

# Set up API key for integration tests (optional)
cp tests/.env.example .env
# Edit .env and add: OPENAI_API_KEY=your-key-here
```

**Run tests (always from project root):**
```bash
# CSV-driven prompt-to-tool mapping tests (requires OpenAI API key)
pytest tests/test_prompt_mapping_from_csv.py -m 'integration and not unit' -v
```

**Test with MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector python -m sde_mcp_server
```

**Important:** 
- Always run tests from the project root directory (not from `tests/`)
- The project must be installed first (`pip install -e .` or `uv sync`)
- Test dependencies are isolated - they don't pollute the server installation

See `tests/README.md` for full testing guide.

### Building

```bash
# Build the package
uv build

# Install locally for testing
uv pip install dist/*.whl

# Test the installed package
sde-mcp-server
```

## Key Features & Use Cases

### 1. Project & Application Management

**Create and manage projects:**

```
"Create a new project called 'Mobile Banking App' in application 456"
"Update project 123's description to 'Customer-facing mobile banking application'"
"List all projects and show their status"
"Delete project 789"
```

**Create project from code context:**

```
"Create an SD Elements project based on the code in this repository"
"Model the sde_mcp_server codebase in SD Elements"
```

**Note:** After creating the project, you must:
1. Review the survey structure returned by the tool
2. Set appropriate survey answers using `add_survey_answers_by_text` or `set_project_survey_by_text`
3. Commit the survey draft using `commit_survey_draft` to generate countermeasures

The `create_project_from_code` tool:
- Creates or uses an existing application
- Creates a new project in that application
- Returns the complete survey structure with all available questions and answers

**IMPORTANT:** This tool does NOT automatically set survey answers or commit the draft. The AI client MUST:
1. Review the returned survey structure (all available questions and answers)
2. Use its AI knowledge to determine appropriate survey answers based on the project context
3. Call `add_survey_answers_by_text` or `set_project_survey_by_text` to set the answers
4. Call `commit_survey_draft` to publish the survey and generate countermeasures

The survey draft is NOT committed automatically. The AI client must commit it after setting the answers to ensure countermeasures are generated.

**Manage applications:**

```
"Create an application called 'Customer Portal'"
"List all applications"
"Update application 456's description"
"Get details for application 123"
```

### 2. Natural Language Survey Management

**Set surveys using plain English instead of answer IDs:**

```
"Set the survey for project 123 to: Python, Django, PostgreSQL, AWS, Docker"
```

**Add/remove specific technologies:**

```
"Add Redis and Kubernetes to project 123"
"Remove Java from the survey"
"Replace MySQL with PostgreSQL"
```

**Query current configuration:**

```
"What answers are in the survey for project 123?"
"Show me the current survey answers"
"Show the survey answers grouped by section"
```

**Commit survey changes:**

```
"Commit the survey draft for project 123"
```

**No need to know answer IDs** - just use technology names like "Java", "Python", "AWS", etc.

### 3. Automated Repository Scanning

**Scan repositories to auto-populate surveys:**

```
"Scan https://github.com/myorg/api-service for project 123"
```

The system will:
- Detect programming languages, frameworks, databases
- Identify cloud technologies and dependencies
- Automatically update the project survey
- Lock the project during scan for data integrity

**Check scan progress:**

```
"Is my scan complete?"
"What did the repository scan detect?"
"Show scan status for project 123"
"List all scans"
"List available repository connections"
```

### 4. Threat Model Diagrams

**Manage diagrams:**

```
"List all diagrams for project 123"
"Get diagram 456"
"Create a new diagram for project 123"
"Update diagram 456 with new data"
"Delete diagram 789"
```

**Note:** The Project Diagrams feature must be enabled on your SD Elements instance. Contact your Customer Success Manager to enable this feature.

### 5. Countermeasure Management

**Track and manage security countermeasures:**

```
"List all countermeasures for project 123"
"Show open countermeasures for project 123"
"Get details for countermeasure 456"
"Update countermeasure 456 status to complete"
"Add a note to countermeasure 789"
"Add notes to countermeasure 789" (uses `add_countermeasure_note` tool)
```

**Important:** When adding notes to countermeasures:
- Use `add_countermeasure_note` when the countermeasure already has the target status
- `update_countermeasure` with `notes` only saves the note when the status actually changes
- If you need to add a note without changing status, always use `add_countermeasure_note`

### 6. Advanced Reporting

**Work with reports:**

```
"List all available reports"
"Run report 123 in JSON format"
"Get report 456 configuration"
"Create a report showing all projects with their countermeasure status"
```

**Execute custom Cube queries:**

```
"Execute a Cube query to analyze security trends"
"Run a custom query on the countermeasure schema"
```

Use the Advanced Reports and Cube API to generate custom analytics and insights from your SD Elements data.

### 7. User & Team Management

**Manage users and teams:**

```
"List all active users"
"Get details for user 123"
"Who am I? (get current authenticated user)"
"List all business units"
"Get business unit 456 details"
```

### 8. Connection Testing & Generic API Access

**Test API connectivity:**

```
"Test the connection to SD Elements"
"Verify my API credentials"
```

**Make custom API requests:**

```
"Make a GET request to endpoint projects/123/"
"Call the custom API endpoint with specific parameters"
```

## Features

- **Natural Language Control**: Manage SD Elements using plain English
- **Full API Coverage**: Supports all major SD Elements API endpoints
- **Authentication**: Secure API key-based authentication
- **Error Handling**: Comprehensive error handling and validation
- **Environment Configuration**: Flexible configuration via environment variables
- **Modern Python**: Built with modern Python packaging (uv, pyproject.toml)
- **MCP Compliant**: Fully compatible with the Model Context Protocol

## Complete Example Workflows

### Project Setup Workflow

```
# Create application and project
"Create an application called 'E-Commerce Platform'"
→ AI: "Created application (ID: 456)"

"Create a project called 'Payment Service' in application 456"
→ AI: "Created project (ID: 789)"

# Set up initial survey
"Set the survey for project 789 to: Python, FastAPI, PostgreSQL, Redis, AWS, Docker"
→ AI: "Survey updated with 6 answers"

# Verify setup
"List all projects and show their details"
→ AI: Shows all projects including the new one

"Get details for project 789"
→ AI: Shows full project details including survey configuration
```

### Survey Management Workflow

```
# Check current state
"What's in the survey for project 123?"
→ AI: "Currently has: Java, MySQL, Tomcat, On-Premise"

# Make changes
"Replace Java with Python, MySQL with PostgreSQL, and Tomcat with Docker"
→ AI: "Updated survey. Removed: Java, MySQL, Tomcat. Added: Python, PostgreSQL, Docker"

# Add new technology
"Add Redis for caching"
→ AI: "Added Redis. Total answers: 5"

# View detailed survey
"Show me the survey answers grouped by section"
→ AI: Shows answers organized by survey sections (Architecture, Technologies, etc.)

# Commit changes
"Commit the survey draft for project 123"
→ AI: "Survey draft committed successfully"
```

### Repository Scanning Workflow

```
# First time setup (one-time)
"List my scan connections"
→ AI: "Found 1 connection: GitHub (ID: 1)"

# Scan repositories (anytime)
"Scan https://github.com/company/api-service for project 456"
→ AI: "Scan started (ID: 789). Analyzing repository..."

# Check progress
"What's the status of scan 789?"
→ AI: "Scan complete! Detected: Python, FastAPI, PostgreSQL, Docker, AWS"

# List all scans
"List all scans for project 456"
→ AI: Shows scan history with status and results

# Survey is now auto-populated
"Show me the survey"
→ AI: "Survey has 15 answers based on repository scan"
```

### Diagram Management Workflow

```
# List diagrams
"List all diagrams for project 123"
→ AI: Shows all diagrams with names and IDs

# View diagram
"Get diagram 456"
→ AI: Returns full diagram data

# Create diagram
"Create a new diagram called 'System Architecture' for project 123"
→ AI: "Diagram created successfully"

# Update diagram
"Update diagram 456 with new data"
→ AI: "Diagram updated successfully"

# Delete diagram
"Delete diagram 789"
→ AI: "Diagram deleted successfully"
```

**Note:** Diagrams must be created/edited through the SD Elements UI or API with proper JSON schema. The feature requires CSM enablement.

### Countermeasure Management Workflow

```
# View countermeasures
"List all countermeasures for project 123"
→ AI: Shows all countermeasures with status

"Show only open countermeasures for project 123"
→ AI: Filters to show incomplete countermeasures

# Update countermeasure
"Get details for countermeasure 456"
→ AI: Shows full countermeasure details

"Update countermeasure 456 status to completed"
→ AI: "Countermeasure marked as completed"

"Add a note to countermeasure 456: Implemented OAuth 2.0 with JWT tokens"
→ AI: Uses `add_countermeasure_note` tool to add the note (ensures note is saved even if status unchanged)

# Or use the dedicated note tool
"Add a note to countermeasure 789 explaining the implementation approach"
→ AI: Uses `add_countermeasure_note` tool to add the note

# Important: If countermeasure already has target status, use add_countermeasure_note
"Countermeasure 123 is already marked as 'Not Applicable', add a note explaining why"
→ AI: Uses `add_countermeasure_note` to ensure note is saved (update_countermeasure notes only save on status change)
```

### Reporting Workflow

```
# List and run reports
"List all available reports"
→ AI: Shows existing reports

"Run report 123 in JSON format"
→ AI: Executes report and returns JSON data

"Get report 456 configuration"
→ AI: Shows report query structure and parameters

# Create custom reports
"Create a report showing all projects with their security status"
→ AI: Creates custom report with specified parameters

# Execute Cube queries
"Execute a Cube query on the countermeasure schema"
→ AI: Runs query and returns results
```

### User & Team Management Workflow

```
# User management
"List all active users"
→ AI: Shows list of active users

"Who am I?"
→ AI: "You are: John Doe (john.doe@company.com), Role: Admin"

"Get details for user 123"
→ AI: Shows user profile and permissions

# Business units
"List all business units"
→ AI: Shows organizational structure

"Get business unit 456 details"
→ AI: Shows business unit info with associated applications
```

### Full Project Lifecycle Example

```
# 1. Initial Setup
"Create application 'Banking Services'"
"Create project 'Mobile App' in application 123"

# 2. Configure via repository scan
"Scan https://github.com/company/mobile-app for project 456"
"Wait for scan to complete and commit survey"

# 3. Manage diagrams (if enabled)
"List diagrams for project 456"
"Create a new diagram for the project"

# 4. Track security work
"List all countermeasures for project 456"
"Update high-priority countermeasures"

# 5. Monitor progress
"Generate a security status report for project 456"
"Show countermeasure completion trends"

# 6. Make updates
"Add Kubernetes to the survey"
"Update project components"

# 7. Create reports
"Create a report showing security status for all projects"
"Run report 123 to analyze countermeasure trends"
```

## API Coverage

This server provides comprehensive access to SD Elements functionality:

### Core Resources
- **Projects**: Full CRUD (Create, Read, Update, Delete) operations
- **Applications**: Create, list, view, and update applications
- **Business Units**: List and view organizational structure

### Security Management
- **Countermeasures**: List, view, update status, and add notes
  - Use `update_countermeasure` to change status (notes are saved as status_note when status changes)
  - Use `add_countermeasure_note` to add notes to countermeasures that already have the target status
  - Note: `update_countermeasure`'s `notes` parameter only saves when status actually changes
- **Project Surveys**: Full survey management with natural language support
  - Set answers using technology names (no ID lookup needed)
  - Add/remove specific answers incrementally
  - View current configuration in multiple formats
  - Commit survey drafts
  - Auto-resolve dependencies

### Automation & Integration
- **Repository Scanning**: Automated technology detection
  - GitHub and GitLab integration
  - Automatic survey population
  - Scan status tracking
  - Historical scan management
  
- **Threat Model Diagrams**: Complete diagram lifecycle (requires CSM enablement)
  - Full CRUD operations
  - List, view, create, update, and delete diagrams
  - Work with diagram data via API

### Analytics & Reporting
- **Advanced Reports**: Flexible reporting and analytics
  - List available reports
  - Execute existing reports (JSON/CSV output)
  - Create custom reports with Cube API
  - Execute Cube queries directly for advanced analytics

### User & Team Management
- **Users**: List users, view profiles, get current user
- **Authentication**: Test API connectivity and credentials

### Advanced Features
- **Generic API Access**: Make custom API calls to any SD Elements endpoint
- **Flexible Configuration**: Environment-based setup with `.env` support
- **Natural Language Interface**: Control everything through plain English commands

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and questions:

1. Check the [Issues](../../issues) page
2. Review the SD Elements API documentation
3. Ensure your API key has proper permissions

---

**Note**: This is an unofficial MCP server for SD Elements. For official SD Elements support, please contact Security Compass. 