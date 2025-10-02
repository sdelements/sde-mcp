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
* `update_project` - Update project details
* `delete_project` - Delete a project

### Application Management
* `list_applications` - List all applications
* `get_application` - Get application details
* `create_application` - Create a new application
* `update_application` - Update application information

### Countermeasures
* `list_countermeasures` - List countermeasures for a project
* `get_countermeasure` - Get countermeasure details
* `update_countermeasure` - Update countermeasure status

### Project Surveys
* `get_project_survey` - Get the complete survey structure for a project
* `get_current_survey_answers` - Get the current answers assigned to a survey in readable format
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
* `create_diagram_from_description` - Create a diagram from natural language architecture description
* `import_diagram` - Import diagram from Microsoft Threat Modeling Tool, diagrams.net (draw.io), or JSON

**Import from local files:**
In Cursor or other MCP clients, you can reference local files directly:
```
"Import the diagram from ./diagrams/threat-model.json into project 123"
"Read my draw.io file at ~/Documents/architecture.drawio and import it to project 456"
```
The AI will read the file and use `import_diagram` automatically.

### Advanced Reports
* `list_advanced_reports` - List all advanced reports
* `get_advanced_report` - Get report configuration
* `run_advanced_report` - Execute a report and get the data (JSON/CSV)
* `create_advanced_report` - Create a new advanced report
* `generate_report_from_description` - Generate and analyze reports using natural language

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

#### Step 1: Set Up Environment Variables

Create a `.env` file in the project root [[memory:4265507]]:

```bash
# .env
SDE_HOST=https://your-sdelements-instance.com
SDE_API_KEY=your-actual-api-key-here
```

Or export them:

```bash
export SDE_HOST="https://your-sdelements-instance.com"
export SDE_API_KEY="your-api-key-here"
```

#### Step 2: Activate Virtual Environment

```bash
# The project uses venv/ for the virtual environment
source venv/bin/activate

# Install dependencies if not already done
uv sync
```

#### Step 3: Test Basic Imports

```bash
# Run the import test
python test_import.py
```

Expected output:
```
✓ Package imported successfully
✓ API client module imported successfully
✓ Server module imported successfully
✓ Main function found
✓ Entry point function found
```

#### Step 4: Test the MCP Server

**Option A: Run with environment variables**
```bash
SDE_HOST=https://your-instance.com SDE_API_KEY=your-key python -m sde_mcp_server
```

**Option B: Run with .env file**
```bash
python -m sde_mcp_server
```

The server will start and output:
```
SD Elements MCP Server starting...
Host: https://your-instance.com
Configuration validated successfully
```

#### Step 5: Test with MCP Inspector (Recommended)

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is the best tool for local testing:

```bash
# Install MCP Inspector
npx @modelcontextprotocol/inspector python -m sde_mcp_server
```

This opens a web interface where you can:
- See all available tools
- Test individual tools with parameters
- View responses in real-time
- Debug issues

#### Step 6: Test in Cursor

**This project includes workspace-specific MCP configuration!**

1. **Add your credentials to `.cursor/mcp.json`:**
   ```bash
   # Edit .cursor/mcp.json and replace the placeholder values:
   nano .cursor/mcp.json
   ```
   
   Replace:
   - `SDE_HOST`: `https://your-sdelements-instance.com` → your actual SD Elements URL
   - `SDE_API_KEY`: `your-api-key-here` → your actual API key

2. **Reload Cursor window** (Cmd/Ctrl+Shift+P → "Developer: Reload Window")

3. **Test with natural language:**
   ```
   "List all projects in SD Elements"
   "Get the survey for project 123"
   "Test the SD Elements connection"
   ```

**Note:** `.cursor/mcp.json` is gitignored to protect your credentials. A template is available at `.cursor/mcp.json.example`.

**If Cursor doesn't auto-detect**, you can add to global config at `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "python3",
      "args": ["-m", "sde_mcp_server"],
      "cwd": "/home/geoff/projects/sde-mcp",
      "env": {
        "PYTHONPATH": "/home/geoff/projects/sde-mcp/venv/lib/python3.10/site-packages"
      }
    }
  }
}
```

#### Step 7: Test Specific Features

**Test Survey Management:**
```bash
# In Cursor or MCP Inspector
"What are the current survey answers for project 1?"
"Add Python to project 1's survey"
```

**Test Repository Scanning:**
```bash
"List my scan connections"
"Scan https://github.com/org/repo for project 1"
```

**Test Diagrams:**
```bash
"List diagrams for project 1"
"Create a diagram from description: Web app with database"
```

### Debugging

**Enable verbose logging:**
```bash
# Add to your code temporarily
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check API connectivity:**
```python
from sde_mcp_server.api_client import SDElementsAPIClient

client = SDElementsAPIClient(
    host="https://your-instance.com",
    api_key="your-key"
)

# Test connection
if client.test_connection():
    print("✓ Connected to SD Elements")
else:
    print("✗ Connection failed")
```

