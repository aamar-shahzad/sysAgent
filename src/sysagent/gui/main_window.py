"""
Main GUI Window for SysAgent - Full-featured intelligent assistant.
Includes all smart features: learning, monitoring, snippets, shortcuts.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List, Dict, Any
import threading
import time
from datetime import datetime

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

# Import smart features
try:
    from ..core.smart_learning import get_learning_system
    LEARNING_AVAILABLE = True
except ImportError:
    LEARNING_AVAILABLE = False

try:
    from ..core.proactive_monitor import get_monitor, start_monitoring
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False

try:
    from ..core.smart_clipboard import get_smart_clipboard
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


# Theme colors
COLORS = {
    "bg": "#0a0a0f",
    "bg_secondary": "#12121a",
    "bg_tertiary": "#1a1a24",
    "sidebar": "#0d0d14",
    "border": "#2a2a35",
    "text": "#ffffff",
    "text_secondary": "#9898a8",
    "text_muted": "#5a5a6a",
    "accent": "#4a6cf7",
    "accent_hover": "#5a7cff",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "error": "#ef4444",
}


class MainWindow:
    """Main application window with all smart features."""

    def __init__(self):
        self.root = None
        self.current_view = "chat"
        self.current_theme = "dark"
        self.agent = None
        self.chat_interface = None
        self.command_palette = None
        self.proactive_agent = None
        self.toast_frame = None
        self.current_mode = "general"
        self.session_manager = None
        self.learning = None
        self.monitor = None
        
        self._initialize_agent()
        self._initialize_smart_features()
        self._create_window()
        self._create_layout()
        self._setup_keyboard_shortcuts()
        self._start_background_tasks()

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
    
    def _initialize_smart_features(self):
        """Initialize all smart features."""
        # Session Manager
        try:
            from ..core.session_manager import SessionManager
            self.session_manager = SessionManager()
            sessions = self.session_manager.list_sessions(limit=1)
            if sessions:
                self.session_manager.load_session(sessions[0]['id'])
            else:
                self.session_manager.create_session()
        except Exception:
            self.session_manager = None
        
        # Learning System
        if LEARNING_AVAILABLE:
            try:
                self.learning = get_learning_system()
            except Exception:
                self.learning = None
        
        # Monitor
        if MONITOR_AVAILABLE:
            try:
                self.monitor = get_monitor()
            except Exception:
                self.monitor = None

    def _create_window(self):
        """Create the main window."""
        if USE_CUSTOMTKINTER:
            ctk.set_appearance_mode(self.current_theme)
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
            self.root.configure(fg_color=COLORS["bg"])
        else:
            self.root = tk.Tk()
        
        self.root.title("SysAgent")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 700)
        
        return self.root

    def _create_layout(self):
        """Create the main layout."""
        if not USE_CUSTOMTKINTER:
            self._create_simple_layout()
            return
        
        # Main container
        self.main_container = ctk.CTkFrame(self.root, fg_color=COLORS["bg"])
        self.main_container.pack(fill="both", expand=True)
        
        # Create sidebar
        self._create_sidebar()
        
        # Create main content area
        self.content_area = ctk.CTkFrame(self.main_container, fg_color=COLORS["bg"])
        self.content_area.pack(side="right", fill="both", expand=True)
        
        # Create top bar
        self._create_top_bar()
        
        # Create content frame
        self.content_frame = ctk.CTkFrame(self.content_area, fg_color=COLORS["bg"])
        self.content_frame.pack(fill="both", expand=True)
        
        # Show chat by default
        self._show_chat()
    
    def _create_simple_layout(self):
        """Create simple layout for non-customtkinter."""
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill="both", expand=True)
        self._show_chat()

    def _create_sidebar(self):
        """Create the sidebar with all features."""
        sidebar = ctk.CTkFrame(
            self.main_container,
            width=240,
            corner_radius=0,
            fg_color=COLORS["sidebar"]
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Logo
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 10))
        
        ctk.CTkLabel(
            logo_frame,
            text="🧠 SysAgent",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w")
        
        # Mode indicator
        self._create_mode_indicator(sidebar)
        
        # Navigation
        self._create_nav_section(sidebar, "NAVIGATION", [
            ("💬", "Chat", self._show_chat, "chat"),
            ("📊", "Dashboard", self._show_dashboard, "dashboard"),
            ("📈", "Activity", self._show_activity, "activity"),
            ("⚙️", "Settings", self._show_settings, "settings"),
        ])
        
        # Smart Features
        self._create_nav_section(sidebar, "SMART FEATURES", [
            ("⚡", "Suggestions", self._show_suggestions, None),
            ("📌", "Snippets", self._show_snippets, None),
            ("⌨️", "Shortcuts", self._show_shortcuts, None),
            ("📜", "History", self._show_history_panel, None),
        ])
        
        # Quick Tools
        self._create_nav_section(sidebar, "QUICK TOOLS", [
            ("🏥", "Health Check", lambda: self._quick_action("Run health check"), None),
            ("💻", "System Info", lambda: self._quick_action("Show system info"), None),
            ("🔍", "Search Files", lambda: self._quick_action("Search for files"), None),
            ("🖥️", "Terminal", self._show_terminal, "terminal"),
        ])
        
        # Status panel at bottom
        self._create_status_panel(sidebar)
    
    def _create_mode_indicator(self, parent):
        """Create mode indicator."""
        mode_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_tertiary"], corner_radius=8)
        mode_frame.pack(fill="x", padx=12, pady=(0, 15))
        
        inner = ctk.CTkFrame(mode_frame, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        # Get current mode
        mode_icon = "🧠"
        mode_name = "General"
        mode_color = COLORS["accent"]
        
        try:
            from ..core.agent_modes import get_mode_manager
            mm = get_mode_manager()
            config = mm.get_config()
            mode_icon = config.icon
            mode_name = config.display_name
            mode_color = config.color
        except Exception:
            pass
        
        ctk.CTkLabel(
            inner,
            text=f"{mode_icon} {mode_name}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=mode_color
        ).pack(side="left")
        
        ctk.CTkButton(
            inner,
            text="Change",
            width=55,
            height=22,
            corner_radius=4,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=COLORS["bg_secondary"],
            text_color=COLORS["text_muted"],
            command=self._show_mode_selector
        ).pack(side="right")
    
    def _create_nav_section(self, parent, title: str, items: list):
        """Create a navigation section."""
        # Section title
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=16, pady=(15, 8))
        
        # Items
        for icon, label, command, view_id in items:
            is_active = view_id and view_id == self.current_view
            
            btn = ctk.CTkButton(
                parent,
                text=f"  {icon}  {label}",
                anchor="w",
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(size=13),
                fg_color=COLORS["accent"] if is_active else "transparent",
                hover_color=COLORS["accent_hover"] if is_active else COLORS["bg_tertiary"],
                text_color=COLORS["text"],
                command=command
            )
            btn.pack(fill="x", padx=8, pady=2)
    
    def _create_status_panel(self, parent):
        """Create status panel at bottom of sidebar."""
        status_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_tertiary"], corner_radius=8)
        status_frame.pack(side="bottom", fill="x", padx=12, pady=12)
        
        inner = ctk.CTkFrame(status_frame, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        # System stats
        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory().percent
                
                # CPU
                cpu_frame = ctk.CTkFrame(inner, fg_color="transparent")
                cpu_frame.pack(fill="x", pady=2)
                ctk.CTkLabel(
                    cpu_frame,
                    text="CPU",
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS["text_muted"],
                    width=35
                ).pack(side="left")
                
                cpu_bar = ctk.CTkProgressBar(cpu_frame, width=100, height=6)
                cpu_bar.set(cpu / 100)
                cpu_bar.pack(side="left", padx=5)
                
                cpu_color = COLORS["success"] if cpu < 70 else COLORS["warning"] if cpu < 90 else COLORS["error"]
                ctk.CTkLabel(
                    cpu_frame,
                    text=f"{cpu:.0f}%",
                    font=ctk.CTkFont(size=10),
                    text_color=cpu_color,
                    width=35
                ).pack(side="left")
                
                # Memory
                mem_frame = ctk.CTkFrame(inner, fg_color="transparent")
                mem_frame.pack(fill="x", pady=2)
                ctk.CTkLabel(
                    mem_frame,
                    text="RAM",
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS["text_muted"],
                    width=35
                ).pack(side="left")
                
                mem_bar = ctk.CTkProgressBar(mem_frame, width=100, height=6)
                mem_bar.set(mem / 100)
                mem_bar.pack(side="left", padx=5)
                
                mem_color = COLORS["success"] if mem < 70 else COLORS["warning"] if mem < 90 else COLORS["error"]
                ctk.CTkLabel(
                    mem_frame,
                    text=f"{mem:.0f}%",
                    font=ctk.CTkFont(size=10),
                    text_color=mem_color,
                    width=35
                ).pack(side="left")
            except Exception:
                pass
        
        # Alerts indicator
        alert_count = 0
        if self.monitor:
            try:
                alerts = self.monitor.get_active_alerts()
                alert_count = len(alerts)
            except Exception:
                pass
        
        if alert_count > 0:
            alert_frame = ctk.CTkFrame(inner, fg_color="transparent")
            alert_frame.pack(fill="x", pady=(8, 0))
            
            ctk.CTkButton(
                alert_frame,
                text=f"🔔 {alert_count} Alert{'s' if alert_count > 1 else ''}",
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color=COLORS["warning"],
                hover_color=COLORS["error"],
                command=self._show_alerts
            ).pack(fill="x")

    def _create_top_bar(self):
        """Create top bar with search and actions."""
        top_bar = ctk.CTkFrame(self.content_area, fg_color=COLORS["bg_secondary"], height=56)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        
        inner = ctk.CTkFrame(top_bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=10)
        
        # Search / Command palette button
        search_btn = ctk.CTkButton(
            inner,
            text="🔍  Search or type a command...  ⌘K",
            width=350,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_muted"],
            anchor="w",
            command=self._toggle_command_palette
        )
        search_btn.pack(side="left")
        
        # Right side actions
        right_frame = ctk.CTkFrame(inner, fg_color="transparent")
        right_frame.pack(side="right")
        
        # Quick actions
        actions = [
            ("📋", "Clipboard", self._show_clipboard),
            ("🔔", "Alerts", self._show_alerts),
            ("➕", "New Chat", self._new_chat),
        ]
        
        for icon, tooltip, cmd in actions:
            btn = ctk.CTkButton(
                right_frame,
                text=icon,
                width=36,
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(size=16),
                fg_color="transparent",
                hover_color=COLORS["bg_tertiary"],
                command=cmd
            )
            btn.pack(side="left", padx=2)

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.root.bind("<Control-k>", lambda e: self._toggle_command_palette())
        self.root.bind("<Command-k>", lambda e: self._toggle_command_palette())
        self.root.bind("<Control-n>", lambda e: self._new_chat())
        self.root.bind("<Control-s>", lambda e: self._show_settings())
        self.root.bind("<Control-q>", lambda e: self._on_exit())
        self.root.bind("<Escape>", lambda e: self._close_popups())
    
    def _start_background_tasks(self):
        """Start background tasks."""
        # Start monitoring if available
        if MONITOR_AVAILABLE and self.monitor:
            try:
                self.monitor.start()
            except Exception:
                pass
        
        # Refresh status periodically
        self._schedule_status_refresh()
    
    def _schedule_status_refresh(self):
        """Schedule periodic status refresh."""
        def refresh():
            try:
                # Refresh would happen here
                pass
            except Exception:
                pass
            finally:
                try:
                    self.root.after(30000, refresh)  # Every 30 seconds
                except Exception:
                    pass
        
        try:
            self.root.after(30000, refresh)
        except Exception:
            pass

    # ==================== VIEW METHODS ====================
    
    def _clear_content(self):
        """Clear content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _show_chat(self):
        """Show chat view."""
        self._clear_content()
        self.current_view = "chat"
        
        from .chat import ChatInterface
        self.chat_interface = ChatInterface(self.content_frame, on_send=self._on_chat_message)
    
    def _show_dashboard(self):
        """Show dashboard view."""
        self._clear_content()
        self.current_view = "dashboard"
        
        if not USE_CUSTOMTKINTER:
            ttk.Label(self.content_frame, text="Dashboard").pack(pady=20)
            return
        
        # Dashboard content
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color=COLORS["bg"])
        scroll.pack(fill="both", expand=True)
        
        # Title
        ctk.CTkLabel(
            scroll,
            text="📊 System Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 15))
        
        # Stats cards
        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        stats = self._get_system_stats()
        
        for i, (title, value, icon, color) in enumerate(stats):
            card = ctk.CTkFrame(stats_frame, fg_color=COLORS["bg_secondary"], corner_radius=12)
            card.grid(row=0, column=i, padx=8, pady=8, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=20, pady=20)
            
            ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=28)).pack()
            ctk.CTkLabel(
                inner,
                text=value,
                font=ctk.CTkFont(size=32, weight="bold"),
                text_color=color
            ).pack(pady=(10, 5))
            ctk.CTkLabel(
                inner,
                text=title,
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_muted"]
            ).pack()
        
        # Quick actions
        ctk.CTkLabel(
            scroll,
            text="Quick Actions",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        actions_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20)
        
        quick_actions = [
            ("🏥 Health Check", "Run health check"),
            ("🧹 Clean Temp", "Clean temporary files"),
            ("📊 Top Processes", "Show top processes"),
            ("🌐 Network Status", "Check network status"),
            ("🔒 Security Scan", "Run security scan"),
        ]
        
        for text, cmd in quick_actions:
            btn = ctk.CTkButton(
                actions_frame,
                text=text,
                height=40,
                corner_radius=8,
                fg_color=COLORS["bg_tertiary"],
                hover_color=COLORS["border"],
                command=lambda c=cmd: self._quick_action(c)
            )
            btn.pack(side="left", padx=5, pady=5)
    
    def _get_system_stats(self) -> list:
        """Get system statistics."""
        stats = []
        
        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                cpu_color = COLORS["success"] if cpu < 70 else COLORS["warning"] if cpu < 90 else COLORS["error"]
                mem_color = COLORS["success"] if mem.percent < 70 else COLORS["warning"] if mem.percent < 90 else COLORS["error"]
                disk_color = COLORS["success"] if disk.percent < 70 else COLORS["warning"] if disk.percent < 90 else COLORS["error"]
                
                stats = [
                    ("CPU Usage", f"{cpu:.0f}%", "🔥", cpu_color),
                    ("Memory", f"{mem.percent:.0f}%", "💾", mem_color),
                    ("Disk", f"{disk.percent:.0f}%", "💿", disk_color),
                    ("Processes", str(len(psutil.pids())), "📋", COLORS["accent"]),
                ]
            except Exception:
                pass
        
        if not stats:
            stats = [
                ("CPU", "N/A", "🔥", COLORS["text_muted"]),
                ("Memory", "N/A", "💾", COLORS["text_muted"]),
                ("Disk", "N/A", "💿", COLORS["text_muted"]),
                ("Processes", "N/A", "📋", COLORS["text_muted"]),
            ]
        
        return stats
    
    def _show_activity(self):
        """Show activity view."""
        self._clear_content()
        self.current_view = "activity"
        
        if not USE_CUSTOMTKINTER:
            ttk.Label(self.content_frame, text="Activity").pack(pady=20)
            return
        
        try:
            from .activity_dashboard import ActivityDashboard
            dashboard = ActivityDashboard.create(self.content_frame)
        except Exception as e:
            ctk.CTkLabel(
                self.content_frame,
                text=f"Activity dashboard unavailable: {e}",
                text_color=COLORS["text_muted"]
            ).pack(pady=40)
    
    def _show_settings(self):
        """Show settings view."""
        self._clear_content()
        self.current_view = "settings"
        
        if not USE_CUSTOMTKINTER:
            ttk.Label(self.content_frame, text="Settings").pack(pady=20)
            return
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color=COLORS["bg"])
        scroll.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            scroll,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 15))
        
        # API Key section
        self._create_settings_section(scroll, "🔑 API Configuration", [
            ("OpenAI API Key", "OPENAI_API_KEY", True),
        ])
        
        # Model section
        self._create_settings_section(scroll, "🤖 Model Settings", [
            ("Model Name", "gpt-4o-mini", False),
        ])
        
        # Monitoring section
        self._create_monitoring_settings(scroll)
    
    def _create_settings_section(self, parent, title: str, fields: list):
        """Create a settings section."""
        section = ctk.CTkFrame(parent, fg_color=COLORS["bg_secondary"], corner_radius=12)
        section.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=16, pady=(16, 10))
        
        for label, default, is_secret in fields:
            field_frame = ctk.CTkFrame(section, fg_color="transparent")
            field_frame.pack(fill="x", padx=16, pady=5)
            
            ctk.CTkLabel(
                field_frame,
                text=label,
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w")
            
            entry = ctk.CTkEntry(
                field_frame,
                placeholder_text=default,
                show="*" if is_secret else "",
                height=36
            )
            entry.pack(fill="x", pady=(5, 0))
        
        ctk.CTkButton(
            section,
            text="Save",
            width=100,
            height=32,
            corner_radius=6
        ).pack(anchor="w", padx=16, pady=16)
    
    def _create_monitoring_settings(self, parent):
        """Create monitoring settings."""
        section = ctk.CTkFrame(parent, fg_color=COLORS["bg_secondary"], corner_radius=12)
        section.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            section,
            text="🔔 Monitoring Thresholds",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=16, pady=(16, 10))
        
        thresholds = [
            ("CPU Warning", "80%"),
            ("Memory Warning", "80%"),
            ("Disk Warning", "80%"),
        ]
        
        for label, default in thresholds:
            row = ctk.CTkFrame(section, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=5)
            
            ctk.CTkLabel(row, text=label, width=120).pack(side="left")
            
            entry = ctk.CTkEntry(row, width=80, placeholder_text=default)
            entry.pack(side="left", padx=10)
        
        ctk.CTkLabel(section, text="", height=10).pack()
    
    def _show_terminal(self):
        """Show terminal view."""
        self._clear_content()
        self.current_view = "terminal"
        
        if not USE_CUSTOMTKINTER:
            ttk.Label(self.content_frame, text="Terminal").pack(pady=20)
            return
        
        # Terminal header
        header = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_secondary"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="🖥️ Terminal",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=16, pady=12)
        
        # Output area
        self.terminal_output = ctk.CTkTextbox(
            self.content_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLORS["bg"],
            text_color=COLORS["text"]
        )
        self.terminal_output.pack(fill="both", expand=True, padx=10, pady=5)
        self.terminal_output.insert("end", "$ Welcome to SysAgent Terminal\n$ Type commands below\n\n")
        
        # Input area
        input_frame = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_secondary"])
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="$", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10, 5))
        
        self.terminal_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter command...",
            height=36,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.terminal_input.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        self.terminal_input.bind("<Return>", self._run_terminal_command)
        
        ctk.CTkButton(
            input_frame,
            text="Run",
            width=60,
            height=32,
            command=self._run_terminal_command
        ).pack(side="right", padx=10)

    # ==================== SMART FEATURE POPUPS ====================
    
    def _show_suggestions(self):
        """Show smart suggestions popup."""
        if not USE_CUSTOMTKINTER:
            return
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("Smart Suggestions")
        popup.geometry("500x400")
        popup.transient(self.root)
        popup.configure(fg_color=COLORS["bg"])
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=COLORS["bg_secondary"])
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="⚡ Smart Suggestions",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=16)
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        if not self.learning:
            ctk.CTkLabel(content, text="Learning system not available", text_color=COLORS["text_muted"]).pack(pady=30)
            return
        
        # Time-based suggestions
        ctk.CTkLabel(content, text="Based on your patterns:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        time_sugg = self.learning.get_time_based_suggestions()
        if time_sugg:
            for s in time_sugg:
                self._create_suggestion_card(content, s['command'], s['reason'], popup)
        else:
            ctk.CTkLabel(content, text="No patterns detected yet", text_color=COLORS["text_muted"]).pack(anchor="w", padx=10)
        
        # Most used
        ctk.CTkLabel(content, text="Most used commands:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(20, 5))
        
        most_used = self.learning.get_most_used_commands(5)
        for cmd, count in most_used:
            self._create_suggestion_card(content, cmd, f"Used {count} times", popup)
    
    def _create_suggestion_card(self, parent, command: str, reason: str, popup):
        """Create a suggestion card."""
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_secondary"], corner_radius=8)
        card.pack(fill="x", pady=3)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        text_frame = ctk.CTkFrame(inner, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame,
            text=command[:50],
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
            text=reason,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkButton(
            inner,
            text="Use",
            width=50,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            command=lambda: self._use_suggestion(command, popup)
        ).pack(side="right")
    
    def _use_suggestion(self, command: str, popup):
        """Use a suggestion."""
        popup.destroy()
        self._show_chat()
        self.root.after(100, lambda: self._quick_action(command))
    
    def _show_snippets(self):
        """Show snippets popup."""
        if not USE_CUSTOMTKINTER:
            return
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("Snippets")
        popup.geometry("550x450")
        popup.transient(self.root)
        popup.configure(fg_color=COLORS["bg"])
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=COLORS["bg_secondary"])
        header.pack(fill="x")
        
        h_inner = ctk.CTkFrame(header, fg_color="transparent")
        h_inner.pack(fill="x", padx=16, pady=12)
        
        ctk.CTkLabel(h_inner, text="📌 Snippets", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        ctk.CTkButton(
            h_inner,
            text="+ New",
            width=70,
            height=28,
            corner_radius=6,
            command=lambda: self._create_snippet(popup)
        ).pack(side="right")
        
        # Search
        search = ctk.CTkEntry(popup, placeholder_text="Search snippets...", height=36)
        search.pack(fill="x", padx=16, pady=10)
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=5)
        
        def render_snippets(query=""):
            for w in content.winfo_children():
                w.destroy()
            
            snippets = []
            if self.learning:
                snippets = self.learning.search_snippets(query)
            
            if not snippets:
                ctk.CTkLabel(content, text="No snippets found", text_color=COLORS["text_muted"]).pack(pady=30)
                return
            
            for snip in snippets:
                card = ctk.CTkFrame(content, fg_color=COLORS["bg_secondary"], corner_radius=8)
                card.pack(fill="x", pady=3)
                
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=12, pady=10)
                
                fav = "⭐ " if snip.get('is_favorite') else ""
                ctk.CTkLabel(
                    inner,
                    text=f"{fav}{snip['name']}",
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(anchor="w")
                
                ctk.CTkLabel(
                    inner,
                    text=snip['command'][:60],
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_secondary"]
                ).pack(anchor="w")
                
                btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
                btn_frame.pack(anchor="e", pady=(5, 0))
                
                ctk.CTkButton(
                    btn_frame,
                    text="Use",
                    width=50,
                    height=24,
                    corner_radius=4,
                    font=ctk.CTkFont(size=10),
                    command=lambda c=snip['command']: self._use_suggestion(c, popup)
                ).pack(side="left", padx=2)
        
        search.bind("<KeyRelease>", lambda e: render_snippets(search.get()))
        render_snippets()
    
    def _create_snippet(self, parent_popup):
        """Show create snippet dialog."""
        parent_popup.destroy()
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("New Snippet")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.configure(fg_color=COLORS["bg"])
        
        ctk.CTkLabel(dialog, text="Create Snippet", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=16)
        
        # Name
        ctk.CTkLabel(dialog, text="Name:", anchor="w").pack(anchor="w", padx=20)
        name_entry = ctk.CTkEntry(dialog, placeholder_text="Snippet name")
        name_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        # Command
        ctk.CTkLabel(dialog, text="Command:", anchor="w").pack(anchor="w", padx=20)
        cmd_entry = ctk.CTkEntry(dialog, placeholder_text="Command to save")
        cmd_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        # Tags
        ctk.CTkLabel(dialog, text="Tags (comma-separated):", anchor="w").pack(anchor="w", padx=20)
        tags_entry = ctk.CTkEntry(dialog, placeholder_text="tag1, tag2")
        tags_entry.pack(fill="x", padx=20, pady=(0, 20))
        
        def save():
            if self.learning and name_entry.get() and cmd_entry.get():
                tags = [t.strip() for t in tags_entry.get().split(",") if t.strip()]
                self.learning.save_snippet(name_entry.get(), cmd_entry.get(), "", tags)
                dialog.destroy()
                self._show_snippets()
        
        ctk.CTkButton(dialog, text="Save Snippet", command=save).pack(pady=10)
    
    def _show_shortcuts(self):
        """Show shortcuts popup."""
        if not USE_CUSTOMTKINTER:
            return
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("Shortcuts")
        popup.geometry("500x400")
        popup.transient(self.root)
        popup.configure(fg_color=COLORS["bg"])
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=COLORS["bg_secondary"])
        header.pack(fill="x")
        
        h_inner = ctk.CTkFrame(header, fg_color="transparent")
        h_inner.pack(fill="x", padx=16, pady=12)
        
        ctk.CTkLabel(h_inner, text="⌨️ Shortcuts", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        ctk.CTkButton(
            h_inner,
            text="+ New",
            width=70,
            height=28,
            corner_radius=6,
            command=lambda: self._create_shortcut(popup)
        ).pack(side="right")
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        shortcuts = []
        if self.learning:
            shortcuts = self.learning.list_shortcuts()
        
        if not shortcuts:
            ctk.CTkLabel(content, text="No shortcuts yet\nCreate one to get started!", text_color=COLORS["text_muted"]).pack(pady=40)
        else:
            for s in shortcuts:
                card = ctk.CTkFrame(content, fg_color=COLORS["bg_secondary"], corner_radius=8)
                card.pack(fill="x", pady=3)
                
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=12, pady=10)
                
                ctk.CTkLabel(inner, text=s['name'], font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
                ctk.CTkLabel(inner, text=s['command'], font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).pack(anchor="w")
                
                ctk.CTkButton(
                    inner,
                    text="Run",
                    width=50,
                    height=24,
                    corner_radius=4,
                    font=ctk.CTkFont(size=10),
                    command=lambda c=s['command']: self._use_suggestion(c, popup)
                ).pack(anchor="e", pady=(5, 0))
    
    def _create_shortcut(self, parent_popup):
        """Show create shortcut dialog."""
        parent_popup.destroy()
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("New Shortcut")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.configure(fg_color=COLORS["bg"])
        
        ctk.CTkLabel(dialog, text="Create Shortcut", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=16)
        
        ctk.CTkLabel(dialog, text="Shortcut name:", anchor="w").pack(anchor="w", padx=20)
        name_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., ss")
        name_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(dialog, text="Command:", anchor="w").pack(anchor="w", padx=20)
        cmd_entry = ctk.CTkEntry(dialog, placeholder_text="show system status")
        cmd_entry.pack(fill="x", padx=20, pady=(0, 20))
        
        def save():
            if self.learning and name_entry.get() and cmd_entry.get():
                self.learning.add_shortcut(name_entry.get(), cmd_entry.get())
                dialog.destroy()
                self._show_shortcuts()
        
        ctk.CTkButton(dialog, text="Save Shortcut", command=save).pack(pady=10)
    
    def _show_history_panel(self):
        """Show command history popup."""
        if not USE_CUSTOMTKINTER:
            return
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("Command History")
        popup.geometry("550x450")
        popup.transient(self.root)
        popup.configure(fg_color=COLORS["bg"])
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=COLORS["bg_secondary"])
        header.pack(fill="x")
        ctk.CTkLabel(header, text="📜 Command History", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=16)
        
        # Search
        search = ctk.CTkEntry(popup, placeholder_text="Search history...", height=36)
        search.pack(fill="x", padx=16, pady=10)
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=5)
        
        def render_history(query=""):
            for w in content.winfo_children():
                w.destroy()
            
            history = []
            if self.learning:
                history = self.learning.search_history(query, limit=50)
            
            if not history:
                ctk.CTkLabel(content, text="No history found", text_color=COLORS["text_muted"]).pack(pady=30)
                return
            
            for entry in history:
                cmd = entry.get('command', '')
                ts = entry.get('timestamp', '')[:10]
                
                row = ctk.CTkFrame(content, fg_color=COLORS["bg_secondary"], corner_radius=6)
                row.pack(fill="x", pady=2)
                
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=8)
                
                ctk.CTkLabel(inner, text=ts, font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"], width=70).pack(side="left")
                ctk.CTkLabel(inner, text=cmd[:50], font=ctk.CTkFont(size=11), anchor="w").pack(side="left", fill="x", expand=True)
                
                ctk.CTkButton(
                    inner,
                    text="Use",
                    width=45,
                    height=22,
                    corner_radius=4,
                    font=ctk.CTkFont(size=10),
                    command=lambda c=cmd: self._use_suggestion(c, popup)
                ).pack(side="right")
        
        search.bind("<KeyRelease>", lambda e: render_history(search.get()))
        render_history()
    
    def _show_alerts(self):
        """Show alerts popup."""
        if not USE_CUSTOMTKINTER:
            return
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("System Alerts")
        popup.geometry("500x400")
        popup.transient(self.root)
        popup.configure(fg_color=COLORS["bg"])
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=COLORS["bg_secondary"])
        header.pack(fill="x")
        
        h_inner = ctk.CTkFrame(header, fg_color="transparent")
        h_inner.pack(fill="x", padx=16, pady=12)
        
        ctk.CTkLabel(h_inner, text="🔔 System Alerts", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        if self.monitor:
            ctk.CTkButton(
                h_inner,
                text="Dismiss All",
                width=90,
                height=28,
                corner_radius=6,
                fg_color=COLORS["bg_tertiary"],
                command=lambda: self._dismiss_all_alerts(popup)
            ).pack(side="right")
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        alerts = []
        if self.monitor:
            alerts = self.monitor.get_active_alerts()
        
        if not alerts:
            ctk.CTkLabel(
                content,
                text="✅ No active alerts\nYour system is running smoothly!",
                text_color=COLORS["success"],
                font=ctk.CTkFont(size=14)
            ).pack(pady=50)
        else:
            for alert in alerts:
                level_color = {
                    'critical': COLORS["error"],
                    'warning': COLORS["warning"],
                    'info': COLORS["accent"]
                }.get(alert.level, COLORS["text_secondary"])
                
                card = ctk.CTkFrame(
                    content,
                    fg_color=COLORS["bg_secondary"],
                    corner_radius=8,
                    border_width=1,
                    border_color=level_color
                )
                card.pack(fill="x", pady=4)
                
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=12, pady=10)
                
                ctk.CTkLabel(inner, text=alert.title, font=ctk.CTkFont(size=13, weight="bold"), text_color=level_color).pack(anchor="w")
                ctk.CTkLabel(inner, text=alert.message, font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"], wraplength=400).pack(anchor="w", pady=(4, 0))
                
                if alert.action:
                    ctk.CTkButton(
                        inner,
                        text="Fix",
                        width=50,
                        height=26,
                        corner_radius=6,
                        font=ctk.CTkFont(size=11),
                        command=lambda a=alert.action: self._use_suggestion(a, popup)
                    ).pack(anchor="w", pady=(8, 0))
    
    def _dismiss_all_alerts(self, popup):
        """Dismiss all alerts."""
        if self.monitor:
            self.monitor.dismiss_all()
        popup.destroy()
    
    def _show_clipboard(self):
        """Show clipboard actions popup."""
        if not USE_CUSTOMTKINTER or not CLIPBOARD_AVAILABLE:
            return
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("Clipboard")
        popup.geometry("450x350")
        popup.transient(self.root)
        popup.configure(fg_color=COLORS["bg"])
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=COLORS["bg_secondary"])
        header.pack(fill="x")
        ctk.CTkLabel(header, text="📋 Smart Clipboard", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=16)
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        try:
            clipboard = get_smart_clipboard()
            
            # Get current clipboard content
            import subprocess
            import platform
            
            clip_content = ""
            try:
                if platform.system() == "Darwin":
                    result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                    clip_content = result.stdout
                elif platform.system() == "Linux":
                    result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True)
                    clip_content = result.stdout
            except Exception:
                pass
            
            if clip_content:
                entry = clipboard.process_content(clip_content)
                
                ctk.CTkLabel(content, text=f"Content Type: {entry.content_type}", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 10))
                
                # Preview
                preview_frame = ctk.CTkFrame(content, fg_color=COLORS["bg_secondary"], corner_radius=8)
                preview_frame.pack(fill="x", pady=5)
                ctk.CTkLabel(
                    preview_frame,
                    text=entry.preview,
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_secondary"],
                    wraplength=380
                ).pack(padx=12, pady=10)
                
                # Actions
                ctk.CTkLabel(content, text="Actions:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(15, 5))
                
                for action in entry.actions:
                    btn = ctk.CTkButton(
                        content,
                        text=f"{action.icon} {action.label}",
                        height=36,
                        corner_radius=8,
                        fg_color=COLORS["bg_tertiary"],
                        hover_color=COLORS["border"],
                        anchor="w",
                        command=lambda a=action.command: self._use_suggestion(a, popup)
                    )
                    btn.pack(fill="x", pady=2)
            else:
                ctk.CTkLabel(content, text="Clipboard is empty", text_color=COLORS["text_muted"]).pack(pady=30)
        except Exception as e:
            ctk.CTkLabel(content, text=f"Error: {e}", text_color=COLORS["error"]).pack(pady=30)
    
    def _show_mode_selector(self):
        """Show mode selector popup."""
        if not USE_CUSTOMTKINTER:
            return
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("Select Mode")
        popup.geometry("350x400")
        popup.transient(self.root)
        popup.configure(fg_color=COLORS["bg"])
        
        ctk.CTkLabel(popup, text="🎯 Select Agent Mode", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        modes = [
            ("🧠", "General", "general", "All-purpose assistant"),
            ("👨‍💻", "Developer", "developer", "Git, code, packages"),
            ("🔧", "SysAdmin", "sysadmin", "System administration"),
            ("🔒", "Security", "security", "Security auditing"),
            ("⚡", "Productivity", "productivity", "Apps and workflows"),
            ("🤖", "Automation", "automation", "Workflow automation"),
        ]
        
        for icon, name, mode_id, desc in modes:
            is_current = mode_id == self.current_mode
            
            btn = ctk.CTkButton(
                popup,
                text=f"  {icon}  {name}\n      {desc}",
                height=50,
                corner_radius=8,
                fg_color=COLORS["accent"] if is_current else COLORS["bg_secondary"],
                hover_color=COLORS["accent_hover"] if is_current else COLORS["bg_tertiary"],
                anchor="w",
                command=lambda m=mode_id, p=popup: self._set_mode(m, p)
            )
            btn.pack(fill="x", padx=20, pady=3)
    
    def _set_mode(self, mode: str, popup=None):
        """Set agent mode."""
        try:
            from ..core.agent_modes import get_mode_manager
            mm = get_mode_manager()
            mode_enum = mm.get_mode_by_name(mode)
            if mode_enum:
                mm.set_mode(mode_enum)
                self.current_mode = mode
                if popup:
                    popup.destroy()
                # Refresh UI
                self._refresh_layout()
        except Exception as e:
            messagebox.showerror("Error", f"Could not change mode: {e}")
    
    def _refresh_layout(self):
        """Refresh the entire layout."""
        self.main_container.destroy()
        self._create_layout()

    # ==================== ACTIONS ====================
    
    def _toggle_command_palette(self):
        """Toggle command palette."""
        try:
            from .command_palette import CommandPalette
            
            if self.command_palette is None:
                self.command_palette = CommandPalette(self.root, on_command=self._on_palette_command)
            
            if self.command_palette.popup is not None:
                self.command_palette.close()
            else:
                self.command_palette.open()
        except Exception as e:
            print(f"Warning: Could not open command palette: {e}")
    
    def _on_palette_command(self, command: str):
        """Handle command from palette."""
        if command:
            self._show_chat()
            self.root.after(100, lambda: self._quick_action(command))
    
    def _quick_action(self, action: str):
        """Execute a quick action."""
        if self.current_view != "chat":
            self._show_chat()
            self.root.after(100, lambda: self._quick_action(action))
            return
        
        if self.chat_interface:
            self.chat_interface._send_message_direct(action)
    
    def _new_chat(self):
        """Start new chat."""
        self._show_chat()
        if self.chat_interface:
            try:
                self.chat_interface.clear_chat()
            except Exception:
                pass
    
    def _close_popups(self):
        """Close any open popups."""
        if self.command_palette and self.command_palette.popup:
            self.command_palette.close()
    
    def _on_chat_message(self, message: str):
        """Handle chat message."""
        if self.agent:
            thread = threading.Thread(target=self._process_chat_message, args=(message,))
            thread.daemon = True
            thread.start()
        else:
            if self.chat_interface:
                self.chat_interface.add_message("Agent not initialized. Please configure your API key.", is_user=False, message_type="error")
    
    def _process_chat_message(self, message: str):
        """Process chat message in background."""
        start_time = time.time()
        
        try:
            # Record to learning
            if self.learning:
                self.learning.record_command(message, success=True)
            
            # Try streaming
            if hasattr(self.agent, 'process_command_streaming'):
                stream_data = None
                try:
                    self.root.after(0, lambda: setattr(self, '_stream_data', self.chat_interface.add_streaming_message()))
                    time.sleep(0.05)
                    stream_data = getattr(self, '_stream_data', None)
                except Exception:
                    pass
                
                full_response = ""
                
                for chunk in self.agent.process_command_streaming(message):
                    chunk_type = chunk.get("type", "")
                    content = chunk.get("content", "")
                    
                    if chunk_type == "content" and content:
                        full_response = content
                        if stream_data:
                            stream_data["content"] = content
                            self.root.after(0, lambda c=content: self._update_stream(stream_data, c))
                    elif chunk_type == "token" and content:
                        full_response += content
                        if stream_data:
                            self.root.after(0, lambda t=content: self.chat_interface.update_streaming_message(stream_data, t))
                    elif chunk_type == "tool_call":
                        name = chunk.get("name", "tool")
                        self.root.after(0, lambda n=name: self.chat_interface.add_execution_log(n, "", "running"))
                    elif chunk_type == "tool_result":
                        duration = int((time.time() - start_time) * 1000)
                        self.root.after(0, lambda d=duration: self.chat_interface.add_execution_log("", "", "success", d))
                    elif chunk_type == "error":
                        full_response = f"Error: {content}"
                        break
                    elif chunk_type == "done":
                        break
                
                if stream_data:
                    self.root.after(0, lambda: self.chat_interface.finish_streaming_message(stream_data))
                elif full_response:
                    self.root.after(0, lambda r=full_response: self.chat_interface.add_message(r, is_user=False))
            else:
                result = self.agent.process_command(message)
                response = result.get('message', 'Done') if result.get('success') else result.get('message', 'Error')
                msg_type = "text" if result.get('success') else "error"
                self.root.after(0, lambda: self.chat_interface.add_message(response, is_user=False, message_type=msg_type))
        
        except Exception as e:
            error_msg = str(e)
            if "context_length" in error_msg:
                error_msg = "Conversation too long. Please start a new chat."
            self.root.after(0, lambda: self.chat_interface.add_message(f"Error: {error_msg}", is_user=False, message_type="error"))
    
    def _update_stream(self, stream_data: dict, content: str):
        """Update streaming message."""
        if stream_data and "label" in stream_data:
            try:
                stream_data["label"].configure(text=content + "▌")
                stream_data["content"] = content
            except Exception:
                pass
    
    def _run_terminal_command(self, event=None):
        """Run terminal command."""
        import subprocess
        
        if not hasattr(self, 'terminal_input'):
            return
        
        command = self.terminal_input.get()
        self.terminal_input.delete(0, "end")
        
        if not command.strip():
            return
        
        self.terminal_output.insert("end", f"$ {command}\n")
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            if result.stdout:
                self.terminal_output.insert("end", result.stdout)
            if result.stderr:
                self.terminal_output.insert("end", f"[stderr] {result.stderr}")
            self.terminal_output.insert("end", "\n")
        except subprocess.TimeoutExpired:
            self.terminal_output.insert("end", "[Timeout]\n\n")
        except Exception as e:
            self.terminal_output.insert("end", f"[Error: {e}]\n\n")
        
        self.terminal_output.see("end")
    
    def _on_exit(self):
        """Handle exit."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            if self.monitor:
                try:
                    self.monitor.stop()
                except Exception:
                    pass
            self.root.destroy()
    
    def run(self):
        """Run the application."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)
        self.root.mainloop()


def launch_gui():
    """Launch the main GUI."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    launch_gui()
