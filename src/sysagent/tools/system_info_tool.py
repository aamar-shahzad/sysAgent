"""
System information and metrics tool for SysAgent CLI.
"""

import os
import sys
import platform
import subprocess
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil

from .base import BaseTool, register_tool, ToolMetadata
from ..types import ToolResult, ToolCategory
from ..utils.platform import detect_platform, get_platform_info


@register_tool
class SystemInfoTool(BaseTool):
    """Tool for system information and metrics."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="system_info_tool",
            description="System information, metrics, and monitoring",
            category=ToolCategory.SYSTEM,
            permissions=["system_info"],
            version="1.0.0"
        )
    
    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Execute system info operations based on action parameter."""
        
        if action == "overview":
            return self._get_system_overview(**kwargs)
        elif action == "cpu":
            return self._get_cpu_info(**kwargs)
        elif action == "memory":
            return self._get_memory_info(**kwargs)
        elif action == "disk":
            return self._get_disk_info(**kwargs)
        elif action == "network":
            return self._get_network_info(**kwargs)
        elif action == "processes":
            return self._get_processes_info(**kwargs)
        elif action == "battery":
            return self._get_battery_info(**kwargs)
        elif action == "uptime":
            return self._get_uptime_info(**kwargs)
        elif action == "performance":
            return self._get_performance_metrics(**kwargs)
        elif action == "hardware":
            return self._get_hardware_info(**kwargs)
        else:
            return ToolResult(
                success=False,
                data={},
                message=f"Unknown action: {action}",
                error=f"Unsupported action: {action}"
            )
    
    def _get_system_overview(self, **kwargs) -> ToolResult:
        """Get comprehensive system overview."""
        try:
            # Basic system info
            system_info = {
                "platform": detect_platform().value,
                "platform_info": get_platform_info(),
                "python_version": sys.version,
                "hostname": platform.node(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
            }
            
            # CPU info
            cpu_info = {
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=1),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            }
            
            # Memory info
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free,
                "percent": memory.percent,
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
            }
            
            # Disk info
            disk_info = self._get_disk_info()
            
            # Network info
            network_info = self._get_network_info()
            
            # Uptime
            uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            uptime_info = {
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "uptime_seconds": uptime.total_seconds(),
                "uptime_days": uptime.days,
                "uptime_hours": uptime.seconds // 3600,
                "uptime_minutes": (uptime.seconds % 3600) // 60,
            }
            
            return ToolResult(
                success=True,
                data={
                    "system": system_info,
                    "cpu": cpu_info,
                    "memory": memory_info,
                    "disk": disk_info,
                    "network": network_info,
                    "uptime": uptime_info,
                    "timestamp": datetime.now().isoformat()
                },
                message="System overview retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get system overview",
                error=str(e)
            )
    
    def _get_cpu_info(self, **kwargs) -> ToolResult:
        """Get detailed CPU information."""
        try:
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            # Get CPU usage for each core
            cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # Get CPU frequency
            cpu_freq = psutil.cpu_freq()
            freq_info = cpu_freq._asdict() if cpu_freq else {}
            
            # Get CPU stats
            cpu_stats = psutil.cpu_stats()
            
            # Get CPU temperature if available
            cpu_temp = self._get_cpu_temperature()
            
            cpu_info = {
                "physical_cores": cpu_count,
                "logical_cores": cpu_count_logical,
                "usage_percent": psutil.cpu_percent(interval=1),
                "usage_per_core": cpu_percent_per_core,
                "frequency": freq_info,
                "stats": {
                    "ctx_switches": cpu_stats.ctx_switches,
                    "interrupts": cpu_stats.interrupts,
                    "soft_interrupts": cpu_stats.soft_interrupts,
                    "syscalls": cpu_stats.syscalls,
                },
                "temperature": cpu_temp,
            }
            
            return ToolResult(
                success=True,
                data=cpu_info,
                message="CPU information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get CPU information",
                error=str(e)
            )
    
    def _get_memory_info(self, **kwargs) -> ToolResult:
        """Get detailed memory information."""
        try:
            virtual_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()
            
            memory_info = {
                "virtual": {
                    "total": virtual_memory.total,
                    "available": virtual_memory.available,
                    "used": virtual_memory.used,
                    "free": virtual_memory.free,
                    "percent": virtual_memory.percent,
                    "total_gb": round(virtual_memory.total / (1024**3), 2),
                    "available_gb": round(virtual_memory.available / (1024**3), 2),
                    "used_gb": round(virtual_memory.used / (1024**3), 2),
                },
                "swap": {
                    "total": swap_memory.total,
                    "used": swap_memory.used,
                    "free": swap_memory.free,
                    "percent": swap_memory.percent,
                    "total_gb": round(swap_memory.total / (1024**3), 2),
                    "used_gb": round(swap_memory.used / (1024**3), 2),
                }
            }
            
            return ToolResult(
                success=True,
                data=memory_info,
                message="Memory information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get memory information",
                error=str(e)
            )
    
    def _get_disk_info(self, **kwargs) -> ToolResult:
        """Get disk usage information."""
        try:
            partitions = psutil.disk_partitions()
            disk_info = {
                "partitions": [],
                "total_usage": {}
            }
            
            total_size = 0
            total_used = 0
            total_free = 0
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partition_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                    }
                    disk_info["partitions"].append(partition_info)
                    
                    total_size += usage.total
                    total_used += usage.used
                    total_free += usage.free
                    
                except (OSError, PermissionError):
                    continue
            
            # Calculate totals
            if total_size > 0:
                disk_info["total_usage"] = {
                    "total": total_size,
                    "used": total_used,
                    "free": total_free,
                    "percent": round((total_used / total_size) * 100, 2),
                    "total_gb": round(total_size / (1024**3), 2),
                    "used_gb": round(total_used / (1024**3), 2),
                    "free_gb": round(total_free / (1024**3), 2),
                }
            
            return ToolResult(
                success=True,
                data=disk_info,
                message="Disk information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get disk information",
                error=str(e)
            )
    
    def _get_network_info(self, **kwargs) -> ToolResult:
        """Get network interface information."""
        try:
            network_interfaces = psutil.net_if_addrs()
            network_stats = psutil.net_if_stats()
            network_io = psutil.net_io_counters()
            
            interfaces = {}
            for interface_name, addresses in network_interfaces.items():
                interface_info = {
                    "addresses": [],
                    "stats": network_stats.get(interface_name, {}),
                }
                
                for address in addresses:
                    addr_info = {
                        "family": str(address.family),
                        "address": address.address,
                        "netmask": address.netmask,
                        "broadcast": address.broadcast,
                    }
                    interface_info["addresses"].append(addr_info)
                
                interfaces[interface_name] = interface_info
            
            network_info = {
                "interfaces": interfaces,
                "io_counters": {
                    "bytes_sent": network_io.bytes_sent,
                    "bytes_recv": network_io.bytes_recv,
                    "packets_sent": network_io.packets_sent,
                    "packets_recv": network_io.packets_recv,
                    "bytes_sent_gb": round(network_io.bytes_sent / (1024**3), 2),
                    "bytes_recv_gb": round(network_io.bytes_recv / (1024**3), 2),
                }
            }
            
            return ToolResult(
                success=True,
                data=network_info,
                message="Network information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get network information",
                error=str(e)
            )
    
    def _get_processes_info(self, **kwargs) -> ToolResult:
        """Get information about running processes."""
        try:
            sort_by = kwargs.get("sort_by", "cpu_percent")
            limit = kwargs.get("limit", 20)
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0 or proc_info['memory_percent'] > 0:
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort processes
            if sort_by == "cpu_percent":
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            elif sort_by == "memory_percent":
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda x: x['name'])
            
            # Limit results
            processes = processes[:limit]
            
            return ToolResult(
                success=True,
                data={
                    "processes": processes,
                    "count": len(processes),
                    "sort_by": sort_by,
                    "limit": limit
                },
                message=f"Retrieved {len(processes)} processes sorted by {sort_by}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get processes information",
                error=str(e)
            )
    
    def _get_battery_info(self, **kwargs) -> ToolResult:
        """Get battery information if available."""
        try:
            battery = psutil.sensors_battery()
            
            if battery is None:
                return ToolResult(
                    success=True,
                    data={"available": False},
                    message="No battery detected"
                )
            
            battery_info = {
                "available": True,
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "time_left": battery.secsleft if battery.secsleft != -1 else None,
                "time_left_hours": round(battery.secsleft / 3600, 1) if battery.secsleft != -1 else None,
            }
            
            return ToolResult(
                success=True,
                data=battery_info,
                message="Battery information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get battery information",
                error=str(e)
            )
    
    def _get_uptime_info(self, **kwargs) -> ToolResult:
        """Get system uptime information."""
        try:
            boot_time = psutil.boot_time()
            uptime = datetime.now() - datetime.fromtimestamp(boot_time)
            
            uptime_info = {
                "boot_time": datetime.fromtimestamp(boot_time).isoformat(),
                "uptime_seconds": uptime.total_seconds(),
                "uptime_days": uptime.days,
                "uptime_hours": uptime.seconds // 3600,
                "uptime_minutes": (uptime.seconds % 3600) // 60,
                "uptime_formatted": str(uptime).split('.')[0],  # Remove microseconds
            }
            
            return ToolResult(
                success=True,
                data=uptime_info,
                message="Uptime information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get uptime information",
                error=str(e)
            )
    
    def _get_performance_metrics(self, **kwargs) -> ToolResult:
        """Get performance metrics and load averages."""
        try:
            # CPU load average
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else None
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            
            # Network I/O
            network_io = psutil.net_io_counters()
            
            performance_metrics = {
                "load_average": {
                    "1min": load_avg[0] if load_avg else None,
                    "5min": load_avg[1] if load_avg else None,
                    "15min": load_avg[2] if load_avg else None,
                },
                "memory": {
                    "usage_percent": memory.percent,
                    "available_percent": round((memory.available / memory.total) * 100, 2),
                },
                "disk_io": {
                    "read_bytes": disk_io.read_bytes,
                    "write_bytes": disk_io.write_bytes,
                    "read_count": disk_io.read_count,
                    "write_count": disk_io.write_count,
                },
                "network_io": {
                    "bytes_sent": network_io.bytes_sent,
                    "bytes_recv": network_io.bytes_recv,
                    "packets_sent": network_io.packets_sent,
                    "packets_recv": network_io.packets_recv,
                },
                "timestamp": datetime.now().isoformat(),
            }
            
            return ToolResult(
                success=True,
                data=performance_metrics,
                message="Performance metrics retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get performance metrics",
                error=str(e)
            )
    
    def _get_hardware_info(self, **kwargs) -> ToolResult:
        """Get detailed hardware information."""
        try:
            hardware_info = {
                "cpu": {
                    "name": platform.processor(),
                    "architecture": platform.architecture()[0],
                    "count": psutil.cpu_count(),
                    "count_logical": psutil.cpu_count(logical=True),
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                },
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                }
            }
            
            # Platform-specific hardware info
            current_platform = detect_platform()
            if current_platform.value == "macos":
                hardware_info.update(self._get_macos_hardware_info())
            elif current_platform.value == "linux":
                hardware_info.update(self._get_linux_hardware_info())
            elif current_platform.value == "windows":
                hardware_info.update(self._get_windows_hardware_info())
            
            return ToolResult(
                success=True,
                data=hardware_info,
                message="Hardware information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to get hardware information",
                error=str(e)
            )
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature if available."""
        try:
            # This is platform-specific and may not work on all systems
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get the first available temperature
                    for name, entries in temps.items():
                        if entries:
                            return entries[0].current
        except Exception:
            pass
        return None
    
    def _get_macos_hardware_info(self) -> Dict[str, Any]:
        """Get macOS-specific hardware information."""
        try:
            # Use system_profiler for detailed hardware info
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType", "-xml"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse the XML output (simplified)
                return {
                    "macos_hardware": "Available (use system_profiler for details)"
                }
        except Exception:
            pass
        
        return {}
    
    def _get_linux_hardware_info(self) -> Dict[str, Any]:
        """Get Linux-specific hardware information."""
        hardware_info = {}
        
        try:
            # CPU info from /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                cpu_info = f.read()
                if 'model name' in cpu_info:
                    for line in cpu_info.split('\n'):
                        if line.startswith('model name'):
                            hardware_info['cpu_model'] = line.split(':')[1].strip()
                            break
        except Exception:
            pass
        
        try:
            # Memory info from /proc/meminfo
            with open('/proc/meminfo', 'r') as f:
                mem_info = f.read()
                if 'MemTotal' in mem_info:
                    for line in mem_info.split('\n'):
                        if line.startswith('MemTotal'):
                            mem_total = line.split()[1]
                            hardware_info['memory_total_kb'] = int(mem_total)
                            break
        except Exception:
            pass
        
        return hardware_info
    
    def _get_windows_hardware_info(self) -> Dict[str, Any]:
        """Get Windows-specific hardware information."""
        try:
            import wmi
            c = wmi.WMI()
            
            hardware_info = {}
            
            # CPU info
            for cpu in c.Win32_Processor():
                hardware_info['cpu_name'] = cpu.Name
                hardware_info['cpu_cores'] = cpu.NumberOfCores
                hardware_info['cpu_threads'] = cpu.NumberOfLogicalProcessors
                break
            
            # Memory info
            for memory in c.Win32_PhysicalMemory():
                hardware_info['memory_slots'] = memory.Capacity
                break
            
            return hardware_info
        except Exception:
            return {}
    
    def get_usage_examples(self) -> List[str]:
        """Get usage examples for this tool."""
        return [
            "Get system overview: system_info_tool --action overview",
            "Get CPU info: system_info_tool --action cpu",
            "Get memory info: system_info_tool --action memory",
            "Get disk usage: system_info_tool --action disk",
            "Get network info: system_info_tool --action network",
            "Get top processes: system_info_tool --action processes --limit 10",
            "Get battery info: system_info_tool --action battery",
            "Get uptime: system_info_tool --action uptime",
            "Get performance metrics: system_info_tool --action performance",
            "Get hardware info: system_info_tool --action hardware"
        ] 