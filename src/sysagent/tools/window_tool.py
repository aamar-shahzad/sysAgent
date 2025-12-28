"""
Window tool for SysAgent CLI - Window management and control.
"""

import subprocess
import json
from typing import List, Dict, Any, Optional

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class WindowTool(BaseTool):
    """Tool for managing application windows."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="window_tool",
            description="Manage windows - resize, move, minimize, maximize, arrange",
            category=ToolCategory.SYSTEM,
            permissions=["window_control"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "list": self._list_windows,
                "focus": self._focus_window,
                "minimize": self._minimize_window,
                "maximize": self._maximize_window,
                "restore": self._restore_window,
                "close": self._close_window,
                "move": self._move_window,
                "resize": self._resize_window,
                "tile_left": self._tile_left,
                "tile_right": self._tile_right,
                "center": self._center_window,
                "fullscreen": self._fullscreen,
                "arrange": self._arrange_windows,
                "get_active": self._get_active_window,
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
                message=f"Window operation failed: {str(e)}",
                error=str(e)
            )

    def _run_applescript(self, script: str) -> str:
        """Run AppleScript on macOS."""
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def _list_windows(self, **kwargs) -> ToolResult:
        """List all open windows."""
        platform = detect_platform()
        windows = []
        
        try:
            if platform == Platform.MACOS:
                script = '''
                tell application "System Events"
                    set windowList to {}
                    repeat with proc in (every process whose background only is false)
                        set procName to name of proc
                        try
                            repeat with win in (every window of proc)
                                set winName to name of win
                                set end of windowList to procName & "|" & winName
                            end repeat
                        end try
                    end repeat
                    return windowList
                end tell
                '''
                result = self._run_applescript(script)
                if result:
                    for item in result.split(", "):
                        if "|" in item:
                            app, title = item.split("|", 1)
                            windows.append({"app": app, "title": title})
            
            elif platform == Platform.WINDOWS:
                # Use PowerShell to get windows
                ps_script = '''
                Get-Process | Where-Object {$_.MainWindowTitle} | 
                Select-Object ProcessName, MainWindowTitle | ConvertTo-Json
                '''
                result = subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True, text=True
                )
                if result.stdout:
                    data = json.loads(result.stdout)
                    if isinstance(data, list):
                        for item in data:
                            windows.append({
                                "app": item.get("ProcessName", ""),
                                "title": item.get("MainWindowTitle", "")
                            })
                    elif isinstance(data, dict):
                        windows.append({
                            "app": data.get("ProcessName", ""),
                            "title": data.get("MainWindowTitle", "")
                        })
            
            else:  # Linux
                result = subprocess.run(
                    ["wmctrl", "-l"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            windows.append({
                                "id": parts[0],
                                "desktop": parts[1],
                                "title": parts[3]
                            })
            
            return ToolResult(
                success=True,
                data={"windows": windows, "count": len(windows)},
                message=f"Found {len(windows)} windows"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list windows: {str(e)}",
                error=str(e)
            )

    def _focus_window(self, **kwargs) -> ToolResult:
        """Focus/activate a window."""
        app = kwargs.get("app") or kwargs.get("application")
        title = kwargs.get("title")
        
        if not app and not title:
            return ToolResult(
                success=False,
                data={},
                message="Specify app or title to focus"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                if app:
                    script = f'tell application "{app}" to activate'
                    self._run_applescript(script)
                elif title:
                    script = f'''
                    tell application "System Events"
                        set frontApp to first process whose frontmost is true
                        tell frontApp
                            perform action "AXRaise" of (first window whose name contains "{title}")
                        end tell
                    end tell
                    '''
                    self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                if app:
                    ps_script = f'''
                    $wshell = New-Object -ComObject wscript.shell
                    $wshell.AppActivate("{app}")
                    '''
                    subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            else:
                if title:
                    subprocess.run(["wmctrl", "-a", title], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"app": app, "title": title},
                message=f"Focused: {app or title}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to focus window: {str(e)}",
                error=str(e)
            )

    def _minimize_window(self, **kwargs) -> ToolResult:
        """Minimize a window."""
        app = kwargs.get("app")
        all_windows = kwargs.get("all", False)
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                if all_windows:
                    script = '''
                    tell application "System Events"
                        repeat with proc in (every process whose background only is false)
                            try
                                click (first button of (every window of proc) whose subrole is "AXMinimizeButton")
                            end try
                        end repeat
                    end tell
                    '''
                elif app:
                    script = f'''
                    tell application "{app}"
                        set miniaturized of every window to true
                    end tell
                    '''
                else:
                    script = '''
                    tell application "System Events"
                        set frontApp to first process whose frontmost is true
                        tell frontApp
                            set value of attribute "AXMinimized" of window 1 to true
                        end tell
                    end tell
                    '''
                self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                ps_script = '$shell = New-Object -ComObject Shell.Application; $shell.MinimizeAll()'
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            else:
                if app:
                    subprocess.run(["wmctrl", "-r", app, "-b", "add,hidden"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"app": app, "all": all_windows},
                message="Window(s) minimized"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to minimize: {str(e)}",
                error=str(e)
            )

    def _maximize_window(self, **kwargs) -> ToolResult:
        """Maximize a window."""
        app = kwargs.get("app")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = '''
                tell application "System Events"
                    tell (first process whose frontmost is true)
                        try
                            click button 2 of window 1
                        end try
                    end tell
                end tell
                '''
                self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                ps_script = '''
                Add-Type -TypeDefinition '
                using System;
                using System.Runtime.InteropServices;
                public class Window {
                    [DllImport("user32.dll")]
                    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                    [DllImport("user32.dll")]
                    public static extern IntPtr GetForegroundWindow();
                }
                '
                [Window]::ShowWindow([Window]::GetForegroundWindow(), 3)
                '''
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            else:
                subprocess.run(["wmctrl", "-r", ":ACTIVE:", "-b", "add,maximized_vert,maximized_horz"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"app": app},
                message="Window maximized"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to maximize: {str(e)}",
                error=str(e)
            )

    def _restore_window(self, **kwargs) -> ToolResult:
        """Restore a minimized window."""
        app = kwargs.get("app")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS and app:
                script = f'''
                tell application "{app}"
                    set miniaturized of every window to false
                    activate
                end tell
                '''
                self._run_applescript(script)
            
            return ToolResult(
                success=True,
                data={"app": app},
                message="Window restored"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to restore: {str(e)}",
                error=str(e)
            )

    def _close_window(self, **kwargs) -> ToolResult:
        """Close a window."""
        app = kwargs.get("app")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                if app:
                    script = f'tell application "{app}" to close window 1'
                else:
                    script = '''
                    tell application "System Events"
                        tell (first process whose frontmost is true)
                            click button 1 of window 1
                        end tell
                    end tell
                    '''
                self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                subprocess.run(["powershell", "-Command", 
                    "(Get-Process | Where-Object {$_.MainWindowHandle -ne 0} | Select-Object -First 1).CloseMainWindow()"],
                    capture_output=True)
            else:
                subprocess.run(["wmctrl", "-c", ":ACTIVE:"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"app": app},
                message="Window closed"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to close window: {str(e)}",
                error=str(e)
            )

    def _move_window(self, **kwargs) -> ToolResult:
        """Move a window to a specific position."""
        x = kwargs.get("x", 0)
        y = kwargs.get("y", 0)
        app = kwargs.get("app")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = f'''
                tell application "System Events"
                    tell (first process whose frontmost is true)
                        set position of window 1 to {{{x}, {y}}}
                    end tell
                end tell
                '''
                self._run_applescript(script)
            elif platform == Platform.LINUX:
                subprocess.run(["wmctrl", "-r", ":ACTIVE:", "-e", f"0,{x},{y},-1,-1"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"x": x, "y": y},
                message=f"Window moved to ({x}, {y})"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to move window: {str(e)}",
                error=str(e)
            )

    def _resize_window(self, **kwargs) -> ToolResult:
        """Resize a window."""
        width = kwargs.get("width", 800)
        height = kwargs.get("height", 600)
        app = kwargs.get("app")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = f'''
                tell application "System Events"
                    tell (first process whose frontmost is true)
                        set size of window 1 to {{{width}, {height}}}
                    end tell
                end tell
                '''
                self._run_applescript(script)
            elif platform == Platform.LINUX:
                subprocess.run(["wmctrl", "-r", ":ACTIVE:", "-e", f"0,-1,-1,{width},{height}"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"width": width, "height": height},
                message=f"Window resized to {width}x{height}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to resize window: {str(e)}",
                error=str(e)
            )

    def _tile_left(self, **kwargs) -> ToolResult:
        """Tile window to left half of screen."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                # Get screen size and tile
                script = '''
                tell application "System Events"
                    tell (first process whose frontmost is true)
                        set position of window 1 to {0, 25}
                        set size of window 1 to {960, 1055}
                    end tell
                end tell
                '''
                self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                # Use Win+Left shortcut
                subprocess.run(["powershell", "-Command", 
                    "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('^{LEFT}')"],
                    capture_output=True)
            else:
                # Get screen resolution
                result = subprocess.run(["xdpyinfo"], capture_output=True, text=True)
                # Default values
                subprocess.run(["wmctrl", "-r", ":ACTIVE:", "-e", "0,0,0,960,1080"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"position": "left"},
                message="Window tiled to left"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to tile left: {str(e)}",
                error=str(e)
            )

    def _tile_right(self, **kwargs) -> ToolResult:
        """Tile window to right half of screen."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = '''
                tell application "System Events"
                    tell (first process whose frontmost is true)
                        set position of window 1 to {960, 25}
                        set size of window 1 to {960, 1055}
                    end tell
                end tell
                '''
                self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                subprocess.run(["powershell", "-Command", 
                    "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('^{RIGHT}')"],
                    capture_output=True)
            else:
                subprocess.run(["wmctrl", "-r", ":ACTIVE:", "-e", "0,960,0,960,1080"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"position": "right"},
                message="Window tiled to right"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to tile right: {str(e)}",
                error=str(e)
            )

    def _center_window(self, **kwargs) -> ToolResult:
        """Center window on screen."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = '''
                tell application "System Events"
                    tell (first process whose frontmost is true)
                        set {w, h} to size of window 1
                        set position of window 1 to {(1920 - w) / 2, (1080 - h) / 2}
                    end tell
                end tell
                '''
                self._run_applescript(script)
            
            return ToolResult(
                success=True,
                data={},
                message="Window centered"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to center: {str(e)}",
                error=str(e)
            )

    def _fullscreen(self, **kwargs) -> ToolResult:
        """Toggle fullscreen mode."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = '''
                tell application "System Events"
                    tell (first process whose frontmost is true)
                        set value of attribute "AXFullScreen" of window 1 to not (value of attribute "AXFullScreen" of window 1)
                    end tell
                end tell
                '''
                self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                subprocess.run(["powershell", "-Command", 
                    "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{F11}')"],
                    capture_output=True)
            else:
                subprocess.run(["wmctrl", "-r", ":ACTIVE:", "-b", "toggle,fullscreen"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={},
                message="Fullscreen toggled"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to toggle fullscreen: {str(e)}",
                error=str(e)
            )

    def _arrange_windows(self, **kwargs) -> ToolResult:
        """Arrange windows in a layout."""
        layout = kwargs.get("layout", "cascade")  # cascade, grid, stack
        
        return ToolResult(
            success=True,
            data={"layout": layout},
            message=f"Use tile_left/tile_right for basic arrangement"
        )

    def _get_active_window(self, **kwargs) -> ToolResult:
        """Get information about the active window."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = '''
                tell application "System Events"
                    set frontApp to first process whose frontmost is true
                    set appName to name of frontApp
                    set winName to name of window 1 of frontApp
                    return appName & "|" & winName
                end tell
                '''
                result = self._run_applescript(script)
                if "|" in result:
                    app, title = result.split("|", 1)
                    return ToolResult(
                        success=True,
                        data={"app": app, "title": title},
                        message=f"Active: {app} - {title}"
                    )
            elif platform == Platform.WINDOWS:
                ps_script = '''
                Add-Type -TypeDefinition '
                using System;
                using System.Runtime.InteropServices;
                using System.Text;
                public class Window {
                    [DllImport("user32.dll")]
                    public static extern IntPtr GetForegroundWindow();
                    [DllImport("user32.dll")]
                    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
                }
                '
                $hwnd = [Window]::GetForegroundWindow()
                $sb = New-Object System.Text.StringBuilder 256
                [Window]::GetWindowText($hwnd, $sb, 256)
                $sb.ToString()
                '''
                result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
                if result.stdout.strip():
                    return ToolResult(
                        success=True,
                        data={"title": result.stdout.strip()},
                        message=f"Active window: {result.stdout.strip()}"
                    )
            
            return ToolResult(
                success=True,
                data={},
                message="Active window information not available"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get active window: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "List windows: window_tool --action list",
            "Focus app: window_tool --action focus --app 'Safari'",
            "Minimize: window_tool --action minimize",
            "Maximize: window_tool --action maximize",
            "Tile left: window_tool --action tile_left",
            "Resize: window_tool --action resize --width 800 --height 600",
        ]
