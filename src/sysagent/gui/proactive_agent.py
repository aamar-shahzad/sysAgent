"""
Proactive Agent for SysAgent - Monitors system state and provides intelligent suggestions.
"""

import threading
import time
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime
import psutil


class ProactiveSuggestion:
    """Represents a proactive suggestion."""
    
    def __init__(self, 
                 title: str, 
                 message: str, 
                 action: Optional[str] = None,
                 priority: str = "low",
                 category: str = "general",
                 icon: str = "💡"):
        self.title = title
        self.message = message
        self.action = action  # Command to execute
        self.priority = priority  # low, medium, high
        self.category = category
        self.icon = icon
        self.timestamp = datetime.now()
        self.dismissed = False


class ProactiveAgent:
    """
    Monitors system state and generates proactive suggestions.
    Runs in background and calls callback when suggestions are available.
    """
    
    def __init__(self, callback: Optional[Callable[[ProactiveSuggestion], None]] = None):
        self.callback = callback
        self.running = False
        self.check_interval = 60  # seconds
        self.thread: Optional[threading.Thread] = None
        self.last_suggestions: Dict[str, datetime] = {}  # Prevent spam
        self.cooldown = 300  # 5 minute cooldown per suggestion type
        
    def start(self):
        """Start the proactive agent."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop the proactive agent."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _can_suggest(self, suggestion_type: str) -> bool:
        """Check if we can make this suggestion (cooldown)."""
        if suggestion_type not in self.last_suggestions:
            return True
        
        elapsed = (datetime.now() - self.last_suggestions[suggestion_type]).seconds
        return elapsed > self.cooldown
    
    def _emit_suggestion(self, suggestion: ProactiveSuggestion):
        """Emit a suggestion if allowed."""
        key = f"{suggestion.category}:{suggestion.title}"
        
        if not self._can_suggest(key):
            return
        
        self.last_suggestions[key] = datetime.now()
        
        if self.callback:
            try:
                self.callback(suggestion)
            except Exception:
                pass
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self._check_system_state()
                self._check_time_based()
            except Exception:
                pass
            
            time.sleep(self.check_interval)
    
    def _check_system_state(self):
        """Check system state and generate suggestions."""
        
        # Check CPU
        cpu = psutil.cpu_percent(interval=1)
        if cpu > 85:
            self._emit_suggestion(ProactiveSuggestion(
                title="High CPU Usage",
                message=f"CPU usage is at {cpu:.0f}%. Want me to show what's using it?",
                action="Show me the top CPU-consuming processes",
                priority="high",
                category="system",
                icon="🔥"
            ))
        
        # Check Memory
        mem = psutil.virtual_memory()
        if mem.percent > 85:
            self._emit_suggestion(ProactiveSuggestion(
                title="High Memory Usage",
                message=f"Memory is at {mem.percent:.0f}%. Consider closing some apps.",
                action="Show me memory usage by application",
                priority="high",
                category="system",
                icon="💾"
            ))
        
        # Check Disk
        try:
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                free_gb = disk.free / (1024**3)
                self._emit_suggestion(ProactiveSuggestion(
                    title="Low Disk Space",
                    message=f"Only {free_gb:.1f} GB free. Need help cleaning up?",
                    action="Help me find large files to clean up",
                    priority="high",
                    category="storage",
                    icon="💿"
                ))
        except:
            pass
        
        # Check Battery
        try:
            battery = psutil.sensors_battery()
            if battery:
                if battery.percent < 20 and not battery.power_plugged:
                    self._emit_suggestion(ProactiveSuggestion(
                        title="Low Battery",
                        message=f"Battery at {battery.percent}%. Connect charger soon!",
                        action=None,
                        priority="high",
                        category="power",
                        icon="🔋"
                    ))
        except:
            pass
    
    def _check_time_based(self):
        """Generate time-based suggestions."""
        hour = datetime.now().hour
        weekday = datetime.now().weekday()
        
        # Morning suggestions (weekdays)
        if 8 <= hour < 9 and weekday < 5:
            self._emit_suggestion(ProactiveSuggestion(
                title="Good Morning!",
                message="Ready to start the day? I can run your morning routine.",
                action="Run my morning routine workflow",
                priority="low",
                category="routine",
                icon="☀️"
            ))
        
        # Lunch break
        if 12 <= hour < 13:
            self._emit_suggestion(ProactiveSuggestion(
                title="Lunch Time",
                message="Taking a break? Want me to save your work?",
                action="Save all my work and check git status",
                priority="low",
                category="routine",
                icon="🍽️"
            ))
        
        # End of day
        if 17 <= hour < 18 and weekday < 5:
            self._emit_suggestion(ProactiveSuggestion(
                title="Wrapping Up?",
                message="End of workday. Need help with end-of-day tasks?",
                action="Run end of day workflow",
                priority="low",
                category="routine",
                icon="🌅"
            ))
        
        # Weekend
        if weekday >= 5 and 10 <= hour < 11:
            self._emit_suggestion(ProactiveSuggestion(
                title="Weekend Maintenance",
                message="Good time for system maintenance?",
                action="Run system maintenance checks",
                priority="low",
                category="maintenance",
                icon="🔧"
            ))
    
    def get_instant_suggestions(self) -> List[ProactiveSuggestion]:
        """Get immediate suggestions based on current state."""
        suggestions = []
        
        # Quick system check
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        
        if cpu < 30 and mem.percent < 50:
            suggestions.append(ProactiveSuggestion(
                title="System Running Smoothly",
                message="Your system is performing well! 👍",
                action=None,
                priority="low",
                category="status",
                icon="✅"
            ))
        
        # Time-based
        hour = datetime.now().hour
        if hour < 6:
            suggestions.append(ProactiveSuggestion(
                title="Late Night",
                message="Working late? Remember to take breaks!",
                action=None,
                priority="low",
                category="wellness",
                icon="🌙"
            ))
        
        # Git status check
        suggestions.append(ProactiveSuggestion(
            title="Check Git Status",
            message="Want to see if you have uncommitted changes?",
            action="Show my git status",
            priority="low",
            category="dev",
            icon="📝"
        ))
        
        return suggestions[:3]


class SmartAssistant:
    """
    Smart assistant that learns from user behavior and provides
    contextual help and suggestions.
    """
    
    def __init__(self):
        self.command_patterns = {}
        self.time_patterns = {}
        self.error_patterns = {}
        
    def learn_from_command(self, command: str, success: bool, context: Dict = None):
        """Learn from a command execution."""
        hour = datetime.now().hour
        
        # Track command frequency by time
        if hour not in self.time_patterns:
            self.time_patterns[hour] = {}
        
        cmd_key = command[:50]  # First 50 chars as key
        if cmd_key not in self.time_patterns[hour]:
            self.time_patterns[hour][cmd_key] = 0
        self.time_patterns[hour][cmd_key] += 1
        
        # Track errors
        if not success:
            if cmd_key not in self.error_patterns:
                self.error_patterns[cmd_key] = []
            self.error_patterns[cmd_key].append({
                "context": context,
                "time": datetime.now().isoformat()
            })
    
    def get_contextual_suggestions(self) -> List[str]:
        """Get suggestions based on learned patterns."""
        suggestions = []
        current_hour = datetime.now().hour
        
        # Find patterns for current time
        if current_hour in self.time_patterns:
            patterns = self.time_patterns[current_hour]
            sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
            
            for cmd, count in sorted_patterns[:3]:
                if count > 2:  # Only suggest if done at least 3 times
                    suggestions.append(f"You often run: {cmd}")
        
        return suggestions
    
    def should_warn(self, command: str) -> Optional[str]:
        """Check if we should warn about a command."""
        cmd_key = command[:50]
        
        if cmd_key in self.error_patterns:
            errors = self.error_patterns[cmd_key]
            if len(errors) > 2:
                return f"This command has failed {len(errors)} times recently. Want me to help troubleshoot?"
        
        return None
