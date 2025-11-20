"""
Test prompt-to-tool mappings from CSV file.

This test reads prompts and expected tool associations from a CSV file
and validates them using an actual LLM. This allows the product team
to manage test cases in a spreadsheet.
"""
import csv
import os
from pathlib import Path
from typing import List, Dict, Optional

# Import pytest only if available (for running as pytest test)
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

# Load .env file if it exists (for OpenAI API key)
try:
    from dotenv import load_dotenv
    env_paths = [
        Path(__file__).parent.parent / ".env",  # Project root
        Path(__file__).parent / ".env",  # Tests directory
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # dotenv not available, skip

# Import OpenAI client
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def load_prompt_mappings(csv_path: Optional[Path] = None) -> List[Dict[str, str]]:
    """
    Load prompt-to-tool mappings from CSV file.
    
    CSV format:
    prompt,expected_tools,category,description,priority
    
    Returns list of dictionaries with prompt and expected_tools.
    """
    if csv_path is None:
        csv_path = Path(__file__).parent / "prompts_tool_mapping.csv"
    
    mappings = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mappings.append({
                'prompt': row['prompt'],
                'expected_tools': row['expected_tools'].split(','),  # Can have multiple tools
                'category': row.get('category', ''),
                'description': row.get('description', ''),
                'priority': row.get('priority', 'medium'),
            })
    
    return mappings


def get_llm_client():
    """Get OpenAI client"""
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and HAS_OPENAI:
        return openai.OpenAI(api_key=openai_key), "gpt"
    
    return None, None


def check_tool_in_response(response_text: str, expected_tools: List[str]) -> tuple[bool, List[str]]:
    """
    Check if expected tools are mentioned in the LLM response.
    
    Returns:
        (found, found_tools) - whether any expected tool was found, and which ones
    """
    response_lower = response_text.lower()
    found_tools = []
    
    for tool_name in expected_tools:
        tool_lower = tool_name.strip().lower()
        # Check various patterns
        patterns = [
            tool_lower,
            tool_lower.replace('_', ' '),
            f"call {tool_lower}",
            f"use {tool_lower}",
            f"{tool_lower}(",
            f"tool: {tool_lower}",
        ]
        
        if any(pattern in response_lower for pattern in patterns):
            found_tools.append(tool_name)
    
    return len(found_tools) > 0, found_tools


# Only define pytest fixtures and tests if pytest is available
if HAS_PYTEST:
    @pytest.fixture
    def prompt_mappings():
        """Load prompt mappings from CSV"""
        return load_prompt_mappings()


    @pytest.fixture
    def llm_client():
        """Get OpenAI client for integration tests"""
        client, model_type = get_llm_client()
        if not client:
            pytest.skip("No OpenAI client available. Install openai package and set OPENAI_API_KEY.")
        return client, model_type


    @pytest.fixture
    def available_tools():
        """Get list of available tools from the server with descriptions"""
        # Import here to avoid circular imports
        from sde_mcp_server.server import mcp
        
        # Tool descriptions to help LLM distinguish between similar tools
        tool_descriptions = {
            # Connection/API tools
            "test_connection": "Test the connection to SD Elements API (for connectivity checks)",
            "api_request": "Make a generic API request to custom endpoint. Use when user says 'make a GET/POST request', 'call API endpoint', or 'custom API call'. Do NOT use for specific operations - use dedicated tools instead.",
            
            # Survey tools - IMPORTANT: distinguish between add vs set
            "add_survey_answers_by_text": "ADD new answers to existing survey. Use when user says 'add', 'include', or wants to keep existing answers. Preserves all existing answers and adds new ones.",
            "set_project_survey_by_text": "SET/REPLACE all survey answers. Use when user says 'set', 'replace', or wants to completely change all answers. REPLACES all existing answers with new ones. Do NOT use when user says 'add'.",
            "remove_survey_answers_by_text": "Remove specific answers from survey",
            "get_project_survey": "Get the complete survey structure (all available questions and ALL possible answers). Use to see what questions exist. Use get_survey_answers_for_project to see only selected answers.",
            "get_survey_answers_for_project": "Get survey answers FOR A PROJECT that are currently selected/assigned. Use when user says 'survey answers FOR project', 'show me the answers FOR project', 'what answers are set FOR project', or 'answers FOR project'. Returns only selected answers for the project, not all available ones.",
            "commit_survey_draft": "Commit survey draft to publish survey and generate countermeasures",
            "find_survey_answers": "Find survey answer IDs by searching for answer text (e.g., 'Python', 'Django')",
            "update_project_survey": "Update project survey answers using answer IDs (not text)",
            
            # Countermeasure tools
            "list_countermeasures": "List all countermeasures for a project (use this to see countermeasures)",
            "get_countermeasure": "Get details of a SPECIFIC countermeasure by its ID. Use when user asks about a particular countermeasure (e.g., 'countermeasure 123', 'T21'). Do NOT use when user asks about available status choices or what statuses are valid - use get_task_status_choices instead.",
            "get_task_status_choices": "Get the complete list of ALL available task status choices. Use when user asks: 'What task statuses are available?', 'What statuses can I use?', 'Show me valid status values', 'What status values are valid for countermeasures?', or any question about available/valid status options. Returns the list of possible statuses (e.g., 'Complete', 'Not Applicable', 'In Progress'), NOT the status of a specific countermeasure.",
            "update_countermeasure": "Update countermeasure (status or notes). Use for 'update status', 'mark as complete', 'change status'. Do NOT use for 'add note', 'document' - use add_countermeasure_note.",
            "add_countermeasure_note": "Add a note to countermeasure. Use when user says 'add note', 'document', 'note that', 'record that', or wants to add documentation. Use update_countermeasure for status changes.",
            
            # Project tools
            "list_projects": "List all projects",
            "get_project": "Get detailed project information (not for listing countermeasures)",
            "create_project": "Create a new project. If profile not specified, attempts to detect from name/description (e.g., 'mobile project' → Mobile profile). If detection fails, prompts user to select from available profiles.",
            "create_project_from_code": "Create application and project from code repository scan",
            "update_project": "Update project (name, description, status, risk_policy). Use for 'update', 'change', 'modify', 'rename', or 'set risk policy'. Do NOT use for 'archive', 'delete', 'remove' - use delete_project.",
            "delete_project": "Delete/remove/archive a project. Use when user says 'delete', 'remove', 'archive', or wants to permanently remove. Do NOT use update_project for archiving.",
            "list_profiles": "List all available profiles",
            "list_risk_policies": "List all available risk policies",
            "get_risk_policy": "Get details of a specific risk policy",
            
            # Application tools
            "list_applications": "List all applications",
            "get_application": "Get application details",
            "create_application": "Create a new application",
            "update_application": "Update application information",
            
            # User tools
            "list_users": "List all users",
            "get_user": "Get user details",
            "get_current_user": "Get current authenticated user",
            
            # Business unit tools
            "list_business_units": "List business units",
            "get_business_unit": "Get business unit details",
            
            # Scan tools
            "list_scan_connections": "List repository scan connections",
            "scan_repository": "Scan a repository to auto-populate survey",
            "get_scan_status": "Get scan status",
            "list_scans": "List all scans",
            
            # Report tools
            "list_advanced_reports": "List available reports",
            "get_advanced_report": "Get report details",
            "run_advanced_report": "Execute a report",
            "create_advanced_report": "Create a new report",
            "execute_cube_query": "Execute a custom Cube API query for advanced analytics",
            
            # Diagram tools
            "list_project_diagrams": "List all diagrams for a project",
            "get_diagram": "Get a specific diagram with its data",
            "create_diagram": "Create a new project diagram",
            "update_diagram": "Update an existing diagram",
            "delete_diagram": "Delete a project diagram",
        }
        
        # Return both list and descriptions
        return list(tool_descriptions.keys()), tool_descriptions


    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.parametrize("mapping", load_prompt_mappings())
    async def test_prompt_triggers_expected_tools(mapping, llm_client, available_tools, skip_if_no_llm):
        """
        Test that prompts from CSV trigger the expected tools.
        
        This test is parametrized - it runs once for each row in the CSV.
        """
        client, model_type = llm_client
        prompt = mapping['prompt']
        expected_tools = mapping['expected_tools']
        category = mapping.get('category', '')
        priority = mapping.get('priority', 'medium')
        
        # Build system message with available tools and descriptions
        tools_list, tool_descriptions = available_tools
        
        # Create tool descriptions text
        tools_desc_text = "\n".join([f"- {tool}: {desc}" for tool, desc in sorted(tool_descriptions.items())])
        
        system_message = f"""You are a helpful assistant with access to SD Elements tools.

Available tools with descriptions:
{tools_desc_text}

IMPORTANT: Pay close attention to keywords in the user's request:
- If user says "add", "include", or wants to add to existing data → use tools with "add" in the name
- If user says "set", "replace", or wants to replace all data → use tools with "set" or "replace" in the name
- If user says "list" or "show all" → use tools with "list" in the name
- If user says "get" or wants details of one item → use tools with "get" in the name

When the user makes a request, identify which tool(s) you would use to fulfill it.
Respond with ONLY the tool name(s) you would call (comma-separated if multiple)."""

        messages = [{"role": "user", "content": prompt}]
        
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": system_message}] + messages,
            max_tokens=500,
        )
        response_text = response.choices[0].message.content
        
        # Check if expected tools are mentioned
        found, found_tools = check_tool_in_response(response_text, expected_tools)
        
        assert found, (
            f"Prompt '{prompt}' (category: {category}, priority: {priority}) "
            f"did not trigger expected tool(s) {expected_tools}. "
            f"LLM response: {response_text[:200]}"
        )


    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_all_high_priority_prompts(llm_client, prompt_mappings, available_tools, skip_if_no_llm):
        """
        Test all high-priority prompts to ensure critical paths work.
        """
        client, model_type = llm_client
        
        high_priority = [m for m in prompt_mappings if m.get('priority', 'medium') == 'high']
        
        tools_list, tool_descriptions = available_tools
        tools_desc_text = "\n".join([f"- {tool}: {desc}" for tool, desc in sorted(tool_descriptions.items())])
        system_message = f"""You are a helpful assistant with access to SD Elements tools.
Available tools with descriptions:
{tools_desc_text}

IMPORTANT: Pay close attention to keywords in the user's request:
- If user says "add", "include", or wants to add to existing data → use tools with "add" in the name
- If user says "set", "replace", or wants to replace all data → use tools with "set" or "replace" in the name
- If user says "list" or "show all" → use tools with "list" in the name
- If user says "get" or wants details of one item → use tools with "get" in the name

When the user makes a request, identify which tool(s) you would use.
Respond with ONLY the tool name(s) you would call."""

        failures = []
        
        for mapping in high_priority:
            prompt = mapping['prompt']
            expected_tools = mapping['expected_tools']
            
            messages = [{"role": "user", "content": prompt}]
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": system_message}] + messages,
                max_tokens=500,
            )
            response_text = response.choices[0].message.content
            
            found, found_tools = check_tool_in_response(response_text, expected_tools)
            
            if not found:
                failures.append({
                    'prompt': prompt,
                    'expected': expected_tools,
                    'response': response_text[:200],
                })
        
        if failures:
            failure_msg = "\n".join(
                f"  - '{f['prompt']}' expected {f['expected']}, got: {f['response']}"
                for f in failures
            )
            pytest.fail(f"High-priority prompts failed:\n{failure_msg}")


