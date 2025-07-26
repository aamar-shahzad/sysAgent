"""
Monitoring tool for SysAgent CLI.
"""

import os
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory, PermissionLevel


@dataclass
class Alert:
    """Represents a monitoring alert."""
    id: str
    name: str
    condition: str
    threshold: float
    current_value: float
    severity: str
    triggered: bool
    created_at: datetime
    last_triggered: Optional[datetime]


@dataclass
class Metric:
    """Represents a system metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str


@register_tool
class MonitoringTool(BaseTool):
    """Tool for monitoring operations."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="monitoring_tool",
            description="System monitoring and performance tracking",
            category=ToolCategory.MONITORING,
            permissions=["monitoring_operations"],
            version="1.0.0"
        )
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.alerts_file = os.path.expanduser("~/.sysagent/alerts.json")
        self.metrics_file = os.path.expanduser("~/.sysagent/metrics.json")
        self._ensure_directories()
        self._load_data()
        self.monitoring_active = False
        self.monitoring_thread = None
    
    def _ensure_directories(self):
        """Ensure monitoring directories exist."""
        os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
    
    def _load_data(self):
        """Load alerts and metrics from files."""
        self.alerts = {}
        self.metrics = []
        
        # Load alerts
        if os.path.exists(self.alerts_file):
            try:
                with open(self.alerts_file, 'r') as f:
                    data = json.load(f)
                    for alert_id, alert_data in data.items():
                        self.alerts[alert_id] = Alert(**alert_data)
            except:
                pass
        
        # Load metrics (keep only last 1000)
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    self.metrics = [Metric(**metric) for metric in data[-1000:]]
            except:
                pass
    
    def _save_data(self):
        """Save alerts and metrics to files."""
        # Save alerts
        alerts_data = {}
        for alert_id, alert in self.alerts.items():
            alerts_data[alert_id] = {
                "id": alert.id,
                "name": alert.name,
                "condition": alert.condition,
                "threshold": alert.threshold,
                "current_value": alert.current_value,
                "severity": alert.severity,
                "triggered": alert.triggered,
                "created_at": alert.created_at.isoformat(),
                "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None
            }
        
        with open(self.alerts_file, 'w') as f:
            json.dump(alerts_data, f, indent=2)
        
        # Save metrics (keep only last 1000)
        metrics_data = []
        for metric in self.metrics[-1000:]:
            metrics_data.append({
                "name": metric.name,
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "category": metric.category
            })
        
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
    
    def _execute(self, action: str, alert_id: str = None, name: str = None,
                 condition: str = None, threshold: float = None, severity: str = "medium",
                 duration: int = 60, **kwargs) -> ToolResult:
        """Execute monitoring action."""
        
        try:
            if action == "create_alert":
                return self._create_alert(name, condition, threshold, severity)
            elif action == "list_alerts":
                return self._list_alerts()
            elif action == "delete_alert":
                return self._delete_alert(alert_id)
            elif action == "check_alerts":
                return self._check_alerts()
            elif action == "get_metrics":
                return self._get_metrics(duration)
            elif action == "start_monitoring":
                return self._start_monitoring()
            elif action == "stop_monitoring":
                return self._stop_monitoring()
            elif action == "get_performance":
                return self._get_performance()
            elif action == "get_resource_usage":
                return self._get_resource_usage()
            elif action == "get_system_health":
                return self._get_system_health()
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
                message=f"Monitoring operation failed: {str(e)}",
                error=str(e)
            )
    
    def _create_alert(self, name: str, condition: str, threshold: float, severity: str) -> ToolResult:
        """Create a new monitoring alert."""
        try:
            if not name or not condition or threshold is None:
                return ToolResult(
                    success=False,
                    data={},
                    message="Name, condition, and threshold are required",
                    error="Missing required parameters"
                )
            
            alert_id = f"alert_{int(time.time())}"
            now = datetime.now()
            
            alert = Alert(
                id=alert_id,
                name=name,
                condition=condition,
                threshold=threshold,
                current_value=0.0,
                severity=severity,
                triggered=False,
                created_at=now,
                last_triggered=None
            )
            
            self.alerts[alert_id] = alert
            self._save_data()
            
            return ToolResult(
                success=True,
                data={
                    "alert_id": alert_id,
                    "alert": {
                        "id": alert.id,
                        "name": alert.name,
                        "condition": alert.condition,
                        "threshold": alert.threshold,
                        "severity": alert.severity
                    }
                },
                message=f"Alert '{name}' created successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to create alert: {str(e)}",
                error=str(e)
            )
    
    def _list_alerts(self) -> ToolResult:
        """List all monitoring alerts."""
        try:
            alerts_list = []
            for alert in self.alerts.values():
                alerts_list.append({
                    "id": alert.id,
                    "name": alert.name,
                    "condition": alert.condition,
                    "threshold": alert.threshold,
                    "current_value": alert.current_value,
                    "severity": alert.severity,
                    "triggered": alert.triggered,
                    "created_at": alert.created_at.isoformat(),
                    "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None
                })
            
            return ToolResult(
                success=True,
                data={
                    "alerts": alerts_list,
                    "total": len(alerts_list)
                },
                message=f"Found {len(alerts_list)} monitoring alerts"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list alerts: {str(e)}",
                error=str(e)
            )
    
    def _delete_alert(self, alert_id: str) -> ToolResult:
        """Delete a monitoring alert."""
        try:
            if alert_id not in self.alerts:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Alert '{alert_id}' not found",
                    error="Alert not found"
                )
            
            alert_name = self.alerts[alert_id].name
            del self.alerts[alert_id]
            self._save_data()
            
            return ToolResult(
                success=True,
                data={"alert_id": alert_id},
                message=f"Alert '{alert_name}' deleted successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to delete alert: {str(e)}",
                error=str(e)
            )
    
    def _check_alerts(self) -> ToolResult:
        """Check all alerts against current metrics."""
        try:
            import psutil
            
            triggered_alerts = []
            
            # Get current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check each alert
            for alert in self.alerts.values():
                current_value = 0.0
                
                if alert.condition == "cpu_percent":
                    current_value = cpu_percent
                elif alert.condition == "memory_percent":
                    current_value = memory.percent
                elif alert.condition == "disk_percent":
                    current_value = disk.percent
                
                alert.current_value = current_value
                
                # Check if alert should be triggered
                if current_value > alert.threshold and not alert.triggered:
                    alert.triggered = True
                    alert.last_triggered = datetime.now()
                    triggered_alerts.append({
                        "id": alert.id,
                        "name": alert.name,
                        "condition": alert.condition,
                        "threshold": alert.threshold,
                        "current_value": current_value,
                        "severity": alert.severity
                    })
                elif current_value <= alert.threshold and alert.triggered:
                    alert.triggered = False
            
            self._save_data()
            
            return ToolResult(
                success=True,
                data={
                    "triggered_alerts": triggered_alerts,
                    "total_alerts": len(self.alerts),
                    "triggered_count": len(triggered_alerts)
                },
                message=f"Alert check completed: {len(triggered_alerts)} alerts triggered"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to check alerts: {str(e)}",
                error=str(e)
            )
    
    def _get_metrics(self, duration: int = 60) -> ToolResult:
        """Get system metrics for the specified duration."""
        try:
            import psutil
            
            now = datetime.now()
            cutoff_time = now - timedelta(seconds=duration)
            
            # Filter metrics by time
            recent_metrics = [
                metric for metric in self.metrics
                if metric.timestamp >= cutoff_time
            ]
            
            # Group by category
            metrics_by_category = {}
            for metric in recent_metrics:
                if metric.category not in metrics_by_category:
                    metrics_by_category[metric.category] = []
                metrics_by_category[metric.category].append({
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat()
                })
            
            return ToolResult(
                success=True,
                data={
                    "metrics": metrics_by_category,
                    "duration_seconds": duration,
                    "total_metrics": len(recent_metrics)
                },
                message=f"Retrieved {len(recent_metrics)} metrics for the last {duration} seconds"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get metrics: {str(e)}",
                error=str(e)
            )
    
    def _start_monitoring(self) -> ToolResult:
        """Start continuous monitoring."""
        try:
            if self.monitoring_active:
                return ToolResult(
                    success=False,
                    data={},
                    message="Monitoring is already active",
                    error="Monitoring already active"
                )
            
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            return ToolResult(
                success=True,
                data={"monitoring_active": True},
                message="Continuous monitoring started successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to start monitoring: {str(e)}",
                error=str(e)
            )
    
    def _stop_monitoring(self) -> ToolResult:
        """Stop continuous monitoring."""
        try:
            if not self.monitoring_active:
                return ToolResult(
                    success=False,
                    data={},
                    message="Monitoring is not active",
                    error="Monitoring not active"
                )
            
            self.monitoring_active = False
            
            return ToolResult(
                success=True,
                data={"monitoring_active": False},
                message="Continuous monitoring stopped successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to stop monitoring: {str(e)}",
                error=str(e)
            )
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        try:
            import psutil
            
            while self.monitoring_active:
                now = datetime.now()
                
                # Collect metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Add metrics
                self.metrics.extend([
                    Metric("cpu_percent", cpu_percent, "%", now, "cpu"),
                    Metric("memory_percent", memory.percent, "%", now, "memory"),
                    Metric("memory_used", memory.used / 1024 / 1024 / 1024, "GB", now, "memory"),
                    Metric("memory_available", memory.available / 1024 / 1024 / 1024, "GB", now, "memory"),
                    Metric("disk_percent", disk.percent, "%", now, "disk"),
                    Metric("disk_used", disk.used / 1024 / 1024 / 1024, "GB", now, "disk"),
                    Metric("disk_free", disk.free / 1024 / 1024 / 1024, "GB", now, "disk")
                ])
                
                # Check alerts
                for alert in self.alerts.values():
                    current_value = 0.0
                    
                    if alert.condition == "cpu_percent":
                        current_value = cpu_percent
                    elif alert.condition == "memory_percent":
                        current_value = memory.percent
                    elif alert.condition == "disk_percent":
                        current_value = disk.percent
                    
                    alert.current_value = current_value
                    
                    if current_value > alert.threshold and not alert.triggered:
                        alert.triggered = True
                        alert.last_triggered = now
                
                # Save data every 10 iterations
                if len(self.metrics) % 10 == 0:
                    self._save_data()
                
                time.sleep(5)  # Collect metrics every 5 seconds
                
        except Exception as e:
            print(f"Monitoring loop error: {e}")
            self.monitoring_active = False
    
    def _get_performance(self) -> ToolResult:
        """Get current system performance metrics."""
        try:
            import psutil
            
            now = datetime.now()
            
            # Get current metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get CPU frequency
            try:
                cpu_freq = psutil.cpu_freq()
                cpu_freq_current = cpu_freq.current if cpu_freq else 0
            except:
                cpu_freq_current = 0
            
            # Get load average
            try:
                load_avg = os.getloadavg()
            except:
                load_avg = (0, 0, 0)
            
            performance_data = {
                "cpu": {
                    "percent": cpu_percent,
                    "frequency_mhz": cpu_freq_current,
                    "count": psutil.cpu_count(),
                    "load_average": load_avg
                },
                "memory": {
                    "percent": memory.percent,
                    "used_gb": memory.used / 1024 / 1024 / 1024,
                    "available_gb": memory.available / 1024 / 1024 / 1024,
                    "total_gb": memory.total / 1024 / 1024 / 1024
                },
                "disk": {
                    "percent": disk.percent,
                    "used_gb": disk.used / 1024 / 1024 / 1024,
                    "free_gb": disk.free / 1024 / 1024 / 1024,
                    "total_gb": disk.total / 1024 / 1024 / 1024
                },
                "timestamp": now.isoformat()
            }
            
            return ToolResult(
                success=True,
                data=performance_data,
                message="Performance metrics retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get performance: {str(e)}",
                error=str(e)
            )
    
    def _get_resource_usage(self) -> ToolResult:
        """Get detailed resource usage information."""
        try:
            import psutil
            
            # Get process resource usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    info = proc.info
                    if info['cpu_percent'] and info['cpu_percent'] > 0:
                        processes.append({
                            "pid": info['pid'],
                            "name": info['name'],
                            "cpu_percent": info['cpu_percent'],
                            "memory_percent": info['memory_percent'],
                            "memory_mb": info['memory_info'].rss / 1024 / 1024
                        })
                except:
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # Get network usage
            network_io = psutil.net_io_counters()
            
            # Get disk I/O
            disk_io = psutil.disk_io_counters()
            
            resource_usage = {
                "top_processes": processes[:10],
                "network": {
                    "bytes_sent": network_io.bytes_sent,
                    "bytes_recv": network_io.bytes_recv,
                    "packets_sent": network_io.packets_sent,
                    "packets_recv": network_io.packets_recv
                },
                "disk_io": {
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                    "read_count": disk_io.read_count if disk_io else 0,
                    "write_count": disk_io.write_count if disk_io else 0
                }
            }
            
            return ToolResult(
                success=True,
                data=resource_usage,
                message="Resource usage information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get resource usage: {str(e)}",
                error=str(e)
            )
    
    def _get_system_health(self) -> ToolResult:
        """Get overall system health assessment."""
        try:
            import psutil
            
            health_score = 100
            issues = []
            warnings = []
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                health_score -= 30
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                health_score -= 10
                warnings.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                health_score -= 30
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 80:
                health_score -= 15
                warnings.append(f"High memory usage: {memory.percent:.1f}%")
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 95:
                health_score -= 25
                issues.append(f"Critical disk usage: {disk.percent:.1f}%")
            elif disk.percent > 85:
                health_score -= 10
                warnings.append(f"High disk usage: {disk.percent:.1f}%")
            
            # Check for too many processes
            process_count = len(list(psutil.process_iter()))
            if process_count > 500:
                health_score -= 10
                warnings.append(f"High process count: {process_count}")
            
            # Determine health status
            if health_score >= 80:
                status = "healthy"
            elif health_score >= 60:
                status = "warning"
            else:
                status = "critical"
            
            system_health = {
                "health_score": health_score,
                "status": status,
                "issues": issues,
                "warnings": warnings,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "process_count": process_count
                }
            }
            
            return ToolResult(
                success=True,
                data=system_health,
                message=f"System health assessment: {status} (score: {health_score})"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get system health: {str(e)}",
                error=str(e)
            ) 