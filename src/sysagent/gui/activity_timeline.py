"""
Activity Timeline for SysAgent - Visual timeline of agent activities.
Shows what the agent has done, when, and allows exploration of history.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class ActivityCategory(Enum):
    COMMAND = "command"
    TOOL = "tool"
    FILE = "file"
    SYSTEM = "system"
    NETWORK = "network"
    ERROR = "error"
    USER_INPUT = "user_input"


@dataclass
class TimelineEntry:
    """An entry in the activity timeline."""
    id: str
    timestamp: datetime
    category: ActivityCategory
    action: str
    details: str = ""
    status: str = "success"  # success, error, pending
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


CATEGORY_ICONS = {
    ActivityCategory.COMMAND: "💬",
    ActivityCategory.TOOL: "🔧",
    ActivityCategory.FILE: "📁",
    ActivityCategory.SYSTEM: "💻",
    ActivityCategory.NETWORK: "🌐",
    ActivityCategory.ERROR: "❌",
    ActivityCategory.USER_INPUT: "👤",
}

CATEGORY_COLORS = {
    ActivityCategory.COMMAND: "#3b82f6",
    ActivityCategory.TOOL: "#8b5cf6",
    ActivityCategory.FILE: "#22c55e",
    ActivityCategory.SYSTEM: "#f59e0b",
    ActivityCategory.NETWORK: "#06b6d4",
    ActivityCategory.ERROR: "#ef4444",
    ActivityCategory.USER_INPUT: "#64748b",
}


class ActivityTimeline:
    """
    Manages the activity timeline data.
    """
    
    def __init__(self, max_entries: int = 500):
        self.entries: List[TimelineEntry] = []
        self.max_entries = max_entries
        self._entry_counter = 0
    
    def add(
        self,
        category: ActivityCategory,
        action: str,
        details: str = "",
        status: str = "success",
        duration_ms: int = 0,
        metadata: Dict[str, Any] = None
    ) -> TimelineEntry:
        """Add a new timeline entry."""
        self._entry_counter += 1
        
        entry = TimelineEntry(
            id=f"entry_{self._entry_counter}",
            timestamp=datetime.now(),
            category=category,
            action=action,
            details=details,
            status=status,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        
        self.entries.insert(0, entry)
        
        # Trim if exceeding max
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[:self.max_entries]
        
        return entry
    
    def get_recent(self, limit: int = 50) -> List[TimelineEntry]:
        """Get recent entries."""
        return self.entries[:limit]
    
    def get_by_category(self, category: ActivityCategory) -> List[TimelineEntry]:
        """Get entries by category."""
        return [e for e in self.entries if e.category == category]
    
    def get_by_date(self, date: datetime) -> List[TimelineEntry]:
        """Get entries from a specific date."""
        return [
            e for e in self.entries
            if e.timestamp.date() == date.date()
        ]
    
    def get_today(self) -> List[TimelineEntry]:
        """Get today's entries."""
        return self.get_by_date(datetime.now())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get timeline statistics."""
        today = self.get_today()
        
        by_category = {}
        for cat in ActivityCategory:
            by_category[cat.value] = len([e for e in today if e.category == cat])
        
        errors = len([e for e in today if e.status == "error"])
        success_rate = ((len(today) - errors) / len(today) * 100) if today else 100
        
        return {
            "total_today": len(today),
            "by_category": by_category,
            "errors": errors,
            "success_rate": round(success_rate, 1),
            "total_all_time": len(self.entries)
        }
    
    def search(self, query: str) -> List[TimelineEntry]:
        """Search entries by action or details."""
        query = query.lower()
        return [
            e for e in self.entries
            if query in e.action.lower() or query in e.details.lower()
        ]
    
    def clear(self):
        """Clear all entries."""
        self.entries = []


class TimelinePanel:
    """
    UI Panel for displaying the activity timeline.
    """
    
    def __init__(
        self,
        parent,
        colors: dict,
        timeline: ActivityTimeline,
        on_entry_click: Optional[Callable[[TimelineEntry], None]] = None
    ):
        if not CTK_AVAILABLE:
            return
        
        self.parent = parent
        self.colors = colors
        self.timeline = timeline
        self.on_entry_click = on_entry_click
        self.selected_category = None
        
        self._create_panel()
    
    def _create_panel(self):
        """Create the timeline panel."""
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors["bg"],
            corner_radius=12
        )
        
        # Header
        header = ctk.CTkFrame(self.frame, fg_color=self.colors["bg_secondary"])
        header.pack(fill="x")
        
        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=12, pady=10)
        
        ctk.CTkLabel(
            header_inner,
            text="📊 Activity Timeline",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        # Search
        self.search_entry = ctk.CTkEntry(
            header_inner,
            placeholder_text="Search...",
            width=150,
            height=28,
            corner_radius=6
        )
        self.search_entry.pack(side="right", padx=8)
        self.search_entry.bind("<Return>", self._on_search)
        
        # Category filter
        filter_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkButton(
            filter_frame,
            text="All",
            width=50,
            height=24,
            corner_radius=4,
            font=ctk.CTkFont(size=10),
            fg_color=self.colors.get("accent", "#4a6cf7"),
            command=lambda: self._filter_category(None)
        ).pack(side="left", padx=2)
        
        for cat in [ActivityCategory.COMMAND, ActivityCategory.TOOL, ActivityCategory.FILE, ActivityCategory.ERROR]:
            ctk.CTkButton(
                filter_frame,
                text=CATEGORY_ICONS.get(cat, ""),
                width=32,
                height=24,
                corner_radius=4,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color=self.colors.get("bg_tertiary", "#1a1a24"),
                command=lambda c=cat: self._filter_category(c)
            ).pack(side="left", padx=2)
        
        # Stats bar
        self.stats_frame = ctk.CTkFrame(self.frame, fg_color=self.colors["bg_tertiary"], corner_radius=8)
        self.stats_frame.pack(fill="x", padx=12, pady=(0, 8))
        self._update_stats()
        
        # Timeline entries
        self.list_frame = ctk.CTkScrollableFrame(
            self.frame,
            fg_color="transparent",
            height=350
        )
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.refresh()
    
    def _update_stats(self):
        """Update the stats bar."""
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        stats = self.timeline.get_stats()
        
        inner = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(
            inner,
            text=f"Today: {stats['total_today']} activities",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")
        
        ctk.CTkLabel(
            inner,
            text=f"Success: {stats['success_rate']}%",
            font=ctk.CTkFont(size=11),
            text_color=self.colors.get("success", "#22c55e") if stats['success_rate'] > 90 else self.colors.get("warning", "#f59e0b")
        ).pack(side="right")
    
    def refresh(self):
        """Refresh the timeline display."""
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        entries = self.timeline.get_recent(50)
        
        if self.selected_category:
            entries = [e for e in entries if e.category == self.selected_category]
        
        if not entries:
            ctk.CTkLabel(
                self.list_frame,
                text="No activities yet",
                text_color=self.colors.get("text_muted", "#5a5a6a")
            ).pack(pady=20)
            return
        
        # Group by time periods
        now = datetime.now()
        today = now.date()
        yesterday = (now - timedelta(days=1)).date()
        
        current_group = None
        
        for entry in entries:
            entry_date = entry.timestamp.date()
            
            # Add group header
            if entry_date == today and current_group != "today":
                current_group = "today"
                self._add_group_header("Today")
            elif entry_date == yesterday and current_group != "yesterday":
                current_group = "yesterday"
                self._add_group_header("Yesterday")
            elif entry_date < yesterday and current_group != "earlier":
                current_group = "earlier"
                self._add_group_header("Earlier")
            
            self._add_entry_card(entry)
        
        self._update_stats()
    
    def _add_group_header(self, text: str):
        """Add a group header."""
        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(8, 4))
        
        ctk.CTkLabel(
            header,
            text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors.get("text_muted", "#5a5a6a")
        ).pack(side="left")
        
        ctk.CTkFrame(
            header,
            height=1,
            fg_color=self.colors.get("border", "#2a2a35")
        ).pack(side="left", fill="x", expand=True, padx=8)
    
    def _add_entry_card(self, entry: TimelineEntry):
        """Add a timeline entry card."""
        card = ctk.CTkFrame(
            self.list_frame,
            fg_color=self.colors.get("bg_secondary", "#12121a"),
            corner_radius=8
        )
        card.pack(fill="x", pady=2)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)
        
        # Time indicator
        time_str = entry.timestamp.strftime("%H:%M")
        ctk.CTkLabel(
            inner,
            text=time_str,
            font=ctk.CTkFont(size=10),
            text_color=self.colors.get("text_muted", "#5a5a6a"),
            width=40
        ).pack(side="left")
        
        # Category icon with color
        icon = CATEGORY_ICONS.get(entry.category, "📌")
        color = CATEGORY_COLORS.get(entry.category, "#3b82f6")
        
        icon_label = ctk.CTkLabel(
            inner,
            text=icon,
            font=ctk.CTkFont(size=14),
            fg_color=color,
            corner_radius=4,
            width=28,
            height=28
        )
        icon_label.pack(side="left", padx=8)
        
        # Content
        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            content,
            text=entry.action[:50] + "..." if len(entry.action) > 50 else entry.action,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")
        
        if entry.details:
            ctk.CTkLabel(
                content,
                text=entry.details[:60] + "..." if len(entry.details) > 60 else entry.details,
                font=ctk.CTkFont(size=10),
                text_color=self.colors.get("text_muted", "#5a5a6a")
            ).pack(anchor="w")
        
        # Status indicator
        status_colors = {
            "success": self.colors.get("success", "#22c55e"),
            "error": self.colors.get("error", "#ef4444"),
            "pending": self.colors.get("warning", "#f59e0b")
        }
        
        status_indicator = ctk.CTkFrame(
            inner,
            width=8,
            height=8,
            fg_color=status_colors.get(entry.status, "#64748b"),
            corner_radius=4
        )
        status_indicator.pack(side="right", padx=4)
        
        # Duration if available
        if entry.duration_ms > 0:
            duration_str = f"{entry.duration_ms}ms" if entry.duration_ms < 1000 else f"{entry.duration_ms/1000:.1f}s"
            ctk.CTkLabel(
                inner,
                text=duration_str,
                font=ctk.CTkFont(size=9),
                text_color=self.colors.get("text_muted", "#5a5a6a")
            ).pack(side="right", padx=4)
        
        # Make clickable
        if self.on_entry_click:
            card.bind("<Button-1>", lambda e, entry=entry: self.on_entry_click(entry))
    
    def _filter_category(self, category: Optional[ActivityCategory]):
        """Filter by category."""
        self.selected_category = category
        self.refresh()
    
    def _on_search(self, event):
        """Handle search."""
        query = self.search_entry.get().strip()
        
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        if query:
            entries = self.timeline.search(query)
        else:
            entries = self.timeline.get_recent(50)
        
        for entry in entries:
            self._add_entry_card(entry)
    
    def pack(self, **kwargs):
        """Pack the panel."""
        self.frame.pack(**kwargs)


# Singleton timeline
_activity_timeline: Optional[ActivityTimeline] = None


def get_activity_timeline() -> ActivityTimeline:
    """Get or create the activity timeline instance."""
    global _activity_timeline
    if _activity_timeline is None:
        _activity_timeline = ActivityTimeline()
    return _activity_timeline


def log_activity(
    category: ActivityCategory,
    action: str,
    details: str = "",
    status: str = "success"
) -> TimelineEntry:
    """Convenience function to log an activity."""
    return get_activity_timeline().add(category, action, details, status)
