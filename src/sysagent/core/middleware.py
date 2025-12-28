"""
Human-in-the-Loop Middleware for SysAgent.
Handles approval requests, confirmations, and user interactions during agent execution.
"""

import threading
import queue
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ApprovalType(Enum):
    """Type of approval request."""
    PERMISSION = "permission"          # Request for tool permission
    CONFIRMATION = "confirmation"      # Confirm an action
    SENSITIVE_ACTION = "sensitive"     # Sensitive operation (delete, modify system)
    EXECUTION = "execution"            # Code/command execution
    NETWORK = "network"                # Network operations
    FILE_WRITE = "file_write"          # File write operations


@dataclass
class ApprovalRequest:
    """A request for human approval."""
    id: str
    type: ApprovalType
    title: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    options: List[str] = field(default_factory=lambda: ["Approve", "Deny"])
    timeout_seconds: int = 60
    created_at: float = field(default_factory=time.time)
    status: ApprovalStatus = ApprovalStatus.PENDING
    response: Optional[str] = None
    callback: Optional[Callable] = None


class HumanInTheLoopMiddleware:
    """
    Middleware for handling human-in-the-loop interactions.
    Provides approval requests, confirmations, and feedback collection.
    """
    
    def __init__(self, auto_approve: bool = False, timeout_seconds: int = 60):
        self.auto_approve = auto_approve
        self.timeout_seconds = timeout_seconds
        
        # Request queues
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._response_queue = queue.Queue()
        self._request_counter = 0
        self._lock = threading.Lock()
        
        # Callbacks for UI integration
        self._on_approval_request: Optional[Callable[[ApprovalRequest], None]] = None
        self._on_approval_response: Optional[Callable[[str, ApprovalStatus], None]] = None
        
        # Pre-approved actions (for "remember my choice")
        self._pre_approved: Dict[str, bool] = {}
        self._session_approved: Dict[str, bool] = {}
    
    def set_approval_callback(self, callback: Callable[[ApprovalRequest], None]):
        """Set callback for when approval is needed."""
        self._on_approval_request = callback
    
    def set_response_callback(self, callback: Callable[[str, ApprovalStatus], None]):
        """Set callback for when response is received."""
        self._on_approval_response = callback
    
    def request_approval(
        self,
        approval_type: ApprovalType,
        title: str,
        description: str,
        details: Dict[str, Any] = None,
        timeout: int = None
    ) -> ApprovalRequest:
        """
        Request human approval for an action.
        Returns the approval request (check status for result).
        """
        with self._lock:
            self._request_counter += 1
            request_id = f"req_{self._request_counter}_{int(time.time())}"
        
        # Create request
        request = ApprovalRequest(
            id=request_id,
            type=approval_type,
            title=title,
            description=description,
            details=details or {},
            timeout_seconds=timeout or self.timeout_seconds
        )
        
        # Check pre-approved
        approval_key = f"{approval_type.value}:{title}"
        if approval_key in self._pre_approved:
            request.status = ApprovalStatus.APPROVED if self._pre_approved[approval_key] else ApprovalStatus.DENIED
            request.response = "Pre-approved" if request.status == ApprovalStatus.APPROVED else "Pre-denied"
            return request
        
        # Check session approved
        if approval_key in self._session_approved:
            request.status = ApprovalStatus.APPROVED if self._session_approved[approval_key] else ApprovalStatus.DENIED
            request.response = "Session approved" if request.status == ApprovalStatus.APPROVED else "Session denied"
            return request
        
        # Auto-approve if enabled
        if self.auto_approve:
            request.status = ApprovalStatus.APPROVED
            request.response = "Auto-approved"
            return request
        
        # Store pending request
        self._pending_requests[request_id] = request
        
        # Notify callback
        if self._on_approval_request:
            self._on_approval_request(request)
        
        return request
    
    def wait_for_approval(self, request: ApprovalRequest, blocking: bool = True) -> ApprovalStatus:
        """
        Wait for approval response.
        If blocking=True, waits until response or timeout.
        """
        if request.status != ApprovalStatus.PENDING:
            return request.status
        
        if not blocking:
            return request.status
        
        # Wait for response with timeout
        start_time = time.time()
        while time.time() - start_time < request.timeout_seconds:
            if request.id not in self._pending_requests:
                return request.status
            
            # Check if response received
            req = self._pending_requests.get(request.id)
            if req and req.status != ApprovalStatus.PENDING:
                return req.status
            
            time.sleep(0.1)
        
        # Timeout
        if request.id in self._pending_requests:
            request.status = ApprovalStatus.TIMEOUT
            del self._pending_requests[request.id]
        
        return request.status
    
    def respond_to_request(
        self,
        request_id: str,
        approved: bool,
        remember: bool = False,
        session_only: bool = False
    ):
        """Respond to an approval request."""
        if request_id not in self._pending_requests:
            return
        
        request = self._pending_requests[request_id]
        request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.DENIED
        request.response = "Approved by user" if approved else "Denied by user"
        
        # Remember choice
        if remember:
            approval_key = f"{request.type.value}:{request.title}"
            if session_only:
                self._session_approved[approval_key] = approved
            else:
                self._pre_approved[approval_key] = approved
        
        # Remove from pending
        del self._pending_requests[request_id]
        
        # Notify callback
        if self._on_approval_response:
            self._on_approval_response(request_id, request.status)
    
    def approve(self, request_id: str, remember: bool = False):
        """Approve a request."""
        self.respond_to_request(request_id, approved=True, remember=remember)
    
    def deny(self, request_id: str, remember: bool = False):
        """Deny a request."""
        self.respond_to_request(request_id, approved=False, remember=remember)
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return list(self._pending_requests.values())
    
    def cancel_all_pending(self):
        """Cancel all pending requests."""
        for request_id in list(self._pending_requests.keys()):
            request = self._pending_requests.get(request_id)
            if request:
                request.status = ApprovalStatus.CANCELLED
            del self._pending_requests[request_id]
    
    def clear_session_approvals(self):
        """Clear session-only approvals."""
        self._session_approved.clear()
    
    def clear_all_approvals(self):
        """Clear all remembered approvals."""
        self._pre_approved.clear()
        self._session_approved.clear()
    
    # === Convenience methods for common approval types ===
    
    def request_permission(self, permission_name: str, reason: str) -> bool:
        """Request permission for a specific action."""
        request = self.request_approval(
            ApprovalType.PERMISSION,
            f"Permission: {permission_name}",
            reason,
            {"permission": permission_name}
        )
        status = self.wait_for_approval(request)
        return status == ApprovalStatus.APPROVED
    
    def confirm_action(self, action: str, details: str = "") -> bool:
        """Confirm a potentially dangerous action."""
        request = self.request_approval(
            ApprovalType.CONFIRMATION,
            f"Confirm: {action}",
            details or f"Are you sure you want to {action}?",
            {"action": action}
        )
        status = self.wait_for_approval(request)
        return status == ApprovalStatus.APPROVED
    
    def confirm_sensitive_operation(self, operation: str, target: str, impact: str) -> bool:
        """Confirm a sensitive operation."""
        request = self.request_approval(
            ApprovalType.SENSITIVE_ACTION,
            f"Sensitive: {operation}",
            f"This will {operation} on {target}. {impact}",
            {"operation": operation, "target": target, "impact": impact}
        )
        status = self.wait_for_approval(request)
        return status == ApprovalStatus.APPROVED
    
    def confirm_execution(self, code_type: str, code: str) -> bool:
        """Confirm code/command execution."""
        # Truncate code for display
        display_code = code[:200] + "..." if len(code) > 200 else code
        
        request = self.request_approval(
            ApprovalType.EXECUTION,
            f"Execute {code_type}",
            f"The agent wants to execute the following {code_type}:\n\n{display_code}",
            {"code_type": code_type, "code": code}
        )
        status = self.wait_for_approval(request)
        return status == ApprovalStatus.APPROVED
    
    def confirm_file_write(self, path: str, operation: str) -> bool:
        """Confirm file write operation."""
        request = self.request_approval(
            ApprovalType.FILE_WRITE,
            f"File: {operation}",
            f"The agent wants to {operation} the file: {path}",
            {"path": path, "operation": operation}
        )
        status = self.wait_for_approval(request)
        return status == ApprovalStatus.APPROVED


# Singleton instance
_middleware: Optional[HumanInTheLoopMiddleware] = None


def get_middleware(auto_approve: bool = False) -> HumanInTheLoopMiddleware:
    """Get or create the middleware instance."""
    global _middleware
    if _middleware is None:
        _middleware = HumanInTheLoopMiddleware(auto_approve=auto_approve)
    return _middleware


def reset_middleware():
    """Reset the middleware instance."""
    global _middleware
    _middleware = None
