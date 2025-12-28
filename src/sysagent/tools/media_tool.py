"""
Media tool for SysAgent CLI - Volume and media playback control.
"""

import subprocess
from typing import List

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class MediaTool(BaseTool):
    """Tool for controlling media playback and audio."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="media_tool",
            description="Control volume, mute, and media playback",
            category=ToolCategory.SYSTEM,
            permissions=["audio_control"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "volume": self._set_volume,
                "get_volume": self._get_volume,
                "mute": self._mute,
                "unmute": self._unmute,
                "toggle_mute": self._toggle_mute,
                "play": self._play,
                "pause": self._pause,
                "play_pause": self._play_pause,
                "next": self._next_track,
                "previous": self._previous_track,
                "stop": self._stop,
                "get_now_playing": self._get_now_playing,
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
                message=f"Media operation failed: {str(e)}",
                error=str(e)
            )

    def _run_applescript(self, script: str) -> str:
        """Run AppleScript on macOS."""
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True
        )
        return result.stdout.strip()

    def _set_volume(self, **kwargs) -> ToolResult:
        """Set system volume (0-100)."""
        level = kwargs.get("level", 50)
        level = max(0, min(100, int(level)))
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                # macOS volume is 0-100
                script = f'set volume output volume {level}'
                self._run_applescript(script)
            elif platform == Platform.WINDOWS:
                # Use PowerShell with audio COM object
                ps_script = f'''
                $obj = New-Object -ComObject WScript.Shell
                $volume = {level}
                # Set volume by sending volume keys
                '''
                # Alternative using nircmd if available
                subprocess.run(["nircmd", "setsysvolume", str(int(level * 655.35))], capture_output=True)
            else:
                # Linux with pactl or amixer
                try:
                    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"], capture_output=True)
                except:
                    subprocess.run(["amixer", "sset", "Master", f"{level}%"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"volume": level},
                message=f"Volume set to {level}%"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to set volume: {str(e)}",
                error=str(e)
            )

    def _get_volume(self, **kwargs) -> ToolResult:
        """Get current system volume."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                result = self._run_applescript("output volume of (get volume settings)")
                volume = int(result) if result.isdigit() else 0
            elif platform == Platform.WINDOWS:
                # This is more complex on Windows
                volume = 50  # Placeholder
            else:
                result = subprocess.run(
                    ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                    capture_output=True, text=True
                )
                # Parse output like "Volume: front-left: 65536 / 100%"
                if "%" in result.stdout:
                    import re
                    match = re.search(r'(\d+)%', result.stdout)
                    volume = int(match.group(1)) if match else 0
                else:
                    volume = 0
            
            return ToolResult(
                success=True,
                data={"volume": volume},
                message=f"Volume is {volume}%"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get volume: {str(e)}",
                error=str(e)
            )

    def _mute(self, **kwargs) -> ToolResult:
        """Mute audio."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                self._run_applescript("set volume with output muted")
            elif platform == Platform.WINDOWS:
                subprocess.run(["nircmd", "mutesysvolume", "1"], capture_output=True)
            else:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"muted": True},
                message="Audio muted"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to mute: {str(e)}",
                error=str(e)
            )

    def _unmute(self, **kwargs) -> ToolResult:
        """Unmute audio."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                self._run_applescript("set volume without output muted")
            elif platform == Platform.WINDOWS:
                subprocess.run(["nircmd", "mutesysvolume", "0"], capture_output=True)
            else:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"muted": False},
                message="Audio unmuted"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to unmute: {str(e)}",
                error=str(e)
            )

    def _toggle_mute(self, **kwargs) -> ToolResult:
        """Toggle mute state."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                # Check current state and toggle
                is_muted = self._run_applescript("output muted of (get volume settings)")
                if is_muted == "true":
                    return self._unmute()
                else:
                    return self._mute()
            elif platform == Platform.WINDOWS:
                subprocess.run(["nircmd", "mutesysvolume", "2"], capture_output=True)
            else:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={},
                message="Mute toggled"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to toggle mute: {str(e)}",
                error=str(e)
            )

    def _play(self, **kwargs) -> ToolResult:
        """Start media playback."""
        return self._play_pause(**kwargs)

    def _pause(self, **kwargs) -> ToolResult:
        """Pause media playback."""
        return self._play_pause(**kwargs)

    def _play_pause(self, **kwargs) -> ToolResult:
        """Toggle play/pause."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                # Use media key
                script = '''
                tell application "System Events"
                    key code 49 using {command down}
                end tell
                '''
                # Or use Music/Spotify directly
                script = '''
                tell application "System Events"
                    key code 49
                end tell
                '''
                subprocess.run(["osascript", "-e", 
                    'tell application "System Events" to key code 49'], capture_output=True)
            elif platform == Platform.WINDOWS:
                subprocess.run(["nircmd", "sendkeypress", "0x1000"], capture_output=True)
            else:
                subprocess.run(["playerctl", "play-pause"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={},
                message="Toggled play/pause"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to toggle playback: {str(e)}",
                error=str(e)
            )

    def _next_track(self, **kwargs) -> ToolResult:
        """Skip to next track."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                subprocess.run(["osascript", "-e", 
                    'tell application "System Events" to key code 124 using {command down}'], 
                    capture_output=True)
            elif platform == Platform.WINDOWS:
                subprocess.run(["nircmd", "sendkeypress", "0x1002"], capture_output=True)
            else:
                subprocess.run(["playerctl", "next"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={},
                message="Skipped to next track"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to skip: {str(e)}",
                error=str(e)
            )

    def _previous_track(self, **kwargs) -> ToolResult:
        """Go to previous track."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                subprocess.run(["osascript", "-e", 
                    'tell application "System Events" to key code 123 using {command down}'], 
                    capture_output=True)
            elif platform == Platform.WINDOWS:
                subprocess.run(["nircmd", "sendkeypress", "0x1001"], capture_output=True)
            else:
                subprocess.run(["playerctl", "previous"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={},
                message="Went to previous track"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed: {str(e)}",
                error=str(e)
            )

    def _stop(self, **kwargs) -> ToolResult:
        """Stop media playback."""
        platform = detect_platform()
        
        try:
            if platform == Platform.LINUX:
                subprocess.run(["playerctl", "stop"], capture_output=True)
            
            return ToolResult(
                success=True,
                data={},
                message="Playback stopped"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to stop: {str(e)}",
                error=str(e)
            )

    def _get_now_playing(self, **kwargs) -> ToolResult:
        """Get currently playing track info."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                # Try Music app
                script = '''
                tell application "Music"
                    if player state is playing then
                        set trackName to name of current track
                        set artistName to artist of current track
                        return trackName & " - " & artistName
                    else
                        return "Nothing playing"
                    end if
                end tell
                '''
                try:
                    result = self._run_applescript(script)
                    return ToolResult(
                        success=True,
                        data={"now_playing": result},
                        message=result
                    )
                except:
                    pass
                
                # Try Spotify
                script = '''
                tell application "Spotify"
                    if player state is playing then
                        set trackName to name of current track
                        set artistName to artist of current track
                        return trackName & " - " & artistName
                    else
                        return "Nothing playing"
                    end if
                end tell
                '''
                try:
                    result = self._run_applescript(script)
                    return ToolResult(
                        success=True,
                        data={"now_playing": result},
                        message=result
                    )
                except:
                    pass
            elif platform == Platform.LINUX:
                result = subprocess.run(
                    ["playerctl", "metadata", "--format", "{{ artist }} - {{ title }}"],
                    capture_output=True, text=True
                )
                if result.stdout.strip():
                    return ToolResult(
                        success=True,
                        data={"now_playing": result.stdout.strip()},
                        message=result.stdout.strip()
                    )
            
            return ToolResult(
                success=True,
                data={"now_playing": "Nothing playing or not available"},
                message="Could not detect now playing"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get now playing: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Set volume: media_tool --action volume --level 50",
            "Mute: media_tool --action mute",
            "Unmute: media_tool --action unmute",
            "Play/pause: media_tool --action play_pause",
            "Next track: media_tool --action next",
            "Get now playing: media_tool --action get_now_playing",
        ]
