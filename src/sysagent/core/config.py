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
        self.env_file = self.config_dir / ".env"
        self.secrets_file = self.config_dir / ".secrets"
        self.logs_dir = self.config_dir / "logs"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self._config: Optional[Config] = None
        
        # Load environment variables from .env file
        self._load_env_file()
    
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
        
        # Create agent config - use gpt-4o-mini by default for 128k context
        agent_config = AgentConfig(
            provider=provider,
            api_key=api_key,
            base_url=base_url if provider == LLMProvider.OLLAMA else None,
            model="gpt-4o-mini" if provider == LLMProvider.OPENAI else "llama2",
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
        self._config = self._create_default_config()
        self.save_config()

    def _load_env_file(self) -> None:
        """Load environment variables from .env file."""
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key and value:
                                os.environ[key] = value
            except Exception as e:
                print(f"Warning: Could not load .env file: {e}")

    def save_api_key(self, key_name: str, key_value: str, use_keyring: bool = True) -> bool:
        """Save an API key securely.
        
        Args:
            key_name: Name of the API key (e.g., 'OPENAI_API_KEY')
            key_value: The API key value
            use_keyring: Whether to try using system keyring
            
        Returns:
            True if saved successfully
        """
        if not key_value:
            return False
        
        saved = False
        
        # Try to use system keyring first
        if use_keyring:
            try:
                import keyring
                keyring.set_password("sysagent", key_name, key_value)
                saved = True
            except Exception:
                pass
        
        # Also save to .env file as backup
        try:
            env_vars = {}
            
            # Load existing
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            env_vars[k.strip()] = v.strip()
            
            # Update
            env_vars[key_name] = key_value
            
            # Save
            with open(self.env_file, 'w') as f:
                for k, v in env_vars.items():
                    f.write(f"{k}={v}\n")
            
            # Set file permissions (read/write for owner only)
            os.chmod(self.env_file, 0o600)
            
            # Also set in environment
            os.environ[key_name] = key_value
            
            saved = True
        except Exception as e:
            print(f"Warning: Could not save to .env file: {e}")
        
        return saved

    def get_api_key(self, key_name: str) -> Optional[str]:
        """Get an API key from secure storage.
        
        Args:
            key_name: Name of the API key
            
        Returns:
            The API key value or None
        """
        # First check environment
        value = os.environ.get(key_name)
        if value:
            return value
        
        # Try keyring
        try:
            import keyring
            value = keyring.get_password("sysagent", key_name)
            if value:
                return value
        except Exception:
            pass
        
        # Try .env file
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            if k.strip() == key_name:
                                return v.strip().strip('"').strip("'")
            except Exception:
                pass
        
        return None

    def delete_api_key(self, key_name: str) -> bool:
        """Delete an API key from storage.
        
        Args:
            key_name: Name of the API key
            
        Returns:
            True if deleted successfully
        """
        deleted = False
        
        # Remove from keyring
        try:
            import keyring
            keyring.delete_password("sysagent", key_name)
            deleted = True
        except Exception:
            pass
        
        # Remove from environment
        if key_name in os.environ:
            del os.environ[key_name]
            deleted = True
        
        # Remove from .env file
        if self.env_file.exists():
            try:
                env_vars = {}
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            if k.strip() != key_name:
                                env_vars[k.strip()] = v.strip()
                
                with open(self.env_file, 'w') as f:
                    for k, v in env_vars.items():
                        f.write(f"{k}={v}\n")
                
                deleted = True
            except Exception:
                pass
        
        return deleted

    def list_api_keys(self) -> Dict[str, bool]:
        """List all stored API keys (names only, not values).
        
        Returns:
            Dictionary of key names and whether they have values
        """
        known_keys = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY", 
            "GOOGLE_API_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "HUGGINGFACE_API_KEY",
            "COHERE_API_KEY",
        ]
        
        result = {}
        for key_name in known_keys:
            value = self.get_api_key(key_name)
            result[key_name] = bool(value)
        
        return result

    def get_settings_summary(self) -> Dict[str, Any]:
        """Get a summary of current settings.
        
        Returns:
            Dictionary with settings summary
        """
        config = self.load_config()
        api_keys = self.list_api_keys()
        
        return {
            "config_dir": str(self.config_dir),
            "provider": config.agent.provider.value,
            "model": config.agent.model,
            "dry_run": config.security.dry_run,
            "verbose": config.verbose,
            "debug": config.debug,
            "api_keys_configured": {k: v for k, v in api_keys.items() if v},
        } 