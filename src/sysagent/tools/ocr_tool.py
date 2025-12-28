"""
OCR Tool for SysAgent - Extract text from images and screen.
"""

import subprocess
import tempfile
import os
from typing import List, Dict, Any
from pathlib import Path

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class OCRTool(BaseTool):
    """Tool for extracting text from images and screen regions."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="ocr_tool",
            description="Extract text from images, screenshots, and screen regions using OCR",
            category=ToolCategory.MEDIA,
            permissions=["screenshot", "file_access"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "from_image": self._ocr_from_image,
                "from_screen": self._ocr_from_screen,
                "from_region": self._ocr_from_region,
                "from_clipboard": self._ocr_from_clipboard,
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
                message=f"OCR failed: {str(e)}",
                error=str(e)
            )

    def _ocr_from_image(self, **kwargs) -> ToolResult:
        """Extract text from an image file."""
        path = kwargs.get("path", "")
        language = kwargs.get("language", "eng")
        
        if not path or not Path(path).exists():
            return ToolResult(
                success=False,
                data={},
                message=f"Image not found: {path}"
            )
        
        try:
            # Try using tesseract
            result = subprocess.run(
                ["tesseract", path, "stdout", "-l", language],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                text = result.stdout.strip()
                return ToolResult(
                    success=True,
                    data={"text": text, "source": path, "char_count": len(text)},
                    message=f"Extracted {len(text)} characters from image"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Tesseract failed: {result.stderr}"
                )
        except FileNotFoundError:
            # Tesseract not installed, try alternative
            return self._ocr_fallback(path)
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"OCR error: {str(e)}",
                error=str(e)
            )

    def _ocr_fallback(self, path: str) -> ToolResult:
        """Fallback OCR using macOS Vision or Windows OCR."""
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                # Use macOS Vision framework via Python
                script = f'''
                import Vision
                import Quartz
                from Foundation import NSURL
                
                url = NSURL.fileURLWithPath_("{path}")
                request = Vision.VNRecognizeTextRequest.alloc().init()
                handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
                handler.performRequests_error_([request], None)
                
                text = ""
                for observation in request.results():
                    text += observation.topCandidates_(1)[0].string() + "\\n"
                print(text)
                '''
                result = subprocess.run(
                    ["python3", "-c", script],
                    capture_output=True, text=True
                )
                if result.stdout:
                    return ToolResult(
                        success=True,
                        data={"text": result.stdout.strip()},
                        message="Text extracted using macOS Vision"
                    )
            
            elif platform == Platform.WINDOWS:
                # Use Windows.Media.Ocr
                ps_script = f'''
                Add-Type -AssemblyName System.Runtime.WindowsRuntime
                $bitmap = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync(
                    [Windows.Storage.Streams.FileRandomAccessStream]::OpenAsync("{path}", 
                    [Windows.Storage.FileAccessMode]::Read).GetAwaiter().GetResult()
                ).GetAwaiter().GetResult()
                $softwareBitmap = $bitmap.GetSoftwareBitmapAsync().GetAwaiter().GetResult()
                $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
                $ocrResult = $ocrEngine.RecognizeAsync($softwareBitmap).GetAwaiter().GetResult()
                Write-Output $ocrResult.Text
                '''
                result = subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True, text=True
                )
                if result.stdout:
                    return ToolResult(
                        success=True,
                        data={"text": result.stdout.strip()},
                        message="Text extracted using Windows OCR"
                    )
            
            return ToolResult(
                success=False,
                data={},
                message="OCR not available. Install tesseract: brew install tesseract (macOS) or apt install tesseract-ocr (Linux)"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"OCR fallback failed: {str(e)}"
            )

    def _ocr_from_screen(self, **kwargs) -> ToolResult:
        """Capture screen and extract text."""
        try:
            # Take screenshot first
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                temp_path = f.name
            
            platform = detect_platform()
            
            if platform == Platform.MACOS:
                subprocess.run(["screencapture", "-x", temp_path], capture_output=True)
            elif platform == Platform.LINUX:
                subprocess.run(["gnome-screenshot", "-f", temp_path], capture_output=True)
            elif platform == Platform.WINDOWS:
                # Use PowerShell to capture screen
                ps_script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen
                $bitmap = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size)
                $bitmap.Save("{temp_path}")
                '''
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            
            # Now OCR the screenshot
            result = self._ocr_from_image(path=temp_path)
            
            # Cleanup
            try:
                os.unlink(temp_path)
            except:
                pass
            
            if result.success:
                result.data["source"] = "screen"
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Screen OCR failed: {str(e)}",
                error=str(e)
            )

    def _ocr_from_region(self, **kwargs) -> ToolResult:
        """Capture a screen region and extract text."""
        x = kwargs.get("x", 0)
        y = kwargs.get("y", 0)
        width = kwargs.get("width", 400)
        height = kwargs.get("height", 200)
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                temp_path = f.name
            
            platform = detect_platform()
            
            if platform == Platform.MACOS:
                subprocess.run(
                    ["screencapture", "-x", "-R", f"{x},{y},{width},{height}", temp_path],
                    capture_output=True
                )
            elif platform == Platform.LINUX:
                subprocess.run(
                    ["gnome-screenshot", "-a", "-f", temp_path],
                    capture_output=True
                )
            
            result = self._ocr_from_image(path=temp_path)
            
            try:
                os.unlink(temp_path)
            except:
                pass
            
            if result.success:
                result.data["source"] = "region"
                result.data["region"] = {"x": x, "y": y, "width": width, "height": height}
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Region OCR failed: {str(e)}",
                error=str(e)
            )

    def _ocr_from_clipboard(self, **kwargs) -> ToolResult:
        """Extract text from an image in clipboard."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                temp_path = f.name
            
            platform = detect_platform()
            
            if platform == Platform.MACOS:
                # Save clipboard image to file
                script = f'''
                set the_file to POSIX file "{temp_path}"
                try
                    set the_data to the clipboard as «class PNGf»
                    set file_ref to open for access the_file with write permission
                    write the_data to file_ref
                    close access file_ref
                    return "success"
                on error
                    return "no image"
                end try
                '''
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True, text=True
                )
                
                if "no image" in result.stdout:
                    return ToolResult(
                        success=False,
                        data={},
                        message="No image in clipboard"
                    )
            
            elif platform == Platform.LINUX:
                subprocess.run(
                    ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
                    stdout=open(temp_path, "wb"),
                    capture_output=False
                )
            
            result = self._ocr_from_image(path=temp_path)
            
            try:
                os.unlink(temp_path)
            except:
                pass
            
            if result.success:
                result.data["source"] = "clipboard"
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Clipboard OCR failed: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Extract text from image: ocr_tool --action from_image --path /path/to/image.png",
            "OCR from screen: ocr_tool --action from_screen",
            "OCR from region: ocr_tool --action from_region --x 100 --y 100 --width 400 --height 200",
            "OCR from clipboard: ocr_tool --action from_clipboard",
        ]
