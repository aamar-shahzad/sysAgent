"""
Smooth, Polished Chat Interface for SysAgent.
Optimized for smoothness and responsiveness like CLI.
Includes smart learning integration, favorites, and proactive suggestions.
Now with search, context menus, drag & drop, and better animations.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import re
import time
import os
from typing import Optional, Callable, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

# Import smart features
try:
    from ..core.smart_learning import get_learning_system
    LEARNING_AVAILABLE = True
except ImportError:
    LEARNING_AVAILABLE = False
    def get_learning_system():
        return None

try:
    from ..core.proactive_monitor import get_monitor
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    def get_monitor():
        return None

try:
    from ..core.deep_agent import DeepAgent, ReasoningStep
    DEEP_AGENT_AVAILABLE = True
except ImportError:
    DEEP_AGENT_AVAILABLE = False


class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"
    TOOL = "tool"


@dataclass
class ChatMessage:
    content: str
    msg_type: MessageType
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


# Clean, minimal color scheme
COLORS = {
    "bg": "#0a0a0f",
    "bg_secondary": "#12121a",
    "bg_hover": "#1a1a24",
    "bg_input": "#0f0f15",
    "border": "#2a2a35",
    "border_focus": "#4a6cf7",
    "text": "#ffffff",
    "text_secondary": "#9898a8",
    "text_muted": "#5a5a6a",
    "accent": "#4a6cf7",
    "accent_hover": "#5a7cff",
    "user_bg": "#4a6cf7",
    "success": "#22c55e",
    "error": "#ef4444",
    "warning": "#f59e0b",
    "code_bg": "#15151f",
}


class SmoothLabel(ctk.CTkLabel if CTK_AVAILABLE else object):
    """Label with smooth text updates."""
    
    def __init__(self, *args, **kwargs):
        if CTK_AVAILABLE:
            super().__init__(*args, **kwargs)
    
    def smooth_update(self, text: str):
        """Update text smoothly."""
        try:
            self.configure(text=text)
        except Exception:
            pass


class TypingIndicator:
    """Smooth typing/thinking indicator."""
    
    def __init__(self, parent, colors: dict):
        self.parent = parent
        self.colors = colors
        self.frame = None
        self.dots = []
        self.running = False
        self.animation_idx = 0
    
    def show(self):
        """Show typing indicator with smooth animation."""
        if not CTK_AVAILABLE:
            return
        
        self.running = True
        
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent"
        )
        self.frame.pack(fill="x", padx=16, pady=8)
        
        row = ctk.CTkFrame(self.frame, fg_color="transparent")
        row.pack(anchor="w")
        
        # Avatar
        ctk.CTkLabel(
            row,
            text="🧠",
            font=ctk.CTkFont(size=22)
        ).pack(side="left", padx=(0, 10))
        
        # Dots container
        dots_frame = ctk.CTkFrame(
            row,
            fg_color=self.colors["bg_secondary"],
            corner_radius=12
        )
        dots_frame.pack(side="left", padx=4, pady=8)
        
        inner = ctk.CTkFrame(dots_frame, fg_color="transparent")
        inner.pack(padx=16, pady=10)
        
        # Three dots
        for i in range(3):
            dot = ctk.CTkLabel(
                inner,
                text="●",
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_muted"],
                width=12
            )
            dot.pack(side="left", padx=2)
            self.dots.append(dot)
        
        self._animate()
    
    def _animate(self):
        """Smooth dot animation."""
        if not self.running or not self.frame:
            return
        
        try:
            for i, dot in enumerate(self.dots):
                if i == self.animation_idx % 3:
                    dot.configure(text_color=self.colors["accent"])
                else:
                    dot.configure(text_color=self.colors["text_muted"])
            
            self.animation_idx += 1
            self.frame.after(300, self._animate)
        except Exception:
            pass
    
    def hide(self):
        """Hide indicator smoothly."""
        self.running = False
        if self.frame:
            try:
                self.frame.destroy()
            except Exception:
                pass
        self.frame = None
        self.dots = []


class ReasoningPanel:
    """Panel showing agent's reasoning process."""
    
    def __init__(self, parent, colors: dict):
        self.parent = parent
        self.colors = colors
        self.frame = None
        self.steps_frame = None
        self.is_visible = False
    
    def show(self):
        """Show reasoning panel."""
        if not CTK_AVAILABLE or self.is_visible:
            return
        
        self.is_visible = True
        
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors["bg_secondary"],
            corner_radius=10,
            border_width=1,
            border_color=self.colors["accent"]
        )
        self.frame.pack(fill="x", padx=16, pady=8)
        
        # Header
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 5))
        
        ctk.CTkLabel(
            header,
            text="🧠 Agent Reasoning",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["accent"]
        ).pack(side="left")
        
        # Steps container
        self.steps_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.steps_frame.pack(fill="x", padx=12, pady=(0, 10))
    
    def add_step(self, step_type: str, content: str):
        """Add a reasoning step."""
        if not self.steps_frame or not CTK_AVAILABLE:
            return
        
        icons = {
            "planning": "📋",
            "analysis": "🔍",
            "execution": "▶️",
            "reflection": "🪞",
            "error_recovery": "🔧",
            "tool_selection": "🔧",
        }
        
        icon = icons.get(step_type, "•")
        
        step_frame = ctk.CTkFrame(self.steps_frame, fg_color="transparent")
        step_frame.pack(fill="x", anchor="w", pady=2)
        
        ctk.CTkLabel(
            step_frame,
            text=f"{icon} {content}",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(side="left")
    
    def set_progress(self, current: int, total: int, description: str):
        """Show progress bar."""
        if not self.steps_frame or not CTK_AVAILABLE:
            return
        
        # Clear and add progress
        for w in self.steps_frame.winfo_children():
            w.destroy()
        
        progress_frame = ctk.CTkFrame(self.steps_frame, fg_color="transparent")
        progress_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            progress_frame,
            text=f"Step {current}/{total}: {description[:40]}...",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text"]
        ).pack(anchor="w")
        
        bar = ctk.CTkProgressBar(progress_frame, width=300, height=8)
        bar.set(current / total if total > 0 else 0)
        bar.pack(anchor="w", pady=(5, 0))
    
    def hide(self):
        """Hide reasoning panel."""
        self.is_visible = False
        if self.frame:
            try:
                self.frame.destroy()
            except Exception:
                pass
        self.frame = None
        self.steps_frame = None


