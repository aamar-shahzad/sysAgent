"""
Reusable UI Components for SysAgent.
Modern, animated, and feature-rich widgets.
"""

import tkinter as tk
from typing import Optional, Callable, List, Dict, Any
import time
import threading

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


# Theme definitions
THEMES = {
    "dark": {
        "bg": "#0a0a0f",
        "bg_secondary": "#12121a",
        "bg_tertiary": "#1a1a24",
        "bg_hover": "#22222e",
        "sidebar": "#0d0d14",
        "border": "#2a2a35",
        "border_focus": "#4a6cf7",
        "text": "#ffffff",
        "text_secondary": "#9898a8",
        "text_muted": "#5a5a6a",
        "accent": "#4a6cf7",
        "accent_hover": "#5a7cff",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "code_bg": "#15151f",
    },
    "light": {
        "bg": "#ffffff",
        "bg_secondary": "#f5f5f7",
        "bg_tertiary": "#e8e8ed",
        "bg_hover": "#dcdce2",
        "sidebar": "#f0f0f5",
        "border": "#d0d0d8",
        "border_focus": "#4a6cf7",
        "text": "#1a1a1a",
        "text_secondary": "#555566",
        "text_muted": "#888899",
        "accent": "#4a6cf7",
        "accent_hover": "#3a5ce7",
        "success": "#16a34a",
        "warning": "#d97706",
        "error": "#dc2626",
        "code_bg": "#f0f0f5",
    }
}

# Current theme
_current_theme = "dark"


def get_theme() -> Dict[str, str]:
    """Get current theme colors."""
    return THEMES.get(_current_theme, THEMES["dark"])


def set_theme(theme: str):
    """Set current theme."""
    global _current_theme
    if theme in THEMES:
        _current_theme = theme
        if CTK_AVAILABLE:
            ctk.set_appearance_mode(theme)


def toggle_theme() -> str:
    """Toggle between dark and light theme."""
    global _current_theme
    _current_theme = "light" if _current_theme == "dark" else "dark"
    if CTK_AVAILABLE:
        ctk.set_appearance_mode(_current_theme)
    return _current_theme


class CollapsibleSection:
    """A collapsible section with header and content."""
    
    def __init__(self, parent, title: str, icon: str = "", initially_open: bool = True):
        self.parent = parent
        self.title = title
        self.icon = icon
        self.is_open = initially_open
        self.colors = get_theme()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI."""
        if not CTK_AVAILABLE:
            return
        
        self.frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.frame.pack(fill="x", pady=2)
        
        # Header
        self.header = ctk.CTkButton(
            self.frame,
            text=f"{'▼' if self.is_open else '▶'} {self.icon} {self.title}",
            anchor="w",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color=self.colors["bg_hover"],
            text_color=self.colors["text_muted"],
            command=self.toggle
        )
        self.header.pack(fill="x", padx=4)
        
        # Content
        self.content = ctk.CTkFrame(self.frame, fg_color="transparent")
        if self.is_open:
            self.content.pack(fill="x", padx=8, pady=(0, 5))
    
    def toggle(self):
        """Toggle section open/close."""
        self.is_open = not self.is_open
        
        arrow = "▼" if self.is_open else "▶"
        self.header.configure(text=f"{arrow} {self.icon} {self.title}")
        
        if self.is_open:
            self.content.pack(fill="x", padx=8, pady=(0, 5))
        else:
            self.content.pack_forget()
    
    def add_item(self, text: str, command: Callable, is_active: bool = False):
        """Add an item to the section."""
        if not CTK_AVAILABLE:
            return
        
        btn = ctk.CTkButton(
            self.content,
            text=f"  {text}",
            anchor="w",
            height=30,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["accent"] if is_active else "transparent",
            hover_color=self.colors["accent_hover"] if is_active else self.colors["bg_tertiary"],
            text_color=self.colors["text"],
            command=command
        )
        btn.pack(fill="x", pady=1)
        return btn


class SearchBar:
    """A search bar with suggestions."""
    
    def __init__(self, parent, placeholder: str = "Search...",
                 on_search: Optional[Callable[[str], None]] = None):
        self.parent = parent
        self.placeholder = placeholder
        self.on_search = on_search
        self.colors = get_theme()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI."""
        if not CTK_AVAILABLE:
            return
        
        self.frame = ctk.CTkFrame(self.parent, fg_color=self.colors["bg_tertiary"], corner_radius=8)
        self.frame.pack(fill="x", pady=5)
        
        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)
        
        # Search icon
        ctk.CTkLabel(
            inner,
            text="🔍",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_muted"]
        ).pack(side="left")
        
        # Entry
        self.entry = ctk.CTkEntry(
            inner,
            placeholder_text=self.placeholder,
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(size=13)
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=8)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<KeyRelease>", self._on_key)
        
        # Clear button
        self.clear_btn = ctk.CTkButton(
            inner,
            text="✕",
            width=24,
            height=24,
            corner_radius=12,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=self.colors["bg_hover"],
            text_color=self.colors["text_muted"],
            command=self.clear
        )
    
    def _on_enter(self, event):
        """Handle enter key."""
        if self.on_search:
            self.on_search(self.entry.get())
    
    def _on_key(self, event):
        """Handle key release."""
        text = self.entry.get()
        if text:
            self.clear_btn.pack(side="right")
        else:
            self.clear_btn.pack_forget()
    
    def clear(self):
        """Clear search."""
        self.entry.delete(0, "end")
        self.clear_btn.pack_forget()
        if self.on_search:
            self.on_search("")
    
    def get(self) -> str:
        """Get search text."""
        return self.entry.get()


