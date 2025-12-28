"""
Workflow tool for SysAgent CLI - Create and run multi-step automated workflows.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, ToolExecutor, register_tool
from ..types import ToolCategory


@register_tool
class WorkflowTool(BaseTool):
    """Tool for creating and running multi-step workflows."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="workflow_tool",
            description="Create, save, and run multi-step automated workflows",
            category=ToolCategory.AUTOMATION,
            permissions=["workflow_execution"],
            version="1.0.0"
        )

    def _get_workflows_dir(self) -> Path:
        """Get workflows directory."""
        path = Path.home() / ".sysagent" / "workflows"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "create": self._create_workflow,
                "run": self._run_workflow,
                "list": self._list_workflows,
                "get": self._get_workflow,
                "delete": self._delete_workflow,
                "add_step": self._add_step,
                "templates": self._get_templates,
                "create_from_template": self._create_from_template,
            }
            
            if action in actions:
                return actions[action](**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={"available_actions": list(actions.keys())},
                    message=f"Unknown action: {action}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Workflow operation failed: {str(e)}",
                error=str(e)
            )

    def _create_workflow(self, **kwargs) -> ToolResult:
        """Create a new workflow."""
        name = kwargs.get("name")
        description = kwargs.get("description", "")
        steps = kwargs.get("steps", [])
        trigger = kwargs.get("trigger")  # manual, schedule, event
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="Workflow name required"
            )
        
        workflow = {
            "name": name,
            "description": description,
            "steps": steps,
            "trigger": trigger or "manual",
            "created": datetime.now().isoformat(),
            "last_run": None,
            "run_count": 0,
            "enabled": True
        }
        
        # Save workflow
        workflow_file = self._get_workflows_dir() / f"{name}.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        return ToolResult(
            success=True,
            data=workflow,
            message=f"Workflow '{name}' created with {len(steps)} steps"
        )

    def _add_step(self, **kwargs) -> ToolResult:
        """Add a step to an existing workflow."""
        workflow_name = kwargs.get("workflow") or kwargs.get("name")
        step = kwargs.get("step", {})
        tool = kwargs.get("tool")
        action = kwargs.get("action")
        params = kwargs.get("params", {})
        
        if not workflow_name:
            return ToolResult(success=False, data={}, message="Workflow name required")
        
        workflow_file = self._get_workflows_dir() / f"{workflow_name}.json"
        if not workflow_file.exists():
            return ToolResult(success=False, data={}, message=f"Workflow '{workflow_name}' not found")
        
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
        
        # Create step from parameters
        if tool and action:
            step = {
                "tool": tool,
                "action": action,
                "params": params,
                "name": f"{tool}.{action}"
            }
        
        if step:
            workflow["steps"].append(step)
            with open(workflow_file, 'w') as f:
                json.dump(workflow, f, indent=2)
            
            return ToolResult(
                success=True,
                data={"step": step, "total_steps": len(workflow["steps"])},
                message=f"Step added to workflow '{workflow_name}'"
            )
        
        return ToolResult(success=False, data={}, message="No step provided")

    def _run_workflow(self, **kwargs) -> ToolResult:
        """Run a workflow."""
        name = kwargs.get("name") or kwargs.get("workflow")
        executor = kwargs.get("executor")  # ToolExecutor instance
        dry_run = kwargs.get("dry_run", False)
        
        if not name:
            return ToolResult(success=False, data={}, message="Workflow name required")
        
        workflow_file = self._get_workflows_dir() / f"{name}.json"
        if not workflow_file.exists():
            return ToolResult(success=False, data={}, message=f"Workflow '{name}' not found")
        
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
        
        steps = workflow.get("steps", [])
        results = []
        
        for i, step in enumerate(steps):
            step_result = {
                "step": i + 1,
                "name": step.get("name", f"Step {i+1}"),
                "tool": step.get("tool"),
                "action": step.get("action"),
            }
            
            if dry_run:
                step_result["status"] = "skipped (dry run)"
                results.append(step_result)
                continue
            
            if executor:
                try:
                    tool_result = executor.execute_tool(
                        step["tool"],
                        action=step["action"],
                        **step.get("params", {})
                    )
                    step_result["status"] = "success" if tool_result.success else "failed"
                    step_result["output"] = tool_result.message
                except Exception as e:
                    step_result["status"] = "error"
                    step_result["error"] = str(e)
            else:
                step_result["status"] = "skipped (no executor)"
            
            results.append(step_result)
        
        # Update workflow stats
        workflow["last_run"] = datetime.now().isoformat()
        workflow["run_count"] = workflow.get("run_count", 0) + 1
        with open(workflow_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        successful = sum(1 for r in results if r.get("status") == "success")
        
        return ToolResult(
            success=True,
            data={"workflow": name, "results": results, "successful": successful, "total": len(steps)},
            message=f"Workflow '{name}' completed: {successful}/{len(steps)} steps successful"
        )

    def _list_workflows(self, **kwargs) -> ToolResult:
        """List all workflows."""
        workflows = []
        
        for f in self._get_workflows_dir().glob("*.json"):
            try:
                with open(f, 'r') as file:
                    wf = json.load(file)
                    workflows.append({
                        "name": wf.get("name"),
                        "description": wf.get("description", ""),
                        "steps": len(wf.get("steps", [])),
                        "trigger": wf.get("trigger", "manual"),
                        "run_count": wf.get("run_count", 0),
                        "enabled": wf.get("enabled", True)
                    })
            except:
                continue
        
        return ToolResult(
            success=True,
            data={"workflows": workflows, "count": len(workflows)},
            message=f"Found {len(workflows)} workflows"
        )

    def _get_workflow(self, **kwargs) -> ToolResult:
        """Get workflow details."""
        name = kwargs.get("name")
        
        if not name:
            return ToolResult(success=False, data={}, message="Workflow name required")
        
        workflow_file = self._get_workflows_dir() / f"{name}.json"
        if not workflow_file.exists():
            return ToolResult(success=False, data={}, message=f"Workflow '{name}' not found")
        
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
        
        return ToolResult(
            success=True,
            data=workflow,
            message=f"Workflow '{name}' has {len(workflow.get('steps', []))} steps"
        )

    def _delete_workflow(self, **kwargs) -> ToolResult:
        """Delete a workflow."""
        name = kwargs.get("name")
        
        if not name:
            return ToolResult(success=False, data={}, message="Workflow name required")
        
        workflow_file = self._get_workflows_dir() / f"{name}.json"
        if workflow_file.exists():
            workflow_file.unlink()
            return ToolResult(success=True, data={"name": name}, message=f"Workflow '{name}' deleted")
        
        return ToolResult(success=False, data={}, message=f"Workflow '{name}' not found")

    def _get_templates(self, **kwargs) -> ToolResult:
        """Get available workflow templates."""
        templates = {
            "morning_routine": {
                "name": "Morning Routine",
                "description": "Start your day with system checks and app launches",
                "steps": [
                    {"tool": "system_info_tool", "action": "overview", "params": {}, "name": "System Check"},
                    {"tool": "browser_tool", "action": "open", "params": {"url": "https://mail.google.com"}, "name": "Open Email"},
                    {"tool": "browser_tool", "action": "open", "params": {"url": "https://calendar.google.com"}, "name": "Open Calendar"},
                    {"tool": "notification_tool", "action": "send", "params": {"title": "Good Morning!", "message": "Your system is ready"}, "name": "Notification"}
                ]
            },
            "dev_setup": {
                "name": "Development Setup",
                "description": "Set up development environment",
                "steps": [
                    {"tool": "app_tool", "action": "launch", "params": {"app_name": "Visual Studio Code"}, "name": "Open VS Code"},
                    {"tool": "app_tool", "action": "launch", "params": {"app_name": "Terminal"}, "name": "Open Terminal"},
                    {"tool": "browser_tool", "action": "open", "params": {"url": "https://github.com"}, "name": "Open GitHub"},
                    {"tool": "git_tool", "action": "status", "params": {}, "name": "Git Status"}
                ]
            },
            "system_maintenance": {
                "name": "System Maintenance",
                "description": "Run system maintenance tasks",
                "steps": [
                    {"tool": "file_tool", "action": "cleanup", "params": {"path": "/tmp"}, "name": "Clean Temp Files"},
                    {"tool": "system_info_tool", "action": "disk", "params": {}, "name": "Check Disk Space"},
                    {"tool": "package_manager_tool", "action": "update", "params": {}, "name": "Update Packages"},
                    {"tool": "notification_tool", "action": "send", "params": {"title": "Maintenance Complete", "message": "System maintenance finished"}, "name": "Notification"}
                ]
            },
            "end_of_day": {
                "name": "End of Day",
                "description": "Wrap up your work day",
                "steps": [
                    {"tool": "git_tool", "action": "status", "params": {}, "name": "Check Git Status"},
                    {"tool": "document_tool", "action": "create_note", "params": {"title": "Daily Summary", "content": "Work completed today..."}, "name": "Create Summary"},
                    {"tool": "browser_tool", "action": "close", "params": {"browser": "all"}, "name": "Close Browsers"},
                    {"tool": "notification_tool", "action": "send", "params": {"title": "Day Complete", "message": "Great work today!"}, "name": "Notification"}
                ]
            },
            "backup_workflow": {
                "name": "Backup Important Files",
                "description": "Backup important files and folders",
                "steps": [
                    {"tool": "file_tool", "action": "list", "params": {"path": "~/Documents"}, "name": "List Documents"},
                    {"tool": "file_tool", "action": "copy", "params": {"source": "~/Documents", "destination": "~/Backups"}, "name": "Backup Documents"},
                    {"tool": "notification_tool", "action": "send", "params": {"title": "Backup Complete", "message": "Files backed up successfully"}, "name": "Notification"}
                ]
            }
        }
        
        return ToolResult(
            success=True,
            data={"templates": list(templates.keys()), "details": templates},
            message=f"Found {len(templates)} workflow templates"
        )

    def _create_from_template(self, **kwargs) -> ToolResult:
        """Create a workflow from a template."""
        template = kwargs.get("template")
        name = kwargs.get("name")
        
        if not template:
            return ToolResult(success=False, data={}, message="Template name required")
        
        templates_result = self._get_templates()
        templates = templates_result.data.get("details", {})
        
        if template not in templates:
            return ToolResult(
                success=False,
                data={"available": list(templates.keys())},
                message=f"Template '{template}' not found"
            )
        
        template_data = templates[template]
        workflow_name = name or template_data["name"]
        
        return self._create_workflow(
            name=workflow_name,
            description=template_data["description"],
            steps=template_data["steps"]
        )

    def get_usage_examples(self) -> List[str]:
        return [
            "Create workflow: workflow_tool --action create --name 'my_workflow'",
            "Add step: workflow_tool --action add_step --workflow 'my_workflow' --tool 'browser_tool' --action 'open' --params '{\"url\": \"google.com\"}'",
            "Run workflow: workflow_tool --action run --name 'my_workflow'",
            "List workflows: workflow_tool --action list",
            "Get templates: workflow_tool --action templates",
            "Create from template: workflow_tool --action create_from_template --template 'morning_routine'",
        ]
