"""
Network diagnostics tool for SysAgent CLI.
"""

import socket
import subprocess
import platform
import time
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory, PermissionLevel


@dataclass
class NetworkInfo:
    """Information about network connectivity."""
    host: str
    port: int
    status: str
    response_time: float
    protocol: str
    details: Dict[str, Any]


@register_tool
class NetworkTool(BaseTool):
    """Tool for network diagnostics."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="network_tool",
            description="Network diagnostics and connectivity testing",
            category=ToolCategory.NETWORK,
            permissions=["network_access"],
            version="1.0.0"
        )
    
    def _execute(self, action: str, host: str = None, port: int = None, 
                 protocol: str = "tcp", timeout: int = 5, count: int = 4, 
                 ports: str = None, **kwargs) -> ToolResult:
        """Execute network diagnostics action."""
        
        try:
            if action == "ping":
                return self._ping_host(host, count, timeout)
            elif action == "port_scan":
                return self._scan_ports(host, ports, protocol, timeout)
            elif action == "connectivity":
                return self._test_connectivity(host, port, protocol, timeout)
            elif action == "dns":
                return self._resolve_dns(host)
            elif action == "traceroute":
                return self._traceroute(host, timeout)
            elif action == "speed_test":
                return self._speed_test()
            elif action == "network_info":
                return self._get_network_info()
            elif action == "check_url":
                return self._check_url(host, timeout)
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
                message=f"Network operation failed: {str(e)}",
                error=str(e)
            )
    
    def _ping_host(self, host: str, count: int = 4, timeout: int = 5) -> ToolResult:
        """Ping a host to check connectivity."""
        try:
            if not host:
                return ToolResult(
                    success=False,
                    data={},
                    message="Host parameter is required",
                    error="Missing host parameter"
                )
            
            # Determine ping command based on OS
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * 2)
            end_time = time.time()
            
            if result.returncode == 0:
                # Parse ping output
                lines = result.stdout.split('\n')
                ping_stats = {
                    "host": host,
                    "status": "reachable",
                    "response_time": end_time - start_time,
                    "raw_output": result.stdout,
                    "packets_sent": count,
                    "packets_received": 0,
                    "packet_loss": 0.0,
                    "min_rtt": 0.0,
                    "avg_rtt": 0.0,
                    "max_rtt": 0.0
                }
                
                # Extract statistics from output
                for line in lines:
                    if "packets transmitted" in line.lower() or "packets received" in line.lower():
                        # Parse packet statistics
                        parts = line.split(',')
                        for part in parts:
                            if "transmitted" in part:
                                ping_stats["packets_sent"] = int(part.split()[0])
                            elif "received" in part:
                                ping_stats["packets_received"] = int(part.split()[0])
                            elif "loss" in part:
                                ping_stats["packet_loss"] = float(part.split('%')[0])
                    
                    elif "rtt min/avg/max" in line.lower() or "round-trip" in line.lower():
                        # Parse RTT statistics
                        try:
                            rtt_part = line.split('=')[1].strip()
                            rtt_values = rtt_part.split('/')
                            if len(rtt_values) >= 3:
                                ping_stats["min_rtt"] = float(rtt_values[0])
                                ping_stats["avg_rtt"] = float(rtt_values[1])
                                ping_stats["max_rtt"] = float(rtt_values[2])
                        except:
                            pass
                
                return ToolResult(
                    success=True,
                    data=ping_stats,
                    message=f"Host {host} is reachable (avg RTT: {ping_stats['avg_rtt']:.2f}ms)"
                )
            else:
                return ToolResult(
                    success=False,
                    data={
                        "host": host,
                        "status": "unreachable",
                        "error": result.stderr,
                        "raw_output": result.stdout
                    },
                    message=f"Host {host} is unreachable"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={"host": host, "status": "timeout"},
                message=f"Ping to {host} timed out"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to ping {host}: {str(e)}",
                error=str(e)
            )
    
    def _scan_ports(self, host: str, ports: str = None, protocol: str = "tcp", 
                   timeout: int = 5) -> ToolResult:
        """Scan ports on a host."""
        try:
            if not host:
                return ToolResult(
                    success=False,
                    data={},
                    message="Host parameter is required",
                    error="Missing host parameter"
                )
            
            # Parse ports to scan
            port_list = []
            if ports:
                if "," in ports:
                    port_list = [int(p.strip()) for p in ports.split(",")]
                elif "-" in ports:
                    start, end = map(int, ports.split("-"))
                    port_list = list(range(start, end + 1))
                else:
                    port_list = [int(ports)]
            else:
                # Default common ports
                port_list = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 5432, 8080]
            
            open_ports = []
            closed_ports = []
            
            for port in port_list:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        open_ports.append(port)
                    else:
                        closed_ports.append(port)
                        
                except Exception:
                    closed_ports.append(port)
            
            scan_result = {
                "host": host,
                "protocol": protocol,
                "total_ports": len(port_list),
                "open_ports": open_ports,
                "closed_ports": closed_ports,
                "open_count": len(open_ports),
                "closed_count": len(closed_ports)
            }
            
            return ToolResult(
                success=True,
                data=scan_result,
                message=f"Port scan completed: {len(open_ports)} open ports found"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to scan ports on {host}: {str(e)}",
                error=str(e)
            )
    
    def _test_connectivity(self, host: str, port: int = None, protocol: str = "tcp", 
                          timeout: int = 5) -> ToolResult:
        """Test connectivity to a specific host and port."""
        try:
            if not host:
                return ToolResult(
                    success=False,
                    data={},
                    message="Host parameter is required",
                    error="Missing host parameter"
                )
            
            if not port:
                port = 80 if protocol == "http" else 443 if protocol == "https" else 22
            
            start_time = time.time()
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                end_time = time.time()
                sock.close()
                
                if result == 0:
                    return ToolResult(
                        success=True,
                        data={
                            "host": host,
                            "port": port,
                            "protocol": protocol,
                            "status": "connected",
                            "response_time": (end_time - start_time) * 1000,
                            "connectivity": "success"
                        },
                        message=f"Successfully connected to {host}:{port}"
                    )
                else:
                    return ToolResult(
                        success=False,
                        data={
                            "host": host,
                            "port": port,
                            "protocol": protocol,
                            "status": "failed",
                            "error_code": result
                        },
                        message=f"Failed to connect to {host}:{port}"
                    )
                    
            except socket.timeout:
                return ToolResult(
                    success=False,
                    data={
                        "host": host,
                        "port": port,
                        "protocol": protocol,
                        "status": "timeout"
                    },
                    message=f"Connection to {host}:{port} timed out"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to test connectivity to {host}:{port}: {str(e)}",
                error=str(e)
            )
    
    def _resolve_dns(self, host: str) -> ToolResult:
        """Resolve DNS for a hostname."""
        try:
            if not host:
                return ToolResult(
                    success=False,
                    data={},
                    message="Host parameter is required",
                    error="Missing host parameter"
                )
            
            # Get IP addresses
            try:
                ip_addresses = socket.gethostbyname_ex(host)
                primary_ip = socket.gethostbyname(host)
            except socket.gaierror as e:
                return ToolResult(
                    success=False,
                    data={"host": host, "error": str(e)},
                    message=f"Failed to resolve DNS for {host}"
                )
            
            # Get reverse DNS
            try:
                reverse_dns = socket.gethostbyaddr(primary_ip)
            except socket.herror:
                reverse_dns = None
            
            dns_info = {
                "hostname": host,
                "primary_ip": primary_ip,
                "all_ips": ip_addresses[2],
                "canonical_name": ip_addresses[0],
                "aliases": ip_addresses[1],
                "reverse_dns": reverse_dns[0] if reverse_dns else None
            }
            
            return ToolResult(
                success=True,
                data=dns_info,
                message=f"DNS resolved: {host} -> {primary_ip}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to resolve DNS for {host}: {str(e)}",
                error=str(e)
            )
    
    def _traceroute(self, host: str, timeout: int = 5) -> ToolResult:
        """Perform traceroute to a host."""
        try:
            if not host:
                return ToolResult(
                    success=False,
                    data={},
                    message="Host parameter is required",
                    error="Missing host parameter"
                )
            
            # Determine traceroute command based on OS
            if platform.system().lower() == "windows":
                cmd = ["tracert", "-d", "-h", "30", "-w", str(timeout * 1000), host]
            else:
                cmd = ["traceroute", "-n", "-w", str(timeout), "-m", "30", host]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * 10)
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={
                        "host": host,
                        "route": result.stdout,
                        "status": "completed"
                    },
                    message=f"Traceroute to {host} completed"
                )
            else:
                return ToolResult(
                    success=False,
                    data={
                        "host": host,
                        "error": result.stderr,
                        "output": result.stdout
                    },
                    message=f"Traceroute to {host} failed"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={"host": host},
                message=f"Traceroute to {host} timed out"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to traceroute to {host}: {str(e)}",
                error=str(e)
            )
    
    def _speed_test(self) -> ToolResult:
        """Perform a basic speed test."""
        try:
            # Test download speed with a small file
            test_urls = [
                "https://httpbin.org/bytes/1024",  # 1KB
                "https://httpbin.org/bytes/10240",  # 10KB
                "https://httpbin.org/bytes/102400"  # 100KB
            ]
            
            speeds = []
            
            for url in test_urls:
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=10)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        duration = end_time - start_time
                        size_kb = len(response.content) / 1024
                        speed_mbps = (size_kb * 8) / (duration * 1000)  # Convert to Mbps
                        speeds.append(speed_mbps)
                        
                except Exception:
                    continue
            
            if speeds:
                avg_speed = sum(speeds) / len(speeds)
                return ToolResult(
                    success=True,
                    data={
                        "average_speed_mbps": round(avg_speed, 2),
                        "speed_tests": len(speeds),
                        "speeds": [round(s, 2) for s in speeds]
                    },
                    message=f"Speed test completed: {round(avg_speed, 2)} Mbps average"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Speed test failed - no successful tests"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Speed test failed: {str(e)}",
                error=str(e)
            )
    
    def _get_network_info(self) -> ToolResult:
        """Get local network information."""
        try:
            # Get hostname
            hostname = socket.gethostname()
            
            # Get local IP
            local_ip = socket.gethostbyname(hostname)
            
            # Get network interfaces (basic info)
            interfaces = []
            try:
                for interface_name in socket.if_nameindex():
                    try:
                        # Get interface address
                        interface_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        interface_socket.connect(("8.8.8.8", 80))
                        interface_ip = interface_socket.getsockname()[0]
                        interface_socket.close()
                        
                        interfaces.append({
                            "name": interface_name[1],
                            "index": interface_name[0],
                            "ip": interface_ip
                        })
                    except:
                        continue
            except:
                # Fallback for systems without if_nameindex
                interfaces.append({
                    "name": "default",
                    "ip": local_ip
                })
            
            network_info = {
                "hostname": hostname,
                "local_ip": local_ip,
                "interfaces": interfaces,
                "platform": platform.system(),
                "architecture": platform.machine()
            }
            
            return ToolResult(
                success=True,
                data=network_info,
                message=f"Network info: {hostname} ({local_ip})"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get network info: {str(e)}",
                error=str(e)
            )
    
    def _check_url(self, url: str, timeout: int = 10) -> ToolResult:
        """Check if a URL is accessible."""
        try:
            if not url:
                return ToolResult(
                    success=False,
                    data={},
                    message="URL parameter is required",
                    error="Missing URL parameter"
                )
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            start_time = time.time()
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            end_time = time.time()
            
            url_info = {
                "url": url,
                "status_code": response.status_code,
                "response_time": (end_time - start_time) * 1000,
                "content_length": len(response.content),
                "headers": dict(response.headers),
                "final_url": response.url,
                "redirects": len(response.history)
            }
            
            if response.status_code < 400:
                return ToolResult(
                    success=True,
                    data=url_info,
                    message=f"URL {url} is accessible (Status: {response.status_code})"
                )
            else:
                return ToolResult(
                    success=False,
                    data=url_info,
                    message=f"URL {url} returned status {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            return ToolResult(
                success=False,
                data={"url": url},
                message=f"URL {url} timed out"
            )
        except requests.exceptions.ConnectionError:
            return ToolResult(
                success=False,
                data={"url": url},
                message=f"Failed to connect to {url}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to check URL {url}: {str(e)}",
                error=str(e)
            ) 