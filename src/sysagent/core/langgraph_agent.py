"""
LangGraph-based agent for SysAgent CLI with human-in-the-loop capabilities.
Includes short-term memory, middleware, and realtime streaming.
"""

import asyncio
import os
import time
import uuid
from typing import Dict, List, Any, Optional, TypedDict, Generator, Tuple
from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt

from .config import ConfigManager
from .permissions import PermissionManager
from ..tools.base import ToolExecutor

# Import memory and middleware
try:
    from .memory import MemoryManager, get_memory_manager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    MemoryManager = None

try:
    from .middleware import (
        HumanInTheLoopMiddleware, get_middleware, ApprovalType,
        BreakpointType, Breakpoint, StateSnapshot, FeedbackEntry
    )
    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False
    HumanInTheLoopMiddleware = None
    BreakpointType = None


class AgentState(TypedDict):
    """State for the LangGraph agent."""
    messages: List[Any]
    user_input: str
    tools_used: List[str]
    human_approval_needed: bool
    pending_action: Optional[Dict[str, Any]]
    session_context: Dict[str, Any]


class LangGraphAgent:
    """LangGraph-based agent with human-in-the-loop capabilities and memory."""

    def __init__(self, config_manager: ConfigManager, permission_manager: PermissionManager, 
                 debug: bool = False, auto_approve: bool = False):
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.permission_manager = permission_manager
        self.debug = debug
        self.auto_approve = auto_approve
        self.tool_executor = ToolExecutor(permission_manager)
        self.session_id = str(int(time.time()))
        self.thread_id = str(uuid.uuid4())  # Unique thread for checkpointing
        
        # Initialize checkpointer for state persistence
        self.checkpointer = MemorySaver()
        
        # Initialize short-term memory
        if MEMORY_AVAILABLE:
            self.memory_manager = get_memory_manager(self.session_id)
        else:
            self.memory_manager = None
        
        # Initialize human-in-the-loop middleware
        if MIDDLEWARE_AVAILABLE:
            self.middleware = get_middleware(auto_approve=auto_approve)
        else:
            self.middleware = None
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Create tools first
        self.tools = self._create_langgraph_tools()
        
        # Register tools with the executor
        self._register_tools_with_executor()
        
        # Create the React agent with checkpointer
        self.agent = self._create_react_agent()

    def _initialize_llm(self):
        """Initialize the OpenAI LLM with appropriate model for context size."""
        try:
            # Load API key from environment or config
            api_key = self._load_api_key()
            if not api_key:
                api_key = self._prompt_for_openai_key()
            
            # Get model from config or use default with large context
            model = self._get_model_name()
            
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model,
                temperature=0,
                api_key=api_key
            )
        except Exception as e:
            print(f"Failed to initialize LLM: {e}")
            return None

    def _get_model_name(self) -> str:
        """Get the model name from config or use a sensible default."""
        # Check environment first (allows override)
        env_model = os.environ.get("OPENAI_MODEL") or os.environ.get("SYSAGENT_MODEL")
        if env_model:
            return env_model
        
        # Check config
        if hasattr(self.config, 'agent') and hasattr(self.config.agent, 'model'):
            configured_model = self.config.agent.model
            if configured_model:
                # Upgrade old gpt-4 configs to gpt-4o-mini for larger context
                if configured_model in ["gpt-4", "gpt-4-0613", "gpt-3.5-turbo"]:
                    return "gpt-4o-mini"
                return configured_model
        
        # Default to gpt-4o-mini which has 128k context and is cost-effective
        return "gpt-4o-mini"
    
    def _trim_conversation_history(self, messages: List[Any], max_messages: int = 10) -> List[Any]:
        """Trim conversation history to prevent context overflow."""
        if len(messages) <= max_messages:
            return messages
        
        # Keep the system message if present, then the last N messages
        trimmed = []
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'system':
                trimmed.append(msg)
                break
            elif isinstance(msg, dict) and msg.get('role') == 'system':
                trimmed.append(msg)
                break
        
        # Add the most recent messages
        trimmed.extend(messages[-(max_messages):])
        return trimmed

    def _load_api_key(self) -> Optional[str]:
        """Load OpenAI API key from various sources."""
        # Try config first
        if self.config.agent.api_key:
            return self.config.agent.api_key
        
        # Try environment variable
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return api_key
        
        # Try .env file
        api_key = self._load_api_key_from_env()
        if api_key:
            return api_key
        
        return None

    def _load_api_key_from_env(self) -> Optional[str]:
        """Load API key from .env file."""
        try:
            from dotenv import load_dotenv
            config_dir = self.config_manager.config_dir
            env_file = config_dir / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                return os.environ.get("OPENAI_API_KEY")
        except Exception:
            pass
        return None

    def _prompt_for_openai_key(self) -> str:
        """Prompt user for OpenAI API key."""
        print("\n🔑 OpenAI API Key Required")
        print("SysAgent needs an OpenAI API key to provide intelligent assistance.")
        print("Get a free API key from: https://platform.openai.com/api-keys\n")
        
        api_key = input("Enter your OpenAI API key: ").strip()
        if api_key:
            self._save_api_key_to_env(api_key)
            return api_key
        else:
            raise ValueError("API key is required")

    def _save_api_key_to_env(self, api_key: str):
        """Save API key to .env file."""
        try:
            config_dir = self.config_manager.config_dir
            config_dir.mkdir(parents=True, exist_ok=True)
            env_file = config_dir / ".env"
            
            with open(env_file, "w") as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")
            
            print("✓ API key saved to environment")
        except Exception as e:
            print(f"Warning: Could not save API key: {e}")

    def _create_langgraph_tools(self):
        """Create LangGraph-compatible tools with permission checking."""
        tools = []

        # File operations tool
        @tool
        def file_operations(action: str, path: str = None, content: str = None) -> str:
            """Perform file system operations (list, read, write, delete files and directories)."""
            try:
                if self.debug:
                    print(f"DEBUG: file_operations tool called with action={action}, path={path}")
                
                # Check permissions
                if not self.permission_manager.has_permission("file_access"):
                    # Return a special message that will be handled by the CLI
                    return "PERMISSION_REQUEST:file_access:file_operations:Permission required for file system access:Grant permission for file operations? (y/n): "
                
                result = self.tool_executor.execute_tool("file_tool", action=action, path=path, content=content)
                
                if self.debug:
                    print(f"DEBUG: file_operations result = {result}")
                
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                if self.debug:
                    print(f"DEBUG: file_operations exception = {e}")
                
                # Check if this is an interrupt exception
                from langgraph.types import Interrupt
                if isinstance(e, tuple) and len(e) > 0 and isinstance(e[0], Interrupt):
                    interrupt = e[0]
                    # Return the interrupt data so it can be handled by the CLI
                    import json
                    return f"INTERRUPT:{json.dumps(interrupt.value)}"
                elif isinstance(e, Interrupt):
                    # Direct interrupt exception
                    import json
                    return f"INTERRUPT:{json.dumps(e.value)}"
                
                return f"Error performing file operations: {str(e)}"

        # System info tool
        @tool
        def system_info(action: str = "general") -> str:
            """Get system information and metrics (CPU, memory, disk usage, OS info)."""
            try:
                if self.debug:
                    print(f"DEBUG: system_info tool called with action={action}")
                
                # Check permissions
                if not self.permission_manager.has_permission("system_info"):
                    # Return a special message that will be handled by the CLI
                    return "PERMISSION_REQUEST:system_info:system_info:Permission required for system information access:Grant permission for system information access? (y/n): "
                
                result = self.tool_executor.execute_tool("system_info_tool", action=action)
                
                if self.debug:
                    print(f"DEBUG: system_info result = {result}")
                
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                if self.debug:
                    print(f"DEBUG: system_info exception = {e}")
                
                # Check if this is an interrupt exception
                from langgraph.types import Interrupt
                if isinstance(e, tuple) and len(e) > 0 and isinstance(e[0], Interrupt):
                    interrupt = e[0]
                    # Return the interrupt data so it can be handled by the CLI
                    import json
                    return f"INTERRUPT:{json.dumps(interrupt.value)}"
                elif isinstance(e, Interrupt):
                    # Direct interrupt exception
                    import json
                    return f"INTERRUPT:{json.dumps(e.value)}"
                
                return f"Error getting system info: {str(e)}"

        # Process management tool
        @tool
        def process_management(action: str, pid: int = None, name: str = None) -> str:
            """Manage system processes (list, kill, monitor processes)."""
            try:
                # Check permissions
                if not self.permission_manager.has_permission("process_management"):
                    # Use interrupt to ask for permission
                    permission_granted = interrupt(f"Permission required for process management. Grant permission? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes', 'grant', 'allow']:
                        self.permission_manager.grant_permission("process_management")
                    else:
                        return "Permission denied for process management"
                
                result = self.tool_executor.execute_tool("process_tool", action=action, pid=pid, name=name)
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                return f"Error performing process management: {str(e)}"

        # Network diagnostics tool
        @tool
        def network_diagnostics(action: str, host: str = None, port: int = None) -> str:
            """Perform network diagnostics (ping, port scan, connectivity tests)."""
            try:
                # Check permissions
                if not self.permission_manager.has_permission("network_access"):
                    # Use interrupt to ask for permission
                    permission_granted = interrupt(f"Permission required for network diagnostics. Grant permission? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes', 'grant', 'allow']:
                        self.permission_manager.grant_permission("network_access")
                    else:
                        return "Permission denied for network diagnostics"
                
                result = self.tool_executor.execute_tool("network_tool", action=action, host=host, port=port)
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                return f"Error performing network diagnostics: {str(e)}"

        # System control tool
        @tool
        def system_control(action: str, service_name: str = None, command: str = None) -> str:
            """Control system services, power management, user management, and system configuration."""
            try:
                # Check permissions
                if not self.permission_manager.has_permission("system_control"):
                    # Use interrupt to ask for permission
                    permission_granted = interrupt(f"Permission required for system control. Grant permission? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes', 'grant', 'allow']:
                        self.permission_manager.grant_permission("system_control")
                    else:
                        return "Permission denied for system control"
                
                result = self.tool_executor.execute_tool("system_control_tool", action=action, service_name=service_name, command=command)
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                return f"Error performing system control: {str(e)}"

        # Code generation tool
        @tool
        def generate_code(description: str, language: str = "python") -> str:
            """Generate and execute Python code for custom solutions when no specific tool exists."""
            try:
                # Check permissions
                if not self.permission_manager.has_permission("code_execution"):
                    # Use interrupt to ask for permission
                    permission_granted = interrupt(f"Permission required for code execution. Grant permission? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes', 'grant', 'allow']:
                        self.permission_manager.grant_permission("code_execution")
                    else:
                        return "Permission denied for code execution"
                
                result = self.tool_executor.execute_tool("code_generation_tool", description=description, language=language)
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                return f"Error generating code: {str(e)}"

        # Security operations tool
        @tool
        def security_operations(action: str, target: str = None) -> str:
            """Perform security audits, vulnerability scanning, and security monitoring."""
            try:
                # Check permissions
                if not self.permission_manager.has_permission("security_operations"):
                    # Use interrupt to ask for permission
                    permission_granted = interrupt(f"Permission required for security operations. Grant permission? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes', 'grant', 'allow']:
                        self.permission_manager.grant_permission("security_operations")
                    else:
                        return "Permission denied for security operations"
                
                result = self.tool_executor.execute_tool("security_tool", action=action, target=target)
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                return f"Error performing security operations: {str(e)}"

        # Automation operations tool
        @tool
        def automation_operations(action: str, name: str = None, command: str = None, schedule: str = None) -> str:
            """Schedule tasks, create workflows, and automate system operations."""
            try:
                # Check permissions
                if not self.permission_manager.has_permission("automation_operations"):
                    # Use interrupt to ask for permission
                    permission_granted = interrupt(f"Permission required for automation operations. Grant permission? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes', 'grant', 'allow']:
                        self.permission_manager.grant_permission("automation_operations")
                    else:
                        return "Permission denied for automation operations"
                
                result = self.tool_executor.execute_tool("automation_tool", action=action, name=name, command=command, schedule=schedule)
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                return f"Error performing automation operations: {str(e)}"

        # Monitoring operations tool
        @tool
        def monitoring_operations(action: str, name: str = None, condition: str = None, threshold: float = None) -> str:
            """Monitor system resources, performance metrics, and create alerts."""
            try:
                # Check permissions
                if not self.permission_manager.has_permission("monitoring_operations"):
                    # Use interrupt to ask for permission
                    permission_granted = interrupt(f"Permission required for monitoring operations. Grant permission? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes', 'grant', 'allow']:
                        self.permission_manager.grant_permission("monitoring_operations")
                    else:
                        return "Permission denied for monitoring operations"
                
                result = self.tool_executor.execute_tool("monitoring_tool", action=action, name=name, condition=condition, threshold=threshold)
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                return f"Error performing monitoring operations: {str(e)}"

        # OS Intelligence tool
        @tool
        def os_intelligence(action: str, target: str = None, analysis_depth: str = "comprehensive",
                           optimization_level: str = "balanced") -> str:
            """Advanced OS-level intelligence, predictive analysis, smart automation, and system optimization."""
            try:
                # Check permissions
                if not self.permission_manager.has_permission("low_level_os"):
                    # Use interrupt to ask for permission
                    permission_granted = interrupt(f"Permission required for OS intelligence. Grant permission? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes', 'grant', 'allow']:
                        self.permission_manager.grant_permission("low_level_os")
                    else:
                        return "Permission denied for OS intelligence"
                
                params = {"action": action}
                if target:
                    params["target"] = target
                if analysis_depth:
                    params["analysis_depth"] = analysis_depth
                if optimization_level:
                    params["optimization_level"] = optimization_level
                
                result = self.tool_executor.execute_tool("os_intelligence_tool", **params)
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                return f"Error performing OS intelligence operations: {str(e)}"

        # Low-level OS tool
        @tool
        def low_level_os(action: str, target: str = None, interface: str = None,
                         system_call: str = None, hardware_component: str = None) -> str:
            """Direct low-level OS access, system calls, kernel interfaces, and real-time hardware data."""
            try:
                # Check permissions
                if not self.permission_manager.has_permission("low_level_os"):
                    # Use interrupt to ask for permission
                    permission_granted = interrupt(f"Permission required for low-level OS access. Grant permission? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes', 'grant', 'allow']:
                        self.permission_manager.grant_permission("low_level_os")
                    else:
                        return "Permission denied for low-level OS access"
                
                params = {"action": action}
                if target:
                    params["target"] = target
                if interface:
                    params["interface"] = interface
                if system_call:
                    params["system_call"] = system_call
                if hardware_component:
                    params["hardware_component"] = hardware_component
                
                result = self.tool_executor.execute_tool("low_level_os_tool", **params)
                if result.success:
                    return str(result.data)
                else:
                    return f"Error: {result.error}"
            except Exception as e:
                return f"Error performing low-level OS operations: {str(e)}"

        # Document operations tool
        @tool
        def document_operations(action: str, path: str = None, content: str = None, 
                               title: str = None, template: str = None) -> str:
            """Create and manage documents, notes, and text files. Actions: create, create_note, edit, read, open, list_notes, search_notes, create_from_template."""
            try:
                if not self.permission_manager.has_permission("file_access"):
                    return "PERMISSION_REQUEST:file_access:document_operations:Permission required for document access"
                
                params = {"action": action}
                if path: params["path"] = path
                if content: params["content"] = content
                if title: params["title"] = title
                if template: params["template"] = template
                
                result = self.tool_executor.execute_tool("document_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error with documents: {str(e)}"

        # Spreadsheet operations tool
        @tool
        def spreadsheet_operations(action: str, path: str = None, headers: list = None,
                                   data: list = None, template: str = None, title: str = None) -> str:
            """Create and manage spreadsheets (Excel/CSV). Actions: create, create_excel, read, write_row, create_data_entry, create_template (budget/inventory/timesheet/contacts/expenses)."""
            try:
                if not self.permission_manager.has_permission("file_access"):
                    return "PERMISSION_REQUEST:file_access:spreadsheet_operations:Permission required for spreadsheet access"
                
                params = {"action": action}
                if path: params["path"] = path
                if headers: params["headers"] = headers
                if data: params["data"] = data
                if template: params["template"] = template
                if title: params["title"] = title
                
                result = self.tool_executor.execute_tool("spreadsheet_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error with spreadsheet: {str(e)}"

        # Application control tool
        @tool
        def app_control(action: str, app_name: str = None, path: str = None) -> str:
            """Launch, close, and manage applications. Actions: launch, close, list, list_running, focus, info, find."""
            try:
                if not self.permission_manager.has_permission("app_control"):
                    permission_granted = interrupt("Permission required for app control. Grant? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes']:
                        self.permission_manager.grant_permission("app_control")
                    else:
                        return "Permission denied"
                
                params = {"action": action}
                if app_name: params["app_name"] = app_name
                if path: params["path"] = path
                
                result = self.tool_executor.execute_tool("app_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error with app control: {str(e)}"

        # Clipboard tool
        @tool
        def clipboard_operations(action: str, text: str = None) -> str:
            """Clipboard operations. Actions: copy, paste, clear, history."""
            try:
                if not self.permission_manager.has_permission("clipboard"):
                    permission_granted = interrupt("Permission required for clipboard. Grant? (y/n): ")
                    if permission_granted.lower() in ['y', 'yes']:
                        self.permission_manager.grant_permission("clipboard")
                    else:
                        return "Permission denied"
                
                params = {"action": action}
                if text: params["text"] = text
                
                result = self.tool_executor.execute_tool("clipboard_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error with clipboard: {str(e)}"

        # Browser control tool
        @tool
        def browser_control(action: str, url: str = None, browser: str = None, query: str = None) -> str:
            """Control web browsers. Actions: open, search, close, list_browsers, get_bookmarks."""
            try:
                params = {"action": action}
                if url: params["url"] = url
                if browser: params["browser"] = browser
                if query: params["query"] = query
                
                result = self.tool_executor.execute_tool("browser_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Window management tool
        @tool
        def window_control(action: str, app: str = None, x: int = None, y: int = None, 
                          width: int = None, height: int = None) -> str:
            """Manage windows. Actions: list, focus, minimize, maximize, tile_left, tile_right, resize, move, close."""
            try:
                params = {"action": action}
                if app: params["app"] = app
                if x is not None: params["x"] = x
                if y is not None: params["y"] = y
                if width: params["width"] = width
                if height: params["height"] = height
                
                result = self.tool_executor.execute_tool("window_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Media control tool
        @tool
        def media_control(action: str, level: int = None) -> str:
            """Control audio/media. Actions: volume, mute, unmute, play_pause, next, previous, get_volume."""
            try:
                params = {"action": action}
                if level is not None: params["level"] = level
                
                result = self.tool_executor.execute_tool("media_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Notification tool
        @tool
        def send_notification(title: str = "SysAgent", message: str = "") -> str:
            """Send system notification."""
            try:
                result = self.tool_executor.execute_tool("notification_tool", action="send", title=title, message=message)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Git operations tool
        @tool
        def git_operations(action: str, message: str = None, branch: str = None, 
                          url: str = None, path: str = None) -> str:
            """Git version control. Actions: status, clone, pull, push, commit, add, branch, checkout, log."""
            try:
                params = {"action": action}
                if message: params["message"] = message
                if branch: params["branch"] = branch
                if url: params["url"] = url
                if path: params["path"] = path
                
                result = self.tool_executor.execute_tool("git_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # API/HTTP requests tool
        @tool
        def http_request(action: str, url: str, data: str = None, headers: str = None) -> str:
            """Make HTTP requests. Actions: get, post, put, delete, download."""
            try:
                import json as json_lib
                params = {"action": action, "url": url}
                if data:
                    try:
                        params["json"] = json_lib.loads(data)
                    except:
                        params["data"] = data
                if headers:
                    try:
                        params["headers"] = json_lib.loads(headers)
                    except:
                        pass
                
                result = self.tool_executor.execute_tool("api_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Package manager tool
        @tool
        def package_manager(action: str, package: str = None, query: str = None) -> str:
            """Manage software packages. Actions: install, uninstall, update, upgrade, search, list."""
            try:
                params = {"action": action}
                if package: params["package"] = package
                if query: params["query"] = query
                
                result = self.tool_executor.execute_tool("package_manager_tool", **params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Workflow tool
        @tool
        def workflow_operations(action: str, name: str = None, steps: list = None, 
                                template: str = None, tool: str = None, params: dict = None) -> str:
            """Create and run multi-step automated workflows. Actions: create, run, list, get, templates, create_from_template, add_step."""
            try:
                tool_params = {"action": action}
                if name: tool_params["name"] = name
                if steps: tool_params["steps"] = steps
                if template: tool_params["template"] = template
                if tool: tool_params["tool"] = tool
                if params: tool_params["params"] = params
                
                result = self.tool_executor.execute_tool("workflow_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Smart search tool
        @tool
        def smart_search(action: str, query: str = None, path: str = None, 
                        limit: int = None, file_type: str = None) -> str:
            """Unified search across files, apps, web, commands. Actions: search, files, apps, web, content, recent, commands, history."""
            try:
                tool_params = {"action": action}
                if query: tool_params["query"] = query
                if path: tool_params["path"] = path
                if limit: tool_params["limit"] = limit
                if file_type: tool_params["type"] = file_type
                
                result = self.tool_executor.execute_tool("smart_search_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # System insights tool
        @tool
        def system_insights(action: str, path: str = None) -> str:
            """AI-powered system analysis and recommendations. Actions: health_check, performance, recommendations, security_scan, resource_hogs, startup_analysis, storage_analysis, network_analysis, optimize, quick_insights."""
            try:
                tool_params = {"action": action}
                if path: tool_params["path"] = path
                
                result = self.tool_executor.execute_tool("system_insights_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Context memory tool
        @tool
        def context_memory(action: str, key: str = None, value: str = None, 
                          category: str = None, name: str = None, command: str = None) -> str:
            """Remember preferences and context. Actions: remember, recall, forget, preferences, set_preference, favorites, add_favorite, suggest, history."""
            try:
                tool_params = {"action": action}
                if key: tool_params["key"] = key
                if value: tool_params["value"] = value
                if category: tool_params["category"] = category
                if name: tool_params["name"] = name
                if command: tool_params["command"] = command
                
                result = self.tool_executor.execute_tool("context_memory_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Keyboard and mouse control tool
        @tool
        def keyboard_mouse(action: str, text: str = None, key: str = None, 
                          shortcut: str = None, x: int = None, y: int = None,
                          direction: str = None, amount: int = None) -> str:
            """Control keyboard and mouse input. Actions: type (text), key (single key), hotkey (shortcut like cmd+c), click, double_click, right_click, move, scroll, drag, get_position."""
            try:
                if not self.permission_manager.has_permission("input_control"):
                    return "PERMISSION_REQUEST:input_control:keyboard_mouse:Permission required for keyboard/mouse control"
                
                tool_params = {"action": action}
                if text: tool_params["text"] = text
                if key: tool_params["key"] = key
                if shortcut: tool_params["shortcut"] = shortcut
                if x is not None: tool_params["x"] = x
                if y is not None: tool_params["y"] = y
                if direction: tool_params["direction"] = direction
                if amount: tool_params["amount"] = amount
                
                result = self.tool_executor.execute_tool("keyboard_mouse_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Screenshot tool
        @tool
        def take_screenshot(action: str = "capture", path: str = None, 
                           region: str = None, window: str = None) -> str:
            """Capture screenshots. Actions: capture (full screen), region (area), window (specific window), list_windows. Saves to path or returns base64."""
            try:
                if not self.permission_manager.has_permission("screenshot"):
                    return "PERMISSION_REQUEST:screenshot:take_screenshot:Permission required for screenshots"
                
                tool_params = {"action": action}
                if path: tool_params["path"] = path
                if region: tool_params["region"] = region
                if window: tool_params["window"] = window
                
                result = self.tool_executor.execute_tool("screenshot_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Scheduler tool
        @tool
        def schedule_task(action: str, name: str = None, command: str = None,
                         schedule: str = None, time: str = None) -> str:
            """Schedule tasks and reminders. Actions: create, list, delete, run_once. Schedule formats: 'daily 9:00', 'hourly', 'every 5 minutes', 'cron 0 9 * * *'."""
            try:
                tool_params = {"action": action}
                if name: tool_params["name"] = name
                if command: tool_params["command"] = command
                if schedule: tool_params["schedule"] = schedule
                if time: tool_params["time"] = time
                
                result = self.tool_executor.execute_tool("scheduler_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Service management tool
        @tool
        def service_control(action: str, name: str = None) -> str:
            """Manage system services. Actions: list, status, start, stop, restart, enable, disable."""
            try:
                if not self.permission_manager.has_permission("system_control"):
                    return "PERMISSION_REQUEST:system_control:service_control:Permission required for service management"
                
                tool_params = {"action": action}
                if name: tool_params["name"] = name
                
                result = self.tool_executor.execute_tool("service_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Email tool
        @tool
        def send_email(action: str = "send", to: str = None, subject: str = None,
                      body: str = None, attachment: str = None) -> str:
            """Send emails. Actions: send, draft, list_drafts. Supports attachments."""
            try:
                if not self.permission_manager.has_permission("email"):
                    return "PERMISSION_REQUEST:email:send_email:Permission required for email access"
                
                tool_params = {"action": action}
                if to: tool_params["to"] = to
                if subject: tool_params["subject"] = subject
                if body: tool_params["body"] = body
                if attachment: tool_params["attachment"] = attachment
                
                result = self.tool_executor.execute_tool("email_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Voice tool
        @tool
        def voice_control(action: str, text: str = None) -> str:
            """Voice input/output. Actions: speak (text-to-speech), listen (speech-to-text), dictate."""
            try:
                tool_params = {"action": action}
                if text: tool_params["text"] = text
                
                result = self.tool_executor.execute_tool("voice_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Auth/credentials tool
        @tool
        def credentials_manager(action: str, service: str = None, 
                               username: str = None, password: str = None) -> str:
            """Manage credentials securely. Actions: store, retrieve, delete, list."""
            try:
                if not self.permission_manager.has_permission("credentials"):
                    return "PERMISSION_REQUEST:credentials:credentials_manager:Permission required for credential access"
                
                tool_params = {"action": action}
                if service: tool_params["service"] = service
                if username: tool_params["username"] = username
                if password: tool_params["password"] = password
                
                result = self.tool_executor.execute_tool("auth_tool", **tool_params)
                return str(result.data) if result.success else f"Error: {result.error}"
            except Exception as e:
                return f"Error: {str(e)}"

        tools.extend([
            file_operations, system_info, process_management, network_diagnostics, 
            system_control, generate_code, security_operations, automation_operations, 
            monitoring_operations, os_intelligence, low_level_os,
            document_operations, spreadsheet_operations, app_control, clipboard_operations,
            browser_control, window_control, media_control, send_notification,
            git_operations, http_request, package_manager,
            workflow_operations, smart_search, system_insights, context_memory,
            # New comprehensive OS control tools
            keyboard_mouse, take_screenshot, schedule_task, service_control,
            send_email, voice_control, credentials_manager
        ])
        return tools

    def _register_tools_with_executor(self):
        """Register all tools with the ToolExecutor."""
        from ..tools import (
            FileTool, SystemInfoTool, ProcessTool, NetworkTool, 
            SystemControlTool, CodeGenerationTool, SecurityTool, 
            AutomationTool, MonitoringTool, OSIntelligenceTool, LowLevelOSTool,
            DocumentTool, SpreadsheetTool, AppTool, ClipboardTool,
            BrowserTool, WindowTool, MediaTool, NotificationTool,
            GitTool, APITool, PackageManagerTool,
            WorkflowTool, SmartSearchTool, SystemInsightsTool, ContextMemoryTool,
            KeyboardMouseTool, ScreenshotTool, SchedulerTool, ServiceTool,
            EmailTool, VoiceTool, AuthTool
        )
        
        # Register all tools for complete OS control
        tools_to_register = [
            # Core system tools
            FileTool(),
            SystemInfoTool(),
            ProcessTool(),
            NetworkTool(),
            SystemControlTool(),
            CodeGenerationTool(),
            SecurityTool(),
            AutomationTool(),
            MonitoringTool(),
            OSIntelligenceTool(),
            LowLevelOSTool(),
            # Document and data tools
            DocumentTool(),
            SpreadsheetTool(),
            # Application and UI control
            AppTool(),
            ClipboardTool(),
            BrowserTool(),
            WindowTool(),
            MediaTool(),
            NotificationTool(),
            # Input simulation
            KeyboardMouseTool(),
            ScreenshotTool(),
            VoiceTool(),
            # Development tools
            GitTool(),
            APITool(),
            PackageManagerTool(),
            # Automation and scheduling
            WorkflowTool(),
            SchedulerTool(),
            ServiceTool(),
            # Communication
            EmailTool(),
            # Memory and intelligence
            SmartSearchTool(),
            SystemInsightsTool(),
            ContextMemoryTool(),
            # Security
            AuthTool(),
        ]
        
        for tool in tools_to_register:
            self.tool_executor.register_tool(tool)

    def _create_react_agent(self):
        """Create the React agent using langgraph.prebuilt with checkpointer."""
        # Get context from long-term memory if available
        memory_context = ""
        if self.memory_manager:
            memory_context = self.memory_manager.get_system_context()
        
        system_prompt = f"""You are SysAgent, an AI that gives users COMPLETE control over their computer through natural language.
You can do ANYTHING the user normally does with keyboard and mouse - from Excel to browsers to system settings.

🎯 COMPLETE OS CONTROL - Your capabilities:

⌨️ INPUT CONTROL:
• keyboard_mouse(action="type", text="X") - Type any text
• keyboard_mouse(action="key", key="enter"|"tab"|"escape") - Press keys
• keyboard_mouse(action="hotkey", shortcut="cmd+c"|"ctrl+v") - Keyboard shortcuts
• keyboard_mouse(action="click", x=N, y=N) - Click anywhere
• keyboard_mouse(action="scroll", direction="up"|"down") - Scroll
• keyboard_mouse(action="move", x=N, y=N) - Move mouse

📱 APPLICATION CONTROL:
• app_control(action="launch"|"close"|"focus", app_name="X") - Open/close/switch apps
• window_control(action="tile_left"|"tile_right"|"maximize"|"minimize"|"resize") - Window management
• browser_control(action="open", url="X") or (action="search", query="X") - Web browsing

📊 SPREADSHEETS & DOCUMENTS:
• spreadsheet_operations(action="create_excel"|"create_template", template="budget"|"inventory") - Create Excel/CSV
• document_operations(action="create_note"|"create", content="X") - Create documents
• file_operations(action="read"|"write"|"list"|"delete", path="X") - File management

🎵 MEDIA & AUDIO:
• media_control(action="volume", level=50) - Set volume 0-100
• media_control(action="mute"|"unmute"|"play_pause"|"next"|"previous") - Media controls

📸 SCREEN & VISUAL:
• take_screenshot(action="capture", path="X") - Take screenshots
• clipboard_operations(action="copy"|"paste", text="X") - Clipboard control

📊 SYSTEM MONITORING:
• system_info(action="overview"|"cpu"|"memory"|"disk"|"battery") - Real-time stats
• system_insights(action="health_check"|"recommendations"|"resource_hogs") - AI analysis
• process_management(action="list"|"kill", name="X") - Process control

🌐 NETWORK & WEB:
• browser_control(action="open", url="X") - Open websites
• browser_control(action="search", query="X") - Search the web
• http_request(action="get"|"post", url="X") - API requests
• network_diagnostics(action="ping"|"ports", host="X") - Network tools

📧 COMMUNICATION:
• send_email(to="X", subject="Y", body="Z") - Send emails
• send_notification(title="X", message="Y") - System notifications
• voice_control(action="speak", text="X") - Text-to-speech

⏰ AUTOMATION:
• workflow_operations(action="run", name="morning_routine") - Run workflows
• schedule_task(action="create", command="X", schedule="daily 9:00") - Schedule tasks
• service_control(action="start"|"stop"|"restart", name="X") - Manage services

🔧 DEVELOPMENT:
• git_operations(action="status"|"commit"|"pull"|"push") - Git control
• package_manager(action="install"|"update", package="X") - Install software
• generate_code(description="X", language="python") - Code generation

🔍 SEARCH & MEMORY:
• smart_search(action="files"|"apps"|"content", query="X") - Find anything
• context_memory(action="remember"|"recall", key="X") - Remember preferences

EXAMPLES - Common user requests:
• "Open Excel" → app_control(action="launch", app_name="Excel")
• "Type hello world" → keyboard_mouse(action="type", text="hello world")
• "Press Ctrl+C" → keyboard_mouse(action="hotkey", shortcut="ctrl+c")
• "Click at 100, 200" → keyboard_mouse(action="click", x=100, y=200)
• "Set volume to 50%" → media_control(action="volume", level=50)
• "Take a screenshot" → take_screenshot(action="capture")
• "Open google.com" → browser_control(action="open", url="https://google.com")
• "Search for python tutorials" → browser_control(action="search", query="python tutorials")
• "Create a budget spreadsheet" → spreadsheet_operations(action="create_template", template="budget")
• "Show system status" → system_info(action="overview")
• "What's using my CPU" → system_insights(action="resource_hogs")
• "Tile windows left and right" → window_control(action="tile_left") then (action="tile_right")

RULES:
1. ALWAYS call a tool - you CAN do anything the user asks
2. For keyboard/mouse operations, use keyboard_mouse tool
3. For app control, use app_control or browser_control
4. Be fast and responsive - one action at a time
5. Confirm sensitive operations (delete files, system changes)

{memory_context}"""

        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt,
            checkpointer=self.checkpointer
        )

    def process_command(self, user_input) -> Dict[str, Any]:
        """Process a command synchronously with memory and middleware support."""
        try:
            # Check if this is a Command object for resuming interrupts
            from langgraph.types import Command
            if isinstance(user_input, Command):
                # Resume from interrupt with thread config
                config = {"configurable": {"thread_id": self.thread_id}}
                result = self.agent.invoke(user_input, config=config)
            else:
                # Add to short-term memory
                if self.memory_manager:
                    self.memory_manager.add_message("user", user_input)
                
                # Get messages from memory for context
                if self.memory_manager:
                    messages = self.memory_manager.get_messages_for_llm()
                    # Ensure the latest message is included
                    if not messages or messages[-1].get("content") != user_input:
                        messages.append({"role": "user", "content": user_input})
                else:
                    messages = [{"role": "user", "content": user_input}]
                
                # Thread config for checkpointing
                config = {"configurable": {"thread_id": self.thread_id}}
                
                # Run the React agent with checkpointer
                result = self.agent.invoke({"messages": messages}, config=config)
            
            # Check for interrupts (human-in-the-loop)
            if result.get('__interrupt__'):
                interrupt_data = result['__interrupt__']
                
                # Handle via middleware if available
                if self.middleware and not self.auto_approve:
                    # Create approval request
                    for interrupt_item in interrupt_data:
                        if hasattr(interrupt_item, 'value'):
                            request = self.middleware.request_approval(
                                ApprovalType.CONFIRMATION,
                                "Agent Confirmation",
                                str(interrupt_item.value),
                                {"interrupt": interrupt_item}
                            )
                            # Wait for response
                            status = self.middleware.wait_for_approval(request, blocking=False)
                
                return {
                    "success": False,
                    "message": "Waiting for approval",
                    "data": result,
                    "__interrupt__": interrupt_data,
                    "tools_used": result.get("tools_used", []),
                    "needs_approval": True
                }
            
            # Extract the response
            ai_response = self._extract_response(result)
            
            # Add to short-term memory
            if self.memory_manager:
                self.memory_manager.add_message("assistant", ai_response)
            
            return {
                "success": True,
                "message": ai_response,
                "data": {},  # Don't return full result to avoid memory issues
                "tools_used": result.get("tools_used", [])
            }
                
        except Exception as e:
            error_msg = str(e)
            # Provide helpful error for context length issues
            if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                # Clear memory and retry
                if self.memory_manager:
                    self.memory_manager.clear_session()
                self.thread_id = str(uuid.uuid4())  # New thread
                return {
                    "success": False,
                    "message": "The conversation got too long. Starting fresh. Please try your request again.",
                    "data": {},
                    "tools_used": []
                }
            return {
                "success": False,
                "message": f"Error processing command: {error_msg}",
                "data": {},
                "tools_used": []
            }

    def _extract_response(self, result: Dict[str, Any]) -> str:
        """Extract the AI response from the result."""
        if "messages" in result and result["messages"]:
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content') and hasattr(msg, 'type') and msg.type == "ai":
                    if msg.content:  # Skip empty messages (tool calls)
                        return msg.content
                elif isinstance(msg, dict) and msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    if content:
                        return content
        return "Command processed successfully"

    def process_command_streaming(self, user_input: str) -> Generator[Dict[str, Any], None, None]:
        """Process a command with realtime streaming output. Yields events as they arrive."""
        try:
            # Add to short-term memory
            if self.memory_manager:
                self.memory_manager.add_message("user", user_input)
            
            # Get messages from memory
            if self.memory_manager:
                messages = self.memory_manager.get_messages_for_llm()
                if not messages or messages[-1].get("content") != user_input:
                    messages.append({"role": "user", "content": user_input})
            else:
                messages = [{"role": "user", "content": user_input}]
            
            # Thread config for checkpointing
            config = {"configurable": {"thread_id": self.thread_id}}
            
            full_response = ""
            tool_calls_made = []
            
            # Use stream method for realtime output
            for chunk in self.agent.stream({"messages": messages}, config=config, stream_mode="updates"):
                # Handle different chunk types
                for node_name, node_output in chunk.items():
                    if node_name == "agent":
                        # Agent node - contains AI messages and tool calls
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                # AI content
                                if hasattr(msg, 'content') and msg.content:
                                    yield {"type": "token", "content": msg.content}
                                    full_response = msg.content
                                
                                # Tool calls
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        tool_name = tc.get("name", "unknown")
                                        tool_calls_made.append(tool_name)
                                        yield {
                                            "type": "tool_call",
                                            "name": tool_name,
                                            "args": tc.get("args", {})
                                        }
                                        
                                        # Record tool usage in memory
                                        if self.memory_manager:
                                            self.memory_manager.long_term.record_tool_usage(tool_name)
                    
                    elif node_name == "tools":
                        # Tool execution results
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                if hasattr(msg, 'content'):
                                    # Check for permission requests
                                    content = str(msg.content)
                                    if content.startswith("PERMISSION_REQUEST:"):
                                        parts = content.split(":")
                                        if len(parts) >= 4:
                                            yield {
                                                "type": "permission_request",
                                                "permission": parts[1],
                                                "tool": parts[2],
                                                "reason": parts[3]
                                            }
                                    else:
                                        yield {
                                            "type": "tool_result",
                                            "content": content[:500] if len(content) > 500 else content
                                        }
                    
                    elif node_name == "__interrupt__":
                        # Human-in-the-loop interrupt
                        yield {
                            "type": "interrupt",
                            "data": node_output
                        }
            
            # Add assistant response to memory
            if self.memory_manager and full_response:
                self.memory_manager.add_message("assistant", full_response, {"tools": tool_calls_made})
            
            yield {"type": "done", "tools_used": tool_calls_made}
            
        except Exception as e:
            error_msg = str(e)
            if "context_length_exceeded" in error_msg:
                if self.memory_manager:
                    self.memory_manager.clear_session()
                self.thread_id = str(uuid.uuid4())
                yield {"type": "error", "content": "Conversation too long. Please try again."}
            else:
                yield {"type": "error", "content": error_msg}
    
    def resume_from_interrupt(self, approved: bool, response_value: Any = None) -> Dict[str, Any]:
        """Resume agent execution after human-in-the-loop interrupt."""
        try:
            from langgraph.types import Command
            
            # Create resume command
            if approved:
                resume_value = response_value if response_value else "approved"
            else:
                resume_value = "denied"
            
            # Resume with the response
            config = {"configurable": {"thread_id": self.thread_id}}
            result = self.agent.invoke(
                Command(resume=resume_value),
                config=config
            )
            
            ai_response = self._extract_response(result)
            
            # Add to memory
            if self.memory_manager:
                self.memory_manager.add_message("assistant", ai_response)
            
            return {
                "success": True,
                "message": ai_response,
                "data": {},
                "tools_used": []
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error resuming: {str(e)}",
                "data": {},
                "tools_used": []
            }
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get pending approval requests from middleware."""
        if self.middleware:
            requests = self.middleware.get_pending_requests()
            return [
                {
                    "id": r.id,
                    "type": r.type.value,
                    "title": r.title,
                    "description": r.description,
                    "options": r.options
                }
                for r in requests
            ]
        return []
    
    def respond_to_approval(self, request_id: str, approved: bool, remember: bool = False):
        """Respond to an approval request."""
        if self.middleware:
            self.middleware.respond_to_request(request_id, approved, remember=remember)

    async def process_command_async(self, user_input: str) -> Dict[str, Any]:
        """Process a command asynchronously (for compatibility)."""
        return self.process_command(user_input)

    def get_conversation_history(self, session_id: str = None) -> List[Dict[str, Any]]:
        """Get conversation history from memory."""
        if self.memory_manager:
            return self.memory_manager.get_messages_for_llm()
        return []

    def clear_conversation_history(self, session_id: str = None):
        """Clear conversation history and start fresh."""
        self.session_id = str(int(time.time()))
        self.thread_id = str(uuid.uuid4())
        if self.memory_manager:
            self.memory_manager.clear_session()
        if self.middleware:
            self.middleware.clear_session_approvals()
    
    def new_session(self):
        """Start a completely new session."""
        self.session_id = str(int(time.time()))
        self.thread_id = str(uuid.uuid4())
        if self.memory_manager:
            self.memory_manager.clear_session()
        if self.middleware:
            self.middleware.clear_session_approvals()
    
    def remember(self, key: str, value: Any, category: str = "general"):
        """Remember something in long-term memory."""
        if self.memory_manager:
            self.memory_manager.remember(key, value, category)
    
    def recall(self, key: str) -> Optional[Any]:
        """Recall something from long-term memory."""
        if self.memory_manager:
            return self.memory_manager.recall(key)
        return None
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        if self.memory_manager:
            self.memory_manager.set_preference(key, value)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        if self.memory_manager:
            return self.memory_manager.get_preference(key, default)
        return default
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation."""
        if self.memory_manager:
            return self.memory_manager.get_summary()
        return "No conversation history."
    
    def set_auto_approve(self, enabled: bool):
        """Enable/disable auto-approve for human-in-the-loop."""
        self.auto_approve = enabled
        if self.middleware:
            self.middleware.auto_approve = enabled
    
    # === Advanced Human-in-the-Loop Features ===
    
    def add_breakpoint(
        self,
        bp_type: str = "before_tool",
        tool_name: str = None,
        condition: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a breakpoint to pause execution.
        
        Types: before_tool, after_tool, on_error, on_sensitive, periodic, conditional
        """
        if not MIDDLEWARE_AVAILABLE or not self.middleware:
            return None
        
        bp_type_enum = {
            "before_tool": BreakpointType.BEFORE_TOOL,
            "after_tool": BreakpointType.AFTER_TOOL,
            "on_error": BreakpointType.ON_ERROR,
            "on_sensitive": BreakpointType.ON_SENSITIVE,
            "periodic": BreakpointType.PERIODIC,
            "conditional": BreakpointType.CONDITIONAL,
            "manual": BreakpointType.MANUAL,
        }.get(bp_type, BreakpointType.BEFORE_TOOL)
        
        bp = self.middleware.add_breakpoint(bp_type_enum, tool_name, condition)
        return {"id": bp.id, "type": bp.type.value, "enabled": bp.enabled}
    
    def remove_breakpoint(self, bp_id: str) -> bool:
        """Remove a breakpoint."""
        if self.middleware:
            return self.middleware.remove_breakpoint(bp_id)
        return False
    
    def get_breakpoints(self) -> List[Dict[str, Any]]:
        """Get all breakpoints."""
        if self.middleware:
            return [
                {"id": bp.id, "type": bp.type.value, "enabled": bp.enabled, "hit_count": bp.hit_count}
                for bp in self.middleware.get_breakpoints()
            ]
        return []
    
    def pause_execution(self):
        """Pause agent execution."""
        if self.middleware:
            self.middleware.pause()
    
    def resume_execution(self):
        """Resume agent execution."""
        if self.middleware:
            self.middleware.resume()
    
    def is_paused(self) -> bool:
        """Check if agent is paused."""
        if self.middleware:
            return self.middleware.is_paused()
        return False
    
    # === Time-Travel / State Management ===
    
    def save_state_snapshot(self, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Save current state for time-travel."""
        if not self.middleware or not self.memory_manager:
            return None
        
        messages = self.memory_manager.get_messages_for_llm()
        snapshot = self.middleware.save_state(messages, metadata=metadata)
        return snapshot.id
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get state snapshot history."""
        if self.middleware:
            return [
                {
                    "id": s.id,
                    "step": s.step_number,
                    "timestamp": s.timestamp,
                    "message_count": len(s.messages),
                    "tools_used": s.tools_used
                }
                for s in self.middleware.get_state_history()
            ]
        return []
    
    def rollback_to_state(self, snapshot_id: str) -> bool:
        """Rollback to a previous state."""
        if not self.middleware:
            return False
        
        snapshot = self.middleware.rollback_to(snapshot_id)
        if snapshot and self.memory_manager:
            # Restore messages to memory
            self.memory_manager.clear_session()
            for msg in snapshot.messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                self.memory_manager.add_message(role, content)
            return True
        return False
    
    def rollback_steps(self, num_steps: int) -> bool:
        """Rollback by a number of steps."""
        if not self.middleware:
            return False
        
        snapshot = self.middleware.rollback_steps(num_steps)
        if snapshot and self.memory_manager:
            self.memory_manager.clear_session()
            for msg in snapshot.messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                self.memory_manager.add_message(role, content)
            return True
        return False
    
    # === Feedback Collection ===
    
    def submit_feedback(
        self,
        rating: int,
        comment: str = None,
        tool_name: str = None,
        tags: List[str] = None
    ) -> Optional[str]:
        """Submit feedback on agent actions."""
        if self.middleware:
            feedback = self.middleware.collect_feedback(
                rating=rating,
                comment=comment,
                tool_name=tool_name,
                tags=tags
            )
            return feedback.id
        return None
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get feedback summary."""
        if self.middleware:
            feedback_list = self.middleware.get_feedback()
            avg_rating = self.middleware.get_average_rating()
            return {
                "total_feedback": len(feedback_list),
                "average_rating": round(avg_rating, 2),
                "recent": [
                    {"rating": f.rating, "comment": f.comment, "tool": f.tool_name}
                    for f in feedback_list[-5:]
                ]
            }
        return {"total_feedback": 0, "average_rating": 0, "recent": []}
    
    def export_feedback(self, path: str = None) -> str:
        """Export all feedback to JSON."""
        if self.middleware:
            return self.middleware.export_feedback(path)
        return "[]"
    
    # === Dynamic Routing ===
    
    def redirect_with_instruction(self, new_instruction: str) -> Dict[str, Any]:
        """Redirect the agent with a new instruction."""
        if self.memory_manager:
            # Add the redirect as a user message
            self.memory_manager.add_message("user", f"[REDIRECT] {new_instruction}")
        
        # Process the new instruction
        return self.process_command(new_instruction)
    
    # === Review Actions ===
    
    def review_before_action(
        self,
        action_name: str,
        action_params: Dict[str, Any],
        editable_fields: List[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Request human review before executing an action.
        Returns (approved, possibly_modified_params).
        """
        if not self.middleware or self.auto_approve:
            return True, action_params
        
        return self.middleware.review_action(action_name, action_params, editable_fields)
    
    # === Approval Workflows ===
    
    def define_approval_workflow(self, name: str, steps: List[str]):
        """
        Define a multi-step approval workflow.
        Steps should be approval types: permission, confirmation, sensitive, execution, etc.
        """
        if self.middleware:
            step_types = []
            for step in steps:
                approval_type = {
                    "permission": ApprovalType.PERMISSION,
                    "confirmation": ApprovalType.CONFIRMATION,
                    "sensitive": ApprovalType.SENSITIVE_ACTION,
                    "execution": ApprovalType.EXECUTION,
                    "network": ApprovalType.NETWORK,
                    "file_write": ApprovalType.FILE_WRITE,
                    "review": ApprovalType.REVIEW,
                }.get(step, ApprovalType.CONFIRMATION)
                step_types.append(approval_type)
            self.middleware.define_workflow(name, step_types)
    
    def run_approval_workflow(
        self,
        workflow_name: str,
        title: str,
        description: str
    ) -> bool:
        """Run a multi-step approval workflow. Returns True if all steps approved."""
        if not self.middleware:
            return True
        
        requests = self.middleware.run_workflow(workflow_name, title, description)
        return all(r.status.value == "approved" for r in requests)
    
    # === Statistics ===
    
    def get_middleware_stats(self) -> Dict[str, Any]:
        """Get human-in-the-loop statistics."""
        if self.middleware:
            return self.middleware.get_stats()
        return {}
    
    # === Process with Breakpoint Support ===
    
    def process_command_with_breakpoints(
        self,
        user_input: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process command with breakpoint and state snapshot support.
        Yields events including breakpoint hits and state snapshots.
        """
        try:
            # Save initial state
            if self.middleware and self.memory_manager:
                self.middleware.save_state(
                    self.memory_manager.get_messages_for_llm(),
                    metadata={"input": user_input}
                )
            
            # Add to memory
            if self.memory_manager:
                self.memory_manager.add_message("user", user_input)
            
            # Get messages
            if self.memory_manager:
                messages = self.memory_manager.get_messages_for_llm()
                if not messages or messages[-1].get("content") != user_input:
                    messages.append({"role": "user", "content": user_input})
            else:
                messages = [{"role": "user", "content": user_input}]
            
            config = {"configurable": {"thread_id": self.thread_id}}
            full_response = ""
            tool_calls_made = []
            
            for chunk in self.agent.stream({"messages": messages}, config=config, stream_mode="updates"):
                # Check if paused
                if self.middleware and self.middleware.is_paused():
                    yield {"type": "paused", "message": "Execution paused by user"}
                    self.middleware.wait_if_paused()
                    yield {"type": "resumed", "message": "Execution resumed"}
                
                for node_name, node_output in chunk.items():
                    if node_name == "agent":
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                if hasattr(msg, 'content') and msg.content:
                                    yield {"type": "token", "content": msg.content}
                                    full_response = msg.content
                                
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        tool_name = tc.get("name", "unknown")
                                        
                                        # Check breakpoints before tool
                                        if self.middleware:
                                            bp = self.middleware.check_breakpoint(
                                                tool_name=tool_name,
                                                context={"tool": tool_name, "args": tc.get("args", {})}
                                            )
                                            if bp:
                                                yield {
                                                    "type": "breakpoint",
                                                    "breakpoint_id": bp.id,
                                                    "breakpoint_type": bp.type.value,
                                                    "tool": tool_name
                                                }
                                                # Wait if paused
                                                self.middleware.wait_if_paused()
                                        
                                        tool_calls_made.append(tool_name)
                                        yield {
                                            "type": "tool_call",
                                            "name": tool_name,
                                            "args": tc.get("args", {})
                                        }
                                        
                                        if self.memory_manager:
                                            self.memory_manager.long_term.record_tool_usage(tool_name)
                    
                    elif node_name == "tools":
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                if hasattr(msg, 'content'):
                                    content = str(msg.content)
                                    
                                    # Check for errors (trigger error breakpoint)
                                    is_error = content.startswith("Error") or "exception" in content.lower()
                                    if is_error and self.middleware:
                                        bp = self.middleware.check_breakpoint(is_error=True)
                                        if bp:
                                            yield {
                                                "type": "breakpoint",
                                                "breakpoint_id": bp.id,
                                                "breakpoint_type": "on_error",
                                                "error": content[:100]
                                            }
                                    
                                    if content.startswith("PERMISSION_REQUEST:"):
                                        parts = content.split(":")
                                        if len(parts) >= 4:
                                            yield {
                                                "type": "permission_request",
                                                "permission": parts[1],
                                                "tool": parts[2],
                                                "reason": parts[3]
                                            }
                                    else:
                                        yield {
                                            "type": "tool_result",
                                            "content": content[:500] if len(content) > 500 else content
                                        }
                    
                    elif node_name == "__interrupt__":
                        yield {"type": "interrupt", "data": node_output}
                
                # Save state after each chunk
                if self.middleware and self.memory_manager:
                    self.middleware.save_state(
                        self.memory_manager.get_messages_for_llm(),
                        tools_used=tool_calls_made
                    )
            
            # Add response to memory
            if self.memory_manager and full_response:
                self.memory_manager.add_message("assistant", full_response, {"tools": tool_calls_made})
            
            yield {"type": "done", "tools_used": tool_calls_made}
            
        except Exception as e:
            error_msg = str(e)
            
            # Check error breakpoint
            if self.middleware:
                bp = self.middleware.check_breakpoint(is_error=True)
                if bp:
                    yield {
                        "type": "breakpoint",
                        "breakpoint_id": bp.id,
                        "breakpoint_type": "on_error",
                        "error": error_msg
                    }
            
            if "context_length_exceeded" in error_msg:
                if self.memory_manager:
                    self.memory_manager.clear_session()
                self.thread_id = str(uuid.uuid4())
                yield {"type": "error", "content": "Conversation too long. Please try again."}
            else:
                yield {"type": "error", "content": error_msg}