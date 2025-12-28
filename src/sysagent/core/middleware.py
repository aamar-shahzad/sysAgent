"""
Human-in-the-Loop Middleware for SysAgent.
Handles approval requests, confirmations, breakpoints, state inspection,
time-travel, dynamic routing, and feedback collection.

Based on LangGraph best practices for human-in-the-loop patterns.
"""

import threading
import queue
import time
import json
import copy
from typing import Dict, Any, Optional, Callable, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    MODIFIED = "modified"  # Human modified the action


class ApprovalType(Enum):
    """Type of approval request."""
    PERMISSION = "permission"          # Request for tool permission
    CONFIRMATION = "confirmation"      # Confirm an action
    SENSITIVE_ACTION = "sensitive"     # Sensitive operation (delete, modify system)
    EXECUTION = "execution"            # Code/command execution
    NETWORK = "network"                # Network operations
    FILE_WRITE = "file_write"          # File write operations
    BREAKPOINT = "breakpoint"          # Breakpoint pause
    REVIEW = "review"                  # Review output before continuing
    EDIT = "edit"                      # Edit agent's planned action


class BreakpointType(Enum):
    """Types of breakpoints for agent execution."""
    BEFORE_TOOL = "before_tool"        # Pause before tool execution
    AFTER_TOOL = "after_tool"          # Pause after tool execution
    ON_ERROR = "on_error"              # Pause when error occurs
    ON_SENSITIVE = "on_sensitive"      # Pause for sensitive operations
    PERIODIC = "periodic"              # Pause every N steps
    CONDITIONAL = "conditional"        # Pause when condition is met
    MANUAL = "manual"                  # User-triggered pause


@dataclass
class Breakpoint:
    """A breakpoint configuration."""
    id: str
    type: BreakpointType
    enabled: bool = True
    condition: Optional[str] = None   # For conditional breakpoints
    tool_name: Optional[str] = None   # For tool-specific breakpoints
    step_interval: int = 5            # For periodic breakpoints
    hit_count: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class StateSnapshot:
    """A snapshot of agent state for time-travel."""
    id: str
    timestamp: float
    step_number: int
    messages: List[Dict[str, Any]]
    pending_action: Optional[Dict[str, Any]]
    tools_used: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackEntry:
    """User feedback on agent actions."""
    id: str
    rating: int                        # 1-5 rating
    comment: Optional[str] = None
    action_id: Optional[str] = None
    tool_name: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


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
    editable_fields: List[str] = field(default_factory=list)  # Fields that can be edited
    modified_values: Dict[str, Any] = field(default_factory=dict)  # User modifications


