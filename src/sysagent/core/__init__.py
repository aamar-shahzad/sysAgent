"""
Core modules for SysAgent CLI.
"""

from .agent import SysAgent, AgentResult
from .config import ConfigManager
from .permissions import PermissionManager
from .langgraph_agent import LangGraphAgent
from .plugins import PluginManager, PluginInfo, create_plugin_template
from .logging import (
    AuditLogger, 
    AuditEvent, 
    EventType, 
    LogLevel,
    get_audit_logger,
    log_tool_execution,
    log_permission_request,
    log_error
)
from .session_manager import SessionManager, Session, Message
from .agent_modes import AgentMode, AgentModeManager, ModeConfig, get_mode_manager
from .activity_tracker import ActivityTracker, Activity, ActivityType, get_activity_tracker
from .smart_learning import SmartLearningSystem, get_learning_system
from .proactive_monitor import ProactiveMonitor, Alert, AlertLevel, get_monitor, start_monitoring

__all__ = [
    "SysAgent",
    "AgentResult", 
    "ConfigManager",
    "PermissionManager",
    "LangGraphAgent",
    "PluginManager",
    "PluginInfo",
    "create_plugin_template",
    "AuditLogger",
    "AuditEvent",
    "EventType",
    "LogLevel",
    "get_audit_logger",
    "log_tool_execution",
    "log_permission_request",
    "log_error",
    # Session Management
    "SessionManager",
    "Session",
    "Message",
    # Agent Modes
    "AgentMode",
    "AgentModeManager",
    "ModeConfig",
    "get_mode_manager",
    # Activity Tracking
    "ActivityTracker",
    "Activity",
    "ActivityType",
    "get_activity_tracker",
    # Smart Learning
    "SmartLearningSystem",
    "get_learning_system",
    # Proactive Monitoring
    "ProactiveMonitor",
    "Alert",
    "AlertLevel",
    "get_monitor",
    "start_monitoring",
] 