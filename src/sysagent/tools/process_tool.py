"""
Process management tool for SysAgent CLI.
"""

import psutil
import subprocess
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory


@register_tool
class ProcessTool(BaseTool):
    """Tool for process management."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="process_tool",
            description="Process management and monitoring",
            category=ToolCategory.PROCESS,
            permissions=["process_management"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Execute process management operations."""
        
        try:
            if action == "list":
                return self._list_processes(**kwargs)
            elif action == "kill":
                return self._kill_process(**kwargs)
            elif action == "monitor":
                return self._monitor_process(**kwargs)
            elif action == "info":
                return self._get_process_info(**kwargs)
            elif action == "search":
                return self._search_processes(**kwargs)
            elif action == "tree":
                return self._get_process_tree(**kwargs)
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
                message=f"Process operation failed: {str(e)}",
                error=str(e)
            )

    def _list_processes(self, **kwargs) -> ToolResult:
        """List running processes."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_percent': proc_info['memory_percent'],
                        'status': proc_info['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            return ToolResult(
                success=True,
                data={
                    'processes': processes,
                    'total_count': len(processes)
                },
                message=f"Found {len(processes)} running processes"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list processes: {str(e)}",
                error=str(e)
            )

    def _kill_process(self, **kwargs) -> ToolResult:
        """Kill a process by PID or name."""
        try:
            pid = kwargs.get('pid')
            name = kwargs.get('name')
            
            if not pid and not name:
                return ToolResult(
                    success=False,
                    data={},
                    message="No PID or process name provided",
                    error="Missing required parameter: pid or name"
                )
            
            killed_processes = []
            
            if pid:
                # Kill by PID
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    killed_processes.append({
                        'pid': pid,
                        'name': proc.name(),
                        'status': 'terminated'
                    })
                except psutil.NoSuchProcess:
                    return ToolResult(
                        success=False,
                        data={},
                        message=f"Process with PID {pid} not found",
                        error="Process not found"
                    )
            else:
                # Kill by name
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'] == name:
                            proc.terminate()
                            killed_processes.append({
                                'pid': proc.info['pid'],
                                'name': name,
                                'status': 'terminated'
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            return ToolResult(
                success=True,
                data={
                    'killed_processes': killed_processes,
                    'count': len(killed_processes)
                },
                message=f"Successfully terminated {len(killed_processes)} process(es)"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to kill process: {str(e)}",
                error=str(e)
            )

    def _monitor_process(self, **kwargs) -> ToolResult:
        """Monitor a specific process."""
        try:
            pid = kwargs.get('pid')
            name = kwargs.get('name')
            duration = kwargs.get('duration', 10)
            interval = kwargs.get('interval', 1)
            
            if not pid and not name:
                return ToolResult(
                    success=False,
                    data={},
                    message="No PID or process name provided",
                    error="Missing required parameter: pid or name"
                )
            
            target_proc = None
            
            if pid:
                target_proc = psutil.Process(pid)
            else:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'] == name:
                            target_proc = proc
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            if not target_proc:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Process not found",
                    error="Process not found"
                )
            
            monitoring_data = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    with target_proc.oneshot():
                        monitoring_data.append({
                            'timestamp': datetime.now().isoformat(),
                            'pid': target_proc.pid,
                            'name': target_proc.name(),
                            'cpu_percent': target_proc.cpu_percent(),
                            'memory_percent': target_proc.memory_percent(),
                            'memory_info': target_proc.memory_info()._asdict(),
                            'status': target_proc.status()
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                
                time.sleep(interval)
            
            return ToolResult(
                success=True,
                data={
                    'monitoring_data': monitoring_data,
                    'duration': duration,
                    'interval': interval,
                    'samples': len(monitoring_data)
                },
                message=f"Monitored process for {duration} seconds, collected {len(monitoring_data)} samples"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to monitor process: {str(e)}",
                error=str(e)
            )

    def _get_process_info(self, **kwargs) -> ToolResult:
        """Get detailed information about a process."""
        try:
            pid = kwargs.get('pid')
            name = kwargs.get('name')
            
            if not pid and not name:
                return ToolResult(
                    success=False,
                    data={},
                    message="No PID or process name provided",
                    error="Missing required parameter: pid or name"
                )
            
            target_proc = None
            
            if pid:
                target_proc = psutil.Process(pid)
            else:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'] == name:
                            target_proc = proc
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            if not target_proc:
                return ToolResult(
                    success=False,
                    data={},
                    message="Process not found",
                    error="Process not found"
                )
            
            try:
                with target_proc.oneshot():
                    process_info = {
                        'pid': target_proc.pid,
                        'name': target_proc.name(),
                        'exe': target_proc.exe(),
                        'cmdline': target_proc.cmdline(),
                        'cwd': target_proc.cwd(),
                        'status': target_proc.status(),
                        'create_time': target_proc.create_time(),
                        'cpu_percent': target_proc.cpu_percent(),
                        'memory_percent': target_proc.memory_percent(),
                        'memory_info': target_proc.memory_info()._asdict(),
                        'num_threads': target_proc.num_threads(),
                        'num_fds': target_proc.num_fds() if hasattr(target_proc, 'num_fds') else None,
                        'connections': len(target_proc.connections()),
                        'open_files': len(target_proc.open_files()),
                        'username': target_proc.username(),
                        'ppid': target_proc.ppid(),
                        'children': [child.pid for child in target_proc.children()]
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Failed to get process info: {str(e)}",
                    error=str(e)
                )
            
            return ToolResult(
                success=True,
                data={'process_info': process_info},
                message=f"Retrieved detailed information for process {process_info['name']} (PID: {process_info['pid']})"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get process info: {str(e)}",
                error=str(e)
            )

    def _search_processes(self, **kwargs) -> ToolResult:
        """Search for processes by name pattern."""
        try:
            pattern = kwargs.get('pattern', '')
            if not pattern:
                return ToolResult(
                    success=False,
                    data={},
                    message="No search pattern provided",
                    error="Missing required parameter: pattern"
                )
            
            matching_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if (pattern.lower() in proc_info['name'].lower() or
                        any(pattern.lower() in arg.lower() for arg in proc_info['cmdline'])):
                        matching_processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline': proc_info['cmdline']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return ToolResult(
                success=True,
                data={
                    'matching_processes': matching_processes,
                    'pattern': pattern,
                    'count': len(matching_processes)
                },
                message=f"Found {len(matching_processes)} processes matching pattern '{pattern}'"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to search processes: {str(e)}",
                error=str(e)
            )

    def _get_process_tree(self, **kwargs) -> ToolResult:
        """Get process tree structure."""
        try:
            pid = kwargs.get('pid')
            
            if not pid:
                # Get root processes (no parent or parent is init)
                root_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'ppid']):
                    try:
                        proc_info = proc.info
                        if proc_info['ppid'] == 1 or proc_info['ppid'] == 0:
                            root_processes.append({
                                'pid': proc_info['pid'],
                                'name': proc_info['name'],
                                'children': self._get_children(proc_info['pid'])
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return ToolResult(
                    success=True,
                    data={'process_tree': root_processes},
                    message=f"Retrieved process tree with {len(root_processes)} root processes"
                )
            else:
                # Get tree for specific process
                try:
                    target_proc = psutil.Process(pid)
                    tree = {
                        'pid': target_proc.pid,
                        'name': target_proc.name(),
                        'children': self._get_children(pid)
                    }
                    
                    return ToolResult(
                        success=True,
                        data={'process_tree': tree},
                        message=f"Retrieved process tree for PID {pid}"
                    )
                except psutil.NoSuchProcess:
                    return ToolResult(
                        success=False,
                        data={},
                        message=f"Process with PID {pid} not found",
                        error="Process not found"
                    )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get process tree: {str(e)}",
                error=str(e)
            )

    def _get_children(self, pid: int) -> List[Dict[str, Any]]:
        """Get children of a process."""
        children = []
        try:
            parent = psutil.Process(pid)
            for child in parent.children():
                try:
                    children.append({
                        'pid': child.pid,
                        'name': child.name(),
                        'children': self._get_children(child.pid)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        
        return children 