"""Project-related tools"""
import asyncio
import json
import sys
from typing import List, Optional, Union

from fastmcp import Context

from ..server import mcp, api_client, init_api_client, detect_profile_from_context
from ._base import build_params

# Timeout for elicitation calls (in seconds)
# If elicitation times out, we'll return an error asking for the parameter
ELICITATION_TIMEOUT = 30.0


@mcp.tool()
async def list_projects(ctx: Context, page_size: Optional[int] = None, include: Optional[str] = None, expand: Optional[str] = None) -> str:
    """List all projects in SD Elements"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    params = build_params({"page_size": page_size, "include": include, "expand": expand})
    result = api_client.list_projects(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_project(ctx: Context, project_id: int, page_size: Optional[int] = None, include: Optional[str] = None, expand: Optional[str] = None) -> str:
    """Get details of a specific project. Use list_countermeasures to see countermeasures for a project, not this tool."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    params = build_params({"page_size": page_size, "include": include, "expand": expand})
    result = api_client.get_project(project_id, params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_profiles(ctx: Context, page_size: Optional[int] = None) -> str:
    """List all available profiles in SD Elements"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    params = {"page_size": page_size} if page_size is not None else {}
    result = api_client.list_profiles(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_risk_policies(ctx: Context, page_size: Optional[int] = None) -> str:
    """List all available risk policies in SD Elements"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    params = {"page_size": page_size} if page_size is not None else {}
    result = api_client.list_risk_policies(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_risk_policy(ctx: Context, risk_policy_id: int, page_size: Optional[int] = None) -> str:
    """Get details of a specific risk policy"""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    params = {"page_size": page_size} if page_size is not None else {}
    result = api_client.get_risk_policy(risk_policy_id, params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def create_project(
    ctx: Context,
    application_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    phase_id: Optional[int] = None,
    profile_id: Optional[str] = None,
) -> str:
    """Create a new project in SD Elements. If name is not specified, prompts user to provide it. If profile is not specified, attempts to detect it from project name/description (e.g., 'mobile project' → Mobile profile). If detection fails, prompts user to select from available profiles."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    # Elicitation for name if not provided
    if not name:
        try:
            name_result = await asyncio.wait_for(
                ctx.elicit(
                    "What is the name of the project you want to create?",
                    response_type=str
                ),
                timeout=ELICITATION_TIMEOUT
            )
            if name_result.action != "accept":
                return json.dumps({"error": "Project creation cancelled: project name is required"})
            name = name_result.data
        except asyncio.TimeoutError:
            return json.dumps({"error": "Elicitation timeout: project name is required. Please provide the 'name' parameter."})
    
    # Elicitation for profile_id if not provided
    if not profile_id:
        profiles_response = api_client.list_profiles({"page_size": 1000})
        profiles = profiles_response.get("results", [])
        
        if not profiles:
            return json.dumps({"error": "No profiles available. Cannot create project without a profile."})
        
        # Try to detect profile from project name/description
        detected_profile_id = detect_profile_from_context(name, description or "", profiles)
        
        if detected_profile_id:
            # Profile detected automatically - use it
            profile_id = detected_profile_id
        else:
            # No profile detected - prompt user to select from available profiles
            profile_options = []
            profile_id_map = {}
            default_profile_id = None
            
            for profile in profiles:
                profile_name_val = profile.get("name", "Unnamed Profile")
                profile_id_val = profile.get("id")
                profile_options.append(profile_name_val)
                profile_id_map[profile_name_val] = profile_id_val
                
                # Track default profile to highlight it in the prompt
                if profile.get("default", False):
                    default_profile_id = profile_id_val
            
            # Always prompt user to select a profile when detection fails
            prompt_message = "Select a profile:"
            if default_profile_id:
                # Find default profile name for the prompt
                default_profile_name = next(
                    (name for name, pid in profile_id_map.items() if pid == default_profile_id),
                    None
                )
                if default_profile_name:
                    prompt_message = f"Select a profile (default: {default_profile_name}):"
            
            try:
                profile_result = await asyncio.wait_for(
                    ctx.elicit(prompt_message, response_type=profile_options),
                    timeout=ELICITATION_TIMEOUT
                )
                if profile_result.action != "accept":
                    return json.dumps({"error": "Project creation cancelled: profile selection is required"})
                profile_id = profile_id_map.get(profile_result.data)
                if not profile_id:
                    return json.dumps({"error": f"Could not find profile ID for selection: {profile_result.data}"})
            except asyncio.TimeoutError:
                return json.dumps({"error": "Elicitation timeout: profile selection is required. Please provide the 'profile_id' parameter."})
    
    # Ensure profile_id is set - API requires it
    if not profile_id:
        return json.dumps({"error": "Profile is required but could not be determined. Please specify a profile_id."})
    
    data = {"name": name, "application": application_id}
    if description:
        data["description"] = description
    if phase_id:
        data["phase_id"] = phase_id
    # Profile is required, so always include it
    data["profile"] = profile_id
    
    result = api_client.create_project(data)
    return json.dumps(result, indent=2)


@mcp.tool()
async def update_project(ctx: Context, project_id: int, name: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None, risk_policy: Optional[Union[int, str]] = None) -> str:
    """Update an existing project (name, description, status, or risk_policy). Use when user says 'update', 'change', 'modify', or 'rename'. Do NOT use for 'archive', 'delete', or 'remove' - use delete_project instead.
    
    IMPORTANT: risk_policy must be the numeric ID of the risk policy (e.g., 1, 2, 3), not the name. Use list_risk_policies to find the correct ID.
    
    According to the API documentation (https://docs.sdelements.com/master/api/docs/projects/), 
    risk_policy is an optional field that accepts the ID of the Risk Policy that applies to this project."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    # Validate risk_policy is an integer if provided
    if risk_policy is not None:
        # Handle string-to-int conversion (MCP framework may pass as string)
        if isinstance(risk_policy, str):
            try:
                risk_policy = int(risk_policy)
            except ValueError:
                return json.dumps({
                    "error": f"risk_policy must be an integer ID, got string that cannot be converted: {risk_policy}",
                    "suggestion": "Use list_risk_policies to find the correct risk policy ID (numeric value)"
                }, indent=2)
        elif not isinstance(risk_policy, int):
            return json.dumps({
                "error": f"risk_policy must be an integer ID, got {type(risk_policy).__name__}: {risk_policy}",
                "suggestion": "Use list_risk_policies to find the correct risk policy ID (numeric value)"
            }, indent=2)
    
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if status is not None:
        data["status"] = status
    if risk_policy is not None:
        data["risk_policy"] = risk_policy
    
    if not data:
        return json.dumps({"error": "No update data provided. Specify at least one field to update (name, description, status, or risk_policy)."}, indent=2)
    
    try:
        result = api_client.update_project(project_id, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = str(e)
        # Check if it's a risk_policy related error
        if "risk_policy" in error_msg.lower() or "risk policy" in error_msg.lower():
            return json.dumps({
                "error": f"Failed to update risk_policy: {error_msg}",
                "suggestion": "Verify the risk_policy ID exists using list_risk_policies. Risk policy must be a valid numeric ID."
            }, indent=2)
        return json.dumps({"error": f"Failed to update project: {error_msg}"}, indent=2)


@mcp.tool()
async def delete_project(ctx: Context, project_id: int) -> str:
    """Delete a project. Use when user says 'delete', 'remove', 'archive', or wants to permanently remove a project. Do NOT use update_project for archiving."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    result = api_client.delete_project(project_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def create_project_from_code(
    ctx: Context,
    project_name: Optional[str] = None,
    application_id: Optional[int] = None,
    application_name: Optional[str] = None,
    business_unit_id: Optional[int] = None,
    business_unit_name: Optional[str] = None,
    project_description: Optional[str] = None,
    profile_id: Optional[str] = None,
    reuse_existing_project: bool = False,
    application_description: Optional[str] = None,
) -> str:
    """
    Create application and project in SD Elements. Returns the project survey structure with all available questions and answers.
    
    IMPORTANT: Before determining survey answers, the AI client MUST search the workspace codebase for evidence of survey answers
    and security requirements. Analyze code files, configuration files, documentation, and comments to identify implementations
    that correspond to survey answers. Look for patterns such as:
    - Security controls and countermeasures mentioned in survey responses
    - Configuration settings related to survey answers (authentication, encryption, etc.)
    - Code comments referencing security requirements
    - Test files that validate survey-related implementations
    - Documentation that maps to survey answer topics
    - Dependency files (package.json, requirements.txt, etc.) indicating technologies
    - Framework and library usage that informs survey answers
    
    Search across all file types including source code, config files, README files, and test files. When evidence is found,
    extract relevant code snippets, file paths, and line numbers to inform survey answer selection.
    
    After gathering evidence from the codebase, review the survey structure, determine appropriate answers based on both the
    project context AND the evidence found in the codebase, set them using add_survey_answers_by_text or set_project_survey_by_text,
    and then commit the survey draft using commit_survey_draft to publish the survey and generate countermeasures.
    """
    global api_client
    if api_client is None:
        api_client = init_api_client()
    
    try:
        # Elicitation 1: Project name
        if not project_name:
            try:
                name_result = await asyncio.wait_for(
                    ctx.elicit(
                        "What is the name of the project you want to create?",
                        response_type=str
                    ),
                    timeout=ELICITATION_TIMEOUT
                )
                if name_result.action != "accept":
                    return json.dumps({"error": "Project creation cancelled: project name is required"})
                project_name = name_result.data
            except asyncio.TimeoutError:
                return json.dumps({"error": "Elicitation timeout: project name is required. Please provide the 'project_name' parameter."})
        
        # Elicitation 2: Application selection
        application_id_resolved = application_id
        app_result = None
        application_was_existing = False
        
        if not application_id_resolved and not application_name:
            # Get available applications for elicitation
            apps_response = api_client.list_applications({"page_size": 100})
            apps = apps_response.get("results", [])
            
            if not apps:
                # No apps available, must create new
                try:
                    app_name_result = await asyncio.wait_for(
                        ctx.elicit(
                            "No existing applications found. What name would you like for the new application?",
                            response_type=str
                        ),
                        timeout=ELICITATION_TIMEOUT
                    )
                    if app_name_result.action != "accept":
                        return json.dumps({"error": "Project creation cancelled: application name is required"})
                    application_name = app_name_result.data
                except asyncio.TimeoutError:
                    return json.dumps({"error": "Elicitation timeout: application name is required. Please provide the 'application_name' parameter."})
            else:
                # Create a list of application options for selection
                app_options = []
                app_id_map = {}
                
                for app in apps[:50]:  # Limit to 50 for selection list
                    app_display_name = app.get("name", "Unnamed Application")
                    bu_name = app.get("business_unit", {}).get("name", "Unknown") if isinstance(app.get("business_unit"), dict) else "Unknown"
                    display_text = f"{app_display_name} ({bu_name})"
                    app_options.append(display_text)
                    app_id_map[display_text] = app.get("id")
                
                # Add option to create new application
                app_options.append("Create a new application...")
                
                try:
                    app_choice_result = await asyncio.wait_for(
                        ctx.elicit(
                            "Please select an existing application or choose to create a new one:",
                            response_type=app_options  # List of strings for selection
                        ),
                        timeout=ELICITATION_TIMEOUT
                    )
                    if app_choice_result.action != "accept":
                        return json.dumps({"error": "Project creation cancelled: application selection is required"})
                    
                    selected_option = app_choice_result.data
                    
                    if selected_option == "Create a new application...":
                        # User wants to create new - ask for name
                        try:
                            app_name_result = await asyncio.wait_for(
                                ctx.elicit(
                                    "What name would you like for the new application?",
                                    response_type=str
                                ),
                                timeout=ELICITATION_TIMEOUT
                            )
                            if app_name_result.action != "accept":
                                return json.dumps({"error": "Project creation cancelled: application name is required"})
                            application_name = app_name_result.data
                        except asyncio.TimeoutError:
                            return json.dumps({"error": "Elicitation timeout: application name is required. Please provide the 'application_name' parameter."})
                except asyncio.TimeoutError:
                    return json.dumps({"error": "Elicitation timeout: application selection is required. Please provide the 'application_id' or 'application_name' parameter."})
                else:
                    # User selected an existing application
                    application_id_resolved = app_id_map.get(selected_option)
                    if not application_id_resolved:
                        return json.dumps({"error": f"Could not find application ID for selection: {selected_option}"})
        
        # Handle application creation/resolution
        if not application_id_resolved:
            if application_name:
                # Check if app exists
                apps_response = api_client.list_applications({"page_size": 1000})
                apps = apps_response.get("results", [])
                existing_app = None
                for app in apps:
                    if app.get("name", "").strip().lower() == application_name.strip().lower():
                        existing_app = app
                        break
                
                if existing_app:
                    application_id_resolved = existing_app.get("id")
                    app_result = existing_app
                    application_was_existing = True
                else:
                    # Create new application
                    business_unit_id_resolved = business_unit_id
                    if not business_unit_id_resolved:
                        if business_unit_name:
                            bus_response = api_client.list_business_units({"page_size": 1000})
                            business_units = bus_response.get("results", [])
                            for bu in business_units:
                                if bu.get("name", "").strip().lower() == business_unit_name.strip().lower():
                                    business_unit_id_resolved = bu.get("id")
                                    break
                        
                        if not business_unit_id_resolved:
                            try:
                                current_user = api_client.get_current_user()
                                user_business_unit = current_user.get("business_unit")
                                if user_business_unit:
                                    business_unit_id_resolved = user_business_unit.get("id") if isinstance(user_business_unit, dict) else user_business_unit
                            except:
                                pass
                        
                        if not business_unit_id_resolved:
                            bus_response = api_client.list_business_units({"page_size": 1000})
                            business_units = bus_response.get("results", [])
                            if business_units:
                                business_unit_id_resolved = business_units[0].get("id")
                    
                    if not business_unit_id_resolved:
                        return json.dumps({"error": "Cannot create application: No business unit found"})
                    
                    app_data = {"name": application_name, "business_unit": business_unit_id_resolved}
                    if application_description:
                        app_data["description"] = application_description
                    app_result = api_client.create_application(app_data)
                    application_id_resolved = app_result.get("id")
            else:
                return json.dumps({"error": "Either application_id or application_name must be provided"})
        else:
            application_was_existing = True
        
        # Elicitation 3: Profile selection
        profile_id_resolved = profile_id
        profile_detected = False
        profile_name = None
        
        if not profile_id_resolved:
            # Try to detect profile
            profiles_response = api_client.list_profiles({"page_size": 1000})
            profiles = profiles_response.get("results", [])
            
            if profiles:
                detected_profile_id = detect_profile_from_context(
                    project_name,
                    project_description or "",
                    profiles
                )
                
                if detected_profile_id:
                    profile_id_resolved = detected_profile_id
                    profile_detected = True
                    for profile in profiles:
                        if profile.get("id") == profile_id_resolved:
                            profile_name = profile.get("name", "Unknown")
                            break
                else:
                    # Elicitation: Ask user to select profile from a list
                    profile_options = []
                    profile_id_map = {}
                    
                    for profile in profiles:
                        profile_name_val = profile.get("name", "Unnamed Profile")
                        profile_id_val = profile.get("id")
                        profile_options.append(profile_name_val)
                        profile_id_map[profile_name_val] = profile_id_val
                    
                    try:
                        profile_result = await asyncio.wait_for(
                            ctx.elicit(
                                "Select a profile:",
                                response_type=profile_options
                            ),
                            timeout=ELICITATION_TIMEOUT
                        )
                        if profile_result.action != "accept":
                            return json.dumps({"error": "Project creation cancelled: profile selection is required"})
                        
                        selected_profile = profile_result.data
                        profile_id_resolved = profile_id_map.get(selected_profile)
                        if not profile_id_resolved:
                            return json.dumps({"error": f"Could not find profile ID for selection: {selected_profile}"})
                    except asyncio.TimeoutError:
                        return json.dumps({"error": "Elicitation timeout: profile selection is required. Please provide the 'profile_id' parameter."})
            else:
                return json.dumps({"error": "No profiles available. Cannot create project without a profile."})
        
        # Check for existing project
        existing_project = None
        try:
            projects_response = api_client.list_projects({"page_size": 1000})
            projects = projects_response.get("results", [])
            for proj in projects:
                proj_app = proj.get("application")
                proj_app_id = proj_app.get("id") if isinstance(proj_app, dict) else proj_app
                if (proj_app_id == application_id_resolved and 
                    proj.get("name", "").strip().lower() == project_name.strip().lower()):
                    existing_project = proj
                    break
        except Exception as list_error:
            print(f"Warning: Could not list existing projects: {list_error}", file=sys.stderr)
        
        if existing_project:
            if reuse_existing_project:
                project_result = existing_project
                project_id = project_result.get("id")
                project_was_existing = True
            else:
                return json.dumps({
                    "error": f"A project with the name '{project_name}' already exists in this application (ID: {existing_project.get('id')}).",
                    "existing_project_id": existing_project.get("id"),
                    "suggestion": "Either provide a different project_name, or set reuse_existing_project=true to reuse the existing project."
                })
        else:
            # Create project
            project_data = {
                "name": project_name,
                "application": application_id_resolved
            }
            if project_description:
                project_data["description"] = project_description
            if profile_id_resolved:
                project_data["profile"] = profile_id_resolved
            
            project_result = api_client.create_project(project_data)
            project_id = project_result.get("id")
            project_was_existing = False
        
        # Get survey structure
        survey_structure = api_client.get_project_survey(project_id)
        
        if api_client._library_answers_cache is None:
            api_client.load_library_answers()
        
        available_answers_summary = []
        if api_client._library_answers_cache:
            for answer in api_client._library_answers_cache:
                available_answers_summary.append({
                    'id': answer.get('id'),
                    'text': answer.get('text', ''),
                    'question': answer.get('display_text', ''),
                    'section': answer.get('section', '')
                })
        
        draft_state = None
        selected_answers_count = 0
        try:
            draft_state = api_client.get(f'projects/{project_id}/survey/draft/')
            selected_answers = [a for a in draft_state.get('answers', []) if a.get('selected', False)]
            selected_answers_count = len(selected_answers)
        except Exception as draft_error:
            draft_state = {"error": str(draft_error)}
        
        result = {
            "success": True,
            "application": {
                "id": application_id_resolved,
                "name": app_result.get("name") if app_result else application_name or "unknown",
                "was_existing": application_was_existing
            },
            "project": {
                "id": project_id,
                "name": project_result.get("name"),
                "url": project_result.get("url"),
                "was_existing": project_was_existing
            },
            "profile": {
                "id": profile_id_resolved,
                "name": profile_name,
                "detected": profile_detected
            } if profile_id_resolved else None,
            "survey_structure": {
                "note": "This contains all available survey questions and answers. Review these options and use your AI knowledge to determine which answers are appropriate for this project.",
                "total_questions": len([q for s in survey_structure.get('sections', []) for q in s.get('questions', [])]),
                "total_answers": len(available_answers_summary),
                "available_answers": available_answers_summary[:100],
                "full_survey": survey_structure
            },
            "survey_draft_state": {
                "selected_answers_count": selected_answers_count,
                "has_answers": selected_answers_count > 0,
                "draft_available": draft_state is not None and "error" not in draft_state
            },
            "next_steps": {
                "step_1": "Review the survey_structure to see all available questions and answers",
                "step_2": "Use your AI knowledge to determine appropriate answers based on the project context",
                "step_3": "Call add_survey_answers_by_text or set_project_survey_by_text to set the answers",
                "step_4": "Call commit_survey_draft to publish the survey and generate countermeasures",
                "important": "The survey draft is NOT committed automatically. You must commit it after setting answers."
            }
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "error_type": type(e).__name__
        })
