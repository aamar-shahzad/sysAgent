"""
Logging and auditing module for SysAgent CLI.

Provides comprehensive logging, audit trails, and event tracking.
"""

import os
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(Enum):
    """Types of auditable events."""
    TOOL_EXECUTION = "tool_execution"
    PERMISSION_REQUEST = "permission_request"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    CONFIG_CHANGE = "config_change"
    CREDENTIAL_ACCESS = "credential_access"
    FILE_ACCESS = "file_access"
    NETWORK_ACCESS = "network_access"
    PROCESS_CONTROL = "process_control"
    SYSTEM_CHANGE = "system_change"
    USER_INPUT = "user_input"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    ERROR = "error"
    SECURITY_EVENT = "security_event"


@dataclass
class AuditEvent:
    """Represents an auditable event."""
    timestamp: str
    event_type: str
    action: str
    details: Dict[str, Any]
    user: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Manages audit logging and event tracking."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for audit logger."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, log_dir: Optional[str] = None, max_file_size_mb: int = 10):
        """Initialize audit logger.
        
        Args:
            log_dir: Directory for log files. Defaults to ~/.sysagent/logs
            max_file_size_mb: Maximum size of each log file in MB.
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        
        if log_dir is None:
            self._log_dir = Path.home() / ".sysagent" / "logs"
        else:
            self._log_dir = Path(log_dir)
        
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._max_file_size = max_file_size_mb * 1024 * 1024
        
        self._session_id = self._generate_session_id()
        self._event_handlers: List[Callable[[AuditEvent], None]] = []
        
        # Set up Python logging
        self._setup_logging()
        
        # Current log file
        self._current_log_file = self._get_log_file_path()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.sha256(f"{timestamp}-{os.getpid()}".encode()).hexdigest()[:16]
    
    def _setup_logging(self):
        """Set up Python logging configuration."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Create logger
        self._logger = logging.getLogger("sysagent")
        self._logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self._logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format))
        self._logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(
            self._log_dir / "sysagent.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        self._logger.addHandler(file_handler)
    
    def _get_log_file_path(self) -> Path:
        """Get the current audit log file path."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self._log_dir / f"audit_{date_str}.jsonl"
    
    def _rotate_if_needed(self):
        """Rotate log file if it exceeds max size."""
        if self._current_log_file.exists():
            if self._current_log_file.stat().st_size > self._max_file_size:
                # Rename current file with timestamp
                timestamp = datetime.now().strftime("%H%M%S")
                new_name = self._current_log_file.stem + f"_{timestamp}.jsonl"
                self._current_log_file.rename(self._log_dir / new_name)
                self._current_log_file = self._get_log_file_path()
    
    def log_event(self, event: AuditEvent):
        """Log an audit event.
        
        Args:
            event: The event to log.
        """
        # Update with session info
        if not event.session_id:
            event.session_id = self._session_id
        
        # Write to audit log
        self._rotate_if_needed()
        
        with open(self._current_log_file, 'a', encoding='utf-8') as f:
            f.write(event.to_json() + '\n')
        
        # Notify handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception:
                pass
        
        # Also log to Python logger
        level = logging.INFO if event.success else logging.ERROR
        self._logger.log(level, f"{event.event_type}: {event.action}")
    
    def log_tool_execution(
        self,
        tool_name: str,
        action: str,
        params: Dict[str, Any],
        result: Any,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log a tool execution event."""
        # Sanitize sensitive data
        sanitized_params = self._sanitize_data(params)
        
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type=EventType.TOOL_EXECUTION.value,
            action=f"{tool_name}.{action}",
            details={
                "tool": tool_name,
                "action": action,
                "params": sanitized_params,
                "result_summary": str(result)[:200] if result else None
            },
            success=success,
            error=error
        )
        self.log_event(event)
    
    def log_permission_request(
        self,
        permission: str,
        tool: str,
        granted: bool,
        reason: Optional[str] = None
    ):
        """Log a permission request."""
        event_type = (
            EventType.PERMISSION_GRANTED if granted 
            else EventType.PERMISSION_DENIED
        )
        
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type.value,
            action=f"permission_{permission}",
            details={
                "permission": permission,
                "tool": tool,
                "granted": granted,
                "reason": reason
            },
            success=granted
        )
        self.log_event(event)
    
    def log_config_change(
        self,
        key: str,
        old_value: Any,
        new_value: Any,
        source: str = "user"
    ):
        """Log a configuration change."""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type=EventType.CONFIG_CHANGE.value,
            action=f"config_set_{key}",
            details={
                "key": key,
                "old_value": self._sanitize_value(old_value),
                "new_value": self._sanitize_value(new_value),
                "source": source
            }
        )
        self.log_event(event)
    
    def log_security_event(
        self,
        event_name: str,
        details: Dict[str, Any],
        severity: str = "info"
    ):
        """Log a security-related event."""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type=EventType.SECURITY_EVENT.value,
            action=event_name,
            details={
                "severity": severity,
                **details
            },
            success=severity != "critical"
        )
        self.log_event(event)
    
    def log_llm_interaction(
        self,
        request: str,
        response: str,
        model: str,
        tokens_used: Optional[int] = None
    ):
        """Log an LLM interaction."""
        # Log request
        request_event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type=EventType.LLM_REQUEST.value,
            action="llm_request",
            details={
                "model": model,
                "request_preview": request[:200] + "..." if len(request) > 200 else request
            }
        )
        self.log_event(request_event)
        
        # Log response
        response_event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type=EventType.LLM_RESPONSE.value,
            action="llm_response",
            details={
                "model": model,
                "response_preview": response[:200] + "..." if len(response) > 200 else response,
                "tokens_used": tokens_used
            }
        )
        self.log_event(response_event)
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log an error event."""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type=EventType.ERROR.value,
            action=error_type,
            details={
                "error_message": error_message,
                "stack_trace": stack_trace,
                "context": context or {}
            },
            success=False,
            error=error_message
        )
        self.log_event(event)
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from logs."""
        sensitive_keys = {
            'password', 'secret', 'token', 'api_key', 'apikey', 
            'key', 'credential', 'auth', 'authorization'
        }
        
        sanitized = {}
        for key, value in data.items():
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize a single value."""
        if isinstance(value, str) and len(value) > 50:
            # Might be a key/token
            if any(c.isalnum() for c in value) and not ' ' in value:
                return "[REDACTED]"
        return value
    
    def add_event_handler(self, handler: Callable[[AuditEvent], None]):
        """Add an event handler.
        
        Args:
            handler: Function to call for each event.
        """
        self._event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable[[AuditEvent], None]):
        """Remove an event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
    
    def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Query audit events.
        
        Args:
            start_date: Start date filter (ISO format).
            end_date: End date filter (ISO format).
            event_types: Filter by event types.
            limit: Maximum number of events to return.
            
        Returns:
            List of matching events.
        """
        events = []
        
        # Get all audit log files
        log_files = sorted(self._log_dir.glob("audit_*.jsonl"), reverse=True)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            data = json.loads(line)
                            
                            # Apply filters
                            if start_date and data["timestamp"] < start_date:
                                continue
                            if end_date and data["timestamp"] > end_date:
                                continue
                            if event_types and data["event_type"] not in event_types:
                                continue
                            
                            events.append(AuditEvent(**data))
                            
                            if len(events) >= limit:
                                return events
                                
                        except json.JSONDecodeError:
                            continue
                            
            except Exception:
                continue
        
        return events
    
    def get_session_events(self) -> List[AuditEvent]:
        """Get all events from the current session.
        
        Returns:
            List of events from this session.
        """
        return self.get_events(
            event_types=None,
            limit=1000
        )
    
    def export_events(
        self,
        output_path: str,
        format: str = "json",
        **filters
    ) -> str:
        """Export events to a file.
        
        Args:
            output_path: Path for output file.
            format: Output format ('json' or 'csv').
            **filters: Filters to apply.
            
        Returns:
            Path to exported file.
        """
        events = self.get_events(**filters)
        
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump([e.to_dict() for e in events], f, indent=2)
        elif format == "csv":
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if events:
                    writer = csv.DictWriter(f, fieldnames=events[0].to_dict().keys())
                    writer.writeheader()
                    for event in events:
                        writer.writerow(event.to_dict())
        
        return output_path
    
    def clear_old_logs(self, days: int = 30):
        """Clear logs older than specified days.
        
        Args:
            days: Number of days to keep.
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        
        for log_file in self._log_dir.glob("audit_*.jsonl"):
            try:
                # Extract date from filename
                date_str = log_file.stem.split("_")[1]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff:
                    log_file.unlink()
            except Exception:
                continue
    
    @property
    def session_id(self) -> str:
        """Get current session ID."""
        return self._session_id
    
    def debug(self, message: str):
        """Log debug message."""
        self._logger.debug(message)
    
    def info(self, message: str):
        """Log info message."""
        self._logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self._logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self._logger.error(message)
    
    def critical(self, message: str):
        """Log critical message."""
        self._logger.critical(message)


# Global logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance.
    
    Returns:
        AuditLogger instance.
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_tool_execution(tool_name: str, action: str, params: Dict, result: Any, success: bool = True, error: str = None):
    """Convenience function to log tool execution."""
    get_audit_logger().log_tool_execution(tool_name, action, params, result, success, error)


def log_permission_request(permission: str, tool: str, granted: bool, reason: str = None):
    """Convenience function to log permission request."""
    get_audit_logger().log_permission_request(permission, tool, granted, reason)


def log_error(error_type: str, error_message: str, stack_trace: str = None, context: Dict = None):
    """Convenience function to log error."""
    get_audit_logger().log_error(error_type, error_message, stack_trace, context)