class TabView:
    """A tab view component."""
    
    def __init__(self, parent, tabs: List[str]):
        self.parent = parent
        self.tabs = tabs
        self.active_tab = 0
        self.tab_frames: Dict[str, ctk.CTkFrame] = {}
        self.tab_buttons: List[ctk.CTkButton] = []
        self.colors = get_theme()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI."""
        if not CTK_AVAILABLE:
            return
        
        self.frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.frame.pack(fill="both", expand=True)
        
        # Tab bar
        tab_bar = ctk.CTkFrame(self.frame, fg_color=self.colors["bg_secondary"], height=40)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)
        
        for i, tab in enumerate(self.tabs):
            btn = ctk.CTkButton(
                tab_bar,
                text=tab,
                height=36,
                corner_radius=0,
                font=ctk.CTkFont(size=12),
                fg_color=self.colors["bg"] if i == 0 else "transparent",
                hover_color=self.colors["bg_tertiary"],
                text_color=self.colors["text"] if i == 0 else self.colors["text_muted"],
                command=lambda idx=i: self.select_tab(idx)
            )
            btn.pack(side="left", padx=2, pady=2)
            self.tab_buttons.append(btn)
        
        # Content area
        self.content = ctk.CTkFrame(self.frame, fg_color=self.colors["bg"])
        self.content.pack(fill="both", expand=True)
        
        # Create frames for each tab
        for tab in self.tabs:
            frame = ctk.CTkFrame(self.content, fg_color="transparent")
            self.tab_frames[tab] = frame
        
        # Show first tab
        self.tab_frames[self.tabs[0]].pack(fill="both", expand=True)
    
    def select_tab(self, index: int):
        """Select a tab."""
        if index == self.active_tab:
            return
        
        # Hide current
        self.tab_frames[self.tabs[self.active_tab]].pack_forget()
        self.tab_buttons[self.active_tab].configure(
            fg_color="transparent",
            text_color=self.colors["text_muted"]
        )
        
        # Show new
        self.active_tab = index
        self.tab_frames[self.tabs[index]].pack(fill="both", expand=True)
        self.tab_buttons[index].configure(
            fg_color=self.colors["bg"],
            text_color=self.colors["text"]
        )
    
    def get_tab_frame(self, tab_name: str) -> Optional[ctk.CTkFrame]:
        """Get frame for a tab."""
        return self.tab_frames.get(tab_name)


class Toast:
    """A toast notification."""
    
    def __init__(self, parent, message: str, duration_ms: int = 3000,
                 toast_type: str = "info"):
        self.parent = parent
        self.message = message
        self.duration_ms = duration_ms
        self.toast_type = toast_type
        self.colors = get_theme()
        
        self._show()
    
    def _show(self):
        """Show the toast."""
        if not CTK_AVAILABLE:
            return
        
        type_colors = {
            "info": self.colors["accent"],
            "success": self.colors["success"],
            "warning": self.colors["warning"],
            "error": self.colors["error"],
        }
        
        bg_color = type_colors.get(self.toast_type, self.colors["accent"])
        
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=bg_color,
            corner_radius=8
        )
        self.frame.place(relx=0.5, rely=0.95, anchor="s")
        
        ctk.CTkLabel(
            self.frame,
            text=self.message,
            font=ctk.CTkFont(size=12),
            text_color="white"
        ).pack(padx=20, pady=10)
        
        # Auto-dismiss
        self.frame.after(self.duration_ms, self._hide)
    
    def _hide(self):
        """Hide the toast."""
        if self.frame:
            try:
                self.frame.destroy()
            except Exception:
                pass


class ContextMenu:
    """A context menu for right-click actions."""
    
    def __init__(self, parent, items: List[tuple]):
        """
        Args:
            parent: Parent widget
            items: List of (label, command) tuples
        """
        self.parent = parent
        self.items = items
        self.menu = None
        self.colors = get_theme()
    
    def show(self, event):
        """Show context menu at event location."""
        if not CTK_AVAILABLE:
            return
        
        self.menu = tk.Menu(self.parent, tearoff=0, bg=self.colors["bg_secondary"],
                           fg=self.colors["text"], activebackground=self.colors["accent"])
        
        for label, command in self.items:
            if label == "-":
                self.menu.add_separator()
            else:
                self.menu.add_command(label=label, command=command)
        
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()


class DragDropZone:
    """A drag and drop zone for files."""
    
    def __init__(self, parent, on_drop: Callable[[List[str]], None],
                 accept_types: List[str] = None):
        self.parent = parent
        self.on_drop = on_drop
        self.accept_types = accept_types or ["*"]
        self.colors = get_theme()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI."""
        if not CTK_AVAILABLE:
            return
        
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors["bg_tertiary"],
            corner_radius=12,
            border_width=2,
            border_color=self.colors["border"]
        )
        self.frame.pack(fill="x", padx=16, pady=8)
        
        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(padx=20, pady=20)
        
        ctk.CTkLabel(
            inner,
            text="📁",
            font=ctk.CTkFont(size=32)
        ).pack()
        
        ctk.CTkLabel(
            inner,
            text="Drop files here or click to browse",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"]
        ).pack(pady=(10, 0))
        
        # Make clickable
        self.frame.bind("<Button-1>", self._browse)
        
        # Try to enable drag and drop
        try:
            self.frame.drop_target_register("DND_Files")
            self.frame.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass
    
    def _browse(self, event=None):
        """Open file browser."""
        from tkinter import filedialog
        files = filedialog.askopenfilenames()
        if files:
            self.on_drop(list(files))
    
    def _on_drop(self, event):
        """Handle dropped files."""
        files = event.data.split()
        if files:
            self.on_drop(files)


