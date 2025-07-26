"""
System control tool for SysAgent CLI.
"""

import subprocess
import platform
import os
import time
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory, PermissionLevel


@dataclass
class ServiceInfo:
    """Information about a system service."""
    name: str
    status: str
    description: str
    pid: int
    memory_usage: float
    cpu_usage: float


@register_tool
class SystemControlTool(BaseTool):
    """Tool for system control operations."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="system_control_tool",
            description="System control and service management",
            category=ToolCategory.SYSTEM,
            permissions=["system_control"],
            version="1.0.0"
        )
    
    def _execute(self, action: str, service_name: str = None, user_name: str = None,
                 command: str = None, timeout: int = 30, **kwargs) -> ToolResult:
        """Execute system control action."""
        
        try:
            if action == "service_list":
                return self._list_services()
            elif action == "service_start":
                return self._start_service(service_name)
            elif action == "service_stop":
                return self._stop_service(service_name)
            elif action == "service_restart":
                return self._restart_service(service_name)
            elif action == "service_status":
                return self._get_service_status(service_name)
            elif action == "service_enable":
                return self._enable_service(service_name)
            elif action == "service_disable":
                return self._disable_service(service_name)
            elif action == "user_list":
                return self._list_users()
            elif action == "user_info":
                return self._get_user_info(user_name)
            elif action == "system_info":
                return self._get_system_info()
            elif action == "power_off":
                return self._power_off()
            elif action == "reboot":
                return self._reboot()
            elif action == "sleep":
                return self._sleep()
            elif action == "execute_command":
                return self._execute_command(command, timeout)
            elif action == "system_update":
                return self._system_update()
            elif action == "disk_cleanup":
                return self._disk_cleanup()
            elif action == "log_analysis":
                return self._analyze_logs()
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
                message=f"System control operation failed: {str(e)}",
                error=str(e)
            )
    
    def _list_services(self) -> ToolResult:
        """List system services."""
        try:
            services = []
            
            if platform.system().lower() == "windows":
                # Windows services
                cmd = ["sc", "query", "type=", "service", "state=", "all"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    current_service = {}
                    
                    for line in lines:
                        line = line.strip()
                        if line.startswith('SERVICE_NAME:'):
                            if current_service:
                                services.append(current_service)
                            current_service = {'name': line.split(':', 1)[1].strip()}
                        elif line.startswith('DISPLAY_NAME:'):
                            current_service['display_name'] = line.split(':', 1)[1].strip()
                        elif line.startswith('STATE:'):
                            current_service['status'] = line.split(':', 1)[1].strip()
                        elif line.startswith('START_TYPE:'):
                            current_service['start_type'] = line.split(':', 1)[1].strip()
                    
                    if current_service:
                        services.append(current_service)
            else:
                # Unix/Linux services using systemctl
                try:
                    cmd = ["systemctl", "list-units", "--type=service", "--all", "--no-pager"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines[1:]:  # Skip header
                            if line.strip() and not line.startswith('●'):
                                parts = line.split()
                                if len(parts) >= 4:
                                    services.append({
                                        'name': parts[0],
                                        'load': parts[1],
                                        'active': parts[2],
                                        'sub': parts[3],
                                        'description': ' '.join(parts[4:]) if len(parts) > 4 else ''
                                    })
                except FileNotFoundError:
                    # Fallback to service command
                    cmd = ["service", "--status-all"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if line.strip():
                                parts = line.split()
                                if len(parts) >= 2:
                                    status = parts[0]
                                    name = parts[1]
                                    services.append({
                                        'name': name,
                                        'status': status,
                                        'description': ' '.join(parts[2:]) if len(parts) > 2 else ''
                                    })
            
            return ToolResult(
                success=True,
                data={
                    "services": services,
                    "total": len(services),
                    "platform": platform.system()
                },
                message=f"Found {len(services)} system services"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list services: {str(e)}",
                error=str(e)
            )
    
    def _start_service(self, service_name: str) -> ToolResult:
        """Start a system service."""
        try:
            if not service_name:
                return ToolResult(
                    success=False,
                    data={},
                    message="Service name is required",
                    error="Missing service name"
                )
            
            if platform.system().lower() == "windows":
                cmd = ["sc", "start", service_name]
            else:
                cmd = ["systemctl", "start", service_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"service": service_name, "action": "started"},
                    message=f"Service {service_name} started successfully"
                )
            else:
                return ToolResult(
                    success=False,
                    data={
                        "service": service_name,
                        "error": result.stderr,
                        "return_code": result.returncode
                    },
                    message=f"Failed to start service {service_name}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to start service {service_name}: {str(e)}",
                error=str(e)
            )
    
    def _stop_service(self, service_name: str) -> ToolResult:
        """Stop a system service."""
        try:
            if not service_name:
                return ToolResult(
                    success=False,
                    data={},
                    message="Service name is required",
                    error="Missing service name"
                )
            
            if platform.system().lower() == "windows":
                cmd = ["sc", "stop", service_name]
            else:
                cmd = ["systemctl", "stop", service_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"service": service_name, "action": "stopped"},
                    message=f"Service {service_name} stopped successfully"
                )
            else:
                return ToolResult(
                    success=False,
                    data={
                        "service": service_name,
                        "error": result.stderr,
                        "return_code": result.returncode
                    },
                    message=f"Failed to stop service {service_name}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to stop service {service_name}: {str(e)}",
                error=str(e)
            )
    
    def _restart_service(self, service_name: str) -> ToolResult:
        """Restart a system service."""
        try:
            if not service_name:
                return ToolResult(
                    success=False,
                    data={},
                    message="Service name is required",
                    error="Missing service name"
                )
            
            if platform.system().lower() == "windows":
                cmd = ["sc", "stop", service_name]
                subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                time.sleep(2)
                cmd = ["sc", "start", service_name]
            else:
                cmd = ["systemctl", "restart", service_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"service": service_name, "action": "restarted"},
                    message=f"Service {service_name} restarted successfully"
                )
            else:
                return ToolResult(
                    success=False,
                    data={
                        "service": service_name,
                        "error": result.stderr,
                        "return_code": result.returncode
                    },
                    message=f"Failed to restart service {service_name}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to restart service {service_name}: {str(e)}",
                error=str(e)
            )
    
    def _get_service_status(self, service_name: str) -> ToolResult:
        """Get status of a specific service."""
        try:
            if not service_name:
                return ToolResult(
                    success=False,
                    data={},
                    message="Service name is required",
                    error="Missing service name"
                )
            
            if platform.system().lower() == "windows":
                cmd = ["sc", "query", service_name]
            else:
                cmd = ["systemctl", "status", service_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            return ToolResult(
                success=True,
                data={
                    "service": service_name,
                    "status_output": result.stdout,
                    "error_output": result.stderr,
                    "return_code": result.returncode
                },
                message=f"Service status for {service_name}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get service status for {service_name}: {str(e)}",
                error=str(e)
            )
    
    def _enable_service(self, service_name: str) -> ToolResult:
        """Enable a system service to start on boot."""
        try:
            if not service_name:
                return ToolResult(
                    success=False,
                    data={},
                    message="Service name is required",
                    error="Missing service name"
                )
            
            if platform.system().lower() == "windows":
                cmd = ["sc", "config", service_name, "start=", "auto"]
            else:
                cmd = ["systemctl", "enable", service_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"service": service_name, "action": "enabled"},
                    message=f"Service {service_name} enabled successfully"
                )
            else:
                return ToolResult(
                    success=False,
                    data={
                        "service": service_name,
                        "error": result.stderr,
                        "return_code": result.returncode
                    },
                    message=f"Failed to enable service {service_name}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to enable service {service_name}: {str(e)}",
                error=str(e)
            )
    
    def _disable_service(self, service_name: str) -> ToolResult:
        """Disable a system service from starting on boot."""
        try:
            if not service_name:
                return ToolResult(
                    success=False,
                    data={},
                    message="Service name is required",
                    error="Missing service name"
                )
            
            if platform.system().lower() == "windows":
                cmd = ["sc", "config", service_name, "start=", "disabled"]
            else:
                cmd = ["systemctl", "disable", service_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"service": service_name, "action": "disabled"},
                    message=f"Service {service_name} disabled successfully"
                )
            else:
                return ToolResult(
                    success=False,
                    data={
                        "service": service_name,
                        "error": result.stderr,
                        "return_code": result.returncode
                    },
                    message=f"Failed to disable service {service_name}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to disable service {service_name}: {str(e)}",
                error=str(e)
            )
    
    def _list_users(self) -> ToolResult:
        """List system users."""
        try:
            users = []
            
            if platform.system().lower() == "windows":
                cmd = ["wmic", "useraccount", "get", "name,fullname,disabled"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines[1:]:  # Skip header
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 3:
                                users.append({
                                    'name': parts[0],
                                    'fullname': parts[1],
                                    'disabled': parts[2] == 'TRUE'
                                })
            else:
                # Unix/Linux users
                with open('/etc/passwd', 'r') as f:
                    for line in f:
                        parts = line.split(':')
                        if len(parts) >= 7:
                            users.append({
                                'name': parts[0],
                                'uid': parts[2],
                                'gid': parts[3],
                                'fullname': parts[4],
                                'home': parts[5],
                                'shell': parts[6]
                            })
            
            return ToolResult(
                success=True,
                data={
                    "users": users,
                    "total": len(users),
                    "platform": platform.system()
                },
                message=f"Found {len(users)} system users"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list users: {str(e)}",
                error=str(e)
            )
    
    def _get_user_info(self, user_name: str) -> ToolResult:
        """Get detailed information about a specific user."""
        try:
            if not user_name:
                return ToolResult(
                    success=False,
                    data={},
                    message="User name is required",
                    error="Missing user name"
                )
            
            user_info = {}
            
            if platform.system().lower() == "windows":
                cmd = ["wmic", "useraccount", "where", f"name='{user_name}'", "get", "name,fullname,disabled,lockout"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines[1:]:  # Skip header
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 4:
                                user_info = {
                                    'name': parts[0],
                                    'fullname': parts[1],
                                    'disabled': parts[2] == 'TRUE',
                                    'lockout': parts[3] == 'TRUE'
                                }
            else:
                # Unix/Linux user info
                cmd = ["id", user_name]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    user_info = {
                        'name': user_name,
                        'id_info': result.stdout.strip()
                    }
                    
                    # Get additional info
                    try:
                        with open('/etc/passwd', 'r') as f:
                            for line in f:
                                parts = line.split(':')
                                if parts[0] == user_name:
                                    user_info.update({
                                        'uid': parts[2],
                                        'gid': parts[3],
                                        'fullname': parts[4],
                                        'home': parts[5],
                                        'shell': parts[6]
                                    })
                                    break
                    except:
                        pass
            
            if user_info:
                return ToolResult(
                    success=True,
                    data=user_info,
                    message=f"User information for {user_name}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"User {user_name} not found",
                    error="User not found"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get user info for {user_name}: {str(e)}",
                error=str(e)
            )
    
    def _get_system_info(self) -> ToolResult:
        """Get comprehensive system information."""
        try:
            system_info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage('/')._asdict(),
                "boot_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time())),
                "uptime": time.time() - psutil.boot_time()
            }
            
            return ToolResult(
                success=True,
                data=system_info,
                message="System information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get system info: {str(e)}",
                error=str(e)
            )
    
    def _power_off(self) -> ToolResult:
        """Power off the system."""
        try:
            if platform.system().lower() == "windows":
                cmd = ["shutdown", "/s", "/t", "0"]
            else:
                cmd = ["shutdown", "-h", "now"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            return ToolResult(
                success=True,
                data={"action": "power_off"},
                message="System power off initiated"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to power off system: {str(e)}",
                error=str(e)
            )
    
    def _reboot(self) -> ToolResult:
        """Reboot the system."""
        try:
            if platform.system().lower() == "windows":
                cmd = ["shutdown", "/r", "/t", "0"]
            else:
                cmd = ["reboot"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            return ToolResult(
                success=True,
                data={"action": "reboot"},
                message="System reboot initiated"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to reboot system: {str(e)}",
                error=str(e)
            )
    
    def _sleep(self) -> ToolResult:
        """Put system to sleep."""
        try:
            if platform.system().lower() == "windows":
                cmd = ["powercfg", "/hibernate", "off"]
                subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                cmd = ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"]
            else:
                cmd = ["systemctl", "suspend"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            return ToolResult(
                success=True,
                data={"action": "sleep"},
                message="System sleep initiated"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to put system to sleep: {str(e)}",
                error=str(e)
            )
    
    def _execute_command(self, command: str, timeout: int = 30) -> ToolResult:
        """Execute a system command."""
        try:
            if not command:
                return ToolResult(
                    success=False,
                    data={},
                    message="Command is required",
                    error="Missing command"
                )
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            
            return ToolResult(
                success=result.returncode == 0,
                data={
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time": timeout
                },
                message=f"Command executed with return code {result.returncode}"
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={"command": command},
                message=f"Command timed out after {timeout} seconds"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to execute command: {str(e)}",
                error=str(e)
            )
    
    def _system_update(self) -> ToolResult:
        """Check for and perform system updates."""
        try:
            if platform.system().lower() == "windows":
                cmd = ["wuauclt", "/detectnow"]
            else:
                # Try different package managers
                for cmd in [["apt", "update"], ["yum", "check-update"], ["pacman", "-Sy"]]:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                        if result.returncode == 0:
                            break
                    except FileNotFoundError:
                        continue
            
            return ToolResult(
                success=True,
                data={"action": "system_update"},
                message="System update check completed"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to perform system update: {str(e)}",
                error=str(e)
            )
    
    def _disk_cleanup(self) -> ToolResult:
        """Perform disk cleanup operations."""
        try:
            cleanup_info = {
                "temp_files_removed": 0,
                "cache_cleared": 0,
                "log_files_cleaned": 0
            }
            
            # Clean temp files
            temp_dirs = []
            if platform.system().lower() == "windows":
                temp_dirs = [os.environ.get('TEMP', ''), os.environ.get('TMP', '')]
            else:
                temp_dirs = ['/tmp', '/var/tmp']
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                try:
                                    file_path = os.path.join(root, file)
                                    if os.path.isfile(file_path):
                                        os.remove(file_path)
                                        cleanup_info["temp_files_removed"] += 1
                                except:
                                    continue
                    except:
                        pass
            
            return ToolResult(
                success=True,
                data=cleanup_info,
                message=f"Disk cleanup completed: {cleanup_info['temp_files_removed']} temp files removed"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to perform disk cleanup: {str(e)}",
                error=str(e)
            )
    
    def _analyze_logs(self) -> ToolResult:
        """Analyze system logs for errors and warnings."""
        try:
            log_analysis = {
                "errors": [],
                "warnings": [],
                "total_entries": 0
            }
            
            # Common log locations
            log_files = []
            if platform.system().lower() == "windows":
                log_files = [
                    os.path.join(os.environ.get('WINDIR', ''), 'System32', 'winevt', 'Logs', 'System.evtx'),
                    os.path.join(os.environ.get('WINDIR', ''), 'System32', 'winevt', 'Logs', 'Application.evtx')
                ]
            else:
                log_files = ['/var/log/syslog', '/var/log/messages', '/var/log/kern.log']
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            for line in f:
                                log_analysis["total_entries"] += 1
                                line_lower = line.lower()
                                if "error" in line_lower:
                                    log_analysis["errors"].append(line.strip())
                                elif "warning" in line_lower:
                                    log_analysis["warnings"].append(line.strip())
                    except:
                        continue
            
            return ToolResult(
                success=True,
                data=log_analysis,
                message=f"Log analysis completed: {len(log_analysis['errors'])} errors, {len(log_analysis['warnings'])} warnings"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to analyze logs: {str(e)}",
                error=str(e)
            ) 