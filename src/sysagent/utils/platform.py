"""
Platform detection and OS-specific utilities for SysAgent CLI.
"""

import os
import sys
import subprocess
from typing import Optional, Tuple
from pathlib import Path

from ..types import Platform, PermissionLevel


def detect_platform() -> Platform:
    """Detect the current operating system platform."""
    system = sys.platform.lower()
    
    if system.startswith("darwin"):
        return Platform.MACOS
    elif system.startswith("linux"):
        return Platform.LINUX
    elif system.startswith("win"):
        return Platform.WINDOWS
    else:
        return Platform.UNKNOWN


def get_platform_info() -> dict:
    """Get detailed platform information."""
    platform = detect_platform()
    
    info = {
        "platform": platform.value,
        "python_version": sys.version,
        "architecture": sys.maxsize > 2**32 and "64bit" or "32bit",
    }
    
    if platform == Platform.MACOS:
        info.update(_get_macos_info())
    elif platform == Platform.LINUX:
        info.update(_get_linux_info())
    elif platform == Platform.WINDOWS:
        info.update(_get_windows_info())
    
    return info


def _get_macos_info() -> dict:
    """Get macOS-specific information."""
    try:
        # Get macOS version
        result = subprocess.run(
            ["sw_vers", "-productVersion"], 
            capture_output=True, 
            text=True
        )
        macos_version = result.stdout.strip() if result.returncode == 0 else "Unknown"
        
        return {
            "os_version": f"macOS {macos_version}",
            "kernel": "Darwin",
        }
    except Exception:
        return {"os_version": "macOS (Unknown)", "kernel": "Darwin"}


def _get_linux_info() -> dict:
    """Get Linux-specific information."""
    try:
        # Try to read /etc/os-release
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                lines = f.readlines()
                os_info = {}
                for line in lines:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os_info[key] = value.strip('"')
                
                return {
                    "os_version": f"{os_info.get('PRETTY_NAME', 'Linux')}",
                    "kernel": os_info.get("ID", "Linux"),
                }
        else:
            return {"os_version": "Linux (Unknown)", "kernel": "Linux"}
    except Exception:
        return {"os_version": "Linux (Unknown)", "kernel": "Linux"}


def _get_windows_info() -> dict:
    """Get Windows-specific information."""
    try:
        import platform
        return {
            "os_version": platform.platform(),
            "kernel": "Windows NT",
        }
    except Exception:
        return {"os_version": "Windows (Unknown)", "kernel": "Windows NT"}


def get_home_directory() -> Path:
    """Get the user's home directory."""
    return Path.home()


def get_temp_directory() -> Path:
    """Get the system's temporary directory."""
    return Path(os.environ.get("TMPDIR", "/tmp"))


def get_desktop_directory() -> Path:
    """Get the user's desktop directory."""
    platform = detect_platform()
    
    if platform == Platform.MACOS:
        return get_home_directory() / "Desktop"
    elif platform == Platform.LINUX:
        # Try common desktop paths
        desktop_paths = [
            get_home_directory() / "Desktop",
            get_home_directory() / "Рабочий стол",  # Russian
            get_home_directory() / "Escritorio",    # Spanish
        ]
        for path in desktop_paths:
            if path.exists():
                return path
        return get_home_directory() / "Desktop"
    elif platform == Platform.WINDOWS:
        return get_home_directory() / "Desktop"
    else:
        return get_home_directory() / "Desktop"


def get_downloads_directory() -> Path:
    """Get the user's downloads directory."""
    platform = detect_platform()
    
    if platform == Platform.MACOS:
        return get_home_directory() / "Downloads"
    elif platform == Platform.LINUX:
        # Try common downloads paths
        downloads_paths = [
            get_home_directory() / "Downloads",
            get_home_directory() / "Загрузки",      # Russian
            get_home_directory() / "Descargas",     # Spanish
        ]
        for path in downloads_paths:
            if path.exists():
                return path
        return get_home_directory() / "Downloads"
    elif platform == Platform.WINDOWS:
        return get_home_directory() / "Downloads"
    else:
        return get_home_directory() / "Downloads"


