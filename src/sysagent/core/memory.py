"""
Short-term and Long-term Memory Management for SysAgent.
Implements conversation buffer memory with sliding window.
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
import threading


@dataclass
class MemoryEntry:
    """A single memory entry."""
    role: str  # user, assistant, system, tool
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_message(self) -> Dict[str, str]:
        """Convert to LangChain message format."""
        return {"role": self.role, "content": self.content}


@dataclass  
class ConversationContext:
    """Context for a conversation session."""
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    learned_patterns: List[str] = field(default_factory=list)
    frequently_used_tools: Dict[str, int] = field(default_factory=dict)


class ShortTermMemory:
    """
    Short-term conversation memory with sliding window.
    Keeps the most recent N messages in context.
    """
    
    def __init__(self, max_messages: int = 20, max_tokens: int = 4000):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self._messages: deque = deque(maxlen=max_messages)
        self._lock = threading.Lock()
        self._token_count = 0
    
    def add(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to short-term memory."""
        with self._lock:
            entry = MemoryEntry(
                role=role,
                content=content,
                metadata=metadata or {}
            )
            self._messages.append(entry)
            
            # Estimate tokens (rough: 4 chars = 1 token)
            self._token_count += len(content) // 4
            
            # Trim if over token limit
            while self._token_count > self.max_tokens and len(self._messages) > 2:
                removed = self._messages.popleft()
                self._token_count -= len(removed.content) // 4
    
    def get_messages(self, limit: int = None) -> List[Dict[str, str]]:
        """Get messages in LangChain format."""
        with self._lock:
            messages = list(self._messages)
            if limit:
                messages = messages[-limit:]
            return [m.to_message() for m in messages]
    
    def get_context_window(self, include_system: bool = True) -> List[Dict[str, str]]:
        """Get optimal context window for LLM."""
        with self._lock:
            messages = []
            
            # Always include system message if present
            for m in self._messages:
                if m.role == "system":
                    messages.append(m.to_message())
                    break
            
            # Add recent messages
            recent = [m for m in self._messages if m.role != "system"]
            messages.extend([m.to_message() for m in recent[-self.max_messages:]])
            
            return messages
    
    def clear(self):
        """Clear short-term memory."""
        with self._lock:
            self._messages.clear()
            self._token_count = 0
    
    def summarize(self) -> str:
        """Get a summary of the conversation so far."""
        with self._lock:
            if not self._messages:
                return "No conversation history."
            
            summary_parts = []
            for m in self._messages:
                if m.role == "user":
                    summary_parts.append(f"User asked: {m.content[:100]}...")
                elif m.role == "assistant":
                    summary_parts.append(f"Agent: {m.content[:100]}...")
            
            return "\n".join(summary_parts[-5:])  # Last 5 exchanges


