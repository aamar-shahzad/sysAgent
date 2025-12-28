"""
Command Palette for SysAgent - Quick fuzzy search and execution of commands.
"""

import tkinter as tk
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass

try:
    import customtkinter as ctk
except ImportError:
    ctk = None


@dataclass
class Command:
    """Represents a command in the palette."""
    name: str
    description: str
    action: str  # The actual command/query to execute
    category: str
    icon: str = "▶"
    keywords: List[str] = None
    
    def matches(self, query: str) -> bool:
        """Check if command matches search query."""
        query_lower = query.lower()
        
        # Check name
        if query_lower in self.name.lower():
            return True
        
        # Check description
        if query_lower in self.description.lower():
            return True
        
        # Check category
        if query_lower in self.category.lower():
            return True
        
        # Check keywords
        if self.keywords:
            for kw in self.keywords:
                if query_lower in kw.lower():
                    return True
        
        return False
    
    def score(self, query: str) -> int:
        """Score how well this matches (higher = better)."""
        query_lower = query.lower()
        score = 0
        
        # Exact name match = highest
        if query_lower == self.name.lower():
            score += 100
        elif self.name.lower().startswith(query_lower):
            score += 50
        elif query_lower in self.name.lower():
            score += 30
        
        # Description match
        if query_lower in self.description.lower():
            score += 10
        
        # Keyword match
        if self.keywords:
            for kw in self.keywords:
                if query_lower in kw.lower():
                    score += 20
        
        return score


