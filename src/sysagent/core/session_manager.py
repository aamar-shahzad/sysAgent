"""
Session Manager for SysAgent - Save, load, and manage chat sessions.
Enterprise-grade conversation persistence.
"""

import json
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class Message:
    """Represents a chat message."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: str
    tool_name: Optional[str] = None
    tool_status: Optional[str] = None
    duration_ms: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(**data)


@dataclass
class Session:
    """Represents a chat session."""
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Message]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Session":
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            id=data["id"],
            title=data.get("title", "Untitled"),
            created_at=data["created_at"],
            updated_at=data.get("updated_at", data["created_at"]),
            messages=messages,
            metadata=data.get("metadata", {})
        )


class SessionManager:
    """
    Manages chat sessions with persistence.
    
    Features:
    - Create, save, load, delete sessions
    - Auto-save on changes
    - Session search and filtering
    - Export/import sessions
    - Session statistics
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path.home() / ".sysagent" / "sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[Session] = None
        self.sessions_index: Dict[str, Dict] = {}
        self._load_index()
    
    def _load_index(self):
        """Load the sessions index."""
        index_file = self.storage_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self.sessions_index = json.load(f)
            except Exception:
                self.sessions_index = {}
        else:
            self.sessions_index = {}
    
    def _save_index(self):
        """Save the sessions index."""
        index_file = self.storage_dir / "index.json"
        try:
            with open(index_file, 'w') as f:
                json.dump(self.sessions_index, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save session index: {e}")
    
    def create_session(self, title: Optional[str] = None) -> Session:
        """Create a new session."""
        session_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        
        session = Session(
            id=session_id,
            title=title or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            created_at=now,
            updated_at=now,
            messages=[],
            metadata={
                "message_count": 0,
                "tool_calls": 0,
                "last_tool": None
            }
        )
        
        self.current_session = session
        self._update_index(session)
        self.save_session(session)
        
        return session
    
    def _update_index(self, session: Session):
        """Update the session index."""
        self.sessions_index[session.id] = {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": len(session.messages),
            "preview": self._get_preview(session)
        }
        self._save_index()
    
    def _get_preview(self, session: Session, max_length: int = 100) -> str:
        """Get a preview of the session."""
        for msg in session.messages:
            if msg.role == "user":
                content = msg.content[:max_length]
                if len(msg.content) > max_length:
                    content += "..."
                return content
        return "Empty session"
    
    def add_message(self, role: str, content: str, **kwargs) -> Message:
        """Add a message to the current session."""
        if not self.current_session:
            self.create_session()
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
        
        self.current_session.messages.append(message)
        self.current_session.updated_at = datetime.now().isoformat()
        self.current_session.metadata["message_count"] = len(self.current_session.messages)
        
        if role == "tool":
            self.current_session.metadata["tool_calls"] = \
                self.current_session.metadata.get("tool_calls", 0) + 1
            self.current_session.metadata["last_tool"] = kwargs.get("tool_name")
        
        # Auto-title based on first user message
        if role == "user" and len(self.current_session.messages) == 1:
            self.current_session.title = content[:50] + ("..." if len(content) > 50 else "")
        
        self._update_index(self.current_session)
        self.save_session(self.current_session)
        
        return message
    
    def save_session(self, session: Optional[Session] = None):
        """Save a session to disk."""
        session = session or self.current_session
        if not session:
            return
        
        session_file = self.storage_dir / f"{session.id}.json"
        try:
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save session: {e}")
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Load a session from disk."""
        session_file = self.storage_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            session = Session.from_dict(data)
            self.current_session = session
            return session
        except Exception as e:
            print(f"Warning: Could not load session: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        session_file = self.storage_dir / f"{session_id}.json"
        
        try:
            if session_file.exists():
                session_file.unlink()
            
            if session_id in self.sessions_index:
                del self.sessions_index[session_id]
                self._save_index()
            
            if self.current_session and self.current_session.id == session_id:
                self.current_session = None
            
            return True
        except Exception as e:
            print(f"Warning: Could not delete session: {e}")
            return False
    
    def list_sessions(self, limit: int = 50, search: Optional[str] = None) -> List[Dict]:
        """List all sessions with optional search."""
        sessions = list(self.sessions_index.values())
        
        # Filter by search
        if search:
            search_lower = search.lower()
            sessions = [
                s for s in sessions
                if search_lower in s.get("title", "").lower()
                or search_lower in s.get("preview", "").lower()
            ]
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return sessions[:limit]
    
    def get_current_session(self) -> Optional[Session]:
        """Get the current active session."""
        return self.current_session
    
    def clear_current_session(self):
        """Clear the current session (start fresh)."""
        if self.current_session:
            self.current_session.messages = []
            self.current_session.updated_at = datetime.now().isoformat()
            self.current_session.metadata = {"message_count": 0, "tool_calls": 0}
            self._update_index(self.current_session)
            self.save_session()
    
    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """Export a session to a string."""
        session = self.load_session(session_id) if session_id != self.current_session.id else self.current_session
        if not session:
            return None
        
        if format == "json":
            return json.dumps(session.to_dict(), indent=2)
        elif format == "markdown":
            lines = [f"# {session.title}", ""]
            lines.append(f"*Created: {session.created_at}*")
            lines.append(f"*Messages: {len(session.messages)}*")
            lines.append("")
            lines.append("---")
            lines.append("")
            
            for msg in session.messages:
                role_emoji = {"user": "👤", "assistant": "🧠", "system": "⚙️", "tool": "🔧"}.get(msg.role, "")
                role_name = msg.role.title()
                lines.append(f"### {role_emoji} {role_name}")
                lines.append("")
                lines.append(msg.content)
                lines.append("")
            
            return "\n".join(lines)
        elif format == "text":
            lines = [f"Session: {session.title}", "=" * 50, ""]
            for msg in session.messages:
                lines.append(f"[{msg.role.upper()}] {msg.timestamp}")
                lines.append(msg.content)
                lines.append("")
            return "\n".join(lines)
        
        return None
    
    def import_session(self, data: str, format: str = "json") -> Optional[Session]:
        """Import a session from a string."""
        if format != "json":
            return None
        
        try:
            session_data = json.loads(data)
            # Generate new ID to avoid conflicts
            session_data["id"] = str(uuid.uuid4())[:8]
            session_data["created_at"] = datetime.now().isoformat()
            session_data["updated_at"] = datetime.now().isoformat()
            session_data["title"] = f"Imported: {session_data.get('title', 'Untitled')}"
            
            session = Session.from_dict(session_data)
            self._update_index(session)
            self.save_session(session)
            
            return session
        except Exception as e:
            print(f"Warning: Could not import session: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_sessions = len(self.sessions_index)
        total_messages = sum(s.get("message_count", 0) for s in self.sessions_index.values())
        
        # Get recent activity
        recent = self.list_sessions(limit=5)
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "storage_path": str(self.storage_dir),
            "recent_sessions": recent,
            "current_session_id": self.current_session.id if self.current_session else None
        }
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up sessions older than specified days."""
        from datetime import timedelta
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        deleted = 0
        
        for session_id, info in list(self.sessions_index.items()):
            if info.get("updated_at", "") < cutoff:
                if self.delete_session(session_id):
                    deleted += 1
        
        return deleted
