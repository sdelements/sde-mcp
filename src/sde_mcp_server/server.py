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
                    "countermeasure_id": {
                        "type": "integer",
                        "description": "The ID of the countermeasure to retrieve",
                        "minimum": 1
                    }
                },
                "required": ["countermeasure_id"]
            }
        ),
        Tool(
            name="update_countermeasure",
            description="Update a countermeasure status or details",
            inputSchema={
                "type": "object",
                "properties": {
                    "countermeasure_id": {
                        "type": "integer",
                        "description": "The ID of the countermeasure to update",
                        "minimum": 1
                    },
                    "status": {
                        "type": "string",
                        "description": "New status for the countermeasure"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes about the countermeasure"
                    }
                },
                "required": ["countermeasure_id"]
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
        Tool(
            name="create_diagram_from_description",
            description="Create a project diagram from a natural language description of the application architecture",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "description": {
                        "type": "string",
                        "description": "Natural language description of the architecture (e.g., 'Web app with React frontend, Node.js backend, PostgreSQL database, and Redis cache, all on AWS')"
                    },
                    "diagram_name": {
                        "type": "string",
                        "description": "Name for the diagram (optional, defaults to 'System Architecture')"
                    }
                },
                "required": ["project_id", "description"]
            }
        ),
        Tool(
            name="import_diagram",
            description="Import a diagram from a file or diagram data. Supports Microsoft Threat Modeling Tool, diagrams.net (draw.io), and JSON formats.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project",
                        "minimum": 1
                    },
                    "diagram_data": {
                        "type": "object",
                        "description": "Diagram data in JSON format (from Microsoft Threat Modeling Tool, diagrams.net, or SD Elements JSON schema)"
                    },
                    "diagram_name": {
                        "type": "string",
                        "description": "Name for the imported diagram"
                    },
                    "source_format": {
                        "type": "string",
                        "enum": ["microsoft_threat_modeling", "diagrams_net", "drawio", "json"],
                        "description": "Source format of the diagram (optional, for better parsing)"
                    }
                },
                "required": ["project_id", "diagram_data", "diagram_name"]
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
            name="generate_report_from_description",
            description="Generate and execute an advanced report based on a natural language description. This is the easiest way to get report data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Natural language description of what you want to report on (e.g., 'Show me all open security tasks by project', 'List countermeasures completed this month')"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "csv", "summary"],
                        "description": "Output format (optional, defaults to 'summary' which provides a natural language summary)"
                    }
                },
                "required": ["description"]
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
            countermeasure_id = arguments["countermeasure_id"]
            result = api_client.get_countermeasure(countermeasure_id)
            
        elif name == "update_countermeasure":
            countermeasure_id = arguments.pop("countermeasure_id")
            data = arguments  # Remaining arguments are the update data
            result = api_client.update_countermeasure(countermeasure_id, data)
            
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
            
        elif name == "create_diagram_from_description":
            project_id = arguments["project_id"]
            description = arguments["description"]
            diagram_name = arguments.get("diagram_name", "System Architecture")
            
            # Parse the description to identify components
            description_lower = description.lower()
            
            # Common component mappings
            component_keywords = {
                'web app': 'web_application',
                'frontend': 'web_application',
                'backend': 'application_server',
                'api': 'api_server',
                'database': 'database',
                'postgres': 'postgresql',
                'mysql': 'mysql',
                'mongodb': 'mongodb',
                'redis': 'redis_cache',
                'cache': 'cache',
                'load balancer': 'load_balancer',
                's3': 'amazon_s3',
                'aws': 'cloud_storage',
                'azure': 'cloud_storage',
                'authentication': 'authentication_service',
                'auth': 'authentication_service',
                'mobile': 'mobile_app',
            }
            
            # Find matching components
            identified_components = []
            for keyword, component_type in component_keywords.items():
                if keyword in description_lower:
                    identified_components.append({
                        'type': component_type,
                        'keyword': keyword
                    })
            
            # Create a simple diagram structure
            # Note: This is a simplified structure - actual SD Elements diagrams may require specific schema
            diagram_data = {
                'nodes': [],
                'edges': [],
                'metadata': {
                    'generated_from': 'natural_language',
                    'description': description
                }
            }
            
            # Add nodes for each identified component
            for i, comp in enumerate(identified_components):
                diagram_data['nodes'].append({
                    'id': f'node_{i}',
                    'type': comp['type'],
                    'label': comp['keyword'].title(),
                    'position': {'x': i * 150, 'y': 100}
                })
            
            # Create basic connections (simplified logic)
            for i in range(len(diagram_data['nodes']) - 1):
                diagram_data['edges'].append({
                    'from': f'node_{i}',
                    'to': f'node_{i+1}',
                    'type': 'data_flow'
                })
            
            # Create the diagram
            data = {
                "project": project_id,
                "name": diagram_name,
                "diagram_data": diagram_data
            }
            
            result = {
                "diagram_created": True,
                "identified_components": identified_components,
                "description_parsed": description,
                "note": "Diagram structure created from natural language. You may need to adjust it in SD Elements UI for your specific schema.",
                "creation_data": data
            }
            
            # Attempt to create the diagram
            try:
                creation_result = api_client.create_project_diagram(data)
                result["creation_result"] = creation_result
                result["success"] = True
            except Exception as e:
                result["success"] = False
                result["error"] = str(e)
                result["suggestion"] = "The diagram structure may need adjustment. Use get_project_survey to understand the project's components, then create_diagram with proper diagram_data format."
            
        elif name == "import_diagram":
            project_id = arguments["project_id"]
            diagram_data = arguments["diagram_data"]
            diagram_name = arguments["diagram_name"]
            source_format = arguments.get("source_format", "json")
            
            # Transform the diagram data based on source format
            transformed_data = diagram_data
            
            if source_format in ["diagrams_net", "drawio"]:
                # Parse diagrams.net/draw.io format
                result_note = "Parsed diagrams.net/draw.io format"
                # Note: Actual transformation would depend on the specific schema
                # This is a placeholder for the transformation logic
                
            elif source_format == "microsoft_threat_modeling":
                # Parse Microsoft Threat Modeling Tool format
                result_note = "Parsed Microsoft Threat Modeling Tool format"
                # Note: Actual transformation would depend on the specific schema
                
            else:
                # Assume it's already in SD Elements JSON format
                result_note = "Using provided JSON format"
            
            # Create the diagram
            data = {
                "project": project_id,
                "name": diagram_name,
                "diagram_data": transformed_data
            }
            
            try:
                creation_result = api_client.create_project_diagram(data)
                result = {
                    "success": True,
                    "message": f"Diagram '{diagram_name}' imported successfully",
                    "source_format": source_format,
                    "note": result_note,
                    "diagram": creation_result
                }
            except Exception as e:
                result = {
                    "success": False,
                    "error": str(e),
                    "source_format": source_format,
                    "suggestion": "The diagram format may not be compatible. Supported formats: Microsoft Threat Modeling Tool, diagrams.net (draw.io), and SD Elements JSON. You may need to export your diagram in a compatible format first."
                }
            
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
            
        elif name == "generate_report_from_description":
            description = arguments["description"]
            output_format = arguments.get("format", "summary")
            
            # This is a placeholder that tells the AI to use existing reports or the API
            # The actual implementation would require mapping natural language to report configs
            result = {
                "note": "This tool helps generate reports from natural language",
                "description": description,
                "format": output_format,
                "instructions": "Use list_advanced_reports to find an existing report that matches, or use execute_cube_query to run a custom query. For a natural language summary, describe the key findings from the data."
            }
            
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