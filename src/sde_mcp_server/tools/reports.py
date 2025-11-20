"""Advanced report tools"""
import json
from typing import Any, Dict, Optional, Union

from fastmcp import Context
from pydantic import BaseModel, field_validator

from ..server import mcp, api_client, init_api_client


class CubeQuery(BaseModel):
    """Cube API query structure"""
    schema: str  # Field name for Cube API
    dimensions: list[str]
    measures: list[str]
    filters: Optional[list[Dict[str, Any]]] = None
    order: Optional[list[list[str]]] = None
    limit: Optional[int] = None
    time_dimensions: Optional[list[Dict[str, Any]]] = None
    
    @classmethod
    def parse_obj_or_str(cls, obj: Union[str, Dict[str, Any]]) -> "CubeQuery":
        """Parse from either a dict or JSON string"""
        if isinstance(obj, str):
            try:
                obj = json.loads(obj)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        return cls(**obj)
    
    class Config:
        # Allow 'schema' as a field name even though it's a Python keyword
        populate_by_name = True


class ChartMeta(BaseModel):
    """Chart metadata structure"""
    columnOrder: Optional[list[str]] = None


def suggest_json_fix(json_str: str, error: json.JSONDecodeError) -> str:
    """Suggest fixes for common JSON typos based on error position"""
    suggestions = []
    pos = error.pos if hasattr(error, 'pos') else None
    
    if pos is not None and pos < len(json_str):
        # Check for common issues around the error position
        context_start = max(0, pos - 20)
        context_end = min(len(json_str), pos + 20)
        context = json_str[context_start:context_end]
        
        # Check for missing quotes
        if 'member' in context and '"member' not in context and "'member" not in context:
            suggestions.append("Missing quotes around 'member' property")
        if 'values' in context and '"values' not in context and "'values" not in context:
            suggestions.append("Missing quotes around 'values' property")
        if 'operator' in context and '"operator' not in context and "'operator" not in context:
            suggestions.append("Missing quotes around 'operator' property")
        
        # Check for missing commas
        if '][' in context or '}{' in context:
            suggestions.append("Missing comma between array/object elements")
        
        # Check for concatenated strings
        if ',pleteCount' in context or ',teCount' in context:
            suggestions.append("Strings appear concatenated - ensure each string is separate: [\"Task.count\",\"Task.completeCount\"]")
        
        # Check for missing brackets
        if context.count('[') != context.count(']'):
            suggestions.append("Mismatched square brackets")
        if context.count('{') != context.count('}'):
            suggestions.append("Mismatched curly braces")
    
    if suggestions:
        return " Possible issues: " + "; ".join(suggestions)
    return ""


