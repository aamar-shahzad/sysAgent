"""
API tool for SysAgent CLI - HTTP requests and API calls.
"""

import json
from typing import List, Dict, Any
from pathlib import Path

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory


@register_tool
class APITool(BaseTool):
    """Tool for making HTTP requests and API calls."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="api_tool",
            description="Make HTTP requests - GET, POST, PUT, DELETE",
            category=ToolCategory.NETWORK,
            permissions=["network_access"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "get": self._get,
                "post": self._post,
                "put": self._put,
                "delete": self._delete,
                "request": self._request,
                "download": self._download,
                "head": self._head,
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
                message=f"API request failed: {str(e)}",
                error=str(e)
            )

    def _make_request(self, method: str, url: str, **kwargs) -> ToolResult:
        """Make an HTTP request."""
        headers = kwargs.get("headers", {})
        data = kwargs.get("data")
        json_data = kwargs.get("json")
        params = kwargs.get("params", {})
        timeout = kwargs.get("timeout", 30)
        auth = kwargs.get("auth")
        
        try:
            import requests
        except ImportError:
            return ToolResult(
                success=False,
                data={},
                message="requests library not installed",
                error="pip install requests"
            )
        
        try:
            # Add common headers
            if "User-Agent" not in headers:
                headers["User-Agent"] = "SysAgent/1.0"
            
            # Prepare request arguments
            req_kwargs = {
                "headers": headers,
                "timeout": timeout,
                "params": params,
            }
            
            if data:
                req_kwargs["data"] = data
            if json_data:
                req_kwargs["json"] = json_data
            if auth:
                if isinstance(auth, dict):
                    req_kwargs["auth"] = (auth.get("username", ""), auth.get("password", ""))
                elif isinstance(auth, (list, tuple)):
                    req_kwargs["auth"] = tuple(auth)
            
            response = requests.request(method.upper(), url, **req_kwargs)
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except:
                response_data = response.text[:2000]
            
            return ToolResult(
                success=response.status_code < 400,
                data={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_data,
                    "url": response.url
                },
                message=f"{method.upper()} {url} - {response.status_code}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Request failed: {str(e)}",
                error=str(e)
            )

    def _get(self, **kwargs) -> ToolResult:
        """Make a GET request."""
        url = kwargs.get("url")
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="URL required"
            )
        return self._make_request("GET", url, **kwargs)

    def _post(self, **kwargs) -> ToolResult:
        """Make a POST request."""
        url = kwargs.get("url")
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="URL required"
            )
        return self._make_request("POST", url, **kwargs)

    def _put(self, **kwargs) -> ToolResult:
        """Make a PUT request."""
        url = kwargs.get("url")
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="URL required"
            )
        return self._make_request("PUT", url, **kwargs)

    def _delete(self, **kwargs) -> ToolResult:
        """Make a DELETE request."""
        url = kwargs.get("url")
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="URL required"
            )
        return self._make_request("DELETE", url, **kwargs)

    def _head(self, **kwargs) -> ToolResult:
        """Make a HEAD request."""
        url = kwargs.get("url")
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="URL required"
            )
        return self._make_request("HEAD", url, **kwargs)

    def _request(self, **kwargs) -> ToolResult:
        """Make a custom request."""
        method = kwargs.get("method", "GET")
        url = kwargs.get("url")
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="URL required"
            )
        return self._make_request(method, url, **kwargs)

    def _download(self, **kwargs) -> ToolResult:
        """Download a file from URL."""
        url = kwargs.get("url")
        path = kwargs.get("path") or kwargs.get("output")
        
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="URL required"
            )
        
        if not path:
            # Extract filename from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            filename = parsed.path.split("/")[-1] or "download"
            path = str(Path.home() / "Downloads" / filename)
        
        try:
            import requests
        except ImportError:
            return ToolResult(
                success=False,
                data={},
                message="requests library not installed"
            )
        
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Ensure directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "path": path,
                    "size": total_size
                },
                message=f"Downloaded to {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Download failed: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "GET request: api_tool --action get --url 'https://api.example.com/data'",
            "POST request: api_tool --action post --url 'https://api.example.com/data' --json '{\"key\": \"value\"}'",
            "Download file: api_tool --action download --url 'https://example.com/file.zip'",
            "With headers: api_tool --action get --url 'https://api.example.com' --headers '{\"Authorization\": \"Bearer token\"}'",
        ]
