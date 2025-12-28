"""
Notification Center for SysAgent - Centralized notification management.
Shows alerts, updates, and system events in a unified panel.
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
import threading
import time


class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"
    SYSTEM = "system"


@dataclass
class Notification:
    """A notification entry."""
    id: str
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    read: bool = False
    action: Optional[str] = None  # Command to run on click
    persistent: bool = False  # Don't auto-dismiss
    source: str = ""  # What generated this notification


# Colors for notification types
TYPE_COLORS = {
    NotificationType.INFO: "#3b82f6",
    NotificationType.SUCCESS: "#22c55e",
    NotificationType.WARNING: "#f59e0b",
    NotificationType.ERROR: "#ef4444",
    NotificationType.ALERT: "#8b5cf6",
    NotificationType.SYSTEM: "#64748b",
}

TYPE_ICONS = {
    NotificationType.INFO: "ℹ️",
    NotificationType.SUCCESS: "✅",
    NotificationType.WARNING: "⚠️",
    NotificationType.ERROR: "❌",
    NotificationType.ALERT: "🔔",
    NotificationType.SYSTEM: "⚙️",
}


class NotificationCenter:
    """
    Centralized notification management system.
    Stores, displays, and manages notifications.
    """
    
    def __init__(self, max_notifications: int = 100):
        self.notifications: List[Notification] = []
        self.max_notifications = max_notifications
        self._notification_counter = 0
        self._callbacks: List[Callable[[Notification], None]] = []
    
    def add(
        self,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        action: str = None,
        persistent: bool = False,
        source: str = ""
    ) -> Notification:
        """Add a new notification."""
        self._notification_counter += 1
        
        notification = Notification(
            id=f"notif_{self._notification_counter}",
            title=title,
            message=message,
            type=type,
            action=action,
            persistent=persistent,
            source=source
        )
        
        self.notifications.insert(0, notification)
        
        # Trim if exceeding max
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[:self.max_notifications]
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(notification)
            except Exception:
                pass
        
        return notification
    
    def mark_read(self, notification_id: str):
        """Mark a notification as read."""
        for notif in self.notifications:
            if notif.id == notification_id:
                notif.read = True
                break
    
    def mark_all_read(self):
        """Mark all notifications as read."""
        for notif in self.notifications:
            notif.read = True
    
    def dismiss(self, notification_id: str):
        """Remove a notification."""
        self.notifications = [n for n in self.notifications if n.id != notification_id]
    
    def clear_all(self):
        """Clear all notifications."""
        self.notifications = []
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        return sum(1 for n in self.notifications if not n.read)
    
    def get_recent(self, limit: int = 10) -> List[Notification]:
        """Get recent notifications."""
        return self.notifications[:limit]
    
    def get_by_type(self, type: NotificationType) -> List[Notification]:
        """Get notifications of a specific type."""
        return [n for n in self.notifications if n.type == type]
    
    def on_notification(self, callback: Callable[[Notification], None]):
        """Register a callback for new notifications."""
        self._callbacks.append(callback)


class NotificationPanel:
    """
    UI Panel for displaying notifications.
    """
    
    def __init__(
        self,
        parent,
        colors: dict,
        notification_center: NotificationCenter,
        on_action: Optional[Callable[[str], None]] = None
    ):
        if not CTK_AVAILABLE:
            return
        
        self.parent = parent
        self.colors = colors
        self.center = notification_center
        self.on_action = on_action
        
        self._create_panel()
    
    def _create_panel(self):
        """Create the notification panel."""
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
            text="🔔 Notifications",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        # Unread count badge
        unread = self.center.get_unread_count()
        if unread > 0:
            self.badge = ctk.CTkLabel(
                header_inner,
                text=str(unread),
                font=ctk.CTkFont(size=10),
                fg_color=self.colors.get("error", "#ef4444"),
                corner_radius=10,
                width=20,
                height=20
            )
            self.badge.pack(side="left", padx=8)
        
        # Actions
        actions = ctk.CTkFrame(header_inner, fg_color="transparent")
        actions.pack(side="right")
        
        ctk.CTkButton(
            actions,
            text="Mark All Read",
            width=100,
            height=24,
            corner_radius=4,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=self.colors.get("bg_tertiary", "#1a1a24"),
            command=self._mark_all_read
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            actions,
            text="Clear",
            width=50,
            height=24,
            corner_radius=4,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=self.colors.get("bg_tertiary", "#1a1a24"),
            command=self._clear_all
        ).pack(side="left", padx=2)
        
        # Notifications list
        self.list_frame = ctk.CTkScrollableFrame(
            self.frame,
            fg_color="transparent",
            height=300
        )
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.refresh()
    
    def refresh(self):
        """Refresh the notifications list."""
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        notifications = self.center.get_recent(20)
        
        if not notifications:
            ctk.CTkLabel(
                self.list_frame,
                text="No notifications",
                text_color=self.colors.get("text_muted", "#5a5a6a")
            ).pack(pady=20)
            return
        
        for notif in notifications:
            self._add_notification_card(notif)
    
    def _add_notification_card(self, notif: Notification):
        """Add a notification card."""
        card = ctk.CTkFrame(
            self.list_frame,
            fg_color=self.colors.get("bg_secondary", "#12121a") if notif.read else self.colors.get("bg_tertiary", "#1a1a24"),
            corner_radius=8
        )
        card.pack(fill="x", pady=2)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)
        
        # Type indicator
        type_color = TYPE_COLORS.get(notif.type, "#3b82f6")
        indicator = ctk.CTkFrame(
            inner,
            width=4,
            height=40,
            fg_color=type_color,
            corner_radius=2
        )
        indicator.pack(side="left", padx=(0, 10))
        
        # Content
        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(side="left", fill="x", expand=True)
        
        title_row = ctk.CTkFrame(content, fg_color="transparent")
        title_row.pack(fill="x")
        
        ctk.CTkLabel(
            title_row,
            text=f"{TYPE_ICONS.get(notif.type, 'ℹ️')} {notif.title}",
            font=ctk.CTkFont(size=12, weight="bold" if not notif.read else "normal")
        ).pack(side="left")
        
        # Time
        time_str = self._format_time(notif.timestamp)
        ctk.CTkLabel(
            title_row,
            text=time_str,
            font=ctk.CTkFont(size=10),
            text_color=self.colors.get("text_muted", "#5a5a6a")
        ).pack(side="right")
        
        ctk.CTkLabel(
            content,
            text=notif.message[:100] + "..." if len(notif.message) > 100 else notif.message,
            font=ctk.CTkFont(size=11),
            text_color=self.colors.get("text_secondary", "#9898a8"),
            anchor="w",
            wraplength=300
        ).pack(anchor="w")
        
        # Actions
        if notif.action:
            ctk.CTkButton(
                inner,
                text="View",
                width=50,
                height=24,
                corner_radius=4,
                font=ctk.CTkFont(size=10),
                command=lambda a=notif.action, n=notif: self._on_view(a, n)
            ).pack(side="right", padx=2)
        
        # Dismiss button
        ctk.CTkButton(
            inner,
            text="×",
            width=24,
            height=24,
            corner_radius=4,
            fg_color="transparent",
            hover_color=self.colors.get("bg_tertiary", "#1a1a24"),
            command=lambda n=notif.id: self._dismiss(n)
        ).pack(side="right")
    
    def _format_time(self, timestamp: datetime) -> str:
        """Format timestamp for display."""
        now = datetime.now()
        diff = now - timestamp
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            mins = int(diff.total_seconds() / 60)
            return f"{mins}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            return timestamp.strftime("%m/%d %H:%M")
    
    def _on_view(self, action: str, notif: Notification):
        """Handle view action."""
        self.center.mark_read(notif.id)
        if self.on_action:
            self.on_action(action)
        self.refresh()
    
    def _dismiss(self, notification_id: str):
        """Dismiss a notification."""
        self.center.dismiss(notification_id)
        self.refresh()
    
    def _mark_all_read(self):
        """Mark all as read."""
        self.center.mark_all_read()
        self.refresh()
    
    def _clear_all(self):
        """Clear all notifications."""
        self.center.clear_all()
        self.refresh()
    
    def pack(self, **kwargs):
        """Pack the panel."""
        self.frame.pack(**kwargs)


class NotificationBadge:
    """
    A small badge showing unread notification count.
    """
    
    def __init__(
        self,
        parent,
        colors: dict,
        notification_center: NotificationCenter,
        on_click: Optional[Callable] = None
    ):
        if not CTK_AVAILABLE:
            return
        
        self.parent = parent
        self.colors = colors
        self.center = notification_center
        self.on_click = on_click
        
        self._create_badge()
        
        # Register for updates
        self.center.on_notification(lambda n: self.update())
    
    def _create_badge(self):
        """Create the badge button."""
        self.button = ctk.CTkButton(
            self.parent,
            text="🔔",
            width=36,
            height=36,
            corner_radius=8,
            fg_color="transparent",
            hover_color=self.colors.get("bg_hover", "#22222e"),
            command=self._on_click
        )
        
        # Count label (overlay)
        self.count_label = ctk.CTkLabel(
            self.button,
            text="",
            font=ctk.CTkFont(size=9),
            fg_color=self.colors.get("error", "#ef4444"),
            corner_radius=8,
            width=16,
            height=16
        )
        
        self.update()
    
    def update(self):
        """Update the badge count."""
        count = self.center.get_unread_count()
        
        if count > 0:
            self.count_label.configure(text=str(min(count, 99)))
            self.count_label.place(relx=0.7, rely=0.1)
        else:
            self.count_label.place_forget()
    
    def _on_click(self):
        """Handle click."""
        if self.on_click:
            self.on_click()
    
    def pack(self, **kwargs):
        """Pack the badge."""
        self.button.pack(**kwargs)


# Singleton notification center
_notification_center: Optional[NotificationCenter] = None


def get_notification_center() -> NotificationCenter:
    """Get or create the notification center instance."""
    global _notification_center
    if _notification_center is None:
        _notification_center = NotificationCenter()
    return _notification_center


def notify(
    title: str,
    message: str,
    type: NotificationType = NotificationType.INFO,
    action: str = None
) -> Notification:
    """Convenience function to add a notification."""
    return get_notification_center().add(title, message, type, action)
