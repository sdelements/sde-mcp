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
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Sequence

from dotenv import load_dotenv
from fastmcp import FastMCP, Context
from pydantic import BaseModel, ValidationError

from .api_client import SDElementsAPIClient, SDElementsAPIError, SDElementsAuthError, SDElementsNotFoundError

# Load environment variables
load_dotenv()

# FastMCP server instance
mcp = FastMCP("sdelements-mcp")

# Import resources to register them with the server
from . import resources  # noqa: F401

# Global API client
api_client: Optional[SDElementsAPIClient] = None


class ToolError(Exception):
    """Custom exception for tool execution errors"""
    pass


# Elicitation response types
# Note: MCP elicitation only supports objects with primitive fields
# For application choice, we'll use a string that can be parsed
# For profile choice, we'll use a simple string (profile ID)


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


def detect_profile_from_context(project_name: str, project_description: str = "", profiles: List[Dict[str, Any]] = None) -> Optional[int]:
    """
    Attempt to detect an appropriate profile based on project context.
    
    This function analyzes the project name and description to match against
    available profile names and descriptions.
    
    Args:
        project_name: Name of the project
        project_description: Optional description of the project
        profiles: List of available profiles with 'id', 'name', and optionally 'description'
        
    Returns:
        Profile ID if a match is found, None otherwise
    """
    if not profiles:
        return None
    
    # Combine project name and description for matching
    context = f"{project_name} {project_description}".lower()
    
    # Try to match profile names/descriptions against project context
    # Look for keywords that might indicate profile type
    profile_keywords = {
        'web': ['web', 'website', 'webapp', 'web application'],
        'mobile': ['mobile', 'ios', 'android', 'app'],
        'api': ['api', 'rest', 'restful', 'service'],
        'desktop': ['desktop', 'client'],
        'cloud': ['cloud', 'aws', 'azure', 'gcp'],
    }
    
    # Score each profile based on name/description match
    best_match = None
    best_score = 0
    
    for profile in profiles:
        profile_name = profile.get('name', '').lower()
        profile_desc = profile.get('description', '').lower()
        profile_text = f"{profile_name} {profile_desc}"
        
        score = 0
        
        # Exact name match gets highest score
        if project_name.lower() in profile_name or profile_name in project_name.lower():
            score += 10
        
        # Check for keyword matches
        for keyword_type, keywords in profile_keywords.items():
            for keyword in keywords:
                if keyword in context and keyword in profile_text:
                    score += 2
        
        # Substring matches
        if any(word in profile_text for word in context.split() if len(word) > 3):
            score += 1
        
        if score > best_score:
            best_score = score
            best_match = profile.get('id')
    
    # Only return a match if score is above threshold
    return best_match if best_score >= 3 else None


