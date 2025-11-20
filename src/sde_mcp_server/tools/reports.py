"""Advanced report tools"""
import json
from typing import Any, Dict, Optional, Union

from fastmcp import Context

from ..server import mcp, api_client, init_api_client


@mcp.tool()
async def list_advanced_reports(ctx: Context) -> str:
    """List all advanced reports"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    result = api_client.list_advanced_reports()
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_advanced_report(ctx: Context, report_id: int) -> str:
    """Get details of a specific advanced report"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    result = api_client.get_advanced_report(report_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def update_advanced_report(
    ctx: Context,
    report_id: int,
    title: Optional[str] = None,
    chart: Optional[str] = None,
    query: Optional[Union[str, Dict[str, Any]]] = None,
    description: Optional[str] = None,
    chart_meta: Optional[Dict[str, Any]] = None,
    type: Optional[str] = None,
) -> str:
    """Update an existing advanced report. Provide only the fields you want to update."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    data = {}
    if title is not None:
        data["title"] = title
    if chart is not None:
        data["chart"] = chart
    if query is not None:
        # Parse query if it's a string
        if isinstance(query, str):
            try:
                query = json.loads(query)
            except json.JSONDecodeError:
                return json.dumps({"error": "Invalid JSON in query parameter. Query must be valid JSON or a dictionary."}, indent=2)
        data["query"] = query
    if description is not None:
        data["description"] = description
    if chart_meta is not None:
        data["chart_meta"] = chart_meta
    if type is not None:
        data["type"] = type
    
    if not data:
        return json.dumps({"error": "No update data provided. Specify at least one field to update."}, indent=2)
    
    result = api_client.update_advanced_report(report_id, data)
    return json.dumps(result, indent=2)


@mcp.tool()
async def run_advanced_report(ctx: Context, report_id: int, format: Optional[str] = None) -> str:
    """Run an advanced report"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    params = {}
    if format is not None:
        params["format"] = format
    result = api_client.run_advanced_report(report_id, params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def create_advanced_report(
    ctx: Context,
    title: str,
    chart: str,
    query: Union[str, Dict[str, Any]],
    description: Optional[str] = None,
    chart_meta: Optional[Dict[str, Any]] = None,
    type: Optional[str] = None,
) -> str:
    """Create a new advanced report. The query parameter can be a JSON string or a dictionary with schema, dimensions, measures, filters, order, and limit."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    # Parse query if it's a string
    if isinstance(query, str):
        try:
            query = json.loads(query)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON in query parameter. Query must be valid JSON or a dictionary."}, indent=2)
    
    data = {"title": title, "chart": chart, "query": query}
    if description:
        data["description"] = description
    if chart_meta is not None:
        data["chart_meta"] = chart_meta
    if type is not None:
        data["type"] = type
    result = api_client.create_advanced_report(data)
    return json.dumps(result, indent=2)


@mcp.tool()
async def execute_cube_query(ctx: Context, query: Union[str, Dict[str, Any]]) -> str:
    """Execute a Cube API query for advanced analytics. The query parameter can be a JSON string or a dictionary.
    
    Query structure (see https://docs.sdelements.com/master/cubeapi/):
    - schema: Required. One of: activity, application, countermeasure, integration, library, project_survey_answers, training, trend_application, trend_projects, trend_tasks, user
    - dimensions: Required. Array like ["Application.name", "Project.id"]
    - measures: Required. Array like ["Project.count", "Task.completeCount"]
    - filters: Optional. Array of objects with member, operator (equals/contains/gt/etc), values
    - order: Optional. 2D array like [["Application.name", "asc"], ["Project.count", "desc"]]
    - limit: Optional. Number to limit results
    - time_dimensions: Optional. For Trend Reports only (trend_application, trend_projects, trend_tasks)
    
    Example: {"schema": "application", "dimensions": ["Application.name"], "measures": ["Project.count"], "limit": 10}"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    # Parse query if it's a string
    if isinstance(query, str):
        try:
            query = json.loads(query)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON in query parameter. Query must be valid JSON or a dictionary."}, indent=2)
    
    # Basic validation
    if not isinstance(query, dict):
        return json.dumps({"error": "Query must be a dictionary/object with schema, dimensions, and measures."}, indent=2)
    
    if "schema" not in query:
        return json.dumps({"error": "Query must include 'schema' field (e.g., 'application', 'countermeasure', 'user')"}, indent=2)
    
    if "dimensions" not in query and "measures" not in query:
        return json.dumps({"error": "Query must include at least one of 'dimensions' or 'measures'"}, indent=2)
    
    result = api_client.execute_cube_query(query)
    return json.dumps(result, indent=2)