def validate_csv_structure(csv_path: Optional[Path] = None):
    """
    Validate that the CSV file has the correct structure.
    Can be run as a standalone check.
    """
    if csv_path is None:
        csv_path = Path(__file__).parent / "prompts_tool_mapping.csv"
    
    required_columns = ['prompt', 'expected_tools']
    optional_columns = ['category', 'description', 'priority']
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        
        if not columns:
            raise ValueError("CSV file is empty or has no header row")
        
        # Check required columns
        for col in required_columns:
            if col not in columns:
                raise ValueError(f"CSV missing required column: {col}")
        
        # Validate rows
        for i, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            if not row.get('prompt', '').strip():
                raise ValueError(f"Row {i}: prompt is empty")
            if not row.get('expected_tools', '').strip():
                raise ValueError(f"Row {i}: expected_tools is empty")
    
    return True


@pytest.mark.unit
def test_csv_structure():
    """Unit test to validate CSV structure"""
    validate_csv_structure()


if __name__ == "__main__":
    import sys
    
    if not HAS_PYTEST:
        print("⚠️  pytest is not installed.")
        print("\nInstall test dependencies:")
        print("  pip install -r tests/requirements.txt")
        print("  # or")
        print("  pip install sde-mcp-server[integration]")
        print("\nThen run with pytest:")
        print("  pytest tests/test_prompt_mapping_from_csv.py -v")
        sys.exit(1)
    
    print("This is a pytest test file. Run it with:")
    print("  pytest tests/test_prompt_mapping_from_csv.py -v")
    print("\nOr validate the CSV structure:")
    print("  python tests/validate_csv.py --summary")
    print("\nTo run tests directly, use pytest:")
    print("  pytest tests/test_prompt_mapping_from_csv.py::test_csv_structure -v")
    
    # Try to validate CSV if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        try:
            validate_csv_structure()
            print("\n✓ CSV structure is valid")
            sys.exit(0)
        except Exception as e:
            print(f"\n✗ CSV validation failed: {e}")
            sys.exit(1)
    else:
        sys.exit(0)