**Common issues:**
- **"Configuration error"**: Check `SDE_HOST` and `SDE_API_KEY` are set
- **"Authentication failed"**: Verify your API key is valid
- **"Connection error"**: Check network access to SD Elements instance
- **Module import errors**: Ensure virtual environment is activated

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

### 1. Natural Language Survey Management

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
```

**No need to know answer IDs** - just use technology names like "Java", "Python", "AWS", etc.

### 2. Automated Repository Scanning

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
```

### 3. Threat Model Diagrams

**Create diagrams from natural language:**

```
"Create a diagram for project 123: Web app with React frontend, 
Node.js API, PostgreSQL database, and Redis cache on AWS"
```

**Import diagrams from files:**

```
"Import the diagram from ./diagrams/threat-model.json into project 123"
"Import my draw.io file at ~/Documents/architecture.drawio"
```

Supports:
- Microsoft Threat Modeling Tool
- diagrams.net (draw.io)
- SD Elements JSON format

### 4. Advanced Reporting with Natural Language

**Generate reports using plain English:**

```
"Show me all high-priority countermeasures across my projects"
"Generate a report of security tasks completed this month"
"What's the status of countermeasures in project 123?"
```

The AI will:
- Find or create appropriate reports
- Execute queries
- Present insights in natural language
- Highlight trends and recommendations

## Features

- **Natural Language Control**: Manage SD Elements using plain English
- **Full API Coverage**: Supports all major SD Elements API endpoints
- **Authentication**: Secure API key-based authentication
- **Error Handling**: Comprehensive error handling and validation
- **Environment Configuration**: Flexible configuration via environment variables
- **Modern Python**: Built with modern Python packaging (uv, pyproject.toml)
- **MCP Compliant**: Fully compatible with the Model Context Protocol

## Complete Example Workflows

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

# Verify
"Show me the updated survey"
→ AI: "Current answers: Python, PostgreSQL, Docker, On-Premise, Redis"
```

### Repository Scanning Workflow

```
# First time setup (one-time)
"List my scan connections"
→ AI: "No connections found. You need to connect GitHub/GitLab first."

"I have a GitHub token: ghp_xxxxxxxxxxxx"
→ AI: "Connected to GitHub successfully!"

# Scan repositories (anytime)
"Scan https://github.com/company/api-service for project 456"
→ AI: "Scan started (ID: 789). Analyzing repository..."

# Check progress
"Is the scan done?"
→ AI: "Scan complete! Detected: Python, FastAPI, PostgreSQL, Docker, AWS"

# Survey is now auto-populated
"Show me the survey"
→ AI: "Survey has 15 answers based on repository scan"
```

### Diagram Creation Workflow

```
# Create from description
"Create a diagram for project 123: Mobile iOS app connecting to REST API, 
with MySQL database and S3 storage"
→ AI: Creates diagram with components: iOS App, REST API, MySQL, Amazon S3

# Import existing diagram
"Import my threat model from ./diagrams/app-threat-model.json"
→ AI: "Imported diagram 'Application Threat Model' with 12 components"

# View diagrams
"List diagrams for project 123"
→ AI: Shows all diagrams with names and IDs
```

### Reporting Workflow

```
# Natural language queries
"Show me all open high-priority security tasks"
→ AI: Generates and presents report with insights

"What countermeasures were completed last month?"
→ AI: "23 countermeasures completed in September. 
      Top categories: Authentication (8), Data Protection (7)..."

"Generate a security status report for all projects"
→ AI: Creates comprehensive report with trends and recommendations
```

## API Coverage

This server provides access to:

- Projects and Applications
- Project Surveys with natural language control
- Repository Scanning (GitHub/GitLab)
- Threat Model Diagrams
- Advanced Reports with natural language queries
- Countermeasures and Tasks
- Users and Teams
- Business Units and Groups

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