class KeyboardShortcutsPanel:
    """Panel showing keyboard shortcuts."""
    
    SHORTCUTS = [
        ("General", [
            ("⌘/Ctrl + K", "Open command palette"),
            ("⌘/Ctrl + N", "New chat"),
            ("⌘/Ctrl + S", "Settings"),
            ("⌘/Ctrl + Q", "Quit"),
            ("Escape", "Close popups"),
        ]),
        ("Chat", [
            ("Enter", "Send message"),
            ("Shift + Enter", "New line"),
            ("↑ / ↓", "Navigate history"),
            ("⌘/Ctrl + L", "Clear chat"),
        ]),
        ("Navigation", [
            ("⌘/Ctrl + 1", "Go to Chat"),
            ("⌘/Ctrl + 2", "Go to Dashboard"),
            ("⌘/Ctrl + 3", "Go to Settings"),
        ]),
    ]
    
    def __init__(self, parent):
        self.parent = parent
        self.colors = get_theme()
    
    def show(self):
        """Show shortcuts panel."""
        if not CTK_AVAILABLE:
            return
        
        popup = ctk.CTkToplevel(self.parent)
        popup.title("Keyboard Shortcuts")
        popup.geometry("450x500")
        popup.transient(self.parent)
        popup.configure(fg_color=self.colors["bg"])
        
        # Header
        header = ctk.CTkFrame(popup, fg_color=self.colors["bg_secondary"])
        header.pack(fill="x")
        
        ctk.CTkLabel(
            header,
            text="⌨️ Keyboard Shortcuts",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=16)
        
        # Content
        content = ctk.CTkScrollableFrame(popup, fg_color=self.colors["bg"])
        content.pack(fill="both", expand=True, padx=16, pady=16)
        
        for section_title, shortcuts in self.SHORTCUTS:
            # Section header
            ctk.CTkLabel(
                content,
                text=section_title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=self.colors["accent"]
            ).pack(anchor="w", pady=(16, 8))
            
            for shortcut, description in shortcuts:
                row = ctk.CTkFrame(content, fg_color="transparent")
                row.pack(fill="x", pady=3)
                
                # Shortcut badge
                badge = ctk.CTkFrame(row, fg_color=self.colors["bg_tertiary"], corner_radius=4)
                badge.pack(side="left")
                
                ctk.CTkLabel(
                    badge,
                    text=shortcut,
                    font=ctk.CTkFont(size=11, family="Consolas"),
                    text_color=self.colors["text"]
                ).pack(padx=8, pady=4)
                
                # Description
                ctk.CTkLabel(
                    row,
                    text=description,
                    font=ctk.CTkFont(size=12),
                    text_color=self.colors["text_secondary"]
                ).pack(side="left", padx=12)


