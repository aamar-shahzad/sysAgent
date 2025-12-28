"""
Smart Clipboard for SysAgent.
Monitors clipboard and provides intelligent actions based on content.
"""

import re
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class ContentType(Enum):
    """Types of clipboard content."""
    TEXT = "text"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    FILE_PATH = "file_path"
    IP_ADDRESS = "ip"
    JSON = "json"
    CODE = "code"
    COMMAND = "command"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ClipboardAction:
    """An action that can be performed on clipboard content."""
    id: str
    label: str
    description: str
    icon: str
    command: str


@dataclass
class ClipboardEntry:
    """A clipboard history entry."""
    content: str
    content_type: str
    timestamp: str
    preview: str
    actions: List[ClipboardAction]


# Action definitions for each content type
CONTENT_ACTIONS: Dict[ContentType, List[ClipboardAction]] = {
    ContentType.URL: [
        ClipboardAction("open_url", "Open URL", "Open in browser", "🌐", "Open {content} in browser"),
        ClipboardAction("check_url", "Check Status", "Check if URL is reachable", "🔍", "Check if {content} is reachable"),
        ClipboardAction("download", "Download", "Download the file", "⬇️", "Download {content}"),
    ],
    ContentType.EMAIL: [
        ClipboardAction("compose", "Compose Email", "Open email compose", "✉️", "Compose email to {content}"),
        ClipboardAction("lookup", "Look Up", "Search for this email", "🔍", "Search for information about {content}"),
    ],
    ContentType.FILE_PATH: [
        ClipboardAction("open_file", "Open File", "Open the file", "📂", "Open file {content}"),
        ClipboardAction("file_info", "File Info", "Show file information", "ℹ️", "Show info for {content}"),
        ClipboardAction("copy_contents", "Read Contents", "Read file contents", "📄", "Read contents of {content}"),
    ],
    ContentType.IP_ADDRESS: [
        ClipboardAction("ping", "Ping", "Ping this IP", "📡", "Ping {content}"),
        ClipboardAction("lookup_ip", "Lookup", "Look up IP information", "🔍", "Look up information for IP {content}"),
        ClipboardAction("port_scan", "Check Ports", "Check common ports", "🔌", "Check open ports on {content}"),
    ],
    ContentType.JSON: [
        ClipboardAction("format", "Format JSON", "Pretty print JSON", "📋", "Format and display this JSON: {content}"),
        ClipboardAction("validate", "Validate", "Validate JSON structure", "✅", "Validate this JSON: {content}"),
    ],
    ContentType.CODE: [
        ClipboardAction("explain", "Explain Code", "Explain what this code does", "💡", "Explain this code: {content}"),
        ClipboardAction("run", "Run Code", "Execute this code", "▶️", "Run this code: {content}"),
        ClipboardAction("improve", "Improve", "Suggest improvements", "✨", "Improve this code: {content}"),
    ],
    ContentType.COMMAND: [
        ClipboardAction("run_cmd", "Run Command", "Execute this command", "▶️", "Run: {content}"),
        ClipboardAction("explain_cmd", "Explain", "Explain command", "💡", "Explain command: {content}"),
        ClipboardAction("safe_check", "Safety Check", "Check if command is safe", "🔒", "Is this command safe: {content}"),
    ],
    ContentType.ERROR: [
        ClipboardAction("analyze", "Analyze Error", "Analyze and explain error", "🔍", "Analyze this error: {content}"),
        ClipboardAction("fix", "Suggest Fix", "Suggest a fix", "🔧", "How to fix: {content}"),
        ClipboardAction("search", "Search Online", "Search for solutions", "🌐", "Search for solutions to: {content}"),
    ],
    ContentType.PHONE: [
        ClipboardAction("format_phone", "Format", "Format phone number", "📞", "Format phone number: {content}"),
    ],
    ContentType.TEXT: [
        ClipboardAction("summarize", "Summarize", "Summarize text", "📝", "Summarize: {content}"),
        ClipboardAction("translate", "Translate", "Translate text", "🌍", "Translate: {content}"),
        ClipboardAction("search_text", "Search", "Search for this text", "🔍", "Search for: {content}"),
    ],
}


