"""
Main GUI Window for SysAgent - Combines Dashboard and Settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

try:
    import customtkinter as ctk
    USE_CUSTOMTKINTER = True
except ImportError:
    USE_CUSTOMTKINTER = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class MainWindow:
    """Main application window combining dashboard, chat, and settings."""

    def __init__(self):
        self.root = None
        self.current_view = "chat"  # Default to chat view
        self.current_theme = "dark"
        self.agent = None
        self.chat_interface = None
        self.command_palette = None
        self.proactive_agent = None
        self._initialize_agent()
        self._create_window()
        self._create_menu()
        self._setup_keyboard_shortcuts()
        self._setup_proactive_agent()
        self._create_content()

    def _initialize_agent(self):
        """Initialize the LangGraph agent."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..core.langgraph_agent import LangGraphAgent
            
            self.config_manager = ConfigManager()
            self.permission_manager = PermissionManager(self.config_manager)
            self.agent = LangGraphAgent(self.config_manager, self.permission_manager)
        except Exception as e:
            print(f"Warning: Could not initialize agent: {e}")
            self.agent = None
            self.config_manager = None
            self.permission_manager = None

    def _create_window(self):
        """Create the main window."""
        if USE_CUSTOMTKINTER:
            ctk.set_appearance_mode(self.current_theme)
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title("SysAgent - Intelligent System Assistant")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Set icon if available
        try:
            # self.root.iconbitmap("path/to/icon.ico")
            pass
        except:
            pass
        
        return self.root

    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Chat", command=self._new_chat)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Chat", command=self._show_chat)
        view_menu.add_command(label="Dashboard", command=self._show_dashboard)
        view_menu.add_command(label="Terminal", command=self._show_terminal)
        view_menu.add_separator()
        view_menu.add_command(label="System Info", command=self._view_system_info)
        view_menu.add_command(label="Processes", command=self._view_processes)
        view_menu.add_command(label="Files", command=self._view_files)
        view_menu.add_command(label="Network", command=self._view_network)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Clean Temp Files", command=self._clean_temp)
        tools_menu.add_command(label="Organize Downloads", command=self._organize_downloads)
        tools_menu.add_command(label="Check Internet", command=self._check_internet)
        tools_menu.add_separator()
        tools_menu.add_command(label="Run CLI Command", command=self._run_cli_command)
        tools_menu.add_command(label="Plugin Manager", command=self._show_plugins)
        
        # Theme menu
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Dark Mode", command=lambda: self._set_theme("dark"))
        theme_menu.add_command(label="Light Mode", command=lambda: self._set_theme("light"))
        theme_menu.add_command(label="System", command=lambda: self._set_theme("system"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_docs)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)

    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts."""
        # Command palette: Ctrl+K or Cmd+K
        self.root.bind("<Control-k>", lambda e: self._toggle_command_palette())
        self.root.bind("<Command-k>", lambda e: self._toggle_command_palette())
        
        # Quick actions
        self.root.bind("<Control-n>", lambda e: self._new_chat())
        self.root.bind("<Control-d>", lambda e: self._show_dashboard())
        self.root.bind("<Control-s>", lambda e: self._show_settings())
        self.root.bind("<Control-t>", lambda e: self._show_terminal())
        self.root.bind("<Control-q>", lambda e: self._on_exit())
        
        # Quick insights
        self.root.bind("<Control-i>", lambda e: self._quick_insights())

    def _setup_proactive_agent(self):
        """Setup the proactive agent for intelligent suggestions."""
        try:
            from .proactive_agent import ProactiveAgent
            self.proactive_agent = ProactiveAgent(callback=self._on_proactive_suggestion)
            self.proactive_agent.start()
        except Exception as e:
            print(f"Warning: Could not initialize proactive agent: {e}")
            self.proactive_agent = None

    def _on_proactive_suggestion(self, suggestion):
        """Handle a proactive suggestion from the agent."""
        if not suggestion or suggestion.dismissed:
            return
        
        # Show suggestion in a non-intrusive way
        try:
            self._show_suggestion_toast(suggestion)
        except Exception:
            pass

    def _show_suggestion_toast(self, suggestion):
        """Show a suggestion as a toast notification."""
        if not hasattr(self, 'toast_frame'):
            return
        
        if USE_CUSTOMTKINTER:
            toast = ctk.CTkFrame(
                self.root,
                fg_color="#2d2d2d",
                corner_radius=10
            )
            toast.place(relx=0.98, rely=0.02, anchor="ne")
            
            # Icon and title
            header = ctk.CTkFrame(toast, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(10, 5))
            
            ctk.CTkLabel(
                header,
                text=f"{suggestion.icon} {suggestion.title}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white"
            ).pack(side="left")
            
            # Close button
            close_btn = ctk.CTkButton(
                header,
                text="×",
                width=20,
                height=20,
                command=toast.destroy,
                fg_color="transparent",
                hover_color="#444"
            )
            close_btn.pack(side="right")
            
            # Message
            ctk.CTkLabel(
                toast,
                text=suggestion.message,
                font=ctk.CTkFont(size=11),
                text_color="#aaa",
                wraplength=250
            ).pack(padx=10, pady=5)
            
            # Action button if available
            if suggestion.action:
                action_btn = ctk.CTkButton(
                    toast,
                    text="Do it",
                    width=60,
                    height=25,
                    command=lambda: self._execute_suggestion(suggestion, toast),
                    fg_color="#4a9eff"
                )
                action_btn.pack(pady=(0, 10))
            
            # Auto-dismiss after 10 seconds
            toast.after(10000, lambda: toast.destroy() if toast.winfo_exists() else None)

    def _execute_suggestion(self, suggestion, toast):
        """Execute a proactive suggestion."""
        if toast and hasattr(toast, 'winfo_exists') and toast.winfo_exists():
            toast.destroy()
        
        if suggestion.action and self.chat_interface:
            # Send the action as a chat message
            self._show_chat()
            self.chat_interface._send_message_direct(suggestion.action)

    def _toggle_command_palette(self):
        """Toggle the command palette."""
        try:
            from .command_palette import CommandPalette
            
            if self.command_palette is None:
                self.command_palette = CommandPalette(
                    self.root,
                    on_command=self._on_palette_command
                )
            
            if self.command_palette.is_open:
                self.command_palette.close()
            else:
                self.command_palette.open()
        except Exception as e:
            print(f"Warning: Could not open command palette: {e}")

    def _on_palette_command(self, command: str):
        """Handle a command from the command palette."""
        if command and self.chat_interface:
            # Switch to chat if not already there
            if self.current_view != "chat":
                self._show_chat()
                # Need to wait for chat to be ready
                self.root.after(100, lambda: self._send_palette_command(command))
            else:
                self._send_palette_command(command)

    def _send_palette_command(self, command: str):
        """Send command from palette to chat."""
        if self.chat_interface:
            # Send directly using the helper method
            self.chat_interface._send_message_direct(command)

    def _quick_insights(self):
        """Show quick system insights."""
        if self.chat_interface:
            if self.current_view != "chat":
                self._show_chat()
                self.root.after(100, lambda: self._send_palette_command("Give me quick system insights"))
            else:
                self._send_palette_command("Give me quick system insights")

    def _set_theme(self, theme: str):
        """Set the application theme."""
        self.current_theme = theme
        if USE_CUSTOMTKINTER:
            ctk.set_appearance_mode(theme)
        messagebox.showinfo("Theme", f"Theme set to: {theme.title()}")

    def _new_chat(self):
        """Start a new chat session."""
        # Always show chat view (which will recreate the interface)
        self._show_chat()
        # Clear any existing messages if the interface was recreated
        if self.chat_interface:
            try:
                self.chat_interface.clear_chat()
            except Exception:
                pass  # Interface may have been recreated

    def _create_content(self):
        """Create the main content area."""
        if USE_CUSTOMTKINTER:
            self.content_frame = ctk.CTkFrame(self.root)
            self.content_frame.pack(fill="both", expand=True)
        else:
            self.content_frame = ttk.Frame(self.root)
            self.content_frame.pack(fill="both", expand=True)
        
        # Show chat by default
        self._show_chat()

    def _clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_chat(self):
        """Show the chat view."""
        self._clear_content()
        self.current_view = "chat"
        
        if USE_CUSTOMTKINTER:
            # Create main layout with sidebar and chat
            main_container = ctk.CTkFrame(self.content_frame)
            main_container.pack(fill="both", expand=True)
            
            # Sidebar
            sidebar = ctk.CTkFrame(main_container, width=200, corner_radius=0)
            sidebar.pack(side="left", fill="y")
            sidebar.pack_propagate(False)
            
            # Logo
            logo = ctk.CTkLabel(
                sidebar,
                text="🧠 SysAgent",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            logo.pack(pady=30)
            
            # Navigation buttons
            nav_buttons = [
                ("💬 Chat", self._show_chat),
                ("🏠 Dashboard", self._show_dashboard),
                ("💻 System Info", self._view_system_info),
                ("📊 Processes", self._view_processes),
                ("📁 Files", self._view_files),
                ("🌐 Network", self._view_network),
                ("🖥️ Terminal", self._show_terminal),
                ("⚙️ Settings", self._show_settings),
            ]
            
            for text, command in nav_buttons:
                btn = ctk.CTkButton(
                    sidebar,
                    text=text,
                    command=command,
                    width=180,
                    height=35,
                    anchor="w"
                )
                btn.pack(pady=3, padx=10)
            
            # Quick status at bottom
            status_frame = ctk.CTkFrame(sidebar)
            status_frame.pack(side="bottom", fill="x", padx=10, pady=10)
            
            if PSUTIL_AVAILABLE:
                cpu = psutil.cpu_percent()
                mem = psutil.virtual_memory().percent
                ctk.CTkLabel(status_frame, text=f"CPU: {cpu}%", font=ctk.CTkFont(size=10)).pack()
                ctk.CTkLabel(status_frame, text=f"RAM: {mem}%", font=ctk.CTkFont(size=10)).pack()
            
            # Chat area
            chat_container = ctk.CTkFrame(main_container)
            chat_container.pack(side="right", fill="both", expand=True)
            
            # Quick actions bar at top
            self._create_quick_actions_bar(chat_container)
            
            # Create chat interface
            from .chat import ChatInterface
            self.chat_interface = ChatInterface(chat_container, on_send=self._on_chat_message)
        else:
            # Simpler layout for standard tkinter
            sidebar = ttk.Frame(self.content_frame, width=200)
            sidebar.pack(side="left", fill="y")
            
            ttk.Label(sidebar, text="🧠 SysAgent", font=("", 14, "bold")).pack(pady=20)
            
            buttons = [
                ("Chat", self._show_chat),
                ("Dashboard", self._show_dashboard),
                ("System Info", self._view_system_info),
                ("Processes", self._view_processes),
                ("Files", self._view_files),
                ("Settings", self._show_settings),
            ]
            
            for text, cmd in buttons:
                ttk.Button(sidebar, text=text, command=cmd).pack(pady=3, padx=10, fill="x")
            
            # Chat area
            chat_container = ttk.Frame(self.content_frame)
            chat_container.pack(side="right", fill="both", expand=True)
            
            from .chat import ChatInterface
            self.chat_interface = ChatInterface(chat_container, on_send=self._on_chat_message)

    def _create_quick_actions_bar(self, parent):
        """Create a quick actions bar for common commands."""
        if USE_CUSTOMTKINTER:
            bar = ctk.CTkFrame(parent, height=50, fg_color="#2d2d2d")
            bar.pack(fill="x", padx=0, pady=0)
            bar.pack_propagate(False)
            
            # Left side - Command palette button
            left_frame = ctk.CTkFrame(bar, fg_color="transparent")
            left_frame.pack(side="left", padx=10)
            
            palette_btn = ctk.CTkButton(
                left_frame,
                text="⌘K Command Palette",
                command=self._toggle_command_palette,
                width=160,
                height=30,
                fg_color="#3d3d3d",
                hover_color="#4d4d4d",
                font=ctk.CTkFont(size=12)
            )
            palette_btn.pack(side="left", padx=5)
            
            # Center - Quick action buttons
            center_frame = ctk.CTkFrame(bar, fg_color="transparent")
            center_frame.pack(side="left", padx=20)
            
            quick_actions = [
                ("🏥 Health", "Check system health"),
                ("📊 Status", "Show system status"),
                ("🔍 Search", "Search for files named "),
                ("⚡ Insights", "Give me quick insights"),
            ]
            
            for text, action in quick_actions:
                btn = ctk.CTkButton(
                    center_frame,
                    text=text,
                    command=lambda a=action: self._quick_action(a),
                    width=90,
                    height=28,
                    fg_color="#3d3d3d",
                    hover_color="#4d4d4d",
                    font=ctk.CTkFont(size=11)
                )
                btn.pack(side="left", padx=3)
            
            # Right side - Workflow dropdown
            right_frame = ctk.CTkFrame(bar, fg_color="transparent")
            right_frame.pack(side="right", padx=10)
            
            workflow_btn = ctk.CTkButton(
                right_frame,
                text="▶ Workflows",
                command=self._show_workflow_menu,
                width=100,
                height=28,
                fg_color="#4a9eff",
                hover_color="#3a8eef",
                font=ctk.CTkFont(size=11)
            )
            workflow_btn.pack(side="right", padx=5)

    def _quick_action(self, action: str):
        """Execute a quick action."""
        if self.chat_interface:
            if action.endswith(" "):
                # User needs to complete the command
                self.chat_interface._set_input_text(action)
                try:
                    self.chat_interface.input_field.focus_set()
                except:
                    pass
            else:
                # Send directly
                self.chat_interface._send_message_direct(action)

    def _show_workflow_menu(self):
        """Show workflow menu."""
        if USE_CUSTOMTKINTER:
            menu = tk.Menu(self.root, tearoff=0)
            
            menu.add_command(label="▶ Morning Routine", command=lambda: self._run_workflow("morning_routine"))
            menu.add_command(label="▶ Dev Setup", command=lambda: self._run_workflow("dev_setup"))
            menu.add_command(label="▶ System Maintenance", command=lambda: self._run_workflow("system_maintenance"))
            menu.add_command(label="▶ End of Day", command=lambda: self._run_workflow("end_of_day"))
            menu.add_separator()
            menu.add_command(label="📋 List Workflows", command=lambda: self._quick_action("List all my workflows"))
            menu.add_command(label="➕ Create Workflow", command=lambda: self._quick_action("Create a new workflow named "))
            
            try:
                menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
            finally:
                menu.grab_release()

    def _run_workflow(self, workflow_name: str):
        """Run a predefined workflow."""
        self._quick_action(f"Run the {workflow_name.replace('_', ' ')} workflow")

    def _on_chat_message(self, message: str):
        """Handle chat message from user with streaming support."""
        if self.agent:
            # Process in background thread to not block UI
            import threading
            thread = threading.Thread(target=self._process_chat_message, args=(message,))
            thread.daemon = True
            thread.start()
        else:
            self.chat_interface.add_message("Agent not initialized. Please configure your API key.", is_user=False)

    def _process_chat_message(self, message: str):
        """Process chat message in background thread with execution logging."""
        import time
        start_time = time.time()
        
        try:
            # Try streaming first
            use_streaming = hasattr(self.agent, 'process_command_streaming')
            
            if use_streaming:
                # Create streaming message container
                stream_data = None
                try:
                    self.root.after(0, lambda: setattr(self, '_stream_data', self.chat_interface.add_streaming_message()))
                    time.sleep(0.05)  # Brief wait for UI update
                    stream_data = getattr(self, '_stream_data', None)
                except Exception:
                    pass
                
                full_response = ""
                tools_used = []
                
                for chunk in self.agent.process_command_streaming(message):
                    chunk_type = chunk.get("type", "")
                    content = chunk.get("content", "")
                    
                    if chunk_type == "content" and content:
                        full_response = content  # Full content replacement
                        if stream_data:
                            stream_data["content"] = content
                            self.root.after(0, lambda c=content: self._update_stream(stream_data, c))
                    elif chunk_type == "token" and content:
                        full_response += content
                        if stream_data:
                            self.root.after(0, lambda t=content: self.chat_interface.update_streaming_message(stream_data, t))
                    elif chunk_type == "tool_call":
                        name = chunk.get("name", "tool")
                        tools_used.append(name)
                        # Add execution log for tool call
                        self.root.after(0, lambda n=name: self._add_tool_log(n, "running"))
                    elif chunk_type == "tool_result":
                        if tools_used:
                            tool = tools_used[-1]
                            duration = int((time.time() - start_time) * 1000)
                            self.root.after(0, lambda t=tool, d=duration: self._add_tool_log(t, "success", d))
                    elif chunk_type == "error":
                        full_response = f"Error: {content}"
                        if tools_used:
                            self.root.after(0, lambda t=tools_used[-1]: self._add_tool_log(t, "error"))
                        break
                    elif chunk_type == "done":
                        break
                
                # Finalize streaming message
                if stream_data:
                    self.root.after(0, lambda: self.chat_interface.finish_streaming_message(stream_data))
                elif full_response:
                    self.root.after(0, lambda r=full_response: self.chat_interface.add_message(r, is_user=False))
            else:
                # Non-streaming fallback with execution logging
                # Show "thinking" log
                self.root.after(0, lambda: self._add_tool_log("SysAgent", "running", details="Processing..."))
                
                result = self.agent.process_command(message)
                
                duration = int((time.time() - start_time) * 1000)
                
                if result.get('success'):
                    response = result.get('message', 'Command executed successfully.')
                    # Show success log
                    self.root.after(0, lambda d=duration: self._add_tool_log("SysAgent", "success", d))
                else:
                    response = result.get('message', 'Unknown error')
                    self.root.after(0, lambda: self._add_tool_log("SysAgent", "error"))
                
                self.root.after(0, lambda r=response: self.chat_interface.add_message(r, is_user=False))
                
        except Exception as e:
            error_msg = str(e)
            # Simplify context length error
            if "context_length" in error_msg:
                error_msg = "Conversation too long. Please start a new chat."
            self.root.after(0, lambda: self._add_tool_log("Error", "error"))
            self.root.after(0, lambda m=error_msg: self.chat_interface.add_message(f"Error: {m}", is_user=False))

    def _add_tool_log(self, tool_name: str, status: str, duration_ms: int = 0, details: str = ""):
        """Add a tool execution log to the chat."""
        if hasattr(self.chat_interface, 'add_execution_log'):
            self.chat_interface.add_execution_log(tool_name, "", status, duration_ms, details)

    def _update_stream(self, stream_data: dict, content: str):
        """Update stream content."""
        if stream_data and "label" in stream_data:
            try:
                stream_data["label"].configure(text=content + "▌")
                stream_data["content"] = content
            except Exception:
                pass

    def _show_tool_status(self, tool_name: str):
        """Show tool execution status."""
        try:
            if hasattr(self.chat_interface, 'status_label'):
                self.chat_interface.status_label.configure(text=f"● Using {tool_name}...")
        except Exception:
            pass
        else:
            self.chat_interface.add_message(
                "Agent not available. Please check your configuration and API keys in Settings.",
                is_user=False
            )

    def _format_data(self, data: dict, max_items: int = 10) -> str:
        """Format data dictionary for display."""
        lines = []
        count = 0
        for key, value in data.items():
            if count >= max_items:
                lines.append("...")
                break
            if isinstance(value, (str, int, float, bool)):
                lines.append(f"• {key}: {value}")
                count += 1
            elif isinstance(value, list) and len(value) <= 5:
                lines.append(f"• {key}: {value}")
                count += 1
        return "\n".join(lines)

    def _show_terminal(self):
        """Show terminal/command output view."""
        self._clear_content()
        self.current_view = "terminal"
        
        if USE_CUSTOMTKINTER:
            # Create terminal view
            terminal_frame = ctk.CTkFrame(self.content_frame)
            terminal_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Title
            title = ctk.CTkLabel(
                terminal_frame,
                text="🖥️ Terminal Output",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title.pack(pady=10)
            
            # Output area
            self.terminal_output = ctk.CTkTextbox(
                terminal_frame,
                font=ctk.CTkFont(family="Courier", size=12),
                wrap="word"
            )
            self.terminal_output.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Input area
            input_frame = ctk.CTkFrame(terminal_frame)
            input_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(input_frame, text="$").pack(side="left", padx=5)
            
            self.terminal_input = ctk.CTkEntry(input_frame, placeholder_text="Enter command...")
            self.terminal_input.pack(side="left", fill="x", expand=True, padx=5)
            self.terminal_input.bind("<Return>", self._run_terminal_command)
            
            run_btn = ctk.CTkButton(
                input_frame,
                text="Run",
                width=80,
                command=self._run_terminal_command
            )
            run_btn.pack(side="right", padx=5)
            
            # Add welcome message
            self.terminal_output.insert("end", "SysAgent Terminal\n")
            self.terminal_output.insert("end", "=" * 50 + "\n")
            self.terminal_output.insert("end", "Enter shell commands below. Use with caution!\n\n")
        else:
            ttk.Label(self.content_frame, text="Terminal View", font=("", 16)).pack(pady=20)
            self.terminal_output = tk.Text(self.content_frame, font=("Courier", 10))
            self.terminal_output.pack(fill="both", expand=True, padx=10, pady=5)
            
            input_frame = ttk.Frame(self.content_frame)
            input_frame.pack(fill="x", padx=10, pady=10)
            
            self.terminal_input = ttk.Entry(input_frame)
            self.terminal_input.pack(side="left", fill="x", expand=True)
            self.terminal_input.bind("<Return>", self._run_terminal_command)
            
            ttk.Button(input_frame, text="Run", command=self._run_terminal_command).pack(side="right")

    def _run_terminal_command(self, event=None):
        """Run a terminal command."""
        import subprocess
        
        if USE_CUSTOMTKINTER:
            command = self.terminal_input.get()
            self.terminal_input.delete(0, "end")
        else:
            command = self.terminal_input.get()
            self.terminal_input.delete(0, "end")
        
        if not command.strip():
            return
        
        self.terminal_output.insert("end", f"$ {command}\n")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                self.terminal_output.insert("end", result.stdout)
            if result.stderr:
                self.terminal_output.insert("end", f"[stderr] {result.stderr}")
            
            self.terminal_output.insert("end", "\n")
        except subprocess.TimeoutExpired:
            self.terminal_output.insert("end", "[Timeout: Command took too long]\n\n")
        except Exception as e:
            self.terminal_output.insert("end", f"[Error: {str(e)}]\n\n")
        
        # Scroll to bottom
        self.terminal_output.see("end")

    def _show_plugins(self):
        """Show plugin manager."""
        if USE_CUSTOMTKINTER:
            plugin_window = ctk.CTkToplevel(self.root)
        else:
            plugin_window = tk.Toplevel(self.root)
        
        plugin_window.title("Plugin Manager")
        plugin_window.geometry("600x400")
        
        try:
            from ..core.plugins import PluginManager
            pm = PluginManager()
            discovered = pm.discover_plugins()
            loaded = pm.list_plugins()
            
            if USE_CUSTOMTKINTER:
                title = ctk.CTkLabel(
                    plugin_window,
                    text="Plugin Manager",
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                title.pack(pady=10)
                
                # Discovered plugins
                ctk.CTkLabel(plugin_window, text="Discovered Plugins:").pack(anchor="w", padx=10)
                
                for plugin in discovered:
                    frame = ctk.CTkFrame(plugin_window)
                    frame.pack(fill="x", padx=10, pady=2)
                    
                    ctk.CTkLabel(frame, text=plugin.get('name', 'Unknown')).pack(side="left", padx=5)
                    status = "Loaded" if plugin.get('loaded') else "Not Loaded"
                    ctk.CTkLabel(frame, text=status, text_color="green" if plugin.get('loaded') else "gray").pack(side="right", padx=5)
                
                if not discovered:
                    ctk.CTkLabel(plugin_window, text="No plugins found. Create one with 'sysagent plugins create <name>'").pack(pady=10)
            else:
                ttk.Label(plugin_window, text="Plugin Manager", font=("", 14, "bold")).pack(pady=10)
                
                for plugin in discovered:
                    text = f"{plugin.get('name', 'Unknown')} - {'Loaded' if plugin.get('loaded') else 'Not Loaded'}"
                    ttk.Label(plugin_window, text=text).pack(anchor="w", padx=10)
                
                if not discovered:
                    ttk.Label(plugin_window, text="No plugins found").pack(pady=10)
        except Exception as e:
            if USE_CUSTOMTKINTER:
                ctk.CTkLabel(plugin_window, text=f"Error: {e}").pack(pady=20)
            else:
                ttk.Label(plugin_window, text=f"Error: {e}").pack(pady=20)

    def _show_shortcuts(self):
        """Show keyboard shortcuts."""
        shortcuts = """
