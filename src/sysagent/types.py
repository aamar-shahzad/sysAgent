"""
Core types and data structures for SysAgent CLI.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class PermissionLevel(Enum):
    """Permission levels for system operations."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class Platform(Enum):
    """Supported operating systems."""
    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class ToolCategory(Enum):
    """Categories for system tools."""
    FILE = "file"
    SYSTEM = "system"
    PROCESS = "process"
    NETWORK = "network"
    APP = "app"
    SCHEDULER = "scheduler"
    SERVICE = "service"
    CLIPBOARD = "clipboard"
    AUTH = "auth"
    SCREENSHOT = "screenshot"
    VOICE = "voice"
    VISION = "vision"
    CUSTOM = "custom"
    SECURITY = "security"
    AUTOMATION = "automation"
    MONITORING = "monitoring"
    CODE_GENERATION = "code_generation"
    OS_INTELLIGENCE = "os_intelligence"
    LOW_LEVEL = "low_level"


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    LOCAL = "local"
    BEDROCK = "bedrock"


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    data: Dict[str, Any]
    message: str
    error: Optional[str] = None
    execution_time: Optional[float] = None


@dataclass
class PermissionRequest:
    """Permission request for system operations."""
    permission: str
    level: PermissionLevel
    description: str
    required: bool = True
    granted: bool = False


class ToolConfig(BaseModel):
    """Configuration for a system tool."""
    name: str
    description: str
    category: ToolCategory
    permissions: List[str] = Field(default_factory=list)
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for the LLM agent."""
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2000
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    config_dir: Optional[str] = None


class SecurityConfig(BaseModel):
    """Security configuration."""
    dry_run: bool = False
    confirm_destructive: bool = True
    log_encryption: bool = False
    audit_logging: bool = True
    guardrails_enabled: bool = True


class Config(BaseModel):
    """Main configuration for SysAgent."""
    agent: AgentConfig = Field(default_factory=AgentConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    tools: List[ToolConfig] = Field(default_factory=list)
    plugins: List[str] = Field(default_factory=list)
    verbose: bool = False
    debug: bool = False


class CommandContext(BaseModel):
    """Context for command execution."""
    user_input: str
    platform: Platform
    permissions: List[PermissionRequest]
    config: Config
    session_id: str
    timestamp: float


class ExecutionPlan(BaseModel):
    """Plan for multi-step execution."""
    steps: List[Dict[str, Any]]
    estimated_time: float
    requires_confirmation: bool
    dry_run: bool = False


class LogEntry(BaseModel):
    """Log entry for auditing."""
    timestamp: float
    session_id: str
    user_input: str
    tool_used: Optional[str] = None
    success: bool
    error: Optional[str] = None
    execution_time: float
    data: Dict[str, Any] = Field(default_factory=dict)


# Type aliases for convenience
ToolData = Dict[str, Any]
ToolResponse = Union[ToolResult, Dict[str, Any]]
PermissionMap = Dict[str, PermissionLevel] 