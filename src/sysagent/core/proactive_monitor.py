"""
Proactive Monitoring System for SysAgent.
Monitors system health and provides intelligent alerts.
"""

import threading
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    CPU_HIGH = "cpu_high"
    MEMORY_HIGH = "memory_high"
    DISK_LOW = "disk_low"
    DISK_FULL = "disk_full"
    PROCESS_HUNG = "process_hung"
    NETWORK_DOWN = "network_down"
    BATTERY_LOW = "battery_low"
    TEMP_HIGH = "temp_high"
    LARGE_FILE_DOWNLOAD = "large_file_download"
    SECURITY_ISSUE = "security_issue"
    MAINTENANCE_NEEDED = "maintenance_needed"


@dataclass
class Alert:
    """Represents a system alert."""
    id: str
    alert_type: str
    level: str
    title: str
    message: str
    suggestion: str = ""
    action: str = ""  # Command to execute
    timestamp: str = ""
    dismissed: bool = False
    auto_dismiss_at: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.id:
            self.id = f"alert_{int(time.time() * 1000)}"


@dataclass
class MonitorConfig:
    """Configuration for monitoring thresholds."""
    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0
    memory_warning_percent: float = 80.0
    memory_critical_percent: float = 95.0
    disk_warning_percent: float = 80.0
    disk_critical_percent: float = 95.0
    battery_warning_percent: float = 20.0
    battery_critical_percent: float = 10.0
    check_interval_seconds: int = 30
    alert_cooldown_minutes: int = 5


