"""
Keyboard and Mouse tool for SysAgent CLI - Input simulation.
"""

import subprocess
import time
from typing import List, Dict, Any

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class KeyboardMouseTool(BaseTool):
    """Tool for simulating keyboard and mouse input."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="keyboard_mouse_tool",
            description="Simulate keyboard and mouse input - type, click, hotkeys",
            category=ToolCategory.SYSTEM,
            permissions=["input_control", "accessibility"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "type": self._type_text,
                "key": self._press_key,
                "hotkey": self._hotkey,
                "click": self._click,
                "double_click": self._double_click,
                "right_click": self._right_click,
                "move": self._move_mouse,
                "scroll": self._scroll,
                "drag": self._drag,
                "get_position": self._get_mouse_position,
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
                message=f"Input simulation failed: {str(e)}",
                error=str(e)
            )

    def _run_applescript(self, script: str) -> str:
        """Run AppleScript on macOS."""
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True
        )
        return result.stdout.strip()

    def _type_text(self, **kwargs) -> ToolResult:
        """Type text as keyboard input."""
        text = kwargs.get("text", "")
        delay = kwargs.get("delay", 0.05)
        
        if not text:
            return ToolResult(
                success=False,
                data={},
                message="No text provided"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                # Escape special characters for AppleScript
                escaped = text.replace('\\', '\\\\').replace('"', '\\"')
                script = f'''
                tell application "System Events"
                    keystroke "{escaped}"
                end tell
                '''
                self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                ps_script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.SendKeys]::SendWait("{text}")
                '''
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            else:
                # Use xdotool on Linux
                subprocess.run(["xdotool", "type", "--delay", str(int(delay*1000)), text], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"text": text[:50] + "..." if len(text) > 50 else text},
                message=f"Typed {len(text)} characters"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to type: {str(e)}",
                error=str(e)
            )

    def _press_key(self, **kwargs) -> ToolResult:
        """Press a single key."""
        key = kwargs.get("key", "")
        
        if not key:
            return ToolResult(
                success=False,
                data={},
                message="No key specified"
            )
        
        platform = detect_platform()
        
        # Key mapping
        key_map = {
            "enter": ("return", "{ENTER}", "Return"),
            "tab": ("tab", "{TAB}", "Tab"),
            "escape": ("escape", "{ESC}", "Escape"),
            "space": ("space", " ", "space"),
            "backspace": ("delete", "{BACKSPACE}", "BackSpace"),
            "delete": ("forward delete", "{DELETE}", "Delete"),
            "up": ("up arrow", "{UP}", "Up"),
            "down": ("down arrow", "{DOWN}", "Down"),
            "left": ("left arrow", "{LEFT}", "Left"),
            "right": ("right arrow", "{RIGHT}", "Right"),
            "home": ("home", "{HOME}", "Home"),
            "end": ("end", "{END}", "End"),
            "pageup": ("page up", "{PGUP}", "Page_Up"),
            "pagedown": ("page down", "{PGDN}", "Page_Down"),
        }
        
        key_lower = key.lower()
        mapped = key_map.get(key_lower, (key, key, key))
        
        try:
            if platform == Platform.MACOS:
                script = f'''
                tell application "System Events"
                    key code {self._get_mac_keycode(mapped[0])}
                end tell
                '''
                # Simpler approach using keystroke for special keys
                if key_lower in ["enter", "return"]:
                    script = 'tell application "System Events" to keystroke return'
                elif key_lower == "tab":
                    script = 'tell application "System Events" to keystroke tab'
                elif key_lower == "escape":
                    script = 'tell application "System Events" to key code 53'
                else:
                    script = f'tell application "System Events" to keystroke "{key}"'
                self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                subprocess.run(["powershell", "-Command", 
                    f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{mapped[1]}')"],
                    capture_output=True)
            else:
                subprocess.run(["xdotool", "key", mapped[2]], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"key": key},
                message=f"Pressed key: {key}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to press key: {str(e)}",
                error=str(e)
            )

    def _get_mac_keycode(self, key: str) -> int:
        """Get macOS key code."""
        codes = {
            "return": 36, "tab": 48, "space": 49, "delete": 51,
            "escape": 53, "up arrow": 126, "down arrow": 125,
            "left arrow": 123, "right arrow": 124
        }
        return codes.get(key.lower(), 0)

    def _hotkey(self, **kwargs) -> ToolResult:
        """Press a keyboard shortcut/hotkey."""
        keys = kwargs.get("keys", [])  # e.g., ["cmd", "c"] or ["ctrl", "alt", "delete"]
        shortcut = kwargs.get("shortcut", "")  # e.g., "cmd+c"
        
        if shortcut:
            keys = [k.strip() for k in shortcut.lower().split("+")]
        
        if not keys:
            return ToolResult(
                success=False,
                data={},
                message="No keys specified. Use keys=['cmd', 'c'] or shortcut='cmd+c'"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                modifiers = []
                key_char = ""
                
                for k in keys:
                    k = k.lower()
                    if k in ["cmd", "command"]:
                        modifiers.append("command down")
                    elif k in ["ctrl", "control"]:
                        modifiers.append("control down")
                    elif k in ["alt", "option"]:
                        modifiers.append("option down")
                    elif k in ["shift"]:
                        modifiers.append("shift down")
                    else:
                        key_char = k
                
                mod_str = ", ".join(modifiers)
                if key_char:
                    script = f'''
                    tell application "System Events"
                        keystroke "{key_char}" using {{{mod_str}}}
                    end tell
                    '''
                    self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                # Map to SendKeys format
                key_map = {"ctrl": "^", "alt": "%", "shift": "+", "win": "^{ESC}"}
                send_keys = ""
                for k in keys:
                    if k.lower() in key_map:
                        send_keys += key_map[k.lower()]
                    else:
                        send_keys += k
                subprocess.run(["powershell", "-Command", 
                    f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{send_keys}')"],
                    capture_output=True)
            else:
                subprocess.run(["xdotool", "key", "+".join(keys)], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"keys": keys},
                message=f"Pressed hotkey: {'+'.join(keys)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to press hotkey: {str(e)}",
                error=str(e)
            )

    def _click(self, **kwargs) -> ToolResult:
        """Click at a position."""
        x = kwargs.get("x")
        y = kwargs.get("y")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                if x is not None and y is not None:
                    script = f'''
                    do shell script "cliclick c:{x},{y}"
                    '''
                    # Fallback without cliclick
                    script = f'''
                    tell application "System Events"
                        click at {{{x}, {y}}}
                    end tell
                    '''
                else:
                    script = '''
                    tell application "System Events"
                        click
                    end tell
                    '''
                try:
                    self._run_applescript(script)
                except:
                    # Try using mouse location script
                    pass
            elif platform == Platform.WINDOWS:
                if x is not None and y is not None:
                    ps_script = f'''
                    Add-Type -TypeDefinition '
                    using System;
                    using System.Runtime.InteropServices;
                    public class Mouse {{
                        [DllImport("user32.dll")]
                        public static extern bool SetCursorPos(int x, int y);
                        [DllImport("user32.dll")]
                        public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtraInfo);
                    }}
                    '
                    [Mouse]::SetCursorPos({x}, {y})
                    [Mouse]::mouse_event(2, 0, 0, 0, 0)
                    [Mouse]::mouse_event(4, 0, 0, 0, 0)
                    '''
                    subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            else:
                if x is not None and y is not None:
                    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], capture_output=True)
                else:
                    subprocess.run(["xdotool", "click", "1"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"x": x, "y": y},
                message=f"Clicked at ({x}, {y})" if x else "Clicked"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to click: {str(e)}",
                error=str(e)
            )

    def _double_click(self, **kwargs) -> ToolResult:
        """Double click."""
        x = kwargs.get("x")
        y = kwargs.get("y")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                if x is not None and y is not None:
                    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "--repeat", "2", "1"], capture_output=True)
                else:
                    subprocess.run(["xdotool", "click", "--repeat", "2", "1"], capture_output=True)
            else:
                # Double click by clicking twice
                self._click(**kwargs)
                time.sleep(0.1)
                self._click(**kwargs)
            
            return ToolResult(
                success=True,
                data={"x": x, "y": y},
                message="Double clicked"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to double click: {str(e)}",
                error=str(e)
            )

    def _right_click(self, **kwargs) -> ToolResult:
        """Right click."""
        x = kwargs.get("x")
        y = kwargs.get("y")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                if x is not None and y is not None:
                    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "3"], capture_output=True)
                else:
                    subprocess.run(["xdotool", "click", "3"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"x": x, "y": y},
                message="Right clicked"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to right click: {str(e)}",
                error=str(e)
            )

    def _move_mouse(self, **kwargs) -> ToolResult:
        """Move mouse to a position."""
        x = kwargs.get("x", 0)
        y = kwargs.get("y", 0)
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = f'''
                do shell script "cliclick m:{x},{y}"
                '''
                try:
                    subprocess.run(["cliclick", f"m:{x},{y}"], capture_output=True)
                except:
                    pass
            elif platform == Platform.WINDOWS:
                ps_script = f'''
                Add-Type -TypeDefinition '
                using System.Runtime.InteropServices;
                public class Mouse {{
                    [DllImport("user32.dll")]
                    public static extern bool SetCursorPos(int x, int y);
                }}
                '
                [Mouse]::SetCursorPos({x}, {y})
                '''
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            else:
                subprocess.run(["xdotool", "mousemove", str(x), str(y)], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"x": x, "y": y},
                message=f"Mouse moved to ({x}, {y})"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to move mouse: {str(e)}",
                error=str(e)
            )

    def _scroll(self, **kwargs) -> ToolResult:
        """Scroll the mouse wheel."""
        direction = kwargs.get("direction", "down")
        amount = kwargs.get("amount", 3)
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                delta = -amount if direction == "down" else amount
                script = f'''
                do shell script "cliclick w:{delta}"
                '''
                try:
                    subprocess.run(["cliclick", f"w:{delta}"], capture_output=True)
                except:
                    pass
            elif platform == Platform.LINUX:
                button = "5" if direction == "down" else "4"
                subprocess.run(["xdotool", "click", "--repeat", str(amount), button], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"direction": direction, "amount": amount},
                message=f"Scrolled {direction} {amount} times"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to scroll: {str(e)}",
                error=str(e)
            )

    def _drag(self, **kwargs) -> ToolResult:
        """Drag from one position to another."""
        from_x = kwargs.get("from_x", 0)
        from_y = kwargs.get("from_y", 0)
        to_x = kwargs.get("to_x", 0)
        to_y = kwargs.get("to_y", 0)
        
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                subprocess.run([
                    "xdotool", "mousemove", str(from_x), str(from_y),
                    "mousedown", "1",
                    "mousemove", str(to_x), str(to_y),
                    "mouseup", "1"
                ], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"from": (from_x, from_y), "to": (to_x, to_y)},
                message=f"Dragged from ({from_x}, {from_y}) to ({to_x}, {to_y})"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to drag: {str(e)}",
                error=str(e)
            )

    def _get_mouse_position(self, **kwargs) -> ToolResult:
        """Get current mouse position."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = '''
                tell application "System Events"
                    return (position of the mouse)
                end tell
                '''
                # Use a different approach
                result = subprocess.run(
                    ["python3", "-c", "import Quartz; loc = Quartz.NSEvent.mouseLocation(); print(f'{int(loc.x)},{int(1080-loc.y)}')"],
                    capture_output=True, text=True
                )
                if result.stdout.strip():
                    x, y = result.stdout.strip().split(",")
                    return ToolResult(
                        success=True,
                        data={"x": int(x), "y": int(y)},
                        message=f"Mouse at ({x}, {y})"
                    )
            elif platform == Platform.LINUX:
                result = subprocess.run(
                    ["xdotool", "getmouselocation"],
                    capture_output=True, text=True
                )
                if result.stdout:
                    # Parse "x:123 y:456 screen:0 window:12345"
                    parts = result.stdout.split()
                    x = int(parts[0].split(":")[1])
                    y = int(parts[1].split(":")[1])
                    return ToolResult(
                        success=True,
                        data={"x": x, "y": y},
                        message=f"Mouse at ({x}, {y})"
                    )
            
            return ToolResult(
                success=True,
                data={},
                message="Could not get mouse position"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get position: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Type text: keyboard_mouse_tool --action type --text 'Hello World'",
            "Press key: keyboard_mouse_tool --action key --key 'enter'",
            "Hotkey: keyboard_mouse_tool --action hotkey --shortcut 'cmd+c'",
            "Click: keyboard_mouse_tool --action click --x 100 --y 200",
            "Scroll: keyboard_mouse_tool --action scroll --direction down --amount 5",
        ]
