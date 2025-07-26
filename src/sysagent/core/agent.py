"""
Core SysAgent for processing natural language commands and routing to tools.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from ..types import Config, ToolResult, CommandContext, ExecutionPlan
from ..tools.base import ToolExecutor, ToolFactory
from .permissions import PermissionManager
from .config import ConfigManager


@dataclass
class AgentResult:
    """Result from agent processing."""
    success: bool
    message: str
    data: Dict[str, Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tools_used: List[str] = None


class SysAgent:
    """Main SysAgent for processing natural language commands."""
    
    def __init__(self, config_manager: ConfigManager, permission_manager: PermissionManager):
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.permission_manager = permission_manager
        self.tool_executor = ToolExecutor(permission_manager)
        self.session_id = str(uuid.uuid4())
        
        # Load API key from environment first
        self._load_api_key_from_env()
        
        # Initialize LLM if configured
        self.llm = self._initialize_llm()
        
        # Load available tools
        self.tools = self._load_tools()
    
    def _initialize_llm(self):
        """Initialize the LLM based on configuration."""
        try:
            if self.config.agent.provider.value == "openai":
                # Check if API key is configured
                if not self.config.agent.api_key:
                    if self.config.debug:
                        print("OpenAI API key not configured, prompting user...")
                    return self._prompt_for_openai_key()
                else:
                    # Try OpenAI with existing key
                    try:
                        return self._initialize_openai()
                    except (ValueError, ImportError, Exception) as e:
                        if self.config.debug:
                            print(f"OpenAI initialization failed: {e}")
                        return self._prompt_for_openai_key()
            elif self.config.agent.provider.value == "ollama":
                # Try Ollama, but fall back to simple LLM if not available
                try:
                    return self._initialize_ollama()
                except (ImportError, Exception):
                    if self.config.debug:
                        print("Ollama not available, using simple LLM")
                    return self._initialize_simple_llm()
            else:
                # Use simple LLM for now
                return self._initialize_simple_llm()
        except Exception as e:
            if self.config.debug:
                print(f"LLM initialization failed: {e}")
            # Always fall back to simple LLM
            return self._initialize_simple_llm()
    
    def _prompt_for_openai_key(self):
        """Prompt user for OpenAI API key and save it."""
        try:
            from rich.console import Console
            from rich.prompt import Prompt
            from rich.panel import Panel
            
            console = Console()
            
            console.print(Panel(
                "[bold blue]OpenAI API Key Required[/bold blue]\n\n"
                "SysAgent needs an OpenAI API key to provide intelligent assistance.\n"
                "You can get a free API key from: https://platform.openai.com/api-keys\n\n"
                "The API key will be securely stored in your environment.",
                title="🔑 API Configuration",
                border_style="blue"
            ))
            
            api_key = Prompt.ask(
                "[bold]Enter your OpenAI API key[/bold]",
                password=True,
                show_default=False
            )
            
            if not api_key or api_key.strip() == "":
                console.print("[yellow]No API key provided. Using simple LLM mode.[/yellow]")
                return self._initialize_simple_llm()
            
            # Test the API key
            console.print("[blue]Testing API key...[/blue]")
            test_client = self._test_openai_key(api_key)
            
            if test_client:
                # Save the API key to environment
                self._save_api_key_to_env(api_key)
                
                # Update config
                self.config.agent.api_key = api_key
                
                console.print("[green]✓ API key saved and working! Using OpenAI LLM.[/green]")
                return test_client
            else:
                console.print("[red]✗ Invalid API key. Using simple LLM mode.[/red]")
                return self._initialize_simple_llm()
                
        except Exception as e:
            if self.config.debug:
                print(f"Error prompting for API key: {e}")
            return self._initialize_simple_llm()
    
    def _test_openai_key(self, api_key: str):
        """Test if the OpenAI API key is valid."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key)
            
            # Make a simple test call
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            return client
            
        except Exception as e:
            if self.config.debug:
                print(f"API key test failed: {e}")
            return None
    
    def _save_api_key_to_env(self, api_key: str):
        """Save API key to environment file."""
        try:
            import os
            from pathlib import Path
            
            # Get config directory
            config_dir = self.config.agent.config_dir
            if not config_dir:
                # Fallback to default config directory
                from platformdirs import user_config_dir
                config_dir = Path(user_config_dir("sysagent"))
            
            # Create .env file in config directory
            env_file = config_dir / ".env"
            env_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing .env file if it exists
            env_content = ""
            if env_file.exists():
                with open(env_file, 'r') as f:
                    env_content = f.read()
            
            # Add or update OPENAI_API_KEY
            if "OPENAI_API_KEY=" in env_content:
                # Update existing key
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith("OPENAI_API_KEY="):
                        lines[i] = f"OPENAI_API_KEY={api_key}"
                        break
                env_content = '\n'.join(lines)
            else:
                # Add new key
                if env_content and not env_content.endswith('\n'):
                    env_content += '\n'
                env_content += f"OPENAI_API_KEY={api_key}\n"
            
            # Write back to file
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            # Set environment variable for current session
            os.environ["OPENAI_API_KEY"] = api_key
            
        except Exception as e:
            if self.config.debug:
                print(f"Error saving API key: {e}")
    
    def _load_api_key_from_env(self):
        """Load API key from environment file."""
        try:
            import os
            from pathlib import Path
            from dotenv import load_dotenv
            
            # Get config directory
            config_dir = self.config.agent.config_dir
            if not config_dir:
                # Fallback to default config directory
                from platformdirs import user_config_dir
                config_dir = Path(user_config_dir("sysagent"))
            
            # Load from .env file
            env_file = config_dir / ".env"
            if env_file.exists():
                load_dotenv(env_file)
            
            # Get from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.config.agent.api_key = api_key
                return True
            
            return False
            
        except Exception as e:
            if self.config.debug:
                print(f"Error loading API key: {e}")
            return False
    
    def _initialize_simple_llm(self):
        """Initialize a simple LLM that works without API keys."""
        return "simple_llm"
    
    def _initialize_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            
            if not self.config.agent.api_key:
                raise ValueError("OpenAI API key not configured")
            
            return OpenAI(
                api_key=self.config.agent.api_key,
                base_url=self.config.agent.base_url
            )
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        except Exception as e:
            raise Exception(f"OpenAI initialization failed: {e}")
    
    def _initialize_ollama(self):
        """Initialize Ollama client."""
        try:
            import ollama
            
            # Set base URL if configured
            if self.config.agent.base_url:
                ollama.set_host(self.config.agent.base_url)
            
            return ollama
        except ImportError:
            raise ImportError("Ollama package not installed. Install with: pip install ollama")
    
    def _load_tools(self) -> Dict[str, Any]:
        """Load available tools."""
        from ..tools.base import list_available_tools
        
        tools = {}
        for tool_info in list_available_tools():
            tool_name = tool_info['name']
            tools[tool_name] = tool_info
        
        return tools
    
    def process_command(self, user_input: str) -> AgentResult:
        """Process a natural language command."""
        start_time = time.time()
        
        try:
            # Create command context
            context = self._create_context(user_input)
            
            # Check for dangerous commands
            if self._is_dangerous_command(user_input):
                return AgentResult(
                    success=False,
                    message="Command blocked for safety",
                    error="Dangerous command detected",
                    execution_time=time.time() - start_time
                )
            
            # Debug: Check what LLM we have
            if self.config.debug:
                print(f"Debug: LLM type = {type(self.llm)}, value = {self.llm}")
            
            # Process with LLM if available
            if self.llm:
                result = self._process_with_llm(user_input, context)
            else:
                result = self._process_with_rules(user_input, context)
            
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Failed to process command: {str(e)}",
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _create_context(self, user_input: str) -> CommandContext:
        """Create command context."""
        from ..types import CommandContext, Platform
        from ..utils.platform import detect_platform
        
        return CommandContext(
            user_input=user_input,
            platform=detect_platform(),
            permissions=[],
            config=self.config,
            session_id=self.session_id,
            timestamp=time.time()
        )
    
    def _is_dangerous_command(self, user_input: str) -> bool:
        """Check if command is potentially dangerous."""
        dangerous_patterns = [
            "rm -rf /",
            "rm -rf /root",
            "rm -rf /home",
            "rm -rf /etc",
            "format",
            "dd if=",
            "mkfs",
            "fdisk",
            "shutdown",
            "reboot",
            "halt",
            "poweroff",
        ]
        
        user_input_lower = user_input.lower()
        for pattern in dangerous_patterns:
            if pattern in user_input_lower:
                return True
        
        return False
    
    def _process_with_llm(self, user_input: str, context: CommandContext) -> AgentResult:
        """Process command using LLM."""
        try:
            if self.llm == "simple_llm":
                return self._process_with_simple_llm(user_input, context)
            elif isinstance(self.llm, object) and hasattr(self.llm, 'chat'):  # OpenAI client
                return self._process_with_openai(user_input, context)
            elif self.config.agent.provider.value == "ollama":
                return self._process_with_ollama(user_input, context)
            else:
                return self._process_with_rules(user_input, context)
        except Exception as e:
            # Fallback to rule-based processing
            if self.config.debug:
                print(f"LLM processing failed: {e}")
            return self._process_with_rules(user_input, context)
    
    def _process_with_simple_llm(self, user_input: str, context: CommandContext) -> AgentResult:
        """Process command using simple LLM (no API required)."""
        try:
            user_input_lower = user_input.lower()
            
            # Handle permission commands
            if "grant" in user_input_lower and "permission" in user_input_lower:
                return self._handle_permission_grant(user_input)
            elif "revoke" in user_input_lower and "permission" in user_input_lower:
                return self._handle_permission_revoke(user_input)
            
            # Handle configuration commands
            elif "config" in user_input_lower or "setting" in user_input_lower:
                return self._handle_config_command(user_input)
            
            # Handle file operations
            elif any(word in user_input_lower for word in ['file', 'files', 'list', 'directory', 'folder', 'clean', 'organize']):
                if 'clean' in user_input_lower or 'cleanup' in user_input_lower:
                    return self._execute_tool('file_tool', action='cleanup')
                elif 'organize' in user_input_lower:
                    return self._execute_tool('file_tool', action='organize')
                elif 'search' in user_input_lower:
                    return self._execute_tool('file_tool', action='search')
                else:
                    return self._execute_tool('file_tool', action='list')
            
            # Handle system information
            elif any(word in user_input_lower for word in ['system', 'info', 'status', 'overview', 'cpu', 'memory', 'disk']):
                if 'cpu' in user_input_lower:
                    return self._execute_tool('system_info_tool', action='cpu')
                elif 'memory' in user_input_lower or 'ram' in user_input_lower:
                    return self._execute_tool('system_info_tool', action='memory')
                elif 'disk' in user_input_lower or 'storage' in user_input_lower:
                    return self._execute_tool('system_info_tool', action='disk')
                else:
                    return self._execute_tool('system_info_tool', action='overview')
            
            # Handle process operations
            elif any(word in user_input_lower for word in ['process', 'processes', 'running', 'kill']):
                return self._execute_tool('system_info_tool', action='processes')
            
            # Handle network operations
            elif any(word in user_input_lower for word in ['network', 'internet', 'connection', 'ping']):
                return self._execute_tool('system_info_tool', action='network')
            
            # Handle general queries
            elif any(word in user_input_lower for word in ['hello', 'hi', 'help', 'what', 'how']):
                return AgentResult(
                    success=True,
                    message="Hello! I'm SysAgent, your intelligent command-line assistant. I can help you with:\n" +
                           "• System information (CPU, memory, disk, processes)\n" +
                           "• File operations (list, clean, organize)\n" +
                           "• Network diagnostics\n" +
                           "• Permission management\n" +
                           "• Configuration settings\n\n" +
                           "Try asking me something like:\n" +
                           "• 'Show me system info'\n" +
                           "• 'List files in current directory'\n" +
                           "• 'Clean up temporary files'\n" +
                           "• 'What's using the most CPU?'"
                )
            
            else:
                return AgentResult(
                    success=False,
                    message="I understand you want to do something, but I'm not sure what. Try being more specific:\n" +
                           "• 'Show system information'\n" +
                           "• 'List files in this directory'\n" +
                           "• 'Clean up temp files'\n" +
                           "• 'What's my CPU usage?'\n" +
                           "• 'Grant permissions for file_tool'",
                    error="Command not understood"
                )
                
        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Error processing command: {str(e)}",
                error=str(e)
            )
    
    def _handle_permission_grant(self, user_input: str) -> AgentResult:
        """Handle permission grant commands."""
        try:
            # Extract tool name from command
            words = user_input.lower().split()
            tool_name = None
            
            # Look for tool name after "for" or after "permission"
            for i, word in enumerate(words):
                if word == "for" and i + 1 < len(words):
                    tool_name = words[i + 1]
                    break
                elif word == "permission" and i + 1 < len(words):
                    tool_name = words[i + 1]
                    break
            
            # If not found, try to extract from the end
            if not tool_name and len(words) >= 2:
                tool_name = words[-1]  # Last word might be the tool name
            
            if not tool_name:
                return AgentResult(
                    success=False,
                    message="Please specify which tool to grant permissions for. Example: 'grant permissions for file_tool'",
                    error="No tool specified"
                )
            
            # Clean up tool name (remove common suffixes)
            if tool_name.endswith('_tool'):
                tool_name = tool_name
            elif tool_name == 'file':
                tool_name = 'file_tool'
            elif tool_name == 'system':
                tool_name = 'system_info_tool'
            
            # Get required permissions for the tool
            required_permissions = self.permission_manager.get_required_permissions(tool_name)
            
            if not required_permissions:
                return AgentResult(
                    success=False,
                    message=f"Tool '{tool_name}' not found or has no permissions. Available tools: {list(self.tools.keys())}",
                    error="Tool not found"
                )
            
            # Grant permissions
            granted_count = 0
            for perm_request in required_permissions:
                if not perm_request.granted:
                    granted = self.permission_manager.request_permission(
                        perm_request.permission,
                        perm_request.level,
                        perm_request.description
                    )
                    if granted:
                        granted_count += 1
            
            if granted_count > 0:
                return AgentResult(
                    success=True,
                    message=f"Successfully granted {granted_count} permission(s) for {tool_name}",
                    data={"tool": tool_name, "permissions_granted": granted_count}
                )
            else:
                return AgentResult(
                    success=True,
                    message=f"No new permissions needed for {tool_name}",
                    data={"tool": tool_name, "permissions_granted": 0}
                )
                
        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Error granting permissions: {str(e)}",
                error=str(e)
            )
    
    def _handle_permission_revoke(self, user_input: str) -> AgentResult:
        """Handle permission revoke commands."""
        try:
            # Extract tool name from command
            words = user_input.lower().split()
            tool_name = None
            
            for i, word in enumerate(words):
                if word in ['revoke', 'permission'] and i + 1 < len(words):
                    tool_name = words[i + 1]
                    break
            
            if not tool_name:
                return AgentResult(
                    success=False,
                    message="Please specify which tool to revoke permissions for. Example: 'revoke file_tool'",
                    error="No tool specified"
                )
            
            # Get required permissions for the tool
            required_permissions = self.permission_manager.get_required_permissions(tool_name)
            
            if not required_permissions:
                return AgentResult(
                    success=False,
                    message=f"Tool '{tool_name}' not found or has no permissions",
                    error="Tool not found"
                )
            
            # Revoke permissions
            revoked_count = 0
            for perm_request in required_permissions:
                if perm_request.granted:
                    self.permission_manager.revoke_permission(perm_request.permission)
                    revoked_count += 1
            
            if revoked_count > 0:
                return AgentResult(
                    success=True,
                    message=f"Successfully revoked {revoked_count} permission(s) for {tool_name}",
                    data={"tool": tool_name, "permissions_revoked": revoked_count}
                )
            else:
                return AgentResult(
                    success=True,
                    message=f"No permissions were revoked for {tool_name}",
                    data={"tool": tool_name, "permissions_revoked": 0}
                )
                
        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Error revoking permissions: {str(e)}",
                error=str(e)
            )
    
    def _handle_config_command(self, user_input: str) -> AgentResult:
        """Handle configuration commands."""
        return AgentResult(
            success=True,
            message="Configuration commands should be used directly:\n" +
                   "• 'config get <key>' - Get configuration value\n" +
                   "• 'config set <key> <value>' - Set configuration value\n" +
                   "• 'config show-config' - Show current configuration\n\n" +
                   "Examples:\n" +
                   "• config get agent.provider\n" +
                   "• config set security.dry_run true"
        )
    
    def _process_with_openai(self, user_input: str, context: CommandContext) -> AgentResult:
        """Process command using OpenAI."""
        try:
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Create user prompt
            user_prompt = f"""
User request: {user_input}

Available tools: {list(self.tools.keys())}

Please analyze the user request and determine which tool(s) to use and with what parameters.
Respond in JSON format with the following structure:
{{
    "tools": [
        {{
            "tool": "tool_name",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
    ],
    "explanation": "Brief explanation of what will be done"
}}

If the user is just saying hello or asking for help, respond with a friendly greeting and explanation of capabilities.
"""
            
            # Call OpenAI
            response = self.llm.chat.completions.create(
                model=self.config.agent.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.agent.temperature,
                max_tokens=self.config.agent.max_tokens
            )
            
            # Parse response
            content = response.choices[0].message.content
            if self.config.debug:
                print(f"OpenAI response: {content}")
            return self._parse_llm_response(content, user_input)
            
        except Exception as e:
            raise Exception(f"OpenAI processing failed: {e}")
    
    def _process_with_ollama(self, user_input: str, context: CommandContext) -> AgentResult:
        """Process command using Ollama."""
        try:
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Create user prompt
            user_prompt = f"""
User request: {user_input}

Available tools: {list(self.tools.keys())}

Please analyze the user request and determine which tool(s) to use and with what parameters.
Respond in JSON format with the following structure:
{{
    "tools": [
        {{
            "tool": "tool_name",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
    ],
    "explanation": "Brief explanation of what will be done"
}}
"""
            
            # Call Ollama
            response = self.llm.chat(
                model=self.config.agent.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse response
            content = response['message']['content']
            return self._parse_llm_response(content, user_input)
            
        except Exception as e:
            raise Exception(f"Ollama processing failed: {e}")
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for LLM."""
        return f"""
You are SysAgent, an intelligent command-line assistant for OS automation and control.

Your capabilities include:
- File system operations (list, read, write, move, delete, organize, cleanup)
- System information and monitoring (CPU, memory, disk, processes, network)
- Process management (list, kill, monitor)
- Network diagnostics (connectivity, ping, DNS)
- Application control (launch, close, focus)

Available tools: {list(self.tools.keys())}

Tool Actions:
- system_info_tool actions: overview, cpu, memory, disk, network, processes, battery, uptime, performance, hardware
- file_tool actions: list, search, cleanup, organize

Guidelines:
1. For tool operations, respond with valid JSON containing tools array
2. For greetings, help requests, or general questions, respond with a friendly message
3. Use the most appropriate tool for the task
4. Provide clear explanations
5. Be safe and avoid destructive operations unless explicitly requested
6. Use dry-run mode when appropriate

Platform: {self.config.agent.provider.value}
"""
    
    def _parse_llm_response(self, content: str, user_input: str) -> AgentResult:
        """Parse LLM response and execute tools."""
        try:
            import json
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = content[json_start:json_end]
            parsed = json.loads(json_str)
            
            tools_to_execute = parsed.get('tools', [])
            explanation = parsed.get('explanation', '')
            
            if not tools_to_execute:
                # Return the explanation as a friendly message
                return AgentResult(
                    success=True,
                    message=explanation or "I understand your request but don't need to use any tools for this. How can I help you with system operations?"
                )
            
            # Execute tools
            results = []
            tools_used = []
            
            for tool_request in tools_to_execute:
                tool_name = tool_request.get('tool')
                parameters = tool_request.get('parameters', {})
                
                if tool_name and tool_name in self.tools:
                    # Check permissions
                    if not self._check_tool_permissions(tool_name):
                        return AgentResult(
                            success=False,
                            message=f"Permission denied for tool: {tool_name}",
                            error=f"Missing permissions for {tool_name}"
                        )
                    
                    # Execute tool
                    result = self.tool_executor.execute_tool(tool_name, **parameters)
                    results.append(result)
                    tools_used.append(tool_name)
                    
                    if not result.success:
                        return AgentResult(
                            success=False,
                            message=f"Tool execution failed: {result.message}",
                            error=result.error,
                            tools_used=tools_used
                        )
            
            # Combine results
            combined_data = {}
            for result in results:
                if result.data:
                    combined_data.update(result.data)
            
            return AgentResult(
                success=True,
                message=explanation or f"Executed {len(tools_used)} tool(s): {', '.join(tools_used)}",
                data=combined_data,
                tools_used=tools_used
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Failed to parse LLM response: {str(e)}",
                error=str(e)
            )
    
    def _process_with_rules(self, user_input: str, context: CommandContext) -> AgentResult:
        """Process command using rule-based approach."""
        user_input_lower = user_input.lower()
        
        # File operations
        if any(word in user_input_lower for word in ['file', 'files', 'list', 'directory', 'folder']):
            if 'clean' in user_input_lower or 'cleanup' in user_input_lower:
                return self._execute_tool('file_tool', action='cleanup')
            elif 'organize' in user_input_lower:
                return self._execute_tool('file_tool', action='organize')
            elif 'search' in user_input_lower:
                return self._execute_tool('file_tool', action='search')
            else:
                return self._execute_tool('file_tool', action='list')
        
        # System information
        elif any(word in user_input_lower for word in ['system', 'info', 'status', 'overview']):
            return self._execute_tool('system_info_tool', action='overview')
        
        # CPU information
        elif any(word in user_input_lower for word in ['cpu', 'processor']):
            return self._execute_tool('system_info_tool', action='cpu')
        
        # Memory information
        elif any(word in user_input_lower for word in ['memory', 'ram']):
            return self._execute_tool('system_info_tool', action='memory')
        
        # Disk information
        elif any(word in user_input_lower for word in ['disk', 'storage', 'space']):
            return self._execute_tool('system_info_tool', action='disk')
        
        # Process information
        elif any(word in user_input_lower for word in ['process', 'processes', 'running']):
            return self._execute_tool('system_info_tool', action='processes')
        
        # Network information
        elif any(word in user_input_lower for word in ['network', 'internet', 'connection']):
            return self._execute_tool('system_info_tool', action='network')
        
        # Battery information
        elif any(word in user_input_lower for word in ['battery', 'power']):
            return self._execute_tool('system_info_tool', action='battery')
        
        # Uptime information
        elif any(word in user_input_lower for word in ['uptime', 'boot']):
            return self._execute_tool('system_info_tool', action='uptime')
        
        # Performance metrics
        elif any(word in user_input_lower for word in ['performance', 'metrics', 'load']):
            return self._execute_tool('system_info_tool', action='performance')
        
        # Hardware information
        elif any(word in user_input_lower for word in ['hardware', 'specs']):
            return self._execute_tool('system_info_tool', action='hardware')
        
        else:
            return AgentResult(
                success=False,
                message="I don't understand this command. Try asking for system info, file operations, or process management.",
                error="No matching rule found"
            )
    
    def _execute_tool(self, tool_name: str, **parameters) -> AgentResult:
        """Execute a specific tool."""
        try:
            # Check permissions
            if not self._check_tool_permissions(tool_name):
                return AgentResult(
                    success=False,
                    message=f"Permission denied for tool: {tool_name}",
                    error=f"Missing permissions for {tool_name}"
                )
            
            # Execute tool
            result = self.tool_executor.execute_tool(tool_name, **parameters)
            
            return AgentResult(
                success=result.success,
                message=result.message,
                data=result.data,
                error=result.error,
                tools_used=[tool_name]
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Failed to execute tool {tool_name}: {str(e)}",
                error=str(e),
                tools_used=[tool_name]
            )
    
    def _check_tool_permissions(self, tool_name: str) -> bool:
        """Check if we have permissions for a tool."""
        if not self.permission_manager:
            return True  # No permission manager, assume allowed
        
        # Get required permissions for tool
        from ..tools.base import get_tool_permissions
        required_permissions = get_tool_permissions(tool_name)
        
        # Check each permission
        for permission, level in required_permissions.items():
            if not self.permission_manager.has_permission(permission, level):
                return False
        
        return True
    
    def get_available_commands(self) -> List[str]:
        """Get list of available commands."""
        return [
            "Show system information",
            "List files in directory",
            "Clean up temporary files",
            "Organize files by type",
            "Search for files",
            "Show CPU usage",
            "Show memory usage",
            "Show disk usage",
            "List running processes",
            "Show network information",
            "Show battery status",
            "Show system uptime",
            "Show performance metrics",
            "Show hardware information"
        ]
    
    def get_help(self) -> str:
        """Get help information."""
        return """
SysAgent CLI Help

Available Commands:
- System Information: "show system info", "cpu usage", "memory status"
- File Operations: "list files", "clean up files", "organize downloads"
- Process Management: "running processes", "top processes"
- Network: "network status", "internet connection"
- System: "uptime", "battery", "performance"

Examples:
  sysagent run "show me system info"
  sysagent run "clean up temp files"
  sysagent run "what's using the most CPU?"
  sysagent run "list files in downloads"

For interactive mode: sysagent repl
        """ 