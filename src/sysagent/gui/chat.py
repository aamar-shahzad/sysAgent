"""
Cursor AI-Style Chat Interface for SysAgent.
Clean, minimal, smart UI with streaming and inline suggestions.
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
    TOOL = "tool"


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


# Modern color scheme inspired by Cursor AI
THEME = {
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_tertiary": "#21262d",
    "bg_input": "#0d1117",
    "border": "#30363d",
    "border_focus": "#58a6ff",
    "text_primary": "#e6edf3",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    "accent": "#58a6ff",
    "accent_hover": "#79c0ff",
    "user_bubble": "#238636",
    "assistant_bg": "transparent",
    "error": "#f85149",
    "warning": "#d29922",
    "success": "#3fb950",
    "tool_bg": "#1f2428",
    "code_bg": "#161b22",
}


class SmartInput:
    """Smart input field with autocomplete suggestions."""
    
    SUGGESTIONS = [
        "Show system status",
        "Check CPU usage",
        "Show memory usage",
        "List running processes",
        "Check disk space",
        "Run system health check",
        "Search for files",
        "Clean temp files",
        "Show network connections",
        "Git status",
        "Open browser",
        "List workflows",
        "Quick insights",
    ]
    
    def __init__(self, parent, on_send: Callable, theme: dict):
        self.parent = parent
        self.on_send = on_send
        self.theme = theme
        self.suggestion_visible = False
        self.selected_suggestion = 0
        self.filtered_suggestions = []
        self.command_history: List[str] = []
        self.history_index = -1
        
        self._create_widget()
    
    def _create_widget(self):
        """Create the smart input widget."""
        if not CTK_AVAILABLE:
            return
        
        self.frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        
        # Input wrapper with border
        self.input_wrapper = ctk.CTkFrame(
            self.frame,
            fg_color=self.theme["bg_input"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"]
        )
        self.input_wrapper.pack(fill="x", padx=16, pady=12)
        
        # Inner container
        inner = ctk.CTkFrame(self.input_wrapper, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Text input
        self.input_field = ctk.CTkTextbox(
            inner,
            height=50,
            fg_color="transparent",
            font=ctk.CTkFont(size=14),
            text_color=self.theme["text_primary"],
            wrap="word",
            border_width=0
        )
        self.input_field.pack(side="left", fill="both", expand=True, padx=8, pady=4)
        
        # Send button
        self.send_btn = ctk.CTkButton(
            inner,
            text="↑",
            width=36,
            height=36,
            corner_radius=18,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            command=self._send
        )
        self.send_btn.pack(side="right", padx=4)
        
        # Placeholder
        self._placeholder = "Message SysAgent..."
        self._placeholder_active = True
        self._show_placeholder()
        
        # Bindings
        self.input_field.bind("<FocusIn>", self._on_focus_in)
        self.input_field.bind("<FocusOut>", self._on_focus_out)
        self.input_field.bind("<Return>", self._on_return)
        self.input_field.bind("<Shift-Return>", lambda e: None)
        self.input_field.bind("<KeyRelease>", self._on_key_release)
        self.input_field.bind("<Up>", self._on_up)
        self.input_field.bind("<Down>", self._on_down)
        self.input_field.bind("<Tab>", self._on_tab)
        self.input_field.bind("<Escape>", self._hide_suggestions)
        
        # Suggestion popup
        self.suggestion_frame = None
    
    def _show_placeholder(self):
        """Show placeholder text."""
        self._placeholder_active = True
        self.input_field.delete("1.0", "end")
        self.input_field.insert("1.0", self._placeholder)
        self.input_field.configure(text_color=self.theme["text_muted"])
    
    def _on_focus_in(self, event):
        """Handle focus in."""
        self.input_wrapper.configure(border_color=self.theme["border_focus"])
        if self._placeholder_active:
            self.input_field.delete("1.0", "end")
            self.input_field.configure(text_color=self.theme["text_primary"])
            self._placeholder_active = False
    
    def _on_focus_out(self, event):
        """Handle focus out."""
        self.input_wrapper.configure(border_color=self.theme["border"])
        content = self.input_field.get("1.0", "end").strip()
        if not content:
            self._show_placeholder()
        self._hide_suggestions(None)
    
    def _on_return(self, event):
        """Handle Enter key."""
        if event.state & 0x1:  # Shift pressed
            return None
        self._send()
        return "break"
    
    def _on_key_release(self, event):
        """Handle key release for autocomplete."""
        if event.keysym in ("Up", "Down", "Return", "Tab", "Escape", "Shift_L", "Shift_R"):
            return
        
        content = self.input_field.get("1.0", "end").strip()
        if content and not self._placeholder_active:
            self._show_suggestions(content)
        else:
            self._hide_suggestions(None)
    
    def _show_suggestions(self, query: str):
        """Show autocomplete suggestions."""
        query_lower = query.lower()
        self.filtered_suggestions = [
            s for s in self.SUGGESTIONS
            if query_lower in s.lower() and s.lower() != query_lower
        ][:5]
        
        if not self.filtered_suggestions:
            self._hide_suggestions(None)
            return
        
        if not self.suggestion_frame:
            self.suggestion_frame = ctk.CTkFrame(
                self.frame,
                fg_color=self.theme["bg_secondary"],
                corner_radius=8,
                border_width=1,
                border_color=self.theme["border"]
            )
        
        # Clear existing
        for widget in self.suggestion_frame.winfo_children():
            widget.destroy()
        
        self.selected_suggestion = 0
        
        for i, suggestion in enumerate(self.filtered_suggestions):
            bg = self.theme["bg_tertiary"] if i == self.selected_suggestion else "transparent"
            btn = ctk.CTkButton(
                self.suggestion_frame,
                text=suggestion,
                font=ctk.CTkFont(size=13),
                height=32,
                anchor="w",
                fg_color=bg,
                hover_color=self.theme["bg_tertiary"],
                text_color=self.theme["text_primary"],
                command=lambda s=suggestion: self._select_suggestion(s)
            )
            btn.pack(fill="x", padx=4, pady=2)
        
        self.suggestion_frame.place(
            in_=self.input_wrapper,
            relx=0,
            rely=0,
            y=-len(self.filtered_suggestions) * 36 - 10,
            relwidth=1
        )
        self.suggestion_visible = True
    
    def _hide_suggestions(self, event):
        """Hide suggestions."""
        if self.suggestion_frame:
            self.suggestion_frame.place_forget()
        self.suggestion_visible = False
    
    def _select_suggestion(self, suggestion: str):
        """Select a suggestion."""
        self.input_field.delete("1.0", "end")
        self.input_field.insert("1.0", suggestion)
        self._placeholder_active = False
        self._hide_suggestions(None)
        self.input_field.focus_set()
    
    def _on_up(self, event):
        """Navigate suggestions up or history."""
        if self.suggestion_visible and self.filtered_suggestions:
            self.selected_suggestion = max(0, self.selected_suggestion - 1)
            self._update_suggestion_highlight()
            return "break"
        elif self.command_history:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.set_text(self.command_history[-(self.history_index + 1)])
            return "break"
    
    def _on_down(self, event):
        """Navigate suggestions down or history."""
        if self.suggestion_visible and self.filtered_suggestions:
            self.selected_suggestion = min(len(self.filtered_suggestions) - 1, self.selected_suggestion + 1)
            self._update_suggestion_highlight()
            return "break"
        elif self.history_index > 0:
            self.history_index -= 1
            self.set_text(self.command_history[-(self.history_index + 1)])
            return "break"
        elif self.history_index == 0:
            self.history_index = -1
            self.set_text("")
            return "break"
    
    def _on_tab(self, event):
        """Accept suggestion on tab."""
        if self.suggestion_visible and self.filtered_suggestions:
            self._select_suggestion(self.filtered_suggestions[self.selected_suggestion])
            return "break"
    
    def _update_suggestion_highlight(self):
        """Update suggestion highlight."""
        if not self.suggestion_frame:
            return
        
        for i, widget in enumerate(self.suggestion_frame.winfo_children()):
            bg = self.theme["bg_tertiary"] if i == self.selected_suggestion else "transparent"
            widget.configure(fg_color=bg)
    
    def _send(self):
        """Send the message."""
        content = self.input_field.get("1.0", "end").strip()
        
        if self._placeholder_active or not content:
            return
        
        # Add to history
        if content and (not self.command_history or self.command_history[-1] != content):
            self.command_history.append(content)
        self.history_index = -1
        
        # Clear and show placeholder
        self.input_field.delete("1.0", "end")
        self._show_placeholder()
        self._hide_suggestions(None)
        
        # Send
        if self.on_send:
            self.on_send(content)
    
    def set_text(self, text: str):
        """Set input text."""
        self.input_field.delete("1.0", "end")
        if text:
            self.input_field.insert("1.0", text)
            self._placeholder_active = False
            self.input_field.configure(text_color=self.theme["text_primary"])
        else:
            self._show_placeholder()
    
    def get_frame(self):
        return self.frame
    
    def set_enabled(self, enabled: bool):
        """Enable/disable input."""
        state = "normal" if enabled else "disabled"
        self.send_btn.configure(state=state)


class ToolExecutionIndicator:
    """Shows tool execution status inline."""
    
    def __init__(self, parent, theme: dict):
        self.parent = parent
        self.theme = theme
        self.frame = None
        self.status_label = None
        self.start_time = None
        self.animation_id = None
    
    def show(self, tool_name: str, action: str = ""):
        """Show execution indicator."""
        if not CTK_AVAILABLE:
            return
        
        self.start_time = time.time()
        
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.theme["tool_bg"],
            corner_radius=8,
            height=36
        )
        self.frame.pack(fill="x", padx=56, pady=4)
        self.frame.pack_propagate(False)
        
        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12)
        
        # Spinner
        self.spinner_label = ctk.CTkLabel(
            inner,
            text="◐",
            font=ctk.CTkFont(size=14),
            text_color=self.theme["accent"],
            width=20
        )
        self.spinner_label.pack(side="left")
        
        # Tool name
        display_name = tool_name.replace("_", " ").title()
        if action:
            display_name += f" → {action}"
        
        self.status_label = ctk.CTkLabel(
            inner,
            text=display_name,
            font=ctk.CTkFont(size=12),
            text_color=self.theme["text_secondary"]
        )
        self.status_label.pack(side="left", padx=8)
        
        # Duration
        self.duration_label = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self.theme["text_muted"]
        )
        self.duration_label.pack(side="right")
        
        self._animate_spinner()
    
    def _animate_spinner(self):
        """Animate the spinner."""
        if not self.frame or not self.spinner_label:
            return
        
        try:
            spinners = ["◐", "◓", "◑", "◒"]
            current = spinners.index(self.spinner_label.cget("text")) if self.spinner_label.cget("text") in spinners else 0
            self.spinner_label.configure(text=spinners[(current + 1) % 4])
            
            # Update duration
            if self.start_time and self.duration_label:
                elapsed = int((time.time() - self.start_time) * 1000)
                self.duration_label.configure(text=f"{elapsed}ms")
            
            self.animation_id = self.parent.after(100, self._animate_spinner)
        except Exception:
            pass
    
    def complete(self, success: bool = True):
        """Mark as complete."""
        if self.animation_id:
            try:
                self.parent.after_cancel(self.animation_id)
            except Exception:
                pass
        
        if not self.frame:
            return
        
        try:
            icon = "✓" if success else "✗"
            color = self.theme["success"] if success else self.theme["error"]
            self.spinner_label.configure(text=icon, text_color=color)
            
            # Final duration
            if self.start_time:
                elapsed = int((time.time() - self.start_time) * 1000)
                self.duration_label.configure(text=f"{elapsed}ms")
        except Exception:
            pass
    
    def destroy(self):
        """Remove indicator."""
        if self.animation_id:
            try:
                self.parent.after_cancel(self.animation_id)
            except Exception:
                pass
        if self.frame:
            try:
                self.frame.destroy()
            except Exception:
                pass


class ChatInterface:
    """Cursor AI-style chat interface."""
    
    def __init__(self, parent, on_send: Optional[Callable[[str], None]] = None):
        """Initialize the chat interface."""
        self.parent = parent
        self.on_send = on_send
        self.messages: List[ChatMessage] = []
        self.message_queue = queue.Queue()
        self.is_processing = False
        self.last_query = ""
        self.current_tool_indicator: Optional[ToolExecutionIndicator] = None
        self.stream_data: Optional[Dict] = None
        self.theme = THEME
        
        self._create_ui()
        self._start_queue_processor()
    
    def _create_ui(self):
        """Create the main UI structure."""
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(self.parent, fg_color=self.theme["bg_primary"])
        else:
            self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        self._create_header()
        self._create_messages_area()
        self._create_input_area()
        self._add_welcome_message()
    
    def _create_header(self):
        """Create a minimal header."""
        if not CTK_AVAILABLE:
            return
        
        header = ctk.CTkFrame(
            self.frame,
            fg_color=self.theme["bg_secondary"],
            corner_radius=0,
            height=50
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Left - Title
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="y", padx=16)
        
        ctk.CTkLabel(
            left,
            text="💬 Chat",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left", pady=12)
        
        # Status
        self.status_frame = ctk.CTkFrame(left, fg_color="transparent")
        self.status_frame.pack(side="left", padx=16)
        
        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=8),
            text_color=self.theme["success"]
        )
        self.status_dot.pack(side="left")
        
        self.status_text = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=self.theme["text_muted"]
        )
        self.status_text.pack(side="left", padx=(4, 0))
        
        # Right - Actions
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", fill="y", padx=16)
        
        btn_style = {
            "width": 32, "height": 32, "corner_radius": 6,
            "fg_color": "transparent",
            "hover_color": self.theme["bg_tertiary"],
            "font": ctk.CTkFont(size=14)
        }
        
        ctk.CTkButton(right, text="🗑", command=self.clear_chat, **btn_style).pack(side="right", padx=2)
        ctk.CTkButton(right, text="📤", command=self._export_chat, **btn_style).pack(side="right", padx=2)
    
    def _create_messages_area(self):
        """Create the scrollable messages area."""
        if not CTK_AVAILABLE:
            self.messages_frame = ttk.Frame(self.frame)
            self.messages_frame.pack(fill="both", expand=True)
            return
        
        self.messages_frame = ctk.CTkScrollableFrame(
            self.frame,
            fg_color=self.theme["bg_primary"],
            corner_radius=0
        )
        self.messages_frame.pack(fill="both", expand=True)
    
    def _create_input_area(self):
        """Create the message input area."""
        if not CTK_AVAILABLE:
            input_frame = ttk.Frame(self.frame)
            input_frame.pack(fill="x", side="bottom")
            self.input_field = ttk.Entry(input_frame)
            self.input_field.pack(fill="x", padx=10, pady=10)
            self.input_field.bind("<Return>", lambda e: self._send_message())
            return
        
        input_container = ctk.CTkFrame(
            self.frame,
            fg_color=self.theme["bg_secondary"],
            corner_radius=0
        )
        input_container.pack(fill="x", side="bottom")
        
        self.smart_input = SmartInput(input_container, self._send_message, self.theme)
        self.smart_input.get_frame().pack(fill="x")
        
        # For backwards compatibility
        self.input_field = self.smart_input.input_field
    
    def _send_message(self, content: str = None):
        """Send a message."""
        if content is None:
            content = self.input_field.get("1.0", "end").strip()
        
        if not content or self.is_processing:
            return
        
        self.last_query = content
        
        # Add user message
        self._add_message(content, MessageType.USER)
        
        # Start processing
        self._set_processing(True)
        
        # Call handler
        if self.on_send:
            self.on_send(content)
        else:
            self._add_message("No agent connected. Configure in Settings.", MessageType.ERROR)
            self._set_processing(False)
    
    def _send_message_direct(self, message: str):
        """Send a message directly (for external calls)."""
        if hasattr(self, 'smart_input'):
            self.smart_input.set_text(message)
        self._send_message(message)
    
    def _set_input_text(self, text: str):
        """Set input field text."""
        if hasattr(self, 'smart_input'):
            self.smart_input.set_text(text)
    
    def _set_processing(self, processing: bool):
        """Set processing state."""
        self.is_processing = processing
        
        if not CTK_AVAILABLE:
            return
        
        try:
            if processing:
                self.status_dot.configure(text_color=self.theme["warning"])
                self.status_text.configure(text="Thinking...")
                if hasattr(self, 'smart_input'):
                    self.smart_input.set_enabled(False)
            else:
                self.status_dot.configure(text_color=self.theme["success"])
                self.status_text.configure(text="Ready")
                if hasattr(self, 'smart_input'):
                    self.smart_input.set_enabled(True)
        except Exception:
            pass
    
    def _add_message(self, content: str, msg_type: MessageType, **kwargs):
        """Add a message to the chat."""
        message = ChatMessage(content=content, msg_type=msg_type, **kwargs)
        self.messages.append(message)
        self._render_message(message)
    
    def _render_message(self, message: ChatMessage):
        """Render a message."""
        if not CTK_AVAILABLE:
            return
        
        try:
            if not self.messages_frame.winfo_exists():
                return
        except Exception:
            return
        
        container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        container.pack(fill="x", padx=16, pady=8)
        
        if message.msg_type == MessageType.USER:
            self._render_user_message(container, message)
        elif message.msg_type == MessageType.ASSISTANT:
            self._render_assistant_message(container, message)
        elif message.msg_type == MessageType.ERROR:
            self._render_error_message(container, message)
        elif message.msg_type == MessageType.SYSTEM:
            self._render_system_message(container, message)
        
        self._scroll_to_bottom()
    
    def _render_user_message(self, container, message: ChatMessage):
        """Render a user message."""
        # Right-aligned
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(anchor="e")
        
        bubble = ctk.CTkFrame(
            row,
            fg_color=self.theme["user_bubble"],
            corner_radius=16
        )
        bubble.pack(anchor="e")
        
        ctk.CTkLabel(
            bubble,
            text=message.content,
            font=ctk.CTkFont(size=14),
            text_color="white",
            wraplength=500,
            justify="right"
        ).pack(padx=16, pady=10)
    
    def _render_assistant_message(self, container, message: ChatMessage):
        """Render an assistant message."""
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(anchor="w", fill="x")
        
        # Avatar
        ctk.CTkLabel(
            row,
            text="🧠",
            font=ctk.CTkFont(size=24),
            width=36
        ).pack(side="left", anchor="n", padx=(0, 8))
        
        # Content
        content_frame = ctk.CTkFrame(row, fg_color="transparent")
        content_frame.pack(side="left", fill="x", expand=True)
        
        # Parse markdown
        self._render_markdown(content_frame, message.content)
        
        # Actions
        actions = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions.pack(anchor="w", pady=(8, 0))
        
        btn_style = {
            "width": 28, "height": 24, "corner_radius": 4,
            "font": ctk.CTkFont(size=12),
            "fg_color": "transparent",
            "hover_color": self.theme["bg_tertiary"],
            "text_color": self.theme["text_muted"]
        }
        
        ctk.CTkButton(actions, text="📋", command=lambda: self._copy_text(message.content), **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="🔄", command=self._retry_last, **btn_style).pack(side="left", padx=2)
        
        # Follow-ups
        self._add_followups(content_frame)
    
    def _render_markdown(self, parent, content: str):
        """Render markdown content."""
        # Split by code blocks
        code_pattern = r'```(\w*)\n?([\s\S]*?)```'
        parts = re.split(code_pattern, content)
        
        i = 0
        while i < len(parts):
            text_part = parts[i].strip()
            if text_part:
                # Simple markdown cleanup
                text_part = re.sub(r'\*\*(.+?)\*\*', r'\1', text_part)
                text_part = re.sub(r'\*(.+?)\*', r'\1', text_part)
                
                ctk.CTkLabel(
                    parent,
                    text=text_part,
                    font=ctk.CTkFont(size=14),
                    text_color=self.theme["text_primary"],
                    wraplength=550,
                    justify="left"
                ).pack(anchor="w", pady=4)
            
            i += 1
            
            # Code block
            if i + 1 < len(parts):
                lang = parts[i] or ""
                code = parts[i + 1].strip()
                
                if code:
                    code_frame = ctk.CTkFrame(
                        parent,
                        fg_color=self.theme["code_bg"],
                        corner_radius=8
                    )
                    code_frame.pack(fill="x", pady=6)
                    
                    # Header
                    header = ctk.CTkFrame(code_frame, fg_color="transparent")
                    header.pack(fill="x", padx=12, pady=(8, 0))
                    
                    if lang:
                        ctk.CTkLabel(
                            header,
                            text=lang,
                            font=ctk.CTkFont(size=10),
                            text_color=self.theme["text_muted"]
                        ).pack(side="left")
                    
                    ctk.CTkButton(
                        header,
                        text="Copy",
                        width=50,
                        height=20,
                        corner_radius=4,
                        font=ctk.CTkFont(size=10),
                        fg_color=self.theme["bg_tertiary"],
                        hover_color=self.theme["border"],
                        command=lambda c=code: self._copy_text(c)
                    ).pack(side="right")
                    
                    # Code
                    ctk.CTkLabel(
                        code_frame,
                        text=code,
                        font=ctk.CTkFont(size=12, family="Consolas"),
                        text_color=self.theme["text_primary"],
                        wraplength=530,
                        justify="left"
                    ).pack(anchor="w", padx=12, pady=(4, 12))
                
                i += 2
    
    def _render_error_message(self, container, message: ChatMessage):
        """Render an error message."""
        bubble = ctk.CTkFrame(
            container,
            fg_color=self.theme["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["error"]
        )
        bubble.pack(anchor="w", padx=44)
        
        ctk.CTkLabel(
            bubble,
            text=f"⚠️ {message.content}",
            font=ctk.CTkFont(size=13),
            text_color=self.theme["error"],
            wraplength=500
        ).pack(padx=16, pady=12)
    
    def _render_system_message(self, container, message: ChatMessage):
        """Render a system message."""
        bubble = ctk.CTkFrame(
            container,
            fg_color=self.theme["bg_secondary"],
            corner_radius=12
        )
        bubble.pack(fill="x", padx=44)
        
        ctk.CTkLabel(
            bubble,
            text=message.content,
            font=ctk.CTkFont(size=13),
            text_color=self.theme["text_secondary"],
            wraplength=550,
            justify="left"
        ).pack(padx=16, pady=16)
    
    def _add_followups(self, parent):
        """Add smart follow-up suggestions."""
        suggestions = self._generate_followups()
        if not suggestions:
            return
        
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(anchor="w", pady=(8, 0))
        
        for suggestion in suggestions[:3]:
            btn = ctk.CTkButton(
                frame,
                text=suggestion,
                height=28,
                corner_radius=14,
                font=ctk.CTkFont(size=11),
                fg_color=self.theme["bg_tertiary"],
                hover_color=self.theme["border"],
                text_color=self.theme["accent"],
                command=lambda s=suggestion: self._send_message_direct(s)
            )
            btn.pack(side="left", padx=3)
    
    def _generate_followups(self) -> List[str]:
        """Generate smart follow-up suggestions."""
        if not self.last_query:
            return []
        
        query_lower = self.last_query.lower()
        
        patterns = {
            "cpu": ["Show top CPU processes", "Monitor CPU usage"],
            "memory": ["Clear memory cache", "Find memory hogs"],
            "disk": ["Find large files", "Clean temp files"],
            "process": ["Kill process", "Monitor process"],
            "system": ["Run health check", "Show all stats"],
            "file": ["Search content", "Organize files"],
            "git": ["Git log", "Git diff"],
            "network": ["Check ports", "Test connectivity"],
        }
        
        suggestions = []
        for key, sug in patterns.items():
            if key in query_lower:
                suggestions.extend(sug)
        
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
        
        container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        container.pack(fill="x", padx=16, pady=8)
        
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(anchor="w", fill="x")
        
        # Avatar
        ctk.CTkLabel(row, text="🧠", font=ctk.CTkFont(size=24), width=36).pack(side="left", anchor="n", padx=(0, 8))
        
        # Content label
        content_label = ctk.CTkLabel(
            row,
            text="▌",
            font=ctk.CTkFont(size=14),
            text_color=self.theme["text_primary"],
            wraplength=550,
            justify="left"
        )
        content_label.pack(side="left", anchor="w")
        
        self.stream_data = {
            "container": container,
            "label": content_label,
            "content": ""
        }
        
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
        """Finalize streaming message."""
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
        
        if status == "running" and not self.current_tool_indicator:
            self.current_tool_indicator = ToolExecutionIndicator(self.messages_frame, self.theme)
            self.current_tool_indicator.show(tool_name, action or details)
        elif self.current_tool_indicator:
            self.current_tool_indicator.complete(status == "success")
            self.current_tool_indicator = None
        
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
        welcome = """👋 Welcome to SysAgent!

