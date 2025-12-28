"""
Smart Learning System for SysAgent.
Learns user patterns, remembers preferences, and provides intelligent suggestions.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import Counter
from enum import Enum


class PatternType(Enum):
    """Types of patterns the system can learn."""
    COMMAND = "command"
    TIME_BASED = "time_based"
    SEQUENCE = "sequence"
    CONTEXT = "context"


@dataclass
class CommandUsage:
    """Track command usage."""
    command: str
    count: int = 0
    last_used: str = ""
    avg_time_of_day: float = 0.0  # Hour of day (0-23)
    success_rate: float = 1.0
    contexts: List[str] = field(default_factory=list)
    following_commands: List[str] = field(default_factory=list)


@dataclass 
class UserPattern:
    """Represents a learned user pattern."""
    pattern_type: str
    pattern_data: Dict[str, Any]
    confidence: float = 0.0
    occurrences: int = 0
    last_seen: str = ""


@dataclass
class Shortcut:
    """User-defined shortcut."""
    name: str
    command: str
    description: str = ""
    usage_count: int = 0
    created_at: str = ""


@dataclass
class Snippet:
    """Reusable command snippet."""
    id: str
    name: str
    command: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    is_favorite: bool = False
    created_at: str = ""


class SmartLearningSystem:
    """
    Learns from user behavior to provide smarter suggestions.
    
    Features:
    - Command usage tracking
    - Time-based pattern detection
    - Command sequence learning
    - User shortcuts
    - Smart snippets
    - Favorites
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path.home() / ".config" / "sysagent" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.commands_file = self.data_dir / "commands.json"
        self.patterns_file = self.data_dir / "patterns.json"
        self.shortcuts_file = self.data_dir / "shortcuts.json"
        self.snippets_file = self.data_dir / "snippets.json"
        self.history_file = self.data_dir / "history.json"
        
        self.command_usage: Dict[str, CommandUsage] = {}
        self.patterns: List[UserPattern] = []
        self.shortcuts: Dict[str, Shortcut] = {}
        self.snippets: Dict[str, Snippet] = {}
        self.command_history: List[Dict] = []
        
        self._load_data()
    
    def _load_data(self):
        """Load all learning data."""
        # Load command usage
        if self.commands_file.exists():
            try:
                data = json.loads(self.commands_file.read_text())
                self.command_usage = {
                    k: CommandUsage(**v) for k, v in data.items()
                }
            except Exception:
                pass
        
        # Load patterns
        if self.patterns_file.exists():
            try:
                data = json.loads(self.patterns_file.read_text())
                self.patterns = [UserPattern(**p) for p in data]
            except Exception:
                pass
        
        # Load shortcuts
        if self.shortcuts_file.exists():
            try:
                data = json.loads(self.shortcuts_file.read_text())
                self.shortcuts = {k: Shortcut(**v) for k, v in data.items()}
            except Exception:
                pass
        
        # Load snippets
        if self.snippets_file.exists():
            try:
                data = json.loads(self.snippets_file.read_text())
                self.snippets = {k: Snippet(**v) for k, v in data.items()}
            except Exception:
                pass
        
        # Load history (last 1000 commands)
        if self.history_file.exists():
            try:
                self.command_history = json.loads(self.history_file.read_text())[-1000:]
            except Exception:
                pass
    
    def _save_data(self):
        """Save all learning data."""
        try:
            # Save command usage
            self.commands_file.write_text(json.dumps(
                {k: asdict(v) for k, v in self.command_usage.items()},
                indent=2
            ))
            
            # Save patterns
            self.patterns_file.write_text(json.dumps(
                [asdict(p) for p in self.patterns],
                indent=2
            ))
            
            # Save shortcuts
            self.shortcuts_file.write_text(json.dumps(
                {k: asdict(v) for k, v in self.shortcuts.items()},
                indent=2
            ))
            
            # Save snippets
            self.snippets_file.write_text(json.dumps(
                {k: asdict(v) for k, v in self.snippets.items()},
                indent=2
            ))
            
            # Save history
            self.history_file.write_text(json.dumps(self.command_history[-1000:]))
        except Exception:
            pass
    
    # === Command Learning ===
    
    def record_command(self, command: str, success: bool = True, 
                       context: str = "", duration_ms: int = 0):
        """Record a command execution for learning."""
        now = datetime.now()
        hour = now.hour + now.minute / 60.0
        
        # Get or create usage record
        key = self._normalize_command(command)
        if key not in self.command_usage:
            self.command_usage[key] = CommandUsage(command=command)
        
        usage = self.command_usage[key]
        usage.count += 1
        usage.last_used = now.isoformat()
        
        # Update average time of day
        if usage.avg_time_of_day == 0:
            usage.avg_time_of_day = hour
        else:
            usage.avg_time_of_day = (usage.avg_time_of_day * 0.9) + (hour * 0.1)
        
        # Update success rate
        usage.success_rate = (usage.success_rate * 0.95) + (1.0 if success else 0.0) * 0.05
        
        # Track context
        if context and context not in usage.contexts:
            usage.contexts.append(context)
            if len(usage.contexts) > 10:
                usage.contexts = usage.contexts[-10:]
        
        # Track command sequences
        if self.command_history:
            last_cmd = self._normalize_command(self.command_history[-1].get('command', ''))
            if last_cmd in self.command_usage:
                following = self.command_usage[last_cmd].following_commands
                if key not in following:
                    following.append(key)
                    if len(following) > 20:
                        self.command_usage[last_cmd].following_commands = following[-20:]
        
        # Add to history
        self.command_history.append({
            'command': command,
            'timestamp': now.isoformat(),
            'success': success,
            'context': context,
            'duration_ms': duration_ms
        })
        
        # Detect patterns periodically
        if len(self.command_history) % 10 == 0:
            self._detect_patterns()
        
        self._save_data()
    
    def _normalize_command(self, command: str) -> str:
        """Normalize command for comparison."""
        # Remove extra whitespace, lowercase
        cmd = ' '.join(command.lower().split())
        # Remove specific values but keep structure
        # e.g., "search for foo" -> "search for *"
        words = cmd.split()
        if len(words) > 3:
            # Keep first 3 words as pattern
            return ' '.join(words[:3]) + ' ...'
        return cmd
    
    def get_suggestions(self, partial: str = "", context: str = "", 
                        limit: int = 5) -> List[Dict[str, Any]]:
        """Get smart command suggestions."""
        suggestions = []
        now = datetime.now()
        current_hour = now.hour
        
        for key, usage in self.command_usage.items():
            score = 0.0
            
            # Frequency score
            score += min(usage.count / 10.0, 5.0)
            
            # Recency score
            try:
                last = datetime.fromisoformat(usage.last_used)
                days_ago = (now - last).days
                score += max(0, 5 - days_ago)
            except Exception:
                pass
            
            # Time of day score (higher if usually used at this time)
            hour_diff = abs(current_hour - usage.avg_time_of_day)
            if hour_diff > 12:
                hour_diff = 24 - hour_diff
            score += max(0, 3 - hour_diff / 4)
            
            # Partial match score
            if partial:
                if usage.command.lower().startswith(partial.lower()):
                    score += 10
                elif partial.lower() in usage.command.lower():
                    score += 5
            
            # Context match score
            if context and context in usage.contexts:
                score += 3
            
            # Success rate bonus
            score *= usage.success_rate
            
            suggestions.append({
                'command': usage.command,
                'score': score,
                'count': usage.count,
                'last_used': usage.last_used
            })
        
        # Sort by score
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:limit]
    
    def get_next_command_suggestions(self, current_command: str, 
                                     limit: int = 3) -> List[str]:
        """Suggest commands that usually follow the current one."""
        key = self._normalize_command(current_command)
        if key in self.command_usage:
            following = self.command_usage[key].following_commands
            # Sort by frequency in history
            counter = Counter(following)
            return [cmd for cmd, _ in counter.most_common(limit)]
        return []
    
    # === Pattern Detection ===
    
    def _detect_patterns(self):
        """Detect patterns in user behavior."""
        if len(self.command_history) < 20:
            return
        
        # Time-based patterns
        self._detect_time_patterns()
        
        # Command sequence patterns
        self._detect_sequence_patterns()
    
    def _detect_time_patterns(self):
        """Detect time-based usage patterns."""
        # Group commands by hour
        hourly = {}
        for entry in self.command_history[-100:]:
            try:
                ts = datetime.fromisoformat(entry['timestamp'])
                hour = ts.hour
                cmd = self._normalize_command(entry['command'])
                if hour not in hourly:
                    hourly[hour] = []
                hourly[hour].append(cmd)
            except Exception:
                pass
        
        # Find commands consistently used at certain times
        for hour, commands in hourly.items():
            counter = Counter(commands)
            for cmd, count in counter.most_common(3):
                if count >= 3:
                    pattern = UserPattern(
                        pattern_type=PatternType.TIME_BASED.value,
                        pattern_data={'hour': hour, 'command': cmd},
                        confidence=min(count / 10.0, 1.0),
                        occurrences=count,
                        last_seen=datetime.now().isoformat()
                    )
                    self._update_or_add_pattern(pattern)
    
    def _detect_sequence_patterns(self):
        """Detect command sequence patterns."""
        if len(self.command_history) < 10:
            return
        
        # Find common 2-command sequences
        sequences = []
        for i in range(len(self.command_history) - 1):
            cmd1 = self._normalize_command(self.command_history[i]['command'])
            cmd2 = self._normalize_command(self.command_history[i + 1]['command'])
            sequences.append((cmd1, cmd2))
        
        counter = Counter(sequences)
        for (cmd1, cmd2), count in counter.most_common(10):
            if count >= 3 and cmd1 != cmd2:
                pattern = UserPattern(
                    pattern_type=PatternType.SEQUENCE.value,
                    pattern_data={'first': cmd1, 'second': cmd2},
                    confidence=min(count / 10.0, 1.0),
                    occurrences=count,
                    last_seen=datetime.now().isoformat()
                )
                self._update_or_add_pattern(pattern)
    
    def _update_or_add_pattern(self, new_pattern: UserPattern):
        """Update existing pattern or add new one."""
        for i, p in enumerate(self.patterns):
            if (p.pattern_type == new_pattern.pattern_type and 
                p.pattern_data == new_pattern.pattern_data):
                self.patterns[i] = new_pattern
                return
        self.patterns.append(new_pattern)
        if len(self.patterns) > 100:
            self.patterns = self.patterns[-100:]
    
    def get_time_based_suggestions(self) -> List[Dict[str, Any]]:
        """Get suggestions based on current time patterns."""
        current_hour = datetime.now().hour
        suggestions = []
        
        for pattern in self.patterns:
            if pattern.pattern_type == PatternType.TIME_BASED.value:
                hour = pattern.pattern_data.get('hour', -1)
                if abs(hour - current_hour) <= 1:  # Within 1 hour
                    suggestions.append({
                        'command': pattern.pattern_data.get('command', ''),
                        'reason': f"You usually do this around {hour}:00",
                        'confidence': pattern.confidence
                    })
        
        return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)[:3]
    
    # === Shortcuts ===
    
    def add_shortcut(self, name: str, command: str, description: str = "") -> bool:
        """Add a user shortcut."""
        if not name or not command:
            return False
        
        self.shortcuts[name.lower()] = Shortcut(
            name=name,
            command=command,
            description=description,
            created_at=datetime.now().isoformat()
        )
        self._save_data()
        return True
    
    def remove_shortcut(self, name: str) -> bool:
        """Remove a shortcut."""
        if name.lower() in self.shortcuts:
            del self.shortcuts[name.lower()]
            self._save_data()
            return True
        return False
    
    def get_shortcut(self, name: str) -> Optional[str]:
        """Get command for shortcut."""
        shortcut = self.shortcuts.get(name.lower())
        if shortcut:
            shortcut.usage_count += 1
            self._save_data()
            return shortcut.command
        return None
    
    def list_shortcuts(self) -> List[Dict[str, Any]]:
        """List all shortcuts."""
        return [
            {
                'name': s.name,
                'command': s.command,
                'description': s.description,
                'usage_count': s.usage_count
            }
            for s in sorted(self.shortcuts.values(), key=lambda x: -x.usage_count)
        ]
    
    # === Snippets ===
    
    def save_snippet(self, name: str, command: str, description: str = "",
                     tags: List[str] = None) -> str:
        """Save a command snippet."""
        snippet_id = f"snip_{int(time.time() * 1000)}"
        self.snippets[snippet_id] = Snippet(
            id=snippet_id,
            name=name,
            command=command,
            description=description,
            tags=tags or [],
            created_at=datetime.now().isoformat()
        )
        self._save_data()
        return snippet_id
    
    def delete_snippet(self, snippet_id: str) -> bool:
        """Delete a snippet."""
        if snippet_id in self.snippets:
            del self.snippets[snippet_id]
            self._save_data()
            return True
        return False
    
    def get_snippet(self, snippet_id: str) -> Optional[Dict[str, Any]]:
        """Get a snippet."""
        snippet = self.snippets.get(snippet_id)
        if snippet:
            snippet.usage_count += 1
            self._save_data()
            return asdict(snippet)
        return None
    
    def search_snippets(self, query: str = "", tags: List[str] = None) -> List[Dict[str, Any]]:
        """Search snippets."""
        results = []
        query = query.lower()
        
        for snippet in self.snippets.values():
            score = 0
            
            if query:
                if query in snippet.name.lower():
                    score += 10
                if query in snippet.command.lower():
                    score += 5
                if query in snippet.description.lower():
                    score += 3
            else:
                score = snippet.usage_count
            
            if tags:
                for tag in tags:
                    if tag.lower() in [t.lower() for t in snippet.tags]:
                        score += 5
            
            if score > 0 or not query:
                results.append({
                    **asdict(snippet),
                    'score': score
                })
        
        return sorted(results, key=lambda x: -x['score'])
    
    def toggle_favorite(self, snippet_id: str) -> bool:
        """Toggle favorite status of a snippet."""
        if snippet_id in self.snippets:
            self.snippets[snippet_id].is_favorite = not self.snippets[snippet_id].is_favorite
            self._save_data()
            return self.snippets[snippet_id].is_favorite
        return False
    
    def get_favorites(self) -> List[Dict[str, Any]]:
        """Get all favorite snippets."""
        return [
            asdict(s) for s in self.snippets.values() if s.is_favorite
        ]
    
    # === History ===
    
    def search_history(self, query: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """Search command history."""
        query = query.lower()
        results = []
        
        for entry in reversed(self.command_history):
            if not query or query in entry.get('command', '').lower():
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_recent_commands(self, limit: int = 10) -> List[str]:
        """Get recent unique commands."""
        seen = set()
        result = []
        for entry in reversed(self.command_history):
            cmd = entry.get('command', '')
            if cmd and cmd not in seen:
                seen.add(cmd)
                result.append(cmd)
                if len(result) >= limit:
                    break
        return result
    
    def get_most_used_commands(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently used commands."""
        sorted_usage = sorted(
            self.command_usage.items(),
            key=lambda x: x[1].count,
            reverse=True
        )
        return [(u.command, u.count) for _, u in sorted_usage[:limit]]
    
    # === Statistics ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        total_commands = len(self.command_history)
        unique_commands = len(self.command_usage)
        
        # Commands today
        today = datetime.now().date()
        today_count = sum(
            1 for e in self.command_history
            if datetime.fromisoformat(e['timestamp']).date() == today
        )
        
        return {
            'total_commands': total_commands,
            'unique_commands': unique_commands,
            'commands_today': today_count,
            'shortcuts_count': len(self.shortcuts),
            'snippets_count': len(self.snippets),
            'patterns_detected': len(self.patterns),
            'favorites_count': len(self.get_favorites())
        }


# Global instance
_learning_system: Optional[SmartLearningSystem] = None


def get_learning_system() -> SmartLearningSystem:
    """Get the global learning system instance."""
    global _learning_system
    if _learning_system is None:
        _learning_system = SmartLearningSystem()
    return _learning_system
