#!/usr/bin/env python3
"""
SD Elements MCP Server

A Model Context Protocol (MCP) server for SD Elements API integration.
This server provides tools to interact with SD Elements through the MCP protocol.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    GetPromptRequest,
    GetPromptResult,
    Prompt,
    PromptMessage,
    ListPromptsRequest,
)
from pydantic import BaseModel, ValidationError

from .api_client import SDElementsAPIClient, SDElementsAPIError, SDElementsAuthError, SDElementsNotFoundError
# Load environment variables
load_dotenv()

# Server instance
server = Server("sdelements-mcp")

# Global API client
api_client: Optional[SDElementsAPIClient] = None


class ToolError(Exception):
    """Custom exception for tool execution errors"""
    pass


def init_api_client() -> SDElementsAPIClient:
    """Initialize the SD Elements API client with configuration from environment variables"""
    host = os.getenv("SDE_HOST")
    api_key = os.getenv("SDE_API_KEY")
    
    if not host:
        raise ValueError("SDE_HOST environment variable is required")
    if not api_key:
        raise ValueError("SDE_API_KEY environment variable is required")
    
    return SDElementsAPIClient(host=host, api_key=api_key)


def format_error_response(error: Exception) -> str:
    """Format error response for tool calls"""
    if isinstance(error, SDElementsAuthError):
        return f"Authentication Error: {str(error)}"
    elif isinstance(error, SDElementsNotFoundError):
        return f"Not Found: {str(error)}"
    elif isinstance(error, SDElementsAPIError):
        return f"API Error: {str(error)}"
    elif isinstance(error, ValidationError):
        return f"Validation Error: {str(error)}"
    else:
        return f"Error: {str(error)}"


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools for SD Elements API interaction"""
    return [
        # Project tools
        Tool(
            name="list_projects",
            description="List all projects in SD Elements",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results per page (optional)"
                    },
                    "include": {
                        "type": "string",
                        "description": "Additional fields to include (comma-separated)"
                    },
                    "expand": {
                        "type": "string",
                        "description": "Fields to expand (comma-separated)"
                    }
                }
            }
        ),
        Tool(
            name="get_project",
            description="Get detailed information about a specific project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to retrieve",
                        "minimum": 1
                    },
                    "include": {
                        "type": "string",
                        "description": "Additional fields to include (comma-separated)"
                    },
                    "expand": {
                        "type": "string",
                        "description": "Fields to expand (comma-separated)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="create_project",
            description="Create a new project in SD Elements",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Project description"
                    },
                    "application_id": {
                        "type": "integer",
                        "description": "ID of the application this project belongs to"
                    },
                    "phase_id": {
                        "type": "integer",
                        "description": "ID of the project phase"
                    }
                },
                "required": ["name", "application_id"]
            }
        ),
        Tool(
            name="update_project",
            description="Update an existing project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to update",
                        "minimum": 1
                    },
                    "name": {
                        "type": "string",
                        "description": "Updated project name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Updated project description"
                    },
                    "status": {
                        "type": "string",
                        "description": "Project status"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="delete_project",
            description="Delete a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to delete",
                        "minimum": 1
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_project_survey",
            description="Get the survey for a project, including all questions, sections, and current answers",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="update_project_survey",
            description="Update project survey answers. Provide answer IDs (e.g., 'A21', 'A493') to set survey responses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of answer IDs to set for the project survey (e.g., ['A21', 'A493'])"
                    },
                    "survey_complete": {
                        "type": "boolean",
                        "description": "Mark the survey as complete (optional, defaults to false)"
                    }
                },
                "required": ["project_id", "answers"]
            }
        ),
        Tool(
            name="find_survey_answers",
            description="Find answer IDs by searching for answer text. Use this to convert natural language (e.g., 'Java', 'Web Application') to answer IDs before updating a survey.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "search_texts": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of answer texts to search for (e.g., ['Java', 'Python', 'Web Application'])"
                    }
                },
                "required": ["project_id", "search_texts"]
            }
        ),
        Tool(
            name="set_project_survey_by_text",
            description="Set project survey using answer text instead of IDs. This automatically finds matching answer IDs and updates the survey.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "answer_texts": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of answer texts to set (e.g., ['Java', 'Web Application', 'AWS'])"
                    },
                    "survey_complete": {
                        "type": "boolean",
                        "description": "Mark the survey as complete (optional, defaults to false)"
                    }
                },
                "required": ["project_id", "answer_texts"]
            }
        ),
        Tool(
            name="remove_survey_answers_by_text",
            description="Remove specific answers from a project survey using answer text (e.g., remove 'Java', 'MySQL')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "answer_texts_to_remove": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of answer texts to remove (e.g., ['Java', 'MySQL'])"
                    }
                },
                "required": ["project_id", "answer_texts_to_remove"]
            }
        ),
        Tool(
            name="add_survey_answers_by_text",
            description="Add specific answers to a project survey without removing existing ones (e.g., add 'Python', 'Redis')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "answer_texts_to_add": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of answer texts to add (e.g., ['Python', 'Redis'])"
                    }
                },
                "required": ["project_id", "answer_texts_to_add"]
            }
        ),
        Tool(
            name="get_current_survey_answers",
            description="Get the current answers assigned to a project survey in human-readable format",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "format": {
                        "type": "string",
                        "enum": ["summary", "detailed", "grouped"],
                        "description": "Output format: 'summary' (just answer texts), 'detailed' (with questions), 'grouped' (organized by section)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="commit_survey_draft",
            description="Commit/save the survey draft to apply all pending changes to the project survey",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="create_project_from_code",
            description="Create application and project in SD Elements based on code context. Returns the project survey structure with all available questions and answers. The AI should review the available survey options and use its knowledge to determine appropriate answers based on the project description/context, then call set_project_survey_by_text separately. This tool does NOT use static code analysis - the AI determines answers from the available survey options.",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_name": {
                        "type": "string",
                        "description": "Name of the application to create (or use existing application_id)"
                    },
                    "application_id": {
                        "type": "integer",
                        "description": "ID of existing application (optional, will create new if not provided and application_name is provided)"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project to create"
                    },
                    "project_description": {
                        "type": "string",
                        "description": "Description of the project (optional)"
                    },
                    "code_context": {
                        "type": "string",
                        "description": "Text description of the project/technologies (optional). This is provided for AI context only - the AI will determine survey answers from available options, not from static analysis."
                    }
                },
                "required": ["project_name"]
            }
        ),
        
        # Application tools
        Tool(
            name="list_applications",
            description="List all applications in SD Elements",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results per page (optional)"
                    },
                    "include": {
                        "type": "string",
                        "description": "Additional fields to include (comma-separated)"
                    },
                    "expand": {
                        "type": "string",
                        "description": "Fields to expand (comma-separated)"
                    }
                }
            }
        ),
        Tool(
            name="get_application",
            description="Get detailed information about a specific application",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_id": {
                        "type": "integer",
                        "description": "The ID of the application to retrieve",
                        "minimum": 1
                    },
                    "include": {
                        "type": "string",
                        "description": "Additional fields to include (comma-separated)"
                    },
                    "expand": {
                        "type": "string",
                        "description": "Fields to expand (comma-separated)"
                    }
                },
                "required": ["application_id"]
            }
        ),
        Tool(
            name="create_application",
            description="Create a new application in SD Elements",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Application name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Application description"
                    },
                    "business_unit_id": {
                        "type": "integer",
                        "description": "ID of the business unit this application belongs to"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="update_application",
            description="Update an existing application",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_id": {
                        "type": "integer",
                        "description": "The ID of the application to update",
                        "minimum": 1
                    },
                    "name": {
                        "type": "string",
                        "description": "Updated application name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Updated application description"
                    }
                },
                "required": ["application_id"]
            }
        ),
        
        # Countermeasure tools
        Tool(
            name="list_countermeasures",
            description="List countermeasures for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by countermeasure status"
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results per page (optional)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_countermeasure",
            description="Get detailed information about a specific countermeasure",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "countermeasure_id": {
                        "type": "integer",
                        "description": "The ID of the countermeasure to retrieve (task number, e.g., 536 for T536)",
                        "minimum": 1
                    },
                    "risk_relevant": {
                        "type": "boolean",
                        "description": "Filter by risk relevance. If true, only return risk-relevant countermeasures. Defaults to true.",
                        "default": True
                    }
                },
                "required": ["project_id", "countermeasure_id"]
            }
        ),
        Tool(
            name="update_countermeasure",
            description="Update a countermeasure status or details",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "countermeasure_id": {
                        "type": "integer",
                        "description": "The ID of the countermeasure to update (task number, e.g., 536 for T536)",
                        "minimum": 1
                    },
                    "status": {
                        "type": "string",
                        "description": "New status for the countermeasure (e.g., TS1, TS2)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes about the countermeasure (will be converted to status_note for tasks endpoint)"
                    }
                },
                "required": ["project_id", "countermeasure_id"]
            }
        ),
        
        # User tools
        Tool(
            name="list_users",
            description="List all users in SD Elements",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results per page (optional)"
                    },
                    "active": {
                        "type": "boolean",
                        "description": "Filter by active users only"
                    }
                }
            }
        ),
        Tool(
            name="get_user",
            description="Get detailed information about a specific user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "The ID of the user to retrieve",
                        "minimum": 1
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_current_user",
            description="Get information about the currently authenticated user",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        # Business Unit tools
        Tool(
            name="list_business_units",
            description="List all business units",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results per page (optional)"
                    }
                }
            }
        ),
        Tool(
            name="get_business_unit",
            description="Get detailed information about a specific business unit",
            inputSchema={
                "type": "object",
                "properties": {
                    "business_unit_id": {
                        "type": "integer",
                        "description": "The ID of the business unit to retrieve",
                        "minimum": 1
                    }
                },
                "required": ["business_unit_id"]
            }
        ),
        
        # Repository Scanning (Team Onboarding) tools
        Tool(
            name="list_scan_connections",
            description="List available repository scan connections (GitHub/GitLab)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="scan_repository",
            description="Scan a repository to automatically populate project survey answers",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to scan for",
                        "minimum": 1
                    },
                    "connection_id": {
                        "type": "integer",
                        "description": "The ID of the repository connection to use",
                        "minimum": 1
                    },
                    "repository_url": {
                        "type": "string",
                        "description": "The repository URL to scan (e.g., 'https://github.com/org/repo')"
                    }
                },
                "required": ["project_id", "connection_id", "repository_url"]
            }
        ),
        Tool(
            name="get_scan_status",
            description="Get the status and results of a repository scan",
            inputSchema={
                "type": "object",
                "properties": {
                    "scan_id": {
                        "type": "integer",
                        "description": "The ID of the scan to check",
                        "minimum": 1
                    }
                },
                "required": ["scan_id"]
            }
        ),
        Tool(
            name="list_scans",
            description="List all repository scans for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project (optional)"
                    }
                }
            }
        ),
        
        # Project Diagrams tools
        Tool(
            name="list_project_diagrams",
            description="List diagrams for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_diagram",
            description="Get a specific project diagram with its data",
            inputSchema={
                "type": "object",
                "properties": {
                    "diagram_id": {
                        "type": "integer",
                        "description": "The ID of the diagram",
                        "minimum": 1
                    }
                },
                "required": ["diagram_id"]
            }
        ),
        Tool(
            name="create_diagram",
            description="Create a new project diagram",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the diagram"
                    },
                    "diagram_data": {
                        "type": "object",
                        "description": "Diagram data in JSON format (optional)"
                    }
                },
                "required": ["project_id", "name"]
            }
        ),
        Tool(
            name="update_diagram",
            description="Update a project diagram",
            inputSchema={
                "type": "object",
                "properties": {
                    "diagram_id": {
                        "type": "integer",
                        "description": "The ID of the diagram to update",
                        "minimum": 1
                    },
                    "name": {
                        "type": "string",
                        "description": "Updated name (optional)"
                    },
                    "diagram_data": {
                        "type": "object",
                        "description": "Updated diagram data (optional)"
                    }
                },
                "required": ["diagram_id"]
            }
        ),
        Tool(
            name="delete_diagram",
            description="Delete a project diagram",
            inputSchema={
                "type": "object",
                "properties": {
                    "diagram_id": {
                        "type": "integer",
                        "description": "The ID of the diagram to delete",
                        "minimum": 1
                    }
                },
                "required": ["diagram_id"]
            }
        ),
        
        # Advanced Reports tools
        Tool(
            name="list_advanced_reports",
            description="List all advanced reports",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_advanced_report",
            description="Get an advanced report configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_id": {
                        "type": "integer",
                        "description": "The ID of the report",
                        "minimum": 1
                    }
                },
                "required": ["report_id"]
            }
        ),
        Tool(
            name="run_advanced_report",
            description="Execute an advanced report and get the data",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_id": {
                        "type": "integer",
                        "description": "The ID of the report to run",
                        "minimum": 1
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "description": "Output format (optional, defaults to json)"
                    }
                },
                "required": ["report_id"]
            }
        ),
        Tool(
            name="create_advanced_report",
            description="Create a new advanced report (query). See https://docs.sdelements.com/master/api/docs/advanced-reports/ for details",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Report title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Report description (optional)"
                    },
                    "chart": {
                        "type": "string",
                        "enum": ["table", "pie", "number", "stacked_bar", "horizontal_bar", "line"],
                        "description": "Chart type for visualization"
                    },
                    "query": {
                        "type": "object",
                        "description": "Query object with schema, dimensions, measures, filters, order, limit. Schema values: all, activity, application, countermeasure, integration, library, project_survey_answers, training, user, trend_application, trend_task, trend_project"
                    },
                    "chart_meta": {
                        "type": "object",
                        "description": "Chart metadata like columnOrder (optional)"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["D", "T"],
                        "description": "Report type: D=Default/Standard, T=Trend (optional, defaults to D)"
                    }
                },
                "required": ["title", "chart", "query"]
            }
        ),
        Tool(
            name="execute_cube_query",
            description="Execute a Cube API query to get report data. See https://docs.sdelements.com/master/cubeapi/ for query format details",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "object",
                        "description": "Cube query object with schema, dimensions, measures, filters, order, limit. See Cube API docs for details."
                    }
                },
                "required": ["query"]
            }
        ),
        
        # Generic API tool
        Tool(
            name="api_request",
            description="Make a custom API request to any SD Elements endpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                        "description": "HTTP method for the request"
                    },
                    "endpoint": {
                        "type": "string",
                        "description": "API endpoint (e.g., 'projects/', 'applications/123/')"
                    },
                    "params": {
                        "type": "object",
                        "description": "URL parameters as key-value pairs"
                    },
                    "data": {
                        "type": "object",
                        "description": "Request body data as key-value pairs"
                    }
                },
                "required": ["method", "endpoint"]
            }
        ),
        
        # Test connection tool
        Tool(
            name="test_connection",
            description="Test the connection to SD Elements API",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for SD Elements API operations"""
    global api_client
    
    try:
        # Initialize API client if not already done
        if api_client is None:
            api_client = init_api_client()
        
        # Helper function to build params
        def build_params(args: Dict[str, Any]) -> Dict[str, Any]:
            params = {}
            if "page_size" in args:
                params["page_size"] = args["page_size"]
            if "include" in args:
                params["include"] = args["include"]
            if "expand" in args:
                params["expand"] = args["expand"]
            return params
        
        # Project tools
        if name == "list_projects":
            params = build_params(arguments)
            result = api_client.list_projects(params)
            
        elif name == "get_project":
            project_id = arguments["project_id"]
            params = build_params(arguments)
            result = api_client.get_project(project_id, params)
            
        elif name == "create_project":
            data = {k: v for k, v in arguments.items() if k in ["name", "description", "application_id", "phase_id"]}
            # Transform application_id to application for API compatibility
            if "application_id" in data:
                data["application"] = data.pop("application_id")
            result = api_client.create_project(data)
            
        elif name == "update_project":
            project_id = arguments.pop("project_id")
            data = arguments  # Remaining arguments are the update data
            result = api_client.update_project(project_id, data)
            
        elif name == "delete_project":
            project_id = arguments["project_id"]
            result = api_client.delete_project(project_id)
            
        elif name == "get_project_survey":
            project_id = arguments["project_id"]
            result = api_client.get_project_survey(project_id)
            
        elif name == "update_project_survey":
            project_id = arguments["project_id"]
            data = {
                "answers": arguments["answers"]
            }
            if "survey_complete" in arguments:
                data["survey_complete"] = arguments["survey_complete"]
            result = api_client.update_project_survey(project_id, data)
            
        elif name == "find_survey_answers":
            project_id = arguments["project_id"]
            search_texts = arguments["search_texts"]
            result = api_client.find_survey_answers_by_text(project_id, search_texts)
            
        elif name == "set_project_survey_by_text":
            project_id = arguments["project_id"]
            answer_texts = arguments["answer_texts"]
            
            # Find answer IDs for the provided texts
            search_results = api_client.find_survey_answers_by_text(project_id, answer_texts)
            
            # Extract the IDs and check for errors
            answer_ids = []
            not_found = []
            for text, info in search_results.items():
                if info.get('id'):
                    answer_ids.append(info['id'])
                else:
                    not_found.append(text)
            
            if not_found:
                result = {
                    "error": f"Could not find answers for: {', '.join(not_found)}",
                    "search_results": search_results,
                    "suggestion": "Use find_survey_answers to see available options or get_project_survey to see all questions and answers"
                }
            else:
                # Update the survey with found IDs
                data = {"answers": answer_ids}
                if "survey_complete" in arguments:
                    data["survey_complete"] = arguments["survey_complete"]
                
                update_result = api_client.update_project_survey(project_id, data)
                result = {
                    "success": True,
                    "matched_answers": search_results,
                    "answer_ids_used": answer_ids,
                    "update_result": update_result
                }
            
        elif name == "remove_survey_answers_by_text":
            project_id = arguments["project_id"]
            answer_texts_to_remove = arguments["answer_texts_to_remove"]
            
            # Get current survey
            current_survey = api_client.get_project_survey(project_id)
            current_answer_ids = current_survey.get('answers', [])
            
            # Find answer IDs for the texts to remove
            search_results = api_client.find_survey_answers_by_text(project_id, answer_texts_to_remove)
            
            # Collect IDs to remove
            ids_to_remove = []
            not_found = []
            for text, info in search_results.items():
                if info.get('id'):
                    ids_to_remove.append(info['id'])
                else:
                    not_found.append(text)
            
            # Remove the IDs from current answers
            new_answer_ids = [aid for aid in current_answer_ids if aid not in ids_to_remove]
            
            if not_found:
                result = {
                    "warning": f"Could not find these answers to remove: {', '.join(not_found)}",
                    "search_results": search_results
                }
            
            # Update the survey with remaining answers
            data = {"answers": new_answer_ids}
            update_result = api_client.update_project_survey(project_id, data)
            
            result = {
                "success": True,
                "removed_answers": {text: info for text, info in search_results.items() if info.get('id')},
                "ids_removed": ids_to_remove,
                "not_found": not_found,
                "remaining_answer_count": len(new_answer_ids),
                "update_result": update_result
            }
            
        elif name == "add_survey_answers_by_text":
            project_id = arguments["project_id"]
            answer_texts_to_add = arguments["answer_texts_to_add"]
            
            # Use the new implementation with automatic dependency resolution
            result = api_client.add_survey_answers_by_text(
                project_id, 
                answer_texts_to_add,
                fuzzy_threshold=0.75,
                auto_resolve_dependencies=True
            )
            
        elif name == "get_current_survey_answers":
            project_id = arguments["project_id"]
            output_format = arguments.get("format", "summary")
            
            # Get the survey
            survey = api_client.get_project_survey(project_id)
            current_answer_ids = survey.get('answers', [])
            
            if not current_answer_ids:
                result = {
                    "project_id": project_id,
                    "message": "No answers are currently assigned to this survey",
                    "answer_count": 0
                }
            else:
                # Build a map of answer IDs to their details
                answer_details = {}
                
                for section in survey.get('sections', []):
                    section_title = section.get('title', 'Untitled Section')
                    for question in section.get('questions', []):
                        question_text = question.get('text', 'Untitled Question')
                        for answer in question.get('answers', []):
                            answer_id = answer.get('id')
                            if answer_id in current_answer_ids:
                                answer_details[answer_id] = {
                                    'text': answer.get('text', 'N/A'),
                                    'question': question_text,
                                    'section': section_title,
                                    'question_id': question.get('id')
                                }
                
                if output_format == "summary":
                    result = {
                        "project_id": project_id,
                        "answer_count": len(current_answer_ids),
                        "answers": [details['text'] for details in answer_details.values()],
                        "answer_ids": current_answer_ids
                    }
                    
                elif output_format == "detailed":
                    result = {
                        "project_id": project_id,
                        "answer_count": len(current_answer_ids),
                        "answers": [
                            {
                                "text": details['text'],
                                "question": details['question'],
                                "answer_id": aid
                            }
                            for aid, details in answer_details.items()
                        ]
                    }
                    
                elif output_format == "grouped":
                    # Group by section
                    grouped = {}
                    for aid, details in answer_details.items():
                        section = details['section']
                        if section not in grouped:
                            grouped[section] = []
                        grouped[section].append({
                            "question": details['question'],
                            "answer": details['text']
                        })
                    
                    result = {
                        "project_id": project_id,
                        "answer_count": len(current_answer_ids),
                        "sections": grouped
                    }
        
        elif name == "commit_survey_draft":
            project_id = arguments["project_id"]
            result = api_client.commit_survey_draft(project_id)
        
        elif name == "create_project_from_code":
            """
            End-to-end workflow to create an SD Elements project.
            
            This tool performs the following steps:
            1. Creates or uses an existing application
            2. Creates a new project in the application
            3. Gets the project survey structure with all available questions and answers
            4. Checks the survey draft state to see if answers are selected
            5. Commits the survey draft only if answers are selected (to publish and generate countermeasures)
            
            IMPORTANT: This tool does NOT automatically set survey answers.
            The AI client should:
            1. Review the returned survey structure (all available questions and answers)
            2. Use its AI knowledge along with the optional code_context to determine appropriate survey answers
            3. Call add_survey_answers_by_text or set_project_survey_by_text to set answers based on code_context
            4. The survey draft will be automatically committed only if answers are already selected
            
            This approach allows the AI to make intelligent decisions by reviewing all available
            survey options rather than relying on hardcoded pattern matching.
            
            Note: The survey draft is only committed if answers are already selected (e.g., from
            application template or previous API calls). If no answers are selected, the AI should
            set them first using the survey management tools, then commit the draft.
            """
            try:
                # Optional context provided by user (for AI reference only, not analyzed)
                code_context = arguments.get("code_context", "")
                
                # Step 1: Create or get application
                # Applications are containers for related projects in SD Elements
                application_id = arguments.get("application_id")
                app_result = None
                application_was_existing = False  # Track if we used an existing application
                
                if not application_id:
                    # No application ID provided, so we need to find or create an application
                    application_name = arguments.get("application_name")
                    if application_name:
                        # First, check if an application with this name already exists
                        existing_app = None
                        try:
                            # List all applications and search for one with matching name
                            apps_response = api_client.list_applications({"page_size": 1000})  # Get a large page size to find existing apps
                            apps = apps_response.get("results", [])
                            
                            # Search for application with matching name (case-insensitive)
                            for app in apps:
                                if app.get("name", "").strip().lower() == application_name.strip().lower():
                                    existing_app = app
                                    break
                        except Exception as list_error:
                            # If listing fails, we'll proceed to create a new application
                            print(f"Warning: Could not list existing applications: {list_error}", file=sys.stderr)
                        
                        if existing_app:
                            # Use existing application
                            application_id = existing_app.get("id")
                            app_result = existing_app
                            application_was_existing = True
                            print(f"Using existing application '{application_name}' (ID: {application_id})", file=sys.stderr)
                        else:
                            # Create new application with the provided name
                            app_data = {"name": application_name}
                            # Add description if provided
                            if "application_description" in arguments:
                                app_data["description"] = arguments["application_description"]
                            
                            # Create the application via API
                            app_result = api_client.create_application(app_data)
                            application_id = app_result.get("id")
                            print(f"Created new application '{application_name}' (ID: {application_id})", file=sys.stderr)
                    else:
                        # Neither application_id nor application_name provided
                        result = {
                            "error": "Either application_id or application_name must be provided"
                        }
                        return [TextContent(type="text", text=json.dumps(result, indent=2))]
                else:
                    # If application_id was provided, we use the existing application
                    application_was_existing = True
                
                # Step 2: Create project in the application
                # Projects represent individual software components or services
                project_data = {
                    "name": arguments["project_name"],  # Required parameter
                    "application": application_id  # Link to the application
                }
                # Add project description if provided
                if "project_description" in arguments:
                    project_data["description"] = arguments["project_description"]
                
                # Create the project via API
                project_result = api_client.create_project(project_data)
                project_id = project_result.get("id")
                
                # Step 3: Get the project survey structure with all available questions and answers
                # This provides the AI with all possible survey options to choose from
                survey_structure = api_client.get_project_survey(project_id)
                
                # Extract a summary of available answers for easier AI review
                # The AI can use this to understand what options are available
                available_answers_summary = []
                for section in survey_structure.get('sections', []):
                    section_title = section.get('title', 'Untitled Section')
                    for question in section.get('questions', []):
                        question_text = question.get('text', 'Untitled Question')
                        for answer in question.get('answers', []):
                            available_answers_summary.append({
                                'id': answer.get('id'),
                                'text': answer.get('text', ''),
                                'question': question_text,
                                'section': section_title
                            })
                
                # Step 4: Check survey draft state to see if answers are selected
                # Get the survey draft to check what answers are currently selected
                draft_state = None
                selected_answers_count = 0
                try:
                    draft_state = api_client.get(f'projects/{project_id}/survey/draft/')
                    # Count selected answers in the draft
                    selected_answers = [a for a in draft_state.get('answers', []) if a.get('selected', False)]
                    selected_answers_count = len(selected_answers)
                except Exception as draft_error:
                    # If we can't get draft state, we'll still try to commit
                    draft_state = {"error": str(draft_error)}
                
                # Step 5: Commit the survey draft to publish it and generate countermeasures
                # Only commit if there are selected answers, otherwise inform the user
                commit_result = None
                commit_success = False
                commit_skipped = False
                
                if selected_answers_count > 0:
                    # Answers are selected, proceed with commit
                    try:
                        commit_result = api_client.commit_survey_draft(project_id)
                        commit_success = True
                    except Exception as commit_error:
                        # If commit fails, log it but don't fail the entire operation
                        commit_result = {
                            "error": str(commit_error),
                            "note": "Survey draft commit failed, but project was created successfully"
                        }
                else:
                    # No answers selected, skip commit and inform user
                    commit_skipped = True
                    commit_result = {
                        "note": "Survey draft not committed because no answers are selected",
                        "action_required": "Use add_survey_answers_by_text or set_project_survey_by_text to set answers, then call commit_survey_draft"
                    }
                
                # Build comprehensive result object with all workflow details
                result = {
                    "success": True,
                    # Project context (optional, provided by user for AI reference)
                    "project_context": code_context if code_context else None,
                    # Application information
                    "application": {
                        "id": application_id,
                        "name": app_result.get("name") if app_result else arguments.get("application_name", "unknown"),
                        "was_existing": application_was_existing
                    },
                    # Project information
                    "project": {
                        "id": project_id,
                        "name": project_result.get("name"),
                        "url": project_result.get("url")  # Direct link to project in SD Elements
                    },
                    # Survey structure: All available questions and answers
                    "survey_structure": {
                        "note": "This contains all available survey questions and answers. Review these options and use your AI knowledge to determine which answers are appropriate for this project.",
                        "total_questions": len([q for s in survey_structure.get('sections', []) for q in s.get('questions', [])]),
                        "total_answers": len(available_answers_summary),
                        "available_answers": available_answers_summary[:100],  # Limit to first 100 for readability
                        "full_survey": survey_structure  # Complete survey structure if needed
                    },
                    # Survey draft state
                    "survey_draft_state": {
                        "selected_answers_count": selected_answers_count,
                        "has_answers": selected_answers_count > 0,
                        "draft_available": draft_state is not None and "error" not in draft_state
                    },
                    # Survey draft commit status
                    "survey_committed": commit_success,
                    "survey_commit_skipped": commit_skipped,
                    "survey_commit_result": commit_result,
                    # Next steps for AI client
                    "next_steps": {
                        "step_1": f"Survey draft checked: {selected_answers_count} answer(s) currently selected",
                        "step_2": f"Survey draft has been {'committed successfully' if commit_success else 'skipped (no answers)' if commit_skipped else 'attempted to commit'}",
                        "step_3": f"Countermeasures will be {'generated' if commit_success else 'generated after answers are set and draft is committed' if commit_skipped else 'generated after manual commit'}",
                        "step_4": "If no answers were set, use add_survey_answers_by_text or set_project_survey_by_text to set answers based on code_context, then call commit_survey_draft"
                    }
                }
            except Exception as e:
                # Handle any errors that occur during the workflow
                # Return error information for debugging
                result = {
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            
        # Application tools
        elif name == "list_applications":
            params = build_params(arguments)
            result = api_client.list_applications(params)
            
        elif name == "get_application":
            app_id = arguments["application_id"]
            params = build_params(arguments)
            result = api_client.get_application(app_id, params)
            
        elif name == "create_application":
            data = {k: v for k, v in arguments.items() if k in ["name", "description", "business_unit_id"]}
            # Transform business_unit_id to business_unit for API compatibility
            if "business_unit_id" in data:
                data["business_unit"] = data.pop("business_unit_id")
            result = api_client.create_application(data)
            
        elif name == "update_application":
            app_id = arguments.pop("application_id")
            data = arguments  # Remaining arguments are the update data
            result = api_client.update_application(app_id, data)
            
        # Countermeasure tools
        elif name == "list_countermeasures":
            project_id = arguments["project_id"]
            params = {}
            if "status" in arguments:
                params["status"] = arguments["status"]
            if "page_size" in arguments:
                params["page_size"] = arguments["page_size"]
            result = api_client.list_countermeasures(project_id, params)
            
        elif name == "get_countermeasure":
            project_id = arguments["project_id"]
            countermeasure_id = arguments["countermeasure_id"]
            params = {}
            # Default risk_relevant to True if not specified
            risk_relevant = arguments.get("risk_relevant", True)
            params["risk_relevant"] = risk_relevant
            result = api_client.get_countermeasure(project_id, countermeasure_id, params)
            
        elif name == "update_countermeasure":
            project_id = arguments.pop("project_id")
            countermeasure_id = arguments.pop("countermeasure_id")
            data = arguments.copy()  # Remaining arguments are the update data
            
            # Convert notes to status_note for tasks endpoint
            if "notes" in data:
                data["status_note"] = data.pop("notes")
            
            result = api_client.update_countermeasure(project_id, countermeasure_id, data)
            
        # User tools
        elif name == "list_users":
            params = {}
            if "page_size" in arguments:
                params["page_size"] = arguments["page_size"]
            if "active" in arguments:
                params["is_active"] = arguments["active"]
            result = api_client.list_users(params)
            
        elif name == "get_user":
            user_id = arguments["user_id"]
            result = api_client.get_user(user_id)
            
        elif name == "get_current_user":
            result = api_client.get_current_user()
            
        # Business Unit tools
        elif name == "list_business_units":
            params = build_params(arguments)
            result = api_client.list_business_units(params)
            
        elif name == "get_business_unit":
            bu_id = arguments["business_unit_id"]
            result = api_client.get_business_unit(bu_id)
            
        # Repository Scanning tools
        elif name == "list_scan_connections":
            result = api_client.list_team_onboarding_connections()
            
        elif name == "scan_repository":
            project_id = arguments["project_id"]
            connection_id = arguments["connection_id"]
            repository_url = arguments["repository_url"]
            data = {
                "project": project_id,
                "connection": connection_id,
                "repository_url": repository_url
            }
            result = api_client.create_team_onboarding_scan(data)
            
        elif name == "get_scan_status":
            scan_id = arguments["scan_id"]
            result = api_client.get_team_onboarding_scan(scan_id)
            
        elif name == "list_scans":
            params = {}
            if "project_id" in arguments:
                params["project"] = arguments["project_id"]
            result = api_client.list_team_onboarding_scans(params)
            
        # Project Diagrams tools
        elif name == "list_project_diagrams":
            project_id = arguments["project_id"]
            result = api_client.list_project_diagrams(project_id)
            
        elif name == "get_diagram":
            diagram_id = arguments["diagram_id"]
            result = api_client.get_project_diagram(diagram_id)
            
        elif name == "create_diagram":
            data = {
                "project": arguments["project_id"],
                "name": arguments["name"]
            }
            if "diagram_data" in arguments:
                data["diagram_data"] = arguments["diagram_data"]
            result = api_client.create_project_diagram(data)
            
        elif name == "update_diagram":
            diagram_id = arguments.pop("diagram_id")
            data = arguments  # Remaining arguments are the update data
            result = api_client.update_project_diagram(diagram_id, data)
            
        elif name == "delete_diagram":
            diagram_id = arguments["diagram_id"]
            result = api_client.delete_project_diagram(diagram_id)
            
        # Advanced Reports tools
        elif name == "list_advanced_reports":
            result = api_client.list_advanced_reports()
            
        elif name == "get_advanced_report":
            report_id = arguments["report_id"]
            result = api_client.get_advanced_report(report_id)
            
        elif name == "run_advanced_report":
            report_id = arguments["report_id"]
            params = {}
            if "format" in arguments:
                params["format"] = arguments["format"]
            result = api_client.run_advanced_report(report_id, params)
            
        elif name == "create_advanced_report":
            data = {
                "title": arguments["title"],
                "chart": arguments["chart"],
                "query": arguments["query"]
            }
            if "description" in arguments:
                data["description"] = arguments["description"]
            if "chart_meta" in arguments:
                data["chart_meta"] = arguments["chart_meta"]
            if "type" in arguments:
                data["type"] = arguments["type"]
            result = api_client.create_advanced_report(data)
            
        elif name == "execute_cube_query":
            query = arguments["query"]
            result = api_client.execute_cube_query(query)
            
        # Generic API tool
        elif name == "api_request":
            method = arguments["method"]
            endpoint = arguments["endpoint"]
            params = arguments.get("params")
            data = arguments.get("data")
            result = api_client.api_request(method, endpoint, params, data)
            
        # Test connection tool
        elif name == "test_connection":
            success = api_client.test_connection()
            result = {
                "connection_successful": success,
                "host": api_client.host,
                "message": "Connection successful" if success else "Connection failed"
            }
            
        else:
            raise ToolError(f"Unknown tool: {name}")
        
        # Format the response
        response_text = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        error_message = format_error_response(e)
        return [TextContent(type="text", text=error_message)]


@server.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts"""
    return [
        Prompt(
            name="project_summary",
            description="Generate a summary of projects in SD Elements",
        ),
        Prompt(
            name="security_status",
            description="Get security status overview for applications and projects",
        ),
        Prompt(
            name="set_project_survey",
            description="Set a project survey using natural language description",
            arguments=[
                {
                    "name": "project_id",
                    "description": "The ID of the project",
                    "required": True
                }
            ]
        ),
        Prompt(
            name="generate_report",
            description="Generate and analyze an advanced report using natural language",
        ),
        Prompt(
            name="create_diagram",
            description="Create a threat model diagram from natural language description",
            arguments=[
                {
                    "name": "project_id",
                    "description": "The ID of the project",
                    "required": True
                }
            ]
        )
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: Dict[str, str] | None = None) -> GetPromptResult:
    """Get a specific prompt"""
    if name == "project_summary":
        return GetPromptResult(
            description="Generate a summary of projects in SD Elements",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="Please provide a summary of all projects in SD Elements, including their status, applications, and key security metrics."
                    )
                )
            ]
        )
    elif name == "security_status":
        return GetPromptResult(
            description="Get security status overview",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="Please provide an overview of the security status across all applications and projects, highlighting any critical countermeasures that need attention."
                    )
                )
            ]
        )
    elif name == "set_project_survey":
        project_id = arguments.get("project_id") if arguments else None
        if not project_id:
            raise ValueError("project_id argument is required for set_project_survey prompt")
        
        return GetPromptResult(
            description="Set a project survey using natural language",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""I want to set the survey for project {project_id} using natural language.

Please follow these steps:
1. Ask me to describe what I want to set in the survey (e.g., "Java web application on AWS")
2. Use the set_project_survey_by_text tool with the answer texts I provide (e.g., ['Java', 'Web Application', 'AWS'])
3. The tool will automatically find matching answer IDs and update the survey

You can use answer text directly - no need to know that "Java" is "A1" or similar IDs. Just use the natural language terms like 'Java', 'Python', 'Web Application', 'Mobile App', 'AWS', etc."""
                    )
                )
            ]
        )
    elif name == "generate_report":
        return GetPromptResult(
            description="Generate and analyze an advanced report",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""I want to generate an advanced report and get insights in natural language.

Please follow these steps:
1. Ask me what I want to know (e.g., "Show me security tasks status across projects", "List completed countermeasures this month", "Report on application risk levels")
2. First check existing reports with list_advanced_reports to see if there's already a report that matches
3. If a matching report exists, use run_advanced_report to execute it
4. If no matching report exists, use api_request to query the data directly from relevant endpoints
5. Analyze the data and present it to me in clear, natural language with:
   - Key findings and insights
   - Trends or patterns
   - Actionable recommendations if applicable
   - Summary statistics

Examples of what I might ask for:
- "Show me all open security tasks by project"
- "What's the status of countermeasures across my applications?"
- "List projects with high risk levels"
- "Give me a summary of tasks completed this month"
- "Which applications have the most pending security work?"

Present the results as a narrative summary, not just raw data."""
                    )
                )
            ]
        )
    elif name == "create_diagram":
        project_id = arguments.get("project_id") if arguments else None
        if not project_id:
            raise ValueError("project_id argument is required for create_diagram prompt")
        
        return GetPromptResult(
            description="Create a threat model diagram from natural language",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""I want to create a threat model diagram for project {project_id} using natural language.

Please follow these steps:
1. Ask me to describe the application architecture in natural language
2. Use the create_diagram_from_description tool with my description
3. The tool will:
   - Parse the description to identify components (databases, servers, APIs, etc.)
   - Create a diagram structure with nodes and connections
   - Attempt to create the diagram in SD Elements

Examples of architecture descriptions:
- "Web application with React frontend, Node.js API backend, PostgreSQL database, and Redis cache"
- "Mobile iOS app connecting to REST API, with MySQL database and S3 file storage on AWS"
- "Microservices architecture: API Gateway, Authentication service, User service, Order service, each with their own database"
- "Three-tier: Load balancer -> Web servers -> Application servers -> Database cluster"

Common components I can understand:
- Frontend: Web app, React, Angular, Vue, Mobile app, iOS, Android
- Backend: API, REST API, Node.js, Python, Java, Application server
- Databases: PostgreSQL, MySQL, MongoDB, Redis, SQL Server
- Infrastructure: Load balancer, Cache, CDN, Message queue
- Cloud: AWS, Azure, S3, Lambda, EC2
- Security: Authentication, Authorization, Firewall, WAF

After creating the diagram, you can:
- View it with get_diagram
- Update it with update_diagram if adjustments are needed
- The diagram will be visible in SD Elements UI for further refinement

You can also import existing diagrams using import_diagram tool with supported formats:
- Microsoft Threat Modeling Tool (.tm7 exported as JSON)
- diagrams.net (draw.io) (.drawio or exported JSON)
- SD Elements JSON format

In Cursor, you can reference local files directly:
Examples:
- "Import the threat model from ./diagrams/app-threat-model.json"
- "Read ~/Documents/architecture.drawio and import it to this project"
- "Import the diagram file at /path/to/diagram.json"

I'll read the file and import it for you automatically."""
                    )
                )
            ]
        )
    else:
        raise ValueError(f"Unknown prompt: {name}")


async def main():
    """Main entry point for the MCP server"""
    # Initialize API client
    global api_client
    try:
        api_client = init_api_client()
        print("SD Elements MCP Server starting...", file=sys.stderr)
        print(f"Host: {os.getenv('SDE_HOST')}", file=sys.stderr)
        print("Configuration validated successfully", file=sys.stderr)
        
        # Load library answers cache on startup
        print("Loading library answers cache...", file=sys.stderr)
        api_client.load_library_answers()
        print("Library answers cache loaded successfully", file=sys.stderr)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("Please set SDE_HOST and SDE_API_KEY environment variables", file=sys.stderr)
        sys.exit(1)
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main()) 