Keyboard Shortcuts:

Ctrl+N    - New Chat
Ctrl+D    - Show Dashboard  
Ctrl+S    - Open Settings
Ctrl+T    - Open Terminal
Ctrl+Q    - Quit

In Chat:
Enter     - Send message
Shift+Enter - New line

In Terminal:
Enter     - Run command
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def _show_dashboard(self):
        """Show the dashboard view."""
        self._clear_content()
        self.current_view = "dashboard"
        
        from .dashboard import DashboardWindow
        
        # Embed dashboard in the content frame
        if USE_CUSTOMTKINTER:
            # Create sidebar
            sidebar = ctk.CTkFrame(self.content_frame, width=200, corner_radius=0)
            sidebar.pack(side="left", fill="y")
            sidebar.pack_propagate(False)
            
            # Logo
            logo = ctk.CTkLabel(
                sidebar,
                text="🧠 SysAgent",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            logo.pack(pady=30)
            
            # Navigation buttons
            nav_buttons = [
                ("🏠 Dashboard", self._show_dashboard),
                ("💻 System Info", self._view_system_info),
                ("📊 Processes", self._view_processes),
                ("📁 Files", self._view_files),
                ("🌐 Network", self._view_network),
                ("⚙️ Settings", self._show_settings),
            ]
            
            for text, command in nav_buttons:
                btn = ctk.CTkButton(
                    sidebar,
                    text=text,
                    command=command,
                    width=180,
                    height=35,
                    anchor="w"
                )
                btn.pack(pady=3, padx=10)
            
            # Main content
            main_content = ctk.CTkFrame(self.content_frame)
            main_content.pack(side="right", fill="both", expand=True)
            
            # Dashboard content
            self._create_dashboard_content(main_content)
        else:
            ttk.Label(
                self.content_frame,
                text="Dashboard View",
                font=("Helvetica", 18, "bold")
            ).pack(pady=20)

    def _create_dashboard_content(self, parent):
        """Create dashboard content."""
        try:
            import psutil
            PSUTIL_AVAILABLE = True
        except ImportError:
            PSUTIL_AVAILABLE = False
        
        if USE_CUSTOMTKINTER:
            # Title
            title = ctk.CTkLabel(
                parent,
                text="System Dashboard",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20, padx=20, anchor="w")
            
            # Stats grid
            stats_frame = ctk.CTkFrame(parent)
            stats_frame.pack(fill="x", padx=20, pady=10)
            
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                stats = [
                    ("CPU Usage", f"{cpu_percent}%", self._get_color(cpu_percent)),
                    ("Memory", f"{memory.percent}%", self._get_color(memory.percent)),
                    ("Disk", f"{disk.percent}%", self._get_color(disk.percent)),
                    ("Processes", str(len(psutil.pids())), "blue"),
                ]
                
                for i, (label, value, color) in enumerate(stats):
                    box = ctk.CTkFrame(stats_frame)
                    box.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
                    stats_frame.grid_columnconfigure(i, weight=1)
                    
                    ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=12)).pack(pady=(15, 5))
                    ctk.CTkLabel(
                        box,
                        text=value,
                        font=ctk.CTkFont(size=28, weight="bold"),
                        text_color=color
                    ).pack(pady=(5, 15))
            
            # System info
            info_frame = ctk.CTkFrame(parent)
            info_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(
                info_frame,
                text="System Information",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", padx=15, pady=(15, 10))
            
            import platform
            from datetime import datetime
            
            info_text = f"""
Platform: {platform.system()} {platform.release()}
Machine: {platform.machine()}
Processor: {platform.processor() or 'N/A'}
Python: {platform.python_version()}
"""
            if PSUTIL_AVAILABLE:
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.now() - boot_time
                info_text += f"Uptime: {str(uptime).split('.')[0]}"
            
            ctk.CTkLabel(
                info_frame,
                text=info_text,
                font=ctk.CTkFont(size=13),
                justify="left"
            ).pack(anchor="w", padx=15, pady=(0, 15))
            
            # Quick actions
            actions_frame = ctk.CTkFrame(parent)
            actions_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(
                actions_frame,
                text="Quick Actions",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", padx=15, pady=(15, 10))
            
            btn_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(0, 15))
            
            actions = [
                ("🔄 Refresh", self._show_dashboard),
                ("🧹 Clean Temp", self._clean_temp),
                ("📊 Processes", self._view_processes),
                ("🌐 Check Net", self._check_internet),
                ("⚙️ Settings", self._show_settings),
            ]
            
            for text, command in actions:
                btn = ctk.CTkButton(btn_frame, text=text, command=command, width=100)
                btn.pack(side="left", padx=5)

    def _get_color(self, percent: float) -> str:
        """Get color based on percentage."""
        if percent < 50:
            return "green"
        elif percent < 80:
            return "orange"
        return "red"

    def _show_settings(self):
        """Show settings view."""
        self._clear_content()
        self.current_view = "settings"
        
        from .settings import SettingsWindow
        
        # Create embedded settings
        if USE_CUSTOMTKINTER:
            settings_instance = SettingsWindow()
            settings_instance._initialize_managers()
            
            # Create widgets in content frame
            title = ctk.CTkLabel(
                self.content_frame,
                text="🔑 Settings",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            # Create notebook for tabs
            notebook = ctk.CTkTabview(self.content_frame)
            notebook.pack(fill="both", expand=True, padx=20, pady=10)
            
            api_tab = notebook.add("API Keys")
            provider_tab = notebook.add("Model Providers")
            permissions_tab = notebook.add("Permissions")
            
            # Simplified API key section
            self._create_simple_api_section(api_tab, settings_instance)
            self._create_simple_provider_section(provider_tab, settings_instance)
            self._create_simple_permissions_section(permissions_tab, settings_instance)
            
            # Back button
            back_btn = ctk.CTkButton(
                self.content_frame,
                text="← Back to Dashboard",
                command=self._show_dashboard,
                width=150
            )
            back_btn.pack(pady=10)
        else:
            ttk.Label(
                self.content_frame,
                text="Settings",
                font=("Helvetica", 18, "bold")
            ).pack(pady=20)

    def _create_simple_api_section(self, parent, settings_instance):
        """Create simplified API key section."""
        if USE_CUSTOMTKINTER:
            # OpenAI
            frame = ctk.CTkFrame(parent)
            frame.pack(fill="x", pady=10, padx=10)
            
            ctk.CTkLabel(frame, text="OpenAI API Key", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            import os
            openai_key = os.environ.get("OPENAI_API_KEY", "")
            
            entry = ctk.CTkEntry(frame, placeholder_text="sk-...", show="*", width=400)
            entry.pack(fill="x", padx=10, pady=(0, 10))
            if openai_key:
                entry.insert(0, openai_key)
            
            settings_instance.openai_api_key_entry = entry
            
            # Save button
            save_btn = ctk.CTkButton(
                parent,
                text="Save API Keys",
                command=settings_instance._save_api_keys,
                width=200
            )
            save_btn.pack(pady=20)

    def _create_simple_provider_section(self, parent, settings_instance):
        """Create simplified provider section."""
        if USE_CUSTOMTKINTER:
            frame = ctk.CTkFrame(parent)
            frame.pack(fill="x", pady=10, padx=10)
            
            ctk.CTkLabel(frame, text="Model Provider", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            settings_instance.provider_var = tk.StringVar(value="openai")
            
            providers = [("OpenAI", "openai"), ("Ollama", "ollama"), ("Anthropic", "anthropic")]
            
            for text, value in providers:
                rb = ctk.CTkRadioButton(frame, text=text, variable=settings_instance.provider_var, value=value)
                rb.pack(anchor="w", padx=20, pady=2)
            
            ctk.CTkLabel(frame, text="Model Name", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(20, 5))
            
            settings_instance.model_entry = ctk.CTkEntry(frame, placeholder_text="gpt-4", width=300)
            settings_instance.model_entry.pack(fill="x", padx=10, pady=(0, 10))
            settings_instance.model_entry.insert(0, "gpt-4")
            
            save_btn = ctk.CTkButton(
                parent,
                text="Save Provider Settings",
                command=settings_instance._save_provider_settings,
                width=200
            )
            save_btn.pack(pady=20)

    def _create_simple_permissions_section(self, parent, settings_instance):
        """Create simplified permissions section."""
        if USE_CUSTOMTKINTER:
            frame = ctk.CTkFrame(parent)
            frame.pack(fill="both", expand=True, pady=10, padx=10)
            
            ctk.CTkLabel(frame, text="Permissions", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            permissions = [
                ("file_access", "File Access"),
                ("system_info", "System Info"),
                ("process_management", "Process Management"),
                ("network_access", "Network Access"),
                ("system_control", "System Control"),
                ("code_execution", "Code Execution"),
            ]
            
            settings_instance.permission_vars = {}
            
            for perm_key, perm_name in permissions:
                var = tk.BooleanVar(value=settings_instance._get_permission_status(perm_key))
                settings_instance.permission_vars[perm_key] = var
                
                cb = ctk.CTkCheckBox(frame, text=perm_name, variable=var)
                cb.pack(anchor="w", padx=20, pady=2)
            
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkButton(
                btn_frame,
                text="Grant All",
                command=settings_instance._grant_all_permissions,
                width=100
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                btn_frame,
                text="Revoke All",
                command=settings_instance._revoke_all_permissions,
                fg_color="red",
                width=100
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                parent,
                text="Save Permissions",
                command=settings_instance._save_permissions,
                width=200
            ).pack(pady=20)

    def _view_system_info(self):
        """View system information."""
        self._clear_content()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                self.content_frame,
                text="System Information",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            try:
                from ..core.config import ConfigManager
                from ..core.permissions import PermissionManager
                from ..tools.base import ToolExecutor
                from ..tools import SystemInfoTool
                
                config_manager = ConfigManager()
                permission_manager = PermissionManager(config_manager)
                executor = ToolExecutor(permission_manager)
                executor.register_tool(SystemInfoTool())
                
                result = executor.execute_tool("system_info_tool", action="overview")
                
                scroll = ctk.CTkScrollableFrame(self.content_frame)
                scroll.pack(fill="both", expand=True, padx=20, pady=10)
                
                if result.success:
                    self._display_data(scroll, result.data)
                else:
                    ctk.CTkLabel(scroll, text=result.message).pack()
                    
            except Exception as e:
                ctk.CTkLabel(self.content_frame, text=f"Error: {e}").pack()
            
            ctk.CTkButton(
                self.content_frame,
                text="← Back",
                command=self._show_dashboard,
                width=100
            ).pack(pady=10)

    def _display_data(self, parent, data, level=0):
        """Display dictionary data recursively."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    if USE_CUSTOMTKINTER:
                        frame = ctk.CTkFrame(parent)
                        frame.pack(fill="x", pady=5, padx=level*20)
                        ctk.CTkLabel(
                            frame,
                            text=str(key).replace("_", " ").title(),
                            font=ctk.CTkFont(weight="bold")
                        ).pack(anchor="w", padx=10, pady=5)
                        self._display_data(frame, value, level + 1)
                else:
                    text = f"{str(key).replace('_', ' ').title()}: {value}"
                    if USE_CUSTOMTKINTER:
                        ctk.CTkLabel(parent, text=text).pack(anchor="w", padx=10 + level*20, pady=2)

    def _view_processes(self):
        """View processes."""
        self._show_process_list()

    def _show_process_list(self):
        """Show process list in a new window."""
        if not PSUTIL_AVAILABLE:
            messagebox.showerror("Error", "psutil is required for process management")
            return
        
        # Create a new window
        if USE_CUSTOMTKINTER:
            proc_window = ctk.CTkToplevel(self.root)
        else:
            proc_window = tk.Toplevel(self.root)
        
        proc_window.title("Process Manager")
        proc_window.geometry("800x600")
        
        # Create treeview for processes
        columns = ("PID", "Name", "CPU %", "Memory %", "Status")
        
        if USE_CUSTOMTKINTER:
            # Frame for treeview
            tree_frame = ctk.CTkFrame(proc_window)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Use ttk.Treeview inside customtkinter
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        else:
            tree_frame = ttk.Frame(proc_window)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100 if col != "Name" else 200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        
        # Populate processes
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = proc.info
                    tree.insert("", "end", values=(
                        info['pid'],
                        info['name'][:30] if info['name'] else "N/A",
                        f"{info['cpu_percent']:.1f}" if info['cpu_percent'] else "0.0",
                        f"{info['memory_percent']:.1f}" if info['memory_percent'] else "0.0",
                        info['status'] if info['status'] else "N/A"
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list processes: {e}")
        
        # Buttons frame
        if USE_CUSTOMTKINTER:
            btn_frame = ctk.CTkFrame(proc_window)
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            refresh_btn = ctk.CTkButton(btn_frame, text="Refresh", command=lambda: self._refresh_processes(tree))
            refresh_btn.pack(side="left", padx=5)
            
            kill_btn = ctk.CTkButton(btn_frame, text="Kill Process", command=lambda: self._kill_selected_process(tree), fg_color="red")
            kill_btn.pack(side="left", padx=5)
        else:
            btn_frame = ttk.Frame(proc_window)
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Button(btn_frame, text="Refresh", command=lambda: self._refresh_processes(tree)).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="Kill Process", command=lambda: self._kill_selected_process(tree)).pack(side="left", padx=5)

    def _refresh_processes(self, tree):
        """Refresh process list."""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Repopulate
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = proc.info
                    tree.insert("", "end", values=(
                        info['pid'],
                        info['name'][:30] if info['name'] else "N/A",
                        f"{info['cpu_percent']:.1f}" if info['cpu_percent'] else "0.0",
                        f"{info['memory_percent']:.1f}" if info['memory_percent'] else "0.0",
                        info['status'] if info['status'] else "N/A"
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh: {e}")

    def _kill_selected_process(self, tree):
        """Kill the selected process."""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a process to kill")
            return
        
        item = tree.item(selected[0])
        pid = int(item['values'][0])
        name = item['values'][1]
        
        if messagebox.askyesno("Confirm", f"Kill process {name} (PID: {pid})?"):
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                messagebox.showinfo("Success", f"Process {name} terminated")
                self._refresh_processes(tree)
            except psutil.NoSuchProcess:
                messagebox.showinfo("Info", "Process no longer exists")
                self._refresh_processes(tree)
            except psutil.AccessDenied:
                messagebox.showerror("Error", "Access denied. Try running with elevated privileges.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to kill process: {e}")

    def _view_files(self):
        """View files."""
        self._show_file_browser()

    def _show_file_browser(self):
        """Show a simple file browser."""
        from pathlib import Path
        
        if USE_CUSTOMTKINTER:
            file_window = ctk.CTkToplevel(self.root)
        else:
            file_window = tk.Toplevel(self.root)
        
        file_window.title("File Browser")
        file_window.geometry("600x500")
        
        current_path = Path.home()
        
        # Path entry
        if USE_CUSTOMTKINTER:
            path_frame = ctk.CTkFrame(file_window)
            path_frame.pack(fill="x", padx=10, pady=10)
            path_entry = ctk.CTkEntry(path_frame, width=400)
            path_entry.pack(side="left", padx=5)
            path_entry.insert(0, str(current_path))
        else:
            path_frame = ttk.Frame(file_window)
            path_frame.pack(fill="x", padx=10, pady=10)
            path_entry = ttk.Entry(path_frame, width=50)
            path_entry.pack(side="left", padx=5)
            path_entry.insert(0, str(current_path))
        
        # File list
        file_list = tk.Listbox(file_window, font=("Courier", 10))
        file_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        def refresh_files():
            path = Path(path_entry.get())
            file_list.delete(0, tk.END)
            
            if path.exists() and path.is_dir():
                file_list.insert(tk.END, "..")
                try:
                    for item in sorted(path.iterdir()):
                        prefix = "[D] " if item.is_dir() else "[F] "
                        file_list.insert(tk.END, prefix + item.name)
                except PermissionError:
                    file_list.insert(tk.END, "(Permission Denied)")
        
        def on_double_click(event):
            selection = file_list.curselection()
            if selection:
                item = file_list.get(selection[0])
                if item == "..":
                    new_path = Path(path_entry.get()).parent
                elif item.startswith("[D] "):
                    new_path = Path(path_entry.get()) / item[4:]
                else:
                    return
                path_entry.delete(0, tk.END)
                path_entry.insert(0, str(new_path))
                refresh_files()
        
        file_list.bind("<Double-Button-1>", on_double_click)
        refresh_files()

    def _view_network(self):
        """View network."""
        self._show_network_info()

    def _show_network_info(self):
        """Show network information."""
        if USE_CUSTOMTKINTER:
            net_window = ctk.CTkToplevel(self.root)
        else:
            net_window = tk.Toplevel(self.root)
        
        net_window.title("Network Information")
        net_window.geometry("600x400")
        
        # Text area for network info
        if USE_CUSTOMTKINTER:
            text_frame = ctk.CTkFrame(net_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            text = tk.Text(text_frame, font=("Courier", 10), wrap="word")
        else:
            text_frame = ttk.Frame(net_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            text = tk.Text(text_frame, font=("Courier", 10), wrap="word")
        
        text.pack(fill="both", expand=True)
        
        # Get network info
        import socket
        info = []
        
        try:
            hostname = socket.gethostname()
            info.append(f"Hostname: {hostname}")
            info.append(f"Local IP: {socket.gethostbyname(hostname)}")
        except:
            info.append("Could not get hostname/IP")
        
        if PSUTIL_AVAILABLE:
            info.append("\nNetwork Interfaces:")
            for iface, addrs in psutil.net_if_addrs().items():
                info.append(f"\n  {iface}:")
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        info.append(f"    IPv4: {addr.address}")
                    elif addr.family == socket.AF_INET6:
                        info.append(f"    IPv6: {addr.address}")
            
            info.append("\nNetwork I/O:")
            net_io = psutil.net_io_counters()
            info.append(f"  Bytes Sent: {net_io.bytes_sent / (1024*1024):.2f} MB")
            info.append(f"  Bytes Received: {net_io.bytes_recv / (1024*1024):.2f} MB")
        
        text.insert("1.0", "\n".join(info))
        text.config(state="disabled")

    def _clean_temp(self):
        """Clean temp files."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..tools.base import ToolExecutor
            from ..tools import FileTool
            
            config_manager = ConfigManager()
            permission_manager = PermissionManager(config_manager)
            executor = ToolExecutor(permission_manager)
            executor.register_tool(FileTool())
            
            result = executor.execute_tool("file_tool", action="cleanup")
            messagebox.showinfo("Cleanup", result.message)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _organize_downloads(self):
        """Organize downloads."""
        from pathlib import Path
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..tools.base import ToolExecutor
            from ..tools import FileTool
            
            config_manager = ConfigManager()
            permission_manager = PermissionManager(config_manager)
            executor = ToolExecutor(permission_manager)
            executor.register_tool(FileTool())
            
            result = executor.execute_tool("file_tool", action="organize", source_dir=str(Path.home() / "Downloads"))
            messagebox.showinfo("Organize", result.message)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _check_internet(self):
        """Check internet connection."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..tools.base import ToolExecutor
            from ..tools import NetworkTool
            
            config_manager = ConfigManager()
            permission_manager = PermissionManager(config_manager)
            executor = ToolExecutor(permission_manager)
            executor.register_tool(NetworkTool())
            
            result = executor.execute_tool("network_tool", action="ping", host="google.com")
            if result.success:
                messagebox.showinfo("Internet", "Internet connection is working!")
            else:
                messagebox.showerror("Internet", "No internet connection")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _run_cli_command(self):
        """Run a CLI command."""
        if USE_CUSTOMTKINTER:
            command = ctk.CTkInputDialog(
                text="Enter command:",
                title="Run CLI Command"
            ).get_input()
            
            if command:
                messagebox.showinfo("CLI", f"Command: {command}\nUse CLI for full functionality.")
        else:
            messagebox.showinfo("CLI", "Use the command line for CLI commands")

    def _show_docs(self):
        """Show documentation."""
        import webbrowser
        webbrowser.open("https://github.com/sysagent/sysagent-cli")

    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About SysAgent",
            "SysAgent v0.1.0\n\n"
            "Secure, intelligent command-line assistant\n"
            "for OS automation and control.\n\n"
            "https://github.com/sysagent/sysagent-cli"
        )

    def _on_exit(self):
        """Handle exit."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.root.destroy()

    def run(self):
        """Run the main window."""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
