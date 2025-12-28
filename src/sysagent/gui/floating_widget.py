"""
Floating Widget for SysAgent - Always-on-top mini interface.
Provides quick access to commands without opening the full GUI.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

import threading
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime


# Colors
COLORS = {
    "bg": "#1a1a2e",
    "bg_secondary": "#16213e",
    "accent": "#6366f1",
    "text": "#ffffff",
    "text_muted": "#94a3b8",
    "success": "#22c55e",
    "error": "#ef4444",
    "border": "#2a2a3e",
}


class FloatingWidget:
    """
    A small, always-on-top floating widget for quick command access.
    Can be dragged around the screen.
    """
    
    def __init__(
        self,
        on_command: Optional[Callable[[str], None]] = None,
        on_expand: Optional[Callable] = None,
        position: tuple = (100, 100)
    ):
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter required for floating widget")
        
        self.on_command = on_command
        self.on_expand = on_expand
        self.position = position
        self.is_expanded = False
        self.is_recording_macro = False
        self.recorded_actions: List[str] = []
        
        # Recent commands
        self.recent_commands: List[str] = []
        self.max_recent = 5
        
        # Quick actions
        self.quick_actions = [
            ("📊", "Show system status", "system_info"),
            ("🔍", "Search files", "smart_search"),
            ("📸", "Screenshot", "take_screenshot"),
            ("🔊", "Volume", "media_control"),
            ("📋", "Clipboard", "clipboard"),
        ]
        
        self._create_widget()
    
    def _create_widget(self):
        """Create the floating widget window."""
        self.root = ctk.CTk()
        self.root.title("")
        self.root.geometry(f"320x60+{self.position[0]}+{self.position[1]}")
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes("-topmost", True)  # Always on top
        self.root.configure(fg_color=COLORS["bg"])
        
        # Make window draggable
        self.root.bind("<Button-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._on_drag)
        
        # Main container
        self.main_frame = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["bg"],
            corner_radius=15,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Collapsed view
        self._create_collapsed_view()
        
        # Expanded view (hidden initially)
        self._create_expanded_view()
    
    def _create_collapsed_view(self):
        """Create the collapsed (mini) view."""
        self.collapsed_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.collapsed_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Left: Icon and drag handle
        left = ctk.CTkFrame(self.collapsed_frame, fg_color="transparent")
        left.pack(side="left")
        
        ctk.CTkLabel(
            left,
            text="🧠",
            font=ctk.CTkFont(size=20)
        ).pack(side="left", padx=(0, 8))
        
        # Center: Command input
        self.mini_input = ctk.CTkEntry(
            self.collapsed_frame,
            placeholder_text="Ask anything...",
            width=180,
            height=32,
            corner_radius=8,
            fg_color=COLORS["bg_secondary"],
            border_width=0
        )
        self.mini_input.pack(side="left", padx=4)
        self.mini_input.bind("<Return>", self._on_mini_submit)
        
        # Right: Expand button
        expand_btn = ctk.CTkButton(
            self.collapsed_frame,
            text="▼",
            width=32,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["bg_secondary"],
            command=self._toggle_expand
        )
        expand_btn.pack(side="right")
        
        # Quick action buttons
        for icon, tooltip, action in self.quick_actions[:3]:
            btn = ctk.CTkButton(
                self.collapsed_frame,
                text=icon,
                width=28,
                height=28,
                corner_radius=6,
                fg_color="transparent",
                hover_color=COLORS["bg_secondary"],
                command=lambda a=action: self._quick_action(a)
            )
            btn.pack(side="right", padx=1)
    
    def _create_expanded_view(self):
        """Create the expanded view with more options."""
        self.expanded_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        # Not packed initially
        
        # Quick actions grid
        actions_frame = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        actions_frame.pack(fill="x", padx=8, pady=4)
        
        for i, (icon, tooltip, action) in enumerate(self.quick_actions):
            btn = ctk.CTkButton(
                actions_frame,
                text=f"{icon}",
                width=50,
                height=40,
                corner_radius=8,
                fg_color=COLORS["bg_secondary"],
                hover_color=COLORS["border"],
                command=lambda a=action: self._quick_action(a)
            )
            btn.grid(row=0, column=i, padx=2, pady=2)
        
        # Recent commands
        recent_frame = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        recent_frame.pack(fill="x", padx=8, pady=4)
        
        ctk.CTkLabel(
            recent_frame,
            text="Recent:",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w")
        
        self.recent_list = ctk.CTkFrame(recent_frame, fg_color="transparent")
        self.recent_list.pack(fill="x")
        
        # Macro controls
        macro_frame = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        macro_frame.pack(fill="x", padx=8, pady=4)
        
        self.macro_btn = ctk.CTkButton(
            macro_frame,
            text="⏺ Record Macro",
            height=28,
            corner_radius=6,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border"],
            command=self._toggle_macro_recording
        )
        self.macro_btn.pack(side="left", padx=2)
        
        ctk.CTkButton(
            macro_frame,
            text="▶ Play Last",
            height=28,
            corner_radius=6,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border"],
            command=self._play_last_macro
        ).pack(side="left", padx=2)
        
        # Bottom buttons
        bottom = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        bottom.pack(fill="x", padx=8, pady=(4, 8))
        
        ctk.CTkButton(
            bottom,
            text="🔳 Full Window",
            height=28,
            corner_radius=6,
            fg_color=COLORS["accent"],
            command=self._open_full_window
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            bottom,
            text="▲ Collapse",
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=COLORS["bg_secondary"],
            command=self._toggle_expand
        ).pack(side="right", padx=2)
    
    def _toggle_expand(self):
        """Toggle between collapsed and expanded view."""
        if self.is_expanded:
            self.expanded_frame.pack_forget()
            self.collapsed_frame.pack(fill="both", expand=True, padx=8, pady=8)
            self.root.geometry(f"320x60+{self.root.winfo_x()}+{self.root.winfo_y()}")
        else:
            self.collapsed_frame.pack_forget()
            self.expanded_frame.pack(fill="both", expand=True)
            self.collapsed_frame.pack(fill="x", padx=8, pady=4)
            self.root.geometry(f"320x220+{self.root.winfo_x()}+{self.root.winfo_y()}")
            self._update_recent_list()
        
        self.is_expanded = not self.is_expanded
    
    def _start_drag(self, event):
        """Start dragging the widget."""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
    
    def _on_drag(self, event):
        """Handle widget dragging."""
        x = self.root.winfo_x() + event.x - self._drag_start_x
        y = self.root.winfo_y() + event.y - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")
    
    def _on_mini_submit(self, event):
        """Handle command submission from mini input."""
        command = self.mini_input.get().strip()
        if command:
            self._execute_command(command)
            self.mini_input.delete(0, "end")
    
    def _execute_command(self, command: str):
        """Execute a command."""
        # Add to recent
        if command not in self.recent_commands:
            self.recent_commands.insert(0, command)
            self.recent_commands = self.recent_commands[:self.max_recent]
        
        # Record if macro recording
        if self.is_recording_macro:
            self.recorded_actions.append(command)
        
        # Execute
        if self.on_command:
            self.on_command(command)
    
    def _quick_action(self, action: str):
        """Execute a quick action."""
        action_commands = {
            "system_info": "show system status",
            "smart_search": "search files",
            "take_screenshot": "take a screenshot",
            "media_control": "show volume controls",
            "clipboard": "show clipboard history",
        }
        command = action_commands.get(action, action)
        self._execute_command(command)
    
    def _update_recent_list(self):
        """Update the recent commands list."""
        for widget in self.recent_list.winfo_children():
            widget.destroy()
        
        for cmd in self.recent_commands[:3]:
            btn = ctk.CTkButton(
                self.recent_list,
                text=cmd[:30] + "..." if len(cmd) > 30 else cmd,
                height=24,
                corner_radius=4,
                fg_color="transparent",
                hover_color=COLORS["bg_secondary"],
                text_color=COLORS["text_muted"],
                anchor="w",
                command=lambda c=cmd: self._execute_command(c)
            )
            btn.pack(fill="x", pady=1)
    
    def _toggle_macro_recording(self):
        """Toggle macro recording."""
        if self.is_recording_macro:
            self.is_recording_macro = False
            self.macro_btn.configure(
                text="⏺ Record Macro",
                fg_color=COLORS["bg_secondary"]
            )
            # Save macro
            if self.recorded_actions:
                self._show_notification(f"Macro saved: {len(self.recorded_actions)} actions")
        else:
            self.is_recording_macro = True
            self.recorded_actions = []
            self.macro_btn.configure(
                text="⏹ Stop Recording",
                fg_color=COLORS["error"]
            )
    
    def _play_last_macro(self):
        """Play the last recorded macro."""
        if self.recorded_actions:
            for action in self.recorded_actions:
                self._execute_command(action)
        else:
            self._show_notification("No macro recorded")
    
    def _show_notification(self, message: str):
        """Show a brief notification."""
        # Create temporary notification
        notif = ctk.CTkLabel(
            self.main_frame,
            text=message,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["success"],
            fg_color=COLORS["bg_secondary"],
            corner_radius=4
        )
        notif.place(relx=0.5, rely=0.5, anchor="center")
        self.root.after(2000, notif.destroy)
    
    def _open_full_window(self):
        """Open the full SysAgent window."""
        if self.on_expand:
            self.on_expand()
    
    def add_command(self, command: str):
        """Add a command to recent list (called externally)."""
        if command not in self.recent_commands:
            self.recent_commands.insert(0, command)
            self.recent_commands = self.recent_commands[:self.max_recent]
    
    def run(self):
        """Start the widget."""
        self.root.mainloop()
    
    def destroy(self):
        """Destroy the widget."""
        try:
            self.root.destroy()
        except Exception:
            pass


class QuickLauncher:
    """
    Spotlight-like quick launcher for fast command access.
    Activated with a hotkey.
    """
    
    def __init__(
        self,
        on_command: Optional[Callable[[str], None]] = None,
        commands: List[Dict[str, Any]] = None
    ):
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter required")
        
        self.on_command = on_command
        self.commands = commands or []
        self.filtered_commands = []
        self.selected_index = 0
        self.is_visible = False
        
        self._create_launcher()
    
    def _create_launcher(self):
        """Create the quick launcher window."""
        self.root = ctk.CTkToplevel()
        self.root.title("")
        self.root.geometry("600x400")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(fg_color=COLORS["bg"])
        
        # Center on screen
        self.root.update_idletasks()
        width = 600
        height = 400
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 3) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Main container with border
        main = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["bg"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        main.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Search input
        search_frame = ctk.CTkFrame(main, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=16)
        
        ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=24)
        ).pack(side="left", padx=(0, 12))
        
        self.search_input = ctk.CTkEntry(
            search_frame,
            placeholder_text="Type a command or search...",
            height=44,
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            border_width=0
        )
        self.search_input.pack(side="left", fill="x", expand=True)
        self.search_input.bind("<KeyRelease>", self._on_search)
        self.search_input.bind("<Return>", self._on_select)
        self.search_input.bind("<Up>", self._on_up)
        self.search_input.bind("<Down>", self._on_down)
        self.search_input.bind("<Escape>", self._on_escape)
        
        # Divider
        ctk.CTkFrame(main, height=1, fg_color=COLORS["border"]).pack(fill="x")
        
        # Results list
        self.results_frame = ctk.CTkScrollableFrame(
            main,
            fg_color="transparent"
        )
        self.results_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Initial commands
        self._populate_default_commands()
        
        # Hide initially
        self.root.withdraw()
    
    def _populate_default_commands(self):
        """Populate with default commands."""
        default_commands = [
            {"icon": "📊", "name": "System Status", "command": "show system status", "category": "System"},
            {"icon": "💻", "name": "CPU Usage", "command": "show cpu usage", "category": "System"},
            {"icon": "🧠", "name": "Memory Usage", "command": "show memory usage", "category": "System"},
            {"icon": "💾", "name": "Disk Space", "command": "show disk space", "category": "System"},
            {"icon": "🔍", "name": "Search Files", "command": "search files", "category": "Files"},
            {"icon": "📁", "name": "Recent Files", "command": "show recent files", "category": "Files"},
            {"icon": "🗑️", "name": "Clean Temp Files", "command": "clean temp files", "category": "Files"},
            {"icon": "📸", "name": "Take Screenshot", "command": "take a screenshot", "category": "Media"},
            {"icon": "🔊", "name": "Volume Up", "command": "volume up", "category": "Media"},
            {"icon": "🔇", "name": "Mute", "command": "mute audio", "category": "Media"},
            {"icon": "🌐", "name": "Open Browser", "command": "open browser", "category": "Apps"},
            {"icon": "📝", "name": "New Note", "command": "create a new note", "category": "Documents"},
            {"icon": "📊", "name": "New Spreadsheet", "command": "create a spreadsheet", "category": "Documents"},
            {"icon": "⚙️", "name": "System Settings", "command": "open system settings", "category": "System"},
            {"icon": "🔄", "name": "Restart", "command": "restart computer", "category": "Power"},
            {"icon": "💤", "name": "Sleep", "command": "put computer to sleep", "category": "Power"},
        ]
        self.commands = default_commands
        self.filtered_commands = default_commands.copy()
        self._update_results()
    
    def _on_search(self, event):
        """Handle search input."""
        query = self.search_input.get().lower().strip()
        
        if not query:
            self.filtered_commands = self.commands.copy()
        else:
            self.filtered_commands = [
                cmd for cmd in self.commands
                if query in cmd["name"].lower() or query in cmd["command"].lower()
            ]
        
        self.selected_index = 0
        self._update_results()
    
    def _update_results(self):
        """Update the results list."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        for i, cmd in enumerate(self.filtered_commands[:10]):
            is_selected = i == self.selected_index
            
            item = ctk.CTkFrame(
                self.results_frame,
                fg_color=COLORS["accent"] if is_selected else "transparent",
                corner_radius=8
            )
            item.pack(fill="x", pady=2)
            
            inner = ctk.CTkFrame(item, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)
            
            ctk.CTkLabel(
                inner,
                text=cmd["icon"],
                font=ctk.CTkFont(size=18)
            ).pack(side="left", padx=(0, 12))
            
            text_frame = ctk.CTkFrame(inner, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(
                text_frame,
                text=cmd["name"],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                text_frame,
                text=cmd["command"],
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_muted"],
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                inner,
                text=cmd.get("category", ""),
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_muted"]
            ).pack(side="right")
            
            # Make clickable
            item.bind("<Button-1>", lambda e, c=cmd: self._execute_command(c["command"]))
            for child in item.winfo_children():
                child.bind("<Button-1>", lambda e, c=cmd: self._execute_command(c["command"]))
    
    def _on_up(self, event):
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self._update_results()
    
    def _on_down(self, event):
        """Move selection down."""
        if self.selected_index < len(self.filtered_commands) - 1:
            self.selected_index += 1
            self._update_results()
    
    def _on_select(self, event):
        """Select current item."""
        if self.filtered_commands:
            cmd = self.filtered_commands[self.selected_index]
            self._execute_command(cmd["command"])
        else:
            # Execute raw input
            self._execute_command(self.search_input.get())
    
    def _execute_command(self, command: str):
        """Execute the command."""
        self.hide()
        if self.on_command:
            self.on_command(command)
    
    def _on_escape(self, event):
        """Close launcher."""
        self.hide()
    
    def show(self):
        """Show the launcher."""
        self.root.deiconify()
        self.search_input.delete(0, "end")
        self.search_input.focus()
        self.filtered_commands = self.commands.copy()
        self.selected_index = 0
        self._update_results()
        self.is_visible = True
    
    def hide(self):
        """Hide the launcher."""
        self.root.withdraw()
        self.is_visible = False
    
    def toggle(self):
        """Toggle visibility."""
        if self.is_visible:
            self.hide()
        else:
            self.show()


class ClipboardHistoryPanel:
    """
    Panel showing clipboard history with search and quick actions.
    """
    
    def __init__(
        self,
        parent,
        colors: dict,
        on_paste: Optional[Callable[[str], None]] = None
    ):
        if not CTK_AVAILABLE:
            return
        
        self.parent = parent
        self.colors = colors
        self.on_paste = on_paste
        self.history: List[Dict[str, Any]] = []
        self.max_history = 50
        
        self._create_panel()
    
    def _create_panel(self):
        """Create the clipboard history panel."""
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors["bg"],
            corner_radius=12
        )
        
        # Header
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=12)
        
        ctk.CTkLabel(
            header,
            text="📋 Clipboard History",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            header,
            text="Clear",
            width=60,
            height=24,
            corner_radius=4,
            fg_color="transparent",
            hover_color=self.colors["bg_secondary"],
            command=self.clear_history
        ).pack(side="right")
        
        # Search
        self.search_entry = ctk.CTkEntry(
            self.frame,
            placeholder_text="Search clipboard...",
            height=32,
            corner_radius=6
        )
        self.search_entry.pack(fill="x", padx=12, pady=(0, 8))
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        # History list
        self.list_frame = ctk.CTkScrollableFrame(
            self.frame,
            fg_color="transparent",
            height=300
        )
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    
    def add_item(self, text: str, item_type: str = "text"):
        """Add item to history."""
        item = {
            "text": text,
            "type": item_type,
            "timestamp": datetime.now(),
            "id": len(self.history)
        }
        self.history.insert(0, item)
        self.history = self.history[:self.max_history]
        self._update_list()
    
    def _on_search(self, event):
        """Handle search."""
        self._update_list()
    
    def _update_list(self):
        """Update the history list."""
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        query = self.search_entry.get().lower() if hasattr(self, 'search_entry') else ""
        
        for item in self.history:
            if query and query not in item["text"].lower():
                continue
            
            item_frame = ctk.CTkFrame(
                self.list_frame,
                fg_color=self.colors["bg_secondary"],
                corner_radius=6
            )
            item_frame.pack(fill="x", pady=2)
            
            inner = ctk.CTkFrame(item_frame, fg_color="transparent")
            inner.pack(fill="x", padx=8, pady=6)
            
            # Preview text
            preview = item["text"][:100] + "..." if len(item["text"]) > 100 else item["text"]
            preview = preview.replace("\n", " ")
            
            ctk.CTkLabel(
                inner,
                text=preview,
                font=ctk.CTkFont(size=12),
                anchor="w",
                wraplength=250
            ).pack(anchor="w")
            
            # Time
            time_str = item["timestamp"].strftime("%H:%M")
            ctk.CTkLabel(
                inner,
                text=time_str,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_muted"]
            ).pack(anchor="w")
            
            # Paste button
            ctk.CTkButton(
                inner,
                text="Paste",
                width=50,
                height=22,
                corner_radius=4,
                font=ctk.CTkFont(size=10),
                command=lambda t=item["text"]: self._paste(t)
            ).pack(side="right")
    
    def _paste(self, text: str):
        """Paste text."""
        if self.on_paste:
            self.on_paste(text)
    
    def clear_history(self):
        """Clear clipboard history."""
        self.history.clear()
        self._update_list()
    
    def pack(self, **kwargs):
        """Pack the panel."""
        self.frame.pack(**kwargs)


def launch_floating_widget(on_command=None, on_expand=None):
    """Launch the floating widget."""
    widget = FloatingWidget(on_command=on_command, on_expand=on_expand)
    widget.run()
    return widget
