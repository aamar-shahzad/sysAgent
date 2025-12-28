"""
Browser tool for SysAgent CLI - Web browser control and automation.
"""

import os
import subprocess
import json
import webbrowser
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class BrowserTool(BaseTool):
    """Tool for controlling web browsers and web automation."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="browser_tool",
            description="Control web browsers - open URLs, manage tabs, bookmarks",
            category=ToolCategory.SYSTEM,
            permissions=["browser_control", "network_access"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "open": self._open_url,
                "open_url": self._open_url,
                "search": self._search,
                "open_app": self._open_browser_app,
                "close": self._close_browser,
                "get_bookmarks": self._get_bookmarks,
                "add_bookmark": self._add_bookmark,
                "get_history": self._get_history,
                "get_downloads": self._get_downloads,
                "open_incognito": self._open_incognito,
                "open_new_window": self._open_new_window,
                "list_browsers": self._list_browsers,
            }
            
            if action in actions:
                return actions[action](**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={"available_actions": list(actions.keys())},
                    message=f"Unknown action: {action}",
                    error=f"Supported actions: {list(actions.keys())}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Browser operation failed: {str(e)}",
                error=str(e)
            )

    def _get_default_browser(self) -> str:
        """Get the default browser name."""
        platform = detect_platform()
        
        if platform == Platform.MACOS:
            try:
                result = subprocess.run(
                    ["defaults", "read", "com.apple.LaunchServices/com.apple.launchservices.secure", "LSHandlers"],
                    capture_output=True, text=True
                )
                if "chrome" in result.stdout.lower():
                    return "chrome"
                elif "firefox" in result.stdout.lower():
                    return "firefox"
                elif "safari" in result.stdout.lower():
                    return "safari"
            except:
                pass
            return "safari"
        elif platform == Platform.WINDOWS:
            return "edge"
        else:
            return "firefox"

    def _open_url(self, **kwargs) -> ToolResult:
        """Open a URL in the default browser."""
        url = kwargs.get("url")
        browser = kwargs.get("browser")
        new_tab = kwargs.get("new_tab", True)
        
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="No URL provided",
                error="Missing url parameter"
            )
        
        # Add protocol if missing
        if not url.startswith(("http://", "https://", "file://")):
            url = "https://" + url
        
        try:
            if browser:
                # Open with specific browser
                platform = detect_platform()
                if platform == Platform.MACOS:
                    browser_apps = {
                        "chrome": "Google Chrome",
                        "firefox": "Firefox",
                        "safari": "Safari",
                        "edge": "Microsoft Edge",
                        "brave": "Brave Browser",
                        "arc": "Arc"
                    }
                    app_name = browser_apps.get(browser.lower(), browser)
                    subprocess.Popen(["open", "-a", app_name, url])
                elif platform == Platform.WINDOWS:
                    browser_paths = {
                        "chrome": "chrome",
                        "firefox": "firefox",
                        "edge": "msedge",
                        "brave": "brave"
                    }
                    browser_cmd = browser_paths.get(browser.lower(), browser)
                    subprocess.Popen([browser_cmd, url])
                else:
                    subprocess.Popen([browser, url])
            else:
                # Use default browser
                webbrowser.open(url, new=2 if new_tab else 1)
            
            return ToolResult(
                success=True,
                data={"url": url, "browser": browser or "default"},
                message=f"Opened: {url}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to open URL: {str(e)}",
                error=str(e)
            )

    def _search(self, **kwargs) -> ToolResult:
        """Search the web using a search engine."""
        query = kwargs.get("query") or kwargs.get("q")
        engine = kwargs.get("engine", "google")
        
        if not query:
            return ToolResult(
                success=False,
                data={},
                message="No search query provided",
                error="Missing query"
            )
        
        search_urls = {
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
            "duckduckgo": "https://duckduckgo.com/?q=",
            "youtube": "https://www.youtube.com/results?search_query=",
            "github": "https://github.com/search?q=",
            "stackoverflow": "https://stackoverflow.com/search?q=",
        }
        
        base_url = search_urls.get(engine.lower(), search_urls["google"])
        
        import urllib.parse
        search_url = base_url + urllib.parse.quote(query)
        
        return self._open_url(url=search_url)

    def _open_browser_app(self, **kwargs) -> ToolResult:
        """Open a browser application."""
        browser = kwargs.get("browser") or kwargs.get("name", "default")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                browser_apps = {
                    "chrome": "Google Chrome",
                    "firefox": "Firefox",
                    "safari": "Safari",
                    "edge": "Microsoft Edge",
                    "brave": "Brave Browser",
                    "arc": "Arc",
                    "default": "Safari"
                }
                app_name = browser_apps.get(browser.lower(), browser)
                subprocess.Popen(["open", "-a", app_name])
            elif platform == Platform.WINDOWS:
                browser_cmds = {
                    "chrome": "chrome",
                    "firefox": "firefox",
                    "edge": "msedge",
                    "brave": "brave",
                    "default": "msedge"
                }
                cmd = browser_cmds.get(browser.lower(), browser)
                subprocess.Popen([cmd])
            else:
                browser_cmds = {
                    "chrome": "google-chrome",
                    "firefox": "firefox",
                    "chromium": "chromium-browser",
                    "default": "xdg-open"
                }
                cmd = browser_cmds.get(browser.lower(), browser)
                if cmd == "xdg-open":
                    subprocess.Popen([cmd, "https://"])
                else:
                    subprocess.Popen([cmd])
            
            return ToolResult(
                success=True,
                data={"browser": browser},
                message=f"Opened browser: {browser}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to open browser: {str(e)}",
                error=str(e)
            )

    def _close_browser(self, **kwargs) -> ToolResult:
        """Close a browser application."""
        browser = kwargs.get("browser", "all")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                if browser == "all":
                    for b in ["Google Chrome", "Firefox", "Safari", "Microsoft Edge"]:
                        subprocess.run(["osascript", "-e", f'quit app "{b}"'], capture_output=True)
                else:
                    browser_apps = {
                        "chrome": "Google Chrome",
                        "firefox": "Firefox",
                        "safari": "Safari",
                        "edge": "Microsoft Edge"
                    }
                    app_name = browser_apps.get(browser.lower(), browser)
                    subprocess.run(["osascript", "-e", f'quit app "{app_name}"'], capture_output=True)
            elif platform == Platform.WINDOWS:
                if browser == "all":
                    for proc in ["chrome.exe", "firefox.exe", "msedge.exe"]:
                        subprocess.run(["taskkill", "/F", "/IM", proc], capture_output=True)
                else:
                    proc_map = {"chrome": "chrome.exe", "firefox": "firefox.exe", "edge": "msedge.exe"}
                    proc = proc_map.get(browser.lower(), f"{browser}.exe")
                    subprocess.run(["taskkill", "/F", "/IM", proc], capture_output=True)
            else:
                if browser == "all":
                    subprocess.run(["pkill", "-f", "chrome|firefox|chromium"], capture_output=True)
                else:
                    subprocess.run(["pkill", "-f", browser], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"browser": browser},
                message=f"Closed browser: {browser}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to close browser: {str(e)}",
                error=str(e)
            )

    def _open_incognito(self, **kwargs) -> ToolResult:
        """Open browser in incognito/private mode."""
        url = kwargs.get("url", "")
        browser = kwargs.get("browser", "chrome")
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                if browser.lower() == "chrome":
                    cmd = ["open", "-a", "Google Chrome", "--args", "--incognito"]
                    if url:
                        cmd.append(url)
                elif browser.lower() == "firefox":
                    cmd = ["open", "-a", "Firefox", "--args", "-private-window"]
                    if url:
                        cmd.append(url)
                elif browser.lower() == "safari":
                    # Safari private window via AppleScript
                    script = 'tell application "Safari" to make new document with properties {URL:"' + (url or "about:blank") + '"}'
                    subprocess.Popen(["osascript", "-e", script])
                    return ToolResult(success=True, data={"browser": browser, "url": url}, message="Opened Safari private window")
                else:
                    cmd = ["open", "-a", browser]
                subprocess.Popen(cmd)
            elif platform == Platform.WINDOWS:
                if browser.lower() == "chrome":
                    cmd = ["chrome", "--incognito"] + ([url] if url else [])
                elif browser.lower() == "edge":
                    cmd = ["msedge", "--inprivate"] + ([url] if url else [])
                elif browser.lower() == "firefox":
                    cmd = ["firefox", "-private-window"] + ([url] if url else [])
                else:
                    cmd = [browser]
                subprocess.Popen(cmd)
            else:
                if browser.lower() in ["chrome", "chromium"]:
                    cmd = ["google-chrome", "--incognito"] + ([url] if url else [])
                else:
                    cmd = ["firefox", "-private-window"] + ([url] if url else [])
                subprocess.Popen(cmd)
            
            return ToolResult(
                success=True,
                data={"browser": browser, "url": url, "mode": "incognito"},
                message=f"Opened {browser} in incognito mode"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to open incognito: {str(e)}",
                error=str(e)
            )

    def _open_new_window(self, **kwargs) -> ToolResult:
        """Open a new browser window."""
        url = kwargs.get("url", "")
        browser = kwargs.get("browser", "default")
        
        try:
            webbrowser.open(url or "about:blank", new=1)
            return ToolResult(
                success=True,
                data={"url": url},
                message=f"Opened new window" + (f" with {url}" if url else "")
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to open new window: {str(e)}",
                error=str(e)
            )

    def _get_bookmarks(self, **kwargs) -> ToolResult:
        """Get browser bookmarks."""
        browser = kwargs.get("browser", "chrome")
        limit = kwargs.get("limit", 50)
        
        platform = detect_platform()
        bookmarks = []
        
        try:
            if browser.lower() == "chrome":
                if platform == Platform.MACOS:
                    bookmarks_path = Path.home() / "Library/Application Support/Google/Chrome/Default/Bookmarks"
                elif platform == Platform.WINDOWS:
                    bookmarks_path = Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Bookmarks"
                else:
                    bookmarks_path = Path.home() / ".config/google-chrome/Default/Bookmarks"
                
                if bookmarks_path.exists():
                    with open(bookmarks_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    def extract_bookmarks(node, bookmarks_list):
                        if isinstance(node, dict):
                            if node.get("type") == "url":
                                bookmarks_list.append({
                                    "name": node.get("name", ""),
                                    "url": node.get("url", "")
                                })
                            for key in ["children", "bookmark_bar", "other", "synced"]:
                                if key in node:
                                    extract_bookmarks(node[key], bookmarks_list)
                        elif isinstance(node, list):
                            for item in node:
                                extract_bookmarks(item, bookmarks_list)
                    
                    extract_bookmarks(data.get("roots", {}), bookmarks)
            
            return ToolResult(
                success=True,
                data={"bookmarks": bookmarks[:limit], "count": len(bookmarks)},
                message=f"Found {len(bookmarks)} bookmarks"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get bookmarks: {str(e)}",
                error=str(e)
            )

    def _add_bookmark(self, **kwargs) -> ToolResult:
        """Add a bookmark (saves to a local file for now)."""
        url = kwargs.get("url")
        name = kwargs.get("name", "")
        
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="No URL provided",
                error="Missing url"
            )
        
        try:
            bookmarks_dir = Path.home() / ".sysagent" / "bookmarks"
            bookmarks_dir.mkdir(parents=True, exist_ok=True)
            bookmarks_file = bookmarks_dir / "bookmarks.json"
            
            bookmarks = []
            if bookmarks_file.exists():
                with open(bookmarks_file, 'r') as f:
                    bookmarks = json.load(f)
            
            bookmarks.append({
                "name": name or url,
                "url": url,
                "added": datetime.now().isoformat()
            })
            
            with open(bookmarks_file, 'w') as f:
                json.dump(bookmarks, f, indent=2)
            
            return ToolResult(
                success=True,
                data={"name": name, "url": url},
                message=f"Bookmark added: {name or url}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to add bookmark: {str(e)}",
                error=str(e)
            )

    def _get_history(self, **kwargs) -> ToolResult:
        """Get browser history (limited access)."""
        browser = kwargs.get("browser", "chrome")
        limit = kwargs.get("limit", 20)
        
        return ToolResult(
            success=True,
            data={"message": "Browser history access requires browser extension or elevated permissions"},
            message="History access limited - use browser directly for full history"
        )

    def _get_downloads(self, **kwargs) -> ToolResult:
        """Get downloads folder contents."""
        platform = detect_platform()
        
        try:
            downloads_path = Path.home() / "Downloads"
            
            files = []
            for f in sorted(downloads_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                if f.is_file():
                    files.append({
                        "name": f.name,
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                    })
            
            return ToolResult(
                success=True,
                data={"downloads": files, "path": str(downloads_path)},
                message=f"Found {len(files)} recent downloads"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get downloads: {str(e)}",
                error=str(e)
            )

    def _list_browsers(self, **kwargs) -> ToolResult:
        """List installed browsers."""
        platform = detect_platform()
        browsers = []
        
        try:
            if platform == Platform.MACOS:
                browser_paths = [
                    ("/Applications/Google Chrome.app", "Chrome"),
                    ("/Applications/Firefox.app", "Firefox"),
                    ("/Applications/Safari.app", "Safari"),
                    ("/Applications/Microsoft Edge.app", "Edge"),
                    ("/Applications/Brave Browser.app", "Brave"),
                    ("/Applications/Arc.app", "Arc"),
                ]
                for path, name in browser_paths:
                    if Path(path).exists():
                        browsers.append({"name": name, "path": path})
            elif platform == Platform.WINDOWS:
                # Check common browser locations
                browser_checks = [
                    ("chrome", "Chrome"),
                    ("firefox", "Firefox"),
                    ("msedge", "Edge"),
                ]
                for cmd, name in browser_checks:
                    try:
                        subprocess.run(["where", cmd], capture_output=True, check=True)
                        browsers.append({"name": name, "command": cmd})
                    except:
                        pass
            else:
                browser_cmds = [
                    ("google-chrome", "Chrome"),
                    ("firefox", "Firefox"),
                    ("chromium-browser", "Chromium"),
                ]
                for cmd, name in browser_cmds:
                    try:
                        subprocess.run(["which", cmd], capture_output=True, check=True)
                        browsers.append({"name": name, "command": cmd})
                    except:
                        pass
            
            return ToolResult(
                success=True,
                data={"browsers": browsers, "count": len(browsers)},
                message=f"Found {len(browsers)} browsers"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list browsers: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Open URL: browser_tool --action open --url 'https://google.com'",
            "Search web: browser_tool --action search --query 'python tutorial'",
            "Open incognito: browser_tool --action open_incognito --browser chrome",
            "List browsers: browser_tool --action list_browsers",
            "Get bookmarks: browser_tool --action get_bookmarks --browser chrome",
        ]
