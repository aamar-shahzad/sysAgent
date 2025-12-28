"""
System Insights tool for SysAgent CLI - AI-powered system analysis and recommendations.
"""

import subprocess
import psutil
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class SystemInsightsTool(BaseTool):
    """Tool for AI-powered system analysis, health checks, and recommendations."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="system_insights_tool",
            description="AI-powered system analysis, health checks, and recommendations",
            category=ToolCategory.SYSTEM,
            permissions=["system_read"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "health_check": self._health_check,
                "performance": self._performance_analysis,
                "recommendations": self._get_recommendations,
                "security_scan": self._security_scan,
                "resource_hogs": self._find_resource_hogs,
                "startup_analysis": self._startup_analysis,
                "storage_analysis": self._storage_analysis,
                "network_analysis": self._network_analysis,
                "optimize": self._get_optimizations,
                "quick_insights": self._quick_insights,
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
                message=f"Insights analysis failed: {str(e)}",
                error=str(e)
            )

    def _health_check(self, **kwargs) -> ToolResult:
        """Perform comprehensive system health check."""
        issues = []
        warnings = []
        good = []
        score = 100
        
        # CPU Check
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            issues.append(f"Critical: CPU usage at {cpu_percent:.1f}%")
            score -= 20
        elif cpu_percent > 70:
            warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            score -= 10
        else:
            good.append(f"CPU usage normal: {cpu_percent:.1f}%")
        
        # Memory Check
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            issues.append(f"Critical: Memory usage at {memory.percent:.1f}%")
            score -= 20
        elif memory.percent > 75:
            warnings.append(f"High memory usage: {memory.percent:.1f}%")
            score -= 10
        else:
            good.append(f"Memory usage normal: {memory.percent:.1f}%")
        
        # Disk Check
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                if usage.percent > 95:
                    issues.append(f"Critical: Disk '{partition.mountpoint}' almost full ({usage.percent:.1f}%)")
                    score -= 15
                elif usage.percent > 85:
                    warnings.append(f"Disk '{partition.mountpoint}' getting full ({usage.percent:.1f}%)")
                    score -= 5
            except:
                continue
        
        if not any("Disk" in i for i in issues + warnings):
            good.append("Disk space adequate")
        
        # Swap Check
        swap = psutil.swap_memory()
        if swap.percent > 80:
            warnings.append(f"High swap usage: {swap.percent:.1f}%")
            score -= 5
        
        # Battery Check (if available)
        try:
            battery = psutil.sensors_battery()
            if battery:
                if battery.percent < 20 and not battery.power_plugged:
                    warnings.append(f"Low battery: {battery.percent}%")
                    score -= 5
                elif battery.power_plugged:
                    good.append(f"Battery charging: {battery.percent}%")
        except:
            pass
        
        # Temperature Check (if available)
        try:
            temps = psutil.sensors_temperatures()
            for name, entries in temps.items():
                for entry in entries:
                    if entry.current > 85:
                        issues.append(f"High temperature: {name} at {entry.current}°C")
                        score -= 10
        except:
            pass
        
        score = max(0, score)
        
        if score >= 80:
            status = "healthy"
        elif score >= 60:
            status = "fair"
        elif score >= 40:
            status = "concerning"
        else:
            status = "critical"
        
        return ToolResult(
            success=True,
            data={
                "score": score,
                "status": status,
                "issues": issues,
                "warnings": warnings,
                "good": good,
                "checked_at": datetime.now().isoformat()
            },
            message=f"System Health Score: {score}/100 ({status})"
        )

    def _performance_analysis(self, **kwargs) -> ToolResult:
        """Analyze system performance."""
        analysis = {}
        
        # CPU analysis
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)
        
        analysis["cpu"] = {
            "cores": cpu_count,
            "frequency_mhz": cpu_freq.current if cpu_freq else None,
            "usage_per_core": cpu_percent_per_core,
            "average_usage": sum(cpu_percent_per_core) / len(cpu_percent_per_core) if cpu_percent_per_core else 0
        }
        
        # Memory analysis
        mem = psutil.virtual_memory()
        analysis["memory"] = {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent
        }
        
        # Process analysis
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] > 0 or info['memory_percent'] > 0:
                    processes.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "cpu": round(info['cpu_percent'], 1),
                        "memory": round(info['memory_percent'], 1)
                    })
            except:
                continue
        
        processes.sort(key=lambda x: x['cpu'] + x['memory'], reverse=True)
        analysis["top_processes"] = processes[:10]
        
        # IO analysis
        io = psutil.disk_io_counters()
        if io:
            analysis["disk_io"] = {
                "read_mb": round(io.read_bytes / (1024**2), 2),
                "write_mb": round(io.write_bytes / (1024**2), 2)
            }
        
        # Network analysis
        net_io = psutil.net_io_counters()
        analysis["network_io"] = {
            "sent_mb": round(net_io.bytes_sent / (1024**2), 2),
            "received_mb": round(net_io.bytes_recv / (1024**2), 2)
        }
        
        return ToolResult(
            success=True,
            data=analysis,
            message="Performance analysis complete"
        )

    def _get_recommendations(self, **kwargs) -> ToolResult:
        """Get system recommendations based on current state."""
        recommendations = []
        
        # Check memory
        mem = psutil.virtual_memory()
        if mem.percent > 80:
            recommendations.append({
                "type": "memory",
                "priority": "high",
                "issue": f"High memory usage ({mem.percent:.1f}%)",
                "action": "Close unused applications or consider adding more RAM",
                "command": "process_tool --action list --sort memory"
            })
        
        # Check CPU
        cpu = psutil.cpu_percent(interval=1)
        if cpu > 80:
            recommendations.append({
                "type": "cpu",
                "priority": "high",
                "issue": f"High CPU usage ({cpu:.1f}%)",
                "action": "Identify and manage resource-heavy processes",
                "command": "process_tool --action list --sort cpu"
            })
        
        # Check disk
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                if usage.percent > 85:
                    recommendations.append({
                        "type": "disk",
                        "priority": "medium" if usage.percent < 95 else "high",
                        "issue": f"Disk '{partition.mountpoint}' at {usage.percent:.1f}%",
                        "action": "Clean up unnecessary files and old downloads",
                        "command": f"smart_search_tool --action storage_analysis"
                    })
            except:
                continue
        
        # Check for too many processes
        process_count = len(list(psutil.process_iter()))
        if process_count > 200:
            recommendations.append({
                "type": "processes",
                "priority": "low",
                "issue": f"Many running processes ({process_count})",
                "action": "Review and close unnecessary background applications",
                "command": "process_tool --action list"
            })
        
        # General recommendations
        recommendations.extend([
            {
                "type": "maintenance",
                "priority": "low",
                "issue": "Regular maintenance",
                "action": "Update system packages",
                "command": "package_manager_tool --action upgrade"
            },
            {
                "type": "backup",
                "priority": "low",
                "issue": "Data protection",
                "action": "Ensure important files are backed up",
                "command": "workflow_tool --action create_from_template --template backup_workflow"
            }
        ])
        
        return ToolResult(
            success=True,
            data={"recommendations": recommendations, "count": len(recommendations)},
            message=f"Generated {len(recommendations)} recommendations"
        )

    def _security_scan(self, **kwargs) -> ToolResult:
        """Perform basic security scan."""
        findings = []
        
        platform = detect_platform()
        
        # Check for open ports
        connections = psutil.net_connections(kind='inet')
        listening = [c for c in connections if c.status == 'LISTEN']
        if listening:
            ports = list(set(c.laddr.port for c in listening if c.laddr))
            findings.append({
                "type": "network",
                "severity": "info",
                "finding": f"Open ports detected: {ports[:10]}",
                "recommendation": "Review if all listening services are necessary"
            })
        
        # Check for root/admin processes
        try:
            if platform != Platform.WINDOWS:
                root_procs = []
                for proc in psutil.process_iter(['pid', 'name', 'username']):
                    try:
                        if proc.info['username'] == 'root':
                            root_procs.append(proc.info['name'])
                    except:
                        continue
                
                if len(set(root_procs)) > 20:
                    findings.append({
                        "type": "processes",
                        "severity": "info",
                        "finding": f"Many processes running as root: {len(set(root_procs))}",
                        "recommendation": "Review privileged processes"
                    })
        except:
            pass
        
        # Check SSH config (Linux/Mac)
        if platform != Platform.WINDOWS:
            ssh_config = Path.home() / ".ssh"
            if ssh_config.exists():
                # Check authorized_keys permissions
                auth_keys = ssh_config / "authorized_keys"
                if auth_keys.exists():
                    mode = oct(auth_keys.stat().st_mode)[-3:]
                    if mode not in ['600', '644']:
                        findings.append({
                            "type": "ssh",
                            "severity": "warning",
                            "finding": f"SSH authorized_keys has unusual permissions: {mode}",
                            "recommendation": "Set permissions to 600"
                        })
                
                # Check for private keys
                private_keys = list(ssh_config.glob("id_*"))
                private_keys = [k for k in private_keys if not k.name.endswith('.pub')]
                if private_keys:
                    findings.append({
                        "type": "ssh",
                        "severity": "info",
                        "finding": f"Found {len(private_keys)} SSH private keys",
                        "recommendation": "Ensure private keys are password-protected"
                    })
        
        # Check for common risky files
        risky_patterns = [".env", "credentials", "secrets", "password"]
        home = Path.home()
        for pattern in risky_patterns:
            try:
                matches = list(home.rglob(f"*{pattern}*"))[:3]
                if matches:
                    findings.append({
                        "type": "files",
                        "severity": "info",
                        "finding": f"Found files matching '{pattern}'",
                        "recommendation": "Ensure sensitive files are properly secured"
                    })
            except:
                continue
        
        return ToolResult(
            success=True,
            data={"findings": findings, "count": len(findings)},
            message=f"Security scan found {len(findings)} items to review"
        )

    def _find_resource_hogs(self, **kwargs) -> ToolResult:
        """Find processes consuming the most resources."""
        hogs = {
            "cpu": [],
            "memory": [],
            "disk": []
        }
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] > 5:
                    hogs["cpu"].append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "percent": round(info['cpu_percent'], 1)
                    })
                if info['memory_percent'] > 2:
                    hogs["memory"].append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "percent": round(info['memory_percent'], 1)
                    })
            except:
                continue
        
        hogs["cpu"].sort(key=lambda x: x['percent'], reverse=True)
        hogs["memory"].sort(key=lambda x: x['percent'], reverse=True)
        hogs["cpu"] = hogs["cpu"][:5]
        hogs["memory"] = hogs["memory"][:5]
        
        total_hogs = len(hogs["cpu"]) + len(hogs["memory"])
        
        return ToolResult(
            success=True,
            data=hogs,
            message=f"Found {total_hogs} resource-intensive processes"
        )

    def _startup_analysis(self, **kwargs) -> ToolResult:
        """Analyze startup items."""
        platform = detect_platform()
        startup_items = []
        
        try:
            if platform == Platform.MACOS:
                # Check LaunchAgents
                for path in [
                    Path.home() / "Library/LaunchAgents",
                    Path("/Library/LaunchAgents"),
                    Path("/Library/LaunchDaemons")
                ]:
                    if path.exists():
                        for f in path.glob("*.plist"):
                            startup_items.append({
                                "name": f.stem,
                                "path": str(f),
                                "type": "LaunchAgent"
                            })
                            
            elif platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["powershell", "-Command", 
                     "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location"],
                    capture_output=True, text=True
                )
                for line in result.stdout.strip().split("\n")[2:]:
                    if line.strip():
                        startup_items.append({"name": line.strip(), "type": "startup"})
                        
            else:  # Linux
                autostart = Path.home() / ".config/autostart"
                if autostart.exists():
                    for f in autostart.glob("*.desktop"):
                        startup_items.append({
                            "name": f.stem,
                            "path": str(f),
                            "type": "autostart"
                        })
                        
                # Check systemd user units
                systemd_user = Path.home() / ".config/systemd/user"
                if systemd_user.exists():
                    for f in systemd_user.glob("*.service"):
                        startup_items.append({
                            "name": f.stem,
                            "path": str(f),
                            "type": "systemd_user"
                        })
            
            return ToolResult(
                success=True,
                data={"items": startup_items, "count": len(startup_items)},
                message=f"Found {len(startup_items)} startup items"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Startup analysis failed: {str(e)}"
            )

    def _storage_analysis(self, **kwargs) -> ToolResult:
        """Analyze storage usage and find large files."""
        path = kwargs.get("path", str(Path.home()))
        large_files = []
        large_dirs = []
        
        try:
            # Find large files
            for root, dirs, files in os.walk(path):
                # Skip hidden and system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
                
                for f in files:
                    try:
                        fp = Path(root) / f
                        size = fp.stat().st_size
                        if size > 100 * 1024 * 1024:  # > 100MB
                            large_files.append({
                                "path": str(fp),
                                "size_mb": round(size / (1024**2), 2)
                            })
                    except:
                        continue
                
                if len(large_files) > 20:
                    break
            
            large_files.sort(key=lambda x: x['size_mb'], reverse=True)
            large_files = large_files[:10]
            
            # Check common directories
            common_dirs = [
                Path.home() / "Downloads",
                Path.home() / "Documents",
                Path.home() / ".cache",
                Path("/tmp")
            ]
            
            for d in common_dirs:
                if d.exists():
                    try:
                        total_size = sum(f.stat().st_size for f in d.rglob('*') if f.is_file())
                        large_dirs.append({
                            "path": str(d),
                            "size_mb": round(total_size / (1024**2), 2)
                        })
                    except:
                        continue
            
            large_dirs.sort(key=lambda x: x['size_mb'], reverse=True)
            
            return ToolResult(
                success=True,
                data={
                    "large_files": large_files,
                    "directory_sizes": large_dirs
                },
                message=f"Found {len(large_files)} large files"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Storage analysis failed: {str(e)}"
            )

    def _network_analysis(self, **kwargs) -> ToolResult:
        """Analyze network connections and usage."""
        analysis = {}
        
        # Get all connections
        connections = psutil.net_connections(kind='inet')
        
        analysis["summary"] = {
            "total_connections": len(connections),
            "established": len([c for c in connections if c.status == 'ESTABLISHED']),
            "listening": len([c for c in connections if c.status == 'LISTEN']),
            "time_wait": len([c for c in connections if c.status == 'TIME_WAIT'])
        }
        
        # Get listening ports
        analysis["listening_ports"] = []
        for c in connections:
            if c.status == 'LISTEN' and c.laddr:
                try:
                    proc = psutil.Process(c.pid) if c.pid else None
                    analysis["listening_ports"].append({
                        "port": c.laddr.port,
                        "process": proc.name() if proc else "unknown",
                        "pid": c.pid
                    })
                except:
                    analysis["listening_ports"].append({
                        "port": c.laddr.port,
                        "process": "unknown",
                        "pid": c.pid
                    })
        
        # Get network interfaces
        analysis["interfaces"] = []
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == 2:  # IPv4
                    analysis["interfaces"].append({
                        "name": name,
                        "address": addr.address
                    })
                    break
        
        # Network IO
        io = psutil.net_io_counters()
        analysis["io"] = {
            "bytes_sent": io.bytes_sent,
            "bytes_recv": io.bytes_recv,
            "packets_sent": io.packets_sent,
            "packets_recv": io.packets_recv
        }
        
        return ToolResult(
            success=True,
            data=analysis,
            message=f"Network analysis: {analysis['summary']['total_connections']} connections"
        )

    def _get_optimizations(self, **kwargs) -> ToolResult:
        """Get system optimization suggestions."""
        optimizations = []
        
        # Memory optimization
        mem = psutil.virtual_memory()
        if mem.percent > 70:
            optimizations.append({
                "area": "memory",
                "action": "Close unused applications",
                "impact": "high",
                "command": "process_tool --action list --sort memory"
            })
        
        # Cache cleanup
        cache_dir = Path.home() / ".cache"
        if cache_dir.exists():
            try:
                cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                if cache_size > 1024**3:  # > 1GB
                    optimizations.append({
                        "area": "storage",
                        "action": f"Clear cache ({cache_size // (1024**2)} MB)",
                        "impact": "medium",
                        "command": f"file_tool --action delete --path {cache_dir}"
                    })
            except:
                pass
        
        # Downloads cleanup
        downloads = Path.home() / "Downloads"
        if downloads.exists():
            try:
                old_files = [f for f in downloads.iterdir() if f.is_file()]
                if len(old_files) > 50:
                    optimizations.append({
                        "area": "organization",
                        "action": f"Organize Downloads folder ({len(old_files)} files)",
                        "impact": "low",
                        "command": "file_tool --action list --path ~/Downloads"
                    })
            except:
                pass
        
        # System update
        optimizations.append({
            "area": "security",
            "action": "Check for system updates",
            "impact": "medium",
            "command": "package_manager_tool --action update"
        })
        
        return ToolResult(
            success=True,
            data={"optimizations": optimizations},
            message=f"Found {len(optimizations)} optimization opportunities"
        )

    def _quick_insights(self, **kwargs) -> ToolResult:
        """Get quick system insights summary."""
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        insights = {
            "cpu_usage": f"{cpu:.1f}%",
            "memory_usage": f"{mem.percent:.1f}%",
            "disk_usage": f"{disk.percent:.1f}%",
            "running_processes": len(list(psutil.process_iter())),
            "status": "healthy"
        }
        
        if cpu > 80 or mem.percent > 80 or disk.percent > 90:
            insights["status"] = "attention_needed"
        
        # Quick tips based on status
        tips = []
        if cpu > 70:
            tips.append("High CPU - check running processes")
        if mem.percent > 70:
            tips.append("High memory - close unused apps")
        if disk.percent > 80:
            tips.append("Low disk space - clean up files")
        
        insights["tips"] = tips if tips else ["System running smoothly"]
        
        return ToolResult(
            success=True,
            data=insights,
            message=f"CPU: {cpu:.0f}% | Memory: {mem.percent:.0f}% | Disk: {disk.percent:.0f}%"
        )

    def get_usage_examples(self) -> List[str]:
        return [
            "Health check: system_insights_tool --action health_check",
            "Performance: system_insights_tool --action performance",
            "Get recommendations: system_insights_tool --action recommendations",
            "Security scan: system_insights_tool --action security_scan",
            "Find resource hogs: system_insights_tool --action resource_hogs",
            "Quick insights: system_insights_tool --action quick_insights",
        ]