class HumanInTheLoopMiddleware:
    """
    Advanced middleware for human-in-the-loop interactions.
    
    Features:
    - Approval requests and confirmations
    - Breakpoints for pausing execution
    - State inspection and time-travel
    - Dynamic routing (redirect agent)
    - Feedback collection
    - Multi-step approval workflows
    
    Based on LangGraph patterns for human-in-the-loop.
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
        self._on_breakpoint_hit: Optional[Callable[[Breakpoint, Dict], None]] = None
        self._on_state_change: Optional[Callable[[StateSnapshot], None]] = None
        
        # Pre-approved actions (for "remember my choice")
        self._pre_approved: Dict[str, bool] = {}
        self._session_approved: Dict[str, bool] = {}
        
        # Breakpoints system
        self._breakpoints: Dict[str, Breakpoint] = {}
        self._breakpoint_counter = 0
        self._is_paused = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially
        
        # Time-travel / State snapshots
        self._state_history: List[StateSnapshot] = []
        self._max_history_size = 50
        self._current_step = 0
        
        # Feedback collection
        self._feedback: List[FeedbackEntry] = []
        self._feedback_counter = 0
        
        # Approval workflows
        self._workflows: Dict[str, List[ApprovalType]] = {}
        
        # Statistics
        self._stats = {
            "total_requests": 0,
            "approved": 0,
            "denied": 0,
            "modified": 0,
            "timeouts": 0,
            "breakpoints_hit": 0,
            "feedback_collected": 0,
        }
    
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
    
    # === Breakpoints System ===
    
    def add_breakpoint(
        self,
        bp_type: BreakpointType,
        tool_name: str = None,
        condition: str = None,
        step_interval: int = 5
    ) -> Breakpoint:
        """Add a breakpoint to the agent execution."""
        with self._lock:
            self._breakpoint_counter += 1
            bp_id = f"bp_{self._breakpoint_counter}"
        
        bp = Breakpoint(
            id=bp_id,
            type=bp_type,
            tool_name=tool_name,
            condition=condition,
            step_interval=step_interval
        )
        self._breakpoints[bp_id] = bp
        return bp
    
    def remove_breakpoint(self, bp_id: str) -> bool:
        """Remove a breakpoint."""
        if bp_id in self._breakpoints:
            del self._breakpoints[bp_id]
            return True
        return False
    
    def enable_breakpoint(self, bp_id: str) -> bool:
        """Enable a breakpoint."""
        if bp_id in self._breakpoints:
            self._breakpoints[bp_id].enabled = True
            return True
        return False
    
    def disable_breakpoint(self, bp_id: str) -> bool:
        """Disable a breakpoint."""
        if bp_id in self._breakpoints:
            self._breakpoints[bp_id].enabled = False
            return True
        return False
    
    def get_breakpoints(self) -> List[Breakpoint]:
        """Get all breakpoints."""
        return list(self._breakpoints.values())
    
    def clear_breakpoints(self):
        """Clear all breakpoints."""
        self._breakpoints.clear()
    
    def check_breakpoint(
        self,
        tool_name: str = None,
        is_error: bool = False,
        is_sensitive: bool = False,
        context: Dict[str, Any] = None
    ) -> Optional[Breakpoint]:
        """
        Check if any breakpoint should trigger.
        Returns the breakpoint that triggered, or None.
        """
        self._current_step += 1
        
        for bp in self._breakpoints.values():
            if not bp.enabled:
                continue
            
            triggered = False
            
            if bp.type == BreakpointType.BEFORE_TOOL and tool_name:
                if bp.tool_name is None or bp.tool_name == tool_name:
                    triggered = True
            
            elif bp.type == BreakpointType.ON_ERROR and is_error:
                triggered = True
            
            elif bp.type == BreakpointType.ON_SENSITIVE and is_sensitive:
                triggered = True
            
            elif bp.type == BreakpointType.PERIODIC:
                if self._current_step % bp.step_interval == 0:
                    triggered = True
            
            elif bp.type == BreakpointType.CONDITIONAL and bp.condition:
                # Evaluate condition (simple key=value check)
                try:
                    if context:
                        for key, value in context.items():
                            if bp.condition == f"{key}={value}":
                                triggered = True
                                break
                except Exception:
                    pass
            
            if triggered:
                bp.hit_count += 1
                self._stats["breakpoints_hit"] += 1
                
                if self._on_breakpoint_hit:
                    self._on_breakpoint_hit(bp, context or {})
                
                return bp
        
        return None
    
    def pause(self):
        """Pause agent execution."""
        self._is_paused = True
        self._pause_event.clear()
    
    def resume(self):
        """Resume agent execution."""
        self._is_paused = False
        self._pause_event.set()
    
    def is_paused(self) -> bool:
        """Check if execution is paused."""
        return self._is_paused
    
    def wait_if_paused(self, timeout: float = None) -> bool:
        """Wait if paused. Returns True if resumed, False if timeout."""
        return self._pause_event.wait(timeout=timeout)
    
    # === Time-Travel / State Snapshots ===
    
    def save_state(
        self,
        messages: List[Dict[str, Any]],
        pending_action: Dict[str, Any] = None,
        tools_used: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> StateSnapshot:
        """Save current state for time-travel."""
        with self._lock:
            snapshot_id = f"state_{len(self._state_history)}_{int(time.time())}"
        
        snapshot = StateSnapshot(
            id=snapshot_id,
            timestamp=time.time(),
            step_number=self._current_step,
            messages=copy.deepcopy(messages),
            pending_action=copy.deepcopy(pending_action) if pending_action else None,
            tools_used=list(tools_used) if tools_used else [],
            metadata=metadata or {}
        )
        
        self._state_history.append(snapshot)
        
        # Trim history if needed
        if len(self._state_history) > self._max_history_size:
            self._state_history = self._state_history[-self._max_history_size:]
        
        if self._on_state_change:
            self._on_state_change(snapshot)
        
        return snapshot
    
    def get_state_history(self) -> List[StateSnapshot]:
        """Get all state snapshots."""
        return list(self._state_history)
    
    def get_state_at(self, step_number: int) -> Optional[StateSnapshot]:
        """Get state snapshot at a specific step."""
        for snapshot in self._state_history:
            if snapshot.step_number == step_number:
                return snapshot
        return None
    
    def rollback_to(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """Rollback to a specific state snapshot."""
        for i, snapshot in enumerate(self._state_history):
            if snapshot.id == snapshot_id:
                # Remove all states after this one
                self._state_history = self._state_history[:i + 1]
                self._current_step = snapshot.step_number
                return snapshot
        return None
    
    def rollback_steps(self, num_steps: int) -> Optional[StateSnapshot]:
        """Rollback by a number of steps."""
        if num_steps <= 0 or num_steps >= len(self._state_history):
            return None
        
        target_index = len(self._state_history) - num_steps - 1
        if target_index >= 0:
            self._state_history = self._state_history[:target_index + 1]
            snapshot = self._state_history[-1]
            self._current_step = snapshot.step_number
            return snapshot
        return None
    
    def clear_history(self):
        """Clear state history."""
        self._state_history.clear()
        self._current_step = 0
    
    # === Feedback Collection ===
    
    def collect_feedback(
        self,
        rating: int,
        comment: str = None,
        action_id: str = None,
        tool_name: str = None,
        tags: List[str] = None
    ) -> FeedbackEntry:
        """Collect feedback on an agent action."""
        with self._lock:
            self._feedback_counter += 1
            feedback_id = f"feedback_{self._feedback_counter}"
        
        # Clamp rating to 1-5
        rating = max(1, min(5, rating))
        
        feedback = FeedbackEntry(
            id=feedback_id,
            rating=rating,
            comment=comment,
            action_id=action_id,
            tool_name=tool_name,
            tags=tags or []
        )
        
        self._feedback.append(feedback)
        self._stats["feedback_collected"] += 1
        
        return feedback
    
    def get_feedback(self, limit: int = 100) -> List[FeedbackEntry]:
        """Get collected feedback."""
        return self._feedback[-limit:]
    
    def get_average_rating(self) -> float:
        """Get average feedback rating."""
        if not self._feedback:
            return 0.0
        return sum(f.rating for f in self._feedback) / len(self._feedback)
    
    def export_feedback(self, path: str = None) -> str:
        """Export feedback to JSON."""
        data = [
            {
                "id": f.id,
                "rating": f.rating,
                "comment": f.comment,
                "action_id": f.action_id,
                "tool_name": f.tool_name,
                "timestamp": f.timestamp,
                "tags": f.tags
            }
            for f in self._feedback
        ]
        
        json_str = json.dumps(data, indent=2)
        
        if path:
            Path(path).write_text(json_str)
        
        return json_str
    
    # === Dynamic Routing ===
    
    def redirect_agent(self, new_instruction: str) -> ApprovalRequest:
        """Redirect the agent with a new instruction."""
        request = self.request_approval(
            ApprovalType.EDIT,
            "Redirect Agent",
            f"Override current plan with: {new_instruction}",
            {"new_instruction": new_instruction, "redirect": True}
        )
        request.status = ApprovalStatus.MODIFIED
        request.modified_values["instruction"] = new_instruction
        return request
    
    def edit_pending_action(
        self,
        request_id: str,
        field_name: str,
        new_value: Any
    ) -> bool:
        """Edit a field in a pending action."""
        if request_id not in self._pending_requests:
            return False
        
        request = self._pending_requests[request_id]
        if field_name not in request.editable_fields:
            return False
        
        request.modified_values[field_name] = new_value
        request.status = ApprovalStatus.MODIFIED
        self._stats["modified"] += 1
        return True
    
    # === Multi-Step Approval Workflows ===
    
    def define_workflow(self, name: str, steps: List[ApprovalType]):
        """Define a multi-step approval workflow."""
        self._workflows[name] = steps
    
    def get_workflow(self, name: str) -> Optional[List[ApprovalType]]:
        """Get a workflow definition."""
        return self._workflows.get(name)
    
    def run_workflow(
        self,
        workflow_name: str,
        title: str,
        description: str,
        details: Dict[str, Any] = None
    ) -> List[ApprovalRequest]:
        """Run a multi-step approval workflow."""
        workflow = self._workflows.get(workflow_name)
        if not workflow:
            return []
        
        requests = []
        for i, approval_type in enumerate(workflow):
            step_title = f"[{i+1}/{len(workflow)}] {title}"
            request = self.request_approval(
                approval_type,
                step_title,
                description,
                details
            )
            
            # Wait for each step
            status = self.wait_for_approval(request)
            requests.append(request)
            
            # Stop if denied
            if status != ApprovalStatus.APPROVED:
                break
        
        return requests
    
    # === Review Before Action ===
    
    def review_action(
        self,
        action_name: str,
        action_details: Dict[str, Any],
        editable_fields: List[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Request human review of an action before execution.
        Returns (approved, possibly_modified_details).
        """
        request = self.request_approval(
            ApprovalType.REVIEW,
            f"Review: {action_name}",
            f"Please review the following action before it executes",
            action_details,
            options=["Approve", "Modify", "Deny"]
        )
        
        if editable_fields:
            request.editable_fields = editable_fields
        
        status = self.wait_for_approval(request)
        
        if status == ApprovalStatus.MODIFIED:
            # Merge modifications
            modified_details = {**action_details, **request.modified_values}
            return True, modified_details
        elif status == ApprovalStatus.APPROVED:
            return True, action_details
        else:
            return False, action_details
    
    # === Statistics ===
    
    def get_stats(self) -> Dict[str, int]:
        """Get middleware statistics."""
        return dict(self._stats)
    
    def reset_stats(self):
        """Reset statistics."""
        for key in self._stats:
            self._stats[key] = 0


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
