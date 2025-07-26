"""
Basic tests for SysAgent CLI.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from sysagent.core.config import ConfigManager
from sysagent.core.permissions import PermissionManager
from sysagent.types import Config, Platform
from sysagent.utils.platform import detect_platform


def test_platform_detection():
    """Test platform detection."""
    platform = detect_platform()
    assert platform in [Platform.MACOS, Platform.LINUX, Platform.WINDOWS, Platform.UNKNOWN]


def test_config_manager():
    """Test configuration management."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigManager(temp_dir)
        config = config_manager.load_config()
        
        assert isinstance(config, Config)
        assert config.agent.provider is not None
        assert config.security.dry_run is False


def test_permission_manager():
    """Test permission management."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigManager(temp_dir)
        permission_manager = PermissionManager(config_manager)
        
        # Test permission checking
        assert permission_manager.has_permission("file_access") is True  # Default permission
        assert permission_manager.has_permission("system_admin") is False  # Default permission
        
        # Test permission status
        status = permission_manager.get_permission_status()
        assert isinstance(status, dict)
        
        # Test listing permissions
        permissions = permission_manager.list_permissions()
        assert isinstance(permissions, list)
        assert len(permissions) > 0


def test_file_tool():
    """Test file tool functionality."""
    from sysagent.tools.file_tool import FileTool
    
    tool = FileTool()
    
    # Test tool metadata
    assert tool.name == "file_tool"
    assert tool.description is not None
    assert tool.category is not None
    
    # Test tool help
    help_text = tool.get_help()
    assert isinstance(help_text, str)
    assert len(help_text) > 0


def test_system_info_tool():
    """Test system info tool functionality."""
    from sysagent.tools.system_info_tool import SystemInfoTool
    
    tool = SystemInfoTool()
    
    # Test tool metadata
    assert tool.name == "system_info_tool"
    assert tool.description is not None
    assert tool.category is not None
    
    # Test tool help
    help_text = tool.get_help()
    assert isinstance(help_text, str)
    assert len(help_text) > 0


def test_tool_registry():
    """Test tool registry functionality."""
    from sysagent.tools.base import list_available_tools, get_tool_class
    
    # Test listing tools
    tools = list_available_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0
    
    # Test getting tool class
    file_tool_class = get_tool_class("file_tool")
    assert file_tool_class is not None
    
    system_info_tool_class = get_tool_class("system_info_tool")
    assert system_info_tool_class is not None


def test_tool_factory():
    """Test tool factory functionality."""
    from sysagent.tools.base import ToolFactory
    
    # Test creating tools
    file_tool = ToolFactory.create_tool("file_tool")
    assert file_tool is not None
    assert file_tool.name == "file_tool"
    
    system_info_tool = ToolFactory.create_tool("system_info_tool")
    assert system_info_tool is not None
    assert system_info_tool.name == "system_info_tool"


def test_tool_execution():
    """Test tool execution."""
    from sysagent.tools.base import ToolExecutor
    
    executor = ToolExecutor()
    
    # Test file tool execution
    result = executor.execute_tool("file_tool", action="list", path=".")
    assert isinstance(result.success, bool)
    assert isinstance(result.message, str)


if __name__ == "__main__":
    pytest.main([__file__]) 