class AnimatedButton:
    """Button with hover animation."""
    
    def __init__(self, parent, text: str, command: Callable,
                 icon: str = "", style: str = "primary"):
        self.parent = parent
        self.text = text
        self.command = command
        self.icon = icon
        self.style = style
        self.colors = get_theme()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the button."""
        if not CTK_AVAILABLE:
            return
        
        styles = {
            "primary": (self.colors["accent"], self.colors["accent_hover"], "white"),
            "secondary": (self.colors["bg_tertiary"], self.colors["bg_hover"], self.colors["text"]),
            "ghost": ("transparent", self.colors["bg_tertiary"], self.colors["text"]),
            "danger": (self.colors["error"], "#dc2626", "white"),
        }
        
        fg, hover, text_color = styles.get(self.style, styles["primary"])
        
        display_text = f"{self.icon} {self.text}" if self.icon else self.text
        
        self.button = ctk.CTkButton(
            self.parent,
            text=display_text,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color=fg,
            hover_color=hover,
            text_color=text_color,
            command=self.command
        )
        self.button.pack(pady=2)
    
    def pack(self, **kwargs):
        """Pack the button."""
        self.button.pack(**kwargs)
    
    def configure(self, **kwargs):
        """Configure the button."""
        self.button.configure(**kwargs)


class StatusIndicator:
    """A status indicator with icon and text."""
    
    def __init__(self, parent, status: str = "ready"):
        self.parent = parent
        self.status = status
        self.colors = get_theme()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the indicator."""
        if not CTK_AVAILABLE:
            return
        
        self.frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.frame.pack(side="left")
        
        self.dot = ctk.CTkLabel(
            self.frame,
            text="●",
            font=ctk.CTkFont(size=8),
            text_color=self.colors["success"]
        )
        self.dot.pack(side="left", padx=(0, 6))
        
        self.label = ctk.CTkLabel(
            self.frame,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        )
        self.label.pack(side="left")
    
    def set_status(self, status: str, text: str = ""):
        """Set status."""
        status_colors = {
            "ready": (self.colors["success"], "Ready"),
            "processing": (self.colors["warning"], "Processing..."),
            "error": (self.colors["error"], "Error"),
            "offline": (self.colors["text_muted"], "Offline"),
        }
        
        color, default_text = status_colors.get(status, (self.colors["text_muted"], status))
        
        self.dot.configure(text_color=color)
        self.label.configure(text=text or default_text)


class LoadingSpinner:
    """An animated loading spinner."""
    
    FRAMES = ["◐", "◓", "◑", "◒"]
    
    def __init__(self, parent, size: int = 16):
        self.parent = parent
        self.size = size
        self.colors = get_theme()
        self.running = False
        self.frame_index = 0
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the spinner."""
        if not CTK_AVAILABLE:
            return
        
        self.label = ctk.CTkLabel(
            self.parent,
            text="◐",
            font=ctk.CTkFont(size=self.size),
            text_color=self.colors["accent"]
        )
    
    def start(self):
        """Start spinning."""
        self.running = True
        self.label.pack()
        self._animate()
    
    def stop(self):
        """Stop spinning."""
        self.running = False
        self.label.pack_forget()
    
    def _animate(self):
        """Animate the spinner."""
        if not self.running:
            return
        
        self.frame_index = (self.frame_index + 1) % len(self.FRAMES)
        self.label.configure(text=self.FRAMES[self.frame_index])
        
        self.label.after(80, self._animate)
