"""
LangGraph-based agent for SysAgent CLI with human-in-the-loop capabilities.
"""

import asyncio
import os
import time
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt

from .config import ConfigManager
from .permissions import PermissionManager
from ..tools.base import ToolExecutor


class AgentState(TypedDict):
    """State for the LangGraph agent."""
    messages: List[Any]
    user_input: str
    tools_used: List[str]
    human_approval_needed: bool
    pending_action: Optional[Dict[str, Any]]
    session_context: Dict[str, Any]


class LangGraphAgent:
    """LangGraph-based agent with human-in-the-loop capabilities."""

    def __init__(self, config_manager: ConfigManager, permission_manager: PermissionManager, debug: bool = False):
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.permission_manager = permission_manager
        self.debug = debug
        self.tool_executor = ToolExecutor(permission_manager)
        self.session_id = str(int(time.time()))
        
        # Initialize memory for conversation history
        self.memory = MemorySaver()
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Create tools first
        self.tools = self._create_langgraph_tools()
        
        # Register tools with the executor
        self._register_tools_with_executor()
        
        # Create the React agent
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

        tools.extend([
            file_operations, system_info, process_management, network_diagnostics, 
            system_control, generate_code, security_operations, automation_operations, 
            monitoring_operations, os_intelligence, low_level_os,
            document_operations, spreadsheet_operations, app_control, clipboard_operations
        ])
        return tools

    def _register_tools_with_executor(self):
        """Register all tools with the ToolExecutor."""
        from ..tools import (
            FileTool, SystemInfoTool, ProcessTool, NetworkTool, 
            SystemControlTool, CodeGenerationTool, SecurityTool, 
            AutomationTool, MonitoringTool, OSIntelligenceTool, LowLevelOSTool,
            DocumentTool, SpreadsheetTool, AppTool, ClipboardTool
        )
        
        # Register all tools
        tools_to_register = [
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
            DocumentTool(),
            SpreadsheetTool(),
            AppTool(),
            ClipboardTool(),
        ]
        
        for tool in tools_to_register:
            self.tool_executor.register_tool(tool)

    def _create_react_agent(self):
        """Create the React agent using langgraph.prebuilt."""
        system_prompt = """You are SysAgent, an intelligent assistant that controls the operating system using natural language.

TOOLS AVAILABLE:
- file_operations: File system operations (list, read, write, delete)
- system_info: System metrics (CPU, memory, disk, OS info)
- process_management: Process control (list, kill, monitor)
- network_diagnostics: Network tools (ping, port scan, connectivity)
- system_control: Services, power, user management
- generate_code: Execute Python code for custom tasks
- security_operations: Security audits and monitoring
- automation_operations: Task scheduling and workflows
- monitoring_operations: Resource monitoring and alerts
- os_intelligence: Advanced OS analysis and optimization
- low_level_os: Low-level OS access and hardware data
- document_operations: Create/edit documents, notes, text files (use for Notepad, Notes, text docs)
- spreadsheet_operations: Create Excel/CSV files, data entry forms, budgets, inventories
- app_control: Launch/close applications (Excel, Notepad, browsers, etc.)
- clipboard_operations: Copy/paste clipboard operations

INSTRUCTIONS:
1. Use tools to get real system information - never make up data
2. For documents/notes: use document_operations (create_note for quick notes, create_from_template for meeting notes/todos)
3. For spreadsheets/Excel: use spreadsheet_operations (create_excel, create_data_entry, create_template)
4. To open apps: use app_control with action="launch" and app_name
5. Keep responses focused and use ONE tool at a time

COMMON TASKS:
- "Create a note" → document_operations(action="create_note", content="...", title="...")
- "Make an Excel sheet" → spreadsheet_operations(action="create_excel", headers=[...], data=[...])
- "Create data entry form" → spreadsheet_operations(action="create_data_entry", fields=[...])
- "Open Notepad/Notes" → app_control(action="launch", app_name="notepad") or app_control(action="launch", app_name="Notes")
- "Create budget" → spreadsheet_operations(action="create_template", template="budget")
- "Take a meeting note" → document_operations(action="create_from_template", template="meeting", title="...")

Be direct and helpful. Always use real data from tools."""

        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt
        )

    def process_command(self, user_input) -> Dict[str, Any]:
        """Process a command synchronously."""
        try:
            # Check if this is a Command object for resuming interrupts
            from langgraph.types import Command
            if isinstance(user_input, Command):
                # Resume from interrupt
                result = self.agent.invoke(user_input)
            else:
                # Regular user input - use minimal history to prevent context overflow
                # Only include the current message, let the agent handle the context
                messages = [{"role": "user", "content": user_input}]
                
                # Run the React agent
                result = self.agent.invoke({"messages": messages})
            
            # Check for interrupts
            if result.get('__interrupt__'):
                return {
                    "success": False,
                    "message": "Interrupt received",
                    "data": result,
                    "__interrupt__": result['__interrupt__'],
                    "tools_used": result.get("tools_used", [])
                }
            
            # Extract the response
            ai_response = self._extract_response(result)
            
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

    def process_command_streaming(self, user_input: str):
        """Process a command with streaming output. Yields tokens as they arrive."""
        try:
            messages = [{"role": "user", "content": user_input}]
            
            # Use stream method for streaming output
            for chunk in self.agent.stream({"messages": messages}):
                # Extract content from the chunk
                if "messages" in chunk:
                    for msg in chunk["messages"]:
                        if hasattr(msg, 'content') and msg.content:
                            yield {"type": "token", "content": msg.content}
                        elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tc in msg.tool_calls:
                                yield {"type": "tool_call", "name": tc.get("name", "unknown")}
                
                # Handle agent node output
                if "agent" in chunk:
                    agent_output = chunk["agent"]
                    if "messages" in agent_output:
                        for msg in agent_output["messages"]:
                            if hasattr(msg, 'content') and msg.content:
                                yield {"type": "content", "content": msg.content}
                
                # Handle tool node output
                if "tools" in chunk:
                    yield {"type": "tool_result", "content": "Tool executed"}
            
            yield {"type": "done"}
            
        except Exception as e:
            yield {"type": "error", "content": str(e)}

    async def process_command_async(self, user_input: str) -> Dict[str, Any]:
        """Process a command asynchronously (for compatibility)."""
        return self.process_command(user_input)

    def get_conversation_history(self, session_id: str = None) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        # Return empty - we don't persist history to avoid context overflow
        return []

    def clear_conversation_history(self, session_id: str = None):
        """Clear conversation history for a session."""
        self.session_id = str(int(time.time())) 