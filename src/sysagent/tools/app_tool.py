"""
Application management tool for SysAgent CLI.
"""

import os
import sys
import subprocess
import platform
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class AppTool(BaseTool):
    """Tool for application launching and management."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="app_tool",
            description="Application launching, management, and control",
            category=ToolCategory.APP,
            permissions=["app_control"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Execute application management action."""
        try:
            if action == "launch":
                return self._launch_app(**kwargs)
            elif action == "close":
                return self._close_app(**kwargs)
            elif action == "list":
                return self._list_apps(**kwargs)
            elif action == "list_running":
                return self._list_running_apps(**kwargs)
            elif action == "focus":
                return self._focus_app(**kwargs)
            elif action == "info":
                return self._get_app_info(**kwargs)
            elif action == "find":
                return self._find_app(**kwargs)
            elif action == "install":
                return self._install_app(**kwargs)
            elif action == "uninstall":
                return self._uninstall_app(**kwargs)
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
                message=f"Application operation failed: {str(e)}",
                error=str(e)
            )

    def _launch_app(self, **kwargs) -> ToolResult:
        """Launch an application."""
        app_name = kwargs.get("name") or kwargs.get("app")
        args = kwargs.get("args", [])
        
        if not app_name:
            return ToolResult(
                success=False,
                data={},
                message="No application name provided",
                error="Missing app name"
            )
        
        try:
            current_platform = detect_platform()
            
            if current_platform == Platform.MACOS:
                # Use 'open' command on macOS
                if app_name.endswith('.app'):
                    cmd = ["open", "-a", app_name]
                else:
                    cmd = ["open", "-a", app_name]
                if args:
                    cmd.extend(["--args"] + args)
                    
            elif current_platform == Platform.LINUX:
                # Try common launchers
                app_paths = self._find_linux_app(app_name)
                if app_paths:
                    cmd = [app_paths[0]] + args
                else:
                    # Try direct execution
                    cmd = [app_name] + args
                    
            elif current_platform == Platform.WINDOWS:
                # Use 'start' command on Windows
                cmd = ["cmd", "/c", "start", "", app_name] + args
            else:
                cmd = [app_name] + args
            
            # Launch the application
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            return ToolResult(
                success=True,
                data={
                    "app": app_name,
                    "pid": process.pid,
                    "command": cmd
                },
                message=f"Launched {app_name} (PID: {process.pid})"
            )
            
        except FileNotFoundError:
            return ToolResult(
                success=False,
                data={},
                message=f"Application '{app_name}' not found",
                error="App not found"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to launch {app_name}: {str(e)}",
                error=str(e)
            )

    def _close_app(self, **kwargs) -> ToolResult:
        """Close an application."""
        app_name = kwargs.get("name") or kwargs.get("app")
        force = kwargs.get("force", False)
        
        if not app_name:
            return ToolResult(
                success=False,
                data={},
                message="No application name provided",
                error="Missing app name"
            )
        
        try:
            import psutil
            
            closed_count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app_name.lower() in proc.info['name'].lower():
                        if force:
                            proc.kill()
                        else:
                            proc.terminate()
                        closed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if closed_count > 0:
                return ToolResult(
                    success=True,
                    data={"app": app_name, "closed_count": closed_count},
                    message=f"Closed {closed_count} instance(s) of {app_name}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"No running instances of {app_name} found",
                    error="App not running"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to close {app_name}: {str(e)}",
                error=str(e)
            )

    def _list_apps(self, **kwargs) -> ToolResult:
        """List installed applications."""
        try:
            current_platform = detect_platform()
            apps = []
            
            if current_platform == Platform.MACOS:
                # List apps in /Applications
                app_dirs = [
                    Path("/Applications"),
                    Path.home() / "Applications"
                ]
                for app_dir in app_dirs:
                    if app_dir.exists():
                        for app in app_dir.glob("*.app"):
                            apps.append({
                                "name": app.stem,
                                "path": str(app),
                                "type": "application"
                            })
                            
            elif current_platform == Platform.LINUX:
                # List apps from .desktop files
                desktop_dirs = [
                    Path("/usr/share/applications"),
                    Path.home() / ".local/share/applications"
                ]
                for desktop_dir in desktop_dirs:
                    if desktop_dir.exists():
                        for desktop_file in desktop_dir.glob("*.desktop"):
                            app_info = self._parse_desktop_file(desktop_file)
                            if app_info:
                                apps.append(app_info)
                                
            elif current_platform == Platform.WINDOWS:
                # List apps from Start Menu
                start_menu_dirs = [
                    Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
                    Path.home() / "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs"
                ]
                for start_dir in start_menu_dirs:
                    if start_dir.exists():
                        for lnk in start_dir.rglob("*.lnk"):
                            apps.append({
                                "name": lnk.stem,
                                "path": str(lnk),
                                "type": "shortcut"
                            })
            
            return ToolResult(
                success=True,
                data={"apps": apps, "count": len(apps)},
                message=f"Found {len(apps)} installed applications"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list applications: {str(e)}",
                error=str(e)
            )

    def _list_running_apps(self, **kwargs) -> ToolResult:
        """List currently running applications."""
        try:
            import psutil
            
            running_apps = []
            seen = set()
            
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'memory_percent', 'cpu_percent']):
                try:
                    info = proc.info
                    name = info['name']
                    
                    # Skip duplicates and system processes
                    if name in seen or name.startswith('['):
                        continue
                    seen.add(name)
                    
                    running_apps.append({
                        "name": name,
                        "pid": info['pid'],
                        "exe": info['exe'],
                        "memory_percent": round(info['memory_percent'], 2),
                        "cpu_percent": info['cpu_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by memory usage
            running_apps.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            return ToolResult(
                success=True,
                data={"running_apps": running_apps[:50], "count": len(running_apps)},
                message=f"Found {len(running_apps)} running applications"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list running applications: {str(e)}",
                error=str(e)
            )

    def _focus_app(self, **kwargs) -> ToolResult:
        """Bring an application to the foreground."""
        app_name = kwargs.get("name") or kwargs.get("app")
        
        if not app_name:
            return ToolResult(
                success=False,
                data={},
                message="No application name provided",
                error="Missing app name"
            )
        
        try:
            current_platform = detect_platform()
            
            if current_platform == Platform.MACOS:
                # Use AppleScript to focus app
                script = f'tell application "{app_name}" to activate'
                subprocess.run(["osascript", "-e", script], capture_output=True)
                
            elif current_platform == Platform.LINUX:
                # Try wmctrl or xdotool
                try:
                    subprocess.run(["wmctrl", "-a", app_name], capture_output=True)
                except FileNotFoundError:
                    try:
                        subprocess.run(["xdotool", "search", "--name", app_name, "windowactivate"], capture_output=True)
                    except FileNotFoundError:
                        return ToolResult(
                            success=False,
                            data={},
                            message="wmctrl or xdotool required for window focus",
                            error="Missing dependency"
                        )
                        
            elif current_platform == Platform.WINDOWS:
                # Use PowerShell to focus window
                script = f'(New-Object -ComObject WScript.Shell).AppActivate("{app_name}")'
                subprocess.run(["powershell", "-Command", script], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"app": app_name},
                message=f"Focused on {app_name}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to focus {app_name}: {str(e)}",
                error=str(e)
            )

    def _get_app_info(self, **kwargs) -> ToolResult:
        """Get information about an application."""
        app_name = kwargs.get("name") or kwargs.get("app")
        
        if not app_name:
            return ToolResult(
                success=False,
                data={},
                message="No application name provided",
                error="Missing app name"
            )
        
        try:
            import psutil
            
            app_info = {
                "name": app_name,
                "running": False,
                "instances": []
            }
            
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time', 'memory_info', 'cpu_percent']):
                try:
                    if app_name.lower() in proc.info['name'].lower():
                        app_info["running"] = True
                        app_info["instances"].append({
                            "pid": proc.info['pid'],
                            "exe": proc.info['exe'],
                            "memory_mb": round(proc.info['memory_info'].rss / 1024 / 1024, 2),
                            "cpu_percent": proc.info['cpu_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return ToolResult(
                success=True,
                data=app_info,
                message=f"Retrieved info for {app_name}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get info for {app_name}: {str(e)}",
                error=str(e)
            )

    def _find_app(self, **kwargs) -> ToolResult:
        """Find an application by name."""
        query = kwargs.get("query") or kwargs.get("name")
        
        if not query:
            return ToolResult(
                success=False,
                data={},
                message="No search query provided",
                error="Missing query"
            )
        
        try:
            # Get list of all apps and filter
            result = self._list_apps()
            if not result.success:
                return result
            
            matching_apps = []
            for app in result.data.get("apps", []):
                if query.lower() in app["name"].lower():
                    matching_apps.append(app)
            
            return ToolResult(
                success=True,
                data={"matching_apps": matching_apps, "count": len(matching_apps)},
                message=f"Found {len(matching_apps)} apps matching '{query}'"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to find apps: {str(e)}",
                error=str(e)
            )

    def _install_app(self, **kwargs) -> ToolResult:
        """Install an application (platform-specific)."""
        app_name = kwargs.get("name") or kwargs.get("app")
        
        if not app_name:
            return ToolResult(
                success=False,
                data={},
                message="No application name provided",
                error="Missing app name"
            )
        
        try:
            current_platform = detect_platform()
            
            if current_platform == Platform.MACOS:
                # Try brew
                result = subprocess.run(
                    ["brew", "install", "--cask", app_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={"app": app_name, "method": "brew cask"},
                        message=f"Installed {app_name} via Homebrew"
                    )
                    
            elif current_platform == Platform.LINUX:
                # Try apt, then snap, then flatpak
                for pkg_manager in [("apt", ["sudo", "apt", "install", "-y"]), 
                                   ("snap", ["sudo", "snap", "install"]),
                                   ("flatpak", ["flatpak", "install", "-y"])]:
                    try:
                        cmd = pkg_manager[1] + [app_name]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            return ToolResult(
                                success=True,
                                data={"app": app_name, "method": pkg_manager[0]},
                                message=f"Installed {app_name} via {pkg_manager[0]}"
                            )
                    except FileNotFoundError:
                        continue
                        
            elif current_platform == Platform.WINDOWS:
                # Try winget or chocolatey
                try:
                    result = subprocess.run(
                        ["winget", "install", app_name],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        return ToolResult(
                            success=True,
                            data={"app": app_name, "method": "winget"},
                            message=f"Installed {app_name} via winget"
                        )
                except FileNotFoundError:
                    pass
            
            return ToolResult(
                success=False,
                data={},
                message=f"Could not install {app_name} - no suitable package manager found",
                error="Installation failed"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to install {app_name}: {str(e)}",
                error=str(e)
            )

    def _uninstall_app(self, **kwargs) -> ToolResult:
        """Uninstall an application."""
        app_name = kwargs.get("name") or kwargs.get("app")
        
        if not app_name:
            return ToolResult(
                success=False,
                data={},
                message="No application name provided",
                error="Missing app name"
            )
        
        return ToolResult(
            success=False,
            data={},
            message="Uninstall requires manual confirmation. Use your system's package manager.",
            error="Safety restriction"
        )

    def _find_linux_app(self, app_name: str) -> List[str]:
        """Find application paths on Linux."""
        paths = []
        search_dirs = ["/usr/bin", "/usr/local/bin", "/opt", str(Path.home() / ".local/bin")]
        
        for search_dir in search_dirs:
            path = Path(search_dir)
            if path.exists():
                for item in path.iterdir():
                    if app_name.lower() in item.name.lower():
                        paths.append(str(item))
        
        return paths

    def _parse_desktop_file(self, desktop_file: Path) -> Optional[Dict[str, Any]]:
        """Parse a .desktop file to extract app info."""
        try:
            with open(desktop_file, 'r') as f:
                content = f.read()
            
            name = None
            exec_cmd = None
            
            for line in content.split('\n'):
                if line.startswith('Name='):
                    name = line.split('=', 1)[1]
                elif line.startswith('Exec='):
                    exec_cmd = line.split('=', 1)[1].split()[0]
            
            if name:
                return {
                    "name": name,
                    "path": str(desktop_file),
                    "exec": exec_cmd,
                    "type": "desktop"
                }
        except Exception:
            pass
        
        return None

    def get_usage_examples(self) -> List[str]:
        """Get usage examples for this tool."""
        return [
            "Launch app: app_tool --action launch --name 'Firefox'",
            "Close app: app_tool --action close --name 'Chrome'",
            "List installed apps: app_tool --action list",
            "List running apps: app_tool --action list_running",
            "Focus app: app_tool --action focus --name 'Terminal'",
            "Find app: app_tool --action find --query 'browser'",
        ]
