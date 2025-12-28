"""
Base tool classes for SysAgent CLI.
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Type
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

    @property
    def name(self) -> str:
        """Get the tool name."""
        return self.metadata.name

    @property
    def description(self) -> str:
        """Get the tool description."""
        return self.metadata.description

    @property
    def category(self) -> ToolCategory:
        """Get the tool category."""
        return self.metadata.category

    @property
    def permissions(self) -> List[str]:
        """Get the tool's required permissions."""
        return self.metadata.permissions

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

    def get_help(self) -> str:
        """Get help text for the tool."""
        help_text = f"""
Tool: {self.name}
Description: {self.description}
Category: {self.category.value}
Version: {self.metadata.version}
Permissions: {', '.join(self.permissions) if self.permissions else 'None'}

"""
        # Add usage examples if available
        if hasattr(self, 'get_usage_examples'):
            examples = self.get_usage_examples()
            if examples:
                help_text += "Usage Examples:\n"
                for example in examples:
                    help_text += f"  - {example}\n"
        
        return help_text


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

    @staticmethod
    def create_tool(tool_name: str) -> Optional[BaseTool]:
        """Create a tool instance by name."""
        tool_class = get_tool_class(tool_name)
        if tool_class:
            return tool_class()
        return None


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
_tool_registry: Dict[str, Type[BaseTool]] = {}

# Tool name to class mapping
_tool_name_to_class: Dict[str, Type[BaseTool]] = {}


def register_tool(tool_class: Type[BaseTool]) -> Type[BaseTool]:
    """Decorator to register a tool."""
    _tool_registry[tool_class.__name__] = tool_class
    
    # Create a temporary instance to get the tool name
    try:
        temp_instance = tool_class()
        _tool_name_to_class[temp_instance.metadata.name] = tool_class
    except Exception:
        pass
    
    return tool_class


def get_registered_tools() -> Dict[str, Type[BaseTool]]:
    """Get all registered tools."""
    return _tool_registry.copy()


def get_tool_class(tool_name: str) -> Optional[Type[BaseTool]]:
    """Get a tool class by tool name."""
    # First try direct lookup
    if tool_name in _tool_name_to_class:
        return _tool_name_to_class[tool_name]
    
    # Try to find by class name patterns
    class_name_patterns = [
        tool_name,
        tool_name.title().replace('_', ''),
        ''.join(word.title() for word in tool_name.split('_')),
    ]
    
    for pattern in class_name_patterns:
        if pattern in _tool_registry:
            return _tool_registry[pattern]
    
    # Try to match by iterating through registry
    for class_name, tool_class in _tool_registry.items():
        try:
            instance = tool_class()
            if instance.metadata.name == tool_name:
                _tool_name_to_class[tool_name] = tool_class
                return tool_class
        except Exception:
            continue
    
    return None


def list_available_tools() -> List[Dict[str, Any]]:
    """List all available tools with their metadata."""
    tools = []
    
    for class_name, tool_class in _tool_registry.items():
        try:
            instance = tool_class()
            tools.append({
                'name': instance.metadata.name,
                'description': instance.metadata.description,
                'category': instance.metadata.category.value,
                'permissions': instance.metadata.permissions,
                'version': instance.metadata.version,
            })
        except Exception:
            continue
    
    return tools


def get_tool_permissions(tool_name: str) -> Dict[str, PermissionLevel]:
    """Get required permissions for a tool."""
    tool_class = get_tool_class(tool_name)
    if not tool_class:
        return {}
    
    try:
        instance = tool_class()
        # Map permission names to permission levels
        permission_map = {}
        for perm in instance.metadata.permissions:
            # Default to READ level for most permissions
            permission_map[perm] = PermissionLevel.READ
        return permission_map
    except Exception:
        return {} 