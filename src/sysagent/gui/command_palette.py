"""
Command Palette for SysAgent - Cursor AI-style quick command search.
Press Ctrl+K / Cmd+K to open.
"""

import tkinter as tk
from typing import Optional, Callable, List, Dict
from dataclasses import dataclass

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


@dataclass
class Command:
    """Represents a command."""
    id: str
    label: str
    description: str
    icon: str
    category: str
    action: str
    shortcut: str = ""


# Default commands organized by category
DEFAULT_COMMANDS = [
    # System
    Command("sys_status", "System Status", "Show overall system status", "📊", "System", "Show system status"),
    Command("sys_health", "Health Check", "Run full system health check", "🏥", "System", "Run system health check"),
    Command("sys_cpu", "CPU Usage", "Show CPU usage details", "💻", "System", "Show CPU usage"),
    Command("sys_memory", "Memory Usage", "Show memory usage", "🧠", "System", "Show memory usage"),
    Command("sys_disk", "Disk Space", "Check disk space", "💾", "System", "Check disk space"),
    Command("sys_processes", "List Processes", "Show running processes", "📋", "System", "List running processes"),
    Command("sys_insights", "Quick Insights", "Get AI-powered insights", "⚡", "System", "Give me quick insights"),
    
    # Files
    Command("file_search", "Search Files", "Search for files by name", "🔍", "Files", "Search for files named "),
    Command("file_large", "Find Large Files", "Find large files", "📦", "Files", "Find large files"),
    Command("file_recent", "Recent Files", "Show recently modified files", "🕐", "Files", "Show recent files"),
    Command("file_cleanup", "Clean Temp Files", "Clean temporary files", "🧹", "Files", "Clean temp files"),
    Command("file_organize", "Organize Downloads", "Organize downloads folder", "📁", "Files", "Organize my downloads"),
    
    # Network
    Command("net_status", "Network Status", "Check network connections", "🌐", "Network", "Show network status"),
    Command("net_ping", "Ping Test", "Test internet connectivity", "📡", "Network", "Ping google.com"),
    Command("net_ports", "Open Ports", "Show open ports", "🚪", "Network", "Show open ports"),
    
    # Git
    Command("git_status", "Git Status", "Show git repository status", "📂", "Git", "Git status"),
    Command("git_log", "Git Log", "Show recent commits", "📜", "Git", "Show git log"),
    Command("git_diff", "Git Diff", "Show uncommitted changes", "📝", "Git", "Git diff"),
    
    # Workflows
    Command("wf_list", "List Workflows", "Show all workflows", "📋", "Workflows", "List all workflows"),
    Command("wf_morning", "Morning Routine", "Run morning routine", "🌅", "Workflows", "Run morning routine workflow"),
    Command("wf_dev", "Dev Setup", "Setup development environment", "💻", "Workflows", "Run dev setup workflow"),
    Command("wf_maintenance", "System Maintenance", "Run maintenance tasks", "🔧", "Workflows", "Run system maintenance workflow"),
    
    # Tools
    Command("tool_terminal", "Open Terminal", "Launch terminal view", "🖥️", "Tools", "open_terminal"),
    Command("tool_browser", "Open Browser", "Open web browser", "🌍", "Tools", "Open browser"),
    Command("tool_settings", "Settings", "Open settings", "⚙️", "Tools", "open_settings"),
    
    # Security
    Command("sec_scan", "Security Scan", "Run security scan", "🔒", "Security", "Run security scan"),
    Command("sec_ports", "Port Scan", "Scan for open ports", "🚪", "Security", "Scan for open ports"),
]