class ApprovalDialog:
    """Dialog for human-in-the-loop approvals."""
    
    def __init__(self, parent, colors: dict, title: str, description: str,
                 on_approve: Callable, on_deny: Callable, options: List[str] = None):
        self.parent = parent
        self.colors = colors
        self.title = title
        self.description = description
        self.on_approve = on_approve
        self.on_deny = on_deny
        self.options = options or ["Approve", "Deny"]
        self.frame = None
        self.result = None
        
        self._show()
    
    def _show(self):
        """Show approval dialog."""
        if not CTK_AVAILABLE:
            return
        
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors["bg_secondary"],
            corner_radius=12,
            border_width=2,
            border_color=self.colors["warning"]
        )
        self.frame.pack(fill="x", padx=16, pady=12)
        
        # Header
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 8))
        
        ctk.CTkLabel(
            header,
            text="⚠️ Approval Required",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["warning"]
        ).pack(side="left")
        
        # Content
        content = ctk.CTkFrame(self.frame, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 8))
        
        ctk.CTkLabel(
            content,
            text=self.title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            content,
            text=self.description,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"],
            wraplength=450
        ).pack(anchor="w", pady=(4, 0))
        
        # Buttons
        buttons = ctk.CTkFrame(self.frame, fg_color="transparent")
        buttons.pack(fill="x", padx=16, pady=(8, 12))
        
        # Remember checkbox
        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            buttons,
            text="Remember my choice",
            variable=self.remember_var,
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"],
            checkbox_height=18,
            checkbox_width=18
        ).pack(side="left")
        
        # Deny button
        ctk.CTkButton(
            buttons,
            text=self.options[1] if len(self.options) > 1 else "Deny",
            width=80,
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["error"],
            hover_color="#dc2626",
            command=self._on_deny
        ).pack(side="right", padx=4)
        
        # Approve button
        ctk.CTkButton(
            buttons,
            text=self.options[0] if self.options else "Approve",
            width=80,
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["success"],
            hover_color="#16a34a",
            command=self._on_approve
        ).pack(side="right", padx=4)
    
    def _on_approve(self):
        """Handle approval."""
        self.result = True
        remember = self.remember_var.get()
        self._hide()
        if self.on_approve:
            self.on_approve(remember)
    
    def _on_deny(self):
        """Handle denial."""
        self.result = False
        remember = self.remember_var.get()
        self._hide()
        if self.on_deny:
            self.on_deny(remember)
    
    def _hide(self):
        """Hide dialog."""
        if self.frame:
            try:
                self.frame.destroy()
            except Exception:
                pass
        self.frame = None


class ToolIndicator:
    """Smooth tool execution indicator."""
    
    def __init__(self, parent, colors: dict):
        self.parent = parent
        self.colors = colors
        self.frame = None
        self.running = False
        self.start_time = None
    
    def show(self, tool_name: str):
        """Show tool indicator."""
        if not CTK_AVAILABLE:
            return
        
        self.running = True
        self.start_time = time.time()
        
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors["bg_secondary"],
            corner_radius=8
        )
        self.frame.pack(fill="x", padx=56, pady=4)
        
        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)
        
        # Spinner
        self.spinner = ctk.CTkLabel(
            inner,
            text="◐",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["accent"],
            width=18
        )
        self.spinner.pack(side="left")
        
        # Tool name
        name = tool_name.replace("_", " ").title()
        ctk.CTkLabel(
            inner,
            text=name,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        ).pack(side="left", padx=(6, 0))
        
        # Duration
        self.duration_label = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_muted"]
        )
        self.duration_label.pack(side="right")
        
        self._animate()
    
    def _animate(self):
        """Animate spinner."""
        if not self.running or not self.frame:
            return
        
        try:
            spinners = ["◐", "◓", "◑", "◒"]
            current = self.spinner.cget("text")
            idx = spinners.index(current) if current in spinners else 0
            self.spinner.configure(text=spinners[(idx + 1) % 4])
            
            if self.start_time:
                elapsed = int((time.time() - self.start_time) * 1000)
                self.duration_label.configure(text=f"{elapsed}ms")
            
            self.frame.after(80, self._animate)
        except Exception:
            pass
    
    def complete(self, success: bool = True):
        """Mark complete."""
        self.running = False
        if not self.frame:
            return
        
        try:
            icon = "✓" if success else "✗"
            color = self.colors["success"] if success else self.colors["error"]
            self.spinner.configure(text=icon, text_color=color)
        except Exception:
            pass
    
    def hide(self):
        """Hide indicator."""
        self.running = False
        if self.frame:
            try:
                self.frame.destroy()
            except Exception:
                pass
        self.frame = None


