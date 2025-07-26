"""
Security tool for SysAgent CLI.
"""

import os
import subprocess
import hashlib
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory, PermissionLevel


@register_tool
class SecurityTool(BaseTool):
    """Tool for security operations."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="security_tool",
            description="Security audits and vulnerability scanning",
            category=ToolCategory.SECURITY,
            permissions=["security_operations"],
            version="1.0.0"
        )
    
    def _execute(self, action: str, target: str = None, path: str = None, 
                 algorithm: str = "sha256", **kwargs) -> ToolResult:
        """Execute security action."""
        
        try:
            if action == "audit_files":
                return self._audit_files(path)
            elif action == "check_permissions":
                return self._check_permissions(path)
            elif action == "scan_vulnerabilities":
                return self._scan_vulnerabilities(target)
            elif action == "monitor_processes":
                return self._monitor_processes()
            elif action == "check_integrity":
                return self._check_integrity(path, algorithm)
            elif action == "analyze_network":
                return self._analyze_network()
            elif action == "audit_users":
                return self._audit_users()
            elif action == "check_services":
                return self._check_services()
            elif action == "scan_ports":
                return self._scan_ports(target)
            elif action == "monitor_logs":
                return self._monitor_logs()
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
                message=f"Security operation failed: {str(e)}",
                error=str(e)
            )
    
    def _audit_files(self, path: str = None) -> ToolResult:
        """Audit files for security issues."""
        try:
            if not path:
                path = "/"
            
            security_issues = []
            
            # Check for world-writable files
            for root, dirs, files in os.walk(path):
                if any(skip in root for skip in ["/proc", "/sys", "/dev", "/tmp", "/var/tmp"]):
                    continue
                
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            stat = os.stat(file_path)
                            
                            # Check world-writable files
                            if stat.st_mode & 0o002:
                                security_issues.append({
                                    "type": "world_writable",
                                    "file": file_path,
                                    "permission": oct(stat.st_mode)[-3:],
                                    "severity": "medium"
                                })
                            
                            # Check setuid/setgid files
                            if stat.st_mode & 0o4000 or stat.st_mode & 0o2000:
                                security_issues.append({
                                    "type": "setuid_setgid",
                                    "file": file_path,
                                    "permission": oct(stat.st_mode)[-3:],
                                    "severity": "high"
                                })
                                
                    except (OSError, PermissionError):
                        continue
            
            return ToolResult(
                success=True,
                data={
                    "security_issues": security_issues,
                    "total_issues": len(security_issues),
                    "scanned_path": path
                },
                message=f"Security audit completed: {len(security_issues)} issues found"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to audit files: {str(e)}",
                error=str(e)
            )
    
    def _check_permissions(self, path: str = None) -> ToolResult:
        """Check file and directory permissions."""
        try:
            if not path:
                path = "/"
            
            permission_issues = []
            
            for root, dirs, files in os.walk(path):
                if any(skip in root for skip in ["/proc", "/sys", "/dev", "/tmp", "/var/tmp"]):
                    continue
                
                for item in dirs + files:
                    try:
                        item_path = os.path.join(root, item)
                        stat = os.stat(item_path)
                        
                        # Check for overly permissive directories
                        if os.path.isdir(item_path) and stat.st_mode & 0o777 == 0o777:
                            permission_issues.append({
                                "type": "overly_permissive_directory",
                                "path": item_path,
                                "permission": oct(stat.st_mode)[-3:],
                                "severity": "high"
                            })
                        
                        # Check for world-readable sensitive files
                        if os.path.isfile(item_path) and "passwd" in item or "shadow" in item:
                            if stat.st_mode & 0o004:
                                permission_issues.append({
                                    "type": "sensitive_file_world_readable",
                                    "path": item_path,
                                    "permission": oct(stat.st_mode)[-3:],
                                    "severity": "critical"
                                })
                                
                    except (OSError, PermissionError):
                        continue
            
            return ToolResult(
                success=True,
                data={
                    "permission_issues": permission_issues,
                    "total_issues": len(permission_issues),
                    "scanned_path": path
                },
                message=f"Permission check completed: {len(permission_issues)} issues found"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to check permissions: {str(e)}",
                error=str(e)
            )
    
    def _scan_vulnerabilities(self, target: str = None) -> ToolResult:
        """Scan for common vulnerabilities."""
        try:
            vulnerabilities = []
            
            # Check for common vulnerable configurations
            vulnerable_paths = [
                "/etc/passwd",
                "/etc/shadow",
                "/etc/sudoers",
                "/etc/ssh/sshd_config"
            ]
            
            for path in vulnerable_paths:
                if os.path.exists(path):
                    try:
                        stat = os.stat(path)
                        if stat.st_mode & 0o777 != 0o600:
                            vulnerabilities.append({
                                "type": "insecure_permissions",
                                "file": path,
                                "current_permission": oct(stat.st_mode)[-3:],
                                "recommended": "600",
                                "severity": "high"
                            })
                    except:
                        pass
            
            # Check for open network services
            try:
                result = subprocess.run(["netstat", "-tlnp"], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines[1:]:  # Skip header
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 4:
                                address = parts[3]
                                if address.startswith("0.0.0.0:"):
                                    vulnerabilities.append({
                                        "type": "open_network_service",
                                        "service": address,
                                        "severity": "medium"
                                    })
            except:
                pass
            
            return ToolResult(
                success=True,
                data={
                    "vulnerabilities": vulnerabilities,
                    "total_vulnerabilities": len(vulnerabilities)
                },
                message=f"Vulnerability scan completed: {len(vulnerabilities)} vulnerabilities found"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to scan vulnerabilities: {str(e)}",
                error=str(e)
            )
    
    def _monitor_processes(self) -> ToolResult:
        """Monitor processes for suspicious activity."""
        try:
            import psutil
            
            suspicious_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'connections']):
                try:
                    info = proc.info
                    
                    # Check for processes with many network connections
                    if info['connections'] and len(info['connections']) > 10:
                        suspicious_processes.append({
                            "type": "high_network_activity",
                            "pid": info['pid'],
                            "name": info['name'],
                            "connections": len(info['connections'])
                        })
                    
                    # Check for processes with unusual names
                    suspicious_names = ['backdoor', 'trojan', 'malware', 'keylogger']
                    if any(name in info['name'].lower() for name in suspicious_names):
                        suspicious_processes.append({
                            "type": "suspicious_name",
                            "pid": info['pid'],
                            "name": info['name']
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return ToolResult(
                success=True,
                data={
                    "suspicious_processes": suspicious_processes,
                    "total_suspicious": len(suspicious_processes)
                },
                message=f"Process monitoring completed: {len(suspicious_processes)} suspicious processes found"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to monitor processes: {str(e)}",
                error=str(e)
            )
    
    def _check_integrity(self, path: str = None, algorithm: str = "sha256") -> ToolResult:
        """Check file integrity using hashes."""
        try:
            if not path:
                path = "/etc"
            
            integrity_checks = []
            
            # Important system files to check
            important_files = [
                "/etc/passwd",
                "/etc/shadow",
                "/etc/hosts",
                "/etc/resolv.conf",
                "/etc/ssh/sshd_config"
            ]
            
            for file_path in important_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            
                        if algorithm == "sha256":
                            file_hash = hashlib.sha256(content).hexdigest()
                        elif algorithm == "md5":
                            file_hash = hashlib.md5(content).hexdigest()
                        else:
                            file_hash = hashlib.sha1(content).hexdigest()
                        
                        integrity_checks.append({
                            "file": file_path,
                            "hash": file_hash,
                            "algorithm": algorithm,
                            "size": len(content),
                            "last_modified": time.ctime(os.path.getmtime(file_path))
                        })
                        
                    except Exception as e:
                        integrity_checks.append({
                            "file": file_path,
                            "error": str(e),
                            "status": "failed"
                        })
            
            return ToolResult(
                success=True,
                data={
                    "integrity_checks": integrity_checks,
                    "algorithm": algorithm
                },
                message=f"Integrity check completed for {len(integrity_checks)} files"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to check integrity: {str(e)}",
                error=str(e)
            )
    
    def _analyze_network(self) -> ToolResult:
        """Analyze network for security issues."""
        try:
            import psutil
            
            network_analysis = {
                "connections": [],
                "listening_ports": [],
                "suspicious_connections": []
            }
            
            # Get all network connections
            for conn in psutil.net_connections():
                if conn.status == "LISTEN":
                    network_analysis["listening_ports"].append({
                        "address": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "pid": conn.pid,
                        "status": conn.status
                    })
                else:
                    network_analysis["connections"].append({
                        "local": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                        "status": conn.status,
                        "pid": conn.pid
                    })
            
            # Check for suspicious connections
            suspicious_ips = ["0.0.0.0", "127.0.0.1"]
            for conn in network_analysis["connections"]:
                if any(ip in conn["remote"] for ip in suspicious_ips):
                    network_analysis["suspicious_connections"].append(conn)
            
            return ToolResult(
                success=True,
                data=network_analysis,
                message=f"Network analysis completed: {len(network_analysis['listening_ports'])} listening ports, {len(network_analysis['connections'])} connections"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to analyze network: {str(e)}",
                error=str(e)
            )
    
    def _audit_users(self) -> ToolResult:
        """Audit user accounts for security issues."""
        try:
            user_audit = {
                "users": [],
                "security_issues": []
            }
            
            # Read /etc/passwd
            try:
                with open('/etc/passwd', 'r') as f:
                    for line in f:
                        parts = line.strip().split(':')
                        if len(parts) >= 7:
                            user_info = {
                                "username": parts[0],
                                "uid": parts[2],
                                "gid": parts[3],
                                "shell": parts[6]
                            }
                            user_audit["users"].append(user_info)
                            
                            # Check for security issues
                            if parts[2] == "0" and parts[0] != "root":
                                user_audit["security_issues"].append({
                                    "type": "non_root_uid_0",
                                    "user": parts[0],
                                    "uid": parts[2]
                                })
                            
                            if parts[6] in ["/bin/bash", "/bin/sh"] and parts[2] != "0":
                                user_audit["security_issues"].append({
                                    "type": "shell_access",
                                    "user": parts[0],
                                    "shell": parts[6]
                                })
            except:
                pass
            
            return ToolResult(
                success=True,
                data=user_audit,
                message=f"User audit completed: {len(user_audit['users'])} users, {len(user_audit['security_issues'])} issues"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to audit users: {str(e)}",
                error=str(e)
            )
    
    def _check_services(self) -> ToolResult:
        """Check running services for security issues."""
        try:
            import psutil
            
            service_audit = {
                "services": [],
                "security_issues": []
            }
            
            # Check for services running as root
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    info = proc.info
                    if info['username'] == 'root' and info['name'] not in ['systemd', 'init', 'kernel']:
                        service_audit["security_issues"].append({
                            "type": "service_as_root",
                            "service": info['name'],
                            "pid": info['pid']
                        })
                except:
                    continue
            
            return ToolResult(
                success=True,
                data=service_audit,
                message=f"Service audit completed: {len(service_audit['security_issues'])} security issues found"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to check services: {str(e)}",
                error=str(e)
            )
    
    def _scan_ports(self, target: str = None) -> ToolResult:
        """Scan ports for security analysis."""
        try:
            if not target:
                target = "localhost"
            
            import socket
            
            common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 5432, 8080]
            open_ports = []
            
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((target, port))
                    sock.close()
                    
                    if result == 0:
                        open_ports.append({
                            "port": port,
                            "service": self._get_service_name(port),
                            "status": "open"
                        })
                except:
                    continue
            
            return ToolResult(
                success=True,
                data={
                    "target": target,
                    "open_ports": open_ports,
                    "total_scanned": len(common_ports)
                },
                message=f"Port scan completed: {len(open_ports)} open ports found"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to scan ports: {str(e)}",
                error=str(e)
            )
    
    def _monitor_logs(self) -> ToolResult:
        """Monitor system logs for security events."""
        try:
            log_events = []
            
            # Common log files to monitor
            log_files = [
                "/var/log/auth.log",
                "/var/log/syslog",
                "/var/log/messages"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            # Get last 50 lines
                            recent_lines = lines[-50:] if len(lines) > 50 else lines
                            
                            for line in recent_lines:
                                line_lower = line.lower()
                                if any(keyword in line_lower for keyword in ['failed', 'error', 'denied', 'unauthorized', 'attack']):
                                    log_events.append({
                                        "log_file": log_file,
                                        "event": line.strip(),
                                        "timestamp": time.ctime()
                                    })
                    except:
                        continue
            
            return ToolResult(
                success=True,
                data={
                    "log_events": log_events,
                    "total_events": len(log_events)
                },
                message=f"Log monitoring completed: {len(log_events)} security events found"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to monitor logs: {str(e)}",
                error=str(e)
            )
    
    def _get_service_name(self, port: int) -> str:
        """Get service name for port."""
        service_names = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S",
            3306: "MySQL",
            5432: "PostgreSQL",
            8080: "HTTP-Proxy"
        }
        return service_names.get(port, "Unknown") 