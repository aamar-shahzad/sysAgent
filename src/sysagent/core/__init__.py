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
from .deep_agent import DeepAgent, TaskPlan, ReasoningStep, create_deep_agent
from .memory import MemoryManager, ShortTermMemory, LongTermMemory, get_memory_manager, reset_memory_manager
from .middleware import (
    HumanInTheLoopMiddleware, ApprovalRequest, ApprovalStatus, ApprovalType,
    BreakpointType, Breakpoint, StateSnapshot, FeedbackEntry,
    get_middleware, reset_middleware
)
from .context_awareness import ContextAwareness, ContextInfo, Suggestion, get_context_awareness
from .task_templates import TaskTemplateManager, TaskTemplate, TaskStep, get_template_manager

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
    # Deep Agent
    "DeepAgent",
    "TaskPlan",
    "ReasoningStep",
    "create_deep_agent",
    # Memory Management
    "MemoryManager",
    "ShortTermMemory",
    "LongTermMemory",
    "get_memory_manager",
    "reset_memory_manager",
    # Human-in-the-Loop Middleware
    "HumanInTheLoopMiddleware",
    "ApprovalRequest",
    "ApprovalStatus",
    "ApprovalType",
    "BreakpointType",
    "Breakpoint",
    "StateSnapshot",
    "FeedbackEntry",
    "get_middleware",
    "reset_middleware",
    # Context Awareness
    "ContextAwareness",
    "ContextInfo",
    "Suggestion",
    "get_context_awareness",
    # Task Templates
    "TaskTemplateManager",
    "TaskTemplate",
    "TaskStep",
    "get_template_manager",
] 