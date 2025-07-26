"""
File system operations tool for SysAgent CLI.
"""

import os
import shutil
import glob
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseTool, register_tool, ToolMetadata
from ..types import ToolResult, ToolCategory


@register_tool
class FileTool(BaseTool):
    """Tool for file system operations."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="file_tool",
            description="File system operations including read, write, move, delete, and cleanup",
            category=ToolCategory.FILE,
            permissions=["file_system"],
            version="1.0.0"
        )
    
    def _execute(self, **kwargs) -> ToolResult:
        """Execute file operations based on action parameter."""
        action = kwargs.get("action", "list")
        
        if action == "list":
            return self._list_files(**kwargs)
        elif action == "read":
            return self._read_file(**kwargs)
        elif action == "write":
            return self._write_file(**kwargs)
        elif action == "move":
            return self._move_file(**kwargs)
        elif action == "delete":
            return self._delete_file(**kwargs)
        elif action == "copy":
            return self._copy_file(**kwargs)
        elif action == "cleanup":
            return self._cleanup_files(**kwargs)
        elif action == "organize":
            return self._organize_files(**kwargs)
        elif action == "search":
            return self._search_files(**kwargs)
        elif action == "info":
            return self._get_file_info(**kwargs)
        else:
            return ToolResult(
                success=False,
                data={},
                message=f"Unknown action: {action}",
                error=f"Unsupported action: {action}"
            )
    
    def _list_files(self, **kwargs) -> ToolResult:
        """List files in a directory."""
        path = kwargs.get("path", ".")
        pattern = kwargs.get("pattern", "*")
        recursive = kwargs.get("recursive", False)
        show_hidden = kwargs.get("show_hidden", False)
        
        try:
            target_path = Path(path).resolve()
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Path does not exist: {path}",
                    error=f"Path not found: {path}"
                )
            
            if not target_path.is_dir():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Path is not a directory: {path}",
                    error=f"Not a directory: {path}"
                )
            
            # Build search pattern
            search_pattern = str(target_path / pattern)
            if recursive:
                search_pattern = str(target_path / "**" / pattern)
            
            files = []
            for file_path in glob.glob(search_pattern, recursive=recursive):
                file_obj = Path(file_path)
                
                # Skip hidden files unless requested
                if not show_hidden and file_obj.name.startswith("."):
                    continue
                
                try:
                    stat = file_obj.stat()
                    files.append({
                        "name": file_obj.name,
                        "path": str(file_obj),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "is_dir": file_obj.is_dir(),
                        "is_file": file_obj.is_file(),
                        "is_symlink": file_obj.is_symlink(),
                    })
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
            
            return ToolResult(
                success=True,
                data={
                    "files": files,
                    "count": len(files),
                    "path": str(target_path),
                    "pattern": pattern,
                    "recursive": recursive
                },
                message=f"Found {len(files)} files in {path}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list files in {path}",
                error=str(e)
            )
    
    def _read_file(self, **kwargs) -> ToolResult:
        """Read file content."""
        path = kwargs.get("path")
        encoding = kwargs.get("encoding", "utf-8")
        max_size = kwargs.get("max_size", 1024 * 1024)  # 1MB default
        
        if not path:
            return ToolResult(
                success=False,
                data={},
                message="No file path provided",
                error="Missing path parameter"
            )
        
        try:
            file_path = Path(path).resolve()
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"File does not exist: {path}",
                    error=f"File not found: {path}"
                )
            
            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Path is not a file: {path}",
                    error=f"Not a file: {path}"
                )
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > max_size:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"File too large ({file_size} bytes), max allowed: {max_size}",
                    error=f"File size exceeds limit: {file_size} > {max_size}"
                )
            
            # Read file content
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                data={
                    "content": content,
                    "size": file_size,
                    "encoding": encoding,
                    "path": str(file_path)
                },
                message=f"Successfully read file: {path}"
            )
            
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to decode file with encoding {encoding}",
                error=f"Encoding error: {encoding}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to read file: {path}",
                error=str(e)
            )
    
    def _write_file(self, **kwargs) -> ToolResult:
        """Write content to a file."""
        path = kwargs.get("path")
        content = kwargs.get("content", "")
        mode = kwargs.get("mode", "w")  # w, a, x
        encoding = kwargs.get("encoding", "utf-8")
        
        if not path:
            return ToolResult(
                success=False,
                data={},
                message="No file path provided",
                error="Missing path parameter"
            )
        
        try:
            file_path = Path(path).resolve()
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists for exclusive write mode
            if mode == "x" and file_path.exists():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"File already exists: {path}",
                    error=f"File exists: {path}"
                )
            
            # Write file content
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                data={
                    "path": str(file_path),
                    "size": len(content),
                    "mode": mode,
                    "encoding": encoding
                },
                message=f"Successfully wrote file: {path}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to write file: {path}",
                error=str(e)
            )
    
    def _move_file(self, **kwargs) -> ToolResult:
        """Move a file or directory."""
        source = kwargs.get("source")
        destination = kwargs.get("destination")
        
        if not source or not destination:
            return ToolResult(
                success=False,
                data={},
                message="Source and destination paths are required",
                error="Missing source or destination parameter"
            )
        
        try:
            source_path = Path(source).resolve()
            dest_path = Path(destination).resolve()
            
            if not source_path.exists():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Source does not exist: {source}",
                    error=f"Source not found: {source}"
                )
            
            # Create destination directory if it doesn't exist
            if dest_path.suffix == "" and not dest_path.exists():
                dest_path.mkdir(parents=True, exist_ok=True)
            
            # Move the file/directory
            shutil.move(str(source_path), str(dest_path))
            
            return ToolResult(
                success=True,
                data={
                    "source": str(source_path),
                    "destination": str(dest_path)
                },
                message=f"Successfully moved {source} to {destination}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to move {source} to {destination}",
                error=str(e)
            )
    
    def _copy_file(self, **kwargs) -> ToolResult:
        """Copy a file or directory."""
        source = kwargs.get("source")
        destination = kwargs.get("destination")
        
        if not source or not destination:
            return ToolResult(
                success=False,
                data={},
                message="Source and destination paths are required",
                error="Missing source or destination parameter"
            )
        
        try:
            source_path = Path(source).resolve()
            dest_path = Path(destination).resolve()
            
            if not source_path.exists():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Source does not exist: {source}",
                    error=f"Source not found: {source}"
                )
            
            # Copy the file/directory
            if source_path.is_dir():
                shutil.copytree(str(source_path), str(dest_path), dirs_exist_ok=True)
            else:
                shutil.copy2(str(source_path), str(dest_path))
            
            return ToolResult(
                success=True,
                data={
                    "source": str(source_path),
                    "destination": str(dest_path)
                },
                message=f"Successfully copied {source} to {destination}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to copy {source} to {destination}",
                error=str(e)
            )
    
    def _delete_file(self, **kwargs) -> ToolResult:
        """Delete a file or directory."""
        path = kwargs.get("path")
        recursive = kwargs.get("recursive", False)
        
        if not path:
            return ToolResult(
                success=False,
                data={},
                message="No file path provided",
                error="Missing path parameter"
            )
        
        try:
            file_path = Path(path).resolve()
            
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Path does not exist: {path}",
                    error=f"Path not found: {path}"
                )
            
            # Check if it's a directory and recursive is required
            if file_path.is_dir() and not recursive:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Directory requires recursive=True: {path}",
                    error="Directory deletion requires recursive flag"
                )
            
            # Delete the file/directory
            if file_path.is_dir():
                shutil.rmtree(str(file_path))
            else:
                file_path.unlink()
            
            return ToolResult(
                success=True,
                data={
                    "path": str(file_path),
                    "was_directory": file_path.is_dir()
                },
                message=f"Successfully deleted: {path}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to delete: {path}",
                error=str(e)
            )
    
    def _cleanup_files(self, **kwargs) -> ToolResult:
        """Clean up temporary files and directories."""
        paths = kwargs.get("paths", [])
        patterns = kwargs.get("patterns", ["*.tmp", "*.temp", "*.log", "*.cache"])
        max_age_days = kwargs.get("max_age_days", 7)
        
        if not paths:
            # Default cleanup paths
            from ..utils.platform import get_temp_directory, get_home_directory
            paths = [
                str(get_temp_directory()),
                str(get_home_directory() / ".cache"),
                str(get_home_directory() / "Downloads")
            ]
        
        cleaned_files = []
        total_size = 0
        
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            
            for path_str in paths:
                path = Path(path_str)
                if not path.exists():
                    continue
                
                for pattern in patterns:
                    for file_path in path.glob(pattern):
                        try:
                            if file_path.is_file():
                                stat = file_path.stat()
                                if stat.st_mtime < cutoff_time:
                                    file_size = stat.st_size
                                    file_path.unlink()
                                    cleaned_files.append({
                                        "path": str(file_path),
                                        "size": file_size,
                                        "age_days": (datetime.now().timestamp() - stat.st_mtime) / (24 * 60 * 60)
                                    })
                                    total_size += file_size
                        except (OSError, PermissionError):
                            continue
            
            return ToolResult(
                success=True,
                data={
                    "cleaned_files": cleaned_files,
                    "total_files": len(cleaned_files),
                    "total_size": total_size,
                    "paths_checked": paths,
                    "patterns": patterns,
                    "max_age_days": max_age_days
                },
                message=f"Cleaned up {len(cleaned_files)} files ({total_size} bytes)"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message="Failed to cleanup files",
                error=str(e)
            )
    
    def _organize_files(self, **kwargs) -> ToolResult:
        """Organize files by type into directories."""
        source_dir = kwargs.get("source_dir", ".")
        extensions_map = kwargs.get("extensions_map", {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
            "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf"],
            "videos": [".mp4", ".avi", ".mov", ".mkv", ".wmv"],
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
            "archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c"]
        })
        
        try:
            source_path = Path(source_dir).resolve()
            if not source_path.exists() or not source_path.is_dir():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Source directory does not exist: {source_dir}",
                    error=f"Invalid source directory: {source_dir}"
                )
            
            organized_files = {}
            total_moved = 0
            
            for file_path in source_path.iterdir():
                if file_path.is_file():
                    extension = file_path.suffix.lower()
                    
                    # Find the category for this extension
                    category = None
                    for cat, exts in extensions_map.items():
                        if extension in exts:
                            category = cat
                            break
                    
                    if category:
                        # Create category directory
                        category_dir = source_path / category
                        category_dir.mkdir(exist_ok=True)
                        
                        # Move file to category directory
                        dest_path = category_dir / file_path.name
                        if not dest_path.exists():
                            shutil.move(str(file_path), str(dest_path))
                            total_moved += 1
                            
                            if category not in organized_files:
                                organized_files[category] = []
                            organized_files[category].append(str(dest_path))
            
            return ToolResult(
                success=True,
                data={
                    "organized_files": organized_files,
                    "total_moved": total_moved,
                    "source_directory": str(source_path),
                    "categories": list(organized_files.keys())
                },
                message=f"Organized {total_moved} files into {len(organized_files)} categories"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to organize files in {source_dir}",
                error=str(e)
            )
    
    def _search_files(self, **kwargs) -> ToolResult:
        """Search for files by name, content, or pattern."""
        path = kwargs.get("path", ".")
        pattern = kwargs.get("pattern", "*")
        name_contains = kwargs.get("name_contains")
        content_contains = kwargs.get("content_contains")
        recursive = kwargs.get("recursive", True)
        max_results = kwargs.get("max_results", 100)
        
        try:
            search_path = Path(path).resolve()
            if not search_path.exists():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Search path does not exist: {path}",
                    error=f"Path not found: {path}"
                )
            
            found_files = []
            
            # Build search pattern
            search_pattern = str(search_path / pattern)
            if recursive:
                search_pattern = str(search_path / "**" / pattern)
            
            for file_path in glob.glob(search_pattern, recursive=recursive):
                file_obj = Path(file_path)
                
                if not file_obj.is_file():
                    continue
                
                # Filter by name if specified
                if name_contains and name_contains.lower() not in file_obj.name.lower():
                    continue
                
                # Filter by content if specified
                if content_contains:
                    try:
                        with open(file_obj, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if content_contains.lower() not in content.lower():
                                continue
                    except (OSError, UnicodeDecodeError):
                        continue
                
                found_files.append({
                    "name": file_obj.name,
                    "path": str(file_obj),
                    "size": file_obj.stat().st_size,
                    "modified": datetime.fromtimestamp(file_obj.stat().st_mtime).isoformat()
                })
                
                if len(found_files) >= max_results:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "files": found_files,
                    "count": len(found_files),
                    "search_path": str(search_path),
                    "pattern": pattern,
                    "name_filter": name_contains,
                    "content_filter": content_contains
                },
                message=f"Found {len(found_files)} files matching criteria"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to search files in {path}",
                error=str(e)
            )
    
    def _get_file_info(self, **kwargs) -> ToolResult:
        """Get detailed information about a file."""
        path = kwargs.get("path")
        
        if not path:
            return ToolResult(
                success=False,
                data={},
                message="No file path provided",
                error="Missing path parameter"
            )
        
        try:
            file_path = Path(path).resolve()
            
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    data={},
                    message=f"File does not exist: {path}",
                    error=f"File not found: {path}"
                )
            
            stat = file_path.stat()
            
            info = {
                "name": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir(),
                "is_symlink": file_path.is_symlink(),
                "extension": file_path.suffix,
                "parent": str(file_path.parent),
                "absolute": str(file_path.absolute()),
            }
            
            # Add file type information
            if file_path.is_file():
                import mimetypes
                mime_type, _ = mimetypes.guess_type(str(file_path))
                info["mime_type"] = mime_type or "unknown"
                
                # Try to get file encoding
                try:
                    with open(file_path, 'rb') as f:
                        raw = f.read(1024)
                        import chardet
                        result = chardet.detect(raw)
                        info["encoding"] = result['encoding']
                except Exception:
                    info["encoding"] = "unknown"
            
            return ToolResult(
                success=True,
                data=info,
                message=f"File information for: {path}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get file info for: {path}",
                error=str(e)
            )
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def get_usage_examples(self) -> List[str]:
        """Get usage examples for this tool."""
        return [
            "List files in current directory: file_tool --action list --path .",
            "Read a file: file_tool --action read --path /path/to/file.txt",
            "Write to a file: file_tool --action write --path /path/to/file.txt --content 'Hello World'",
            "Move a file: file_tool --action move --source /old/path --destination /new/path",
            "Delete a file: file_tool --action delete --path /path/to/file.txt",
            "Clean up temp files: file_tool --action cleanup --paths ['/tmp', '/var/tmp']",
            "Organize downloads: file_tool --action organize --source_dir ~/Downloads",
            "Search for files: file_tool --action search --path . --name_contains 'test'",
            "Get file info: file_tool --action info --path /path/to/file.txt"
        ] 