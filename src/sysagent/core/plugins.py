"""
Plugin system for SysAgent CLI.

Allows loading custom tools from external directories.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional, Type
from dataclasses import dataclass
from datetime import datetime
import json

from ..tools.base import BaseTool, register_tool, _tool_registry


@dataclass
class PluginInfo:
    """Information about a loaded plugin."""
    name: str
    version: str
    description: str
    author: str
    path: str
    tools: List[str]
    loaded_at: str
    enabled: bool = True


class PluginManager:
    """Manages loading and lifecycle of plugins."""
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """Initialize plugin manager.
        
        Args:
            plugin_dirs: List of directories to search for plugins.
                        Defaults to ~/.sysagent/plugins and ./plugins
        """
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_tools: Dict[str, Type[BaseTool]] = {}
        
        if plugin_dirs is None:
            self._plugin_dirs = [
                Path.home() / ".sysagent" / "plugins",
                Path.cwd() / "plugins"
            ]
        else:
            self._plugin_dirs = [Path(d) for d in plugin_dirs]
        
        # Create plugin directories if they don't exist
        for plugin_dir in self._plugin_dirs:
            plugin_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_plugins(self) -> List[Dict[str, Any]]:
        """Discover all available plugins.
        
        Returns:
            List of plugin metadata dictionaries.
        """
        discovered = []
        
        for plugin_dir in self._plugin_dirs:
            if not plugin_dir.exists():
                continue
            
            for item in plugin_dir.iterdir():
                if item.is_dir():
                    manifest_path = item / "plugin.json"
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r') as f:
                                manifest = json.load(f)
                            manifest["path"] = str(item)
                            manifest["loaded"] = item.name in self._plugins
                            discovered.append(manifest)
                        except Exception as e:
                            discovered.append({
                                "name": item.name,
                                "path": str(item),
                                "error": str(e)
                            })
                elif item.suffix == ".py" and not item.name.startswith("_"):
                    # Single-file plugin
                    discovered.append({
                        "name": item.stem,
                        "path": str(item),
                        "type": "single_file",
                        "loaded": item.stem in self._plugins
                    })
        
        return discovered
    
    def load_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """Load a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to load.
            
        Returns:
            PluginInfo if successful, None otherwise.
        """
        # Find the plugin
        plugin_path = None
        manifest = None
        
        for plugin_dir in self._plugin_dirs:
            # Check for directory plugin
            dir_path = plugin_dir / plugin_name
            if dir_path.exists() and dir_path.is_dir():
                manifest_path = dir_path / "plugin.json"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    plugin_path = dir_path
                    break
            
            # Check for single-file plugin
            file_path = plugin_dir / f"{plugin_name}.py"
            if file_path.exists():
                plugin_path = file_path
                manifest = {
                    "name": plugin_name,
                    "version": "1.0.0",
                    "description": f"Single-file plugin: {plugin_name}",
                    "author": "Unknown"
                }
                break
        
        if plugin_path is None:
            return None
        
        try:
            tools_loaded = []
            
            if plugin_path.is_dir():
                # Load directory plugin
                init_path = plugin_path / "__init__.py"
                if init_path.exists():
                    spec = importlib.util.spec_from_file_location(
                        f"sysagent_plugin_{plugin_name}",
                        init_path
                    )
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = module
                    spec.loader.exec_module(module)
                    
                    # Check for register function
                    if hasattr(module, "register"):
                        tools_loaded = module.register() or []
                    
                    # Also load any tool modules
                    for py_file in plugin_path.glob("*_tool.py"):
                        tool_spec = importlib.util.spec_from_file_location(
                            f"sysagent_plugin_{plugin_name}_{py_file.stem}",
                            py_file
                        )
                        tool_module = importlib.util.module_from_spec(tool_spec)
                        sys.modules[tool_spec.name] = tool_module
                        tool_spec.loader.exec_module(tool_module)
            else:
                # Load single-file plugin
                spec = importlib.util.spec_from_file_location(
                    f"sysagent_plugin_{plugin_name}",
                    plugin_path
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                
                if hasattr(module, "register"):
                    tools_loaded = module.register() or []
            
            # Record loaded tools
            for tool_name, tool_class in _tool_registry.items():
                if tool_name not in self._plugin_tools:
                    # New tool from this plugin
                    self._plugin_tools[tool_name] = tool_class
                    tools_loaded.append(tool_name)
            
            plugin_info = PluginInfo(
                name=manifest.get("name", plugin_name),
                version=manifest.get("version", "1.0.0"),
                description=manifest.get("description", ""),
                author=manifest.get("author", "Unknown"),
                path=str(plugin_path),
                tools=tools_loaded,
                loaded_at=datetime.now().isoformat()
            )
            
            self._plugins[plugin_name] = plugin_info
            return plugin_info
            
        except Exception as e:
            print(f"Failed to load plugin {plugin_name}: {e}")
            return None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload.
            
        Returns:
            True if successful, False otherwise.
        """
        if plugin_name not in self._plugins:
            return False
        
        plugin_info = self._plugins[plugin_name]
        
        # Remove tools registered by this plugin
        for tool_name in plugin_info.tools:
            if tool_name in _tool_registry:
                del _tool_registry[tool_name]
            if tool_name in self._plugin_tools:
                del self._plugin_tools[tool_name]
        
        # Remove from loaded plugins
        del self._plugins[plugin_name]
        
        # Remove from sys.modules
        modules_to_remove = [
            name for name in sys.modules 
            if name.startswith(f"sysagent_plugin_{plugin_name}")
        ]
        for mod_name in modules_to_remove:
            del sys.modules[mod_name]
        
        return True
    
    def reload_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """Reload a plugin.
        
        Args:
            plugin_name: Name of the plugin to reload.
            
        Returns:
            PluginInfo if successful, None otherwise.
        """
        self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name)
    
    def load_all(self) -> Dict[str, PluginInfo]:
        """Load all discovered plugins.
        
        Returns:
            Dictionary of loaded plugins.
        """
        for plugin_data in self.discover_plugins():
            if "error" not in plugin_data:
                name = plugin_data.get("name")
                if name and name not in self._plugins:
                    self.load_plugin(name)
        
        return self._plugins
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get info about a loaded plugin.
        
        Args:
            plugin_name: Name of the plugin.
            
        Returns:
            PluginInfo if loaded, None otherwise.
        """
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all loaded plugins.
        
        Returns:
            List of PluginInfo objects.
        """
        return list(self._plugins.values())
    
    def get_plugin_tools(self) -> Dict[str, Type[BaseTool]]:
        """Get all tools registered by plugins.
        
        Returns:
            Dictionary of tool name to tool class.
        """
        return dict(self._plugin_tools)
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        if plugin_name in self._plugins:
            self._plugins[plugin_name].enabled = True
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin (keeps it loaded but inactive)."""
        if plugin_name in self._plugins:
            self._plugins[plugin_name].enabled = False
            return True
        return False


def create_plugin_template(plugin_name: str, output_dir: Optional[str] = None) -> str:
    """Create a plugin template.
    
    Args:
        plugin_name: Name for the new plugin.
        output_dir: Directory to create plugin in. Defaults to ~/.sysagent/plugins
        
    Returns:
        Path to created plugin directory.
    """
    if output_dir is None:
        output_dir = Path.home() / ".sysagent" / "plugins"
    else:
        output_dir = Path(output_dir)
    
    plugin_dir = output_dir / plugin_name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create plugin.json
    manifest = {
        "name": plugin_name,
        "version": "1.0.0",
        "description": f"Custom plugin: {plugin_name}",
        "author": "Your Name",
        "sysagent_version": ">=1.0.0",
        "dependencies": []
    }
    
    with open(plugin_dir / "plugin.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create __init__.py
    init_content = '''"""
{name} plugin for SysAgent.
"""

def register():
    """Register plugin tools. Called when plugin is loaded."""
    # Import your tools here
    from .example_tool import ExampleTool
    return ["example_tool"]
'''.format(name=plugin_name)
    
    with open(plugin_dir / "__init__.py", "w") as f:
        f.write(init_content)
    
    # Create example tool
    tool_content = '''"""
