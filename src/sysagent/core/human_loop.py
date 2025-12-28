"""
Advanced Human-in-the-Loop System for SysAgent using LangGraph patterns.
Implements interrupt(), Command, and proper approval workflows.

Based on LangGraph documentation for human-in-the-loop:
- interrupt() for pausing execution
- Command for dynamic routing  
- Proper state management with checkpointers
"""

from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import time
import uuid


class ApprovalType(Enum):
    """Types of approval requests."""
    TOOL_CALL = "tool_call"           # Before executing a tool
    SENSITIVE_ACTION = "sensitive"     # Dangerous operations
    FILE_WRITE = "file_write"         # Writing/deleting files
    SYSTEM_CHANGE = "system_change"   # System modifications
    NETWORK = "network"               # Network operations
    EDIT_TOOL_ARGS = "edit_args"      # Allow user to edit tool arguments
    CONFIRMATION = "confirmation"      # General confirmation
    MULTI_STEP = "multi_step"         # Multi-step workflow approval


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"  # User modified the action
    TIMEOUT = "timeout"


@dataclass
class ToolApprovalRequest:
    """Request for tool execution approval."""
    id: str
    tool_name: str
    tool_args: Dict[str, Any]
    approval_type: ApprovalType
    description: str
    risk_level: str = "low"  # low, medium, high, critical
    timestamp: datetime = field(default_factory=datetime.now)
    status: ApprovalStatus = ApprovalStatus.PENDING
    user_response: Optional[str] = None
    modified_args: Optional[Dict[str, Any]] = None
    # Callback when approved/rejected
    on_response: Optional[Callable] = None


@dataclass 
class WorkflowStep:
    """A step in a multi-step approval workflow."""
    name: str
    description: str
    tool_name: str
    tool_args: Dict[str, Any]
    requires_approval: bool = True
    completed: bool = False
    result: Optional[str] = None


