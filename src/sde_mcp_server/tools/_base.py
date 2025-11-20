"""Base utilities for tools"""
import json
from typing import Any, Dict, Optional


def build_params(args: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function for building params"""
    params = {}
    if "page_size" in args and args["page_size"] is not None:
        params["page_size"] = args["page_size"]
    if "include" in args and args["include"] is not None:
        params["include"] = args["include"]
    if "expand" in args and args["expand"] is not None:
        params["expand"] = args["expand"]
    return params

