"""
Smart Search tool for SysAgent CLI - Unified search across files, apps, web, and more.
"""

import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class SmartSearchTool(BaseTool):
    """Tool for intelligent unified search across the system."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="smart_search_tool",
            description="Unified intelligent search across files, apps, web, and system",
            category=ToolCategory.FILE,
            permissions=["file_access", "search"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "search": self._unified_search,
                "files": self._search_files,
                "apps": self._search_apps,
                "web": self._search_web,
                "content": self._search_content,
                "recent": self._search_recent,
                "commands": self._search_commands,
                "history": self._search_history,
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
                message=f"Search failed: {str(e)}",
                error=str(e)
            )

    def _unified_search(self, **kwargs) -> ToolResult:
        """Perform unified search across all sources."""
        query = kwargs.get("query") or kwargs.get("q")
        limit = kwargs.get("limit", 20)
        
        if not query:
            return ToolResult(success=False, data={}, message="Search query required")
        
        results = {
            "files": [],
            "apps": [],
            "commands": [],
            "web_suggestions": []
        }
        
        # Search files
        files_result = self._search_files(query=query, limit=limit//4)
        if files_result.success:
            results["files"] = files_result.data.get("files", [])[:5]
        
        # Search apps
        apps_result = self._search_apps(query=query)
        if apps_result.success:
            results["apps"] = apps_result.data.get("apps", [])[:5]
        
        # Search commands
        commands_result = self._search_commands(query=query)
        if commands_result.success:
            results["commands"] = commands_result.data.get("commands", [])[:5]
        
        # Web search suggestions
        results["web_suggestions"] = [
            f"Search Google for '{query}'",
            f"Search YouTube for '{query}'",
            f"Search GitHub for '{query}'"
        ]
        
        total = len(results["files"]) + len(results["apps"]) + len(results["commands"])
        
        return ToolResult(
            success=True,
            data=results,
            message=f"Found {total} results for '{query}'"
        )

    def _search_files(self, **kwargs) -> ToolResult:
        """Search for files by name or content."""
        query = kwargs.get("query") or kwargs.get("q")
        path = kwargs.get("path", str(Path.home()))
        limit = kwargs.get("limit", 20)
        file_type = kwargs.get("type")  # e.g., "pdf", "txt", "py"
        
        if not query:
            return ToolResult(success=False, data={}, message="Search query required")
        
        platform = detect_platform()
        files = []
        
        try:
            if platform == Platform.MACOS:
                # Use mdfind (Spotlight) for fast search
                cmd = ["mdfind", "-name", query]
                if path != str(Path.home()):
                    cmd.extend(["-onlyin", path])
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                for line in result.stdout.strip().split("\n")[:limit]:
                    if line:
                        p = Path(line)
                        if p.exists():
                            files.append({
                                "name": p.name,
                                "path": str(p),
                                "type": p.suffix or "folder" if p.is_dir() else "file",
                                "size": p.stat().st_size if p.is_file() else 0
                            })
            else:
                # Use find command
                cmd = ["find", path, "-iname", f"*{query}*", "-maxdepth", "5"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                for line in result.stdout.strip().split("\n")[:limit]:
                    if line:
                        p = Path(line)
                        if p.exists():
                            files.append({
                                "name": p.name,
                                "path": str(p),
                                "type": p.suffix or "folder",
                            })
            
            # Filter by type if specified
            if file_type:
                files = [f for f in files if f.get("type", "").endswith(file_type)]
            
            return ToolResult(
                success=True,
                data={"files": files, "count": len(files), "query": query},
                message=f"Found {len(files)} files matching '{query}'"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={},
                message="Search timed out",
                error="Timeout"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"File search failed: {str(e)}",
                error=str(e)
            )

    def _search_apps(self, **kwargs) -> ToolResult:
        """Search for installed applications."""
        query = kwargs.get("query") or kwargs.get("q")
        
        if not query:
            return ToolResult(success=False, data={}, message="Search query required")
        
        platform = detect_platform()
        apps = []
        query_lower = query.lower()
        
        try:
            if platform == Platform.MACOS:
                # Search in Applications folder
                for app_dir in ["/Applications", Path.home() / "Applications"]:
                    if Path(app_dir).exists():
                        for app in Path(app_dir).glob("*.app"):
                            if query_lower in app.stem.lower():
                                apps.append({
                                    "name": app.stem,
                                    "path": str(app),
                                    "type": "application"
                                })
            elif platform == Platform.WINDOWS:
                # Search common locations
                result = subprocess.run(
                    ["powershell", "-Command", 
                     f"Get-StartApps | Where-Object {{ $_.Name -like '*{query}*' }} | Select-Object Name, AppID"],
                    capture_output=True, text=True
                )
                for line in result.stdout.strip().split("\n")[2:]:
                    if line.strip():
                        apps.append({"name": line.strip(), "type": "application"})
            else:
                # Linux - search .desktop files
                desktop_dirs = [
                    "/usr/share/applications",
                    Path.home() / ".local/share/applications"
                ]
                for d in desktop_dirs:
                    if Path(d).exists():
                        for f in Path(d).glob("*.desktop"):
                            if query_lower in f.stem.lower():
                                apps.append({
                                    "name": f.stem,
                                    "path": str(f),
                                    "type": "application"
                                })
            
            return ToolResult(
                success=True,
                data={"apps": apps[:20], "count": len(apps)},
                message=f"Found {len(apps)} apps matching '{query}'"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"App search failed: {str(e)}",
                error=str(e)
            )

    def _search_web(self, **kwargs) -> ToolResult:
        """Generate web search URLs."""
        query = kwargs.get("query") or kwargs.get("q")
        engine = kwargs.get("engine", "google")
        
        if not query:
            return ToolResult(success=False, data={}, message="Search query required")
        
        import urllib.parse
        encoded = urllib.parse.quote(query)
        
        engines = {
            "google": f"https://www.google.com/search?q={encoded}",
            "bing": f"https://www.bing.com/search?q={encoded}",
            "duckduckgo": f"https://duckduckgo.com/?q={encoded}",
            "youtube": f"https://www.youtube.com/results?search_query={encoded}",
            "github": f"https://github.com/search?q={encoded}",
            "stackoverflow": f"https://stackoverflow.com/search?q={encoded}",
            "wikipedia": f"https://en.wikipedia.org/wiki/Special:Search?search={encoded}",
        }
        
        return ToolResult(
            success=True,
            data={
                "query": query,
                "url": engines.get(engine, engines["google"]),
                "all_engines": engines
            },
            message=f"Web search URL for '{query}'"
        )

    def _search_content(self, **kwargs) -> ToolResult:
        """Search file contents using grep/ripgrep."""
        query = kwargs.get("query") or kwargs.get("q")
        path = kwargs.get("path", ".")
        file_type = kwargs.get("type")
        limit = kwargs.get("limit", 20)
        
        if not query:
            return ToolResult(success=False, data={}, message="Search query required")
        
        matches = []
        
        try:
            # Try ripgrep first (faster)
            cmd = ["rg", "-l", "-i", query, path]
            if file_type:
                cmd.extend(["-t", file_type])
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                for line in result.stdout.strip().split("\n")[:limit]:
                    if line:
                        matches.append({"file": line, "type": "content_match"})
            except FileNotFoundError:
                # Fall back to grep
                cmd = ["grep", "-r", "-l", "-i", query, path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                for line in result.stdout.strip().split("\n")[:limit]:
                    if line:
                        matches.append({"file": line, "type": "content_match"})
            
            return ToolResult(
                success=True,
                data={"matches": matches, "count": len(matches)},
                message=f"Found {len(matches)} files containing '{query}'"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Content search failed: {str(e)}",
                error=str(e)
            )

    def _search_recent(self, **kwargs) -> ToolResult:
        """Search recently accessed files."""
        limit = kwargs.get("limit", 20)
        file_type = kwargs.get("type")
        
        platform = detect_platform()
        recent = []
        
        try:
            if platform == Platform.MACOS:
                # Use mdfind for recently modified
                result = subprocess.run(
                    ["mdfind", "-onlyin", str(Path.home()), 
                     "kMDItemFSContentChangeDate >= $time.today(-7)"],
                    capture_output=True, text=True, timeout=10
                )
                
                files = result.stdout.strip().split("\n")[:limit*2]
                for f in files:
                    if f and Path(f).exists():
                        p = Path(f)
                        if file_type and not p.suffix.endswith(file_type):
                            continue
                        recent.append({
                            "name": p.name,
                            "path": str(p),
                            "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                        })
                        if len(recent) >= limit:
                            break
            else:
                # Use find for recently modified
                result = subprocess.run(
                    ["find", str(Path.home()), "-type", "f", "-mtime", "-7", "-maxdepth", "4"],
                    capture_output=True, text=True, timeout=30
                )
                
                for line in result.stdout.strip().split("\n")[:limit]:
                    if line:
                        p = Path(line)
                        if p.exists():
                            recent.append({
                                "name": p.name,
                                "path": str(p)
                            })
            
            return ToolResult(
                success=True,
                data={"files": recent, "count": len(recent)},
                message=f"Found {len(recent)} recently modified files"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Recent search failed: {str(e)}",
                error=str(e)
            )

    def _search_commands(self, **kwargs) -> ToolResult:
        """Search available agent commands."""
        query = kwargs.get("query") or kwargs.get("q", "")
        
        query_lower = query.lower()
        
        # All available commands/actions
        commands = [
            {"name": "Show system status", "command": "system_info --action overview", "category": "system"},
            {"name": "Show CPU usage", "command": "system_info --action cpu", "category": "system"},
            {"name": "Show memory usage", "command": "system_info --action memory", "category": "system"},
            {"name": "Show disk space", "command": "system_info --action disk", "category": "system"},
            {"name": "List processes", "command": "process_tool --action list", "category": "process"},
            {"name": "Kill process", "command": "process_tool --action kill --pid <PID>", "category": "process"},
            {"name": "Open URL", "command": "browser_tool --action open --url <URL>", "category": "browser"},
            {"name": "Search web", "command": "browser_tool --action search --query <QUERY>", "category": "browser"},
            {"name": "Set volume", "command": "media_tool --action volume --level <0-100>", "category": "media"},
            {"name": "Mute audio", "command": "media_tool --action mute", "category": "media"},
            {"name": "Git status", "command": "git_tool --action status", "category": "git"},
            {"name": "Git commit", "command": "git_tool --action commit --message <MSG>", "category": "git"},
            {"name": "Create note", "command": "document_tool --action create_note --content <TEXT>", "category": "docs"},
            {"name": "Create spreadsheet", "command": "spreadsheet_tool --action create_excel", "category": "docs"},
            {"name": "Send notification", "command": "notification_tool --action send --message <MSG>", "category": "notify"},
            {"name": "Install package", "command": "package_manager_tool --action install --package <NAME>", "category": "packages"},
            {"name": "Run workflow", "command": "workflow_tool --action run --name <NAME>", "category": "workflow"},
            {"name": "Tile windows", "command": "window_tool --action tile_left", "category": "window"},
            {"name": "Search files", "command": "smart_search_tool --action files --query <QUERY>", "category": "search"},
        ]
        
        if query:
            matches = [c for c in commands if query_lower in c["name"].lower() or query_lower in c.get("category", "")]
        else:
            matches = commands
        
        return ToolResult(
            success=True,
            data={"commands": matches, "count": len(matches)},
            message=f"Found {len(matches)} commands"
        )

    def _search_history(self, **kwargs) -> ToolResult:
        """Search command/shell history."""
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 20)
        
        history = []
        
        try:
            # Read bash/zsh history
            for hist_file in [".bash_history", ".zsh_history"]:
                hist_path = Path.home() / hist_file
                if hist_path.exists():
                    with open(hist_path, 'r', errors='ignore') as f:
                        lines = f.readlines()[-500:]  # Last 500 lines
                        for line in reversed(lines):
                            line = line.strip()
                            if line and (not query or query.lower() in line.lower()):
                                if line not in [h["command"] for h in history]:
                                    history.append({"command": line})
                                if len(history) >= limit:
                                    break
                    break
            
            return ToolResult(
                success=True,
                data={"history": history, "count": len(history)},
                message=f"Found {len(history)} history entries"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"History search failed: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Unified search: smart_search_tool --action search --query 'python'",
            "Search files: smart_search_tool --action files --query 'report.pdf'",
            "Search apps: smart_search_tool --action apps --query 'chrome'",
            "Search content: smart_search_tool --action content --query 'TODO'",
            "Recent files: smart_search_tool --action recent --limit 10",
        ]
