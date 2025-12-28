"""
Smooth Command Palette for SysAgent.
Fast, fuzzy-searchable command launcher.
"""

from dataclasses import dataclass
from typing import List, Optional, Callable
import re

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


@dataclass
class Command:
    """Command definition."""
    id: str
    label: str
    description: str
    icon: str
    category: str
    action: str
    shortcut: str = ""


# Default commands
COMMANDS = [
    # System
    Command("status", "System Status", "Show current system status", "📊", "System", "Show system status"),
    Command("health", "Health Check", "Run comprehensive health check", "🏥", "System", "Run health check"),
    Command("cpu", "CPU Usage", "Monitor CPU usage", "🔥", "System", "Show CPU usage"),
    Command("memory", "Memory Usage", "Check memory usage", "💾", "System", "Show memory usage"),
    Command("disk", "Disk Space", "Check disk space", "💿", "System", "Check disk space"),
    Command("processes", "Top Processes", "Show running processes", "📋", "System", "Show top processes"),
    
    # Files
    Command("files", "Browse Files", "Browse files in current directory", "📁", "Files", "List files"),
    Command("search", "Search Files", "Search for files by name", "🔍", "Files", "Search for files"),
    Command("large", "Large Files", "Find large files", "📦", "Files", "Find large files over 100MB"),
    
    # Network
    Command("network", "Network Status", "Check network connections", "🌐", "Network", "Show network status"),
    Command("ports", "Open Ports", "List open ports", "🔌", "Network", "Show open ports"),
    Command("ping", "Ping Test", "Test network connectivity", "📡", "Network", "Ping google.com"),
    
    # Automation
    Command("workflow", "Workflows", "List saved workflows", "⚡", "Automation", "List workflows"),
    Command("schedule", "Scheduled Tasks", "View scheduled tasks", "📅", "Automation", "Show scheduled tasks"),
    
    # Security
    Command("security", "Security Scan", "Run security analysis", "🔒", "Security", "Run security scan"),
    Command("updates", "System Updates", "Check for updates", "🔄", "Security", "Check for system updates"),
]


# Colors
COLORS = {
    "bg": "#0a0a0f",
    "bg_secondary": "#12121a",
    "bg_hover": "#1a1a24",
    "border": "#2a2a35",
    "border_focus": "#4a6cf7",
    "text": "#ffffff",
    "text_secondary": "#9898a8",
    "text_muted": "#5a5a6a",
    "accent": "#4a6cf7",
}


