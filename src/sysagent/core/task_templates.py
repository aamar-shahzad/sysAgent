"""
Task Templates System for SysAgent.
Pre-built templates for common multi-step tasks.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime


@dataclass
class TaskStep:
    """A single step in a task template."""
    name: str
    command: str
    description: str = ""
    wait_ms: int = 0
    required: bool = True
    on_error: str = "stop"  # "stop", "continue", "retry"
    max_retries: int = 1


@dataclass
class TaskTemplate:
    """A template for a multi-step task."""
    id: str
    name: str
    description: str
    category: str
    icon: str
    steps: List[TaskStep] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)  # Placeholders
    created_at: str = ""
    is_builtin: bool = False


class TaskTemplateManager:
    """
    Manages task templates - both built-in and user-created.
    """
    
    def __init__(self):
        self._templates: Dict[str, TaskTemplate] = {}
        self._templates_dir = Path.home() / ".sysagent" / "templates"
        self._templates_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_builtin_templates()
        self._load_user_templates()
    
    def _load_builtin_templates(self):
        """Load built-in templates."""
        builtin = [
            # Morning Routine
            TaskTemplate(
                id="morning_routine",
                name="Morning Routine",
                description="Start your day with a quick system check and email overview",
                category="productivity",
                icon="🌅",
                steps=[
                    TaskStep("Check System Health", "check system health", "Run system diagnostics", 0),
                    TaskStep("Show Calendar", "open calendar", "View today's schedule", 1000),
                    TaskStep("Check Emails", "open email", "View unread emails", 1000),
                    TaskStep("Show Weather", "show weather", "Get weather forecast", 500),
                ],
                tags=["morning", "routine", "productivity"],
                is_builtin=True
            ),
            
            # Dev Setup
            TaskTemplate(
                id="dev_setup",
                name="Development Setup",
                description="Set up your development environment",
                category="development",
                icon="💻",
                steps=[
                    TaskStep("Open Code Editor", "open VS Code", "Launch your code editor", 2000),
                    TaskStep("Open Terminal", "open terminal", "Launch terminal", 1000),
                    TaskStep("Git Status", "git status", "Check repository status", 500),
                    TaskStep("Run Dev Server", "npm run dev", "Start development server", 0, required=False),
                ],
                tags=["development", "coding", "setup"],
                is_builtin=True
            ),
            
            # System Cleanup
            TaskTemplate(
                id="system_cleanup",
                name="System Cleanup",
                description="Clean up temp files and optimize system",
                category="system",
                icon="🧹",
                steps=[
                    TaskStep("Clean Temp Files", "clean temp files", "Remove temporary files", 0),
                    TaskStep("Empty Trash", "empty trash", "Clear recycle bin", 1000),
                    TaskStep("Clear Browser Cache", "clear browser cache", "Remove browser cache", 1000),
                    TaskStep("Analyze Disk", "analyze disk usage", "Show disk usage summary", 500),
                ],
                tags=["cleanup", "system", "maintenance"],
                is_builtin=True
            ),
            
            # Security Audit
            TaskTemplate(
                id="security_audit",
                name="Security Audit",
                description="Run security checks on your system",
                category="security",
                icon="🔒",
                steps=[
                    TaskStep("Check Open Ports", "check open ports", "Scan for open network ports", 0),
                    TaskStep("Review Permissions", "review permissions", "Check file permissions", 1000),
                    TaskStep("Check Updates", "check for updates", "Look for security updates", 1000),
                    TaskStep("Scan for Issues", "security scan", "Run security scanner", 2000),
                ],
                tags=["security", "audit", "protection"],
                is_builtin=True
            ),
            
            # Meeting Prep
            TaskTemplate(
                id="meeting_prep",
                name="Meeting Preparation",
                description="Prepare for a meeting",
                category="productivity",
                icon="📅",
                steps=[
                    TaskStep("Open Calendar", "open calendar", "View meeting details", 1000),
                    TaskStep("Open Notes", "open notes", "Review meeting notes", 1000),
                    TaskStep("Test Microphone", "test microphone", "Check audio input", 500),
                    TaskStep("Test Camera", "test camera", "Check video", 500),
                    TaskStep("Close Background Apps", "close background apps", "Reduce distractions", 1000),
                ],
                tags=["meeting", "video call", "preparation"],
                is_builtin=True
            ),
            
            # End of Day
            TaskTemplate(
                id="end_of_day",
                name="End of Day",
                description="Wrap up your work day",
                category="productivity",
                icon="🌙",
                steps=[
                    TaskStep("Save All Work", "save all", "Save open documents", 500),
                    TaskStep("Git Commit", "git commit -m 'EOD checkpoint'", "Commit changes", 1000),
                    TaskStep("Check Tomorrow's Calendar", "show tomorrow's calendar", "Preview tomorrow", 500),
                    TaskStep("Clean Downloads", "organize downloads", "Tidy up downloads folder", 1000),
                    TaskStep("System Status", "show system status", "Final health check", 500),
                ],
                tags=["evening", "cleanup", "productivity"],
                is_builtin=True
            ),
            
            # Quick Screenshot Workflow
            TaskTemplate(
                id="screenshot_workflow",
                name="Screenshot & Share",
                description="Take a screenshot and share it",
                category="media",
                icon="📸",
                steps=[
                    TaskStep("Take Screenshot", "take screenshot", "Capture screen", 0),
                    TaskStep("Open in Editor", "open screenshot in editor", "Edit if needed", 1000, required=False),
                    TaskStep("Copy to Clipboard", "copy screenshot to clipboard", "Ready to paste", 500),
                ],
                tags=["screenshot", "share", "quick"],
                is_builtin=True
            ),
            
            # Research Mode
            TaskTemplate(
                id="research_mode",
                name="Research Mode",
                description="Set up for focused research",
                category="productivity",
                icon="🔬",
                steps=[
                    TaskStep("Open Browser", "open browser", "Launch web browser", 1000),
                    TaskStep("Open Notes App", "open notes", "For taking notes", 1000),
                    TaskStep("Enable Focus Mode", "enable focus mode", "Block distractions", 500),
                    TaskStep("Set Timer", "set timer for 25 minutes", "Pomodoro timer", 0),
                ],
                tags=["research", "focus", "productivity"],
                is_builtin=True
            ),
            
            # File Backup
            TaskTemplate(
                id="file_backup",
                name="File Backup",
                description="Backup important files",
                category="system",
                icon="💾",
                steps=[
                    TaskStep("Check Backup Drive", "check backup drive", "Verify drive connected", 0),
                    TaskStep("Backup Documents", "backup documents folder", "Copy documents", 2000),
                    TaskStep("Backup Desktop", "backup desktop folder", "Copy desktop files", 2000),
                    TaskStep("Verify Backup", "verify backup", "Check integrity", 1000),
                    TaskStep("Show Summary", "show backup summary", "Display results", 0),
                ],
                tags=["backup", "files", "safety"],
                variables={"backup_path": "/Volumes/Backup"},
                is_builtin=True
            ),
            
            # Quick Notes
            TaskTemplate(
                id="quick_notes",
                name="Quick Notes",
                description="Quickly capture thoughts",
                category="productivity",
                icon="📝",
                steps=[
                    TaskStep("Create Note", "create note titled '{title}'", "New note", 0),
                    TaskStep("Open Note", "open the note", "Ready to type", 500),
                ],
                tags=["notes", "quick", "capture"],
                variables={"title": "Quick Note"},
                is_builtin=True
            ),
        ]
        
        for template in builtin:
            self._templates[template.id] = template
    
    def _load_user_templates(self):
        """Load user-created templates from disk."""
        for file in self._templates_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                steps = [TaskStep(**s) for s in data.get("steps", [])]
                template = TaskTemplate(
                    id=data["id"],
                    name=data["name"],
                    description=data.get("description", ""),
                    category=data.get("category", "custom"),
                    icon=data.get("icon", "📋"),
                    steps=steps,
                    tags=data.get("tags", []),
                    variables=data.get("variables", {}),
                    created_at=data.get("created_at", ""),
                    is_builtin=False
                )
                self._templates[template.id] = template
            except Exception:
                pass
    
    def save_template(self, template: TaskTemplate):
        """Save a user template to disk."""
        if template.is_builtin:
            return  # Don't save built-in templates
        
        file_path = self._templates_dir / f"{template.id}.json"
        data = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "icon": template.icon,
            "steps": [asdict(s) for s in template.steps],
            "tags": template.tags,
            "variables": template.variables,
            "created_at": template.created_at or datetime.now().isoformat()
        }
        file_path.write_text(json.dumps(data, indent=2))
        self._templates[template.id] = template
    
    def get_template(self, template_id: str) -> Optional[TaskTemplate]:
        """Get a template by ID."""
        return self._templates.get(template_id)
    
    def list_templates(self, category: str = None) -> List[TaskTemplate]:
        """List all templates, optionally filtered by category."""
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return sorted(templates, key=lambda x: (not x.is_builtin, x.name))
    
    def search_templates(self, query: str) -> List[TaskTemplate]:
        """Search templates by name, description, or tags."""
        query = query.lower()
        results = []
        
        for template in self._templates.values():
            if (query in template.name.lower() or 
                query in template.description.lower() or
                any(query in tag.lower() for tag in template.tags)):
                results.append(template)
        
        return results
    
    def get_categories(self) -> List[str]:
        """Get all template categories."""
        categories = set()
        for template in self._templates.values():
            categories.add(template.category)
        return sorted(list(categories))
    
    def create_template(
        self,
        name: str,
        description: str,
        category: str,
        steps: List[Dict[str, Any]],
        icon: str = "📋",
        tags: List[str] = None,
        variables: Dict[str, str] = None
    ) -> TaskTemplate:
        """Create a new user template."""
        template_id = name.lower().replace(" ", "_")
        
        # Ensure unique ID
        counter = 1
        original_id = template_id
        while template_id in self._templates:
            template_id = f"{original_id}_{counter}"
            counter += 1
        
        template_steps = [TaskStep(**s) for s in steps]
        
        template = TaskTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            icon=icon,
            steps=template_steps,
            tags=tags or [],
            variables=variables or {},
            created_at=datetime.now().isoformat(),
            is_builtin=False
        )
        
        self.save_template(template)
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a user template."""
        template = self._templates.get(template_id)
        if not template or template.is_builtin:
            return False
        
        del self._templates[template_id]
        file_path = self._templates_dir / f"{template_id}.json"
        if file_path.exists():
            file_path.unlink()
        return True
    
    def duplicate_template(self, template_id: str, new_name: str) -> Optional[TaskTemplate]:
        """Duplicate a template with a new name."""
        original = self._templates.get(template_id)
        if not original:
            return None
        
        return self.create_template(
            name=new_name,
            description=original.description,
            category=original.category,
            steps=[asdict(s) for s in original.steps],
            icon=original.icon,
            tags=original.tags.copy(),
            variables=original.variables.copy()
        )


# Singleton instance
_template_manager: Optional[TaskTemplateManager] = None


def get_template_manager() -> TaskTemplateManager:
    """Get or create the template manager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = TaskTemplateManager()
    return _template_manager
