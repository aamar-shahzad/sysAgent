"""
Commercial-Grade Chat Interface for SysAgent GUI.
Professional UI with streaming, loading states, and smart features.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import re
import time
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


class MessageType(Enum):
    """Message types for styling."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"
    SUCCESS = "success"
    TOOL = "tool"
    LOADING = "loading"


@dataclass
class ChatMessage:
    """Represents a chat message."""
    content: str
    msg_type: MessageType
    timestamp: datetime = None
    tool_name: str = ""
    duration_ms: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ThinkingAnimation:
    """Animated thinking/loading indicator."""
    
    def __init__(self, parent, label_widget):
        self.parent = parent
        self.label = label_widget
        self.running = False
        self.dots = 0
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.frame_idx = 0
    
    def start(self, text: str = "Thinking"):
        """Start the animation."""
        self.running = True
        self.base_text = text
        self._animate()
    
    def stop(self):
        """Stop the animation."""
        self.running = False
    
    def _animate(self):
        """Animate the indicator."""
        if not self.running:
            return
        
        try:
            spinner = self.frames[self.frame_idx % len(self.frames)]
            self.label.configure(text=f"{spinner} {self.base_text}...")
            self.frame_idx += 1
            self.parent.after(80, self._animate)
        except Exception:
            pass


class ToolExecutionCard:
    """Visual card for tool execution status."""
    
    STATUS_COLORS = {
        "pending": ("#64748b", "#94a3b8"),
        "running": ("#f59e0b", "#fbbf24"),
        "success": ("#10b981", "#34d399"),
        "error": ("#ef4444", "#f87171"),
    }
    
    STATUS_ICONS = {
        "pending": "○",
        "running": "◐",
        "success": "●",
        "error": "✕",
    }
    
    def __init__(self, parent, tool_name: str, action: str = ""):
        self.parent = parent
        self.tool_name = tool_name
        self.action = action
        self.status = "pending"
        self.start_time = time.time()
        self.frame = None
        self.status_label = None
        self.duration_label = None
        self._create_widget()
    
    def _create_widget(self):
        """Create the tool execution card."""
        if not CTK_AVAILABLE:
            return
        
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=("#f1f5f9", "#1e293b"),
            corner_radius=8,
            height=44
        )
        self.frame.pack(fill="x", padx=60, pady=3)
        self.frame.pack_propagate(False)
        
        # Inner container
        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=8)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            inner,
            text=f"{self.STATUS_ICONS['pending']} {self.tool_name}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.STATUS_COLORS["pending"][1]
        )
        self.status_label.pack(side="left")
        
        # Action text
        if self.action:
            ctk.CTkLabel(
                inner,
                text=f"  →  {self.action[:40]}{'...' if len(self.action) > 40 else ''}",
                font=ctk.CTkFont(size=11),
                text_color=("#64748b", "#94a3b8")
            ).pack(side="left")
        
        # Duration
        self.duration_label = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=("#94a3b8", "#64748b")
        )
        self.duration_label.pack(side="right")
        
        self.set_status("running")
    
    def set_status(self, status: str, details: str = ""):
        """Update the status."""
        self.status = status
        
        if not self.frame or not CTK_AVAILABLE:
            return
        
        try:
            icon = self.STATUS_ICONS.get(status, "○")
            color = self.STATUS_COLORS.get(status, self.STATUS_COLORS["pending"])
            
            self.status_label.configure(
                text=f"{icon} {self.tool_name}",
                text_color=color[1]
            )
            
            if status in ["success", "error"]:
                duration = int((time.time() - self.start_time) * 1000)
                self.duration_label.configure(text=f"{duration}ms")
        except Exception:
            pass


