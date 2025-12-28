"""
Screenshot tool for SysAgent CLI.
"""

import subprocess
import os
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class ScreenshotTool(BaseTool):
    """Tool for screen capture and analysis."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="screenshot_tool",
            description="Screen capture, window capture, and screenshot analysis",
            category=ToolCategory.VISION,
            permissions=["screenshot", "screen_access"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Execute screenshot action."""
        try:
            if action == "capture":
                return self._capture_screen(**kwargs)
            elif action == "window":
                return self._capture_window(**kwargs)
            elif action == "region":
                return self._capture_region(**kwargs)
            elif action == "analyze":
                return self._analyze_screenshot(**kwargs)
            elif action == "list":
                return self._list_screenshots(**kwargs)
            elif action == "delete":
                return self._delete_screenshot(**kwargs)
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
                message=f"Screenshot operation failed: {str(e)}",
                error=str(e)
            )

    def _get_default_path(self) -> Path:
        """Get default screenshot save path."""
        current_platform = detect_platform()
        
        if current_platform == Platform.MACOS:
            default_dir = Path.home() / "Desktop"
        elif current_platform == Platform.WINDOWS:
            default_dir = Path.home() / "Pictures" / "Screenshots"
        else:
            default_dir = Path.home() / "Pictures"
        
        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir

    def _generate_filename(self, prefix: str = "screenshot") -> str:
        """Generate a unique filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.png"

    def _capture_screen(self, **kwargs) -> ToolResult:
        """Capture full screen."""
        output_path = kwargs.get("output") or kwargs.get("path")
        delay = kwargs.get("delay", 0)
        
        if not output_path:
            output_path = str(self._get_default_path() / self._generate_filename())
        
        if delay > 0:
            time.sleep(delay)
        
        try:
            current_platform = detect_platform()
            
            if current_platform == Platform.MACOS:
                subprocess.run(
                    ["screencapture", "-x", output_path],
                    capture_output=True,
                    check=True
                )
                
            elif current_platform == Platform.LINUX:
                # Try different tools
                success = False
                errors = []
                
                # Try gnome-screenshot
                try:
                    subprocess.run(
                        ["gnome-screenshot", "-f", output_path],
                        capture_output=True,
                        check=True
                    )
                    success = True
                except (FileNotFoundError, subprocess.CalledProcessError) as e:
                    errors.append(f"gnome-screenshot: {e}")
                
                # Try scrot
                if not success:
                    try:
                        subprocess.run(
                            ["scrot", output_path],
                            capture_output=True,
                            check=True
                        )
                        success = True
                    except (FileNotFoundError, subprocess.CalledProcessError) as e:
                        errors.append(f"scrot: {e}")
                
                # Try import from ImageMagick
                if not success:
                    try:
                        subprocess.run(
                            ["import", "-window", "root", output_path],
                            capture_output=True,
                            check=True
                        )
                        success = True
                    except (FileNotFoundError, subprocess.CalledProcessError) as e:
                        errors.append(f"import: {e}")
                
                # Try grim for Wayland
                if not success:
                    try:
                        subprocess.run(
                            ["grim", output_path],
                            capture_output=True,
                            check=True
                        )
                        success = True
                    except (FileNotFoundError, subprocess.CalledProcessError) as e:
                        errors.append(f"grim: {e}")
                
                if not success:
                    return ToolResult(
                        success=False,
                        data={},
                        message="No screenshot tool found (install scrot, gnome-screenshot, or grim)",
                        error="; ".join(errors)
                    )
                    
            elif current_platform == Platform.WINDOWS:
                # Use PowerShell with .NET
                ps_script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen
                $bitmap = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size)
                $bitmap.Save("{output_path}")
                '''
                subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    check=True
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Screenshots not supported on this platform",
                    error="Unsupported platform"
                )
            
            # Verify file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                return ToolResult(
                    success=True,
                    data={
                        "path": output_path,
                        "size_bytes": file_size
                    },
                    message=f"Screenshot saved to {output_path}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Screenshot capture failed - file not created",
                    error="Capture failed"
                )
                
        except subprocess.CalledProcessError as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Screenshot capture failed: {e.stderr}",
                error=str(e)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Screenshot capture failed: {str(e)}",
                error=str(e)
            )

    def _capture_window(self, **kwargs) -> ToolResult:
        """Capture a specific window."""
        window_name = kwargs.get("window") or kwargs.get("name")
        output_path = kwargs.get("output") or kwargs.get("path")
        
        if not output_path:
            output_path = str(self._get_default_path() / self._generate_filename("window"))
        
        try:
            current_platform = detect_platform()
            
            if current_platform == Platform.MACOS:
                if window_name:
                    # Use screencapture with window selection by name
                    subprocess.run(
                        ["screencapture", "-x", "-l", window_name, output_path],
                        capture_output=True
                    )
                else:
                    # Interactive window selection
                    subprocess.run(
                        ["screencapture", "-x", "-w", output_path],
                        capture_output=True
                    )
                    
            elif current_platform == Platform.LINUX:
                try:
                    # Use scrot with window selection
                    subprocess.run(
                        ["scrot", "-u", output_path],
                        capture_output=True,
                        check=True
                    )
                except FileNotFoundError:
                    # Try import with window ID
                    subprocess.run(
                        ["import", output_path],
                        capture_output=True
                    )
                    
            elif current_platform == Platform.WINDOWS:
                # Interactive window capture on Windows is complex
                return ToolResult(
                    success=False,
                    data={},
                    message="Window capture on Windows requires interactive selection",
                    error="Not fully implemented"
                )
            
            if os.path.exists(output_path):
                return ToolResult(
                    success=True,
                    data={"path": output_path, "size_bytes": os.path.getsize(output_path)},
                    message=f"Window screenshot saved to {output_path}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Window capture failed",
                    error="File not created"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Window capture failed: {str(e)}",
                error=str(e)
            )

    def _capture_region(self, **kwargs) -> ToolResult:
        """Capture a region of the screen."""
        x = kwargs.get("x", 0)
        y = kwargs.get("y", 0)
        width = kwargs.get("width")
        height = kwargs.get("height")
        output_path = kwargs.get("output") or kwargs.get("path")
        
        if not output_path:
            output_path = str(self._get_default_path() / self._generate_filename("region"))
        
        try:
            current_platform = detect_platform()
            
            if current_platform == Platform.MACOS:
                if width and height:
                    # Capture specific region
                    subprocess.run(
                        ["screencapture", "-x", "-R", f"{x},{y},{width},{height}", output_path],
                        capture_output=True
                    )
                else:
                    # Interactive region selection
                    subprocess.run(
                        ["screencapture", "-x", "-s", output_path],
                        capture_output=True
                    )
                    
            elif current_platform == Platform.LINUX:
                if width and height:
                    # Use scrot with geometry
                    try:
                        subprocess.run(
                            ["scrot", "-a", f"{x},{y},{width},{height}", output_path],
                            capture_output=True,
                            check=True
                        )
                    except FileNotFoundError:
                        # Use import with geometry
                        subprocess.run(
                            ["import", "-window", "root", "-crop", f"{width}x{height}+{x}+{y}", output_path],
                            capture_output=True
                        )
                else:
                    # Interactive selection
                    subprocess.run(
                        ["scrot", "-s", output_path],
                        capture_output=True
                    )
                    
            elif current_platform == Platform.WINDOWS:
                return ToolResult(
                    success=False,
                    data={},
                    message="Region capture on Windows not fully implemented",
                    error="Not implemented"
                )
            
            if os.path.exists(output_path):
                return ToolResult(
                    success=True,
                    data={"path": output_path, "size_bytes": os.path.getsize(output_path)},
                    message=f"Region screenshot saved to {output_path}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Region capture failed or cancelled",
                    error="File not created"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Region capture failed: {str(e)}",
                error=str(e)
            )

    def _analyze_screenshot(self, **kwargs) -> ToolResult:
        """Analyze a screenshot (requires vision model)."""
        image_path = kwargs.get("path") or kwargs.get("image")
        
        if not image_path:
            return ToolResult(
                success=False,
                data={},
                message="No image path provided",
                error="Missing path"
            )
        
        if not os.path.exists(image_path):
            return ToolResult(
                success=False,
                data={},
                message=f"Image not found: {image_path}",
                error="File not found"
            )
        
        try:
            # Get basic image info
            file_size = os.path.getsize(image_path)
            
            # Try to get image dimensions using PIL if available
            try:
                from PIL import Image
                with Image.open(image_path) as img:
                    width, height = img.size
                    mode = img.mode
                    format_type = img.format
                    
                return ToolResult(
                    success=True,
                    data={
                        "path": image_path,
                        "width": width,
                        "height": height,
                        "mode": mode,
                        "format": format_type,
                        "size_bytes": file_size
                    },
                    message=f"Image: {width}x{height} {format_type} ({file_size} bytes)"
                )
            except ImportError:
                return ToolResult(
                    success=True,
                    data={
                        "path": image_path,
                        "size_bytes": file_size,
                        "note": "Install PIL/Pillow for detailed analysis"
                    },
                    message=f"Image file: {file_size} bytes (install Pillow for details)"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Analysis failed: {str(e)}",
                error=str(e)
            )

    def _list_screenshots(self, **kwargs) -> ToolResult:
        """List saved screenshots."""
        directory = kwargs.get("directory")
        
        if not directory:
            directory = self._get_default_path()
        else:
            directory = Path(directory)
        
        try:
            screenshots = []
            
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp"]:
                for img_file in directory.glob(ext):
                    screenshots.append({
                        "name": img_file.name,
                        "path": str(img_file),
                        "size_bytes": img_file.stat().st_size,
                        "modified": datetime.fromtimestamp(img_file.stat().st_mtime).isoformat()
                    })
            
            # Sort by modification time (newest first)
            screenshots.sort(key=lambda x: x["modified"], reverse=True)
            
            return ToolResult(
                success=True,
                data={"screenshots": screenshots[:50], "count": len(screenshots)},
                message=f"Found {len(screenshots)} screenshots in {directory}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list screenshots: {str(e)}",
                error=str(e)
            )

    def _delete_screenshot(self, **kwargs) -> ToolResult:
        """Delete a screenshot."""
        path = kwargs.get("path")
        
        if not path:
            return ToolResult(
                success=False,
                data={},
                message="No path provided",
                error="Missing path"
            )
        
        try:
            if os.path.exists(path):
                os.remove(path)
                return ToolResult(
                    success=True,
                    data={"path": path},
                    message=f"Deleted screenshot: {path}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Screenshot not found: {path}",
                    error="File not found"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to delete screenshot: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        """Get usage examples for this tool."""
        return [
            "Capture screen: screenshot_tool --action capture",
            "Capture with delay: screenshot_tool --action capture --delay 3",
            "Capture window: screenshot_tool --action window",
            "Capture region: screenshot_tool --action region --x 0 --y 0 --width 800 --height 600",
            "Analyze image: screenshot_tool --action analyze --path /path/to/image.png",
            "List screenshots: screenshot_tool --action list",
        ]
