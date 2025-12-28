"""
Agent Modes for SysAgent - Specialized agent personas for different tasks.
Switch between Developer, SysAdmin, Security, and other modes.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class AgentMode(Enum):
    """Available agent modes."""
    GENERAL = "general"
    DEVELOPER = "developer"
    SYSADMIN = "sysadmin"
    SECURITY = "security"
    PRODUCTIVITY = "productivity"
    AUTOMATION = "automation"


@dataclass
class ModeConfig:
    """Configuration for an agent mode."""
    name: str
    display_name: str
    icon: str
    description: str
    system_prompt_extension: str
    preferred_tools: List[str]
    quick_actions: List[Dict[str, str]]
    color: str


class AgentModeManager:
    """
    Manages different agent modes/personas.
    
    Each mode has:
    - Custom system prompt additions
    - Preferred tools
    - Quick actions
    - Specialized behavior
    """
    
    MODES: Dict[AgentMode, ModeConfig] = {
        AgentMode.GENERAL: ModeConfig(
            name="general",
            display_name="General Assistant",
            icon="🧠",
            description="All-purpose system assistant for any task",
            system_prompt_extension="",
            preferred_tools=[],
            quick_actions=[
                {"label": "System Status", "command": "Show system status"},
                {"label": "List Processes", "command": "List running processes"},
                {"label": "Disk Space", "command": "Check disk space"},
            ],
            color="#3b82f6"
        ),
        
        AgentMode.DEVELOPER: ModeConfig(
            name="developer",
            display_name="Developer Mode",
            icon="👨‍💻",
            description="Optimized for software development tasks",
            system_prompt_extension="""
DEVELOPER MODE ACTIVE - Focus on development tasks:
- Git operations (status, commit, push, pull, branch)
- Code file management and search
- Package management (npm, pip, cargo, etc.)
- Running build commands and scripts
- Debugging assistance

PRIORITIZE:
1. git_operations for version control
2. file_operations for code files
3. process_management for dev servers
4. package_manager for dependencies
5. smart_search for finding code files

When user mentions "commit", "push", "pull", "branch" -> use git_operations
When user mentions "install", "update packages" -> use package_manager
When user mentions "find file", "search code" -> use smart_search with action="content"
""",
            preferred_tools=["git_operations", "file_operations", "process_management", 
                            "package_manager", "smart_search", "generate_code"],
            quick_actions=[
                {"label": "🔀 Git Status", "command": "Show git status"},
                {"label": "📦 Install Deps", "command": "Install dependencies"},
                {"label": "🔍 Find Code", "command": "Search for code containing "},
                {"label": "🚀 Run Server", "command": "Start the development server"},
                {"label": "📝 Recent Files", "command": "Show recently modified files"},
                {"label": "🐛 Kill Port", "command": "Kill process on port 3000"},
            ],
            color="#10b981"
        ),
        
        AgentMode.SYSADMIN: ModeConfig(
            name="sysadmin",
            display_name="SysAdmin Mode",
            icon="🔧",
            description="System administration and infrastructure management",
            system_prompt_extension="""
SYSADMIN MODE ACTIVE - Focus on system administration:
- System monitoring and health checks
- Process and service management
- Disk and storage management
- Network diagnostics
- Performance optimization
- Log analysis

PRIORITIZE:
1. system_insights for health checks and diagnostics
2. system_info for real-time metrics
3. process_management for service control
4. network_diagnostics for connectivity
5. file_operations for log access

When user mentions "health", "diagnose" -> use system_insights(action="health_check")
When user mentions "slow", "performance" -> use system_insights(action="resource_hogs")
When user mentions "disk full", "storage" -> use system_insights(action="storage_analysis")
When user mentions "network", "connection" -> use network_diagnostics
""",
            preferred_tools=["system_insights", "system_info", "process_management",
                            "network_diagnostics", "file_operations", "low_level_os"],
            quick_actions=[
                {"label": "🏥 Health Check", "command": "Run full system health check"},
                {"label": "📊 Performance", "command": "Analyze system performance"},
                {"label": "🔥 Resource Hogs", "command": "Find resource-heavy processes"},
                {"label": "💾 Storage Analysis", "command": "Analyze storage usage"},
                {"label": "🌐 Network Status", "command": "Show network connections"},
                {"label": "📜 System Logs", "command": "Show recent system logs"},
            ],
            color="#f59e0b"
        ),
        
        AgentMode.SECURITY: ModeConfig(
            name="security",
            display_name="Security Mode",
            icon="🔒",
            description="Security auditing, scanning, and hardening",
            system_prompt_extension="""
SECURITY MODE ACTIVE - Focus on security tasks:
- Security scanning and auditing
- Vulnerability assessment
- Network security analysis
- Permission and access review
- Suspicious activity detection
- Security recommendations

PRIORITIZE:
1. system_insights(action="security_scan") for security audits
2. security_operations for detailed scans
3. network_diagnostics for port scanning
4. process_management to check running processes
5. file_operations for permission checks