class CommandPalette:
    """Smooth command palette."""
    
    def __init__(self, parent, on_command: Callable[[str], None], commands: List[Command] = None):
        self.parent = parent
        self.on_command = on_command
        self.commands = commands or COMMANDS
        self.popup = None
        self.selected_idx = 0
        self.filtered: List[Command] = []
    
    def open(self):
        """Open palette."""
        if not CTK_AVAILABLE:
            return
        
        if self.popup:
            self.close()
        
        # Create popup
        self.popup = ctk.CTkToplevel(self.parent)
        self.popup.overrideredirect(True)
        self.popup.configure(fg_color=COLORS["bg"])
        
        # Position at center top
        pw, ph = 500, 400
        x = self.parent.winfo_x() + (self.parent.winfo_width() - pw) // 2
        y = self.parent.winfo_y() + 100
        self.popup.geometry(f"{pw}x{ph}+{x}+{y}")
        
        # Shadow effect
        self.popup.attributes("-alpha", 0.98)
        
        # Main container
        container = ctk.CTkFrame(
            self.popup,
            fg_color=COLORS["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        container.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Search bar
        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", padx=12, pady=12)
        
        ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=(8, 0))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search commands...",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=0,
            text_color=COLORS["text"],
            height=36
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=8)
        
        # Separator
        sep = ctk.CTkFrame(container, fg_color=COLORS["border"], height=1)
        sep.pack(fill="x")
        
        # Results
        self.results_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent"
        )
        self.results_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Hint
        hint = ctk.CTkFrame(container, fg_color="transparent")
        hint.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            hint,
            text="↑↓ Navigate  ↵ Select  Esc Close",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        ).pack(side="left")
        
        # Bindings
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.search_entry.bind("<Up>", self._on_up)
        self.search_entry.bind("<Down>", self._on_down)
        self.search_entry.bind("<Return>", self._on_select)
        self.search_entry.bind("<Escape>", lambda e: self.close())
        self.popup.bind("<FocusOut>", self._on_focus_out)
        
        # Focus
        self.search_entry.focus_set()
        
        # Initial render
        self._filter("")
    
    def close(self):
        """Close palette."""
        if self.popup:
            try:
                self.popup.destroy()
            except Exception:
                pass
            self.popup = None
    
    def _on_focus_out(self, event):
        """Close on focus out."""
        try:
            focus = self.popup.focus_get()
            if focus is None or focus.winfo_toplevel() != self.popup:
                self.popup.after(100, self.close)
        except Exception:
            pass
    
    def _on_search(self, event):
        """Filter on search."""
        query = self.search_entry.get().strip()
        self._filter(query)
    
    def _filter(self, query: str):
        """Filter commands."""
        if not query:
            self.filtered = self.commands[:]
        else:
            scored = []
            q = query.lower()
            for cmd in self.commands:
                score = self._score(cmd, q)
                if score > 0:
                    scored.append((score, cmd))
            scored.sort(reverse=True, key=lambda x: x[0])
            self.filtered = [c for _, c in scored]
        
        self.selected_idx = 0
        self._render()
    
    def _score(self, cmd: Command, query: str) -> int:
        """Score command match."""
        score = 0
        
        # Exact match
        if query in cmd.label.lower():
            score += 100
        if query in cmd.description.lower():
            score += 50
        if query in cmd.category.lower():
            score += 30
        if query in cmd.action.lower():
            score += 20
        
        # Fuzzy
        if self._fuzzy_match(query, cmd.label.lower()):
            score += 10
        
        return score
    
    def _fuzzy_match(self, query: str, text: str) -> bool:
        """Check fuzzy match."""
        qi = 0
        for c in text:
            if qi < len(query) and c == query[qi]:
                qi += 1
        return qi == len(query)
    
    def _render(self):
        """Render results."""
        # Clear
        for w in self.results_frame.winfo_children():
            w.destroy()
        
        if not self.filtered:
            ctk.CTkLabel(
                self.results_frame,
                text="No commands found",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_muted"]
            ).pack(pady=20)
            return
        
        # Group by category
        categories = {}
        for cmd in self.filtered:
            cat = cmd.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(cmd)
        
        idx = 0
        for cat, cmds in categories.items():
            # Category header
            ctk.CTkLabel(
                self.results_frame,
                text=cat.upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=COLORS["text_muted"]
            ).pack(anchor="w", padx=12, pady=(8, 4))
            
            for cmd in cmds:
                self._render_item(cmd, idx)
                idx += 1
    
    def _render_item(self, cmd: Command, idx: int):
        """Render command item."""
        selected = idx == self.selected_idx
        
        bg = COLORS["bg_hover"] if selected else "transparent"
        
        item = ctk.CTkFrame(
            self.results_frame,
            fg_color=bg,
            corner_radius=8,
            cursor="hand2"
        )
        item.pack(fill="x", padx=4, pady=1)
        
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)
        
        # Icon
        ctk.CTkLabel(
            inner,
            text=cmd.icon,
            font=ctk.CTkFont(size=18),
            width=28
        ).pack(side="left")
        
        # Text
        text_frame = ctk.CTkFrame(inner, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True, padx=8)
        
        ctk.CTkLabel(
            text_frame,
            text=cmd.label,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
            text=cmd.description,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        
        # Shortcut
        if cmd.shortcut:
            ctk.CTkLabel(
                inner,
                text=cmd.shortcut,
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_muted"]
            ).pack(side="right", padx=4)
        
        # Click binding
        item.bind("<Button-1>", lambda e, i=idx: self._select(i))
        for child in item.winfo_children():
            child.bind("<Button-1>", lambda e, i=idx: self._select(i))
            for grandchild in child.winfo_children():
                grandchild.bind("<Button-1>", lambda e, i=idx: self._select(i))
    
    def _on_up(self, event):
        """Move selection up."""
        if self.selected_idx > 0:
            self.selected_idx -= 1
            self._render()
        return "break"
    
    def _on_down(self, event):
        """Move selection down."""
        if self.selected_idx < len(self.filtered) - 1:
            self.selected_idx += 1
            self._render()
        return "break"
    
    def _on_select(self, event):
        """Select current."""
        if self.filtered and 0 <= self.selected_idx < len(self.filtered):
            cmd = self.filtered[self.selected_idx]
            self.close()
            self.on_command(cmd.action)
    
    def _select(self, idx: int):
        """Select by index."""
        if 0 <= idx < len(self.filtered):
            cmd = self.filtered[idx]
            self.close()
            self.on_command(cmd.action)