def parse_query_param(query: Union[str, Dict[str, Any], Any]) -> tuple[Dict[str, Any], Optional[str]]:
    """
    Parse query parameter from string or dict, handling FastMCP serialization.
    Returns (parsed_query_dict, error_message)
    
    Handles multiple encoding scenarios:
    1. Direct dict (already parsed)
    2. JSON string (needs parsing)
    3. Double-encoded JSON string (FastMCP may encode twice)
    4. Other types (attempts to convert)
    """
    # If it's already a dict, use it directly
    if isinstance(query, dict):
        return query, None
    
    # Convert to string if it's not already
    query_str = str(query) if not isinstance(query, str) else query
    
    # Try to parse as JSON, handling multiple encoding layers
    max_attempts = 3
    parsed = query_str
    
    for attempt in range(max_attempts):
        try:
            if isinstance(parsed, str):
                parsed = json.loads(parsed)
            else:
                break  # Already parsed to a non-string
        except json.JSONDecodeError as e:
            if attempt == max_attempts - 1:
                # Final attempt failed - return detailed error with suggestions
                suggestion_text = suggest_json_fix(query_str, e)
                error_msg = {
                    "error": "Invalid JSON in query parameter",
                    "json_error": str(e),
                    "position": f"Line {e.lineno}, Column {e.colno}" if hasattr(e, 'lineno') else f"Position {e.pos}" if hasattr(e, 'pos') else "Unknown",
                    "received_type": type(query).__name__,
                    "received_value_preview": query_str[:500] if len(query_str) > 500 else query_str,
                    "attempt": attempt + 1,
                    "suggestion": "Ensure the query is valid JSON. Check for missing quotes, commas, or brackets." + suggestion_text
                }
                return None, json.dumps(error_msg, indent=2)
            # Try again with the parsed result (might be double-encoded)
            continue
    
    # Validate that we got a dict
    if not isinstance(parsed, dict):
        return None, json.dumps({
            "error": "Query parameter must be a JSON object/dictionary",
            "received_type": type(query).__name__,
            "parsed_type": type(parsed).__name__,
            "parsed_value_preview": str(parsed)[:200],
            "suggestion": "The query must be a JSON object, not an array or primitive value."
        }, indent=2)
    
    return parsed, None


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
    chart_meta: Optional[Union[str, Dict[str, Any]]] = None,
    type: Optional[str] = None,
) -> str:
    """Update an existing advanced report. Provide only the fields you want to update. The query and chart_meta parameters can be JSON strings or dicts."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    data = {}
    if title is not None:
        data["title"] = title
    if chart is not None:
        data["chart"] = chart
    if query is not None:
        query_dict, error = parse_query_param(query)
        if error:
            return error
        try:
            cube_query = CubeQuery(**query_dict)
            data["query"] = cube_query.model_dump()
        except ValueError as e:
            return json.dumps({
                "error": "Invalid query parameter",
                "details": str(e),
                "suggestion": "Ensure query has required fields: schema, dimensions, measures"
            }, indent=2)
    if description is not None:
        data["description"] = description
    if chart_meta is not None:
        if isinstance(chart_meta, dict):
            chart_meta_dict = chart_meta
        else:
            chart_meta_str = str(chart_meta)
            parsed_meta = chart_meta_str
            for _ in range(3):
                try:
                    if isinstance(parsed_meta, str):
                        parsed_meta = json.loads(parsed_meta)
                    else:
                        break
                except json.JSONDecodeError as e:
                    return json.dumps({
                        "error": "Invalid chart_meta parameter",
                        "json_error": str(e),
                        "position": f"Line {e.lineno}, Column {e.colno}" if hasattr(e, 'lineno') else "Unknown"
                    }, indent=2)
            if not isinstance(parsed_meta, dict):
                return json.dumps({
                    "error": "Invalid chart_meta parameter",
                    "details": f"Expected dict, got {type(parsed_meta).__name__}"
                }, indent=2)
            chart_meta_dict = parsed_meta
        try:
            chart_meta_obj = ChartMeta(**chart_meta_dict)
            data["chart_meta"] = chart_meta_obj.model_dump()
        except ValueError as e:
            return json.dumps({
                "error": "Invalid chart_meta parameter",
                "details": str(e)
            }, indent=2)
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
    chart_meta: Optional[Union[str, Dict[str, Any]]] = None,
    type: Optional[str] = None,
) -> str:
    """Create a new advanced report. The query parameter can be a JSON string or dict with schema, dimensions, measures, filters, order, and limit. The chart_meta parameter can be a JSON string or dict if provided.
    
    Example query: {"schema": "application", "dimensions": ["Project.name"], "measures": ["Task.count"]}
    Example chart_meta: {"columnOrder": ["Project.name", "Task.count"]}
    """
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    # Parse query (handles both dict and JSON string, including FastMCP double-encoding)
    query_dict, error = parse_query_param(query)
    if error:
        return error
    
    try:
        # Validate using Pydantic model
        cube_query = CubeQuery(**query_dict)
        query_dict = cube_query.model_dump()
    except ValueError as e:
        return json.dumps({
            "error": "Invalid query parameter",
            "details": str(e),
            "suggestion": "Ensure query is valid JSON with schema, dimensions, and measures fields"
        }, indent=2)
    
    # Parse chart_meta if provided (handles FastMCP double-encoding)
    chart_meta_dict = None
    if chart_meta is not None:
        if isinstance(chart_meta, dict):
            chart_meta_dict = chart_meta
        else:
            # Parse as JSON string, handling multiple encoding layers
            chart_meta_str = str(chart_meta)
            parsed_meta = chart_meta_str
            for _ in range(3):  # Try up to 3 layers of encoding
                try:
                    if isinstance(parsed_meta, str):
                        parsed_meta = json.loads(parsed_meta)
                    else:
                        break
                except json.JSONDecodeError as e:
                    return json.dumps({
                        "error": "Invalid chart_meta parameter",
                        "json_error": str(e),
                        "position": f"Line {e.lineno}, Column {e.colno}" if hasattr(e, 'lineno') else "Unknown",
                        "received_preview": chart_meta_str[:200]
                    }, indent=2)
            
            if not isinstance(parsed_meta, dict):
                return json.dumps({
                    "error": "Invalid chart_meta parameter",
                    "details": f"Expected dict, got {type(parsed_meta).__name__}"
                }, indent=2)
            chart_meta_dict = parsed_meta
        
        try:
            chart_meta_obj = ChartMeta(**chart_meta_dict)
            chart_meta_dict = chart_meta_obj.model_dump()
        except ValueError as e:
            return json.dumps({
                "error": "Invalid chart_meta parameter",
                "details": str(e)
            }, indent=2)
    
    data = {"title": title, "chart": chart, "query": query_dict}
    if description:
        data["description"] = description
    if chart_meta_dict:
        data["chart_meta"] = chart_meta_dict
    if type is not None:
        data["type"] = type
    result = api_client.create_advanced_report(data)
    return json.dumps(result, indent=2)


@mcp.tool()
async def execute_cube_query(ctx: Context, query: Union[str, Dict[str, Any]]) -> str:
    """Execute a Cube API query for advanced analytics. The query parameter can be a JSON string or dict.
    
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
    
    # Parse query (handles both dict and JSON string)
    try:
        if isinstance(query, str):
            query_dict = json.loads(query)
        else:
            query_dict = query
        # Validate using Pydantic model
        cube_query = CubeQuery(**query_dict)
        parsed_query = cube_query.model_dump()
    except (json.JSONDecodeError, ValueError) as e:
        return json.dumps({
            "error": "Invalid query parameter",
            "details": str(e),
            "suggestion": "Ensure query is valid JSON with schema, dimensions, and measures fields"
        }, indent=2)
    
    # Basic validation
    if "schema" not in parsed_query:
        return json.dumps({"error": "Query must include 'schema' field (e.g., 'application', 'countermeasure', 'user')"}, indent=2)
    
    if "dimensions" not in parsed_query and "measures" not in parsed_query:
        return json.dumps({"error": "Query must include at least one of 'dimensions' or 'measures'"}, indent=2)
    
    result = api_client.execute_cube_query(parsed_query)
    return json.dumps(result, indent=2)

