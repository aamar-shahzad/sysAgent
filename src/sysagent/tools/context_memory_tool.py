"""
Context Memory tool for SysAgent CLI - Smart memory to remember user preferences and context.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory


@register_tool
class ContextMemoryTool(BaseTool):
    """Tool for managing user preferences, context, and memory."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="context_memory_tool",
            description="Remember user preferences, frequently used commands, and context across sessions",
            category=ToolCategory.AUTOMATION,
            permissions=["memory"],
            version="1.0.0"
        )

    def _get_memory_dir(self) -> Path:
        """Get memory storage directory."""
        path = Path.home() / ".sysagent" / "memory"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _load_memory(self, memory_type: str) -> Dict:
        """Load memory file."""
        file_path = self._get_memory_dir() / f"{memory_type}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_memory(self, memory_type: str, data: Dict):
        """Save memory file."""
        file_path = self._get_memory_dir() / f"{memory_type}.json"
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "remember": self._remember,
                "recall": self._recall,
                "forget": self._forget,
                "preferences": self._get_preferences,
                "set_preference": self._set_preference,
                "history": self._get_history,
                "add_history": self._add_history,
                "favorites": self._get_favorites,
                "add_favorite": self._add_favorite,
                "learn": self._learn_pattern,
                "suggest": self._suggest_from_context,
                "clear_all": self._clear_all,
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
                message=f"Memory operation failed: {str(e)}",
                error=str(e)
            )

    def _remember(self, **kwargs) -> ToolResult:
        """Remember a key-value pair."""
        key = kwargs.get("key")
        value = kwargs.get("value")
        category = kwargs.get("category", "general")
        
        if not key or value is None:
            return ToolResult(success=False, data={}, message="Key and value required")
        
        memories = self._load_memory("memories")
        
        if category not in memories:
            memories[category] = {}
        
        memories[category][key] = {
            "value": value,
            "remembered_at": datetime.now().isoformat(),
            "access_count": 0
        }
        
        self._save_memory("memories", memories)
        
        return ToolResult(
            success=True,
            data={"key": key, "value": value, "category": category},
            message=f"Remembered: {key} = {value}"
        )

    def _recall(self, **kwargs) -> ToolResult:
        """Recall a remembered value."""
        key = kwargs.get("key")
        category = kwargs.get("category")
        
        memories = self._load_memory("memories")
        
        if key:
            # Search for specific key
            for cat, items in memories.items():
                if key in items:
                    items[key]["access_count"] = items[key].get("access_count", 0) + 1
                    self._save_memory("memories", memories)
                    
                    return ToolResult(
                        success=True,
                        data={"key": key, "value": items[key]["value"], "category": cat},
                        message=f"{key}: {items[key]['value']}"
                    )
            
            return ToolResult(success=False, data={}, message=f"No memory found for '{key}'")
        
        if category:
            if category in memories:
                return ToolResult(
                    success=True,
                    data={"category": category, "items": memories[category]},
                    message=f"Found {len(memories[category])} items in '{category}'"
                )
            return ToolResult(success=False, data={}, message=f"Category '{category}' not found")
        
        # Return all memories summary
        summary = {cat: list(items.keys()) for cat, items in memories.items()}
        return ToolResult(
            success=True,
            data={"memories": summary},
            message=f"Found memories in {len(memories)} categories"
        )

    def _forget(self, **kwargs) -> ToolResult:
        """Forget a remembered value."""
        key = kwargs.get("key")
        category = kwargs.get("category")
        
        memories = self._load_memory("memories")
        
        if category and key:
            if category in memories and key in memories[category]:
                del memories[category][key]
                self._save_memory("memories", memories)
                return ToolResult(success=True, data={}, message=f"Forgot: {key}")
        
        if key:
            for cat in memories:
                if key in memories[cat]:
                    del memories[cat][key]
                    self._save_memory("memories", memories)
                    return ToolResult(success=True, data={}, message=f"Forgot: {key}")
        
        return ToolResult(success=False, data={}, message=f"Nothing to forget for '{key}'")

    def _get_preferences(self, **kwargs) -> ToolResult:
        """Get user preferences."""
        prefs = self._load_memory("preferences")
        
        return ToolResult(
            success=True,
            data={"preferences": prefs},
            message=f"Found {len(prefs)} preferences"
        )

    def _set_preference(self, **kwargs) -> ToolResult:
        """Set a user preference."""
        name = kwargs.get("name") or kwargs.get("key")
        value = kwargs.get("value")
        
        if not name:
            return ToolResult(success=False, data={}, message="Preference name required")
        
        prefs = self._load_memory("preferences")
        prefs[name] = {
            "value": value,
            "set_at": datetime.now().isoformat()
        }
        self._save_memory("preferences", prefs)
        
        return ToolResult(
            success=True,
            data={"name": name, "value": value},
            message=f"Preference '{name}' set to '{value}'"
        )

    def _get_history(self, **kwargs) -> ToolResult:
        """Get command history."""
        limit = kwargs.get("limit", 20)
        
        history = self._load_memory("command_history")
        commands = history.get("commands", [])
        
        return ToolResult(
            success=True,
            data={"history": commands[-limit:]},
            message=f"Last {min(limit, len(commands))} commands"
        )

    def _add_history(self, **kwargs) -> ToolResult:
        """Add to command history."""
        command = kwargs.get("command")
        result = kwargs.get("result")
        
        if not command:
            return ToolResult(success=False, data={}, message="Command required")
        
        history = self._load_memory("command_history")
        if "commands" not in history:
            history["commands"] = []
        
        history["commands"].append({
            "command": command,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep last 100 commands
        history["commands"] = history["commands"][-100:]
        self._save_memory("command_history", history)
        
        return ToolResult(success=True, data={}, message="Command added to history")

    def _get_favorites(self, **kwargs) -> ToolResult:
        """Get favorite commands/actions."""
        favorites = self._load_memory("favorites")
        
        return ToolResult(
            success=True,
            data={"favorites": favorites.get("items", [])},
            message=f"Found {len(favorites.get('items', []))} favorites"
        )

    def _add_favorite(self, **kwargs) -> ToolResult:
        """Add a favorite command/action."""
        name = kwargs.get("name")
        command = kwargs.get("command")
        description = kwargs.get("description", "")
        
        if not name or not command:
            return ToolResult(success=False, data={}, message="Name and command required")
        
        favorites = self._load_memory("favorites")
        if "items" not in favorites:
            favorites["items"] = []
        
        # Check for duplicates
        favorites["items"] = [f for f in favorites["items"] if f.get("name") != name]
        
        favorites["items"].append({
            "name": name,
            "command": command,
            "description": description,
            "added_at": datetime.now().isoformat(),
            "use_count": 0
        })
        
        self._save_memory("favorites", favorites)
        
        return ToolResult(
            success=True,
            data={"name": name, "command": command},
            message=f"Added favorite: {name}"
        )

    def _learn_pattern(self, **kwargs) -> ToolResult:
        """Learn a usage pattern for smarter suggestions."""
        context = kwargs.get("context")  # e.g., "morning", "coding", "meeting"
        actions = kwargs.get("actions", [])  # List of actions typically done in this context
        
        if not context:
            return ToolResult(success=False, data={}, message="Context required")
        
        patterns = self._load_memory("patterns")
        
        patterns[context] = {
            "actions": actions,
            "learned_at": datetime.now().isoformat(),
            "trigger_count": patterns.get(context, {}).get("trigger_count", 0)
        }
        
        self._save_memory("patterns", patterns)
        
        return ToolResult(
            success=True,
            data={"context": context, "actions": actions},
            message=f"Learned pattern for context: {context}"
        )

    def _suggest_from_context(self, **kwargs) -> ToolResult:
        """Get suggestions based on current context."""
        context_hints = kwargs.get("hints", [])
        
        suggestions = []
        
        # Load all memory sources
        patterns = self._load_memory("patterns")
        history = self._load_memory("command_history")
        favorites = self._load_memory("favorites")
        prefs = self._load_memory("preferences")
        
        # Check patterns
        for context, data in patterns.items():
            if any(hint.lower() in context.lower() for hint in context_hints):
                suggestions.extend([
                    {"type": "pattern", "context": context, "action": action}
                    for action in data.get("actions", [])
                ])
        
        # Check frequently used commands
        commands = history.get("commands", [])
        command_freq = {}
        for cmd in commands:
            c = cmd.get("command", "")
            command_freq[c] = command_freq.get(c, 0) + 1
        
        frequent = sorted(command_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        for cmd, count in frequent:
            suggestions.append({
                "type": "frequent",
                "command": cmd,
                "count": count
            })
        
        # Add favorites
        for fav in favorites.get("items", [])[:5]:
            suggestions.append({
                "type": "favorite",
                "name": fav.get("name"),
                "command": fav.get("command")
            })
        
        # Time-based suggestions
        hour = datetime.now().hour
        if 6 <= hour < 9:
            suggestions.append({
                "type": "time_based",
                "suggestion": "Good morning! Check system status?",
                "command": "system_insights_tool --action quick_insights"
            })
        elif 17 <= hour < 19:
            suggestions.append({
                "type": "time_based",
                "suggestion": "End of day? Check git status?",
                "command": "git_tool --action status"
            })
        
        return ToolResult(
            success=True,
            data={"suggestions": suggestions[:10]},
            message=f"Generated {len(suggestions[:10])} suggestions"
        )

    def _clear_all(self, **kwargs) -> ToolResult:
        """Clear all memory (with confirmation)."""
        confirm = kwargs.get("confirm", False)
        
        if not confirm:
            return ToolResult(
                success=False,
                data={},
                message="Add --confirm to clear all memory"
            )
        
        memory_dir = self._get_memory_dir()
        for f in memory_dir.glob("*.json"):
            f.unlink()
        
        return ToolResult(
            success=True,
            data={},
            message="All memory cleared"
        )

    def get_usage_examples(self) -> List[str]:
        return [
            "Remember: context_memory_tool --action remember --key 'project' --value 'sysagent'",
            "Recall: context_memory_tool --action recall --key 'project'",
            "Set preference: context_memory_tool --action set_preference --name 'theme' --value 'dark'",
            "Get suggestions: context_memory_tool --action suggest --hints 'morning'",
            "Add favorite: context_memory_tool --action add_favorite --name 'status' --command 'system_info --action overview'",
        ]