class HumanApprovalSystem:
    """
    Advanced human-in-the-loop system that integrates with LangGraph's
    interrupt() and Command patterns.
    """
    
    # Tool risk classifications
    HIGH_RISK_TOOLS = {
        "file_operations": ["delete", "write", "move"],
        "system_control": ["shutdown", "restart", "sleep"],
        "process_management": ["kill", "terminate"],
        "service_control": ["stop", "restart", "disable"],
        "security_operations": ["change_permissions", "modify_firewall"],
    }
    
    SENSITIVE_TOOLS = {
        "keyboard_mouse", "credentials_manager", "send_email",
        "automation_operations", "schedule_task"
    }
    
    def __init__(
        self,
        auto_approve_low_risk: bool = False,
        approval_timeout: int = 300,
        on_approval_request: Optional[Callable[[ToolApprovalRequest], None]] = None
    ):
        self.auto_approve_low_risk = auto_approve_low_risk
        self.approval_timeout = approval_timeout
        self.on_approval_request = on_approval_request
        
        self._pending_requests: Dict[str, ToolApprovalRequest] = {}
        self._approval_history: List[ToolApprovalRequest] = []
        self._remembered_approvals: Dict[str, bool] = {}  # tool_name -> always allow
        self._lock = threading.Lock()
        self._response_events: Dict[str, threading.Event] = {}
    
    def classify_risk(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Classify the risk level of a tool call."""
        # Check for high-risk operations
        for tool_pattern, actions in self.HIGH_RISK_TOOLS.items():
            if tool_pattern in tool_name:
                action = tool_args.get("action", "")
                if action in actions:
                    return "high"
        
        # Check for sensitive tools
        if tool_name in self.SENSITIVE_TOOLS:
            return "medium"
        
        # Specific checks
        if tool_name == "file_operations":
            action = tool_args.get("action", "")
            if action == "delete":
                return "critical"
            elif action == "write":
                return "high"
        
        if tool_name == "system_control":
            return "high"
        
        return "low"
    
    def requires_approval(self, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """Determine if a tool call requires human approval."""
        # Check if always approved
        if tool_name in self._remembered_approvals:
            return not self._remembered_approvals[tool_name]
        
        risk = self.classify_risk(tool_name, tool_args)
        
        # Auto-approve low risk if configured
        if risk == "low" and self.auto_approve_low_risk:
            return False
        
        # High and critical always need approval
        if risk in ["high", "critical"]:
            return True
        
        # Medium risk tools need approval unless remembered
        if risk == "medium":
            return True
        
        return False
    
    def create_approval_request(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        description: str = None
    ) -> ToolApprovalRequest:
        """Create an approval request for a tool call."""
        risk = self.classify_risk(tool_name, tool_args)
        
        # Determine approval type
        if "file" in tool_name and tool_args.get("action") in ["write", "delete"]:
            approval_type = ApprovalType.FILE_WRITE
        elif "system" in tool_name:
            approval_type = ApprovalType.SYSTEM_CHANGE
        elif "network" in tool_name or "http" in tool_name:
            approval_type = ApprovalType.NETWORK
        elif tool_name in self.SENSITIVE_TOOLS:
            approval_type = ApprovalType.SENSITIVE_ACTION
        else:
            approval_type = ApprovalType.TOOL_CALL
        
        # Generate description if not provided
        if not description:
            description = self._generate_description(tool_name, tool_args)
        
        request = ToolApprovalRequest(
            id=str(uuid.uuid4())[:8],
            tool_name=tool_name,
            tool_args=tool_args,
            approval_type=approval_type,
            description=description,
            risk_level=risk
        )
        
        with self._lock:
            self._pending_requests[request.id] = request
            self._response_events[request.id] = threading.Event()
        
        # Notify UI callback
        if self.on_approval_request:
            try:
                self.on_approval_request(request)
            except Exception:
                pass
        
        return request
    
    def _generate_description(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Generate a human-readable description of the action."""
        action = tool_args.get("action", "execute")
        
        descriptions = {
            "file_operations": f"File operation: {action} on {tool_args.get('path', 'unknown path')}",
            "keyboard_mouse": f"Input: {action} - {tool_args.get('text', tool_args.get('key', ''))}",
            "system_control": f"System: {action}",
            "process_management": f"Process: {action} {tool_args.get('name', '')}",
            "app_control": f"App: {action} {tool_args.get('app_name', '')}",
            "browser_control": f"Browser: {action} {tool_args.get('url', tool_args.get('query', ''))}",
            "send_email": f"Email to: {tool_args.get('to', '')}",
        }
        
        return descriptions.get(tool_name, f"{tool_name}: {action}")
    
    def wait_for_approval(
        self,
        request: ToolApprovalRequest,
        timeout: int = None
    ) -> ApprovalStatus:
        """Wait for user approval of a request."""
        timeout = timeout or self.approval_timeout
        
        event = self._response_events.get(request.id)
        if not event:
            return ApprovalStatus.REJECTED
        
        # Wait for response
        got_response = event.wait(timeout=timeout)
        
        if not got_response:
            request.status = ApprovalStatus.TIMEOUT
            return ApprovalStatus.TIMEOUT
        
        return request.status
    
    def approve(
        self,
        request_id: str,
        remember: bool = False,
        modified_args: Dict[str, Any] = None
    ):
        """Approve a pending request."""
        with self._lock:
            request = self._pending_requests.get(request_id)
            if not request:
                return
            
            if modified_args:
                request.modified_args = modified_args
                request.status = ApprovalStatus.MODIFIED
            else:
                request.status = ApprovalStatus.APPROVED
            
            if remember:
                self._remembered_approvals[request.tool_name] = True
            
            self._approval_history.append(request)
            
            # Signal the waiting thread
            event = self._response_events.get(request_id)
            if event:
                event.set()
    
    def reject(self, request_id: str, reason: str = None):
        """Reject a pending request."""
        with self._lock:
            request = self._pending_requests.get(request_id)
            if not request:
                return
            
            request.status = ApprovalStatus.REJECTED
            request.user_response = reason
            
            self._approval_history.append(request)
            
            event = self._response_events.get(request_id)
            if event:
                event.set()
    
    def get_pending_requests(self) -> List[ToolApprovalRequest]:
        """Get all pending approval requests."""
        with self._lock:
            return [r for r in self._pending_requests.values() 
                   if r.status == ApprovalStatus.PENDING]
    
    def clear_remembered(self):
        """Clear all remembered approvals."""
        self._remembered_approvals.clear()
    
    def get_approval_history(self, limit: int = 50) -> List[ToolApprovalRequest]:
        """Get recent approval history."""
        return self._approval_history[-limit:]


def create_tool_approval_node(approval_system: HumanApprovalSystem):
    """
    Create a LangGraph node that handles tool approval.
    Uses interrupt() to pause for human approval.
    
    Usage in graph:
        graph.add_node("approve_tool", create_tool_approval_node(approval_system))
    """
    from langgraph.types import interrupt, Command
    
    def approve_tool_node(state: Dict[str, Any]) -> Union[Dict[str, Any], Command]:
        """Node that checks if tool needs approval and interrupts if so."""
        pending_tool = state.get("pending_tool_call")
        
        if not pending_tool:
            return state
        
        tool_name = pending_tool.get("name", "")
        tool_args = pending_tool.get("args", {})
        
        # Check if approval needed
        if approval_system.requires_approval(tool_name, tool_args):
            # Create approval request
            request = approval_system.create_approval_request(
                tool_name=tool_name,
                tool_args=tool_args
            )
            
            # Interrupt execution for human approval
            # This will pause the graph and return control
            response = interrupt({
                "type": "tool_approval",
                "request_id": request.id,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "description": request.description,
                "risk_level": request.risk_level
            })
            
            # When resumed, response will contain user's decision
            if response.get("approved"):
                # Check if args were modified
                if response.get("modified_args"):
                    state["pending_tool_call"]["args"] = response["modified_args"]
                
                return state
            else:
                # Rejected - skip the tool call
                return Command(goto="agent", update={
                    "messages": state.get("messages", []) + [
                        {"role": "system", "content": f"Tool {tool_name} was rejected by user. Reason: {response.get('reason', 'No reason given')}"}
                    ],
                    "pending_tool_call": None
                })
        
        return state
    
    return approve_tool_node


def create_human_feedback_node():
    """
    Create a LangGraph node that collects human feedback.
    Uses interrupt() to get feedback on agent responses.
    """
    from langgraph.types import interrupt
    
    def feedback_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Node that collects human feedback."""
        if not state.get("collect_feedback"):
            return state
        
        last_response = state.get("last_response", "")
        
        # Interrupt for feedback
        feedback = interrupt({
            "type": "feedback_request",
            "response": last_response,
            "options": ["👍 Good", "👎 Bad", "💡 Suggestion"]
        })
        
        # Store feedback
        state["feedback_history"] = state.get("feedback_history", [])
        state["feedback_history"].append({
            "response": last_response,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
        
        return state
    
    return feedback_node


class MultiStepApprovalWorkflow:
    """
    Manages multi-step workflows that require incremental human approval.
    Useful for complex tasks like "set up development environment".
    """
    
    def __init__(self, approval_system: HumanApprovalSystem):
        self.approval_system = approval_system
        self.workflows: Dict[str, List[WorkflowStep]] = {}
        self.active_workflow: Optional[str] = None
        self.current_step_index: int = 0
    
    def create_workflow(self, name: str, steps: List[WorkflowStep]) -> str:
        """Create a new multi-step workflow."""
        workflow_id = f"{name}_{uuid.uuid4().hex[:6]}"
        self.workflows[workflow_id] = steps
        return workflow_id
    
    def start_workflow(self, workflow_id: str) -> Optional[WorkflowStep]:
        """Start executing a workflow."""
        if workflow_id not in self.workflows:
            return None
        
        self.active_workflow = workflow_id
        self.current_step_index = 0
        return self.get_current_step()
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the current step in the active workflow."""
        if not self.active_workflow:
            return None
        
        steps = self.workflows.get(self.active_workflow, [])
        if self.current_step_index >= len(steps):
            return None
        
        return steps[self.current_step_index]
    
    def complete_step(self, result: str) -> Optional[WorkflowStep]:
        """Mark current step complete and move to next."""
        step = self.get_current_step()
        if step:
            step.completed = True
            step.result = result
            self.current_step_index += 1
        
        return self.get_current_step()
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get status of the active workflow."""
        if not self.active_workflow:
            return {"active": False}
        
        steps = self.workflows.get(self.active_workflow, [])
        completed = sum(1 for s in steps if s.completed)
        
        return {
            "active": True,
            "workflow_id": self.active_workflow,
            "total_steps": len(steps),
            "completed_steps": completed,
            "current_step": self.current_step_index,
            "progress_percent": (completed / len(steps) * 100) if steps else 0
        }


# Singleton instance
_approval_system: Optional[HumanApprovalSystem] = None


def get_approval_system(
    auto_approve_low_risk: bool = False,
    on_request: Callable = None
) -> HumanApprovalSystem:
    """Get or create the approval system instance."""
    global _approval_system
    if _approval_system is None:
        _approval_system = HumanApprovalSystem(
            auto_approve_low_risk=auto_approve_low_risk,
            on_approval_request=on_request
        )
    return _approval_system


def reset_approval_system():
    """Reset the approval system (useful for testing)."""
    global _approval_system
    _approval_system = None