def extract_answer_texts_from_context(code_context: str, available_answers: List[Dict[str, Any]]) -> List[str]:
    """
    Extract relevant answer texts from code_context by matching against available answers.
    
    This function analyzes the code_context and matches it against available survey answers
    to determine which technologies and characteristics apply to the project.
    
    Args:
        code_context: Description of the project/technologies
        available_answers: List of available answer dictionaries with 'text' field
        
    Returns:
        List of answer texts that match the code_context
    """
    import re
    
    if not code_context:
        return []
    
    code_context_lower = code_context.lower()
    matched_answers = []
    
    # Common technology mappings (case-insensitive)
    # Order matters: longer, more specific matches should come first
    technology_keywords = [
        # Application types (longer matches first)
        ('rest api', 'REST API'),
        ('restful api', 'REST API'),
        ('restful', 'REST API'),
        ('web application', 'Web Application'),
        ('web app', 'Web Application'),
        ('webapp', 'Web Application'),
        ('mobile application', 'Mobile Application'),
        ('mobile app', 'Mobile Application'),
        ('desktop application', 'Desktop Application'),
        ('desktop app', 'Desktop Application'),
        ('microservices', 'Microservices'),
        ('microservice', 'Microservices'),
        
        # Cloud platforms (longer matches first)
        ('amazon web services', 'AWS'),
        ('google cloud platform', 'Google Cloud Platform'),
        ('google cloud', 'Google Cloud Platform'),
        ('microsoft azure', 'Azure'),
        
        # Programming languages (longer matches first)
        ('javascript', 'JavaScript'),
        ('typescript', 'TypeScript'),
        ('node.js', 'Node.js'),
        ('nodejs', 'Node.js'),
        ('golang', 'Go'),
        ('csharp', 'C#'),
        ('ruby on rails', 'Ruby on Rails'),
        ('spring boot', 'Spring Boot'),
        
        # Single-word languages (use word boundaries to avoid false matches)
        ('python', 'Python'),
        ('java', 'Java'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('swift', 'Swift'),
        ('kotlin', 'Kotlin'),
        ('scala', 'Scala'),
        ('r language', 'R'),  # Only match "R" if explicitly mentioned as "R language"
        ('r programming', 'R'),
        ('matlab', 'MATLAB'),
        
        # Databases (longer matches first)
        ('postgresql', 'PostgreSQL'),
        ('postgres', 'PostgreSQL'),
        ('sql server', 'SQL Server'),
        ('oracle database', 'Oracle Database'),
        ('mysql', 'MySQL'),
        ('mongodb', 'MongoDB'),
        ('redis', 'Redis'),
        ('cassandra', 'Cassandra'),
        ('sqlite', 'SQLite'),
        ('dynamodb', 'DynamoDB'),
        ('elasticsearch', 'Elasticsearch'),
        
        # Frameworks and tools (longer matches first)
        ('vue.js', 'Vue.js'),
        ('spring', 'Spring'),
        ('react', 'React'),
        ('angular', 'Angular'),
        ('vue', 'Vue.js'),
        ('express', 'Express'),
        ('django', 'Django'),
        ('flask', 'Flask'),
        ('rails', 'Ruby on Rails'),
        ('laravel', 'Laravel'),
        ('kubernetes', 'Kubernetes'),
        ('k8s', 'Kubernetes'),
        ('docker', 'Docker'),
        
        # Security and authentication
        ('oauth 2.0', 'OAuth 2.0'),
        ('oauth2', 'OAuth 2.0'),
        ('oauth', 'OAuth'),
        ('jwt', 'JWT'),
        ('saml', 'SAML'),
        ('ldap', 'LDAP'),
        ('active directory', 'Active Directory'),
        
        # Data formats
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('yaml', 'YAML'),
        ('csv', 'CSV'),
    ]
    
    # Extract answer texts from available answers for matching
    available_texts = {ans.get('text', '').lower(): ans.get('text', '') for ans in available_answers if ans.get('text')}
    
    # Match technologies from code_context using word boundaries for better precision
    # Process longer matches first to avoid substring issues
    for keyword, answer_text in technology_keywords:
        # Use word boundaries for single-word keywords to avoid false matches
        # For multi-word keywords, use simple substring matching
        if ' ' in keyword:
            # Multi-word: simple substring match
            pattern = re.escape(keyword)
        else:
            # Single-word: use word boundaries to avoid substring matches
            # e.g., "rest" won't match "r" but "rest api" will match "rest"
            pattern = r'\b' + re.escape(keyword) + r'\b'
        
        if re.search(pattern, code_context_lower, re.IGNORECASE):
            # Check if this answer text exists in available answers
            if answer_text.lower() in available_texts:
                matched_text = available_texts[answer_text.lower()]
                if matched_text not in matched_answers:
                    matched_answers.append(matched_text)
    
    # Also do fuzzy matching against available answers
    # Look for direct mentions of answer texts in code_context
    # Sort by length (longest first) to prioritize more specific matches
    sorted_available = sorted(available_texts.items(), key=lambda x: len(x[0]), reverse=True)
    
    for answer_text_lower, answer_text in sorted_available:
        # Skip if already matched
        if answer_text in matched_answers:
            continue
        
        # Skip very short answers (1-2 characters) to avoid false matches
        if len(answer_text_lower) <= 2:
            continue
        
        # Use word boundaries for better matching
        # Check if answer text appears as a whole word in code_context
        pattern = r'\b' + re.escape(answer_text_lower) + r'\b'
        if re.search(pattern, code_context_lower, re.IGNORECASE):
            matched_answers.append(answer_text)
    
    return matched_answers


# Import all tools - this registers them with FastMCP
# Tools are organized in separate files in the tools/ directory
from . import tools  # noqa: F401


def main():
    """Main entry point for the MCP server"""
    # Initialize API client
    global api_client
    try:
        api_client = init_api_client()
        
        # Load library answers cache on startup
        api_client.load_library_answers()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("Please set SDE_HOST and SDE_API_KEY environment variables", file=sys.stderr)
        sys.exit(1)
    
    # Run the FastMCP server
    # Note: mcp.run() is synchronous and manages its own event loop via anyio.run()
    # Apply nest_asyncio if available to handle nested event loops (e.g., in Jupyter)
    # This is optional - the server works fine without it in normal usage
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass  # nest_asyncio not available - not required for normal operation
    
    mcp.run()


if __name__ == "__main__":
    main()
