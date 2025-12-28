"""
Macro Recording and Playback Tool for SysAgent.
Record and replay sequences of actions.
"""

import json
import time
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory


@dataclass
class MacroStep:
    """A single step in a macro."""
    action_type: str  # "keyboard", "mouse", "command", "wait"
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    delay_ms: int = 0


@dataclass
class Macro:
    """A recorded macro."""
    name: str
    description: str = ""
    steps: List[MacroStep] = field(default_factory=list)
    created_at: str = ""
    last_run: Optional[str] = None
    run_count: int = 0
    tags: List[str] = field(default_factory=list)


@register_tool
class MacroTool(BaseTool):
    """Tool for recording and playing back macros."""
    
    _macros: Dict[str, Macro] = {}
    _is_recording: bool = False
    _current_recording: Optional[Macro] = None
    _recording_start_time: float = 0.0
    _last_step_time: float = 0.0
    _macros_dir: Path = Path.home() / ".sysagent" / "macros"
    
    def __init__(self):
        super().__init__()
        self._macros_dir.mkdir(parents=True, exist_ok=True)
        self._load_macros()
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="macro_tool",
            description="Record and playback macros - sequences of actions",
            category=ToolCategory.AUTOMATION,
            permissions=["automation"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "start_recording": self._start_recording,
                "stop_recording": self._stop_recording,
                "add_step": self._add_step,
                "play": self._play_macro,
                "list": self._list_macros,
                "get": self._get_macro,
                "delete": self._delete_macro,
                "edit": self._edit_macro,
                "export": self._export_macro,
                "import": self._import_macro,
                "templates": self._get_templates,
                "create_from_template": self._create_from_template,
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
                message=f"Macro operation failed: {str(e)}",
                error=str(e)
            )

    def _load_macros(self):
        """Load saved macros from disk."""
        for file in self._macros_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                steps = [MacroStep(**s) for s in data.get("steps", [])]
                macro = Macro(
                    name=data["name"],
                    description=data.get("description", ""),
                    steps=steps,
                    created_at=data.get("created_at", ""),
                    last_run=data.get("last_run"),
                    run_count=data.get("run_count", 0),
                    tags=data.get("tags", [])
                )
                self._macros[macro.name] = macro
            except Exception:
                pass

    def _save_macro(self, macro: Macro):
        """Save a macro to disk."""
        file_path = self._macros_dir / f"{macro.name}.json"
        data = {
            "name": macro.name,
            "description": macro.description,
            "steps": [asdict(s) for s in macro.steps],
            "created_at": macro.created_at,
            "last_run": macro.last_run,
            "run_count": macro.run_count,
            "tags": macro.tags
        }
        file_path.write_text(json.dumps(data, indent=2))

    def _start_recording(self, **kwargs) -> ToolResult:
        """Start recording a new macro."""
        name = kwargs.get("name", f"macro_{int(time.time())}")
        description = kwargs.get("description", "")
        
        if self._is_recording:
            return ToolResult(
                success=False,
                data={},
                message="Already recording a macro. Stop the current recording first."
            )
        
        self._is_recording = True
        self._recording_start_time = time.time()
        self._last_step_time = self._recording_start_time
        self._current_recording = Macro(
            name=name,
            description=description,
            created_at=datetime.now().isoformat()
        )
        
        return ToolResult(
            success=True,
            data={"name": name},
            message=f"Started recording macro: {name}"
        )

    def _stop_recording(self, **kwargs) -> ToolResult:
        """Stop recording and save the macro."""
        if not self._is_recording or not self._current_recording:
            return ToolResult(
                success=False,
                data={},
                message="No recording in progress"
            )
        
        macro = self._current_recording
        self._macros[macro.name] = macro
        self._save_macro(macro)
        
        self._is_recording = False
        self._current_recording = None
        
        return ToolResult(
            success=True,
            data={
                "name": macro.name,
                "step_count": len(macro.steps),
                "duration_ms": sum(s.delay_ms for s in macro.steps)
            },
            message=f"Macro '{macro.name}' saved with {len(macro.steps)} steps"
        )

    def _add_step(self, **kwargs) -> ToolResult:
        """Add a step to the current recording."""
        if not self._is_recording or not self._current_recording:
            return ToolResult(
                success=False,
                data={},
                message="No recording in progress"
            )
        
        step_type = kwargs.get("type", "command")
        params = kwargs.get("params", {})
        
        current_time = time.time()
        delay_ms = int((current_time - self._last_step_time) * 1000)
        self._last_step_time = current_time
        
        step = MacroStep(
            action_type=step_type,
            params=params,
            timestamp=current_time - self._recording_start_time,
            delay_ms=delay_ms
        )
        
        self._current_recording.steps.append(step)
        
        return ToolResult(
            success=True,
            data={"step_number": len(self._current_recording.steps)},
            message=f"Added step {len(self._current_recording.steps)}"
        )

    def _play_macro(self, **kwargs) -> ToolResult:
        """Play back a recorded macro."""
        name = kwargs.get("name", "")
        speed = kwargs.get("speed", 1.0)  # 1.0 = normal, 2.0 = 2x faster
        
        if not name:
            return ToolResult(
                success=False,
                data={},
                message="Macro name required"
            )
        
        if name not in self._macros:
            return ToolResult(
                success=False,
                data={"available_macros": list(self._macros.keys())},
                message=f"Macro not found: {name}"
            )
        
        macro = self._macros[name]
        results = []
        
        for i, step in enumerate(macro.steps):
            # Wait for delay
            delay = step.delay_ms / 1000 / speed
            if delay > 0:
                time.sleep(delay)
            
            # Execute step
            try:
                result = self._execute_step(step)
                results.append({"step": i + 1, "success": True, "result": result})
            except Exception as e:
                results.append({"step": i + 1, "success": False, "error": str(e)})
        
        # Update run stats
        macro.last_run = datetime.now().isoformat()
        macro.run_count += 1
        self._save_macro(macro)
        
        return ToolResult(
            success=True,
            data={
                "name": name,
                "steps_executed": len(results),
                "results": results
            },
            message=f"Executed macro '{name}' ({len(macro.steps)} steps)"
        )

    def _execute_step(self, step: MacroStep) -> str:
        """Execute a single macro step."""
        from .keyboard_mouse_tool import KeyboardMouseTool
        
        if step.action_type == "keyboard":
            tool = KeyboardMouseTool()
            action = step.params.get("action", "type")
            result = tool._execute(action, **step.params)
            return result.message
        
        elif step.action_type == "mouse":
            tool = KeyboardMouseTool()
            action = step.params.get("action", "click")
            result = tool._execute(action, **step.params)
            return result.message
        
        elif step.action_type == "wait":
            duration = step.params.get("duration_ms", 1000)
            time.sleep(duration / 1000)
            return f"Waited {duration}ms"
        
        elif step.action_type == "command":
            # This would integrate with the main agent
            return f"Command: {step.params.get('command', '')}"
        
        return "Unknown step type"

    def _list_macros(self, **kwargs) -> ToolResult:
        """List all saved macros."""
        macros_list = []
        for name, macro in self._macros.items():
            macros_list.append({
                "name": name,
                "description": macro.description,
                "steps": len(macro.steps),
                "run_count": macro.run_count,
                "last_run": macro.last_run,
                "tags": macro.tags
            })
        
        return ToolResult(
            success=True,
            data={"macros": macros_list},
            message=f"Found {len(macros_list)} macros"
        )

    def _get_macro(self, **kwargs) -> ToolResult:
        """Get details of a specific macro."""
        name = kwargs.get("name", "")
        
        if name not in self._macros:
            return ToolResult(
                success=False,
                data={},
                message=f"Macro not found: {name}"
            )
        
        macro = self._macros[name]
        
        return ToolResult(
            success=True,
            data={
                "name": macro.name,
                "description": macro.description,
                "steps": [asdict(s) for s in macro.steps],
                "created_at": macro.created_at,
                "run_count": macro.run_count,
                "tags": macro.tags
            },
            message=f"Macro: {name}"
        )

    def _delete_macro(self, **kwargs) -> ToolResult:
        """Delete a macro."""
        name = kwargs.get("name", "")
        
        if name not in self._macros:
            return ToolResult(
                success=False,
                data={},
                message=f"Macro not found: {name}"
            )
        
        del self._macros[name]
        file_path = self._macros_dir / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
        
        return ToolResult(
            success=True,
            data={"deleted": name},
            message=f"Deleted macro: {name}"
        )

    def _edit_macro(self, **kwargs) -> ToolResult:
        """Edit a macro's metadata."""
        name = kwargs.get("name", "")
        
        if name not in self._macros:
            return ToolResult(
                success=False,
                data={},
                message=f"Macro not found: {name}"
            )
        
        macro = self._macros[name]
        
        if "description" in kwargs:
            macro.description = kwargs["description"]
        if "tags" in kwargs:
            macro.tags = kwargs["tags"]
        
        self._save_macro(macro)
        
        return ToolResult(
            success=True,
            data={"name": name},
            message=f"Updated macro: {name}"
        )

    def _export_macro(self, **kwargs) -> ToolResult:
        """Export a macro to a file."""
        name = kwargs.get("name", "")
        path = kwargs.get("path", "")
        
        if name not in self._macros:
            return ToolResult(
                success=False,
                data={},
                message=f"Macro not found: {name}"
            )
        
        macro = self._macros[name]
        
        if not path:
            path = str(Path.home() / f"{name}_macro.json")
        
        data = {
            "name": macro.name,
            "description": macro.description,
            "steps": [asdict(s) for s in macro.steps],
            "tags": macro.tags
        }
        
        Path(path).write_text(json.dumps(data, indent=2))
        
        return ToolResult(
            success=True,
            data={"path": path},
            message=f"Exported macro to: {path}"
        )

    def _import_macro(self, **kwargs) -> ToolResult:
        """Import a macro from a file."""
        path = kwargs.get("path", "")
        
        if not path or not Path(path).exists():
            return ToolResult(
                success=False,
                data={},
                message=f"File not found: {path}"
            )
        
        try:
            data = json.loads(Path(path).read_text())
            steps = [MacroStep(**s) for s in data.get("steps", [])]
            
            macro = Macro(
                name=data["name"],
                description=data.get("description", ""),
                steps=steps,
                created_at=datetime.now().isoformat(),
                tags=data.get("tags", [])
            )
            
            self._macros[macro.name] = macro
            self._save_macro(macro)
            
            return ToolResult(
                success=True,
                data={"name": macro.name, "steps": len(steps)},
                message=f"Imported macro: {macro.name}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Import failed: {str(e)}"
            )

    def _get_templates(self, **kwargs) -> ToolResult:
        """Get available macro templates."""
        templates = [
            {
                "name": "open_and_type",
                "description": "Open an app and type text",
                "steps": [
                    {"action_type": "command", "params": {"command": "open app"}, "delay_ms": 0},
                    {"action_type": "wait", "params": {"duration_ms": 1000}, "delay_ms": 1000},
                    {"action_type": "keyboard", "params": {"action": "type", "text": "Hello"}, "delay_ms": 0}
                ]
            },
            {
                "name": "screenshot_and_save",
                "description": "Take a screenshot and save it",
                "steps": [
                    {"action_type": "command", "params": {"command": "take screenshot"}, "delay_ms": 0}
                ]
            },
            {
                "name": "quick_search",
                "description": "Open browser and search",
                "steps": [
                    {"action_type": "command", "params": {"command": "open browser"}, "delay_ms": 0},
                    {"action_type": "wait", "params": {"duration_ms": 1500}, "delay_ms": 1500},
                    {"action_type": "keyboard", "params": {"action": "hotkey", "shortcut": "cmd+l"}, "delay_ms": 0},
                    {"action_type": "keyboard", "params": {"action": "type", "text": "search query"}, "delay_ms": 100},
                    {"action_type": "keyboard", "params": {"action": "key", "key": "enter"}, "delay_ms": 100}
                ]
            }
        ]
        
        return ToolResult(
            success=True,
            data={"templates": templates},
            message=f"Found {len(templates)} templates"
        )

    def _create_from_template(self, **kwargs) -> ToolResult:
        """Create a macro from a template."""
        template_name = kwargs.get("template", "")
        new_name = kwargs.get("name", "")
        
        templates_result = self._get_templates()
        templates = templates_result.data.get("templates", [])
        
        template = None
        for t in templates:
            if t["name"] == template_name:
                template = t
                break
        
        if not template:
            return ToolResult(
                success=False,
                data={},
                message=f"Template not found: {template_name}"
            )
        
        name = new_name or f"{template_name}_{int(time.time())}"
        steps = [MacroStep(**s) for s in template["steps"]]
        
        macro = Macro(
            name=name,
            description=template["description"],
            steps=steps,
            created_at=datetime.now().isoformat()
        )
        
        self._macros[name] = macro
        self._save_macro(macro)
        
        return ToolResult(
            success=True,
            data={"name": name, "steps": len(steps)},
            message=f"Created macro '{name}' from template '{template_name}'"
        )

    def get_usage_examples(self) -> List[str]:
        return [
            "Start recording: macro_tool --action start_recording --name my_macro",
            "Stop recording: macro_tool --action stop_recording",
            "Play macro: macro_tool --action play --name my_macro",
            "List macros: macro_tool --action list",
            "Get templates: macro_tool --action templates",
        ]