class LongTermMemory:
    """
    Long-term memory with persistence.
    Stores important facts, user preferences, and learned patterns.
    """
    
    def __init__(self, storage_path: Path = None):
        self.storage_path = storage_path or Path.home() / ".sysagent" / "memory"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._facts: Dict[str, Any] = {}
        self._preferences: Dict[str, Any] = {}
        self._patterns: List[Dict[str, Any]] = []
        self._tool_usage: Dict[str, int] = {}
        
        self._load()
    
    def _load(self):
        """Load memory from disk."""
        try:
            memory_file = self.storage_path / "long_term.json"
            if memory_file.exists():
                with open(memory_file) as f:
                    data = json.load(f)
                    self._facts = data.get("facts", {})
                    self._preferences = data.get("preferences", {})
                    self._patterns = data.get("patterns", [])
                    self._tool_usage = data.get("tool_usage", {})
        except Exception:
            pass
    
    def _save(self):
        """Save memory to disk."""
        try:
            memory_file = self.storage_path / "long_term.json"
            with open(memory_file, "w") as f:
                json.dump({
                    "facts": self._facts,
                    "preferences": self._preferences,
                    "patterns": self._patterns,
                    "tool_usage": self._tool_usage,
                    "updated_at": time.time()
                }, f, indent=2)
        except Exception:
            pass
    
    def remember_fact(self, key: str, value: Any, category: str = "general"):
        """Remember a fact."""
        self._facts[key] = {
            "value": value,
            "category": category,
            "timestamp": time.time()
        }
        self._save()
    
    def recall_fact(self, key: str) -> Optional[Any]:
        """Recall a fact."""
        fact = self._facts.get(key)
        return fact["value"] if fact else None
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        self._preferences[key] = {
            "value": value,
            "timestamp": time.time()
        }
        self._save()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        pref = self._preferences.get(key)
        return pref["value"] if pref else default
    
    def record_pattern(self, pattern: str, context: Dict[str, Any] = None):
        """Record a usage pattern."""
        self._patterns.append({
            "pattern": pattern,
            "context": context or {},
            "timestamp": time.time()
        })
        # Keep only last 100 patterns
        self._patterns = self._patterns[-100:]
        self._save()
    
    def record_tool_usage(self, tool_name: str):
        """Record tool usage."""
        self._tool_usage[tool_name] = self._tool_usage.get(tool_name, 0) + 1
        self._save()
    
    def get_frequent_tools(self, limit: int = 5) -> List[tuple]:
        """Get most frequently used tools."""
        sorted_tools = sorted(self._tool_usage.items(), key=lambda x: x[1], reverse=True)
        return sorted_tools[:limit]
    
    def get_context_for_prompt(self) -> str:
        """Get relevant context for the system prompt."""
        context_parts = []
        
        # Add preferences
        if self._preferences:
            prefs = [f"- {k}: {v['value']}" for k, v in list(self._preferences.items())[:5]]
            context_parts.append("User Preferences:\n" + "\n".join(prefs))
        
        # Add frequent tools
        frequent = self.get_frequent_tools(3)
        if frequent:
            tools = [f"- {t[0]} (used {t[1]} times)" for t in frequent]
            context_parts.append("Frequently Used Tools:\n" + "\n".join(tools))
        
        # Add recent facts
        recent_facts = sorted(self._facts.items(), key=lambda x: x[1]["timestamp"], reverse=True)[:3]
        if recent_facts:
            facts = [f"- {k}: {v['value']}" for k, v in recent_facts]
            context_parts.append("Known Facts:\n" + "\n".join(facts))
        
        return "\n\n".join(context_parts) if context_parts else ""


class MemoryManager:
    """
    Unified memory manager combining short-term and long-term memory.
    """
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(int(time.time()))
        self.short_term = ShortTermMemory(max_messages=20, max_tokens=4000)
        self.long_term = LongTermMemory()
        self._context = ConversationContext(session_id=self.session_id)
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to memory."""
        self.short_term.add(role, content, metadata)
        self._context.last_active = time.time()
        
        # Learn from the message
        if role == "user" and metadata:
            tool = metadata.get("tool_used")
            if tool:
                self.long_term.record_tool_usage(tool)
    
    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Get messages formatted for LLM context."""
        return self.short_term.get_context_window()
    
    def get_system_context(self) -> str:
        """Get additional context from long-term memory for system prompt."""
        return self.long_term.get_context_for_prompt()
    
    def remember(self, key: str, value: Any, category: str = "general"):
        """Remember something for the long term."""
        self.long_term.remember_fact(key, value, category)
    
    def recall(self, key: str) -> Optional[Any]:
        """Recall something from long-term memory."""
        return self.long_term.recall_fact(key)
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.long_term.set_preference(key, value)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.long_term.get_preference(key, default)
    
    def clear_session(self):
        """Clear the current session's short-term memory."""
        self.short_term.clear()
        self.session_id = str(int(time.time()))
        self._context = ConversationContext(session_id=self.session_id)
    
    def get_summary(self) -> str:
        """Get a summary of current conversation."""
        return self.short_term.summarize()


# Singleton instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(session_id: str = None) -> MemoryManager:
    """Get or create the memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(session_id)
    return _memory_manager


def reset_memory_manager():
    """Reset the memory manager."""
    global _memory_manager
    if _memory_manager:
        _memory_manager.clear_session()
    _memory_manager = None
