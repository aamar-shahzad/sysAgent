"""
Document tool for SysAgent CLI - Create and manage documents, notes, and text files.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class DocumentTool(BaseTool):
    """Tool for creating and managing documents, notes, and text files."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="document_tool",
            description="Create, edit, and manage documents, notes, and text files",
            category=ToolCategory.FILE,
            permissions=["file_access", "app_control"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "create": self._create_document,
                "create_note": self._create_note,
                "edit": self._edit_document,
                "read": self._read_document,
                "append": self._append_to_document,
                "open": self._open_document,
                "list_notes": self._list_notes,
                "search_notes": self._search_notes,
                "create_from_template": self._create_from_template,
                "to_pdf": self._convert_to_pdf,
            }
            
            if action in actions:
                return actions[action](**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown action: {action}",
                    error=f"Supported actions: {list(actions.keys())}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Document operation failed: {str(e)}",
                error=str(e)
            )

    def _get_notes_dir(self) -> Path:
        """Get the notes directory."""
        notes_dir = Path.home() / ".sysagent" / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        return notes_dir

    def _create_document(self, **kwargs) -> ToolResult:
        """Create a new document."""
        path = kwargs.get("path")
        content = kwargs.get("content", "")
        title = kwargs.get("title", "")
        doc_type = kwargs.get("type", "txt")  # txt, md, html, rtf
        
        if not path:
            # Generate path from title
            if title:
                safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
                safe_title = safe_title.replace(" ", "_")
                path = str(Path.home() / "Documents" / f"{safe_title}.{doc_type}")
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = str(Path.home() / "Documents" / f"document_{timestamp}.{doc_type}")
        
        try:
            # Ensure directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            # Add title as header if provided
            if title and doc_type == "md":
                content = f"# {title}\n\n{content}"
            elif title and doc_type == "html":
                content = f"<!DOCTYPE html>\n<html>\n<head><title>{title}</title></head>\n<body>\n<h1>{title}</h1>\n{content}\n</body>\n</html>"
            elif title and not content:
                content = f"{title}\n{'='*len(title)}\n\n"
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                data={"path": path, "title": title, "type": doc_type, "size": len(content)},
                message=f"Document created: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to create document: {str(e)}",
                error=str(e)
            )

    def _create_note(self, **kwargs) -> ToolResult:
        """Create a quick note."""
        content = kwargs.get("content") or kwargs.get("text") or kwargs.get("note")
        title = kwargs.get("title", "")
        tags = kwargs.get("tags", [])
        
        if not content:
            return ToolResult(
                success=False,
                data={},
                message="No content provided for note",
                error="Missing content"
            )
        
        try:
            notes_dir = self._get_notes_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if title:
                safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
                filename = f"{safe_title}_{timestamp}.md"
            else:
                filename = f"note_{timestamp}.md"
            
            note_path = notes_dir / filename
            
            # Create note with metadata
            note_content = f"""---
title: {title or 'Untitled Note'}
created: {datetime.now().isoformat()}
tags: {', '.join(tags) if tags else 'none'}
---

{content}
"""
            
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(note_content)
            
            # Also save to notes index
            self._update_notes_index(str(note_path), title, tags)
            
            return ToolResult(
                success=True,
                data={
                    "path": str(note_path),
                    "title": title,
                    "tags": tags,
                    "created": datetime.now().isoformat()
                },
                message=f"Note created: {filename}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to create note: {str(e)}",
                error=str(e)
            )

    def _update_notes_index(self, path: str, title: str, tags: List[str]):
        """Update the notes index file."""
        index_file = self._get_notes_dir() / "index.json"
        
        index = []
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    index = json.load(f)
            except:
                pass
        
        index.append({
            "path": path,
            "title": title,
            "tags": tags,
            "created": datetime.now().isoformat()
        })
        
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)

    def _edit_document(self, **kwargs) -> ToolResult:
        """Edit an existing document."""
        path = kwargs.get("path")
        content = kwargs.get("content")
        append = kwargs.get("append", False)
        
        if not path:
            return ToolResult(
                success=False,
                data={},
                message="No file path provided",
                error="Missing path"
            )
        
        if not Path(path).exists():
            return ToolResult(
                success=False,
                data={},
                message=f"File not found: {path}",
                error="File not found"
            )
        
        try:
            if append and content:
                with open(path, 'a', encoding='utf-8') as f:
                    f.write("\n" + content)
            elif content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return ToolResult(
                success=True,
                data={"path": path, "action": "append" if append else "replace"},
                message=f"Document updated: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to edit document: {str(e)}",
                error=str(e)
            )

    def _read_document(self, **kwargs) -> ToolResult:
        """Read a document's contents."""
        path = kwargs.get("path")
        
        if not path:
            return ToolResult(
                success=False,
                data={},
                message="No file path provided",
                error="Missing path"
            )
        
        if not Path(path).exists():
            return ToolResult(
                success=False,
                data={},
                message=f"File not found: {path}",
                error="File not found"
            )
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "content": content,
                    "size": len(content),
                    "lines": content.count('\n') + 1
                },
                message=f"Read document: {path} ({len(content)} chars)"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to read document: {str(e)}",
                error=str(e)
            )

    def _append_to_document(self, **kwargs) -> ToolResult:
        """Append content to a document."""
        kwargs['append'] = True
        return self._edit_document(**kwargs)

    def _open_document(self, **kwargs) -> ToolResult:
        """Open a document in the default application."""
        path = kwargs.get("path")
        app = kwargs.get("app")  # Optional specific app
        
        if not path:
            return ToolResult(
                success=False,
                data={},
                message="No file path provided",
                error="Missing path"
            )
        
        if not Path(path).exists():
            return ToolResult(
                success=False,
                data={},
                message=f"File not found: {path}",
                error="File not found"
            )
        
        try:
            platform = detect_platform()
            
            if platform == Platform.MACOS:
                if app:
                    subprocess.Popen(["open", "-a", app, path])
                else:
                    subprocess.Popen(["open", path])
            elif platform == Platform.WINDOWS:
                if app:
                    subprocess.Popen([app, path])
                else:
                    os.startfile(path)
            else:  # Linux
                if app:
                    subprocess.Popen([app, path])
                else:
                    subprocess.Popen(["xdg-open", path])
            
            return ToolResult(
                success=True,
                data={"path": path, "app": app},
                message=f"Opened: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to open document: {str(e)}",
                error=str(e)
            )

    def _list_notes(self, **kwargs) -> ToolResult:
        """List all saved notes."""
        try:
            notes_dir = self._get_notes_dir()
            notes = []
            
            for note_file in notes_dir.glob("*.md"):
                if note_file.name == "index.json":
                    continue
                
                stat = note_file.stat()
                notes.append({
                    "name": note_file.stem,
                    "path": str(note_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            notes.sort(key=lambda x: x['modified'], reverse=True)
            
            return ToolResult(
                success=True,
                data={"notes": notes, "count": len(notes)},
                message=f"Found {len(notes)} notes"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list notes: {str(e)}",
                error=str(e)
            )

    def _search_notes(self, **kwargs) -> ToolResult:
        """Search notes by content or tags."""
        query = kwargs.get("query") or kwargs.get("search")
        
        if not query:
            return ToolResult(
                success=False,
                data={},
                message="No search query provided",
                error="Missing query"
            )
        
        try:
            notes_dir = self._get_notes_dir()
            matching = []
            
            for note_file in notes_dir.glob("*.md"):
                try:
                    with open(note_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if query.lower() in content.lower():
                        matching.append({
                            "name": note_file.stem,
                            "path": str(note_file),
                            "preview": content[:200] + "..." if len(content) > 200 else content
                        })
                except:
                    continue
            
            return ToolResult(
                success=True,
                data={"notes": matching, "count": len(matching), "query": query},
                message=f"Found {len(matching)} notes matching '{query}'"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to search notes: {str(e)}",
                error=str(e)
            )

    def _create_from_template(self, **kwargs) -> ToolResult:
        """Create a document from a template."""
        template = kwargs.get("template")  # meeting, todo, project, journal
        title = kwargs.get("title", "")
        path = kwargs.get("path")
        
        templates = {
            "meeting": """# Meeting Notes: {title}

**Date:** {date}
**Attendees:** 

## Agenda
1. 
2. 
3. 

## Discussion Points


## Action Items
- [ ] 
- [ ] 

## Next Steps

""",
            "todo": """# Todo List: {title}

**Created:** {date}

## High Priority
- [ ] 

## Medium Priority
- [ ] 

## Low Priority
- [ ] 

## Completed
- [x] 

""",
            "project": """# Project: {title}

**Created:** {date}
**Status:** In Progress

## Overview


## Goals
1. 
2. 

## Tasks
- [ ] 
- [ ] 

## Timeline


## Notes

""",
            "journal": """# Journal Entry

**Date:** {date}

## Today's Highlights


## What I Learned


## Tomorrow's Goals


## Gratitude

"""
        }
        
        if template not in templates:
            return ToolResult(
                success=False,
                data={"available_templates": list(templates.keys())},
                message=f"Unknown template: {template}",
                error=f"Available templates: {list(templates.keys())}"
            )
        
        content = templates[template].format(
            title=title or template.title(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        if not path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in (title or template))
            path = str(Path.home() / "Documents" / f"{safe_title}_{timestamp}.md")
        
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                data={"path": path, "template": template, "title": title},
                message=f"Created {template} document: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to create from template: {str(e)}",
                error=str(e)
            )

    def _convert_to_pdf(self, **kwargs) -> ToolResult:
        """Convert a document to PDF (requires pandoc or similar)."""
        path = kwargs.get("path")
        output = kwargs.get("output")
        
        if not path:
            return ToolResult(
                success=False,
                data={},
                message="No file path provided",
                error="Missing path"
            )
        
        if not Path(path).exists():
            return ToolResult(
                success=False,
                data={},
                message=f"File not found: {path}",
                error="File not found"
            )
        
        if not output:
            output = str(Path(path).with_suffix('.pdf'))
        
        try:
            # Try pandoc
            result = subprocess.run(
                ["pandoc", path, "-o", output],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"input": path, "output": output},
                    message=f"Converted to PDF: {output}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="PDF conversion failed. Install pandoc: brew install pandoc",
                    error=result.stderr
                )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                data={},
                message="pandoc not found. Install with: brew install pandoc (macOS) or apt install pandoc (Linux)",
                error="pandoc not installed"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to convert to PDF: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Create document: document_tool --action create --title 'My Doc' --content 'Hello'",
            "Create note: document_tool --action create_note --content 'Remember this' --title 'Reminder'",
            "Create from template: document_tool --action create_from_template --template meeting --title 'Team Sync'",
            "List notes: document_tool --action list_notes",
            "Search notes: document_tool --action search_notes --query 'meeting'",
            "Open document: document_tool --action open --path '/path/to/doc.txt'",
        ]