def get_documents_directory() -> Path:
    """Get the user's documents directory."""
    platform = detect_platform()
    
    if platform == Platform.MACOS:
        return get_home_directory() / "Documents"
    elif platform == Platform.LINUX:
        return get_home_directory() / "Documents"
    elif platform == Platform.WINDOWS:
        return get_home_directory() / "Documents"
    else:
        return get_home_directory() / "Documents"


def is_admin() -> bool:
    """Check if the current user has administrative privileges."""
    platform = detect_platform()
    
    if platform == Platform.MACOS:
        try:
            result = subprocess.run(
                ["id", "-u"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip() == "0"
        except Exception:
            pass
        return False
    
    elif platform == Platform.LINUX:
        try:
            result = subprocess.run(
                ["id", "-u"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip() == "0"
        except Exception:
            pass
        return False
    
    elif platform == Platform.WINDOWS:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            pass
        return False
    
    return False


def can_elevate_privileges() -> bool:
    """Check if the system supports privilege elevation."""
    platform = detect_platform()
    
    if platform == Platform.MACOS:
        # Check if we can use sudo
        try:
            result = subprocess.run(
                ["sudo", "-n", "true"], 
                capture_output=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    elif platform == Platform.LINUX:
        # Check if we can use sudo or pkexec
        try:
            result = subprocess.run(
                ["sudo", "-n", "true"], 
                capture_output=True
            )
            if result.returncode == 0:
                return True
            
            # Try pkexec
            result = subprocess.run(
                ["pkexec", "--version"], 
                capture_output=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    elif platform == Platform.WINDOWS:
        # Windows UAC is always available
        return True
    
    return False


def get_system_paths() -> dict:
    """Get common system paths for the current platform."""
    platform = detect_platform()
    
    paths = {
        "home": get_home_directory(),
        "temp": get_temp_directory(),
        "desktop": get_desktop_directory(),
        "downloads": get_downloads_directory(),
        "documents": get_documents_directory(),
    }
    
    if platform == Platform.MACOS:
        paths.update({
            "applications": Path("/Applications"),
            "system_applications": Path("/System/Applications"),
            "user_applications": get_home_directory() / "Applications",
            "library": get_home_directory() / "Library",
            "system_library": Path("/System/Library"),
        })
    
    elif platform == Platform.LINUX:
        paths.update({
            "applications": Path("/usr/share/applications"),
            "user_applications": get_home_directory() / ".local/share/applications",
            "bin": Path("/usr/bin"),
            "sbin": Path("/usr/sbin"),
        })
    
    elif platform == Platform.WINDOWS:
        paths.update({
            "program_files": Path(os.environ.get("ProgramFiles", "C:\\Program Files")),
            "program_files_x86": Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")),
            "system32": Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32",
        })
    
    return paths


def get_environment_variables() -> dict:
    """Get relevant environment variables for the current platform."""
    platform = detect_platform()
    
    env_vars = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "USER": os.environ.get("USER", ""),
        "SHELL": os.environ.get("SHELL", ""),
    }
    
    if platform == Platform.MACOS:
        env_vars.update({
            "TERM_PROGRAM": os.environ.get("TERM_PROGRAM", ""),
            "TERM_PROGRAM_VERSION": os.environ.get("TERM_PROGRAM_VERSION", ""),
        })
    
    elif platform == Platform.LINUX:
        env_vars.update({
            "DISPLAY": os.environ.get("DISPLAY", ""),
            "XDG_CURRENT_DESKTOP": os.environ.get("XDG_CURRENT_DESKTOP", ""),
        })
    
    elif platform == Platform.WINDOWS:
        env_vars.update({
            "APPDATA": os.environ.get("APPDATA", ""),
            "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", ""),
            "TEMP": os.environ.get("TEMP", ""),
            "USERPROFILE": os.environ.get("USERPROFILE", ""),
        })
    
    return env_vars 