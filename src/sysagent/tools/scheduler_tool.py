"""
Scheduler tool for SysAgent CLI - Task scheduling and automation.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class SchedulerTool(BaseTool):
    """Tool for task scheduling and cron job management."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="scheduler_tool",
            description="Schedule tasks, manage cron jobs, and automate recurring operations",
            category=ToolCategory.SCHEDULER,
            permissions=["scheduler", "system_control"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "list": self._list_scheduled_tasks,
                "add": self._add_task,
                "remove": self._remove_task,
                "enable": self._enable_task,
                "disable": self._disable_task,
                "run_now": self._run_task_now,
                "status": self._get_scheduler_status,
                "create_reminder": self._create_reminder,
                "list_reminders": self._list_reminders,
            }
            
            if action in actions:
                return actions[action](**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown action: {action}",
                    error=f"Supported actions: {list(actions.keys())}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Scheduler operation failed: {str(e)}",
                error=str(e)
            )

    def _list_scheduled_tasks(self, **kwargs) -> ToolResult:
        """List all scheduled tasks."""
        platform = detect_platform()
        tasks = []
        
        try:
            if platform == Platform.LINUX:
                # List crontab entries
                result = subprocess.run(
                    ["crontab", "-l"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line and not line.startswith('#'):
                            tasks.append({
                                "type": "cron",
                                "schedule": line[:line.rfind(' ')],
                                "command": line[line.rfind(' ')+1:] if ' ' in line else line,
                                "raw": line
                            })
                
                # Also check systemd timers
                result = subprocess.run(
                    ["systemctl", "list-timers", "--all", "--no-pager"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 5:
                                tasks.append({
                                    "type": "systemd_timer",
                                    "next": parts[0] + " " + parts[1] if len(parts) > 1 else "N/A",
                                    "unit": parts[-1] if parts else "unknown"
                                })
                                
            elif platform == Platform.MACOS:
                # List launchd jobs
                result = subprocess.run(
                    ["launchctl", "list"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            tasks.append({
                                "type": "launchd",
                                "pid": parts[0],
                                "status": parts[1],
                                "label": parts[2]
                            })
                
                # Also check crontab
                result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line and not line.startswith('#'):
                            tasks.append({"type": "cron", "raw": line})
                            
            elif platform == Platform.WINDOWS:
                # Use schtasks
                result = subprocess.run(
                    ["schtasks", "/query", "/fo", "LIST"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    current_task = {}
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            current_task[key.strip()] = value.strip()
                        elif not line.strip() and current_task:
                            tasks.append({"type": "windows_task", **current_task})
                            current_task = {}
            
            return ToolResult(
                success=True,
                data={"tasks": tasks[:50], "count": len(tasks)},
                message=f"Found {len(tasks)} scheduled tasks"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list tasks: {str(e)}",
                error=str(e)
            )

    def _add_task(self, **kwargs) -> ToolResult:
        """Add a new scheduled task."""
        name = kwargs.get("name")
        command = kwargs.get("command")
        schedule = kwargs.get("schedule")  # cron format or keywords
        
        if not command:
            return ToolResult(
                success=False,
                data={},
                message="No command provided",
                error="Missing command"
            )
        
        if not schedule:
            return ToolResult(
                success=False,
                data={},
                message="No schedule provided",
                error="Missing schedule. Use cron format or keywords like 'hourly', 'daily', 'weekly'"
            )
        
        # Convert keywords to cron format
        schedule_map = {
            "hourly": "0 * * * *",
            "daily": "0 0 * * *",
            "weekly": "0 0 * * 0",
            "monthly": "0 0 1 * *",
            "midnight": "0 0 * * *",
            "noon": "0 12 * * *",
        }
        
        cron_schedule = schedule_map.get(schedule.lower(), schedule)
        
        platform = detect_platform()
        
        try:
            if platform in [Platform.LINUX, Platform.MACOS]:
                # Add to crontab
                result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
                existing = result.stdout if result.returncode == 0 else ""
                
                new_entry = f"{cron_schedule} {command}"
                if name:
                    new_entry = f"# {name}\n{new_entry}"
                
                new_crontab = existing.strip() + "\n" + new_entry + "\n"
                
                process = subprocess.Popen(
                    ["crontab", "-"],
                    stdin=subprocess.PIPE,
                    text=True
                )
                process.communicate(new_crontab)
                
                if process.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={"name": name, "schedule": cron_schedule, "command": command},
                        message=f"Task '{name or command}' scheduled successfully"
                    )
                    
            elif platform == Platform.WINDOWS:
                # Use schtasks
                cmd = [
                    "schtasks", "/create",
                    "/tn", name or "SysAgentTask",
                    "/tr", command,
                    "/sc", self._convert_to_windows_schedule(schedule)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={"name": name, "command": command},
                        message=f"Task '{name}' scheduled successfully"
                    )
            
            return ToolResult(
                success=False,
                data={},
                message="Failed to add scheduled task",
                error="Scheduler returned error"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to add task: {str(e)}",
                error=str(e)
            )

    def _remove_task(self, **kwargs) -> ToolResult:
        """Remove a scheduled task."""
        name = kwargs.get("name")
        pattern = kwargs.get("pattern")
        
        if not name and not pattern:
            return ToolResult(
                success=False,
                data={},
                message="No task name or pattern provided",
                error="Missing name or pattern"
            )
        
        return ToolResult(
            success=False,
            data={},
            message="Task removal requires manual confirmation. Use 'crontab -e' or Task Scheduler.",
            error="Safety restriction"
        )

    def _enable_task(self, **kwargs) -> ToolResult:
        """Enable a disabled task."""
        name = kwargs.get("name")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No task name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        if platform == Platform.WINDOWS:
            result = subprocess.run(
                ["schtasks", "/change", "/tn", name, "/enable"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"name": name},
                    message=f"Task '{name}' enabled"
                )
        
        return ToolResult(
            success=False,
            data={},
            message="Enable not supported or task not found",
            error="Operation failed"
        )

    def _disable_task(self, **kwargs) -> ToolResult:
        """Disable a task."""
        name = kwargs.get("name")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No task name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        if platform == Platform.WINDOWS:
            result = subprocess.run(
                ["schtasks", "/change", "/tn", name, "/disable"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"name": name},
                    message=f"Task '{name}' disabled"
                )
        
        return ToolResult(
            success=False,
            data={},
            message="Disable not supported or task not found",
            error="Operation failed"
        )

    def _run_task_now(self, **kwargs) -> ToolResult:
        """Run a scheduled task immediately."""
        name = kwargs.get("name")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No task name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        if platform == Platform.WINDOWS:
            result = subprocess.run(
                ["schtasks", "/run", "/tn", name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"name": name},
                    message=f"Task '{name}' started"
                )
        
        return ToolResult(
            success=False,
            data={},
            message="Run now not supported or task not found",
            error="Operation failed"
        )

    def _get_scheduler_status(self, **kwargs) -> ToolResult:
        """Get scheduler service status."""
        platform = detect_platform()
        status = {"platform": platform.value}
        
        try:
            if platform == Platform.LINUX:
                # Check cron service
                result = subprocess.run(
                    ["systemctl", "is-active", "cron"],
                    capture_output=True,
                    text=True
                )
                status["cron_service"] = result.stdout.strip()
                
            elif platform == Platform.MACOS:
                status["launchd"] = "active"  # Always active on macOS
                
            elif platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["sc", "query", "Schedule"],
                    capture_output=True,
                    text=True
                )
                status["task_scheduler"] = "running" if "RUNNING" in result.stdout else "stopped"
            
            return ToolResult(
                success=True,
                data=status,
                message=f"Scheduler status: {status}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get status: {str(e)}",
                error=str(e)
            )

    def _create_reminder(self, **kwargs) -> ToolResult:
        """Create a simple reminder."""
        message = kwargs.get("message")
        time_str = kwargs.get("time")  # e.g., "5m", "1h", "tomorrow 9am"
        
        if not message:
            return ToolResult(
                success=False,
                data={},
                message="No reminder message provided",
                error="Missing message"
            )
        
        # Save reminder to file
        reminders_file = Path.home() / ".sysagent" / "reminders.json"
        reminders_file.parent.mkdir(parents=True, exist_ok=True)
        
        reminders = []
        if reminders_file.exists():
            try:
                with open(reminders_file, 'r') as f:
                    reminders = json.load(f)
            except:
                pass
        
        reminder = {
            "id": len(reminders) + 1,
            "message": message,
            "time": time_str,
            "created": datetime.now().isoformat(),
            "status": "pending"
        }
        reminders.append(reminder)
        
        with open(reminders_file, 'w') as f:
            json.dump(reminders, f, indent=2)
        
        return ToolResult(
            success=True,
            data=reminder,
            message=f"Reminder created: '{message}'"
        )

    def _list_reminders(self, **kwargs) -> ToolResult:
        """List all reminders."""
        reminders_file = Path.home() / ".sysagent" / "reminders.json"
        
        if not reminders_file.exists():
            return ToolResult(
                success=True,
                data={"reminders": [], "count": 0},
                message="No reminders found"
            )
        
        try:
            with open(reminders_file, 'r') as f:
                reminders = json.load(f)
            
            return ToolResult(
                success=True,
                data={"reminders": reminders, "count": len(reminders)},
                message=f"Found {len(reminders)} reminders"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list reminders: {str(e)}",
                error=str(e)
            )

    def _convert_to_windows_schedule(self, schedule: str) -> str:
        """Convert schedule keyword to Windows schedule type."""
        schedule_map = {
            "hourly": "HOURLY",
            "daily": "DAILY",
            "weekly": "WEEKLY",
            "monthly": "MONTHLY",
            "once": "ONCE",
            "onstart": "ONSTART",
            "onlogon": "ONLOGON",
        }
        return schedule_map.get(schedule.lower(), "DAILY")

    def get_usage_examples(self) -> List[str]:
        return [
            "List tasks: scheduler_tool --action list",
            "Add daily task: scheduler_tool --action add --name 'backup' --command 'backup.sh' --schedule daily",
            "Create reminder: scheduler_tool --action create_reminder --message 'Meeting' --time '1h'",
            "Get status: scheduler_tool --action status",
        ]
