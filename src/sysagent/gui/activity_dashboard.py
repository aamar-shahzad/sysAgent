"""
Activity Dashboard for SysAgent - Visual activity history and audit trail.
Professional analytics and monitoring interface.
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime, timedelta

# Handle missing tkinter gracefully
try:
    import tkinter as tk
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False
    tk = None

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None


class ActivityDashboard:
    """
    Activity dashboard showing:
    - Recent activity timeline
    - Tool usage statistics
    - Error log
    - Session history
    """
    
    COLORS = {
        "bg": "#0f172a",
        "card": "#1e293b",
        "text": "#f8fafc",
        "muted": "#94a3b8",
        "accent": "#3b82f6",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
    }
    
    def __init__(self, parent: Optional[Any] = None):
        self.parent = parent
        self.frame = None
        self.activity_list = None
        self.stats_labels = {}
    
    def create(self, parent: Optional[Any] = None) -> Any:
        """Create the dashboard widget."""
        if not CTK_AVAILABLE:
            return None
        
        parent = parent or self.parent
        
        self.frame = ctk.CTkFrame(parent, fg_color=self.COLORS["bg"])
        
        # Header
        header = ctk.CTkFrame(self.frame, fg_color="transparent", height=60)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="📊 Activity Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLORS["text"]
        ).pack(side="left")
        
        # Refresh button
        ctk.CTkButton(
            header,
            text="↻ Refresh",
            width=100,
            height=32,
            fg_color=self.COLORS["card"],
            command=self.refresh
        ).pack(side="right")
        
        # Time range selector
        self.time_range = ctk.CTkSegmentedButton(
            header,
            values=["Today", "Week", "Month"],
            command=lambda v: self.refresh()
        )
        self.time_range.set("Today")
        self.time_range.pack(side="right", padx=10)
        
        # Main content with scroll
        content = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Stats row
        stats_row = ctk.CTkFrame(content, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 15))
        
        self._create_stat_card(stats_row, "total", "Total Actions", "0", self.COLORS["accent"])
        self._create_stat_card(stats_row, "tools", "Tool Calls", "0", self.COLORS["success"])
        self._create_stat_card(stats_row, "errors", "Errors", "0", self.COLORS["error"])
        self._create_stat_card(stats_row, "sessions", "Sessions", "0", self.COLORS["warning"])
        
        # Two column layout
        columns = ctk.CTkFrame(content, fg_color="transparent")
        columns.pack(fill="both", expand=True)
        
        left_col = ctk.CTkFrame(columns, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_col = ctk.CTkFrame(columns, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Activity timeline
        self._create_activity_timeline(left_col)
        
        # Top tools
        self._create_top_tools(right_col)
        
        # Recent errors
        self._create_error_log(content)
        
        # Initial load
        self.refresh()
        
        return self.frame
    
    def _create_stat_card(self, parent, key: str, label: str, value: str, color: str):
        """Create a stat card."""
        card = ctk.CTkFrame(parent, fg_color=self.COLORS["card"], corner_radius=10)
        card.pack(side="left", fill="x", expand=True, padx=5)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=15)
        
        ctk.CTkLabel(
            inner,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS["muted"]
        ).pack(anchor="w")
        
        value_label = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=color
        )
        value_label.pack(anchor="w")
        
        self.stats_labels[key] = value_label
    
    def _create_activity_timeline(self, parent):
        """Create activity timeline."""
        card = ctk.CTkFrame(parent, fg_color=self.COLORS["card"], corner_radius=10)
        card.pack(fill="both", expand=True, pady=5)
        
        ctk.CTkLabel(
            card,
            text="Recent Activity",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COLORS["text"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.activity_list = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            height=250
        )
        self.activity_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def _create_top_tools(self, parent):
        """Create top tools chart."""
        card = ctk.CTkFrame(parent, fg_color=self.COLORS["card"], corner_radius=10)
        card.pack(fill="both", expand=True, pady=5)
        
        ctk.CTkLabel(
            card,
            text="Top Tools",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COLORS["text"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.tools_list = ctk.CTkFrame(card, fg_color="transparent")
        self.tools_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    def _create_error_log(self, parent):
        """Create error log section."""
        card = ctk.CTkFrame(parent, fg_color=self.COLORS["card"], corner_radius=10)
        card.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            card,
            text="Recent Errors",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COLORS["text"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.error_list = ctk.CTkFrame(card, fg_color="transparent")
        self.error_list.pack(fill="x", padx=15, pady=(0, 15))
    
    def refresh(self):
        """Refresh dashboard data."""
        try:
            from ..core.activity_tracker import get_activity_tracker, ActivityType
            
            tracker = get_activity_tracker()
            
            # Get time range
            range_val = self.time_range.get() if hasattr(self, 'time_range') else "Today"
            days = {"Today": 1, "Week": 7, "Month": 30}.get(range_val, 1)
            
            # Get statistics
            stats = tracker.get_statistics(days=days)
            
            # Update stat cards
            if "total" in self.stats_labels:
                self.stats_labels["total"].configure(text=str(stats.get("total_activities", 0)))
            if "tools" in self.stats_labels:
                self.stats_labels["tools"].configure(text=str(stats.get("by_type", {}).get("tool_call", 0)))
            if "errors" in self.stats_labels:
                self.stats_labels["errors"].configure(text=str(stats.get("error_count", 0)))
            if "sessions" in self.stats_labels:
                self.stats_labels["sessions"].configure(text=str(stats.get("by_type", {}).get("session", 0)))
            
            # Update activity timeline
            self._update_timeline(tracker.get_recent(limit=20))
            
            # Update top tools
            self._update_top_tools(stats.get("top_tools", []))
            
            # Update error log
            self._update_errors(tracker.get_recent(limit=5, activity_type=ActivityType.ERROR))
            
        except Exception as e:
            print(f"Could not refresh dashboard: {e}")
    
    def _update_timeline(self, activities: List):
        """Update activity timeline."""
        if not self.activity_list:
            return
        
        # Clear existing
        for widget in self.activity_list.winfo_children():
            widget.destroy()
        
        if not activities:
            ctk.CTkLabel(
                self.activity_list,
                text="No recent activity",
                text_color=self.COLORS["muted"]
            ).pack(pady=20)
            return
        
        for activity in activities:
            row = ctk.CTkFrame(self.activity_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            # Icon based on type
            icons = {
                "chat": "💬",
                "tool_call": "🔧",
                "error": "❌",
                "session": "📁",
                "api": "🌐",
                "workflow": "⚡"
            }
            icon = icons.get(activity.type.value, "•")
            
            # Status color
            color = self.COLORS["success"] if activity.success else self.COLORS["error"]
            
            ctk.CTkLabel(
                row,
                text=icon,
                width=25,
                font=ctk.CTkFont(size=12)
            ).pack(side="left")
            
            ctk.CTkLabel(
                row,
                text=activity.action[:40],
                font=ctk.CTkFont(size=12),
                text_color=color,
                anchor="w"
            ).pack(side="left", fill="x", expand=True)
            
            # Time
            try:
                dt = datetime.fromisoformat(activity.timestamp)
                time_str = dt.strftime("%H:%M")
            except:
                time_str = ""
            
            ctk.CTkLabel(
                row,
                text=time_str,
                font=ctk.CTkFont(size=11),
                text_color=self.COLORS["muted"],
                width=50
            ).pack(side="right")
    
    def _update_top_tools(self, tools: List):
        """Update top tools chart."""
        if not self.tools_list:
            return
        
        for widget in self.tools_list.winfo_children():
            widget.destroy()
        
        if not tools:
            ctk.CTkLabel(
                self.tools_list,
                text="No tool usage data",
                text_color=self.COLORS["muted"]
            ).pack(pady=20)
            return
        
        max_count = tools[0][1] if tools else 1
        
        for tool_name, count in tools[:8]:
            row = ctk.CTkFrame(self.tools_list, fg_color="transparent")
            row.pack(fill="x", pady=3)
            
            ctk.CTkLabel(
                row,
                text=tool_name,
                font=ctk.CTkFont(size=12),
                width=120,
                anchor="w"
            ).pack(side="left")
            
            # Progress bar
            progress_frame = ctk.CTkFrame(row, fg_color="#334155", height=8, corner_radius=4)
            progress_frame.pack(side="left", fill="x", expand=True, padx=10)
            
            width_pct = (count / max_count) * 100 if max_count > 0 else 0
            
            progress = ctk.CTkFrame(
                progress_frame,
                fg_color=self.COLORS["accent"],
                height=8,
                corner_radius=4
            )
            progress.place(relx=0, rely=0, relwidth=width_pct/100, relheight=1)
            
            ctk.CTkLabel(
                row,
                text=str(count),
                font=ctk.CTkFont(size=11),
                text_color=self.COLORS["muted"],
                width=40
            ).pack(side="right")
    
    def _update_errors(self, errors: List):
        """Update error log."""
        if not self.error_list:
            return
        
        for widget in self.error_list.winfo_children():
            widget.destroy()
        
        if not errors:
            ctk.CTkLabel(
                self.error_list,
                text="✓ No errors",
                text_color=self.COLORS["success"]
            ).pack(anchor="w")
            return
        
        for error in errors:
            row = ctk.CTkFrame(self.error_list, fg_color="#2d1f1f", corner_radius=6)
            row.pack(fill="x", pady=2)
            
            details = error.details.get("error", "Unknown error")
            if len(details) > 60:
                details = details[:60] + "..."
            
            ctk.CTkLabel(
                row,
                text=f"❌ {details}",
                font=ctk.CTkFont(size=11),
                text_color=self.COLORS["error"],
                anchor="w"
            ).pack(fill="x", padx=10, pady=8)
    
    def show_as_popup(self):
        """Show dashboard as popup window."""
        if not CTK_AVAILABLE:
            return
        
        popup = ctk.CTkToplevel()
        popup.title("Activity Dashboard - SysAgent")
        popup.geometry("900x700")
        
        self.parent = popup
        self.create(popup)
        self.frame.pack(fill="both", expand=True)
        
        popup.focus_force()


def show_activity_dashboard():
    """Show activity dashboard as standalone window."""
    if not CTK_AVAILABLE:
        print("Dashboard requires customtkinter")
        return
    
    ctk.set_appearance_mode("dark")
    
    root = ctk.CTk()
    root.title("Activity Dashboard - SysAgent")
    root.geometry("900x700")
    
    dashboard = ActivityDashboard()
    dashboard.create(root)
    dashboard.frame.pack(fill="both", expand=True)
    
    root.mainloop()


if __name__ == "__main__":
    show_activity_dashboard()