When user mentions "scan", "audit", "security check" -> use system_insights(action="security_scan")
When user mentions "ports", "open ports" -> use network_diagnostics(action="ports")
When user mentions "suspicious", "malware" -> use security_operations
BE CAUTIOUS and provide detailed security recommendations
""",
            preferred_tools=["system_insights", "security_operations", "network_diagnostics",
                            "process_management", "file_operations"],
            quick_actions=[
                {"label": "🔍 Security Scan", "command": "Run a security scan"},
                {"label": "🚪 Open Ports", "command": "Scan for open ports"},
                {"label": "👀 Suspicious Processes", "command": "Check for suspicious processes"},
                {"label": "🔐 Permission Audit", "command": "Audit file permissions"},
                {"label": "🌐 Network Audit", "command": "Analyze network connections"},
                {"label": "📋 Security Report", "command": "Generate security report"},
            ],
            color="#ef4444"
        ),
        
        AgentMode.PRODUCTIVITY: ModeConfig(
            name="productivity",
            display_name="Productivity Mode",
            icon="⚡",
            description="Focus on productivity and workflow efficiency",
            system_prompt_extension="""
PRODUCTIVITY MODE ACTIVE - Focus on efficiency:
- Application management
- Window organization
- Note-taking and documentation
- Reminders and notifications
- Workflow automation
- Quick actions

PRIORITIZE:
1. app_control for launching/managing apps
2. window_control for workspace organization
3. document_operations for notes
4. send_notification for reminders
5. workflow_operations for automation
6. browser_control for web tasks

When user mentions "open", "launch" -> use app_control
When user mentions "note", "write down" -> use document_operations(action="create_note")
When user mentions "remind", "notification" -> use send_notification
When user mentions "organize windows" -> use window_control(action="tile_left") or tile_right
""",
            preferred_tools=["app_control", "window_control", "document_operations",
                            "send_notification", "workflow_operations", "browser_control"],
            quick_actions=[
                {"label": "📝 Quick Note", "command": "Create a note about "},
                {"label": "🪟 Tile Windows", "command": "Organize my windows"},
                {"label": "⏰ Set Reminder", "command": "Remind me in 30 minutes to "},
                {"label": "🌐 Open Browser", "command": "Open Chrome"},
                {"label": "📧 Check Email", "command": "Open my email"},
                {"label": "📅 Calendar", "command": "Open calendar"},
            ],
            color="#8b5cf6"
        ),
        
        AgentMode.AUTOMATION: ModeConfig(
            name="automation",
            display_name="Automation Mode",
            icon="🤖",
            description="Create and run automated workflows",
            system_prompt_extension="""
AUTOMATION MODE ACTIVE - Focus on automation:
- Creating and running workflows
- Scheduling tasks
- Batch operations
- Multi-step automations
- Template-based tasks

PRIORITIZE:
1. workflow_operations for workflow management
2. automation_operations for scheduling
3. context_memory for saving patterns
4. smart_search for finding automation targets
5. file_operations for batch file operations

When user mentions "workflow", "routine" -> use workflow_operations
When user mentions "schedule", "automate" -> use automation_operations
When user mentions "remember", "save pattern" -> use context_memory
SUGGEST workflow creation for repetitive tasks
""",
            preferred_tools=["workflow_operations", "automation_operations", "context_memory",
                            "smart_search", "file_operations"],
            quick_actions=[
                {"label": "▶️ Run Workflow", "command": "List and run a workflow"},
                {"label": "➕ Create Workflow", "command": "Create a new workflow for "},
                {"label": "📋 Show Templates", "command": "Show workflow templates"},
                {"label": "🌅 Morning Routine", "command": "Run morning routine workflow"},
                {"label": "⏰ Schedule Task", "command": "Schedule a task to "},
                {"label": "🔄 Batch Process", "command": "Process all files in "},
            ],
            color="#06b6d4"
        ),
    }
    
    def __init__(self):
        self.current_mode = AgentMode.GENERAL
    
    def set_mode(self, mode: AgentMode) -> ModeConfig:
        """Set the current agent mode."""
        self.current_mode = mode
        return self.MODES[mode]
    
    def get_mode(self) -> AgentMode:
        """Get the current mode."""
        return self.current_mode
    
    def get_config(self) -> ModeConfig:
        """Get the current mode configuration."""
        return self.MODES[self.current_mode]
    
    def get_system_prompt_extension(self) -> str:
        """Get the system prompt extension for the current mode."""
        return self.MODES[self.current_mode].system_prompt_extension
    
    def get_quick_actions(self) -> List[Dict[str, str]]:
        """Get quick actions for the current mode."""
        return self.MODES[self.current_mode].quick_actions
    
    def get_preferred_tools(self) -> List[str]:
        """Get preferred tools for the current mode."""
        return self.MODES[self.current_mode].preferred_tools
    
    def list_modes(self) -> List[Dict]:
        """List all available modes."""
        return [
            {
                "id": mode.value,
                "name": config.display_name,
                "icon": config.icon,
                "description": config.description,
                "color": config.color,
                "is_current": mode == self.current_mode
            }
            for mode, config in self.MODES.items()
        ]
    
    def get_mode_by_name(self, name: str) -> Optional[AgentMode]:
        """Get a mode by its name."""
        for mode in AgentMode:
            if mode.value == name.lower():
                return mode
        return None


# Global instance
_mode_manager: Optional[AgentModeManager] = None


def get_mode_manager() -> AgentModeManager:
    """Get the global mode manager instance."""
    global _mode_manager
    if _mode_manager is None:
        _mode_manager = AgentModeManager()
    return _mode_manager
