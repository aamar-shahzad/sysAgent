"""
Base tool classes for SysAgent CLI.
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from ..types import ToolCategory, PermissionLevel


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    name: str
    description: str
    category: ToolCategory
    permissions: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "SysAgent Team"


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Dict[str, Any]
    message: str
    error: Optional[str] = None
    execution_time: Optional[float] = None


class BaseTool(ABC):
    """Base class for all SysAgent tools."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.metadata = self._get_metadata()

    @abstractmethod
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        pass

    @abstractmethod
    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Execute the tool action."""
        pass

    def execute(self, action: str, permission_manager=None, **kwargs) -> ToolResult:
        """Execute the tool with permission checking."""
        start_time = time.time()
        
        try:
            # Check permissions if permission manager is provided
            if permission_manager:
                tool_name = self.metadata.name
                if not permission_manager.check_tool_permissions(tool_name):
                    return ToolResult(
                        success=False,
                        data={},
                        message=f"Permission denied for {tool_name}",
                        error="Insufficient permissions"
                    )
            
            # Execute the tool
            result = self._execute(action, **kwargs)
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Tool execution failed: {str(e)}",
                error=str(e),
                execution_time=time.time() - start_time
            )


class ToolFactory:
    """Factory for creating tool instances."""

    def __init__(self):
        self._tools = {}

    def register_tool(self, tool_class: type):
        """Register a tool class."""
        tool_instance = tool_class()
        self._tools[tool_instance.metadata.name] = tool_instance
        return tool_class

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all available tools."""
        return list(self._tools.keys())

    def get_tool_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool."""
        tool = self.get_tool(name)
        return tool.metadata if tool else None


class ToolExecutor:
    """Executes tools with proper error handling and logging."""

    def __init__(self, permission_manager=None):
        self.permission_manager = permission_manager
        self.factory = ToolFactory()

    def register_tool(self, tool: BaseTool):
        """Register a tool with the executor."""
        self.factory._tools[tool.metadata.name] = tool

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.factory.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data={},
                message=f"Tool '{tool_name}' not found",
                error=f"Unknown tool: {tool_name}"
            )
        
        # Extract action from kwargs
        action = kwargs.pop('action', 'default')
        
        return tool.execute(action, self.permission_manager, **kwargs)

    def list_available_tools(self) -> List[str]:
        """List all available tools."""
        return self.factory.list_tools()


# Global tool registry
_tool_registry = {}


def register_tool(tool_class: type):
    """Decorator to register a tool."""
    _tool_registry[tool_class.__name__] = tool_class
    return tool_class


def get_registered_tools() -> Dict[str, type]:
    """Get all registered tools."""
    return _tool_registry.copy() 