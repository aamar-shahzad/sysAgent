"""
Automation tool for SysAgent CLI.
"""

import os
import json
import time
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory, PermissionLevel


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    id: str
    name: str
    command: str
    schedule: str  # cron-like format or interval
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    created_at: datetime


@dataclass
class Workflow:
    """Represents an automation workflow."""
    id: str
    name: str
    steps: List[Dict[str, Any]]
    triggers: List[str]
    enabled: bool
    created_at: datetime


@register_tool
class AutomationTool(BaseTool):
    """Tool for automation operations."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="automation_tool",
            description="Task scheduling and workflow automation",
            category=ToolCategory.AUTOMATION,
            permissions=["automation_operations"],
            version="1.0.0"
        )
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.tasks_file = os.path.expanduser("~/.sysagent/tasks.json")
        self.workflows_file = os.path.expanduser("~/.sysagent/workflows.json")
        self._ensure_directories()
        self._load_data()
    
    def _ensure_directories(self):
        """Ensure automation directories exist."""
        os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.workflows_file), exist_ok=True)
    
    def _load_data(self):
        """Load tasks and workflows from files."""
        self.tasks = {}
        self.workflows = {}
        
        # Load tasks
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                    for task_id, task_data in data.items():
                        self.tasks[task_id] = ScheduledTask(**task_data)
            except:
                pass
        
        # Load workflows
        if os.path.exists(self.workflows_file):
            try:
                with open(self.workflows_file, 'r') as f:
                    data = json.load(f)
                    for workflow_id, workflow_data in data.items():
                        self.workflows[workflow_id] = Workflow(**workflow_data)
            except:
                pass
    
    def _save_data(self):
        """Save tasks and workflows to files."""
        # Save tasks
        tasks_data = {}
        for task_id, task in self.tasks.items():
            tasks_data[task_id] = {
                "id": task.id,
                "name": task.name,
                "command": task.command,
                "schedule": task.schedule,
                "enabled": task.enabled,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.next_run.isoformat() if task.next_run else None,
                "created_at": task.created_at.isoformat()
            }
        
        with open(self.tasks_file, 'w') as f:
            json.dump(tasks_data, f, indent=2)
        
        # Save workflows
        workflows_data = {}
        for workflow_id, workflow in self.workflows.items():
            workflows_data[workflow_id] = {
                "id": workflow.id,
                "name": workflow.name,
                "steps": workflow.steps,
                "triggers": workflow.triggers,
                "enabled": workflow.enabled,
                "created_at": workflow.created_at.isoformat()
            }
        
        with open(self.workflows_file, 'w') as f:
            json.dump(workflows_data, f, indent=2)
    
    def _execute(self, action: str, task_id: str = None, workflow_id: str = None,
                 name: str = None, command: str = None, schedule: str = None,
                 steps: List[Dict] = None, triggers: List[str] = None, **kwargs) -> ToolResult:
        """Execute automation action."""
        
        try:
            if action == "create_task":
                return self._create_task(name, command, schedule)
            elif action == "list_tasks":
                return self._list_tasks()
            elif action == "enable_task":
                return self._enable_task(task_id)
            elif action == "disable_task":
                return self._disable_task(task_id)
            elif action == "delete_task":
                return self._delete_task(task_id)
            elif action == "run_task":
                return self._run_task(task_id)
            elif action == "create_workflow":
                return self._create_workflow(name, steps, triggers)
            elif action == "list_workflows":
                return self._list_workflows()
            elif action == "run_workflow":
                return self._run_workflow(workflow_id)
            elif action == "enable_workflow":
                return self._enable_workflow(workflow_id)
            elif action == "disable_workflow":
                return self._disable_workflow(workflow_id)
            elif action == "delete_workflow":
                return self._delete_workflow(workflow_id)
            elif action == "monitor_tasks":
                return self._monitor_tasks()
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown action: {action}",
                    error=f"Unsupported action: {action}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Automation operation failed: {str(e)}",
                error=str(e)
            )
    
    def _create_task(self, name: str, command: str, schedule: str) -> ToolResult:
        """Create a new scheduled task."""
        try:
            if not name or not command or not schedule:
                return ToolResult(
                    success=False,
                    data={},
                    message="Name, command, and schedule are required",
                    error="Missing required parameters"
                )
            
            task_id = f"task_{int(time.time())}"
            now = datetime.now()
            
            # Parse schedule to determine next run
            next_run = self._parse_schedule(schedule, now)
            
            task = ScheduledTask(
                id=task_id,
                name=name,
                command=command,
                schedule=schedule,
                enabled=True,
                last_run=None,
                next_run=next_run,
                created_at=now
            )
            
            self.tasks[task_id] = task
            self._save_data()
            
            return ToolResult(
                success=True,
                data={
                    "task_id": task_id,
                    "task": {
                        "id": task.id,
                        "name": task.name,
                        "command": task.command,
                        "schedule": task.schedule,
                        "next_run": task.next_run.isoformat() if task.next_run else None
                    }
                },
                message=f"Task '{name}' created successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to create task: {str(e)}",
                error=str(e)
            )
    
    def _list_tasks(self) -> ToolResult:
        """List all scheduled tasks."""
        try:
            tasks_list = []
            for task in self.tasks.values():
                tasks_list.append({
                    "id": task.id,
                    "name": task.name,
                    "command": task.command,
                    "schedule": task.schedule,
                    "enabled": task.enabled,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "created_at": task.created_at.isoformat()
                })
            
            return ToolResult(
                success=True,
                data={
                    "tasks": tasks_list,
                    "total": len(tasks_list)
                },
                message=f"Found {len(tasks_list)} scheduled tasks"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list tasks: {str(e)}",
                error=str(e)
            )
    
    def _enable_task(self, task_id: str) -> ToolResult:
        """Enable a scheduled task."""
        try:
            if task_id not in self.tasks:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Task '{task_id}' not found",
                    error="Task not found"
                )
            
            self.tasks[task_id].enabled = True
            self._save_data()
            
            return ToolResult(
                success=True,
                data={"task_id": task_id},
                message=f"Task '{task_id}' enabled successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to enable task: {str(e)}",
                error=str(e)
            )
    
    def _disable_task(self, task_id: str) -> ToolResult:
        """Disable a scheduled task."""
        try:
            if task_id not in self.tasks:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Task '{task_id}' not found",
                    error="Task not found"
                )
            
            self.tasks[task_id].enabled = False
            self._save_data()
            
            return ToolResult(
                success=True,
                data={"task_id": task_id},
                message=f"Task '{task_id}' disabled successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to disable task: {str(e)}",
                error=str(e)
            )
    
    def _delete_task(self, task_id: str) -> ToolResult:
        """Delete a scheduled task."""
        try:
            if task_id not in self.tasks:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Task '{task_id}' not found",
                    error="Task not found"
                )
            
            task_name = self.tasks[task_id].name
            del self.tasks[task_id]
            self._save_data()
            
            return ToolResult(
                success=True,
                data={"task_id": task_id},
                message=f"Task '{task_name}' deleted successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to delete task: {str(e)}",
                error=str(e)
            )
    
    def _run_task(self, task_id: str) -> ToolResult:
        """Run a scheduled task immediately."""
        try:
            if task_id not in self.tasks:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Task '{task_id}' not found",
                    error="Task not found"
                )
            
            task = self.tasks[task_id]
            
            # Execute the command
            result = subprocess.run(
                task.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Update task status
            task.last_run = datetime.now()
            task.next_run = self._parse_schedule(task.schedule, task.last_run)
            self._save_data()
            
            return ToolResult(
                success=result.returncode == 0,
                data={
                    "task_id": task_id,
                    "command": task.command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time": datetime.now().isoformat()
                },
                message=f"Task '{task.name}' executed with return code {result.returncode}"
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={"task_id": task_id},
                message=f"Task '{task_id}' timed out after 5 minutes"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to run task: {str(e)}",
                error=str(e)
            )
    
    def _create_workflow(self, name: str, steps: List[Dict], triggers: List[str]) -> ToolResult:
        """Create a new automation workflow."""
        try:
            if not name or not steps:
                return ToolResult(
                    success=False,
                    data={},
                    message="Name and steps are required",
                    error="Missing required parameters"
                )
            
            workflow_id = f"workflow_{int(time.time())}"
            now = datetime.now()
            
            workflow = Workflow(
                id=workflow_id,
                name=name,
                steps=steps,
                triggers=triggers or [],
                enabled=True,
                created_at=now
            )
            
            self.workflows[workflow_id] = workflow
            self._save_data()
            
            return ToolResult(
                success=True,
                data={
                    "workflow_id": workflow_id,
                    "workflow": {
                        "id": workflow.id,
                        "name": workflow.name,
                        "steps": workflow.steps,
                        "triggers": workflow.triggers
                    }
                },
                message=f"Workflow '{name}' created successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to create workflow: {str(e)}",
                error=str(e)
            )
    
    def _list_workflows(self) -> ToolResult:
        """List all automation workflows."""
        try:
            workflows_list = []
            for workflow in self.workflows.values():
                workflows_list.append({
                    "id": workflow.id,
                    "name": workflow.name,
                    "steps": workflow.steps,
                    "triggers": workflow.triggers,
                    "enabled": workflow.enabled,
                    "created_at": workflow.created_at.isoformat()
                })
            
            return ToolResult(
                success=True,
                data={
                    "workflows": workflows_list,
                    "total": len(workflows_list)
                },
                message=f"Found {len(workflows_list)} automation workflows"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list workflows: {str(e)}",
                error=str(e)
            )
    
    def _run_workflow(self, workflow_id: str) -> ToolResult:
        """Run an automation workflow."""
        try:
            if workflow_id not in self.workflows:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Workflow '{workflow_id}' not found",
                    error="Workflow not found"
                )
            
            workflow = self.workflows[workflow_id]
            results = []
            
            for i, step in enumerate(workflow.steps):
                try:
                    step_type = step.get("type", "command")
                    step_data = step.get("data", {})
                    
                    if step_type == "command":
                        command = step_data.get("command", "")
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        results.append({
                            "step": i + 1,
                            "type": "command",
                            "command": command,
                            "success": result.returncode == 0,
                            "return_code": result.returncode,
                            "output": result.stdout,
                            "error": result.stderr
                        })
                    elif step_type == "delay":
                        delay = step_data.get("seconds", 1)
                        time.sleep(delay)
                        results.append({
                            "step": i + 1,
                            "type": "delay",
                            "seconds": delay,
                            "success": True
                        })
                    
                except Exception as e:
                    results.append({
                        "step": i + 1,
                        "type": step_type,
                        "success": False,
                        "error": str(e)
                    })
            
            return ToolResult(
                success=True,
                data={
                    "workflow_id": workflow_id,
                    "workflow_name": workflow.name,
                    "steps_executed": len(results),
                    "results": results
                },
                message=f"Workflow '{workflow.name}' executed successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to run workflow: {str(e)}",
                error=str(e)
            )
    
    def _enable_workflow(self, workflow_id: str) -> ToolResult:
        """Enable an automation workflow."""
        try:
            if workflow_id not in self.workflows:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Workflow '{workflow_id}' not found",
                    error="Workflow not found"
                )
            
            self.workflows[workflow_id].enabled = True
            self._save_data()
            
            return ToolResult(
                success=True,
                data={"workflow_id": workflow_id},
                message=f"Workflow '{workflow_id}' enabled successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to enable workflow: {str(e)}",
                error=str(e)
            )
    
    def _disable_workflow(self, workflow_id: str) -> ToolResult:
        """Disable an automation workflow."""
        try:
            if workflow_id not in self.workflows:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Workflow '{workflow_id}' not found",
                    error="Workflow not found"
                )
            
            self.workflows[workflow_id].enabled = False
            self._save_data()
            
            return ToolResult(
                success=True,
                data={"workflow_id": workflow_id},
                message=f"Workflow '{workflow_id}' disabled successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to disable workflow: {str(e)}",
                error=str(e)
            )
    
    def _delete_workflow(self, workflow_id: str) -> ToolResult:
        """Delete an automation workflow."""
        try:
            if workflow_id not in self.workflows:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Workflow '{workflow_id}' not found",
                    error="Workflow not found"
                )
            
            workflow_name = self.workflows[workflow_id].name
            del self.workflows[workflow_id]
            self._save_data()
            
            return ToolResult(
                success=True,
                data={"workflow_id": workflow_id},
                message=f"Workflow '{workflow_name}' deleted successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to delete workflow: {str(e)}",
                error=str(e)
            )
    
    def _monitor_tasks(self) -> ToolResult:
        """Monitor scheduled tasks for execution."""
        try:
            now = datetime.now()
            due_tasks = []
            
            for task in self.tasks.values():
                if task.enabled and task.next_run and task.next_run <= now:
                    due_tasks.append({
                        "id": task.id,
                        "name": task.name,
                        "command": task.command,
                        "next_run": task.next_run.isoformat()
                    })
            
            return ToolResult(
                success=True,
                data={
                    "due_tasks": due_tasks,
                    "total_due": len(due_tasks),
                    "total_tasks": len(self.tasks)
                },
                message=f"Task monitoring: {len(due_tasks)} tasks due for execution"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to monitor tasks: {str(e)}",
                error=str(e)
            )
    
    def _parse_schedule(self, schedule: str, base_time: datetime) -> datetime:
        """Parse schedule string to determine next run time."""
        try:
            if schedule.startswith("every "):
                # Parse "every X minutes/hours/days"
                parts = schedule.split()
                if len(parts) >= 3:
                    interval = int(parts[1])
                    unit = parts[2]
                    
                    if unit.startswith("minute"):
                        return base_time + timedelta(minutes=interval)
                    elif unit.startswith("hour"):
                        return base_time + timedelta(hours=interval)
                    elif unit.startswith("day"):
                        return base_time + timedelta(days=interval)
            
            # Default to 1 hour from now
            return base_time + timedelta(hours=1)
            
        except:
            # Default to 1 hour from now
            return base_time + timedelta(hours=1) 