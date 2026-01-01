"""
Tool Executor Service
Handles execution of tools/functions called by LLM
"""
import logging
from typing import Dict, Any, Optional, List
from app.services.tools import (
    execute_tool,
    get_available_tools,
    detect_tool_need,
    TOOLS
)

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes tools and manages tool calling workflow.
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.tool_history = []  # Track tool usage
        logger.info(f"Tool executor initialized (enabled: {enabled})")
    
    def execute_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool call.
        
        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
        
        Returns:
            Execution result
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Tool execution is disabled"
            }
        
        result = execute_tool(tool_name, parameters)
        
        # Track usage
        self.tool_history.append({
            'tool': tool_name,
            'parameters': parameters,
            'success': result.get('success', False),
            'timestamp': __import__('time').time()
        })
        
        # Keep only last 100 entries
        if len(self.tool_history) > 100:
            self.tool_history = self.tool_history[-100:]
        
        return result
    
    def auto_detect_and_execute(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Auto-detect tool need from text and execute.
        
        Args:
            text: User input text
        
        Returns:
            Tool result if tool was executed, None otherwise
        """
        if not self.enabled:
            return None
        
        tool_name = detect_tool_need(text)
        if not tool_name:
            return None
        
        # Extract parameters from text (simplified)
        parameters = self._extract_parameters(text, tool_name)
        
        logger.info(f"Auto-detected tool: {tool_name} with params: {parameters}")
        return self.execute_tool_call(tool_name, parameters)
    
    def _extract_parameters(self, text: str, tool_name: str) -> Dict[str, Any]:
        """
        Extract tool parameters from text (simplified extraction).
        
        Args:
            text: User input
            tool_name: Tool name
        
        Returns:
            Parameters dictionary
        """
        parameters = {}
        
        if tool_name == "calculator":
            # Extract expression (simplified)
            parameters["expression"] = text
        elif tool_name == "get_current_time":
            parameters = {}
        elif tool_name == "get_weather":
            # Extract location (simplified)
            words = text.split()
            if len(words) > 2:
                # Try to find location after "weather" keyword
                weather_idx = next((i for i, w in enumerate(words) if "weather" in w.lower()), -1)
                if weather_idx >= 0 and weather_idx + 1 < len(words):
                    parameters["location"] = " ".join(words[weather_idx + 1:])
                else:
                    parameters["location"] = "unknown"
            else:
                parameters["location"] = "unknown"
        elif tool_name == "search_web":
            # Extract query
            search_keywords = ["search", "find", "look up"]
            for keyword in search_keywords:
                if keyword in text.lower():
                    idx = text.lower().find(keyword)
                    parameters["query"] = text[idx + len(keyword):].strip()
                    break
            if "query" not in parameters:
                parameters["query"] = text
        
        return parameters
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about tool usage"""
        from collections import Counter
        tool_counts = Counter(entry['tool'] for entry in self.tool_history)
        return {
            'enabled': self.enabled,
            'total_executions': len(self.tool_history),
            'tool_usage': dict(tool_counts),
            'available_tools': list(TOOLS.keys())
        }


# Global tool executor instance
_tool_executor = ToolExecutor()


def get_tool_executor() -> ToolExecutor:
    """Get global tool executor instance"""
    return _tool_executor

