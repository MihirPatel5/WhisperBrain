"""
Tool Definitions
Functions that the LLM can call (function calling / tool use)
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# Available tools
TOOLS = {
    "calculator": {
        "name": "calculator",
        "description": "Perform mathematical calculations",
        "parameters": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)')"
            }
        }
    },
    "get_current_time": {
        "name": "get_current_time",
        "description": "Get the current date and time",
        "parameters": {}
    },
    "get_weather": {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "parameters": {
            "location": {
                "type": "string",
                "description": "City name or location"
            }
        }
    },
    "search_web": {
        "name": "search_web",
        "description": "Search the web for information",
        "parameters": {
            "query": {
                "type": "string",
                "description": "Search query"
            }
        }
    }
}


def calculator(expression: str) -> Dict[str, Any]:
    """
    Evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression as string
    
    Returns:
        Result dictionary
    """
    try:
        # Safe evaluation (only basic math operations)
        allowed_chars = set('0123456789+-*/()., ')
        if not all(c in allowed_chars or c.isalpha() for c in expression):
            return {
                "success": False,
                "error": "Invalid characters in expression",
                "result": None
            }
        
        # Use eval with limited scope (in production, use a proper math parser)
        # For now, return a placeholder
        result = f"Calculation result for: {expression}"
        
        logger.info(f"Calculator: {expression} = {result}")
        return {
            "success": True,
            "result": result,
            "expression": expression
        }
    except Exception as e:
        logger.error(f"Calculator error: {e}")
        return {
            "success": False,
            "error": str(e),
            "result": None
        }


def get_current_time() -> Dict[str, Any]:
    """Get current date and time"""
    now = datetime.now()
    return {
        "success": True,
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timestamp": now.timestamp()
    }


def get_weather(location: str) -> Dict[str, Any]:
    """
    Get weather information (placeholder - would integrate with weather API).
    
    Args:
        location: City name or location
    
    Returns:
        Weather information
    """
    # Placeholder - in production, integrate with weather API
    logger.info(f"Weather requested for: {location}")
    return {
        "success": True,
        "location": location,
        "temperature": "N/A",
        "condition": "Weather API not configured",
        "note": "This is a placeholder. Configure a weather API to get real data."
    }


def search_web(query: str) -> Dict[str, Any]:
    """
    Search the web (placeholder - would integrate with search API).
    
    Args:
        query: Search query
    
    Returns:
        Search results
    """
    # Placeholder - in production, integrate with search API
    logger.info(f"Web search requested: {query}")
    return {
        "success": True,
        "query": query,
        "results": [],
        "note": "Web search API not configured. Configure a search API to get real results."
    }


# Tool execution mapping
TOOL_FUNCTIONS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "get_weather": get_weather,
    "search_web": search_web,
}


def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool function.
    
    Args:
        tool_name: Name of the tool
        parameters: Tool parameters
    
    Returns:
        Tool execution result
    """
    if tool_name not in TOOL_FUNCTIONS:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(TOOL_FUNCTIONS.keys())
        }
    
    try:
        tool_func = TOOL_FUNCTIONS[tool_name]
        result = tool_func(**parameters)
        logger.info(f"Tool executed: {tool_name} with params: {parameters}")
        return result
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "tool": tool_name
        }


def get_available_tools() -> Dict[str, Dict]:
    """Get all available tools"""
    return TOOLS.copy()


def detect_tool_need(text: str) -> Optional[str]:
    """
    Detect if user text indicates need for a tool.
    
    Args:
        text: User input text
    
    Returns:
        Tool name if detected, None otherwise
    """
    text_lower = text.lower()
    
    # Calculator detection
    calc_keywords = ["calculate", "compute", "math", "add", "subtract", "multiply", "divide", "="]
    if any(keyword in text_lower for keyword in calc_keywords):
        return "calculator"
    
    # Time detection
    time_keywords = ["time", "date", "what time", "what date", "now"]
    if any(keyword in text_lower for keyword in time_keywords):
        return "get_current_time"
    
    # Weather detection
    weather_keywords = ["weather", "temperature", "forecast", "rain", "sunny"]
    if any(keyword in text_lower for keyword in weather_keywords):
        return "get_weather"
    
    # Search detection
    search_keywords = ["search", "find", "look up", "google", "information about"]
    if any(keyword in text_lower for keyword in search_keywords):
        return "search_web"
    
    return None

