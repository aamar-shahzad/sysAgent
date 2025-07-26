"""
Configuration management for SysAgent CLI.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from platformdirs import user_config_dir

from ..types import Config, AgentConfig, SecurityConfig, LLMProvider, Platform
from ..utils.platform import detect_platform


class ConfigManager:
    """Manages SysAgent configuration and settings."""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.platform = detect_platform()
        self.config_dir = self._get_config_dir(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.permissions_file = self.config_dir / "permissions.json"
        self.logs_dir = self.config_dir / "logs"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self._config: Optional[Config] = None
    
    def _get_config_dir(self, config_dir: Optional[str] = None) -> Path:
        """Get the configuration directory based on platform."""
        if config_dir:
            return Path(config_dir)
        
        return Path(user_config_dir("SysAgent", "SysAgent"))
    
    def load_config(self) -> Config:
        """Load configuration from file or create default."""
        if self._config is not None:
            return self._config
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                self._config = Config(**config_data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Invalid config file, creating a new one: {e}")
                self._config = self._create_default_config()
                self.save_config()
        else:
            self._config = self._create_default_config()
            self.save_config()
        
        return self._config
    
    def _create_default_config(self) -> Config:
        """Create default configuration based on platform."""
        # Load environment variables
        llm_provider = os.getenv("SYSAGENT_LLM_PROVIDER", "openai")
        api_key = os.getenv("SYSAGENT_OPENAI_API_KEY")
        base_url = os.getenv("SYSAGENT_OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Determine default LLM provider
        try:
            provider = LLMProvider(llm_provider)
        except ValueError:
            provider = LLMProvider.OPENAI
        
        # Create agent config
        agent_config = AgentConfig(
            provider=provider,
            api_key=api_key,
            base_url=base_url if provider == LLMProvider.OLLAMA else None,
            model="gpt-4" if provider == LLMProvider.OPENAI else "llama2",
            config_dir=str(self.config_dir),
        )
        
        # Create security config
        security_config = SecurityConfig(
            dry_run=os.getenv("SYSAGENT_DRY_RUN", "false").lower() == "true",
            confirm_destructive=True,
            audit_logging=True,
            guardrails_enabled=True,
        )
        
        # Platform-specific configurations
        tools_config = self._get_default_tools_config()
        
        return Config(
            agent=agent_config,
            security=security_config,
            tools=tools_config,
            verbose=os.getenv("SYSAGENT_VERBOSE", "false").lower() == "true",
            debug=os.getenv("SYSAGENT_DEBUG", "false").lower() == "true",
        )
    
    def _get_default_tools_config(self) -> list:
        """Get default tools configuration based on platform."""
        from ..types import ToolConfig, ToolCategory
        
        base_tools = [
            ToolConfig(
                name="file_tool",
                description="File system operations",
                category=ToolCategory.FILE,
                permissions=["file_system"],
            ),
            ToolConfig(
                name="system_info_tool",
                description="System information and metrics",
                category=ToolCategory.SYSTEM,
                permissions=["system_info"],
            ),
            ToolConfig(
                name="process_tool",
                description="Process management",
                category=ToolCategory.PROCESS,
                permissions=["process_control"],
            ),
            ToolConfig(
                name="network_tool",
                description="Network diagnostics",
                category=ToolCategory.NETWORK,
                permissions=["network"],
            ),
            ToolConfig(
                name="app_tool",
                description="Application control",
                category=ToolCategory.APP,
                permissions=["app_control"],
            ),
        ]
        
        # Platform-specific tools
        if self.platform == Platform.MACOS:
            base_tools.extend([
                ToolConfig(
                    name="scheduler_tool",
                    description="Task scheduling",
                    category=ToolCategory.SCHEDULER,
                    permissions=["scheduler"],
                ),
                ToolConfig(
                    name="clipboard_tool",
                    description="Clipboard operations",
                    category=ToolCategory.CLIPBOARD,
                    permissions=["clipboard"],
                ),
            ])
        elif self.platform == Platform.LINUX:
            base_tools.extend([
                ToolConfig(
                    name="service_tool",
                    description="System service management",
                    category=ToolCategory.SERVICE,
                    permissions=["service_control"],
                ),
            ])
        
        return base_tools
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        if self._config is None:
            return
        
        config_data = self._config.model_dump()
        
        # Convert enum values to strings for JSON serialization
        if 'agent' in config_data and 'provider' in config_data['agent']:
            config_data['agent']['provider'] = config_data['agent']['provider'].value
        
        # Convert any enum values in tools list
        if 'tools' in config_data:
            for tool in config_data['tools']:
                if 'category' in tool and hasattr(tool['category'], 'value'):
                    tool['category'] = tool['category'].value
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def update_config(self, **kwargs: Any) -> None:
        """Update configuration with new values."""
        config = self.load_config()
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            elif hasattr(config.agent, key):
                setattr(config.agent, key, value)
            elif hasattr(config.security, key):
                setattr(config.security, key, value)
        
        self.save_config()
    
    def get_config(self) -> Config:
        """Get current configuration."""
        return self.load_config()
    
    def reload_config(self) -> Config:
        """Reload configuration from file."""
        self._config = None
        return self.load_config()
    
    def get_config_path(self) -> Path:
        """Get the configuration directory path."""
        return self.config_dir
    
    def get_logs_path(self) -> Path:
        """Get the logs directory path."""
        return self.logs_dir
    
    def export_config(self, path: str) -> None:
        """Export configuration to a file."""
        config = self.load_config()
        config_data = config.model_dump()
        
        # Convert enum values to strings for JSON serialization
        if 'agent' in config_data and 'provider' in config_data['agent']:
            config_data['agent']['provider'] = config_data['agent']['provider'].value
        
        # Convert any enum values in tools list
        if 'tools' in config_data:
            for tool in config_data['tools']:
                if 'category' in tool and hasattr(tool['category'], 'value'):
                    tool['category'] = tool['category'].value
        
        export_path = Path(path)
        with open(export_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def import_config(self, path: str) -> None:
        """Import configuration from a file."""
        import_path = Path(path)
        if not import_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(import_path, 'r') as f:
            config_data = json.load(f)
        
        self._config = Config(**config_data)
        self.save_config()
    
    def reset_config(self) -> None:
        """Reset configuration to defaults."""
        self._config = None
        if self.config_file.exists():
            self.config_file.unlink()
        self.load_config() 