I can help you with system monitoring, file management, automation, and more.

Try asking me something like:
• "Show system status"
• "Check disk usage"
• "Run health check"
• "Search for large files"

Just type below to get started!"""
        
        self._add_message(welcome, MessageType.SYSTEM)
    
    def _scroll_to_bottom(self):
        """Scroll to bottom."""
        try:
            if CTK_AVAILABLE and hasattr(self.messages_frame, '_parent_canvas'):
                self.messages_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
    
    def _copy_text(self, text: str):
        """Copy text to clipboard."""
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
            self._show_toast("Copied!")
        except Exception:
            pass
    
    def _retry_last(self):
        """Retry last message."""
        if self.last_query:
            self._send_message_direct(self.last_query)
    
    def _export_chat(self):
        """Export chat."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")]
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write("# SysAgent Chat\n\n")
                    for msg in self.messages:
                        role = "You" if msg.msg_type == MessageType.USER else "SysAgent"
                        f.write(f"**{role}**: {msg.content}\n\n")
                self._show_toast("Exported!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _show_toast(self, message: str):
        """Show toast."""
        if CTK_AVAILABLE:
            try:
                self.status_text.configure(text=message)
                self.parent.after(2000, lambda: self.status_text.configure(text="Ready"))
            except Exception:
                pass
    
    def clear_chat(self):
        """Clear chat."""
        try:
            for widget in self.messages_frame.winfo_children():
                widget.destroy()
            self.messages.clear()
            self._add_message("Chat cleared. How can I help?", MessageType.SYSTEM)
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
            def process():
                try:
                    result = self.agent.process_command(message)
                    response = result.get('message', 'Done')
                    msg_type = "text" if result.get('success') else "error"
                    self.chat.add_message(response, is_user=False, message_type=msg_type)
                except Exception as e:
                    self.chat.add_message(f"Error: {e}", is_user=False, message_type="error")
            
            import threading
            thread = threading.Thread(target=process, daemon=True)
            thread.start()
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