class SmartClipboard:
    """
    Smart clipboard manager with content detection and actions.
    
    Features:
    - Content type detection
    - Smart action suggestions
    - Clipboard history
    - Pattern matching
    """
    
    def __init__(self, on_new_content: Optional[Callable[[ClipboardEntry], None]] = None):
        self.on_new_content = on_new_content
        self.history: List[ClipboardEntry] = []
        self.max_history = 50
        self._last_content = ""
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def detect_content_type(self, content: str) -> ContentType:
        """Detect the type of content."""
        content = content.strip()
        
        if not content:
            return ContentType.UNKNOWN
        
        # URL detection
        url_pattern = r'^https?://[^\s]+$'
        if re.match(url_pattern, content):
            return ContentType.URL
        
        # Email detection
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, content):
            return ContentType.EMAIL
        
        # Phone number detection
        phone_pattern = r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$'
        if re.match(phone_pattern, content.replace(' ', '')):
            return ContentType.PHONE
        
        # IP address detection
        ip_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if re.match(ip_pattern, content):
            return ContentType.IP_ADDRESS
        
        # File path detection
        if content.startswith('/') or content.startswith('~') or re.match(r'^[A-Za-z]:\\', content):
            return ContentType.FILE_PATH
        
        # JSON detection
        if (content.startswith('{') and content.endswith('}')) or \
           (content.startswith('[') and content.endswith(']')):
            try:
                import json
                json.loads(content)
                return ContentType.JSON
            except Exception:
                pass
        
        # Error detection
        error_keywords = ['error', 'exception', 'traceback', 'failed', 'cannot', 'unable']
        if any(kw in content.lower() for kw in error_keywords):
            if len(content) > 50:  # Likely an error message
                return ContentType.ERROR
        
        # Command detection
        command_starters = ['sudo', 'cd', 'ls', 'cat', 'grep', 'find', 'mkdir', 'rm', 'cp', 'mv', 
                           'git', 'docker', 'npm', 'pip', 'python', 'node', 'curl', 'wget']
        first_word = content.split()[0].lower() if content.split() else ""
        if first_word in command_starters:
            return ContentType.COMMAND
        
        # Code detection
        code_indicators = ['def ', 'function ', 'class ', 'import ', 'const ', 'let ', 'var ', 
                          'if (', 'for (', 'while (', '=>', '->']
        if any(ind in content for ind in code_indicators):
            return ContentType.CODE
        
        return ContentType.TEXT
    
    def get_actions(self, content: str, content_type: Optional[ContentType] = None) -> List[ClipboardAction]:
        """Get available actions for content."""
        if content_type is None:
            content_type = self.detect_content_type(content)
        
        actions = CONTENT_ACTIONS.get(content_type, CONTENT_ACTIONS[ContentType.TEXT])
        
        # Substitute content in commands
        result = []
        preview = content[:100] + "..." if len(content) > 100 else content
        for action in actions:
            new_action = ClipboardAction(
                id=action.id,
                label=action.label,
                description=action.description,
                icon=action.icon,
                command=action.command.replace("{content}", preview)
            )
            result.append(new_action)
        
        return result
    
    def process_content(self, content: str) -> ClipboardEntry:
        """Process clipboard content and create entry."""
        content_type = self.detect_content_type(content)
        actions = self.get_actions(content, content_type)
        
        preview = content[:100] + "..." if len(content) > 100 else content
        
        entry = ClipboardEntry(
            content=content,
            content_type=content_type.value,
            timestamp=datetime.now().isoformat(),
            preview=preview,
            actions=actions
        )
        
        return entry
    
    def add_to_history(self, content: str) -> Optional[ClipboardEntry]:
        """Add content to history and return entry if new."""
        if not content or content == self._last_content:
            return None
        
        self._last_content = content
        entry = self.process_content(content)
        
        # Add to history
        self.history.insert(0, entry)
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        # Notify callback
        if self.on_new_content:
            try:
                self.on_new_content(entry)
            except Exception:
                pass
        
        return entry
    
    def start_monitoring(self):
        """Start monitoring clipboard."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring clipboard."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
    
    def _monitor_loop(self):
        """Monitor clipboard for changes."""
        while self._running:
            try:
                content = self._get_clipboard()
                if content:
                    self.add_to_history(content)
            except Exception:
                pass
            time.sleep(1)
    
    def _get_clipboard(self) -> str:
        """Get current clipboard content."""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                return result.stdout
            elif system == "Linux":
                try:
                    result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                                          capture_output=True, text=True)
                    return result.stdout
                except Exception:
                    try:
                        result = subprocess.run(['xsel', '--clipboard', '--output'],
                                              capture_output=True, text=True)
                        return result.stdout
                    except Exception:
                        pass
            elif system == "Windows":
                try:
                    import ctypes
                    CF_TEXT = 1
                    kernel32 = ctypes.windll.kernel32
                    user32 = ctypes.windll.user32
                    user32.OpenClipboard(0)
                    if user32.IsClipboardFormatAvailable(CF_TEXT):
                        data = user32.GetClipboardData(CF_TEXT)
                        text = ctypes.c_char_p(data).value
                        user32.CloseClipboard()
                        return text.decode('utf-8') if text else ""
                    user32.CloseClipboard()
                except Exception:
                    pass
        except Exception:
            pass
        
        return ""
    
    def get_history(self, limit: int = 10) -> List[ClipboardEntry]:
        """Get clipboard history."""
        return self.history[:limit]
    
    def clear_history(self):
        """Clear clipboard history."""
        self.history.clear()
        self._last_content = ""
    
    def search_history(self, query: str) -> List[ClipboardEntry]:
        """Search clipboard history."""
        query = query.lower()
        return [
            entry for entry in self.history
            if query in entry.content.lower()
        ]


# Global instance
_clipboard: Optional[SmartClipboard] = None


def get_smart_clipboard() -> SmartClipboard:
    """Get the global smart clipboard instance."""
    global _clipboard
    if _clipboard is None:
        _clipboard = SmartClipboard()
    return _clipboard