class CommandPalette:
    """
    Cursor AI-style command palette.
    Fuzzy search across all commands with keyboard navigation.
    """
    
    THEME = {
        "bg": "#0d1117",
        "bg_hover": "#161b22",
        "bg_selected": "#21262d",
        "border": "#30363d",
        "text": "#e6edf3",
        "text_muted": "#8b949e",
        "accent": "#58a6ff",
    }
    
    def __init__(self, parent, on_command: Optional[Callable[[str], None]] = None):
        self.parent = parent
        self.on_command = on_command
        self.commands = DEFAULT_COMMANDS.copy()
        self.filtered_commands: List[Command] = []
        self.selected_index = 0
        self.is_open = False
        self.window = None
    
    def open(self):
        """Open the command palette."""
        if self.is_open:
            self.close()
            return
        
        if not CTK_AVAILABLE:
            return
        
        self.is_open = True
        
        # Create overlay window
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("")
        self.window.overrideredirect(True)
        
        # Position in center of parent
        width, height = 600, 450
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - width) // 2
        y = self.parent.winfo_rooty() + 80
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Main frame with shadow effect
        self.main_frame = ctk.CTkFrame(
            self.window,
            fg_color=self.THEME["bg"],
            corner_radius=12,
            border_width=1,
            border_color=self.THEME["border"]
        )
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Search input
        self.search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=16, pady=(16, 8))
        
        ctk.CTkLabel(
            self.search_frame,
            text="🔍",
            font=ctk.CTkFont(size=16),
            text_color=self.THEME["text_muted"]
        ).pack(side="left", padx=(0, 8))
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Search commands...",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=0,
            text_color=self.THEME["text"],
            height=36
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.focus_set()
        
        # Separator
        ctk.CTkFrame(
            self.main_frame,
            fg_color=self.THEME["border"],
            height=1
        ).pack(fill="x", padx=16, pady=8)
        
        # Results area
        self.results_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="transparent"
        )
        self.results_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        # Bindings
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.search_entry.bind("<Return>", self._on_select)
        self.search_entry.bind("<Up>", self._on_up)
        self.search_entry.bind("<Down>", self._on_down)
        self.search_entry.bind("<Escape>", self._on_escape)
        self.window.bind("<FocusOut>", self._on_focus_out)
        
        # Show all commands initially
        self._filter_commands("")
        
        # Keep focus
        self.window.after(100, lambda: self.search_entry.focus_set())
    
    def close(self):
        """Close the command palette."""
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None
        self.is_open = False
    
    def _on_search(self, event):
        """Handle search input."""
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        
        query = self.search_entry.get()
        self._filter_commands(query)
    
    def _filter_commands(self, query: str):
        """Filter commands by query using fuzzy matching."""
        query_lower = query.lower().strip()
        
        if not query_lower:
            self.filtered_commands = self.commands.copy()
        else:
            # Score commands
            scored = []
            for cmd in self.commands:
                score = self._fuzzy_score(query_lower, cmd)
                if score > 0:
                    scored.append((cmd, score))
            
            # Sort by score descending
            scored.sort(key=lambda x: x[1], reverse=True)
            self.filtered_commands = [cmd for cmd, _ in scored[:15]]
        
        self.selected_index = 0
        self._render_results()
    
    def _fuzzy_score(self, query: str, cmd: Command) -> int:
        """Calculate fuzzy match score."""
        score = 0
        
        # Exact match in label
        label_lower = cmd.label.lower()
        if query == label_lower:
            score += 100
        elif query in label_lower:
            score += 50
        elif self._subsequence_match(query, label_lower):
            score += 30
        
        # Match in description
        desc_lower = cmd.description.lower()
        if query in desc_lower:
            score += 20
        
        # Match in category
        cat_lower = cmd.category.lower()
        if query in cat_lower:
            score += 10
        
        # Match in action
        action_lower = cmd.action.lower()
        if query in action_lower:
            score += 15
        
        return score
    
    def _subsequence_match(self, query: str, text: str) -> bool:
        """Check if query is a subsequence of text."""
        query_idx = 0
        for char in text:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1
        return query_idx == len(query)
    
    def _render_results(self):
        """Render filtered results."""
        # Clear existing
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not self.filtered_commands:
            ctk.CTkLabel(
                self.results_frame,
                text="No commands found",
                font=ctk.CTkFont(size=13),
                text_color=self.THEME["text_muted"]
            ).pack(pady=20)
            return
        
        current_category = None
        
        for i, cmd in enumerate(self.filtered_commands):
            # Category header
            if cmd.category != current_category:
                current_category = cmd.category
                ctk.CTkLabel(
                    self.results_frame,
                    text=current_category.upper(),
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=self.THEME["text_muted"]
                ).pack(anchor="w", padx=12, pady=(12 if i > 0 else 4, 4))
            
            # Command row
            is_selected = i == self.selected_index
            bg = self.THEME["bg_selected"] if is_selected else "transparent"
            
            row = ctk.CTkFrame(
                self.results_frame,
                fg_color=bg,
                corner_radius=6,
                height=44
            )
            row.pack(fill="x", padx=4, pady=1)
            row.pack_propagate(False)
            
            # Make clickable
            row.bind("<Button-1>", lambda e, idx=i: self._select_index(idx))
            row.bind("<Enter>", lambda e, idx=i, r=row: self._on_hover(idx, r))
            row.bind("<Leave>", lambda e, r=row: self._on_leave(r))
            
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12)
            inner.bind("<Button-1>", lambda e, idx=i: self._select_index(idx))
            
            # Icon
            icon_label = ctk.CTkLabel(
                inner,
                text=cmd.icon,
                font=ctk.CTkFont(size=16),
                width=28
            )
            icon_label.pack(side="left", pady=10)
            icon_label.bind("<Button-1>", lambda e, idx=i: self._select_index(idx))
            
            # Label and description
            text_frame = ctk.CTkFrame(inner, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True, padx=8)
            text_frame.bind("<Button-1>", lambda e, idx=i: self._select_index(idx))
            
            name_label = ctk.CTkLabel(
                text_frame,
                text=cmd.label,
                font=ctk.CTkFont(size=13),
                text_color=self.THEME["text"],
                anchor="w"
            )
            name_label.pack(anchor="w")
            name_label.bind("<Button-1>", lambda e, idx=i: self._select_index(idx))
            
            desc_label = ctk.CTkLabel(
                text_frame,
                text=cmd.description,
                font=ctk.CTkFont(size=11),
                text_color=self.THEME["text_muted"],
                anchor="w"
            )
            desc_label.pack(anchor="w")
            desc_label.bind("<Button-1>", lambda e, idx=i: self._select_index(idx))
            
            # Shortcut if any
            if cmd.shortcut:
                ctk.CTkLabel(
                    inner,
                    text=cmd.shortcut,
                    font=ctk.CTkFont(size=10),
                    text_color=self.THEME["text_muted"]
                ).pack(side="right")
    
    def _on_hover(self, index: int, row):
        """Handle mouse hover."""
        self.selected_index = index
        row.configure(fg_color=self.THEME["bg_hover"])
    
    def _on_leave(self, row):
        """Handle mouse leave."""
        row.configure(fg_color="transparent")
    
    def _on_up(self, event):
        """Navigate up."""
        if self.filtered_commands:
            self.selected_index = max(0, self.selected_index - 1)
            self._render_results()
        return "break"
    
    def _on_down(self, event):
        """Navigate down."""
        if self.filtered_commands:
            self.selected_index = min(len(self.filtered_commands) - 1, self.selected_index + 1)
            self._render_results()
        return "break"
    
    def _on_select(self, event):
        """Select current command."""
        self._select_index(self.selected_index)
        return "break"
    
    def _select_index(self, index: int):
        """Select command at index."""
        if 0 <= index < len(self.filtered_commands):
            cmd = self.filtered_commands[index]
            self.close()
            
            # Handle special actions
            if cmd.action.startswith("open_"):
                # Internal action
                pass
            elif self.on_command:
                self.on_command(cmd.action)
    
    def _on_escape(self, event):
        """Close on escape."""
        self.close()
        return "break"
    
    def _on_focus_out(self, event):
        """Close on focus out."""
        # Small delay to allow clicking on results
        if self.window:
            self.window.after(200, self._check_focus)
    
    def _check_focus(self):
        """Check if focus is still in palette."""
        try:
            focused = self.parent.focus_get()
            if focused and self.window:
                # Check if focused widget is a child of our window
                parent = focused
                while parent:
                    if parent == self.window:
                        return
                    parent = parent.master if hasattr(parent, 'master') else None
            self.close()
        except Exception:
            pass
    
    def add_command(self, command: Command):
        """Add a custom command."""
        self.commands.append(command)
    
    def remove_command(self, command_id: str):
        """Remove a command by ID."""
        self.commands = [c for c in self.commands if c.id != command_id]