class ChatInterface:
    """Smooth, polished chat interface."""
    
    def __init__(self, parent, on_send: Optional[Callable[[str], None]] = None,
                 on_file_drop: Optional[Callable[[List[str]], None]] = None):
        self.parent = parent
        self.on_send = on_send
        self.on_file_drop = on_file_drop
        self.messages: List[ChatMessage] = []
        self.message_widgets: List[Tuple[ctk.CTkFrame, ChatMessage]] = []  # Track message widgets
        self.message_queue = queue.Queue()
        self.is_processing = False
        self.last_query = ""
        self.command_history: List[str] = []
        self.history_index = -1
        self.colors = COLORS
        
        self.typing_indicator: Optional[TypingIndicator] = None
        self.tool_indicator: Optional[ToolIndicator] = None
        self.reasoning_panel: Optional[ReasoningPanel] = None
        self.stream_data: Optional[Dict] = None
        self.show_reasoning = True  # Toggle for showing reasoning
        self.search_mode = False
        self.search_query = ""
        self.search_results: List[int] = []
        self.current_search_index = 0
        
        self._create_ui()
        self._start_queue_processor()
        self._setup_drag_drop()
    
    def _create_ui(self):
        """Create smooth UI."""
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(self.parent, fg_color=self.colors["bg"])
        else:
            self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        self._create_header()
        self._create_messages_area()
        self._create_input_area()
        self._show_welcome()
    
    def _create_header(self):
        """Create minimal header."""
        if not CTK_AVAILABLE:
            return
        
        self.header_frame = ctk.CTkFrame(self.frame, fg_color=self.colors["bg_secondary"], height=48)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)
        
        # Left side
        left = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        left.pack(side="left", pady=10, padx=16)
        
        ctk.CTkLabel(
            left,
            text="SysAgent",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        ).pack(side="left")
        
        # Status
        self.status_dot = ctk.CTkLabel(
            left,
            text="●",
            font=ctk.CTkFont(size=6),
            text_color=self.colors["success"]
        )
        self.status_dot.pack(side="left", padx=(12, 4))
        
        self.status_text = ctk.CTkLabel(
            left,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        )
        self.status_text.pack(side="left")
        
        # Right side
        right = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right.pack(side="right", pady=8, padx=12)
        
        # Search button
        self.search_btn = ctk.CTkButton(
            right,
            text="🔍",
            width=32,
            height=32,
            corner_radius=6,
            fg_color="transparent",
            hover_color=self.colors["bg_hover"],
            command=self._toggle_search
        )
        self.search_btn.pack(side="left", padx=2)
        
        # Alerts button (shows if there are alerts)
        self.alerts_btn = ctk.CTkButton(
            right,
            text="🔔",
            width=32,
            height=32,
            corner_radius=6,
            fg_color="transparent",
            hover_color=self.colors["bg_hover"],
            command=self._show_alerts
        )
        self.alerts_btn.pack(side="left", padx=2)
        self._update_alerts_badge()
        
        for icon, cmd in [("🗑", self.clear_chat), ("📤", self._export_chat)]:
            btn = ctk.CTkButton(
                right,
                text=icon,
                width=32,
                height=32,
                corner_radius=6,
                fg_color="transparent",
                hover_color=self.colors["bg_hover"],
                command=cmd
            )
            btn.pack(side="left", padx=2)
        
        # Search bar (initially hidden)
        self.search_frame = ctk.CTkFrame(self.frame, fg_color=self.colors["bg_secondary"], height=50)
        self._search_visible = False
    
    def _update_alerts_badge(self):
        """Update alerts button badge."""
        if not CTK_AVAILABLE or not hasattr(self, 'alerts_btn'):
            return
        
        alert_count = 0
        if MONITOR_AVAILABLE:
            try:
                monitor = get_monitor()
                if monitor:
                    alerts = monitor.get_active_alerts()
                    alert_count = len(alerts)
            except Exception:
                pass
        
        if alert_count > 0:
            self.alerts_btn.configure(
                text=f"🔔{alert_count}",
                text_color=self.colors["warning"]
            )
        else:
            self.alerts_btn.configure(
                text="🔔",
                text_color=self.colors["text_secondary"]
            )
    
    def _show_alerts(self):
        """Show alerts popup."""
        if not CTK_AVAILABLE:
            return
        
        popup = ctk.CTkToplevel(self.parent)
        popup.title("Alerts")
        popup.geometry("450x350")
        popup.transient(self.parent)
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=self.colors["bg_secondary"])
        header.pack(fill="x")
        
        h_inner = ctk.CTkFrame(header, fg_color="transparent")
        h_inner.pack(fill="x", padx=16, pady=12)
        
        ctk.CTkLabel(
            h_inner,
            text="🔔 System Alerts",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            h_inner,
            text="Dismiss All",
            width=90,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color=self.colors["bg_hover"],
            command=lambda: self._dismiss_all_alerts(popup)
        ).pack(side="right")
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=self.colors["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        alerts = []
        if MONITOR_AVAILABLE:
            try:
                monitor = get_monitor()
                if monitor:
                    alerts = monitor.get_active_alerts()
            except Exception:
                pass
        
        if not alerts:
            ctk.CTkLabel(
                content,
                text="✅ No active alerts\nYour system is running smoothly!",
                text_color=self.colors["success"],
                font=ctk.CTkFont(size=13)
            ).pack(pady=40)
        else:
            for alert in alerts:
                level_color = {
                    'critical': self.colors["error"],
                    'warning': self.colors["warning"],
                    'info': self.colors["accent"]
                }.get(alert.level, self.colors["text_secondary"])
                
                row = ctk.CTkFrame(
                    content,
                    fg_color=self.colors["bg_secondary"],
                    corner_radius=8,
                    border_width=1,
                    border_color=level_color
                )
                row.pack(fill="x", pady=4)
                
                row_inner = ctk.CTkFrame(row, fg_color="transparent")
                row_inner.pack(fill="x", padx=12, pady=10)
                
                # Title
                ctk.CTkLabel(
                    row_inner,
                    text=alert.title,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=level_color
                ).pack(anchor="w")
                
                # Message
                ctk.CTkLabel(
                    row_inner,
                    text=alert.message,
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_secondary"],
                    wraplength=380
                ).pack(anchor="w", pady=(4, 0))
                
                # Action button if available
                if alert.action:
                    ctk.CTkButton(
                        row_inner,
                        text=alert.suggestion or "Fix",
                        height=26,
                        corner_radius=6,
                        font=ctk.CTkFont(size=10),
                        fg_color=self.colors["accent"],
                        command=lambda a=alert.action, p=popup: self._execute_alert_action(a, p)
                    ).pack(anchor="w", pady=(8, 0))
    
    def _dismiss_all_alerts(self, popup):
        """Dismiss all alerts."""
        if MONITOR_AVAILABLE:
            try:
                monitor = get_monitor()
                if monitor:
                    monitor.dismiss_all()
            except Exception:
                pass
        popup.destroy()
        self._update_alerts_badge()
    
    def _execute_alert_action(self, action: str, popup):
        """Execute an alert action."""
        popup.destroy()
        self._quick_send(action)
        self._update_alerts_badge()
    
    def _create_messages_area(self):
        """Create messages area."""
        if not CTK_AVAILABLE:
            self.messages_frame = ttk.Frame(self.frame)
            self.messages_frame.pack(fill="both", expand=True)
            return
        
        self.messages_frame = ctk.CTkScrollableFrame(
            self.frame,
            fg_color=self.colors["bg"]
        )
        self.messages_frame.pack(fill="both", expand=True)
    
    def _create_input_area(self):
        """Create smooth input area."""
        if not CTK_AVAILABLE:
            self.input_field = ttk.Entry(self.frame)
            self.input_field.pack(fill="x", padx=10, pady=10)
            self.input_field.bind("<Return>", lambda e: self._send())
            return
        
        # Container
        container = ctk.CTkFrame(self.frame, fg_color=self.colors["bg_secondary"])
        container.pack(fill="x", side="bottom")
        
        inner = ctk.CTkFrame(container, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        
        # Input wrapper
        input_wrapper = ctk.CTkFrame(
            inner,
            fg_color=self.colors["bg_input"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"]
        )
        input_wrapper.pack(fill="x")
        
        input_inner = ctk.CTkFrame(input_wrapper, fg_color="transparent")
        input_inner.pack(fill="x", padx=4, pady=4)
        
        # File attachment button
        attach_btn = ctk.CTkButton(
            input_inner,
            text="📎",
            width=36,
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=self.colors["bg_hover"],
            command=self._browse_files
        )
        attach_btn.pack(side="left", padx=4)
        
        # Text input
        self.input_field = ctk.CTkTextbox(
            input_inner,
            height=44,
            fg_color="transparent",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text"],
            wrap="word",
            border_width=0
        )
        self.input_field.pack(side="left", fill="both", expand=True, padx=8, pady=4)
        
        # Placeholder
        self._placeholder = "Message SysAgent..."
        self._placeholder_active = True
        self._show_placeholder()
        
        # Send button
        self.send_btn = ctk.CTkButton(
            input_inner,
            text="↑",
            width=36,
            height=36,
            corner_radius=18,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            command=self._send
        )
        self.send_btn.pack(side="right", padx=4)
        
        # Bindings
        self.input_field.bind("<FocusIn>", self._on_focus_in)
        self.input_field.bind("<FocusOut>", self._on_focus_out)
        self.input_field.bind("<Return>", self._on_return)
        self.input_field.bind("<Shift-Return>", lambda e: None)
        self.input_field.bind("<Up>", self._on_history_up)
        self.input_field.bind("<Down>", self._on_history_down)
        
        # Store wrapper for focus styling
        self._input_wrapper = input_wrapper
        
        # Quick actions
        self._create_quick_actions(container)
    
    def _create_quick_actions(self, parent):
        """Create quick action chips with smart suggestions."""
        if not CTK_AVAILABLE:
            return
        
        actions_frame = ctk.CTkFrame(parent, fg_color="transparent")
        actions_frame.pack(fill="x", padx=16, pady=(0, 12))
        
        # Get smart suggestions if available
        actions = self._get_smart_suggestions()
        
        for text, cmd in actions[:5]:
            btn = ctk.CTkButton(
                actions_frame,
                text=text,
                height=28,
                corner_radius=14,
                font=ctk.CTkFont(size=11),
                fg_color=self.colors["bg_hover"],
                hover_color=self.colors["border"],
                text_color=self.colors["text_secondary"],
                command=lambda c=cmd: self._quick_send(c)
            )
            btn.pack(side="left", padx=3)
        
        # Add favorites button
        fav_btn = ctk.CTkButton(
            actions_frame,
            text="⭐",
            width=28,
            height=28,
            corner_radius=14,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_hover"],
            hover_color=self.colors["border"],
            text_color=self.colors["warning"],
            command=self._show_favorites
        )
        fav_btn.pack(side="right", padx=3)
        
        # Add history button
        hist_btn = ctk.CTkButton(
            actions_frame,
            text="📜",
            width=28,
            height=28,
            corner_radius=14,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_hover"],
            hover_color=self.colors["border"],
            text_color=self.colors["text_secondary"],
            command=self._show_history
        )
        hist_btn.pack(side="right", padx=3)
    
    def _get_smart_suggestions(self) -> List[tuple]:
        """Get smart suggestions based on learning."""
        default_actions = [
            ("📊 Status", "Show system status"),
            ("🏥 Health", "Run health check"),
            ("💾 Disk", "Check disk space"),
            ("🔍 Search", "Search for files"),
        ]
        
        if not LEARNING_AVAILABLE:
            return default_actions
        
        try:
            learning = get_learning_system()
            if not learning:
                return default_actions
            
            # Get time-based suggestions
            time_suggestions = learning.get_time_based_suggestions()
            if time_suggestions:
                smart_actions = []
                for s in time_suggestions[:2]:
                    cmd = s.get('command', '')
                    if cmd:
                        # Get first word as label
                        label = cmd.split()[0].title() if cmd else "Run"
                        smart_actions.append((f"⚡ {label}", cmd))
                smart_actions.extend(default_actions[:3])
                return smart_actions
            
            # Get most used commands
            most_used = learning.get_most_used_commands(3)
            if most_used:
                smart_actions = []
                for cmd, count in most_used:
                    label = cmd.split()[0].title() if cmd else "Run"
                    smart_actions.append((f"🔄 {label}", cmd))
                smart_actions.extend(default_actions[:2])
                return smart_actions
        except Exception:
            pass
        
        return default_actions
    
    def _show_favorites(self):
        """Show favorites popup."""
        if not CTK_AVAILABLE:
            return
        
        popup = ctk.CTkToplevel(self.parent)
        popup.title("Favorites")
        popup.geometry("400x300")
        popup.transient(self.parent)
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=self.colors["bg_secondary"])
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="⭐ Favorites",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=12)
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=self.colors["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        favorites = []
        if LEARNING_AVAILABLE:
            try:
                learning = get_learning_system()
                if learning:
                    favorites = learning.get_favorites()
            except Exception:
                pass
        
        if not favorites:
            ctk.CTkLabel(
                content,
                text="No favorites yet.\nSave commands as favorites from history.",
                text_color=self.colors["text_muted"],
                font=ctk.CTkFont(size=12)
            ).pack(pady=30)
        else:
            for fav in favorites:
                row = ctk.CTkFrame(content, fg_color=self.colors["bg_hover"], corner_radius=8)
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(
                    row,
                    text=fav.get('name', 'Unnamed'),
                    font=ctk.CTkFont(weight="bold")
                ).pack(anchor="w", padx=10, pady=(8, 2))
                
                ctk.CTkLabel(
                    row,
                    text=fav.get('command', '')[:50],
                    text_color=self.colors["text_secondary"],
                    font=ctk.CTkFont(size=11)
                ).pack(anchor="w", padx=10, pady=(0, 8))
                
                row.bind("<Button-1>", lambda e, c=fav.get('command', ''): self._use_favorite(c, popup))
    
    def _use_favorite(self, command: str, popup):
        """Use a favorite command."""
        popup.destroy()
        self._quick_send(command)
    
    def _show_history(self):
        """Show command history popup."""
        if not CTK_AVAILABLE:
            return
        
        popup = ctk.CTkToplevel(self.parent)
        popup.title("History")
        popup.geometry("500x400")
        popup.transient(self.parent)
        
        # Header with search
        header = ctk.CTkFrame(popup, fg_color=self.colors["bg_secondary"])
        header.pack(fill="x")
        
        ctk.CTkLabel(
            header,
            text="📜 Command History",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(12, 8))
        
        search_entry = ctk.CTkEntry(
            header,
            placeholder_text="Search history...",
            width=300
        )
        search_entry.pack(pady=(0, 12))
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=self.colors["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        def render_history(query: str = ""):
            # Clear
            for w in content.winfo_children():
                w.destroy()
            
            history = []
            if LEARNING_AVAILABLE:
                try:
                    learning = get_learning_system()
                    if learning:
                        history = learning.search_history(query, limit=30)
                except Exception:
                    pass
            
            # Also include local command history
            for cmd in self.command_history[-20:]:
                if not query or query.lower() in cmd.lower():
                    history.append({'command': cmd, 'timestamp': ''})
            
            if not history:
                ctk.CTkLabel(
                    content,
                    text="No history found",
                    text_color=self.colors["text_muted"]
                ).pack(pady=30)
                return
            
            for entry in history[:30]:
                cmd = entry.get('command', '')
                if not cmd:
                    continue
                
                row = ctk.CTkFrame(content, fg_color=self.colors["bg_hover"], corner_radius=6)
                row.pack(fill="x", pady=2)
                
                row_inner = ctk.CTkFrame(row, fg_color="transparent")
                row_inner.pack(fill="x", padx=10, pady=8)
                
                ctk.CTkLabel(
                    row_inner,
                    text=cmd[:60] + ("..." if len(cmd) > 60 else ""),
                    font=ctk.CTkFont(size=12),
                    anchor="w"
                ).pack(side="left", fill="x", expand=True)
                
                # Use button
                ctk.CTkButton(
                    row_inner,
                    text="Use",
                    width=50,
                    height=24,
                    corner_radius=4,
                    font=ctk.CTkFont(size=10),
                    fg_color=self.colors["accent"],
                    command=lambda c=cmd: self._use_history(c, popup)
                ).pack(side="right")
        
        search_entry.bind("<KeyRelease>", lambda e: render_history(search_entry.get()))
        render_history()
    
    def _use_history(self, command: str, popup):
        """Use a command from history."""
        popup.destroy()
        self._quick_send(command)
    
    def _show_placeholder(self):
        """Show placeholder."""
        self._placeholder_active = True
        self.input_field.delete("1.0", "end")
        self.input_field.insert("1.0", self._placeholder)
        self.input_field.configure(text_color=self.colors["text_muted"])
    
    def _on_focus_in(self, event):
        """Handle focus in."""
        if CTK_AVAILABLE:
            self._input_wrapper.configure(border_color=self.colors["border_focus"])
        if self._placeholder_active:
            self.input_field.delete("1.0", "end")
            self.input_field.configure(text_color=self.colors["text"])
            self._placeholder_active = False
    
    def _on_focus_out(self, event):
        """Handle focus out."""
        if CTK_AVAILABLE:
            self._input_wrapper.configure(border_color=self.colors["border"])
        content = self.input_field.get("1.0", "end").strip()
        if not content:
            self._show_placeholder()
    
    def _on_return(self, event):
        """Handle enter key."""
        if not (event.state & 0x1):  # Shift not pressed
            self._send()
            return "break"
    
    def _on_history_up(self, event):
        """Navigate history up."""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self._set_input_text(self.command_history[-(self.history_index + 1)])
        return "break"
    
    def _on_history_down(self, event):
        """Navigate history down."""
        if self.history_index > 0:
            self.history_index -= 1
            self._set_input_text(self.command_history[-(self.history_index + 1)])
        elif self.history_index == 0:
            self.history_index = -1
            self._set_input_text("")
        return "break"
    
    def _set_input_text(self, text: str):
        """Set input text."""
        self.input_field.delete("1.0", "end")
        if text:
            self.input_field.insert("1.0", text)
            self._placeholder_active = False
            self.input_field.configure(text_color=self.colors["text"])
        else:
            self._show_placeholder()
    
    def _quick_send(self, message: str):
        """Send quick action."""
        self._set_input_text(message)
        self._send()
    
    def _send(self):
        """Send message."""
        content = self.input_field.get("1.0", "end").strip()
        
        if self._placeholder_active or not content or self.is_processing:
            return
        
        # Clear input
        self.input_field.delete("1.0", "end")
        self._show_placeholder()
        
        # Add to history
        if content and (not self.command_history or self.command_history[-1] != content):
            self.command_history.append(content)
        self.history_index = -1
        self.last_query = content
        
        # Record to learning system
        if LEARNING_AVAILABLE:
            try:
                learning = get_learning_system()
                if learning:
                    learning.record_command(content, success=True)
            except Exception:
                pass
        
        # Add user message
        self._add_message(content, MessageType.USER)
        
        # Start processing
        self._set_processing(True)
        
        # Show typing indicator
        self._show_typing()
        
        # Send
        if self.on_send:
            self.on_send(content)
        else:
            self._hide_typing()
            self._add_message("No agent connected.", MessageType.ERROR)
            self._set_processing(False)
    
    def _send_message_direct(self, message: str):
        """Send message directly."""
        self._set_input_text(message)
        self._send()
    
    def _set_processing(self, processing: bool):
        """Set processing state."""
        self.is_processing = processing
        
        if not CTK_AVAILABLE:
            return
        
        try:
            if processing:
                self.status_dot.configure(text_color=self.colors["warning"])
                self.status_text.configure(text="Processing...")
                self.send_btn.configure(state="disabled")
            else:
                self.status_dot.configure(text_color=self.colors["success"])
                self.status_text.configure(text="Ready")
                self.send_btn.configure(state="normal")
        except Exception:
            pass
    
    def _show_typing(self):
        """Show typing indicator."""
        self._hide_typing()
        self.typing_indicator = TypingIndicator(self.messages_frame, self.colors)
        self.typing_indicator.show()
        self._scroll_to_bottom()
    
    def _hide_typing(self):
        """Hide typing indicator."""
        if self.typing_indicator:
            self.typing_indicator.hide()
            self.typing_indicator = None
    
    def _show_reasoning(self):
        """Show reasoning panel."""
        if not self.show_reasoning:
            return
        self._hide_reasoning()
        self.reasoning_panel = ReasoningPanel(self.messages_frame, self.colors)
        self.reasoning_panel.show()
        self._scroll_to_bottom()
    
    def _hide_reasoning(self):
        """Hide reasoning panel."""
        if self.reasoning_panel:
            self.reasoning_panel.hide()
            self.reasoning_panel = None
    
    def add_reasoning_step(self, step_type: str, content: str):
        """Add a reasoning step to the panel."""
        if not self.reasoning_panel:
            self._show_reasoning()
        if self.reasoning_panel:
            self.reasoning_panel.add_step(step_type, content)
            self._scroll_to_bottom()
    
    def update_reasoning_progress(self, current: int, total: int, description: str):
        """Update reasoning progress."""
        if not self.reasoning_panel:
            self._show_reasoning()
        if self.reasoning_panel:
            self.reasoning_panel.set_progress(current, total, description)
            self._scroll_to_bottom()
    
    def _add_message(self, content: str, msg_type: MessageType):
        """Add message."""
        message = ChatMessage(content=content, msg_type=msg_type)
        self.messages.append(message)
        self._render_message(message)
    
    def _render_message(self, message: ChatMessage):
        """Render message smoothly."""
        if not CTK_AVAILABLE:
            return
        
        try:
            if not self.messages_frame.winfo_exists():
                return
        except Exception:
            return
        
        container = ctk.CTkFrame(self.messages_frame, fg_color="transparent", corner_radius=8)
        container.pack(fill="x", padx=16, pady=6)
        
        # Track widget for search
        self.message_widgets.append((container, message))
        
        # Bind context menu
        container.bind("<Button-3>", lambda e, m=message: self._show_message_context_menu(e, m))
        container.bind("<Button-2>", lambda e, m=message: self._show_message_context_menu(e, m))  # macOS
        
        if message.msg_type == MessageType.USER:
            self._render_user(container, message)
        elif message.msg_type == MessageType.ASSISTANT:
            self._render_assistant(container, message)
        elif message.msg_type == MessageType.ERROR:
            self._render_error(container, message)
        elif message.msg_type == MessageType.SYSTEM:
            self._render_system(container, message)
        
        self._scroll_to_bottom()
    
    def _render_user(self, container, message: ChatMessage):
        """Render user message."""
        bubble = ctk.CTkFrame(
            container,
            fg_color=self.colors["user_bg"],
            corner_radius=16
        )
        bubble.pack(anchor="e")
        
        ctk.CTkLabel(
            bubble,
            text=message.content,
            font=ctk.CTkFont(size=14),
            text_color="white",
            wraplength=450,
            justify="right"
        ).pack(padx=16, pady=10)
    
    def _render_assistant(self, container, message: ChatMessage):
        """Render assistant message."""
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(anchor="w", fill="x")
        
        # Avatar
        ctk.CTkLabel(
            row,
            text="🧠",
            font=ctk.CTkFont(size=22)
        ).pack(side="left", anchor="n", padx=(0, 10))
        
        # Content
        content_frame = ctk.CTkFrame(row, fg_color="transparent")
        content_frame.pack(side="left", fill="x", expand=True)
        
        # Render markdown
        self._render_markdown(content_frame, message.content)
        
        # Actions
        actions = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions.pack(anchor="w", pady=(6, 0))
        
        for icon, cmd in [("📋", lambda: self._copy(message.content)), ("🔄", self._retry)]:
            btn = ctk.CTkButton(
                actions,
                text=icon,
                width=26,
                height=24,
                corner_radius=4,
                fg_color="transparent",
                hover_color=self.colors["bg_hover"],
                command=cmd
            )
            btn.pack(side="left", padx=2)
        
        # Feedback buttons
        ctk.CTkLabel(actions, text="  ", width=20).pack(side="left")
        
        for rating, icon in [(5, "👍"), (1, "👎")]:
            btn = ctk.CTkButton(
                actions,
                text=icon,
                width=26,
                height=24,
                corner_radius=4,
                fg_color="transparent",
                hover_color=self.colors["bg_hover"],
                command=lambda r=rating, c=message.content: self._record_feedback(r, c)
            )
            btn.pack(side="left", padx=1)
        
        # Follow-ups
        self._add_followups(content_frame)
    
    def _render_markdown(self, parent, content: str):
        """Render markdown."""
        # Split by code blocks
        code_pattern = r'```(\w*)\n?([\s\S]*?)```'
        parts = re.split(code_pattern, content)
        
        i = 0
        while i < len(parts):
            text = parts[i].strip()
            if text:
                # Clean markdown
                text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
                text = re.sub(r'\*(.+?)\*', r'\1', text)
                
                ctk.CTkLabel(
                    parent,
                    text=text,
                    font=ctk.CTkFont(size=14),
                    text_color=self.colors["text"],
                    wraplength=500,
                    justify="left"
                ).pack(anchor="w", pady=3)
            
            i += 1
            
            # Code block
            if i + 1 < len(parts):
                lang = parts[i] or ""
                code = parts[i + 1].strip()
                
                if code:
                    code_frame = ctk.CTkFrame(
                        parent,
                        fg_color=self.colors["code_bg"],
                        corner_radius=8
                    )
                    code_frame.pack(fill="x", pady=4)
                    
                    header = ctk.CTkFrame(code_frame, fg_color="transparent")
                    header.pack(fill="x", padx=10, pady=(6, 0))
                    
                    if lang:
                        ctk.CTkLabel(
                            header,
                            text=lang,
                            font=ctk.CTkFont(size=10),
                            text_color=self.colors["text_muted"]
                        ).pack(side="left")
                    
                    ctk.CTkButton(
                        header,
                        text="Copy",
                        width=45,
                        height=18,
                        corner_radius=4,
                        font=ctk.CTkFont(size=9),
                        fg_color=self.colors["bg_hover"],
                        hover_color=self.colors["border"],
                        command=lambda c=code: self._copy(c)
                    ).pack(side="right")
                    
                    ctk.CTkLabel(
                        code_frame,
                        text=code,
                        font=ctk.CTkFont(size=12, family="Consolas"),
                        text_color=self.colors["text"],
                        wraplength=480,
                        justify="left"
                    ).pack(anchor="w", padx=10, pady=(2, 8))
                
                i += 2
    
    def _render_error(self, container, message: ChatMessage):
        """Render error message."""
        bubble = ctk.CTkFrame(
            container,
            fg_color=self.colors["bg_secondary"],
            corner_radius=10,
            border_width=1,
            border_color=self.colors["error"]
        )
        bubble.pack(anchor="w", padx=32)
        
        ctk.CTkLabel(
            bubble,
            text=f"⚠️ {message.content}",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["error"],
            wraplength=450
        ).pack(padx=14, pady=10)
    
    def _render_system(self, container, message: ChatMessage):
        """Render system message."""
        bubble = ctk.CTkFrame(
            container,
            fg_color=self.colors["bg_secondary"],
            corner_radius=10
        )
        bubble.pack(fill="x", padx=32)
        
        ctk.CTkLabel(
            bubble,
            text=message.content,
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_secondary"],
            wraplength=500,
            justify="left"
        ).pack(padx=14, pady=12)
    
    def _add_followups(self, parent):
        """Add follow-up suggestions."""
        suggestions = self._get_followups()
        if not suggestions:
            return
        
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(anchor="w", pady=(6, 0))
        
        for s in suggestions[:3]:
            btn = ctk.CTkButton(
                frame,
                text=s,
                height=26,
                corner_radius=13,
                font=ctk.CTkFont(size=11),
                fg_color=self.colors["bg_hover"],
                hover_color=self.colors["border"],
                text_color=self.colors["accent"],
                command=lambda x=s: self._send_message_direct(x)
            )
            btn.pack(side="left", padx=2)
    
    def _get_followups(self) -> List[str]:
        """Get smart follow-ups."""
        if not self.last_query:
            return []
        
        q = self.last_query.lower()
        
        if "cpu" in q:
            return ["Show top processes", "Monitor CPU"]
        elif "memory" in q or "ram" in q:
            return ["Find memory hogs", "Clear cache"]
        elif "disk" in q:
            return ["Find large files", "Clean temp"]
        elif "process" in q:
            return ["Kill process", "Monitor"]
        elif "health" in q or "status" in q:
            return ["Show processes", "Check network"]
        elif "file" in q:
            return ["Search content", "Organize"]
        
        return ["Show status", "Run health check"]
    
    def add_streaming_message(self) -> Optional[Dict]:
        """Create streaming message."""
        if not CTK_AVAILABLE:
            return None
        
        try:
            if not self.messages_frame.winfo_exists():
                return None
        except Exception:
            return None
        
        self._hide_typing()
        
        container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        container.pack(fill="x", padx=16, pady=6)
        
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(anchor="w", fill="x")
        
        ctk.CTkLabel(row, text="🧠", font=ctk.CTkFont(size=22)).pack(side="left", anchor="n", padx=(0, 10))
        
        label = ctk.CTkLabel(
            row,
            text="▌",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text"],
            wraplength=500,
            justify="left"
        )
        label.pack(side="left", anchor="w")
        
        self.stream_data = {"container": container, "label": label, "content": ""}
        self._scroll_to_bottom()
        return self.stream_data
    
    def update_streaming_message(self, stream_data: Dict, token: str):
        """Update streaming message."""
        if not stream_data or "label" not in stream_data:
            return
        
        try:
            stream_data["content"] += token
            stream_data["label"].configure(text=stream_data["content"] + "▌")
            self._scroll_to_bottom()
        except Exception:
            pass
    
    def finish_streaming_message(self, stream_data: Dict):
        """Finish streaming message."""
        if not stream_data:
            return
        
        try:
            stream_data["label"].configure(text=stream_data["content"])
            self.messages.append(ChatMessage(content=stream_data["content"], msg_type=MessageType.ASSISTANT))
            self._set_processing(False)
        except Exception:
            pass
    
    def add_execution_log(self, tool_name: str, action: str = "", status: str = "running",
                          duration_ms: int = 0, details: str = ""):
        """Add tool execution log."""
        if not CTK_AVAILABLE:
            return
        
        try:
            if not self.messages_frame.winfo_exists():
                return
        except Exception:
            return
        
        if status == "running":
            self._hide_typing()
            if self.tool_indicator:
                self.tool_indicator.hide()
            self.tool_indicator = ToolIndicator(self.messages_frame, self.colors)
            self.tool_indicator.show(tool_name)
        elif self.tool_indicator:
            self.tool_indicator.complete(status == "success")
            self.tool_indicator = None
        
        self._scroll_to_bottom()
    
    def show_approval_dialog(self, title: str, description: str,
                            on_approve: Callable[[bool], None],
                            on_deny: Callable[[bool], None],
                            options: List[str] = None) -> ApprovalDialog:
        """Show an approval dialog for human-in-the-loop."""
        if not CTK_AVAILABLE:
            return None
        
        try:
            if not self.messages_frame.winfo_exists():
                return None
        except Exception:
            return None
        
        self._hide_typing()
        
        dialog = ApprovalDialog(
            self.messages_frame,
            self.colors,
            title,
            description,
            on_approve,
            on_deny,
            options
        )
        
        self._scroll_to_bottom()
        return dialog
    
    def show_permission_request(self, permission: str, reason: str,
                               on_response: Callable[[bool, bool], None]):
        """Show a permission request dialog."""
        def on_approve(remember):
            on_response(True, remember)
        
        def on_deny(remember):
            on_response(False, remember)
        
        return self.show_approval_dialog(
            f"Permission: {permission}",
            reason,
            on_approve,
            on_deny,
            ["Grant", "Deny"]
        )
    
    def add_message(self, content: str, is_user: bool = False, message_type: str = "text"):
        """Add message (thread-safe)."""
        msg_type = MessageType.USER if is_user else MessageType.ASSISTANT
        if message_type == "error":
            msg_type = MessageType.ERROR
        
        self.message_queue.put((content, msg_type))
    
    def _start_queue_processor(self):
        """Process message queue."""
        def process():
            try:
                while True:
                    content, msg_type = self.message_queue.get_nowait()
                    self._hide_typing()
                    if self.tool_indicator:
                        self.tool_indicator.hide()
                        self.tool_indicator = None
                    self._add_message(content, msg_type)
                    if msg_type != MessageType.USER:
                        self._set_processing(False)
            except queue.Empty:
                pass
            except Exception:
                pass
            finally:
                try:
                    self.parent.after(50, process)
                except Exception:
                    pass
        
        try:
            self.parent.after(50, process)
        except Exception:
            pass
    
    def _show_welcome(self):
        """Show welcome message."""
        welcome = """Welcome to SysAgent! 👋

I can help you with:
• System monitoring and health checks
• File management and search
• Process control
• Network diagnostics
• Automation workflows

Just type a message below to get started!"""
        
        self._add_message(welcome, MessageType.SYSTEM)
    
    def _scroll_to_bottom(self):
        """Scroll to bottom."""
        try:
            if CTK_AVAILABLE and hasattr(self.messages_frame, '_parent_canvas'):
                self.messages_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
    
    def _copy(self, text: str):
        """Copy to clipboard."""
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
            self._toast("Copied!")
        except Exception:
            pass
    
    def _retry(self):
        """Retry last."""
        if self.last_query:
            self._send_message_direct(self.last_query)
    
    def _record_feedback(self, rating: int, content: str):
        """Record feedback on a response."""
        try:
            if LEARNING_AVAILABLE:
                learning = get_learning_system()
                if learning and hasattr(learning, 'record_command'):
                    # Store feedback as a pattern
                    learning.record_command(
                        f"feedback_{rating}_{content[:50]}",
                        success=rating >= 4
                    )
            
            # Show feedback received
            icon = "👍" if rating >= 4 else "👎"
            self._toast(f"{icon} Feedback recorded!")
        except Exception:
            pass
    
    def _export_chat(self):
        """Export chat."""
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")]
        )
        if path:
            try:
                with open(path, "w") as f:
                    f.write("# SysAgent Chat\n\n")
                    for m in self.messages:
                        role = "You" if m.msg_type == MessageType.USER else "SysAgent"
                        f.write(f"**{role}**: {m.content}\n\n")
                self._toast("Exported!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _toast(self, msg: str):
        """Show toast."""
        try:
            self.status_text.configure(text=msg)
            self.parent.after(1500, lambda: self.status_text.configure(text="Ready"))
        except Exception:
            pass
    
    def clear_chat(self):
        """Clear chat."""
        try:
            for w in self.messages_frame.winfo_children():
                w.destroy()
            self.messages.clear()
            self.message_widgets.clear()
            self._add_message("Chat cleared. How can I help?", MessageType.SYSTEM)
        except Exception:
            pass
    
    def get_frame(self):
        return self.frame
    
    # ==================== SEARCH FUNCTIONALITY ====================
    
    def _toggle_search(self):
        """Toggle search bar visibility."""
        if not CTK_AVAILABLE:
            return
        
        if self._search_visible:
            self._hide_search()
        else:
            self._show_search()
    
    def _show_search(self):
        """Show search bar."""
        self._search_visible = True
        
        # Create search bar content
        for w in self.search_frame.winfo_children():
            w.destroy()
        
        inner = ctk.CTkFrame(self.search_frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=10)
        
        # Search icon
        ctk.CTkLabel(
            inner,
            text="🔍",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_muted"]
        ).pack(side="left")
        
        # Search entry
        self.search_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Search messages...",
            height=30,
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.search_entry.bind("<Return>", lambda e: self._do_search())
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search_key())
        self.search_entry.bind("<Escape>", lambda e: self._hide_search())
        
        # Results label
        self.search_results_label = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        )
        self.search_results_label.pack(side="left", padx=5)
        
        # Navigation buttons
        ctk.CTkButton(
            inner,
            text="▲",
            width=28,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color=self.colors["bg_hover"],
            hover_color=self.colors["border"],
            command=self._search_prev
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            inner,
            text="▼",
            width=28,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color=self.colors["bg_hover"],
            hover_color=self.colors["border"],
            command=self._search_next
        ).pack(side="left", padx=2)
        
        # Close button
        ctk.CTkButton(
            inner,
            text="✕",
            width=28,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=self.colors["bg_hover"],
            command=self._hide_search
        ).pack(side="left", padx=2)
        
        # Show frame
        self.search_frame.pack(fill="x", after=self.header_frame)
        self.search_entry.focus_set()
    
    def _hide_search(self):
        """Hide search bar."""
        self._search_visible = False
        self.search_frame.pack_forget()
        self._clear_search_highlights()
    
    def _on_search_key(self):
        """Handle search key release."""
        query = self.search_entry.get()
        if len(query) >= 2:
            self._do_search()
        elif len(query) == 0:
            self._clear_search_highlights()
            self.search_results_label.configure(text="")
    
    def _do_search(self):
        """Perform search."""
        query = self.search_entry.get().lower()
        if not query:
            return
        
        self._clear_search_highlights()
        self.search_results = []
        
        for i, msg in enumerate(self.messages):
            if query in msg.content.lower():
                self.search_results.append(i)
        
        if self.search_results:
            self.current_search_index = 0
            self.search_results_label.configure(
                text=f"1/{len(self.search_results)}"
            )
            self._highlight_search_result()
        else:
            self.search_results_label.configure(text="No results")
    
    def _search_next(self):
        """Go to next search result."""
        if not self.search_results:
            return
        
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self.search_results_label.configure(
            text=f"{self.current_search_index + 1}/{len(self.search_results)}"
        )
        self._highlight_search_result()
    
    def _search_prev(self):
        """Go to previous search result."""
        if not self.search_results:
            return
        
        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        self.search_results_label.configure(
            text=f"{self.current_search_index + 1}/{len(self.search_results)}"
        )
        self._highlight_search_result()
    
    def _highlight_search_result(self):
        """Highlight current search result."""
        if not self.search_results or not self.message_widgets:
            return
        
        idx = self.search_results[self.current_search_index]
        
        # Find the widget for this message
        if idx < len(self.message_widgets):
            widget, _ = self.message_widgets[idx]
            try:
                # Highlight the widget
                widget.configure(border_width=2, border_color=self.colors["accent"])
                
                # Scroll to it
                self._scroll_to_bottom()
            except Exception:
                pass
    
    def _clear_search_highlights(self):
        """Clear all search highlights."""
        for widget, _ in self.message_widgets:
            try:
                widget.configure(border_width=0)
            except Exception:
                pass
    
    # ==================== DRAG & DROP ====================
    
    def _setup_drag_drop(self):
        """Setup drag and drop for files."""
        try:
            # Try to enable TkDnD if available
            self.frame.drop_target_register("DND_Files")
            self.frame.dnd_bind("<<Drop>>", self._on_file_drop)
            self.frame.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.frame.dnd_bind("<<DragLeave>>", self._on_drag_leave)
        except Exception:
            # TkDnD not available, use file button instead
            pass
    
    def _on_drag_enter(self, event=None):
        """Handle drag enter."""
        if CTK_AVAILABLE:
            try:
                self.messages_frame.configure(border_width=2, border_color=self.colors["accent"])
            except Exception:
                pass
    
    def _on_drag_leave(self, event=None):
        """Handle drag leave."""
        if CTK_AVAILABLE:
            try:
                self.messages_frame.configure(border_width=0)
            except Exception:
                pass
    
    def _on_file_drop(self, event):
        """Handle file drop."""
        self._on_drag_leave()
        
        try:
            # Parse dropped files
            files = event.data.split() if isinstance(event.data, str) else [event.data]
            
            # Clean up file paths
            clean_files = []
            for f in files:
                # Remove braces and clean path
                f = f.strip('{}')
                if os.path.exists(f):
                    clean_files.append(f)
            
            if clean_files:
                if self.on_file_drop:
                    self.on_file_drop(clean_files)
                else:
                    # Default: show files in chat
                    file_list = "\n".join([f"📄 {Path(f).name}" for f in clean_files])
                    self._add_message(f"Files received:\n{file_list}", MessageType.SYSTEM)
                    
                    # Offer to analyze
                    for f in clean_files:
                        self._quick_send(f"Analyze file: {f}")
                        break  # Just analyze first file
        except Exception as e:
            self._add_message(f"Error processing files: {e}", MessageType.ERROR)
    
    def add_file_button(self, parent):
        """Add file attachment button."""
        if not CTK_AVAILABLE:
            return
        
        btn = ctk.CTkButton(
            parent,
            text="📎",
            width=36,
            height=36,
            corner_radius=6,
            fg_color="transparent",
            hover_color=self.colors["bg_hover"],
            command=self._browse_files
        )
        return btn
    
    def _browse_files(self):
        """Browse for files."""
        files = filedialog.askopenfilenames(
            title="Select files",
            filetypes=[
                ("All files", "*.*"),
                ("Text files", "*.txt *.md *.json *.yaml *.yml"),
                ("Code files", "*.py *.js *.ts *.go *.rs *.java"),
                ("Log files", "*.log"),
            ]
        )
        
        if files:
            if self.on_file_drop:
                self.on_file_drop(list(files))
            else:
                for f in files:
                    self._quick_send(f"Analyze file: {f}")
                    break
    
    # ==================== CONTEXT MENU ====================
    
    def _show_message_context_menu(self, event, message: ChatMessage):
        """Show context menu for a message."""
        menu = tk.Menu(self.parent, tearoff=0, 
                      bg=self.colors["bg_secondary"],
                      fg=self.colors["text"],
                      activebackground=self.colors["accent"])
        
        menu.add_command(label="📋 Copy", command=lambda: self._copy(message.content))
        menu.add_separator()
        
        if message.msg_type == MessageType.ASSISTANT:
            menu.add_command(label="🔄 Retry", command=self._retry)
            menu.add_command(label="👍 Good response", command=lambda: self._record_feedback(5, message.content))
            menu.add_command(label="👎 Bad response", command=lambda: self._record_feedback(1, message.content))
            menu.add_separator()
            menu.add_command(label="💾 Save as snippet", command=lambda: self._save_as_snippet(message.content))
        
        if message.msg_type == MessageType.USER:
            menu.add_command(label="📝 Edit & resend", command=lambda: self._edit_message(message.content))
            menu.add_command(label="⭐ Add to favorites", command=lambda: self._add_to_favorites(message.content))
        
        menu.add_separator()
        menu.add_command(label="🔍 Search similar", command=lambda: self._search_similar(message.content))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _save_as_snippet(self, content: str):
        """Save content as snippet."""
        if not LEARNING_AVAILABLE:
            self._toast("Learning system not available")
            return
        
        try:
            learning = get_learning_system()
            if learning:
                # Create a name from first few words
                name = " ".join(content.split()[:5])
                if len(name) > 30:
                    name = name[:30] + "..."
                learning.save_snippet(name, content, "", ["chat"])
                self._toast("Saved as snippet!")
        except Exception as e:
            self._toast(f"Error: {e}")
    
    def _edit_message(self, content: str):
        """Edit and resend a message."""
        self._set_input_text(content)
        self.input_field.focus_set()
    
    def _add_to_favorites(self, content: str):
        """Add command to favorites."""
        if not LEARNING_AVAILABLE:
            return
        
        try:
            learning = get_learning_system()
            if learning:
                learning.save_snippet(content[:30], content, "", ["favorite"], is_favorite=True)
                self._toast("Added to favorites!")
        except Exception:
            pass
    
    def _search_similar(self, content: str):
        """Search for similar messages."""
        # Get first few words as search query
        query = " ".join(content.split()[:3])
        self._show_search()
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, query)
        self._do_search()


