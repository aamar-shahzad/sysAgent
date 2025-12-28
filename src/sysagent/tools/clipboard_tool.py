"""
Clipboard tool for SysAgent CLI.
"""

import subprocess
import platform
from typing import List, Optional

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class ClipboardTool(BaseTool):
    """Tool for clipboard operations."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="clipboard_tool",
            description="Clipboard read, write, and management operations",
            category=ToolCategory.SYSTEM,
            permissions=["clipboard"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Execute clipboard action."""
        try:
            if action == "copy":
                return self._copy(**kwargs)
            elif action == "paste":
                return self._paste(**kwargs)
            elif action == "clear":
                return self._clear(**kwargs)
            elif action == "history":
                return self._get_history(**kwargs)
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
                message=f"Clipboard operation failed: {str(e)}",
                error=str(e)
            )

    def _copy(self, **kwargs) -> ToolResult:
        """Copy text to clipboard."""
        text = kwargs.get("text") or kwargs.get("content")
        
        if text is None:
            return ToolResult(
                success=False,
                data={},
                message="No text provided to copy",
                error="Missing text"
            )
        
        try:
            current_platform = detect_platform()
            
            if current_platform == Platform.MACOS:
                process = subprocess.Popen(
                    ["pbcopy"],
                    stdin=subprocess.PIPE,
                    close_fds=True
                )
                process.communicate(text.encode('utf-8'))
                
            elif current_platform == Platform.LINUX:
                # Try xclip first, then xsel
                try:
                    process = subprocess.Popen(
                        ["xclip", "-selection", "clipboard"],
                        stdin=subprocess.PIPE,
                        close_fds=True
                    )
                    process.communicate(text.encode('utf-8'))
                except FileNotFoundError:
                    try:
                        process = subprocess.Popen(
                            ["xsel", "--clipboard", "--input"],
                            stdin=subprocess.PIPE,
                            close_fds=True
                        )
                        process.communicate(text.encode('utf-8'))
                    except FileNotFoundError:
                        # Try wl-copy for Wayland
                        process = subprocess.Popen(
                            ["wl-copy"],
                            stdin=subprocess.PIPE,
                            close_fds=True
                        )
                        process.communicate(text.encode('utf-8'))
                        
            elif current_platform == Platform.WINDOWS:
                # Use PowerShell
                subprocess.run(
                    ["powershell", "-Command", f"Set-Clipboard -Value '{text}'"],
                    capture_output=True
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Clipboard not supported on this platform",
                    error="Unsupported platform"
                )
            
            return ToolResult(
                success=True,
                data={"text_length": len(text)},
                message=f"Copied {len(text)} characters to clipboard"
            )
            
        except FileNotFoundError:
            return ToolResult(
                success=False,
                data={},
                message="No clipboard utility found (install xclip, xsel, or wl-clipboard)",
                error="Missing clipboard utility"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to copy to clipboard: {str(e)}",
                error=str(e)
            )

    def _paste(self, **kwargs) -> ToolResult:
        """Get text from clipboard."""
        try:
            current_platform = detect_platform()
            content = None
            
            if current_platform == Platform.MACOS:
                result = subprocess.run(
                    ["pbpaste"],
                    capture_output=True,
                    text=True
                )
                content = result.stdout
                
            elif current_platform == Platform.LINUX:
                # Try xclip first, then xsel
                try:
                    result = subprocess.run(
                        ["xclip", "-selection", "clipboard", "-o"],
                        capture_output=True,
                        text=True
                    )
                    content = result.stdout
                except FileNotFoundError:
                    try:
                        result = subprocess.run(
                            ["xsel", "--clipboard", "--output"],
                            capture_output=True,
                            text=True
                        )
                        content = result.stdout
                    except FileNotFoundError:
                        # Try wl-paste for Wayland
                        result = subprocess.run(
                            ["wl-paste"],
                            capture_output=True,
                            text=True
                        )
                        content = result.stdout
                        
            elif current_platform == Platform.WINDOWS:
                result = subprocess.run(
                    ["powershell", "-Command", "Get-Clipboard"],
                    capture_output=True,
                    text=True
                )
                content = result.stdout.strip()
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Clipboard not supported on this platform",
                    error="Unsupported platform"
                )
            
            return ToolResult(
                success=True,
                data={"content": content, "length": len(content) if content else 0},
                message=f"Retrieved {len(content) if content else 0} characters from clipboard"
            )
            
        except FileNotFoundError:
            return ToolResult(
                success=False,
                data={},
                message="No clipboard utility found (install xclip, xsel, or wl-clipboard)",
                error="Missing clipboard utility"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to paste from clipboard: {str(e)}",
                error=str(e)
            )

    def _clear(self, **kwargs) -> ToolResult:
        """Clear the clipboard."""
        try:
            # Copy empty string to clear
            return self._copy(text="")
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to clear clipboard: {str(e)}",
                error=str(e)
            )

    def _get_history(self, **kwargs) -> ToolResult:
        """Get clipboard history (if supported)."""
        # Most systems don't have native clipboard history
        return ToolResult(
            success=False,
            data={},
            message="Clipboard history requires a clipboard manager (e.g., CopyQ, Parcellite)",
            error="Not implemented"
        )

    def get_usage_examples(self) -> List[str]:
        """Get usage examples for this tool."""
        return [
            "Copy text: clipboard_tool --action copy --text 'Hello World'",
            "Paste: clipboard_tool --action paste",
            "Clear clipboard: clipboard_tool --action clear",
        ]
