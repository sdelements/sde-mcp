"""
SD Elements API Client

A Python client for interacting with the SD Elements API v2.
"""

import os
import requests
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urljoin, urlparse
from difflib import SequenceMatcher
import json
from datetime import datetime, timedelta


class SDElementsAPIError(Exception):
    """Base exception for SD Elements API errors"""
    pass


class SDElementsAuthError(SDElementsAPIError):
    """Authentication error"""
    pass


class SDElementsNotFoundError(SDElementsAPIError):
    """Resource not found error"""
    pass


class SDElementsAPIClient:
    """
    SD Elements API v2 Client
    
    Provides methods to interact with SD Elements API endpoints.
    """
    
    def __init__(self, host: str, api_key: str):
        """
        Initialize the SD Elements API client.
        
        Args:
            host: SD Elements host URL (e.g., "https://your-instance.sdelements.com")
            api_key: API key for authentication
        """
        self.host = host.rstrip('/')
        self.api_key = api_key
        self.base_url = f"{self.host}/api/v2/"
        
        # JWT token cache for Cube API (expires after 1 minute by default)
        self._jwt_token = None
        self._jwt_expires_at = None
        
        # Default headers
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.api_key}',
            'Accept': 'application/json'
        }
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Cache for library answers (loaded on startup)
        self._library_answers_cache: Optional[List[Dict[str, Any]]] = None
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the SD Elements API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to base_url)
            params: URL parameters
            data: Form data
            json_data: JSON data for request body
            
        Returns:
            Response data as dictionary
            
        Raises:
            SDElementsAPIError: For API errors
            SDElementsAuthError: For authentication errors
            SDElementsNotFoundError: For 404 errors
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                timeout=30
            )
            
            # Handle different status codes
            if response.status_code == 401:
                raise SDElementsAuthError("Authentication failed. Check your API key.")
            elif response.status_code == 403:
                raise SDElementsAuthError("Access forbidden. Check your permissions.")
            elif response.status_code == 404:
                raise SDElementsNotFoundError(f"Resource not found: {url}")
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    # Try to get detailed error message from various possible fields
                    error_msg = (
                        error_data.get('detail') or 
                        error_data.get('error') or 
                        error_data.get('message') or
                        str(error_data)  # Fallback to string representation of entire error object
                    )
                    if not error_msg or error_msg == 'None':
                        error_msg = f"API error: {response.status_code}\nResponse: {json.dumps(error_data, indent=2)}"
                    else:
                        error_msg = f"API error: {response.status_code} - {error_msg}"
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                raise SDElementsAPIError(error_msg)
            
            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                if response.status_code == 204:  # No content
                    return {}
                # If we got HTML instead of JSON, it's likely an authentication or endpoint issue
                if 'text/html' in response.headers.get('Content-Type', ''):
                    raise SDElementsAuthError(f"Received HTML response instead of JSON. This may indicate an authentication issue or that the endpoint doesn't exist. URL: {url}")
                return {"text": response.text}
                
        except requests.exceptions.ConnectionError:
            raise SDElementsAPIError(f"Connection error: Unable to connect to {self.host}")
        except requests.exceptions.Timeout:
            raise SDElementsAPIError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise SDElementsAPIError(f"Request error: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request"""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request"""
        return self._make_request('POST', endpoint, json_data=data)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request"""
        return self._make_request('PUT', endpoint, json_data=data)
    
    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PATCH request"""
        return self._make_request('PATCH', endpoint, json_data=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request"""
        return self._make_request('DELETE', endpoint)
    
    # Projects API
    def list_projects(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List all projects"""
        return self.get('projects/', params)
    
    def get_project(self, project_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get project by ID"""
        return self.get(f'projects/{project_id}/', params)
    
    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            data: Dictionary with project data including 'name', 'application' (or 'application_id'),
                  and optionally 'profile' (or 'profile_id'), 'description', 'phase_id'
        """
        # Transform application_id to application if needed
        if 'application_id' in data:
            data['application'] = data.pop('application_id')
        # Transform profile_id to profile if needed
        if 'profile_id' in data:
            data['profile'] = data.pop('profile_id')
        return self.post('projects/', data)
    
    def update_project(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a project"""
        return self.patch(f'projects/{project_id}/', data)
    
    def delete_project(self, project_id: int) -> Dict[str, Any]:
        """Delete a project"""
        return self.delete(f'projects/{project_id}/')
    
    # Project Survey API
    def get_project_survey(self, project_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get project survey"""
        return self.get(f'projects/{project_id}/survey/', params)
    
    def update_project_survey(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update project survey with answers using the draft workflow.
        
        This method:
        1. Gets the current survey draft (works even if survey is already published)
        2. Updates each answer in the provided list to be selected
        3. Deselects any answers that are currently selected but not in the provided list
        4. Optionally commits the draft if survey_complete is True
        
        Note: The draft endpoint works for both unpublished and published surveys.
        For published surveys, the draft reflects the current published state and can be
        modified and committed again to update the published survey.
        
        Args:
            project_id: The project ID
            data: Dictionary with 'answers' (list of answer IDs) and optionally 'survey_complete' (bool)
            
        Example:
            data = {
                "answers": ["A21", "A493"],
                "survey_complete": True
            }
        """
        # Get the current draft state
        # This works even if the survey is already published - the draft will reflect
        # the current published state and can be modified
        try:
            draft = self.get(f'projects/{project_id}/survey/draft/')
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to retrieve survey draft: {str(e)}",
                'suggestion': 'The survey draft endpoint may not be available for this project, or the project may not exist.'
            }
        
        current_answers = draft.get('answers', [])
        
        # Get the target answer IDs
        target_answer_ids = set(data.get('answers', []))
        
        # Track what we're updating
        selected_count = 0
        deselected_count = 0
        errors = []
        
        # Update each answer in the draft
        for answer in current_answers:
            answer_id = answer['id']
            is_currently_selected = answer.get('selected', False)
            should_be_selected = answer_id in target_answer_ids
            
            if should_be_selected and not is_currently_selected:
                # Select this answer
                try:
                    self.patch(f'projects/{project_id}/survey/draft/{answer_id}/', {'selected': True})
                    selected_count += 1
                except Exception as e:
                    errors.append(f"Failed to select {answer_id}: {str(e)}")
            elif not should_be_selected and is_currently_selected:
                # Deselect this answer
                try:
                    self.patch(f'projects/{project_id}/survey/draft/{answer_id}/', {'selected': False})
                    deselected_count += 1
                except Exception as e:
                    errors.append(f"Failed to deselect {answer_id}: {str(e)}")
        
        # Check if any target answers weren't found in the draft
        found_answer_ids = {answer['id'] for answer in current_answers}
        missing_answers = target_answer_ids - found_answer_ids
        
        result = {
            'success': True,
            'selected_count': selected_count,
            'deselected_count': deselected_count,
            'target_answers': list(target_answer_ids),
            'missing_answers': list(missing_answers) if missing_answers else None,
            'errors': errors if errors else None
        }
        
        # If survey_complete is True, commit the draft
        if data.get('survey_complete', False):
            try:
                commit_result = self.commit_survey_draft(project_id)
                result['draft_committed'] = True
                result['commit_result'] = commit_result
            except Exception as e:
                result['draft_committed'] = False
                result['commit_error'] = str(e)
        else:
            result['draft_committed'] = False
            result['note'] = 'Draft updated but not committed. Call commit_survey_draft to apply changes.'
        
        return result
    
    def add_answer_to_survey_draft(self, project_id: int, answer_id: str, 
                                   auto_resolve_dependencies: bool = True) -> Dict[str, Any]:
        """
        Add an answer to the project survey draft with automatic dependency resolution.
        
        Args:
            project_id: The project ID
            answer_id: The answer ID to add (e.g., 'A1252')
            auto_resolve_dependencies: If True, automatically add prerequisite answers
            
        Returns:
            Dictionary with result status and details
        """
        import sys
        
        # Get the draft to check current state
        draft = self.get(f'projects/{project_id}/survey/draft/')
        
        # Find the target answer in the draft
        target_answer = None
        for answer in draft.get('answers', []):
            if answer['id'] == answer_id:
                target_answer = answer
                break
        
        if not target_answer:
            return {
                'success': False,
                'answer_id': answer_id,
                'error': f'Answer {answer_id} not found in survey'
            }
        
        # Check if already selected
        if target_answer['selected']:
            return {
                'success': True,
                'answer_id': answer_id,
                'already_selected': True,
                'message': f'Answer {answer_id} is already selected'
            }
        
        # Check if it's valid
        if not target_answer['valid']:
            if not auto_resolve_dependencies:
                return {
                    'success': False,
                    'answer_id': answer_id,
                    'error': 'Answer has unmet dependencies',
                    'suggestion': 'Use auto_resolve_dependencies=True to automatically resolve'
                }
            
            # Try to find and add prerequisite answers
            question_id = target_answer['question']
            print(f"Answer {answer_id} is invalid (question: {question_id}). Looking for prerequisites...", file=sys.stderr)
            
            # Find valid answers for the same or related questions
            dependencies_added = []
            for answer in draft.get('answers', []):
                # Look for valid, unselected answers that might be prerequisites
                if (answer['valid'] and 
                    not answer['selected'] and 
                    answer['question'] == question_id):
                    
                    # Try adding this as a potential prerequisite
                    print(f"  Trying prerequisite answer {answer['id']} ({answer.get('text', 'N/A')})...", file=sys.stderr)
                    try:
                        self.patch(f'projects/{project_id}/survey/draft/{answer["id"]}/', 
                                 {'selected': True})
                        dependencies_added.append({
                            'id': answer['id'],
                            'text': answer.get('text', 'N/A')
                        })
                        print(f"  ✓ Added prerequisite {answer['id']}", file=sys.stderr)
                        
                        # Refresh the draft to check if target is now valid
                        draft = self.get(f'projects/{project_id}/survey/draft/')
                        target_answer = next((a for a in draft.get('answers', []) if a['id'] == answer_id), None)
                        
                        if target_answer and target_answer['valid']:
                            # Success! Now add the target answer
                            result = self.patch(f'projects/{project_id}/survey/draft/{answer_id}/', 
                                              {'selected': True})
                            return {
                                'success': True,
                                'answer_id': answer_id,
                                'dependencies_added': dependencies_added,
                                'result': result,
                                'message': f'Automatically added {len(dependencies_added)} prerequisite answer(s)'
                            }
                    except Exception as e:
                        print(f"  ✗ Could not add prerequisite {answer['id']}: {e}", file=sys.stderr)
                        continue
            
            # If we get here, we couldn't resolve dependencies
            return {
                'success': False,
                'answer_id': answer_id,
                'error': 'Could not automatically resolve dependencies',
                'dependencies_attempted': dependencies_added,
                'suggestion': 'This answer may require prerequisite answers from different questions'
            }
        
        # Answer is valid, just add it
        try:
            result = self.patch(f'projects/{project_id}/survey/draft/{answer_id}/', 
                              {'selected': True})
            return {
                'success': True,
                'answer_id': answer_id,
                'dependencies_added': [],
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'answer_id': answer_id,
                'error': str(e)
            }
    
    def load_library_answers(self) -> None:
        """
        Load all library answers from SD Elements API and cache them.
        This should be called once on server startup for better performance.
        """
        try:
            print("Loading SD Elements library answers cache...")
            response = self.get('library/answers/', {'page_size': 10000})
            self._library_answers_cache = response.get('results', [])
            print(f"Loaded {len(self._library_answers_cache)} library answers into cache")
        except Exception as e:
            print(f"Warning: Failed to load library answers cache: {e}")
            self._library_answers_cache = []
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using SequenceMatcher.
        Returns a value between 0.0 (no match) and 1.0 (exact match).
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def find_survey_answers_by_text(self, project_id: int, search_texts: List[str], 
                                    fuzzy_threshold: float = 0.75) -> Dict[str, Any]:
        """
        Find answer IDs by searching for answer text in the library answers cache.
        Supports both exact matching and fuzzy matching for typos/variations.
        
        Args:
            project_id: The project ID (kept for backwards compatibility, not used)
            search_texts: List of answer texts to search for (case-insensitive)
            fuzzy_threshold: Minimum similarity score (0.0-1.0) for fuzzy matches. Default: 0.75
            
        Returns:
            Dictionary mapping search text to answer details (id, exact text, question, match_type, similarity)
            
        Example:
            results = client.find_survey_answers_by_text(123, ["Java", "Pyton", "Web Application"])
            # Returns: {
            #   "Java": {"id": "A1", "text": "Java", "match_type": "exact", "similarity": 1.0, ...},
            #   "Pyton": {"id": "A707", "text": "Python", "match_type": "fuzzy", "similarity": 0.89, ...},
            #   ...
            # }
        """
        # Load cache if not already loaded
        if self._library_answers_cache is None:
            self.load_library_answers()
        
        results = {}
        
        # Normalize search texts for case-insensitive matching
        search_map = {text.lower(): text for text in search_texts}
        
        # First pass: Try exact and substring matches (fastest)
        for answer in self._library_answers_cache:
            answer_text = answer.get('text', '')
            answer_text_lower = answer_text.lower()
            display_text = answer.get('display_text', '')
            
            # Check if this answer matches any search text
            for search_lower, original_search in search_map.items():
                # Skip if already found
                if original_search in results:
                    continue
                
                # Exact match
                if search_lower == answer_text_lower:
                    results[original_search] = {
                        'id': answer.get('id'),
                        'text': answer_text,
                        'question': display_text,
                        'description': answer.get('description', ''),
                        'is_active': answer.get('is_active', True),
                        'match_type': 'exact',
                        'similarity': 1.0
                    }
                # Substring match
                elif search_lower in answer_text_lower or answer_text_lower in search_lower:
                    similarity = self._calculate_similarity(search_lower, answer_text_lower)
                    results[original_search] = {
                        'id': answer.get('id'),
                        'text': answer_text,
                        'question': display_text,
                        'description': answer.get('description', ''),
                        'is_active': answer.get('is_active', True),
                        'match_type': 'substring',
                        'similarity': similarity
                    }
        
        # Second pass: Fuzzy matching for remaining unfound search texts
        for original_search in search_texts:
            if original_search in results:
                continue
            
            search_lower = original_search.lower()
            best_match = None
            best_similarity = 0.0
            
            # Find the best fuzzy match
            for answer in self._library_answers_cache:
                answer_text = answer.get('text', '')
                if not answer_text:
                    continue
                
                similarity = self._calculate_similarity(search_lower, answer_text)
                
                if similarity > best_similarity and similarity >= fuzzy_threshold:
                    best_similarity = similarity
                    best_match = {
                        'id': answer.get('id'),
                        'text': answer_text,
                        'question': answer.get('display_text', ''),
                        'description': answer.get('description', ''),
                        'is_active': answer.get('is_active', True),
                        'match_type': 'fuzzy',
                        'similarity': similarity
                    }
            
            if best_match:
                results[original_search] = best_match
        
        # Add info about search texts that weren't found
        for original_search in search_texts:
            if original_search not in results:
                results[original_search] = {
                    'id': None,
                    'text': None,
                    'question': None,
                    'error': f'No matching answer found (threshold: {fuzzy_threshold})',
                    'match_type': 'none',
                    'similarity': 0.0
                }
        
        return results
    
    def add_survey_answers_by_text(self, project_id: int, answer_texts: List[str],
                                   fuzzy_threshold: float = 0.75,
                                   auto_resolve_dependencies: bool = True) -> Dict[str, Any]:
        """
        Add survey answers to a project by text with automatic dependency resolution.
        
        This method combines fuzzy text matching with the draft API to automatically
        resolve answer dependencies.
        
        Args:
            project_id: The project ID
            answer_texts: List of answer texts to add (e.g., ["PostgreSQL", "Java"])
            fuzzy_threshold: Minimum similarity score for fuzzy matching (0.0-1.0)
            auto_resolve_dependencies: If True, automatically add prerequisite answers
            
        Returns:
            Dictionary with detailed results for each answer
        """
        import sys
        
        # Find answer IDs from text
        print(f"Looking up answers for: {answer_texts}", file=sys.stderr)
        search_results = self.find_survey_answers_by_text(project_id, answer_texts, fuzzy_threshold)
        
        # Process each answer
        results = {
            'added': [],
            'skipped': [],
            'failed': [],
            'dependencies': []
        }
        
        for text in answer_texts:
            answer_info = search_results.get(text, {})
            answer_id = answer_info.get('id')
            
            if not answer_id:
                results['failed'].append({
                    'text': text,
                    'reason': 'Answer not found',
                    'match_info': answer_info
                })
                continue
            
            print(f"\nAdding answer '{text}' ({answer_id})...", file=sys.stderr)
            
            # Try to add using the draft API with dependency resolution
            add_result = self.add_answer_to_survey_draft(
                project_id, 
                answer_id, 
                auto_resolve_dependencies=auto_resolve_dependencies
            )
            
            if add_result['success']:
                if add_result.get('already_selected'):
                    results['skipped'].append({
                        'text': text,
                        'answer_id': answer_id,
                        'reason': 'Already selected'
                    })
                else:
                    results['added'].append({
                        'text': text,
                        'answer_id': answer_id,
                        'matched_text': answer_info.get('text'),
                        'match_type': answer_info.get('match_type'),
                        'similarity': answer_info.get('similarity')
                    })
                    
                    # Track dependencies
                    deps = add_result.get('dependencies_added', [])
                    if deps:
                        results['dependencies'].extend(deps)
                        print(f"  ✓ Added {text} (with {len(deps)} dependencies)", file=sys.stderr)
                    else:
                        print(f"  ✓ Added {text}", file=sys.stderr)
            else:
                results['failed'].append({
                    'text': text,
                    'answer_id': answer_id,
                    'reason': add_result.get('error'),
                    'suggestion': add_result.get('suggestion')
                })
                print(f"  ✗ Failed to add {text}: {add_result.get('error')}", file=sys.stderr)
        
        return {
            'success': len(results['failed']) == 0,
            'summary': {
                'added': len(results['added']),
                'skipped': len(results['skipped']),
                'failed': len(results['failed']),
                'dependencies_added': len(results['dependencies'])
            },
            'details': results
        }
    
    def commit_survey_draft(self, project_id: int) -> Dict[str, Any]:
        """
        Commit/save the survey draft to apply all changes.
        
        Args:
            project_id: The project ID
            
        Returns:
            Dictionary with the updated survey state
        """
        import sys
        print(f"Committing survey draft for project {project_id}...", file=sys.stderr)
        result = self.post(f'projects/{project_id}/survey/draft/', {})
        print(f"Survey draft committed successfully", file=sys.stderr)
        return result
    
    # Applications API
    def list_applications(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List all applications"""
        return self.get('applications/', params)
    
    def get_application(self, app_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get application by ID"""
        return self.get(f'applications/{app_id}/', params)
    
    def create_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new application"""
        return self.post('applications/', data)
    
    def update_application(self, app_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an application"""
        return self.patch(f'applications/{app_id}/', data)
    
    # Countermeasures/Tasks API
    def list_countermeasures(self, project_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List countermeasures (tasks) for a project"""
        if params is None:
            params = {}
        # Use tasks endpoint instead of countermeasures endpoint
        return self.get(f'projects/{project_id}/tasks/', params)
    
    def get_task(self, project_id: int, task_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a task (countermeasure) by project ID and task ID.
        
        Args:
            project_id: The project ID
            task_id: The task ID (e.g., "T536" or full "31244-T536")
            params: Optional query parameters
        """
        # Construct full task ID if needed (format: project_id-task_id)
        if not task_id.startswith(str(project_id)):
            full_task_id = f"{project_id}-{task_id}"
        else:
            full_task_id = task_id
        return self.get(f'projects/{project_id}/tasks/{full_task_id}/', params)
    
    def update_task(self, project_id: int, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a task (countermeasure) via the tasks endpoint.
        
        Args:
            project_id: The project ID
            task_id: The task ID (e.g., "T536" or full "31244-T536")
            data: Update data (can include status, status_note, etc.)
        """
        # Construct full task ID if needed (format: project_id-task_id)
        if not task_id.startswith(str(project_id)):
            full_task_id = f"{project_id}-{task_id}"
        else:
            full_task_id = task_id
        return self.patch(f'projects/{project_id}/tasks/{full_task_id}/', data)
    
    def get_countermeasure(self, project_id: int, countermeasure_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get countermeasure by project and task ID"""
        return self.get_task(project_id, countermeasure_id, params)
    
    def update_countermeasure(self, project_id: int, countermeasure_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a countermeasure (task)"""
        # Convert 'notes' to 'status_note' if present
        if 'notes' in data:
            data['status_note'] = data.pop('notes')
        return self.update_task(project_id, countermeasure_id, data)
    
    def add_task_note(self, project_id: int, task_id: str, note: str) -> Dict[str, Any]:
        """
        Add a note to a task (countermeasure) via the notes endpoint.
        
        Args:
            project_id: The project ID
            task_id: The task ID (e.g., "T536" or full "31244-T536")
            note: The note text to add
        """
        # Construct full task ID if needed (format: project_id-task_id)
        if not task_id.startswith(str(project_id)):
            full_task_id = f"{project_id}-{task_id}"
        else:
            full_task_id = task_id
        return self.post(f'projects/{project_id}/tasks/{full_task_id}/notes/', {"text": note})
    
    # Users API
    def list_users(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List all users"""
        return self.get('users/', params)
    
    def get_user(self, user_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get user by ID"""
        return self.get(f'users/{user_id}/', params)
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user"""
        return self.get('users/me/')
    
    # Business Units API
    def list_business_units(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List all business units"""
        return self.get('business-units/', params)
    
    def get_business_unit(self, bu_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get business unit by ID"""
        return self.get(f'business-units/{bu_id}/', params)
    
    # Profiles API
    def list_profiles(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List all available profiles"""
        return self.get('profiles/', params)
    
    def get_profile(self, profile_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get profile by ID"""
        return self.get(f'profiles/{profile_id}/', params)
    
    # Groups API
    def list_groups(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List all groups"""
        return self.get('groups/', params)
    
    def get_group(self, group_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get group by ID"""
        return self.get(f'groups/{group_id}/', params)
    
    # Team Onboarding / Repository Scanning API
    def list_team_onboarding_connections(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List team onboarding connections (GitHub/GitLab)"""
        return self.get('team-onboarding/connections/', params)
    
    def create_team_onboarding_connection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a team onboarding connection for repository scanning"""
        return self.post('team-onboarding/connections/', data)
    
    def list_team_onboarding_scans(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List team onboarding scans for a project"""
        return self.get('team-onboarding/scans/', params)
    
    def create_team_onboarding_scan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create/trigger a team onboarding scan for a project.
        
        Args:
            data: Dictionary with 'project' (ID), 'connection' (ID), and 'repository_url'
            
        Example:
            data = {
                "project": 123,
                "connection": 1,
                "repository_url": "https://github.com/org/repo"
            }
        """
        return self.post('team-onboarding/scans/', data)
    
    def get_team_onboarding_scan(self, scan_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get team onboarding scan status and results"""
        return self.get(f'team-onboarding/scans/{scan_id}/', params)
    
    # Project Diagrams API
    def list_project_diagrams(self, project_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List diagrams for a project"""
        if params is None:
            params = {}
        params['project'] = project_id
        return self.get('project-diagrams/', params)
    
    def get_project_diagram(self, diagram_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a specific project diagram"""
        return self.get(f'project-diagrams/{diagram_id}/', params)
    
    def create_project_diagram(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a project diagram.
        
        Args:
            data: Dictionary with 'project' (ID), 'name', and optional 'diagram_data' (JSON)
            
        Example:
            data = {
                "project": 123,
                "name": "System Architecture",
                "diagram_data": {...}  # JSON diagram data
            }
        """
        return self.post('project-diagrams/', data)
    
    def update_project_diagram(self, diagram_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a project diagram"""
        return self.patch(f'project-diagrams/{diagram_id}/', data)
    
    def delete_project_diagram(self, diagram_id: int) -> Dict[str, Any]:
        """Delete a project diagram"""
        return self.delete(f'project-diagrams/{diagram_id}/')
    
    # Advanced Reports API (using queries endpoint)
    def list_advanced_reports(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List advanced reports (queries)"""
        return self.get('queries/', params)
    
    def get_advanced_report(self, report_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a specific advanced report (query)"""
        return self.get(f'queries/{report_id}/', params)
    
    def create_advanced_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an advanced report (query).
        
        Args:
            data: Dictionary with report configuration including 'title', 'description', 
                  'query' (with schema, dimensions, measures, filters), 'chart', 'chart_meta', 'type'
            
        Example:
            data = {
                "title": "Security Status Report",
                "description": "Overview of security tasks",
                "chart": "table",
                "query": {
                    "schema": "application",
                    "dimensions": ["Application.name"],
                    "measures": ["Project.count"],
                    "filters": [...],
                    "order": [["Application.name", "desc"]],
                    "limit": 20
                },
                "chart_meta": {"columnOrder": []},
                "type": "D"
            }
        """
        return self.post('queries/', data)
    
    def update_advanced_report(self, report_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an advanced report (query)"""
        return self.patch(f'queries/{report_id}/', data)
    
    def delete_advanced_report(self, report_id: int) -> Dict[str, Any]:
        """Delete an advanced report (query)"""
        return self.delete(f'queries/{report_id}/')
    
    def run_advanced_report(self, report_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run/execute an advanced report to get the actual data results.
        
        This method:
        1. Fetches the query definition
        2. Executes it via the Cube API
        3. Returns the actual data results
        
        Args:
            report_id: The report ID (query_id)
            params: Optional parameters
        
        Returns:
            Dictionary with 'query' (definition) and 'data' (results)
        """
        # Get the query definition
        query_def = self.get(f'queries/{report_id}/', params)
        
        # Execute the query via Cube API to get actual data
        if 'query' in query_def:
            cube_query = query_def['query']
            try:
                data = self.execute_cube_query(cube_query)
                return {
                    "query": query_def,
                    "data": data
                }
            except Exception as e:
                # If cube execution fails, return just the query definition
                return {
                    "query": query_def,
                    "data": None,
                    "error": f"Failed to execute cube query: {str(e)}"
                }
        
        return query_def
    
    def get_cube_jwt(self) -> str:
        """
        Get a JWT token for Cube API authentication.
        JWTs are cached and automatically refreshed when expired (default 1 minute expiration).
        
        Returns:
            JWT token string
        """
        # Check if we have a valid cached token
        if self._jwt_token and self._jwt_expires_at:
            if datetime.now() < self._jwt_expires_at:
                return self._jwt_token
        
        # Get a new JWT token
        response = self.get('users/me/auth-token/')
        
        if 'token' in response:
            self._jwt_token = response['token']
            # Set expiration to 50 seconds from now (10 second buffer before actual expiration)
            self._jwt_expires_at = datetime.now() + timedelta(seconds=50)
            return self._jwt_token
        else:
            raise SDElementsAuthError(f"Failed to get JWT token: {response}")
    
    def execute_cube_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Cube API query to get actual data results.
        
        Args:
            query: A cube query object with schema, dimensions, measures, filters, etc.
                   Format: https://docs.sdelements.com/master/cubeapi/
        
        Returns:
            Query results from the Cube API
        
        Example:
            query = {
                "schema": "application",
                "dimensions": ["Application.name"],
                "measures": ["Project.count"],
                "filters": [...],
                "order": [["Application.name", "asc"]],
                "limit": 20
            }
        """
        # The Cube API uses the standard Cube.js endpoint format with JWT authentication
        # Get a JWT token for authentication (auto-refreshes if expired)
        jwt_token = self.get_cube_jwt()
        
        # Cube.js expects the query as a URL parameter, not in the POST body
        url = f"{self.host}/cubejs-api/v1/load"
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        params = {
            'query': json.dumps(query)
        }
        response = requests.get(url, headers=headers, params=params)
        
        # Check if response is successful
        if response.status_code >= 200 and response.status_code < 300:
            try:
                return response.json()
            except ValueError as e:
                # Not valid JSON, return raw text for debugging
                raise Exception(f"Cube API returned non-JSON response (status {response.status_code}): {response.text[:500]}")
        else:
            # Error response - try to parse it
            try:
                error_data = response.json()
                raise Exception(f"Cube API error (status {response.status_code}): {error_data}")
            except ValueError:
                # Response isn't JSON, return the raw text
                raise Exception(f"Cube API error (status {response.status_code}): {response.text[:500]}")
    
    # Generic API request method
    def api_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a custom API request to any endpoint.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint
            params: URL parameters
            data: Request body data
            
        Returns:
            API response data
        """
        if method.upper() in ['GET', 'DELETE']:
            return self._make_request(method.upper(), endpoint, params=params)
        else:
            return self._make_request(method.upper(), endpoint, params=params, json_data=data)
    
    def test_connection(self) -> bool:
        """
        Test the API connection and authentication.
        
        Returns:
            True if connection and authentication are successful
        """
        try:
            self.get_current_user()
            return True
        except (SDElementsAPIError, SDElementsAuthError):
            return False 