class ChatWindow:
    """Standalone chat window."""
    
    def __init__(self):
        self.root = None
        self.agent = None
        self.chat = None
        self._init_agent()
    
    def _init_agent(self):
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..core.langgraph_agent import LangGraphAgent
            
            config = ConfigManager()
            perms = PermissionManager(config)
            self.agent = LangGraphAgent(config, perms)
        except Exception as e:
            print(f"Agent init failed: {e}")
    
    def _create_window(self):
        if CTK_AVAILABLE:
            ctk.set_appearance_mode("dark")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title("SysAgent")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        return self.root
    
    def _on_message(self, message: str):
        if self.agent:
            def process():
                try:
                    result = self.agent.process_command(message)
                    response = result.get('message', 'Done')
                    msg_type = "text" if result.get('success') else "error"
                    self.chat.add_message(response, is_user=False, message_type=msg_type)
                except Exception as e:
                    self.chat.add_message(f"Error: {e}", is_user=False, message_type="error")
            
            threading.Thread(target=process, daemon=True).start()
        else:
            self.chat.add_message("Agent not available", is_user=False, message_type="error")
    
    def run(self):
        self._create_window()
        self.chat = ChatInterface(self.root, on_send=self._on_message)
        self.root.mainloop()


def launch_chat():
    ChatWindow().run()


if __name__ == "__main__":
    launch_chat()