class CommandPalette:
    """
    A quick command palette with fuzzy search.
    Press Ctrl+K or Cmd+K to open.
    """
    
    # Default commands
    DEFAULT_COMMANDS = [
        # System
        Command("System Status", "Show overall system status", "Show my system status", "system", "💻", ["status", "overview"]),
        Command("CPU Usage", "Show CPU usage details", "Show CPU usage", "system", "🔥", ["processor"]),
        Command("Memory Usage", "Show RAM usage details", "Show memory usage", "system", "💾", ["ram"]),
        Command("Disk Space", "Show disk space usage", "Show disk space", "system", "💿", ["storage"]),
        Command("Battery Status", "Show battery information", "Show battery status", "system", "🔋", ["power"]),
        Command("Health Check", "Run system health check", "Run a system health check", "system", "🏥", ["diagnose"]),
        
        # Processes
        Command("List Processes", "Show running processes", "List all running processes", "process", "📋", ["ps"]),
        Command("Kill Process", "Terminate a process", "Kill process named ", "process", "❌", ["terminate", "stop"]),
        Command("Find Resource Hogs", "Find processes using most resources", "Find resource-heavy processes", "process", "🔍", ["heavy", "slow"]),
        
        # Browser
        Command("Open Google", "Open Google in browser", "Open Google in browser", "browser", "🌐", ["search", "web"]),
        Command("Open YouTube", "Open YouTube", "Open YouTube in browser", "browser", "▶️", ["video"]),
        Command("Open GitHub", "Open GitHub", "Open GitHub in browser", "browser", "🐙", ["code", "repo"]),
        Command("Search Web", "Search the web", "Search the web for ", "browser", "🔍", ["google"]),
        
        # Files
        Command("Search Files", "Search for files", "Search for files named ", "files", "📁", ["find"]),
        Command("Recent Files", "Show recently modified files", "Show my recent files", "files", "📄", ["latest"]),
        Command("Open Downloads", "Open Downloads folder", "Open my Downloads folder", "files", "📥", ["download"]),
        Command("Open Documents", "Open Documents folder", "Open my Documents folder", "files", "📂", []),
        
        # Git
        Command("Git Status", "Show git status", "Show git status", "git", "📝", ["repo"]),
        Command("Git Commit", "Commit changes", "Commit my changes with message: ", "git", "✅", ["save"]),
        Command("Git Pull", "Pull latest changes", "Pull the latest changes", "git", "⬇️", ["fetch"]),
        Command("Git Push", "Push changes", "Push my changes", "git", "⬆️", ["upload"]),
        
        # Media
        Command("Volume Up", "Increase volume", "Increase the volume", "media", "🔊", ["louder"]),
        Command("Volume Down", "Decrease volume", "Decrease the volume", "media", "🔉", ["quieter"]),
        Command("Mute", "Mute audio", "Mute the audio", "media", "🔇", ["silence"]),
        Command("Play/Pause", "Toggle media playback", "Play or pause the media", "media", "⏯️", ["music"]),
        
        # Notifications
        Command("Send Notification", "Send a notification", "Send a notification saying: ", "notify", "🔔", ["alert"]),
        Command("Set Reminder", "Create a reminder", "Remind me to ", "notify", "⏰", ["timer"]),
        
        # Workflows
        Command("Run Workflow", "Run a saved workflow", "Run the workflow named ", "workflow", "▶️", ["automation"]),
        Command("List Workflows", "Show all workflows", "List all my workflows", "workflow", "📋", []),
        Command("Morning Routine", "Run morning routine", "Run my morning routine", "workflow", "☀️", ["start day"]),
        
        # Packages
        Command("Install Package", "Install a package", "Install the package ", "packages", "📦", ["add"]),
        Command("Update Packages", "Update all packages", "Update all my packages", "packages", "⬆️", ["upgrade"]),
        Command("Search Packages", "Search for a package", "Search for a package named ", "packages", "🔍", []),
        
        # Windows
        Command("List Windows", "Show open windows", "List all open windows", "windows", "🪟", []),
        Command("Tile Windows", "Tile windows left/right", "Tile my windows", "windows", "⬜", ["arrange"]),
        Command("Minimize All", "Minimize all windows", "Minimize all windows", "windows", "⬇️", ["hide"]),
        
        # Quick Actions
        Command("Lock Screen", "Lock the computer", "Lock my screen", "quick", "🔒", ["security"]),
        Command("Take Screenshot", "Take a screenshot", "Take a screenshot", "quick", "📸", ["capture"]),
        Command("Empty Trash", "Empty the trash", "Empty my trash", "quick", "🗑️", ["delete"]),
        
        # Notes & Docs
        Command("Create Note", "Create a new note", "Create a note about ", "docs", "📝", ["write"]),
        Command("Create Spreadsheet", "Create new spreadsheet", "Create a new spreadsheet", "docs", "📊", ["excel"]),
        Command("Search Notes", "Search my notes", "Search my notes for ", "docs", "🔍", []),
        
        # Email
        Command("Compose Email", "Write a new email", "Compose an email to ", "email", "✉️", ["mail"]),
        
        # Settings
        Command("Preferences", "Open preferences", "Show my preferences", "settings", "⚙️", ["config"]),
        Command("Show History", "Show command history", "Show my command history", "settings", "📜", []),
    ]
    
    def __init__(self, parent, on_command: Callable[[str], None]):
        """
        Initialize command palette.
        
        Args:
            parent: Parent window
            on_command: Callback when command is selected (receives action string)
        """
        self.parent = parent
        self.on_command = on_command
        self.commands = self.DEFAULT_COMMANDS.copy()
        self.filtered_commands: List[Command] = []
        self.selected_index = 0
        self.window: Optional[tk.Toplevel] = None
        self.is_open = False
        
    def add_command(self, command: Command):
        """Add a custom command."""
        self.commands.append(command)
        
    def add_recent_command(self, name: str, action: str):
        """Add a recent/frequent command to the top."""
        cmd = Command(
            name=name,
            description="Recent command",
            action=action,
            category="recent",
            icon="🕐"
        )
        # Add to front, remove duplicates
        self.commands = [c for c in self.commands if c.action != action]
        self.commands.insert(0, cmd)
        # Keep max 50 recent
        if len([c for c in self.commands if c.category == "recent"]) > 10:
            self.commands = [c for c in self.commands if c.category != "recent" or self.commands.index(c) < 10]
    
    def open(self):
        """Open the command palette."""
        if self.is_open:
            self.close()
            return
        
        self.is_open = True
        self.selected_index = 0
        
        # Create popup window
        if ctk:
            self.window = ctk.CTkToplevel(self.parent)
        else:
            self.window = tk.Toplevel(self.parent)
        
        self.window.title("")
        self.window.overrideredirect(True)  # No title bar
        
        # Position in center of parent
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_w = self.parent.winfo_width()
        parent_h = self.parent.winfo_height()
        
        width = 600
        height = 400
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 3
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.configure(bg="#1e1e1e")
        
        # Make it stay on top
        self.window.attributes("-topmost", True)
        
        # Focus handling
        self.window.bind("<FocusOut>", lambda e: self._on_focus_out(e))
        self.window.bind("<Escape>", lambda e: self.close())
        
        # Main frame
        if ctk:
            main_frame = ctk.CTkFrame(self.window, fg_color="#1e1e1e", corner_radius=10)
        else:
            main_frame = tk.Frame(self.window, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Search entry
        if ctk:
            self.search_var = ctk.StringVar()
            self.search_entry = ctk.CTkEntry(
                main_frame,
                placeholder_text="Type a command...",
                textvariable=self.search_var,
                height=50,
                font=("SF Pro Display", 18),
                fg_color="#2d2d2d",
                border_color="#444",
                text_color="white"
            )
        else:
            self.search_var = tk.StringVar()
            self.search_entry = tk.Entry(
                main_frame,
                textvariable=self.search_var,
                font=("Helvetica", 18),
                bg="#2d2d2d",
                fg="white",
                insertbackground="white"
            )
        
        self.search_entry.pack(fill="x", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.search_entry.bind("<Return>", self._on_select)
        self.search_entry.bind("<Up>", self._on_up)
        self.search_entry.bind("<Down>", self._on_down)
        
        # Results frame with scrollable
        if ctk:
            self.results_frame = ctk.CTkScrollableFrame(
                main_frame,
                fg_color="#1e1e1e"
            )
        else:
            self.results_frame = tk.Frame(main_frame, bg="#1e1e1e")
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Initial display
        self._filter_commands("")
        self._display_results()
        
        # Focus search
        self.search_entry.focus_set()
    
    def close(self):
        """Close the command palette."""
        if self.window:
            self.window.destroy()
            self.window = None
        self.is_open = False
    
    def _on_focus_out(self, event):
        """Handle focus out."""
        # Small delay to check if focus moved to child
        if self.window:
            self.window.after(100, self._check_focus)
    
    def _check_focus(self):
        """Check if palette should close."""
        if self.window:
            try:
                focused = self.window.focus_get()
                if focused is None:
                    self.close()
            except:
                self.close()
    
    def _on_search(self, event):
        """Handle search input."""
        query = self.search_var.get()
        self._filter_commands(query)
        self.selected_index = 0
        self._display_results()
    
    def _filter_commands(self, query: str):
        """Filter commands by query."""
        if not query:
            self.filtered_commands = self.commands[:15]  # Show first 15
        else:
            # Score and sort
            matches = [(cmd, cmd.score(query)) for cmd in self.commands if cmd.matches(query)]
            matches.sort(key=lambda x: x[1], reverse=True)
            self.filtered_commands = [cmd for cmd, score in matches[:15]]
    
    def _display_results(self):
        """Display filtered results."""
        # Clear existing
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not self.filtered_commands:
            if ctk:
                label = ctk.CTkLabel(
                    self.results_frame,
                    text="No commands found",
                    text_color="#888",
                    font=("SF Pro Display", 14)
                )
            else:
                label = tk.Label(
                    self.results_frame,
                    text="No commands found",
                    fg="#888",
                    bg="#1e1e1e",
                    font=("Helvetica", 14)
                )
            label.pack(pady=20)
            return
        
        for i, cmd in enumerate(self.filtered_commands):
            is_selected = i == self.selected_index
            self._create_command_row(cmd, i, is_selected)
    
    def _create_command_row(self, cmd: Command, index: int, selected: bool):
        """Create a command row."""
        bg_color = "#3d3d3d" if selected else "#1e1e1e"
        
        if ctk:
            row = ctk.CTkFrame(
                self.results_frame,
                fg_color=bg_color,
                corner_radius=5,
                height=50
            )
        else:
            row = tk.Frame(self.results_frame, bg=bg_color, height=50)
        
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        
        # Bind click
        row.bind("<Button-1>", lambda e, i=index: self._select_index(i))
        
        # Icon and name
        if ctk:
            icon_label = ctk.CTkLabel(
                row,
                text=cmd.icon,
                font=("SF Pro Display", 18),
                width=40,
                fg_color="transparent",
                text_color="white"
            )
        else:
            icon_label = tk.Label(
                row,
                text=cmd.icon,
                font=("Helvetica", 18),
                width=3,
                bg=bg_color,
                fg="white"
            )
        icon_label.pack(side="left", padx=(10, 5))
        icon_label.bind("<Button-1>", lambda e, i=index: self._select_index(i))
        
        # Text frame
        if ctk:
            text_frame = ctk.CTkFrame(row, fg_color="transparent")
        else:
            text_frame = tk.Frame(row, bg=bg_color)
        text_frame.pack(side="left", fill="both", expand=True, padx=5)
        text_frame.bind("<Button-1>", lambda e, i=index: self._select_index(i))
        
        # Name
        if ctk:
            name_label = ctk.CTkLabel(
                text_frame,
                text=cmd.name,
                font=("SF Pro Display", 14, "bold"),
                text_color="white",
                anchor="w"
            )
        else:
            name_label = tk.Label(
                text_frame,
                text=cmd.name,
                font=("Helvetica", 14, "bold"),
                fg="white",
                bg=bg_color,
                anchor="w"
            )
        name_label.pack(side="top", fill="x")
        name_label.bind("<Button-1>", lambda e, i=index: self._select_index(i))
        
        # Description
        if ctk:
            desc_label = ctk.CTkLabel(
                text_frame,
                text=cmd.description,
                font=("SF Pro Display", 11),
                text_color="#888",
                anchor="w"
            )
        else:
            desc_label = tk.Label(
                text_frame,
                text=cmd.description,
                font=("Helvetica", 11),
                fg="#888",
                bg=bg_color,
                anchor="w"
            )
        desc_label.pack(side="top", fill="x")
        desc_label.bind("<Button-1>", lambda e, i=index: self._select_index(i))
        
        # Category badge
        if ctk:
            cat_label = ctk.CTkLabel(
                row,
                text=cmd.category,
                font=("SF Pro Display", 10),
                text_color="#666",
                fg_color="#2d2d2d",
                corner_radius=5,
                width=60
            )
        else:
            cat_label = tk.Label(
                row,
                text=cmd.category,
                font=("Helvetica", 10),
                fg="#666",
                bg="#2d2d2d"
            )
        cat_label.pack(side="right", padx=10)
        cat_label.bind("<Button-1>", lambda e, i=index: self._select_index(i))
    
    def _on_up(self, event):
        """Handle up arrow."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self._display_results()
        return "break"
    
    def _on_down(self, event):
        """Handle down arrow."""
        if self.selected_index < len(self.filtered_commands) - 1:
            self.selected_index += 1
            self._display_results()
        return "break"
    
    def _select_index(self, index: int):
        """Select command at index."""
        self.selected_index = index
        self._on_select(None)
    
    def _on_select(self, event):
        """Handle command selection."""
        if self.filtered_commands and 0 <= self.selected_index < len(self.filtered_commands):
            cmd = self.filtered_commands[self.selected_index]
            action = cmd.action
            
            # If action ends with space or colon, append search query
            if action.endswith(": ") or action.endswith(" "):
                query = self.search_var.get()
                # Remove matched command name from query to get extra input
                words = query.split()
                if len(words) > 1:
                    action += " ".join(words[1:])
            
            self.close()
            
            if self.on_command:
                self.on_command(action)