class ChatInterface:
    """Commercial-grade chat interface with streaming and smart features."""
    
    # Color scheme (light, dark)
    COLORS = {
        "bg": ("#ffffff", "#0f172a"),
        "surface": ("#f8fafc", "#1e293b"),
        "surface_alt": ("#f1f5f9", "#334155"),
        "border": ("#e2e8f0", "#334155"),
        "text": ("#0f172a", "#f8fafc"),
        "text_secondary": ("#64748b", "#94a3b8"),
        "accent": ("#3b82f6", "#60a5fa"),
        "accent_hover": ("#2563eb", "#3b82f6"),
        "user_bubble": ("#3b82f6", "#2563eb"),
        "assistant_bubble": ("#f1f5f9", "#1e293b"),
        "success": ("#10b981", "#34d399"),
        "error": ("#ef4444", "#f87171"),
        "warning": ("#f59e0b", "#fbbf24"),
    }
    
    def __init__(self, parent, on_send: Optional[Callable[[str], None]] = None):
        """Initialize the chat interface."""
        self.parent = parent
        self.on_send = on_send
        self.messages: List[ChatMessage] = []
        self.message_queue = queue.Queue()
        self.is_processing = False
        self.command_history: List[str] = []
        self.history_index = -1
        self.last_query = ""
        self.current_tool_card: Optional[ToolExecutionCard] = None
        self.thinking_animation: Optional[ThinkingAnimation] = None
        self.stream_data: Optional[Dict] = None
        
        self._create_ui()
        self._start_queue_processor()
    
    def _create_ui(self):
        """Create the main UI structure."""
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        else:
            self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        self._create_header()
        self._create_messages_area()
        self._create_input_area()
        self._add_welcome_message()
    
    def _create_header(self):
        """Create a sleek header."""
        if not CTK_AVAILABLE:
            header = ttk.Frame(self.frame)
            header.pack(fill="x", pady=5)
            ttk.Label(header, text="SysAgent", font=("", 14, "bold")).pack(side="left", padx=10)
            return
        
        header = ctk.CTkFrame(
            self.frame,
            fg_color=self.COLORS["surface"],
            corner_radius=0,
            height=56
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Left section
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="y", padx=16)
        
        # Logo and title
        title_frame = ctk.CTkFrame(left, fg_color="transparent")
        title_frame.pack(side="left", pady=12)
        
        ctk.CTkLabel(
            title_frame,
            text="🧠",
            font=ctk.CTkFont(size=24)
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(
            title_frame,
            text="SysAgent",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS["text"]
        ).pack(side="left")
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(left, fg_color="transparent")
        self.status_frame.pack(side="left", padx=20)
        
        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color=self.COLORS["success"]
        )
        self.status_dot.pack(side="left")
        
        self.status_text = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS["text_secondary"]
        )
        self.status_text.pack(side="left", padx=(4, 0))
        
        # Right section - controls
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", fill="y", padx=16)
        
        btn_style = {
            "width": 36,
            "height": 36,
            "corner_radius": 8,
            "fg_color": "transparent",
            "hover_color": self.COLORS["surface_alt"],
            "font": ctk.CTkFont(size=16)
        }
        
        ctk.CTkButton(right, text="📤", command=self._export_chat, **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(right, text="🗑️", command=self.clear_chat, **btn_style).pack(side="left", padx=2)
    
    def _create_messages_area(self):
        """Create the scrollable messages area."""
        if not CTK_AVAILABLE:
            self.messages_frame = ttk.Frame(self.frame)
            self.messages_frame.pack(fill="both", expand=True, padx=10, pady=10)
            return
        
        # Container with subtle border
        container = ctk.CTkFrame(
            self.frame,
            fg_color=self.COLORS["bg"],
            corner_radius=0
        )
        container.pack(fill="both", expand=True)
        
        # Scrollable frame for messages
        self.messages_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent",
            corner_radius=0
        )
        self.messages_frame.pack(fill="both", expand=True, padx=0, pady=0)
    
    def _create_input_area(self):
        """Create the message input area."""
        if not CTK_AVAILABLE:
            input_frame = ttk.Frame(self.frame)
            input_frame.pack(fill="x", padx=10, pady=10)
            
            self.input_field = ttk.Entry(input_frame)
            self.input_field.pack(side="left", fill="x", expand=True)
            self.input_field.bind("<Return>", lambda e: self._send_message())
            
            ttk.Button(input_frame, text="Send", command=self._send_message).pack(side="right")
            return
        
        # Input container
        input_container = ctk.CTkFrame(
            self.frame,
            fg_color=self.COLORS["surface"],
            corner_radius=0,
            height=100
        )
        input_container.pack(fill="x", side="bottom")
        input_container.pack_propagate(False)
        
        # Inner padding
        inner = ctk.CTkFrame(input_container, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=12)
        
        # Input field with border
        input_wrapper = ctk.CTkFrame(
            inner,
            fg_color=self.COLORS["bg"],
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS["border"]
        )
        input_wrapper.pack(side="left", fill="both", expand=True, padx=(0, 12))
        
        # Text input
        self.input_field = ctk.CTkTextbox(
            input_wrapper,
            height=60,
            fg_color="transparent",
            font=ctk.CTkFont(size=14),
            wrap="word",
            border_width=0
        )
        self.input_field.pack(fill="both", expand=True, padx=12, pady=8)
        
        # Placeholder
        self._placeholder = "Ask me anything... (Enter to send, Shift+Enter for new line)"
        self._show_placeholder()
        
        # Bindings
        self.input_field.bind("<FocusIn>", self._on_focus_in)
        self.input_field.bind("<FocusOut>", self._on_focus_out)
        self.input_field.bind("<Return>", self._on_return)
        self.input_field.bind("<Shift-Return>", lambda e: None)
        self.input_field.bind("<Up>", self._on_history_up)
        self.input_field.bind("<Down>", self._on_history_down)
        
        # Send button
        self.send_btn = ctk.CTkButton(
            inner,
            text="Send",
            width=80,
            height=44,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.COLORS["accent"],
            hover_color=self.COLORS["accent_hover"],
            command=self._send_message
        )
        self.send_btn.pack(side="right")
        
        # Quick actions
        self._create_quick_actions(input_container)
    
    def _create_quick_actions(self, parent):
        """Create quick action buttons."""
        if not CTK_AVAILABLE:
            return
        
        actions_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        actions_frame.pack(fill="x", side="bottom", padx=16, pady=(0, 8))
        
        actions = [
            ("💻 System", "Show system status"),
            ("📊 CPU", "Show CPU usage"),
            ("🧠 Memory", "Show memory usage"),
            ("💾 Disk", "Check disk space"),
            ("🏥 Health", "Run system health check"),
            ("🔍 Search", "Search for files"),
        ]
        
        for text, cmd in actions:
            btn = ctk.CTkButton(
                actions_frame,
                text=text,
                height=28,
                corner_radius=14,
                font=ctk.CTkFont(size=11),
                fg_color=self.COLORS["surface_alt"],
                hover_color=self.COLORS["border"],
                text_color=self.COLORS["text_secondary"],
                command=lambda c=cmd: self._quick_send(c)
            )
            btn.pack(side="left", padx=3)
    
    def _show_placeholder(self):
        """Show placeholder text."""
        self._placeholder_active = True
        if CTK_AVAILABLE:
            self.input_field.delete("1.0", "end")
            self.input_field.insert("1.0", self._placeholder)
            self.input_field.configure(text_color=self.COLORS["text_secondary"][1])
    
    def _on_focus_in(self, event):
        """Handle focus in."""
        if self._placeholder_active:
            self.input_field.delete("1.0", "end")
            if CTK_AVAILABLE:
                self.input_field.configure(text_color=self.COLORS["text"][1])
            self._placeholder_active = False
    
    def _on_focus_out(self, event):
        """Handle focus out."""
        content = self.input_field.get("1.0", "end").strip()
        if not content:
            self._show_placeholder()
    
    def _on_return(self, event):
        """Handle Enter key."""
        if not (event.state & 0x1):  # Shift not pressed
            self._send_message()
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
        """Set input field text."""
        self.input_field.delete("1.0", "end")
        if text:
            self.input_field.insert("1.0", text)
            self._placeholder_active = False
            if CTK_AVAILABLE:
                self.input_field.configure(text_color=self.COLORS["text"][1])
    
    def _quick_send(self, message: str):
        """Send a quick action."""
        self._set_input_text(message)
        self._send_message()
    
    def _send_message(self):
        """Send the current message."""
        content = self.input_field.get("1.0", "end").strip()
        
        if self._placeholder_active or not content or content == self._placeholder:
            return
        
        if self.is_processing:
            return
        
        # Clear input
        self._set_input_text("")
        self._show_placeholder()
        
        # Add to history
        if content and (not self.command_history or self.command_history[-1] != content):
            self.command_history.append(content)
        self.history_index = -1
        self.last_query = content
        
        # Add user message
        self._add_message(content, MessageType.USER)
        
        # Start processing
        self._set_processing(True)
        
        # Call handler
        if self.on_send:
            self.on_send(content)
        else:
            self._add_message("No agent connected. Configure API keys in Settings.", MessageType.ERROR)
            self._set_processing(False)
    
    def _send_message_direct(self, message: str):
        """Send a message directly (for external calls)."""
        self._set_input_text(message)
        self._send_message()
    
    def _set_processing(self, processing: bool):
        """Set processing state with animation."""
        self.is_processing = processing
        
        if not CTK_AVAILABLE:
            return
        
        try:
            if processing:
                self.status_dot.configure(text_color=self.COLORS["warning"])
                self.status_text.configure(text="Processing")
                self.send_btn.configure(state="disabled", text="...")
                
                # Show thinking indicator
                self._show_thinking_indicator()
            else:
                self.status_dot.configure(text_color=self.COLORS["success"])
                self.status_text.configure(text="Ready")
                self.send_btn.configure(state="normal", text="Send")
                
                # Hide thinking indicator
                self._hide_thinking_indicator()
        except Exception:
            pass
    
    def _show_thinking_indicator(self):
        """Show animated thinking indicator."""
        if not CTK_AVAILABLE:
            return
        
        try:
            self.thinking_frame = ctk.CTkFrame(
                self.messages_frame,
                fg_color="transparent"
            )
            self.thinking_frame.pack(fill="x", padx=16, pady=8)
            
            bubble = ctk.CTkFrame(
                self.thinking_frame,
                fg_color=self.COLORS["assistant_bubble"],
                corner_radius=16
            )
            bubble.pack(anchor="w", padx=40)
            
            self.thinking_label = ctk.CTkLabel(
                bubble,
                text="⠋ Thinking...",
                font=ctk.CTkFont(size=13),
                text_color=self.COLORS["text_secondary"]
            )
            self.thinking_label.pack(padx=16, pady=12)
            
            self.thinking_animation = ThinkingAnimation(self.parent, self.thinking_label)
            self.thinking_animation.start("Thinking")
            
            self._scroll_to_bottom()
        except Exception:
            pass
    
    def _hide_thinking_indicator(self):
        """Hide thinking indicator."""
        if self.thinking_animation:
            self.thinking_animation.stop()
            self.thinking_animation = None
        
        if hasattr(self, 'thinking_frame') and self.thinking_frame:
            try:
                self.thinking_frame.destroy()
            except Exception:
                pass
            self.thinking_frame = None
    
    def _add_message(self, content: str, msg_type: MessageType, **kwargs):
        """Add a message to the chat."""
        message = ChatMessage(content=content, msg_type=msg_type, **kwargs)
        self.messages.append(message)
        self._render_message(message)
    
    def _render_message(self, message: ChatMessage):
        """Render a message in the UI."""
        if not CTK_AVAILABLE:
            # Basic tkinter fallback
            label = ttk.Label(self.messages_frame, text=message.content, wraplength=400)
            label.pack(anchor="e" if message.msg_type == MessageType.USER else "w", padx=10, pady=5)
            return
        
        try:
            if not self.messages_frame.winfo_exists():
                return
        except Exception:
            return
        
        # Container
        container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        container.pack(fill="x", padx=16, pady=6)
        
        if message.msg_type == MessageType.USER:
            self._render_user_message(container, message)
        elif message.msg_type == MessageType.ASSISTANT:
            self._render_assistant_message(container, message)
        elif message.msg_type == MessageType.ERROR:
            self._render_error_message(container, message)
        elif message.msg_type == MessageType.SYSTEM:
            self._render_system_message(container, message)
        elif message.msg_type == MessageType.TOOL:
            self._render_tool_message(container, message)
        
        self._scroll_to_bottom()
    
    def _render_user_message(self, container, message: ChatMessage):
        """Render a user message."""
        # Right-aligned bubble
        bubble = ctk.CTkFrame(
            container,
            fg_color=self.COLORS["user_bubble"],
            corner_radius=16
        )
        bubble.pack(anchor="e", padx=0)
        
        # Content
        ctk.CTkLabel(
            bubble,
            text=message.content,
            font=ctk.CTkFont(size=14),
            text_color="white",
            wraplength=450,
            justify="right"
        ).pack(padx=16, pady=12)
        
        # Timestamp
        ctk.CTkLabel(
            container,
            text=message.timestamp.strftime("%H:%M"),
            font=ctk.CTkFont(size=10),
            text_color=self.COLORS["text_secondary"]
        ).pack(anchor="e", padx=4, pady=(2, 0))
    
    def _render_assistant_message(self, container, message: ChatMessage):
        """Render an assistant message with markdown support."""
        # Left-aligned with avatar
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(anchor="w", fill="x")
        
        # Avatar
        ctk.CTkLabel(
            row,
            text="🧠",
            font=ctk.CTkFont(size=28),
            width=40
        ).pack(side="left", anchor="n", padx=(0, 8))
        
        # Message content
        content_frame = ctk.CTkFrame(row, fg_color="transparent")
        content_frame.pack(side="left", fill="x", expand=True)
        
        # Bubble
        bubble = ctk.CTkFrame(
            content_frame,
            fg_color=self.COLORS["assistant_bubble"],
            corner_radius=16
        )
        bubble.pack(anchor="w")
        
        # Parse and render markdown
        self._render_markdown_content(bubble, message.content)
        
        # Actions row
        actions = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions.pack(anchor="w", pady=(4, 0))
        
        # Timestamp
        ctk.CTkLabel(
            actions,
            text=message.timestamp.strftime("%H:%M"),
            font=ctk.CTkFont(size=10),
            text_color=self.COLORS["text_secondary"]
        ).pack(side="left")
        
        # Action buttons
        btn_style = {
            "width": 28, "height": 22, "corner_radius": 6,
            "font": ctk.CTkFont(size=11),
            "fg_color": "transparent",
            "hover_color": self.COLORS["surface_alt"],
            "text_color": self.COLORS["text_secondary"]
        }
        
        ctk.CTkButton(actions, text="📋", command=lambda: self._copy_to_clipboard(message.content), **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="💾", command=lambda: self._save_to_file(message.content), **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="🔄", command=self._retry_last, **btn_style).pack(side="left", padx=2)
        
        # Add follow-up suggestions
        if self.last_query:
            self._add_followups(content_frame, message.content)
    
    def _render_markdown_content(self, parent, content: str):
        """Render markdown content."""
        # Split by code blocks
        code_pattern = r'```(\w*)\n?([\s\S]*?)```'
        parts = re.split(code_pattern, content)
        
        i = 0
        while i < len(parts):
            text_part = parts[i].strip()
            if text_part:
                # Clean markdown formatting
                text_part = re.sub(r'\*\*(.+?)\*\*', r'\1', text_part)
                text_part = re.sub(r'\*(.+?)\*', r'\1', text_part)
                text_part = re.sub(r'`(.+?)`', r'[\1]', text_part)
                
                ctk.CTkLabel(
                    parent,
                    text=text_part,
                    font=ctk.CTkFont(size=14),
                    text_color=self.COLORS["text"],
                    wraplength=500,
                    justify="left"
                ).pack(anchor="w", padx=16, pady=8)
            
            i += 1
            
            # Code block
            if i + 1 < len(parts):
                lang = parts[i] or ""
                code = parts[i + 1].strip()
                
                if code:
                    code_frame = ctk.CTkFrame(
                        parent,
                        fg_color=("#1e293b", "#0f172a"),
                        corner_radius=8
                    )
                    code_frame.pack(fill="x", padx=12, pady=4)
                    
                    # Header with language and copy button
                    header = ctk.CTkFrame(code_frame, fg_color="transparent")
                    header.pack(fill="x", padx=12, pady=(8, 4))
                    
                    if lang:
                        ctk.CTkLabel(
                            header,
                            text=lang,
                            font=ctk.CTkFont(size=10),
                            text_color="#64748b"
                        ).pack(side="left")
                    
                    ctk.CTkButton(
                        header,
                        text="Copy",
                        width=50,
                        height=20,
                        corner_radius=4,
                        font=ctk.CTkFont(size=10),
                        fg_color="#334155",
                        hover_color="#475569",
                        command=lambda c=code: self._copy_to_clipboard(c)
                    ).pack(side="right")
                    
                    # Code content
                    ctk.CTkLabel(
                        code_frame,
                        text=code,
                        font=ctk.CTkFont(size=12, family="Consolas"),
                        text_color="#e2e8f0",
                        wraplength=480,
                        justify="left"
                    ).pack(anchor="w", padx=12, pady=(0, 12))
                
                i += 2
    
    def _render_error_message(self, container, message: ChatMessage):
        """Render an error message."""
        bubble = ctk.CTkFrame(
            container,
            fg_color=("#fef2f2", "#450a0a"),
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS["error"]
        )
        bubble.pack(anchor="w", padx=40)
        
        ctk.CTkLabel(
            bubble,
            text=f"❌ {message.content}",
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS["error"],
            wraplength=500
        ).pack(padx=16, pady=12)
    
    def _render_system_message(self, container, message: ChatMessage):
        """Render a system message."""
        bubble = ctk.CTkFrame(
            container,
            fg_color=self.COLORS["surface_alt"],
            corner_radius=12
        )
        bubble.pack(fill="x", padx=40)
        
        ctk.CTkLabel(
            bubble,
            text=message.content,
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS["text_secondary"],
            wraplength=500,
            justify="left"
        ).pack(padx=20, pady=16)
    
    def _render_tool_message(self, container, message: ChatMessage):
        """Render a tool execution message."""
        # This is handled by ToolExecutionCard
        pass
    
    def _add_followups(self, parent, response: str):
        """Add follow-up suggestion buttons."""
        suggestions = self._generate_followups(self.last_query, response)
        if not suggestions:
            return
        
        followup_frame = ctk.CTkFrame(parent, fg_color="transparent")
        followup_frame.pack(anchor="w", pady=(8, 0))
        
        ctk.CTkLabel(
            followup_frame,
            text="💡",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 6))
        
        for suggestion in suggestions[:3]:
            btn = ctk.CTkButton(
                followup_frame,
                text=suggestion,
                height=26,
                corner_radius=13,
                font=ctk.CTkFont(size=11),
                fg_color=self.COLORS["surface_alt"],
                hover_color=self.COLORS["border"],
                text_color=self.COLORS["accent"],
                command=lambda s=suggestion: self._quick_send(s)
            )
            btn.pack(side="left", padx=3)
    
    def _generate_followups(self, query: str, response: str) -> List[str]:
        """Generate follow-up suggestions."""
        suggestions = []
        combined = (query + " " + response).lower()
        
        patterns = {
            "cpu": ["Show top CPU processes", "Monitor CPU"],
            "memory": ["Show memory hogs", "Clear cache"],
            "disk": ["Find large files", "Clean temp files"],
            "process": ["Kill process", "Monitor process"],
            "system": ["Check health", "Show processes"],
            "file": ["Search files", "List directory"],
            "git": ["Git log", "Git diff"],
            "network": ["Check connectivity", "Show ports"],
        }
        
        for key, sug in patterns.items():
            if key in combined:
                suggestions.extend(sug[:2])
                if len(suggestions) >= 3:
                    break
        
        return suggestions[:3]
    
    def add_streaming_message(self) -> Optional[Dict]:
        """Create a streaming message container."""
        if not CTK_AVAILABLE:
            return None
        
        try:
            if not self.messages_frame.winfo_exists():
                return None
        except Exception:
            return None
        
        # Hide thinking indicator
        self._hide_thinking_indicator()
        
        # Container
        container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        container.pack(fill="x", padx=16, pady=6)
        
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(anchor="w", fill="x")
        
        # Avatar
        ctk.CTkLabel(row, text="🧠", font=ctk.CTkFont(size=28), width=40).pack(side="left", anchor="n", padx=(0, 8))
        
        # Bubble
        bubble = ctk.CTkFrame(
            row,
            fg_color=self.COLORS["assistant_bubble"],
            corner_radius=16
        )
        bubble.pack(side="left")
        
        # Content label
        content_label = ctk.CTkLabel(
            bubble,
            text="▌",
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS["text"],
            wraplength=500,
            justify="left"
        )
        content_label.pack(padx=16, pady=12)
        
        self.stream_data = {
            "container": container,
            "bubble": bubble,
            "label": content_label,
            "content": ""
        }
        
        self._scroll_to_bottom()
        return self.stream_data
    
    def update_streaming_message(self, stream_data: Dict, token: str):
        """Update streaming message with new token."""
        if not stream_data or "label" not in stream_data:
            return
        
        try:
            stream_data["content"] += token
            stream_data["label"].configure(text=stream_data["content"] + "▌")
            self._scroll_to_bottom()
        except Exception:
            pass
    
    def finish_streaming_message(self, stream_data: Dict):
        """Finalize streaming message."""
        if not stream_data or "label" not in stream_data:
            return
        
        try:
            # Remove cursor
            stream_data["label"].configure(text=stream_data["content"])
            
            # Store as message
            self.messages.append(ChatMessage(
                content=stream_data["content"],
                msg_type=MessageType.ASSISTANT
            ))
            
            self._set_processing(False)
        except Exception:
            pass
    
    def add_execution_log(self, tool_name: str, action: str = "", status: str = "running",
                          duration_ms: int = 0, details: str = ""):
        """Add a tool execution log."""
        if not CTK_AVAILABLE:
            return
        
        try:
            if not self.messages_frame.winfo_exists():
                return
        except Exception:
            return
        
        # Update or create card
        if status == "running" and not self.current_tool_card:
            self._hide_thinking_indicator()
            self.current_tool_card = ToolExecutionCard(self.messages_frame, tool_name, action or details)
        elif self.current_tool_card:
            self.current_tool_card.set_status(status, details)
            if status in ["success", "error"]:
                self.current_tool_card = None
        
        self._scroll_to_bottom()
    
    def add_message(self, content: str, is_user: bool = False, message_type: str = "text"):
        """Add message (thread-safe, backwards compatible)."""
        msg_type = MessageType.USER if is_user else MessageType.ASSISTANT
        if message_type == "error":
            msg_type = MessageType.ERROR
        
        self.message_queue.put((content, msg_type))
    
    def _start_queue_processor(self):
        """Start background queue processor."""
        def process():
            try:
                while True:
                    content, msg_type = self.message_queue.get_nowait()
                    self._hide_thinking_indicator()
                    self._add_message(content, msg_type)
                    if msg_type != MessageType.USER:
                        self._set_processing(False)
            except queue.Empty:
                pass
            except Exception:
                pass
            finally:
                try:
                    self.parent.after(100, process)
                except Exception:
                    pass
        
        try:
            self.parent.after(100, process)
        except Exception:
            pass
    
    def _add_welcome_message(self):
        """Add welcome message."""
        welcome = """Welcome to SysAgent! 🎉

I'm your intelligent system assistant. I can help you with:

📊 **System Monitoring** - CPU, memory, disk, processes
📁 **File Management** - Search, organize, cleanup
🔧 **Automation** - Workflows, scheduled tasks
🔍 **Smart Search** - Find files, apps, commands
🏥 **Health Checks** - System diagnostics & recommendations

Just ask me anything in natural language!"""
        
        self._add_message(welcome, MessageType.SYSTEM)
    
    def _scroll_to_bottom(self):
        """Scroll to bottom."""
        try:
            if CTK_AVAILABLE and hasattr(self.messages_frame, '_parent_canvas'):
                self.messages_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
    
    def _copy_to_clipboard(self, text: str):
        """Copy to clipboard."""
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
            self._show_toast("Copied!")
        except Exception:
            pass
    
    def _save_to_file(self, content: str):
        """Save content to file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Markdown", "*.md"), ("All", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(content)
                self._show_toast("Saved!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _retry_last(self):
        """Retry last message."""
        if self.command_history:
            self._quick_send(self.command_history[-1])
    
    def _export_chat(self):
        """Export chat history."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")]
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write("# SysAgent Chat Export\n\n")
                    for msg in self.messages:
                        role = "You" if msg.msg_type == MessageType.USER else "SysAgent"
                        f.write(f"**{role}** ({msg.timestamp.strftime('%H:%M')}):\n")
                        f.write(f"{msg.content}\n\n---\n\n")
                self._show_toast("Exported!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _show_toast(self, message: str):
        """Show brief toast notification."""
        if CTK_AVAILABLE:
            try:
                self.status_text.configure(text=message)
                self.parent.after(1500, lambda: self.status_text.configure(text="Ready"))
            except Exception:
                pass
    
    def clear_chat(self):
        """Clear all messages."""
        try:
            for widget in self.messages_frame.winfo_children():
                widget.destroy()
            self.messages.clear()
            self._add_message("Chat cleared. How can I help you?", MessageType.SYSTEM)
        except Exception:
            pass
    
    def get_frame(self):
        """Get main frame."""
        return self.frame


class ChatWindow:
    """Standalone chat window."""
    
    def __init__(self):
        self.root = None
        self.agent = None
        self.chat = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize agent."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..core.langgraph_agent import LangGraphAgent
            
            config = ConfigManager()
            perms = PermissionManager(config)
            self.agent = LangGraphAgent(config, perms)
        except Exception as e:
            print(f"Agent init failed: {e}")
            self.agent = None
    
    def _create_window(self):
        """Create window."""
        if CTK_AVAILABLE:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title("SysAgent")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        return self.root
    
    def _on_message(self, message: str):
        """Handle message."""
        if self.agent:
            try:
                result = self.agent.process_command(message)
                response = result.get('message', 'Done')
                msg_type = "text" if result.get('success') else "error"
                self.chat.add_message(response, is_user=False, message_type=msg_type)
            except Exception as e:
                self.chat.add_message(f"Error: {e}", is_user=False, message_type="error")
        else:
            self.chat.add_message("Agent not available", is_user=False, message_type="error")
    
    def run(self):
        """Run window."""
        self._create_window()
        self.chat = ChatInterface(self.root, on_send=self._on_message)
        self.root.mainloop()


def launch_chat():
    """Launch chat window."""
    ChatWindow().run()


if __name__ == "__main__":
    launch_chat()
