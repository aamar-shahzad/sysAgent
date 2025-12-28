"""
Screen Recording Tool for SysAgent - Record screen and create videos.
"""

import subprocess
import os
import time
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class ScreenRecorderTool(BaseTool):
    """Tool for recording screen activity."""
    
    _recording_process: Optional[subprocess.Popen] = None
    _is_recording: bool = False
    _output_path: Optional[str] = None
    _start_time: Optional[float] = None
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="screen_recorder_tool",
            description="Record screen activity to video files",
            category=ToolCategory.MEDIA,
            permissions=["screenshot", "file_access"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "start": self._start_recording,
                "stop": self._stop_recording,
                "status": self._get_status,
                "list": self._list_recordings,
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
                message=f"Screen recording failed: {str(e)}",
                error=str(e)
            )

    def _start_recording(self, **kwargs) -> ToolResult:
        """Start screen recording."""
        if self._is_recording:
            return ToolResult(
                success=False,
                data={},
                message="Recording already in progress"
            )
        
        output_path = kwargs.get("path", "")
        fps = kwargs.get("fps", 30)
        audio = kwargs.get("audio", True)
        region = kwargs.get("region")  # Optional: "x,y,width,height"
        
        # Generate default path if not provided
        if not output_path:
            recordings_dir = Path.home() / "SysAgent_Recordings"
            recordings_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(recordings_dir / f"recording_{timestamp}.mp4")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                # Use ffmpeg with avfoundation
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "avfoundation",
                    "-framerate", str(fps),
                    "-i", "1:0" if audio else "1",  # screen:audio
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "23",
                ]
                if audio:
                    cmd.extend(["-c:a", "aac", "-b:a", "128k"])
                cmd.append(output_path)
                
            elif platform == Platform.LINUX:
                # Use ffmpeg with x11grab
                display = os.environ.get("DISPLAY", ":0")
                
                # Get screen size
                try:
                    result = subprocess.run(
                        ["xdpyinfo"],
                        capture_output=True, text=True
                    )
                    for line in result.stdout.split("\n"):
                        if "dimensions:" in line:
                            size = line.split()[1]
                            break
                    else:
                        size = "1920x1080"
                except:
                    size = "1920x1080"
                
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "x11grab",
                    "-framerate", str(fps),
                    "-video_size", size,
                    "-i", display,
                ]
                
                if audio:
                    cmd.extend([
                        "-f", "pulse",
                        "-i", "default",
                        "-c:a", "aac", "-b:a", "128k"
                    ])
                
                cmd.extend([
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "23",
                    output_path
                ])
                
            elif platform == Platform.WINDOWS:
                # Use ffmpeg with gdigrab
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "gdigrab",
                    "-framerate", str(fps),
                    "-i", "desktop",
                ]
                
                if audio:
                    cmd.extend([
                        "-f", "dshow",
                        "-i", "audio=virtual-audio-capturer",
                        "-c:a", "aac", "-b:a", "128k"
                    ])
                
                cmd.extend([
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "23",
                    output_path
                ])
            
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Screen recording not supported on this platform"
                )
            
            # Start recording in background
            self._recording_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._is_recording = True
            self._output_path = output_path
            self._start_time = time.time()
            
            return ToolResult(
                success=True,
                data={
                    "path": output_path,
                    "fps": fps,
                    "audio": audio
                },
                message=f"Recording started. Output: {output_path}"
            )
            
        except FileNotFoundError:
            return ToolResult(
                success=False,
                data={},
                message="ffmpeg not found. Install: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to start recording: {str(e)}",
                error=str(e)
            )

    def _stop_recording(self, **kwargs) -> ToolResult:
        """Stop screen recording."""
        if not self._is_recording or not self._recording_process:
            return ToolResult(
                success=False,
                data={},
                message="No recording in progress"
            )
        
        try:
            # Send 'q' to ffmpeg to stop gracefully
            self._recording_process.stdin.write(b'q') if self._recording_process.stdin else None
            self._recording_process.terminate()
            self._recording_process.wait(timeout=10)
            
            duration = time.time() - self._start_time if self._start_time else 0
            output_path = self._output_path
            
            # Reset state
            self._is_recording = False
            self._recording_process = None
            self._start_time = None
            old_path = self._output_path
            self._output_path = None
            
            # Verify file exists
            if old_path and Path(old_path).exists():
                file_size = Path(old_path).stat().st_size
                return ToolResult(
                    success=True,
                    data={
                        "path": old_path,
                        "duration_seconds": round(duration, 1),
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    },
                    message=f"Recording saved: {old_path} ({round(duration, 1)}s)"
                )
            else:
                return ToolResult(
                    success=True,
                    data={"path": old_path, "duration": duration},
                    message=f"Recording stopped. Duration: {round(duration, 1)}s"
                )
                
        except Exception as e:
            # Force kill if graceful stop fails
            if self._recording_process:
                self._recording_process.kill()
            self._is_recording = False
            self._recording_process = None
            
            return ToolResult(
                success=False,
                data={},
                message=f"Error stopping recording: {str(e)}",
                error=str(e)
            )

    def _get_status(self, **kwargs) -> ToolResult:
        """Get current recording status."""
        if self._is_recording:
            duration = time.time() - self._start_time if self._start_time else 0
            return ToolResult(
                success=True,
                data={
                    "is_recording": True,
                    "output_path": self._output_path,
                    "duration_seconds": round(duration, 1)
                },
                message=f"Recording in progress: {round(duration, 1)}s"
            )
        else:
            return ToolResult(
                success=True,
                data={"is_recording": False},
                message="Not currently recording"
            )

    def _list_recordings(self, **kwargs) -> ToolResult:
        """List saved recordings."""
        recordings_dir = Path.home() / "SysAgent_Recordings"
        
        if not recordings_dir.exists():
            return ToolResult(
                success=True,
                data={"recordings": []},
                message="No recordings directory found"
            )
        
        recordings = []
        for file in recordings_dir.glob("*.mp4"):
            stat = file.stat()
            recordings.append({
                "name": file.name,
                "path": str(file),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            })
        
        recordings.sort(key=lambda x: x["created"], reverse=True)
        
        return ToolResult(
            success=True,
            data={"recordings": recordings[:20]},
            message=f"Found {len(recordings)} recordings"
        )

    def get_usage_examples(self) -> List[str]:
        return [
            "Start recording: screen_recorder_tool --action start",
            "Start with custom path: screen_recorder_tool --action start --path /path/to/video.mp4",
            "Stop recording: screen_recorder_tool --action stop",
            "Check status: screen_recorder_tool --action status",
            "List recordings: screen_recorder_tool --action list",
        ]
