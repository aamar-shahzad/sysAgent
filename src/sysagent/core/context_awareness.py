"""
Context Awareness System for SysAgent.
Provides intelligent suggestions based on current context,
active application, time of day, and user patterns.
"""

import subprocess
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path

from ..utils.platform import detect_platform, Platform


@dataclass
class ContextInfo:
    """Current context information."""
    active_app: str = ""
    active_window: str = ""
    current_directory: str = ""
    time_of_day: str = ""  # morning, afternoon, evening, night
    day_of_week: str = ""
    clipboard_content: str = ""
    recent_files: List[str] = field(default_factory=list)
    system_state: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class Suggestion:
    """A contextual suggestion."""
    text: str
    command: str
    icon: str = "💡"
    category: str = "general"
    priority: int = 0  # Higher = more relevant
    context_match: str = ""  # Why this was suggested


class ContextAwareness:
    """
    System for understanding current context and providing
    intelligent suggestions.
    """
    
    def __init__(self):
        self.platform = detect_platform()
        self._suggestion_rules: List[Dict] = []
        self._load_default_rules()
    
    def get_current_context(self) -> ContextInfo:
        """Get the current context information."""
        context = ContextInfo()
        
        # Get active application
        context.active_app = self._get_active_app()
        context.active_window = self._get_active_window()
        
        # Get current directory
        context.current_directory = os.getcwd()
        
        # Get time context
        now = datetime.now()
        hour = now.hour
        if 5 <= hour < 12:
            context.time_of_day = "morning"
        elif 12 <= hour < 17:
            context.time_of_day = "afternoon"
        elif 17 <= hour < 21:
            context.time_of_day = "evening"
        else:
            context.time_of_day = "night"
        
        context.day_of_week = now.strftime("%A").lower()
        
        # Get clipboard content
        context.clipboard_content = self._get_clipboard()[:200]  # Limit size
        
        # Get recent files
        context.recent_files = self._get_recent_files()
        
        # Get system state
        context.system_state = self._get_system_state()
        
        return context
    
    def _get_active_app(self) -> str:
        """Get the currently active application."""
        try:
            if self.platform == Platform.MACOS:
                script = '''
                tell application "System Events"
                    set frontApp to name of first process whose frontmost is true
                end tell
                return frontApp
                '''
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True, text=True
                )
                return result.stdout.strip()
            
            elif self.platform == Platform.LINUX:
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True
                )
                return result.stdout.strip().split(" - ")[-1] if result.stdout else ""
            
            elif self.platform == Platform.WINDOWS:
                ps_script = '''
                Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class FG {
                    [DllImport("user32.dll")]
                    public static extern IntPtr GetForegroundWindow();
                    [DllImport("user32.dll")]
                    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
                }
"@
                $hwnd = [FG]::GetForegroundWindow()
                $sb = New-Object System.Text.StringBuilder 256
                [void][FG]::GetWindowText($hwnd, $sb, 256)
                Write-Output $sb.ToString()
                '''
                result = subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True, text=True
                )
                return result.stdout.strip()
        except Exception:
            pass
        return ""
    
    def _get_active_window(self) -> str:
        """Get the active window title."""
        try:
            if self.platform == Platform.MACOS:
                script = '''
                tell application "System Events"
                    tell (first process whose frontmost is true)
                        tell window 1
                            get name
                        end tell
                    end tell
                end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True, text=True
                )
                return result.stdout.strip()
            
            elif self.platform == Platform.LINUX:
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True
                )
                return result.stdout.strip()
        except Exception:
            pass
        return ""
    
    def _get_clipboard(self) -> str:
        """Get clipboard content."""
        try:
            if self.platform == Platform.MACOS:
                result = subprocess.run(
                    ["pbpaste"],
                    capture_output=True, text=True
                )
                return result.stdout
            
            elif self.platform == Platform.LINUX:
                result = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    capture_output=True, text=True
                )
                return result.stdout
            
            elif self.platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["powershell", "-Command", "Get-Clipboard"],
                    capture_output=True, text=True
                )
                return result.stdout
        except Exception:
            pass
        return ""
    
    def _get_recent_files(self) -> List[str]:
        """Get recently modified files."""
        recent = []
        try:
            home = Path.home()
            
            # Check common directories
            dirs_to_check = [
                home / "Desktop",
                home / "Documents",
                home / "Downloads",
            ]
            
            for dir_path in dirs_to_check:
                if dir_path.exists():
                    files = sorted(
                        dir_path.glob("*"),
                        key=lambda x: x.stat().st_mtime if x.is_file() else 0,
                        reverse=True
                    )
                    recent.extend([str(f) for f in files[:5] if f.is_file()])
        except Exception:
            pass
        
        return recent[:10]
    
    def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state."""
        state = {}
        
        try:
            import psutil
            state["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            state["memory_percent"] = psutil.virtual_memory().percent
            state["disk_percent"] = psutil.disk_usage("/").percent
            state["battery"] = None
            
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    state["battery"] = {
                        "percent": battery.percent,
                        "charging": battery.power_plugged
                    }
        except ImportError:
            pass
        
        return state
    
    def _load_default_rules(self):
        """Load default suggestion rules."""
        self._suggestion_rules = [
            # Time-based rules
            {
                "condition": {"time_of_day": "morning"},
                "suggestions": [
                    Suggestion("Check emails", "open email", "📧", "morning", 10, "morning routine"),
                    Suggestion("View calendar", "open calendar", "📅", "morning", 9, "morning routine"),
                    Suggestion("System health check", "check system health", "🏥", "morning", 8, "morning routine"),
                ]
            },
            {
                "condition": {"time_of_day": "evening"},
                "suggestions": [
                    Suggestion("Backup important files", "backup files", "💾", "evening", 10, "evening routine"),
                    Suggestion("Clean temp files", "clean temp files", "🧹", "evening", 9, "evening routine"),
                ]
            },
            
            # App-based rules
            {
                "condition": {"active_app_contains": "code"},
                "suggestions": [
                    Suggestion("Git status", "git status", "📊", "development", 10, "VS Code active"),
                    Suggestion("Run tests", "run tests", "🧪", "development", 9, "VS Code active"),
                    Suggestion("Format code", "format code", "✨", "development", 8, "VS Code active"),
                ]
            },
            {
                "condition": {"active_app_contains": "terminal"},
                "suggestions": [
                    Suggestion("Show command history", "show history", "📜", "terminal", 10, "Terminal active"),
                    Suggestion("List files", "list files", "📁", "terminal", 9, "Terminal active"),
                ]
            },
            {
                "condition": {"active_app_contains": "chrome"},
                "suggestions": [
                    Suggestion("Bookmark this page", "bookmark page", "🔖", "browser", 10, "Chrome active"),
                    Suggestion("Open new tab", "new tab", "➕", "browser", 9, "Chrome active"),
                    Suggestion("Clear browsing data", "clear browser data", "🧹", "browser", 8, "Chrome active"),
                ]
            },
            {
                "condition": {"active_app_contains": "excel"},
                "suggestions": [
                    Suggestion("Create chart", "create chart", "📊", "spreadsheet", 10, "Excel active"),
                    Suggestion("Format cells", "format cells", "🎨", "spreadsheet", 9, "Excel active"),
                    Suggestion("Save as PDF", "save as pdf", "📄", "spreadsheet", 8, "Excel active"),
                ]
            },
            {
                "condition": {"active_app_contains": "finder"},
                "suggestions": [
                    Suggestion("Search files", "search files", "🔍", "files", 10, "Finder active"),
                    Suggestion("New folder", "create folder", "📁", "files", 9, "Finder active"),
                    Suggestion("Show hidden files", "show hidden files", "👁️", "files", 8, "Finder active"),
                ]
            },
            
            # System state rules
            {
                "condition": {"cpu_high": True},
                "suggestions": [
                    Suggestion("Find resource hogs", "show resource hogs", "🔥", "system", 15, "High CPU usage"),
                    Suggestion("List processes", "list processes", "📋", "system", 14, "High CPU usage"),
                ]
            },
            {
                "condition": {"memory_high": True},
                "suggestions": [
                    Suggestion("Free memory", "free memory", "🧠", "system", 15, "High memory usage"),
                    Suggestion("Close unused apps", "close unused apps", "🚫", "system", 14, "High memory usage"),
                ]
            },
            {
                "condition": {"disk_high": True},
                "suggestions": [
                    Suggestion("Analyze disk usage", "analyze storage", "💾", "system", 15, "Low disk space"),
                    Suggestion("Clean temp files", "clean temp files", "🧹", "system", 14, "Low disk space"),
                    Suggestion("Find large files", "find large files", "📦", "system", 13, "Low disk space"),
                ]
            },
            {
                "condition": {"battery_low": True},
                "suggestions": [
                    Suggestion("Enable power saver", "enable power saver", "🔋", "system", 20, "Low battery"),
                    Suggestion("Close background apps", "close background apps", "🚫", "system", 19, "Low battery"),
                ]
            },
            
            # Clipboard-based rules
            {
                "condition": {"clipboard_is_url": True},
                "suggestions": [
                    Suggestion("Open URL", "open clipboard url", "🔗", "clipboard", 12, "URL in clipboard"),
                    Suggestion("Shorten URL", "shorten url", "✂️", "clipboard", 11, "URL in clipboard"),
                ]
            },
            {
                "condition": {"clipboard_is_code": True},
                "suggestions": [
                    Suggestion("Run code", "run clipboard code", "▶️", "clipboard", 12, "Code in clipboard"),
                    Suggestion("Save as snippet", "save as snippet", "💾", "clipboard", 11, "Code in clipboard"),
                ]
            },
        ]
    
    def get_suggestions(self, context: ContextInfo = None, limit: int = 5) -> List[Suggestion]:
        """Get contextual suggestions based on current context."""
        if context is None:
            context = self.get_current_context()
        
        suggestions = []
        
        for rule in self._suggestion_rules:
            condition = rule["condition"]
            
            if self._matches_condition(condition, context):
                suggestions.extend(rule["suggestions"])
        
        # Sort by priority
        suggestions.sort(key=lambda x: x.priority, reverse=True)
        
        return suggestions[:limit]
    
    def _matches_condition(self, condition: Dict, context: ContextInfo) -> bool:
        """Check if a condition matches the current context."""
        for key, value in condition.items():
            if key == "time_of_day":
                if context.time_of_day != value:
                    return False
            
            elif key == "day_of_week":
                if context.day_of_week != value:
                    return False
            
            elif key == "active_app_contains":
                if value.lower() not in context.active_app.lower():
                    return False
            
            elif key == "cpu_high":
                cpu = context.system_state.get("cpu_percent", 0)
                if cpu < 80:
                    return False
            
            elif key == "memory_high":
                mem = context.system_state.get("memory_percent", 0)
                if mem < 80:
                    return False
            
            elif key == "disk_high":
                disk = context.system_state.get("disk_percent", 0)
                if disk < 90:
                    return False
            
            elif key == "battery_low":
                battery = context.system_state.get("battery")
                if not battery or battery["percent"] > 20 or battery["charging"]:
                    return False
            
            elif key == "clipboard_is_url":
                if not context.clipboard_content.startswith(("http://", "https://")):
                    return False
            
            elif key == "clipboard_is_code":
                code_indicators = ["def ", "function ", "class ", "import ", "const ", "let ", "var "]
                if not any(ind in context.clipboard_content for ind in code_indicators):
                    return False
        
        return True
    
    def add_custom_rule(self, condition: Dict, suggestions: List[Suggestion]):
        """Add a custom suggestion rule."""
        self._suggestion_rules.append({
            "condition": condition,
            "suggestions": suggestions
        })


# Singleton instance
_context_awareness: Optional[ContextAwareness] = None


def get_context_awareness() -> ContextAwareness:
    """Get or create the context awareness instance."""
    global _context_awareness
    if _context_awareness is None:
        _context_awareness = ContextAwareness()
    return _context_awareness
