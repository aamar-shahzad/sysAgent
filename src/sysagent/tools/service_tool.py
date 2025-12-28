"""
Service tool for SysAgent CLI - System service management.
"""

import subprocess
from typing import List, Dict, Any, Optional

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class ServiceTool(BaseTool):
    """Tool for system service management."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="service_tool",
            description="Manage system services - start, stop, restart, enable, disable",
            category=ToolCategory.SERVICE,
            permissions=["service_control", "system_control"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "list": self._list_services,
                "status": self._get_service_status,
                "start": self._start_service,
                "stop": self._stop_service,
                "restart": self._restart_service,
                "enable": self._enable_service,
                "disable": self._disable_service,
                "info": self._get_service_info,
                "logs": self._get_service_logs,
                "search": self._search_services,
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
                message=f"Service operation failed: {str(e)}",
                error=str(e)
            )

    def _list_services(self, **kwargs) -> ToolResult:
        """List all system services."""
        platform = detect_platform()
        services = []
        filter_status = kwargs.get("status")  # running, stopped, all
        
        try:
            if platform == Platform.LINUX:
                # Use systemctl
                result = subprocess.run(
                    ["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--plain"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.split()
                        if len(parts) >= 4:
                            service = {
                                "name": parts[0].replace(".service", ""),
                                "load": parts[1],
                                "active": parts[2],
                                "sub": parts[3],
                                "description": " ".join(parts[4:]) if len(parts) > 4 else ""
                            }
                            
                            if filter_status:
                                if filter_status == "running" and service["active"] != "active":
                                    continue
                                if filter_status == "stopped" and service["active"] != "inactive":
                                    continue
                            
                            services.append(service)
                            
            elif platform == Platform.MACOS:
                # Use launchctl
                result = subprocess.run(
                    ["launchctl", "list"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            services.append({
                                "name": parts[2],
                                "pid": parts[0] if parts[0] != "-" else None,
                                "status": "running" if parts[0] != "-" else "stopped",
                                "exit_code": parts[1]
                            })
                            
            elif platform == Platform.WINDOWS:
                # Use sc query
                result = subprocess.run(
                    ["sc", "query", "state=", "all"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    current_service = {}
                    for line in result.stdout.strip().split('\n'):
                        line = line.strip()
                        if line.startswith("SERVICE_NAME:"):
                            if current_service:
                                services.append(current_service)
                            current_service = {"name": line.split(":", 1)[1].strip()}
                        elif line.startswith("DISPLAY_NAME:"):
                            current_service["display_name"] = line.split(":", 1)[1].strip()
                        elif line.startswith("STATE"):
                            state_parts = line.split()
                            if len(state_parts) >= 4:
                                current_service["state"] = state_parts[3]
                    if current_service:
                        services.append(current_service)
            
            return ToolResult(
                success=True,
                data={"services": services[:100], "count": len(services)},
                message=f"Found {len(services)} services"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list services: {str(e)}",
                error=str(e)
            )

    def _get_service_status(self, **kwargs) -> ToolResult:
        """Get status of a specific service."""
        name = kwargs.get("name") or kwargs.get("service")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                result = subprocess.run(
                    ["systemctl", "status", name, "--no-pager"],
                    capture_output=True,
                    text=True
                )
                
                # Parse status
                status_info = {
                    "name": name,
                    "raw_output": result.stdout[:500]
                }
                
                for line in result.stdout.split('\n'):
                    if 'Active:' in line:
                        status_info["active"] = "active" in line.lower()
                        status_info["status_line"] = line.strip()
                    elif 'Main PID:' in line:
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if p == "PID:":
                                status_info["pid"] = parts[i+1] if i+1 < len(parts) else None
                
                return ToolResult(
                    success=True,
                    data=status_info,
                    message=f"Service {name}: {'active' if status_info.get('active') else 'inactive'}"
                )
                
            elif platform == Platform.MACOS:
                result = subprocess.run(
                    ["launchctl", "list", name],
                    capture_output=True,
                    text=True
                )
                
                return ToolResult(
                    success=result.returncode == 0,
                    data={"name": name, "output": result.stdout},
                    message=f"Service {name} status retrieved" if result.returncode == 0 else f"Service {name} not found"
                )
                
            elif platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["sc", "query", name],
                    capture_output=True,
                    text=True
                )
                
                status_info = {"name": name}
                for line in result.stdout.split('\n'):
                    if 'STATE' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            status_info["state"] = parts[3]
                
                return ToolResult(
                    success=result.returncode == 0,
                    data=status_info,
                    message=f"Service {name}: {status_info.get('state', 'unknown')}"
                )
            
            return ToolResult(
                success=False,
                data={},
                message="Platform not supported",
                error="Unsupported platform"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get status: {str(e)}",
                error=str(e)
            )

    def _start_service(self, **kwargs) -> ToolResult:
        """Start a service."""
        name = kwargs.get("name") or kwargs.get("service")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                result = subprocess.run(
                    ["sudo", "systemctl", "start", name],
                    capture_output=True,
                    text=True
                )
            elif platform == Platform.MACOS:
                result = subprocess.run(
                    ["sudo", "launchctl", "start", name],
                    capture_output=True,
                    text=True
                )
            elif platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["sc", "start", name],
                    capture_output=True,
                    text=True
                )
            else:
                return ToolResult(success=False, data={}, message="Platform not supported")
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"name": name, "action": "start"},
                    message=f"Service {name} started successfully"
                )
            else:
                return ToolResult(
                    success=False,
                    data={"error": result.stderr},
                    message=f"Failed to start {name}",
                    error=result.stderr
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to start service: {str(e)}",
                error=str(e)
            )

    def _stop_service(self, **kwargs) -> ToolResult:
        """Stop a service."""
        name = kwargs.get("name") or kwargs.get("service")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                result = subprocess.run(
                    ["sudo", "systemctl", "stop", name],
                    capture_output=True,
                    text=True
                )
            elif platform == Platform.MACOS:
                result = subprocess.run(
                    ["sudo", "launchctl", "stop", name],
                    capture_output=True,
                    text=True
                )
            elif platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["sc", "stop", name],
                    capture_output=True,
                    text=True
                )
            else:
                return ToolResult(success=False, data={}, message="Platform not supported")
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"name": name, "action": "stop"},
                    message=f"Service {name} stopped successfully"
                )
            else:
                return ToolResult(
                    success=False,
                    data={"error": result.stderr},
                    message=f"Failed to stop {name}",
                    error=result.stderr
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to stop service: {str(e)}",
                error=str(e)
            )

    def _restart_service(self, **kwargs) -> ToolResult:
        """Restart a service."""
        name = kwargs.get("name") or kwargs.get("service")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                result = subprocess.run(
                    ["sudo", "systemctl", "restart", name],
                    capture_output=True,
                    text=True
                )
            elif platform == Platform.MACOS:
                # Stop then start
                subprocess.run(["sudo", "launchctl", "stop", name], capture_output=True)
                result = subprocess.run(
                    ["sudo", "launchctl", "start", name],
                    capture_output=True,
                    text=True
                )
            elif platform == Platform.WINDOWS:
                subprocess.run(["sc", "stop", name], capture_output=True)
                import time
                time.sleep(2)
                result = subprocess.run(
                    ["sc", "start", name],
                    capture_output=True,
                    text=True
                )
            else:
                return ToolResult(success=False, data={}, message="Platform not supported")
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"name": name, "action": "restart"},
                    message=f"Service {name} restarted successfully"
                )
            else:
                return ToolResult(
                    success=False,
                    data={"error": result.stderr},
                    message=f"Failed to restart {name}",
                    error=result.stderr
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to restart service: {str(e)}",
                error=str(e)
            )

    def _enable_service(self, **kwargs) -> ToolResult:
        """Enable a service to start on boot."""
        name = kwargs.get("name") or kwargs.get("service")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                result = subprocess.run(
                    ["sudo", "systemctl", "enable", name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={"name": name},
                        message=f"Service {name} enabled for autostart"
                    )
            elif platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["sc", "config", name, "start=", "auto"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={"name": name},
                        message=f"Service {name} set to automatic start"
                    )
            
            return ToolResult(
                success=False,
                data={},
                message="Enable not supported or failed",
                error="Operation failed"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to enable service: {str(e)}",
                error=str(e)
            )

    def _disable_service(self, **kwargs) -> ToolResult:
        """Disable a service from starting on boot."""
        name = kwargs.get("name") or kwargs.get("service")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                result = subprocess.run(
                    ["sudo", "systemctl", "disable", name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={"name": name},
                        message=f"Service {name} disabled from autostart"
                    )
            elif platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["sc", "config", name, "start=", "demand"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={"name": name},
                        message=f"Service {name} set to manual start"
                    )
            
            return ToolResult(
                success=False,
                data={},
                message="Disable not supported or failed",
                error="Operation failed"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to disable service: {str(e)}",
                error=str(e)
            )

    def _get_service_info(self, **kwargs) -> ToolResult:
        """Get detailed information about a service."""
        name = kwargs.get("name") or kwargs.get("service")
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        info = {"name": name}
        
        try:
            if platform == Platform.LINUX:
                result = subprocess.run(
                    ["systemctl", "show", name, "--no-pager"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key in ['Description', 'LoadState', 'ActiveState', 'SubState', 
                                       'MainPID', 'ExecStart', 'User', 'MemoryCurrent']:
                                info[key] = value
                
            elif platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["sc", "qc", name],
                    capture_output=True,
                    text=True
                )
                info["config"] = result.stdout
            
            return ToolResult(
                success=True,
                data=info,
                message=f"Retrieved info for service {name}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get service info: {str(e)}",
                error=str(e)
            )

    def _get_service_logs(self, **kwargs) -> ToolResult:
        """Get logs for a service."""
        name = kwargs.get("name") or kwargs.get("service")
        lines = kwargs.get("lines", 50)
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing name"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                result = subprocess.run(
                    ["journalctl", "-u", name, "-n", str(lines), "--no-pager"],
                    capture_output=True,
                    text=True
                )
                
                return ToolResult(
                    success=True,
                    data={"name": name, "logs": result.stdout},
                    message=f"Retrieved last {lines} log entries for {name}"
                )
            
            return ToolResult(
                success=False,
                data={},
                message="Service logs not available on this platform",
                error="Unsupported"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get logs: {str(e)}",
                error=str(e)
            )

    def _search_services(self, **kwargs) -> ToolResult:
        """Search for services by name pattern."""
        query = kwargs.get("query") or kwargs.get("pattern")
        
        if not query:
            return ToolResult(
                success=False,
                data={},
                message="No search query provided",
                error="Missing query"
            )
        
        # Get all services and filter
        result = self._list_services()
        if not result.success:
            return result
        
        services = result.data.get("services", [])
        matching = [s for s in services if query.lower() in s.get("name", "").lower()]
        
        return ToolResult(
            success=True,
            data={"services": matching, "count": len(matching)},
            message=f"Found {len(matching)} services matching '{query}'"
        )

    def get_usage_examples(self) -> List[str]:
        return [
            "List services: service_tool --action list",
            "List running: service_tool --action list --status running",
            "Get status: service_tool --action status --name nginx",
            "Start service: service_tool --action start --name nginx",
            "Stop service: service_tool --action stop --name nginx",
            "Restart service: service_tool --action restart --name nginx",
            "View logs: service_tool --action logs --name nginx --lines 100",
            "Search: service_tool --action search --query docker",
        ]
