"""
Activity Tracker for SysAgent - Audit trail and activity logging.
Enterprise-grade activity monitoring and history.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class ActivityType(Enum):
    """Types of activities."""
    CHAT = "chat"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SESSION = "session"
    PERMISSION = "permission"
    CONFIG = "config"
    API = "api"
    WORKFLOW = "workflow"


@dataclass
class Activity:
    """Represents an activity event."""
    id: str
    type: ActivityType
    action: str
    timestamp: str
    details: Dict[str, Any]
    duration_ms: int = 0
    success: bool = True
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "type": self.type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Activity":
        data["type"] = ActivityType(data["type"])
        return cls(**data)


class ActivityTracker:
    """
    Tracks all activities in SysAgent for audit and analytics.
    
    Features:
    - Log all activities (commands, tool calls, errors)
    - Query activity history
    - Generate reports
    - Export audit logs
    - Real-time activity stream
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path.home() / ".sysagent" / "activity"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_day: Optional[str] = None
        self.activities: List[Activity] = []
        self.lock = threading.Lock()
        self._load_today()
        self._activity_id = 0
    
    def _get_day_file(self, date: Optional[datetime] = None) -> Path:
        """Get the file path for a specific day."""
        date = date or datetime.now()
        return self.storage_dir / f"{date.strftime('%Y-%m-%d')}.json"
    
    def _load_today(self):
        """Load today's activities."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_day:
            self.current_day = today
            self.activities = []
            
            file_path = self._get_day_file()
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        self.activities = [Activity.from_dict(a) for a in data]
                        self._activity_id = len(self.activities)
                except Exception:
                    self.activities = []
    
    def _save_today(self):
        """Save today's activities."""
        file_path = self._get_day_file()
        try:
            with open(file_path, 'w') as f:
                json.dump([a.to_dict() for a in self.activities], f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save activities: {e}")
    
    def log(self, activity_type: ActivityType, action: str, 
            details: Dict = None, duration_ms: int = 0, 
            success: bool = True, session_id: str = None) -> Activity:
        """Log an activity."""
        with self.lock:
            self._load_today()
            
            self._activity_id += 1
            activity = Activity(
                id=f"{self.current_day}-{self._activity_id:06d}",
                type=activity_type,
                action=action,
                timestamp=datetime.now().isoformat(),
                details=details or {},
                duration_ms=duration_ms,
                success=success,
                session_id=session_id
            )
            
            self.activities.append(activity)
            self._save_today()
            
            return activity
    
    def log_chat(self, message: str, response: str = "", session_id: str = None) -> Activity:
        """Log a chat interaction."""
        return self.log(
            ActivityType.CHAT,
            "chat_message",
            {"message": message[:200], "response_length": len(response)},
            session_id=session_id
        )
    
    def log_tool_call(self, tool_name: str, action: str, params: Dict = None,
                      duration_ms: int = 0, success: bool = True) -> Activity:
        """Log a tool call."""
        return self.log(
            ActivityType.TOOL_CALL,
            f"{tool_name}.{action}",
            {"tool": tool_name, "action": action, "params": params or {}},
            duration_ms=duration_ms,
            success=success
        )
    
    def log_error(self, error: str, context: Dict = None) -> Activity:
        """Log an error."""
        return self.log(
            ActivityType.ERROR,
            "error",
            {"error": error[:500], "context": context or {}},
            success=False
        )
    
    def log_session(self, action: str, session_id: str) -> Activity:
        """Log a session event."""
        return self.log(
            ActivityType.SESSION,
            action,
            {"session_id": session_id},
            session_id=session_id
        )
    
    def log_api(self, endpoint: str, method: str, status: int,
                duration_ms: int = 0) -> Activity:
        """Log an API request."""
        return self.log(
            ActivityType.API,
            f"{method} {endpoint}",
            {"endpoint": endpoint, "method": method, "status": status},
            duration_ms=duration_ms,
            success=200 <= status < 400
        )
    
    def log_workflow(self, workflow_name: str, action: str,
                     steps_completed: int = 0, total_steps: int = 0) -> Activity:
        """Log a workflow execution."""
        return self.log(
            ActivityType.WORKFLOW,
            f"workflow.{action}",
            {
                "workflow": workflow_name,
                "action": action,
                "steps_completed": steps_completed,
                "total_steps": total_steps
            }
        )
    
    def get_recent(self, limit: int = 50, 
                   activity_type: Optional[ActivityType] = None) -> List[Activity]:
        """Get recent activities."""
        with self.lock:
            self._load_today()
            
            activities = self.activities.copy()
            
            if activity_type:
                activities = [a for a in activities if a.type == activity_type]
            
            return list(reversed(activities[-limit:]))
    
    def get_by_date(self, date: datetime) -> List[Activity]:
        """Get activities for a specific date."""
        file_path = self._get_day_file(date)
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return [Activity.from_dict(a) for a in data]
        except Exception:
            return []
    
    def get_date_range(self, start: datetime, end: datetime) -> List[Activity]:
        """Get activities for a date range."""
        activities = []
        current = start
        
        while current <= end:
            activities.extend(self.get_by_date(current))
            current += timedelta(days=1)
        
        return activities
    
    def search(self, query: str, limit: int = 50) -> List[Activity]:
        """Search activities."""
        query_lower = query.lower()
        results = []
        
        # Search in today's activities first
        for activity in reversed(self.activities):
            if query_lower in activity.action.lower():
                results.append(activity)
            elif query_lower in str(activity.details).lower():
                results.append(activity)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get activity statistics."""
        end = datetime.now()
        start = end - timedelta(days=days)
        
        activities = self.get_date_range(start, end)
        
        # Count by type
        type_counts = {}
        for activity in activities:
            type_name = activity.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Count by day
        day_counts = {}
        for activity in activities:
            day = activity.timestamp[:10]
            day_counts[day] = day_counts.get(day, 0) + 1
        
        # Top tools
        tool_counts = {}
        for activity in activities:
            if activity.type == ActivityType.TOOL_CALL:
                tool = activity.details.get("tool", "unknown")
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        top_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Error rate
        total = len(activities)
        errors = sum(1 for a in activities if not a.success)
        error_rate = (errors / total * 100) if total > 0 else 0
        
        # Average duration
        durations = [a.duration_ms for a in activities if a.duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_activities": total,
            "by_type": type_counts,
            "by_day": day_counts,
            "top_tools": top_tools,
            "error_count": errors,
            "error_rate": round(error_rate, 2),
            "avg_duration_ms": round(avg_duration, 2),
            "period_days": days
        }
    
    def get_tool_usage(self, days: int = 30) -> Dict[str, int]:
        """Get tool usage statistics."""
        end = datetime.now()
        start = end - timedelta(days=days)
        activities = self.get_date_range(start, end)
        
        usage = {}
        for activity in activities:
            if activity.type == ActivityType.TOOL_CALL:
                tool = activity.details.get("tool", "unknown")
                usage[tool] = usage.get(tool, 0) + 1
        
        return dict(sorted(usage.items(), key=lambda x: x[1], reverse=True))
    
    def export(self, format: str = "json", days: int = 7) -> str:
        """Export activity log."""
        end = datetime.now()
        start = end - timedelta(days=days)
        activities = self.get_date_range(start, end)
        
        if format == "json":
            return json.dumps([a.to_dict() for a in activities], indent=2)
        
        elif format == "csv":
            lines = ["id,type,action,timestamp,success,duration_ms"]
            for a in activities:
                lines.append(f"{a.id},{a.type.value},{a.action},{a.timestamp},{a.success},{a.duration_ms}")
            return "\n".join(lines)
        
        elif format == "text":
            lines = ["SysAgent Activity Log", "=" * 50, ""]
            for a in activities:
                status = "✓" if a.success else "✗"
                lines.append(f"[{a.timestamp}] {status} {a.action}")
                if a.duration_ms:
                    lines.append(f"  Duration: {a.duration_ms}ms")
                if a.details:
                    lines.append(f"  Details: {a.details}")
                lines.append("")
            return "\n".join(lines)
        
        return ""
    
    def cleanup(self, days: int = 30) -> int:
        """Clean up old activity logs."""
        cutoff = datetime.now() - timedelta(days=days)
        deleted = 0
        
        for file in self.storage_dir.glob("*.json"):
            try:
                # Parse date from filename
                date_str = file.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff:
                    file.unlink()
                    deleted += 1
            except Exception:
                continue
        
        return deleted


# Global instance
_tracker: Optional[ActivityTracker] = None


def get_activity_tracker() -> ActivityTracker:
    """Get the global activity tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ActivityTracker()
    return _tracker
