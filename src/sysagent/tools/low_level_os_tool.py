"""
Low-level OS tools for SysAgent CLI - Direct system access and real-time data.
"""

import os
import sys
import platform
import subprocess
import time
import threading
import signal
import socket
import struct
import fcntl
import termios
import select
import mmap
import ctypes
import ctypes.util
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import psutil
import json

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory, PermissionLevel


@register_tool
class LowLevelOSTool(BaseTool):
    """Tool for low-level OS operations."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="low_level_os_tool",
            description="Direct low-level OS access and system calls",
            category=ToolCategory.SYSTEM,
            permissions=["low_level_os"],
            version="1.0.0"
        )

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.system_calls = {}
        self.kernel_interfaces = {}
        self.hardware_monitors = {}

    def _execute(self, action: str, target: str = None, interface: str = None,
                 system_call: str = None, hardware_component: str = None, **kwargs) -> ToolResult:
        """Execute low-level OS operations."""
        
        try:
            if action == "system_call":
                return self._execute_system_call(system_call, **kwargs)
            elif action == "kernel_interface":
                return self._access_kernel_interface(interface, **kwargs)
            elif action == "hardware_access":
                return self._access_hardware_directly(hardware_component, **kwargs)
            elif action == "real_time_monitoring":
                return self._real_time_system_monitoring(**kwargs)
            elif action == "memory_mapping":
                return self._memory_mapping_operations(target, **kwargs)
            elif action == "process_injection":
                return self._process_injection_operations(target, **kwargs)
            elif action == "network_raw":
                return self._raw_network_operations(**kwargs)
            elif action == "file_system_low":
                return self._low_level_file_system(target, **kwargs)
            elif action == "device_io":
                return self._device_io_operations(target, **kwargs)
            elif action == "interrupt_handling":
                return self._interrupt_handling_operations(**kwargs)
            elif action == "system_tables":
                return self._access_system_tables(**kwargs)
            elif action == "performance_counters":
                return self._access_performance_counters(**kwargs)
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
                message=f"Low-level OS operation failed: {str(e)}",
                error=str(e)
            )

    def _execute_system_call(self, system_call: str, **kwargs) -> ToolResult:
        """Execute low-level system calls."""
        try:
            if system_call == "getpid":
                result = os.getpid()
            elif system_call == "getuid":
                result = os.getuid()
            elif system_call == "getgid":
                result = os.getgid()
            elif system_call == "getppid":
                result = os.getppid()
            elif system_call == "getcwd":
                result = os.getcwd()
            elif system_call == "umask":
                result = os.umask(0)
            elif system_call == "getloadavg":
                result = os.getloadavg()
            elif system_call == "sysconf":
                name = kwargs.get("name", "SC_NPROCESSORS_ONLN")
                result = os.sysconf(name)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown system call: {system_call}",
                    error=f"Unsupported system call: {system_call}"
                )

            return ToolResult(
                success=True,
                data={"system_call": system_call, "result": result},
                message=f"System call {system_call} executed successfully"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"System call {system_call} failed: {str(e)}",
                error=str(e)
            )

    def _access_kernel_interface(self, interface: str, **kwargs) -> ToolResult:
        """Access kernel interfaces and system information."""
        try:
            if interface == "proc":
                return self._read_proc_interface(**kwargs)
            elif interface == "sys":
                return self._read_sys_interface(**kwargs)
            elif interface == "dev":
                return self._read_dev_interface(**kwargs)
            elif interface == "mem":
                return self._read_memory_interface(**kwargs)
            elif interface == "cpu":
                return self._read_cpu_interface(**kwargs)
            elif interface == "network":
                return self._read_network_interface(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown kernel interface: {interface}",
                    error=f"Unsupported interface: {interface}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Kernel interface access failed: {str(e)}",
                error=str(e)
            )

    def _read_proc_interface(self, **kwargs) -> ToolResult:
        """Read from /proc filesystem."""
        try:
            proc_path = kwargs.get("path", "/proc")
            data = {}
            
            # Read /proc/cpuinfo
            try:
                with open("/proc/cpuinfo", "r") as f:
                    data["cpuinfo"] = f.read()
            except:
                data["cpuinfo"] = "Not available"
            
            # Read /proc/meminfo
            try:
                with open("/proc/meminfo", "r") as f:
                    data["meminfo"] = f.read()
            except:
                data["meminfo"] = "Not available"
            
            # Read /proc/loadavg
            try:
                with open("/proc/loadavg", "r") as f:
                    data["loadavg"] = f.read().strip()
            except:
                data["loadavg"] = "Not available"
            
            # Read /proc/stat
            try:
                with open("/proc/stat", "r") as f:
                    data["stat"] = f.read()
            except:
                data["stat"] = "Not available"
            
            # Read /proc/net/dev
            try:
                with open("/proc/net/dev", "r") as f:
                    data["net_dev"] = f.read()
            except:
                data["net_dev"] = "Not available"

            return ToolResult(
                success=True,
                data=data,
                message="Proc interface data retrieved successfully"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to read proc interface: {str(e)}",
                error=str(e)
            )

    def _read_sys_interface(self, **kwargs) -> ToolResult:
        """Read from /sys filesystem."""
        try:
            data = {}
            
            # Read CPU information from /sys
            try:
                cpu_path = "/sys/devices/system/cpu"
                if os.path.exists(cpu_path):
                    data["cpu_count"] = len([d for d in os.listdir(cpu_path) if d.startswith("cpu")])
                    data["cpu_online"] = []
                    for cpu in range(data["cpu_count"]):
                        online_file = f"{cpu_path}/cpu{cpu}/online"
                        if os.path.exists(online_file):
                            with open(online_file, "r") as f:
                                data["cpu_online"].append(f.read().strip() == "1")
            except:
                data["cpu_info"] = "Not available"
            
            # Read memory information from /sys
            try:
                mem_path = "/sys/devices/system/memory"
                if os.path.exists(mem_path):
                    data["memory_blocks"] = len([d for d in os.listdir(mem_path) if d.startswith("memory")])
            except:
                data["memory_info"] = "Not available"

            return ToolResult(
                success=True,
                data=data,
                message="Sys interface data retrieved successfully"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to read sys interface: {str(e)}",
                error=str(e)
            )

    def _access_hardware_directly(self, component: str, **kwargs) -> ToolResult:
        """Access hardware directly through low-level interfaces."""
        try:
            if component == "cpu":
                return self._access_cpu_hardware(**kwargs)
            elif component == "memory":
                return self._access_memory_hardware(**kwargs)
            elif component == "disk":
                return self._access_disk_hardware(**kwargs)
            elif component == "network":
                return self._access_network_hardware(**kwargs)
            elif component == "temperature":
                return self._access_temperature_sensors(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown hardware component: {component}",
                    error=f"Unsupported component: {component}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Hardware access failed: {str(e)}",
                error=str(e)
            )

    def _access_cpu_hardware(self, **kwargs) -> ToolResult:
        """Access CPU hardware directly."""
        try:
            cpu_data = {}
            
            # Get CPU frequency
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("cpu MHz"):
                            cpu_data["frequency_mhz"] = float(line.split(":")[1].strip())
                            break
            except:
                cpu_data["frequency_mhz"] = "Not available"
            
            # Get CPU temperature
            try:
                temp_paths = [
                    "/sys/class/thermal/thermal_zone0/temp",
                    "/proc/acpi/thermal_zone/THM0/temperature"
                ]
                for temp_path in temp_paths:
                    if os.path.exists(temp_path):
                        with open(temp_path, "r") as f:
                            temp = int(f.read().strip())
                            cpu_data["temperature_c"] = temp / 1000.0
                            break
            except:
                cpu_data["temperature_c"] = "Not available"
            
            # Get CPU usage per core
            try:
                cpu_data["usage_per_core"] = psutil.cpu_percent(interval=1, percpu=True)
            except:
                cpu_data["usage_per_core"] = "Not available"

            return ToolResult(
                success=True,
                data=cpu_data,
                message="CPU hardware data retrieved successfully"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to access CPU hardware: {str(e)}",
                error=str(e)
            )

    def _real_time_system_monitoring(self, **kwargs) -> ToolResult:
        """Real-time system monitoring with low-level access."""
        try:
            duration = kwargs.get("duration", 5)
            interval = kwargs.get("interval", 1)
            
            monitoring_data = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                snapshot = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu": {
                        "usage": psutil.cpu_percent(interval=interval),
                        "count": psutil.cpu_count(),
                        "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                    },
                    "memory": {
                        "total": psutil.virtual_memory().total,
                        "available": psutil.virtual_memory().available,
                        "used": psutil.virtual_memory().used,
                        "percent": psutil.virtual_memory().percent
                    },
                    "disk": {
                        "io_counters": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                    },
                    "network": {
                        "io_counters": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
                    }
                }
                
                monitoring_data.append(snapshot)
                time.sleep(interval)
            
            return ToolResult(
                success=True,
                data={
                    "monitoring_duration": duration,
                    "interval": interval,
                    "snapshots": monitoring_data,
                    "summary": {
                        "total_snapshots": len(monitoring_data),
                        "avg_cpu_usage": sum(s["cpu"]["usage"] for s in monitoring_data) / len(monitoring_data),
                        "avg_memory_usage": sum(s["memory"]["percent"] for s in monitoring_data) / len(monitoring_data)
                    }
                },
                message=f"Real-time monitoring completed for {duration} seconds"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Real-time monitoring failed: {str(e)}",
                error=str(e)
            )

    def _memory_mapping_operations(self, target: str, **kwargs) -> ToolResult:
        """Low-level memory mapping operations."""
        try:
            if target == "process_memory":
                return self._map_process_memory(**kwargs)
            elif target == "shared_memory":
                return self._map_shared_memory(**kwargs)
            elif target == "physical_memory":
                return self._map_physical_memory(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown memory mapping target: {target}",
                    error=f"Unsupported target: {target}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Memory mapping operation failed: {str(e)}",
                error=str(e)
            )

    def _raw_network_operations(self, **kwargs) -> ToolResult:
        """Raw network operations and packet analysis."""
        try:
            operation = kwargs.get("operation", "interfaces")
            
            if operation == "interfaces":
                # Get raw network interface information
                interfaces = {}
                try:
                    for interface in psutil.net_if_addrs():
                        interfaces[interface] = []
                        for addr in psutil.net_if_addrs()[interface]:
                            interfaces[interface].append({
                                "family": str(addr.family),
                                "address": addr.address,
                                "netmask": addr.netmask,
                                "broadcast": addr.broadcast
                            })
                except Exception as e:
                    interfaces = {"error": str(e)}
                
                return ToolResult(
                    success=True,
                    data={"interfaces": interfaces},
                    message="Raw network interface data retrieved"
                )
            
            elif operation == "connections":
                # Get raw network connections
                try:
                    connections = []
                    for conn in psutil.net_connections():
                        connections.append({
                            "fd": conn.fd,
                            "family": conn.family,
                            "type": conn.type,
                            "laddr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            "raddr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            "status": conn.status,
                            "pid": conn.pid
                        })
                except Exception as e:
                    connections = {"error": str(e)}
                
                return ToolResult(
                    success=True,
                    data={"connections": connections},
                    message="Raw network connections data retrieved"
                )
            
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown network operation: {operation}",
                    error=f"Unsupported operation: {operation}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Raw network operation failed: {str(e)}",
                error=str(e)
            )

    def _low_level_file_system(self, target: str, **kwargs) -> ToolResult:
        """Low-level file system operations."""
        try:
            if target == "inodes":
                return self._get_inode_information(**kwargs)
            elif target == "blocks":
                return self._get_block_information(**kwargs)
            elif target == "mounts":
                return self._get_mount_information(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown file system target: {target}",
                    error=f"Unsupported target: {target}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Low-level file system operation failed: {str(e)}",
                error=str(e)
            )

    def _get_inode_information(self, **kwargs) -> ToolResult:
        """Get inode information."""
        try:
            path = kwargs.get("path", "/")
            inode_data = {}
            
            try:
                stat_info = os.stat(path)
                inode_data = {
                    "inode": stat_info.st_ino,
                    "device": stat_info.st_dev,
                    "mode": stat_info.st_mode,
                    "uid": stat_info.st_uid,
                    "gid": stat_info.st_gid,
                    "size": stat_info.st_size,
                    "atime": stat_info.st_atime,
                    "mtime": stat_info.st_mtime,
                    "ctime": stat_info.st_ctime
                }
            except Exception as e:
                inode_data = {"error": str(e)}
            
            return ToolResult(
                success=True,
                data={"inode_info": inode_data},
                message="Inode information retrieved successfully"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get inode information: {str(e)}",
                error=str(e)
            )

    def _access_performance_counters(self, **kwargs) -> ToolResult:
        """Access system performance counters."""
        try:
            counter_type = kwargs.get("type", "cpu")
            
            if counter_type == "cpu":
                # CPU performance counters
                cpu_counters = {
                    "user_time": psutil.cpu_times().user,
                    "system_time": psutil.cpu_times().system,
                    "idle_time": psutil.cpu_times().idle,
                    "iowait_time": psutil.cpu_times().iowait if hasattr(psutil.cpu_times(), 'iowait') else 0,
                    "irq_time": psutil.cpu_times().irq if hasattr(psutil.cpu_times(), 'irq') else 0,
                    "softirq_time": psutil.cpu_times().softirq if hasattr(psutil.cpu_times(), 'softirq') else 0
                }
                
                return ToolResult(
                    success=True,
                    data={"cpu_counters": cpu_counters},
                    message="CPU performance counters retrieved"
                )
            
            elif counter_type == "memory":
                # Memory performance counters
                memory_counters = {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "used": psutil.virtual_memory().used,
                    "free": psutil.virtual_memory().free,
                    "active": psutil.virtual_memory().active if hasattr(psutil.virtual_memory(), 'active') else 0,
                    "inactive": psutil.virtual_memory().inactive if hasattr(psutil.virtual_memory(), 'inactive') else 0,
                    "buffers": psutil.virtual_memory().buffers if hasattr(psutil.virtual_memory(), 'buffers') else 0,
                    "cached": psutil.virtual_memory().cached if hasattr(psutil.virtual_memory(), 'cached') else 0
                }
                
                return ToolResult(
                    success=True,
                    data={"memory_counters": memory_counters},
                    message="Memory performance counters retrieved"
                )
            
            elif counter_type == "disk":
                # Disk performance counters
                try:
                    disk_counters = psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                except:
                    disk_counters = {"error": "Not available"}
                
                return ToolResult(
                    success=True,
                    data={"disk_counters": disk_counters},
                    message="Disk performance counters retrieved"
                )
            
            elif counter_type == "network":
                # Network performance counters
                try:
                    network_counters = psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
                except:
                    network_counters = {"error": "Not available"}
                
                return ToolResult(
                    success=True,
                    data={"network_counters": network_counters},
                    message="Network performance counters retrieved"
                )
            
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown performance counter type: {counter_type}",
                    error=f"Unsupported type: {counter_type}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Performance counter access failed: {str(e)}",
                error=str(e)
            ) 