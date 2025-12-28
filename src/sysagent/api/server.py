"""
REST API Server for SysAgent - HTTP API for external integration.
Enterprise-grade API with authentication and rate limiting.
"""

import json
import os
import time
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from functools import wraps
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading


class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if a request is allowed."""
        now = time.time()
        minute_ago = now - 60
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Clean old requests
        self.requests[client_id] = [
            t for t in self.requests[client_id] if t > minute_ago
        ]
        
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        self.requests[client_id].append(now)
        return True


class APIKeyManager:
    """Manages API keys for authentication."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".sysagent" / "api_keys.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.keys: Dict[str, Dict] = {}
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.keys = json.load(f)
            except Exception:
                self.keys = {}
    
    def _save_keys(self):
        """Save API keys to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.keys, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save API keys: {e}")
    
    def create_key(self, name: str, permissions: List[str] = None) -> str:
        """Create a new API key."""
        key = f"sysagent_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        self.keys[key_hash] = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "permissions": permissions or ["read", "write", "execute"],
            "last_used": None,
            "request_count": 0
        }
        
        self._save_keys()
        return key
    
    def validate_key(self, key: str) -> Optional[Dict]:
        """Validate an API key and return its info."""
        if not key:
            return None
        
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash in self.keys:
            # Update last used
            self.keys[key_hash]["last_used"] = datetime.now().isoformat()
            self.keys[key_hash]["request_count"] += 1
            self._save_keys()
            return self.keys[key_hash]
        
        return None
    
    def revoke_key(self, key_hash: str) -> bool:
        """Revoke an API key."""
        if key_hash in self.keys:
            del self.keys[key_hash]
            self._save_keys()
            return True
        return False
    
    def list_keys(self) -> List[Dict]:
        """List all API keys (without the actual keys)."""
        return [
            {"hash": k[:16] + "...", **v}
            for k, v in self.keys.items()
        ]


class SysAgentAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for SysAgent API."""
    
    agent = None
    key_manager = None
    rate_limiter = None
    require_auth = True
    
    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        """Set response headers."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key")
        self.end_headers()
    
    def _json_response(self, data: Dict, status: int = 200):
        """Send a JSON response."""
        self._set_headers(status)
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _error_response(self, message: str, status: int = 400):
        """Send an error response."""
        self._json_response({"error": message, "status": status}, status)
    
    def _authenticate(self) -> Optional[Dict]:
        """Authenticate the request."""
        if not self.require_auth:
            return {"permissions": ["read", "write", "execute"]}
        
        # Check API key in header
        api_key = self.headers.get("X-API-Key") or self.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not api_key:
            return None
        
        return self.key_manager.validate_key(api_key)
    
    def _check_rate_limit(self) -> bool:
        """Check rate limit."""
        client_ip = self.client_address[0]
        return self.rate_limiter.is_allowed(client_ip)
    
    def _get_body(self) -> Dict:
        """Get request body as JSON."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        
        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode())
        except Exception:
            return {}
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self._set_headers(204)
    
    def do_GET(self):
        """Handle GET requests."""
        # Rate limiting
        if not self._check_rate_limit():
            self._error_response("Rate limit exceeded", 429)
            return
        
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        # Public endpoints
        if path == "/api/health":
            self._json_response({
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        if path == "/api/info":
            self._json_response({
                "name": "SysAgent API",
                "version": "1.0.0",
                "endpoints": [
                    "GET /api/health - Health check",
                    "GET /api/info - API information",
                    "POST /api/chat - Send a message",
                    "GET /api/tools - List available tools",
                    "POST /api/tool/{name} - Execute a tool",
                    "GET /api/sessions - List sessions",
                    "GET /api/session/{id} - Get session",
                    "POST /api/session - Create session",
                ]
            })
            return
        
        # Authenticated endpoints
        auth = self._authenticate()
        if not auth:
            self._error_response("Unauthorized", 401)
            return
        
        if path == "/api/tools":
            tools = self._get_tools_list()
            self._json_response({"tools": tools})
            return
        
        if path == "/api/sessions":
            from ..core.session_manager import SessionManager
            sm = SessionManager()
            sessions = sm.list_sessions(limit=int(query.get("limit", [50])[0]))
            self._json_response({"sessions": sessions})
            return
        
        if path.startswith("/api/session/"):
            session_id = path.split("/")[-1]
            from ..core.session_manager import SessionManager
            sm = SessionManager()
            session = sm.load_session(session_id)
            if session:
                self._json_response(session.to_dict())
            else:
                self._error_response("Session not found", 404)
            return
        
        if path == "/api/stats":
            stats = self._get_stats()
            self._json_response(stats)
            return
        
        self._error_response("Not found", 404)
    
    def do_POST(self):
        """Handle POST requests."""
        # Rate limiting
        if not self._check_rate_limit():
            self._error_response("Rate limit exceeded", 429)
            return
        
        # Authenticate
        auth = self._authenticate()
        if not auth:
            self._error_response("Unauthorized", 401)
            return
        
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._get_body()
        
        if path == "/api/chat":
            message = body.get("message")
            if not message:
                self._error_response("Message required")
                return
            
            response = self._process_chat(message)
            self._json_response(response)
            return
        
        if path.startswith("/api/tool/"):
            tool_name = path.split("/")[-1]
            result = self._execute_tool(tool_name, body)
            self._json_response(result)
            return
        
        if path == "/api/session":
            from ..core.session_manager import SessionManager
            sm = SessionManager()
            title = body.get("title")
            session = sm.create_session(title)
            self._json_response({"session_id": session.id, "title": session.title})
            return
        
        if path == "/api/keys":
            # Create new API key (requires admin permission)
            if "admin" not in auth.get("permissions", []) and self.require_auth:
                self._error_response("Admin permission required", 403)
                return
            
            name = body.get("name", "unnamed")
            permissions = body.get("permissions", ["read", "write", "execute"])
            key = self.key_manager.create_key(name, permissions)
            self._json_response({"api_key": key, "note": "Save this key - it won't be shown again"})
            return
        
        self._error_response("Not found", 404)
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        auth = self._authenticate()
        if not auth:
            self._error_response("Unauthorized", 401)
            return
        
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path.startswith("/api/session/"):
            session_id = path.split("/")[-1]
            from ..core.session_manager import SessionManager
            sm = SessionManager()
            if sm.delete_session(session_id):
                self._json_response({"deleted": session_id})
            else:
                self._error_response("Session not found", 404)
            return
        
        self._error_response("Not found", 404)
    
    def _get_tools_list(self) -> List[Dict]:
        """Get list of available tools."""
        tools = [
            {"name": "system_info", "description": "Get system information", "actions": ["overview", "cpu", "memory", "disk", "battery"]},
            {"name": "file_operations", "description": "File system operations", "actions": ["list", "read", "write", "delete"]},
            {"name": "process_management", "description": "Process control", "actions": ["list", "kill"]},
            {"name": "network_diagnostics", "description": "Network tools", "actions": ["ping", "ports"]},
            {"name": "browser_control", "description": "Browser control", "actions": ["open", "search", "close"]},
            {"name": "media_control", "description": "Audio control", "actions": ["volume", "mute", "play_pause"]},
            {"name": "smart_search", "description": "Search everything", "actions": ["files", "apps", "content"]},
            {"name": "system_insights", "description": "AI analysis", "actions": ["health_check", "recommendations"]},
            {"name": "workflow_operations", "description": "Automation", "actions": ["run", "list", "create"]},
            {"name": "git_operations", "description": "Git control", "actions": ["status", "commit", "push", "pull"]},
        ]
        return tools
    
    def _process_chat(self, message: str) -> Dict:
        """Process a chat message."""
        if not self.agent:
            return {"error": "Agent not initialized", "success": False}
        
        try:
            result = self.agent.process_command(message)
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "tools_used": result.get("tools_used", [])
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _execute_tool(self, tool_name: str, params: Dict) -> Dict:
        """Execute a specific tool."""
        if not self.agent:
            return {"error": "Agent not initialized", "success": False}
        
        try:
            action = params.pop("action", "default")
            result = self.agent.tool_executor.execute_tool(tool_name, action=action, **params)
            return {
                "success": result.success,
                "data": result.data,
                "message": result.message
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _get_stats(self) -> Dict:
        """Get system statistics."""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "uptime_seconds": time.time() - psutil.boot_time()
            }
        except Exception:
            return {"error": "Could not get stats"}
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class SysAgentAPIServer:
    """
    REST API Server for SysAgent.
    
    Usage:
        server = SysAgentAPIServer(port=8080)
        server.start()  # Starts in background thread
        server.stop()   # Stops the server
    """
    
    def __init__(self, host: str = "localhost", port: int = 8080, 
                 require_auth: bool = True, agent=None):
        self.host = host
        self.port = port
        self.require_auth = require_auth
        self.agent = agent
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.key_manager = APIKeyManager()
        self.rate_limiter = RateLimiter()
        
        # Configure handler
        SysAgentAPIHandler.agent = agent
        SysAgentAPIHandler.key_manager = self.key_manager
        SysAgentAPIHandler.rate_limiter = self.rate_limiter
        SysAgentAPIHandler.require_auth = require_auth
    
    def start(self, blocking: bool = False):
        """Start the API server."""
        self.server = HTTPServer((self.host, self.port), SysAgentAPIHandler)
        
        print(f"🚀 SysAgent API Server starting on http://{self.host}:{self.port}")
        print(f"   Authentication: {'required' if self.require_auth else 'disabled'}")
        print(f"   Endpoints: /api/health, /api/chat, /api/tools, /api/sessions")
        
        if self.require_auth:
            print(f"\n   Create an API key with: POST /api/keys")
        
        if blocking:
            self.server.serve_forever()
        else:
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop the API server."""
        if self.server:
            self.server.shutdown()
            print("🛑 SysAgent API Server stopped")
    
    def create_api_key(self, name: str = "default") -> str:
        """Create a new API key."""
        return self.key_manager.create_key(name)
    
    def get_url(self) -> str:
        """Get the server URL."""
        return f"http://{self.host}:{self.port}"


def start_api_server(port: int = 8080, require_auth: bool = True):
    """Start the API server (CLI entry point)."""
    try:
        from ..core.config import ConfigManager
        from ..core.permissions import PermissionManager
        from ..core.langgraph_agent import LangGraphAgent
        
        config = ConfigManager()
        perms = PermissionManager(config)
        agent = LangGraphAgent(config, perms)
        
        server = SysAgentAPIServer(port=port, require_auth=require_auth, agent=agent)
        
        # Create default key if auth required
        if require_auth:
            key = server.create_api_key("default")
            print(f"\n🔑 Your API Key: {key}")
            print("   Use this in the X-API-Key header for requests\n")
        
        server.start(blocking=True)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")


if __name__ == "__main__":
    start_api_server()