Example tool for {name} plugin.
"""

from typing import List
from sysagent.tools.base import BaseTool, ToolMetadata, ToolResult, register_tool
from sysagent.types import ToolCategory


@register_tool
class ExampleTool(BaseTool):
    """Example plugin tool."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="example_tool",
            description="An example plugin tool",
            category=ToolCategory.SYSTEM,
            permissions=["basic"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Execute tool action."""
        if action == "hello":
            name = kwargs.get("name", "World")
            return ToolResult(
                success=True,
                data={{"greeting": f"Hello, {{name}}!"}},
                message=f"Greeted {{name}}"
            )
        else:
            return ToolResult(
                success=False,
                data={{}},
                message=f"Unknown action: {{action}}",
                error="Unsupported action"
            )
    
    def get_usage_examples(self) -> List[str]:
        """Get usage examples."""
        return [
            "example_tool --action hello --name 'User'",
        ]
'''.format(name=plugin_name)
    
    with open(plugin_dir / "example_tool.py", "w") as f:
        f.write(tool_content)
    
    # Create README
    readme_content = f'''# {plugin_name} Plugin

A custom plugin for SysAgent CLI.

## Installation

Copy this directory to `~/.sysagent/plugins/`

## Tools

- **example_tool**: An example tool that demonstrates plugin functionality.

## Usage

```bash
sysagent run "use example_tool to say hello"
```

## Development

1. Edit `example_tool.py` to customize the tool.
2. Add more tools by creating new `*_tool.py` files.
3. Update `__init__.py` to register new tools.
'''
    
    with open(plugin_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    return str(plugin_dir)