class ProactiveMonitor:
    """
    Background monitoring system that detects issues proactively.
    
    Features:
    - CPU/Memory/Disk monitoring with thresholds
    - Battery monitoring
    - Network connectivity checks
    - Process health monitoring
    - Maintenance suggestions
    - Smart alert aggregation
    """
    
    def __init__(self, config: Optional[MonitorConfig] = None,
                 on_alert: Optional[Callable[[Alert], None]] = None):
        self.config = config or MonitorConfig()
        self.on_alert = on_alert
        
        self.data_dir = Path.home() / ".config" / "sysagent" / "monitoring"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.alerts_file = self.data_dir / "alerts.json"
        self.config_file = self.data_dir / "config.json"
        
        self.alerts: Dict[str, Alert] = {}
        self.alert_cooldowns: Dict[str, datetime] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        self._load_alerts()
        self._load_config()
    
    def _load_alerts(self):
        """Load saved alerts."""
        if self.alerts_file.exists():
            try:
                data = json.loads(self.alerts_file.read_text())
                self.alerts = {k: Alert(**v) for k, v in data.items()}
            except Exception:
                pass
    
    def _save_alerts(self):
        """Save alerts."""
        try:
            self.alerts_file.write_text(json.dumps(
                {k: asdict(v) for k, v in self.alerts.items()},
                indent=2
            ))
        except Exception:
            pass
    
    def _load_config(self):
        """Load monitoring config."""
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                for key, value in data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
            except Exception:
                pass
    
    def save_config(self):
        """Save monitoring config."""
        try:
            self.config_file.write_text(json.dumps(asdict(self.config), indent=2))
        except Exception:
            pass
    
    def start(self):
        """Start background monitoring."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop background monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                self._check_system()
            except Exception:
                pass
            
            time.sleep(self.config.check_interval_seconds)
    
    def _check_system(self):
        """Run all system checks."""
        if not PSUTIL_AVAILABLE:
            return
        
        self._check_cpu()
        self._check_memory()
        self._check_disk()
        self._check_battery()
        self._check_network()
        self._check_maintenance()
    
    def _can_alert(self, alert_type: str) -> bool:
        """Check if we can send an alert (cooldown)."""
        if alert_type in self.alert_cooldowns:
            cooldown_until = self.alert_cooldowns[alert_type]
            if datetime.now() < cooldown_until:
                return False
        return True
    
    def _set_cooldown(self, alert_type: str):
        """Set cooldown for an alert type."""
        self.alert_cooldowns[alert_type] = (
            datetime.now() + timedelta(minutes=self.config.alert_cooldown_minutes)
        )
    
    def _send_alert(self, alert: Alert):
        """Send an alert."""
        if not self._can_alert(alert.alert_type):
            return
        
        self.alerts[alert.id] = alert
        self._set_cooldown(alert.alert_type)
        self._save_alerts()
        
        if self.on_alert:
            try:
                self.on_alert(alert)
            except Exception:
                pass
    
    def _check_cpu(self):
        """Check CPU usage."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            
            if cpu >= self.config.cpu_critical_percent:
                self._send_alert(Alert(
                    id="",
                    alert_type=AlertType.CPU_HIGH.value,
                    level=AlertLevel.CRITICAL.value,
                    title="Critical CPU Usage",
                    message=f"CPU is at {cpu:.0f}% - system may become unresponsive",
                    suggestion="Close unnecessary applications or identify heavy processes",
                    action="Show top CPU consuming processes"
                ))
            elif cpu >= self.config.cpu_warning_percent:
                self._send_alert(Alert(
                    id="",
                    alert_type=AlertType.CPU_HIGH.value,
                    level=AlertLevel.WARNING.value,
                    title="High CPU Usage",
                    message=f"CPU is at {cpu:.0f}%",
                    suggestion="Consider closing some applications",
                    action="Show processes using most CPU"
                ))
        except Exception:
            pass
    
    def _check_memory(self):
        """Check memory usage."""
        try:
            mem = psutil.virtual_memory()
            percent = mem.percent
            
            if percent >= self.config.memory_critical_percent:
                available_gb = mem.available / (1024**3)
                self._send_alert(Alert(
                    id="",
                    alert_type=AlertType.MEMORY_HIGH.value,
                    level=AlertLevel.CRITICAL.value,
                    title="Critical Memory Usage",
                    message=f"Memory is at {percent:.0f}% - only {available_gb:.1f}GB free",
                    suggestion="Close memory-heavy applications immediately",
                    action="Show memory consuming processes"
                ))
            elif percent >= self.config.memory_warning_percent:
                self._send_alert(Alert(
                    id="",
                    alert_type=AlertType.MEMORY_HIGH.value,
                    level=AlertLevel.WARNING.value,
                    title="High Memory Usage",
                    message=f"Memory is at {percent:.0f}%",
                    suggestion="Consider closing some applications",
                    action="Show memory usage"
                ))
        except Exception:
            pass
    
    def _check_disk(self):
        """Check disk usage."""
        try:
            # Check main partitions
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    percent = usage.percent
                    free_gb = usage.free / (1024**3)
                    
                    if percent >= self.config.disk_critical_percent:
                        self._send_alert(Alert(
                            id="",
                            alert_type=AlertType.DISK_FULL.value,
                            level=AlertLevel.CRITICAL.value,
                            title=f"Disk Almost Full: {partition.mountpoint}",
                            message=f"Only {free_gb:.1f}GB free ({percent:.0f}% used)",
                            suggestion="Delete large files or move data to external storage",
                            action="Find large files"
                        ))
                    elif percent >= self.config.disk_warning_percent:
                        self._send_alert(Alert(
                            id="",
                            alert_type=AlertType.DISK_LOW.value,
                            level=AlertLevel.WARNING.value,
                            title=f"Disk Space Low: {partition.mountpoint}",
                            message=f"{free_gb:.1f}GB free ({percent:.0f}% used)",
                            suggestion="Consider cleaning up temporary files",
                            action="Clean temporary files"
                        ))
                except Exception:
                    continue
        except Exception:
            pass
    
    def _check_battery(self):
        """Check battery status."""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return
            
            percent = battery.percent
            plugged = battery.power_plugged
            
            if not plugged:
                if percent <= self.config.battery_critical_percent:
                    self._send_alert(Alert(
                        id="",
                        alert_type=AlertType.BATTERY_LOW.value,
                        level=AlertLevel.CRITICAL.value,
                        title="Battery Critically Low",
                        message=f"Battery at {percent}% - connect charger immediately",
                        suggestion="Save your work and connect charger",
                        action=""
                    ))
                elif percent <= self.config.battery_warning_percent:
                    self._send_alert(Alert(
                        id="",
                        alert_type=AlertType.BATTERY_LOW.value,
                        level=AlertLevel.WARNING.value,
                        title="Battery Low",
                        message=f"Battery at {percent}%",
                        suggestion="Consider connecting charger soon",
                        action=""
                    ))
        except Exception:
            pass
    
    def _check_network(self):
        """Check network connectivity."""
        try:
            import socket
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=3)
            except OSError:
                self._send_alert(Alert(
                    id="",
                    alert_type=AlertType.NETWORK_DOWN.value,
                    level=AlertLevel.WARNING.value,
                    title="Network Connection Issue",
                    message="Unable to reach the internet",
                    suggestion="Check your network connection",
                    action="Run network diagnostics"
                ))
        except Exception:
            pass
    
    def _check_maintenance(self):
        """Check if maintenance is needed."""
        try:
            # Check temp files
            temp_dirs = [
                Path("/tmp"),
                Path.home() / ".cache",
                Path.home() / "Library" / "Caches" if Path.home().joinpath("Library").exists() else None
            ]
            
            total_temp_size = 0
            for temp_dir in temp_dirs:
                if temp_dir and temp_dir.exists():
                    try:
                        for f in temp_dir.rglob("*"):
                            if f.is_file():
                                total_temp_size += f.stat().st_size
                    except Exception:
                        pass
            
            temp_size_gb = total_temp_size / (1024**3)
            if temp_size_gb > 5:  # More than 5GB in temp
                self._send_alert(Alert(
                    id="",
                    alert_type=AlertType.MAINTENANCE_NEEDED.value,
                    level=AlertLevel.INFO.value,
                    title="Cleanup Recommended",
                    message=f"Temporary files using {temp_size_gb:.1f}GB",
                    suggestion="Run cleanup to free disk space",
                    action="Clean temporary files"
                ))
        except Exception:
            pass
    
    # === Alert Management ===
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (non-dismissed) alerts."""
        now = datetime.now()
        active = []
        for alert in self.alerts.values():
            if alert.dismissed:
                continue
            if alert.auto_dismiss_at:
                try:
                    dismiss_at = datetime.fromisoformat(alert.auto_dismiss_at)
                    if now > dismiss_at:
                        alert.dismissed = True
                        continue
                except Exception:
                    pass
            active.append(alert)
        return sorted(active, key=lambda x: x.timestamp, reverse=True)
    
    def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].dismissed = True
            self._save_alerts()
            return True
        return False
    
    def dismiss_all(self) -> int:
        """Dismiss all alerts."""
        count = 0
        for alert in self.alerts.values():
            if not alert.dismissed:
                alert.dismissed = True
                count += 1
        self._save_alerts()
        return count
    
    def get_alert_history(self, limit: int = 50) -> List[Alert]:
        """Get alert history."""
        all_alerts = list(self.alerts.values())
        return sorted(all_alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def clear_old_alerts(self, days: int = 7) -> int:
        """Clear alerts older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []
        for alert_id, alert in self.alerts.items():
            try:
                ts = datetime.fromisoformat(alert.timestamp)
                if ts < cutoff:
                    to_remove.append(alert_id)
            except Exception:
                pass
        
        for alert_id in to_remove:
            del self.alerts[alert_id]
        
        self._save_alerts()
        return len(to_remove)
    
    # === Manual Checks ===
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run a comprehensive health check."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': [],
            'metrics': {}
        }
        
        if not PSUTIL_AVAILABLE:
            results['status'] = 'unknown'
            results['issues'].append('psutil not available')
            return results
        
        try:
            # CPU
            cpu = psutil.cpu_percent(interval=1)
            results['metrics']['cpu_percent'] = cpu
            if cpu >= self.config.cpu_warning_percent:
                results['issues'].append(f"High CPU: {cpu}%")
                results['status'] = 'warning'
            
            # Memory
            mem = psutil.virtual_memory()
            results['metrics']['memory_percent'] = mem.percent
            results['metrics']['memory_available_gb'] = mem.available / (1024**3)
            if mem.percent >= self.config.memory_warning_percent:
                results['issues'].append(f"High Memory: {mem.percent}%")
                results['status'] = 'warning'
            
            # Disk
            disk = psutil.disk_usage('/')
            results['metrics']['disk_percent'] = disk.percent
            results['metrics']['disk_free_gb'] = disk.free / (1024**3)
            if disk.percent >= self.config.disk_warning_percent:
                results['issues'].append(f"Low Disk: {disk.free / (1024**3):.1f}GB free")
                results['status'] = 'warning'
            
            # Battery
            battery = psutil.sensors_battery()
            if battery:
                results['metrics']['battery_percent'] = battery.percent
                results['metrics']['battery_plugged'] = battery.power_plugged
                if not battery.power_plugged and battery.percent < self.config.battery_warning_percent:
                    results['issues'].append(f"Low Battery: {battery.percent}%")
                    results['status'] = 'warning'
            
            # Upgrade to critical if needed
            if any(issue for issue in results['issues'] if 'Critical' in issue or results['metrics'].get('cpu_percent', 0) >= self.config.cpu_critical_percent):
                results['status'] = 'critical'
        
        except Exception as e:
            results['status'] = 'error'
            results['issues'].append(str(e))
        
        return results


# Global instance
_monitor: Optional[ProactiveMonitor] = None


def get_monitor() -> ProactiveMonitor:
    """Get the global monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = ProactiveMonitor()
    return _monitor


def start_monitoring(on_alert: Optional[Callable[[Alert], None]] = None):
    """Start the global monitor."""
    monitor = get_monitor()
    if on_alert:
        monitor.on_alert = on_alert
    monitor.start()
    return monitor


def stop_monitoring():
    """Stop the global monitor."""
    if _monitor:
        _monitor.stop()
