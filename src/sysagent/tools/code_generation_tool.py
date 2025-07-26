"""
Code generation tool for SysAgent CLI.
"""

import subprocess
import tempfile
import os
import sys
from typing import Dict, List, Any, Optional

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory, PermissionLevel


@register_tool
class CodeGenerationTool(BaseTool):
    """Tool for code generation and execution."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="code_generation_tool",
            description="Generate and execute custom code solutions",
            category=ToolCategory.CODE_GENERATION,
            permissions=["code_execution"],
            version="1.0.0"
        )
    
    def _execute(self, description: str, language: str = "python", **kwargs) -> ToolResult:
        """Generate and execute code based on description."""
        try:
            # Create a safe execution environment
            import tempfile
            import os
            
            # Generate code based on the description
            code_prompt = f"""
Generate Python code to: {description}

Requirements:
- Use only standard library modules (os, sys, subprocess, platform, psutil, etc.)
- Make it safe and non-destructive
- Return the result as a string
- Handle errors gracefully
- Focus on system information and analysis
- Don't use any external libraries that aren't already available

Code:
"""
            
            # For now, we'll use a simple code template
            # In a real implementation, this would call the LLM
            code = self._generate_code_for_description(description)
            
            # Create temporary file for execution
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute the code safely
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={
                            "output": result.stdout,
                            "code": code,
                            "description": description
                        },
                        message=f"Code executed successfully for: {description}"
                    )
                else:
                    return ToolResult(
                        success=False,
                        data={
                            "error": result.stderr,
                            "code": code,
                            "description": description
                        },
                        message=f"Code execution failed for: {description}"
                    )
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Error generating/executing code: {str(e)}",
                error=str(e)
            )
    
    def _generate_code_for_description(self, description: str) -> str:
        """Generate appropriate code based on the description."""
        description_lower = description.lower()
        
        # Common code templates
        if "python files" in description_lower or "find" in description_lower:
            return '''
import os
import glob
from pathlib import Path

def find_python_files():
    python_files = []
    for root, dirs, files in os.walk("/"):
        if any(skip in root for skip in ["/proc", "/sys", "/dev", "/tmp", "/var/tmp"]):
            continue
        for file in files:
            if file.endswith(".py"):
                try:
                    full_path = os.path.join(root, file)
                    if os.path.isfile(full_path):
                        python_files.append(full_path)
                except:
                    continue
    return python_files[:50]  # Limit results

result = find_python_files()
print(f"Found {len(result)} Python files:")
for file in result[:10]:
    print(f"  {file}")
if len(result) > 10:
    print(f"  ... and {len(result) - 10} more")
'''
        
        elif "ports" in description_lower or "listening" in description_lower:
            return '''
import socket
import psutil

def get_listening_ports():
    listening_ports = []
    for conn in psutil.net_connections():
        if conn.status == "LISTEN":
            listening_ports.append({
                "port": conn.laddr.port,
                "address": conn.laddr.ip,
                "pid": conn.pid
            })
    return listening_ports

result = get_listening_ports()
print(f"Found {len(result)} listening ports:")
for port_info in result:
    print(f"  {port_info['address']}:{port_info['port']} (PID: {port_info['pid']})")
'''
        
        elif "memory" in description_lower and "process" in description_lower:
            return '''
import psutil

def analyze_memory_by_process():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
        try:
            info = proc.info
            if info['memory_percent'] and info['memory_percent'] > 0:
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'memory_percent': info['memory_percent'],
                    'memory_mb': info['memory_info'].rss / 1024 / 1024
                })
        except:
            continue
    
    # Sort by memory usage
    processes.sort(key=lambda x: x['memory_percent'], reverse=True)
    return processes[:10]

result = analyze_memory_by_process()
print("Top memory-consuming processes:")
for proc in result:
    print(f"  {proc['name']} (PID: {proc['pid']}): {proc['memory_percent']:.1f}% ({proc['memory_mb']:.1f} MB)")
'''
        
        elif "large files" in description_lower:
            return '''
import os
from pathlib import Path

def find_large_files(directory="/", min_size_mb=100):
    large_files = []
    try:
        for root, dirs, files in os.walk(directory):
            if any(skip in root for skip in ["/proc", "/sys", "/dev", "/tmp", "/var/tmp"]):
                continue
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        if size > min_size_mb * 1024 * 1024:
                            large_files.append({
                                'path': file_path,
                                'size_mb': size / 1024 / 1024
                            })
                except:
                    continue
    except:
        pass
    
    large_files.sort(key=lambda x: x['size_mb'], reverse=True)
    return large_files[:10]

result = find_large_files()
print("Large files found:")
for file in result:
    print(f"  {file['path']}: {file['size_mb']:.1f} MB")
'''
        
        elif "uptime" in description_lower or "load" in description_lower:
            return '''
import psutil
import time
import os

def get_system_info():
    uptime = time.time() - psutil.boot_time()
    load_avg = os.getloadavg()
    
    return {
        'uptime_seconds': uptime,
        'uptime_days': uptime / 86400,
        'load_avg_1min': load_avg[0],
        'load_avg_5min': load_avg[1],
        'load_avg_15min': load_avg[2]
    }

result = get_system_info()
print(f"System Uptime: {result['uptime_days']:.1f} days")
print(f"Load Average: {result['load_avg_1min']:.2f} (1min), {result['load_avg_5min']:.2f} (5min), {result['load_avg_15min']:.2f} (15min)")
'''
        
        else:
            # Generic template for other requests
            return f'''
import os
import sys
import platform
import psutil

def custom_analysis():
    """Custom analysis for: {description}"""
    try:
        # Basic system info
        info = {{
            'platform': platform.system(),
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('/')._asdict()
        }}
        
        result = f"System Analysis for: {description}\\n"
        result += f"Platform: {{info['platform']}}\\n"
        result += f"CPU Cores: {{info['cpu_count']}}\\n"
        result += f"Memory Usage: {{info['memory']['percent']:.1f}}%\\n"
        result += f"Disk Usage: {{info['disk']['percent']:.1f}}%\\n"
        
        return result
    except Exception as e:
        return f"Error analyzing system: {{str(e)}}"

print(custom_analysis())
''' 