# 🧠 SysAgent CLI

**Secure, intelligent command-line assistant for OS automation and control**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🌟 Features

### 🧠 LLM-Driven Intelligence
- Natural language command processing
- Multi-step planning and execution
- Support for OpenAI, Ollama, and local models
- Context-aware responses and suggestions

### 🛠️ Comprehensive System Tools (33+ Tools)

**Core System Tools:**
- **FileTool**: File operations, cleanup, organization
- **SystemInfoTool**: Real-time system metrics and monitoring
- **ProcessTool**: Process management and control
- **NetworkTool**: Network diagnostics and connectivity
- **SystemControlTool**: System power and control operations
- **SecurityTool**: Security scanning and management
- **MonitoringTool**: System monitoring and alerts

**Application & Window Control:**
- **AppTool**: Application launching and management
- **BrowserTool**: Web browser control, open URLs, search, bookmarks
- **WindowTool**: Window management (resize, move, tile, minimize, maximize)
- **KeyboardMouseTool**: Keyboard/mouse input simulation

**Media & Notifications:**
- **MediaTool**: Volume control, mute, play/pause, next/previous track
- **NotificationTool**: System notifications and alerts
- **ClipboardTool**: Clipboard operations
- **ScreenshotTool**: Screen capture and analysis
- **VoiceTool**: Voice input/output capabilities

**Documents & Data:**
- **DocumentTool**: Create/edit documents, notes, text files
- **SpreadsheetTool**: Create Excel/CSV, data entry forms, budgets

**Development & Automation:**
- **GitTool**: Git operations (clone, commit, push, pull, branch)
- **APITool**: HTTP requests (GET, POST, PUT, DELETE)
- **CodeGenerationTool**: Code generation and execution
- **PackageManagerTool**: Software install/update (brew, apt, winget)
- **EmailTool**: Send emails with attachments

**System Management:**
- **SchedulerTool**: Task scheduling and cron jobs
- **ServiceTool**: System service control
- **AuthTool**: Secure credential management
- **AutomationTool**: Workflow automation
- **OSIntelligenceTool**: OS-specific optimizations
- **LowLevelOSTool**: Low-level OS operations

### 🚀 Next-Level Features (NEW!)

**Workflow Builder:**
- **WorkflowTool**: Create and run multi-step automated workflows
- Pre-built templates: Morning routine, Dev setup, System maintenance, End of day
- Chain multiple actions into reusable sequences
- Schedule workflows to run at specific times

**Smart Search:**
- **SmartSearchTool**: Unified search across files, apps, commands, and web
- Find files by name or content
- Search installed applications
- Quick command lookup
- Search history and recent files

**AI-Powered Insights:**
- **SystemInsightsTool**: Intelligent system analysis and recommendations
- Health checks with scoring (0-100)
- Performance analysis with suggestions
- Security scanning and auditing
- Resource hog detection
- Storage analysis and cleanup suggestions
- Network connection analysis

**Smart Memory:**
- **ContextMemoryTool**: Remember user preferences across sessions
- Store favorites and frequently used commands
- Learn usage patterns for smarter suggestions
- Time-based contextual recommendations

### 🏢 Enterprise Features (NEW!)

**Session Management:**
- Save and resume chat conversations
- Export sessions (JSON, Markdown, Text)
- Search through conversation history
- Session statistics and analytics

**REST API Server:**
- Full HTTP API for external integrations
- API key authentication with rate limiting
- Endpoints for chat, tools, sessions
- CORS support for web applications

**Agent Modes:**
- **General**: All-purpose assistant
- **Developer**: Git, code, packages, development focus
- **SysAdmin**: System administration and monitoring
- **Security**: Security auditing and scanning
- **Productivity**: Apps, workflows, notifications
- **Automation**: Workflow creation and scheduling

**Activity Dashboard:**
- Real-time activity timeline
- Tool usage statistics
- Error logging and tracking
- Session analytics
- Visual audit trail

**Onboarding Wizard:**
- First-time user setup experience
- API key configuration
- Permission selection
- Mode selection
- Quick tips tour

**System Tray Mode:**
- Run in background with tray icon
- Global hotkeys (Ctrl+Shift+S / Cmd+Shift+S)
- Quick actions from tray menu
- System notifications

### 🖥️ Next-Level GUI Features
- **Chat Interface**: Natural language interaction with markdown rendering & streaming
- **Command Palette**: Quick command search with ⌘K / Ctrl+K (fuzzy search all commands)
- **Quick Actions Bar**: One-click access to common actions
- **Proactive Agent**: Intelligent suggestions based on system state
- **Execution Logs**: Visual display of tool execution with status & timing
- **Follow-up Suggestions**: Contextual suggestions after each response
- **Workflow Runner**: Visual workflow management and execution
- **Settings GUI**: Configure API keys, model providers, and permissions
- **System Dashboard**: Real-time system monitoring with graphs
- **Process Manager**: Visual process management interface
- **File Browser**: Graphical file operations
- **Terminal View**: Execute shell commands directly
- **Theme Support**: Dark/Light mode switching

### 🔒 Security & Safety
- Permission-gated execution with OS-specific implementations
- Dry-run mode for safe testing
- Guardrails against dangerous operations
- Encrypted configuration and logging
- One-time permission setup with persistent state

### 🧩 Extensible Architecture
- Plugin system for custom tools
- Modular design for easy extension
- Configuration management
- Comprehensive logging and auditing

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/sysagent/sysagent-cli.git
cd sysagent-cli

# Install from local directory
pip install -e .

# Or install with all optional features
pip install -e ".[full]"

# Install with GUI support
pip install -e ".[gui]"

# For development
pip install -e ".[dev]"
```

> **Note**: This package is not yet published to PyPI. Install from source as shown above.

### First Run

```bash
# Start the interactive CLI
sysagent

# Or run a direct command
sysagent "show me system info"
```

## 📖 Usage Examples

### Basic Commands

```bash
# System information
sysagent "what's my system status?"
sysagent "show CPU and memory usage"

# File operations
sysagent "clean up temp files"
sysagent "organize my downloads folder"
sysagent "find large files in my home directory"

# Process management
sysagent "show me what's using the most CPU"
sysagent "kill the process using too much memory"
sysagent "restart my browser"

# Network diagnostics
sysagent "check my internet connection"
sysagent "ping google.com"
sysagent "what's my public IP address?"

# Application control
sysagent "open my code editor"
sysagent "close all browser windows"
sysagent "focus on my terminal"

# Documents and notes
sysagent "create a note about today's meeting"
sysagent "make a todo list for the project"
sysagent "create meeting notes template"

# Spreadsheets and data
sysagent "create an Excel sheet for expense tracking"
sysagent "make a data entry form with name, email, phone"
sysagent "create a budget spreadsheet"
sysagent "create an inventory list template"
```

### Browser & Web

```bash
# Browser control
sysagent "open google.com"
sysagent "search youtube for python tutorials"
sysagent "open Chrome in incognito mode"
sysagent "show my bookmarks"

# API requests
sysagent "make a GET request to api.github.com"
sysagent "download file from https://example.com/file.zip"
```

### Window & Media Control

```bash
# Window management
sysagent "tile my windows left and right"
sysagent "minimize all windows"
sysagent "maximize the current window"
sysagent "list all open windows"

# Media control
sysagent "set volume to 50%"
sysagent "mute the audio"
sysagent "play next track"
sysagent "what song is playing?"
```

### Git & Development

```bash
# Git operations
sysagent "git status"
sysagent "commit with message 'fix bug'"
sysagent "pull latest changes"
sysagent "show recent commits"

# Package management
sysagent "install vim"
sysagent "update all packages"
sysagent "search for python packages"
```

### Notifications & Email

```bash
# Notifications
sysagent "send me a notification saying 'Meeting in 5 minutes'"
sysagent "set a reminder for 3pm"

# Email
sysagent "compose email to john@example.com"
sysagent "send email with subject 'Report' to team@company.com"
```

### Advanced Features

```bash
# Scheduled tasks
sysagent "schedule a backup every day at 2 AM"
sysagent "create a reminder to restart my computer weekly"

# System maintenance
sysagent "run a full system cleanup"
sysagent "check for system updates"
sysagent "optimize my startup programs"

# Development workflows
sysagent "set up my development environment"
sysagent "monitor my project's resource usage"
```

### 🚀 Next-Level Features

```bash
# Workflows - Chain multiple actions
sysagent "run my morning routine"
sysagent "create a workflow for project setup"
sysagent "list all my workflows"
sysagent "run the dev setup workflow"

# Smart Search - Find anything
sysagent "search for files about python"
sysagent "find apps named code"
sysagent "search my recent files"
sysagent "search commands for git"

# System Insights - AI-powered analysis
sysagent "check my system health"
sysagent "give me recommendations"
sysagent "run a security scan"
sysagent "find resource hogs"
sysagent "analyze my storage usage"
sysagent "quick insights"

# Smart Memory - Remember preferences
sysagent "remember my project is sysagent"
sysagent "what was my project?"
sysagent "add favorite command: check status"
sysagent "suggest commands"
```

### ⌨️ Keyboard Shortcuts (GUI)

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` / `⌘K` | Open Command Palette |
| `Ctrl+N` | New Chat |
| `Ctrl+D` | Dashboard |
| `Ctrl+S` | Settings |
| `Ctrl+T` | Terminal |
| `Ctrl+I` | Quick Insights |
| `Ctrl+Q` | Quit |

### GUI Commands

```bash
# Launch the main GUI with chat interface
sysagent gui

# Open standalone chat window
sysagent chat

# Open settings to configure API keys
sysagent settings

# Open the system dashboard
sysagent dashboard

# Open activity dashboard (audit trail)
sysagent activity

# Run in system tray mode (background)
sysagent tray
```

### REST API Server

```bash
# Start API server on default port 8080
sysagent api

# Custom port and host
sysagent api --port 3000 --host 0.0.0.0

# Disable authentication (development only)
sysagent api --no-auth
```

API Endpoints:
- `GET /api/health` - Health check
- `GET /api/info` - API information
- `POST /api/chat` - Send a message
- `GET /api/tools` - List available tools
- `POST /api/tool/{name}` - Execute a tool
- `GET /api/sessions` - List sessions
- `GET /api/session/{id}` - Get session details
- `POST /api/keys` - Create API key (admin only)

### Session Management

```bash
# List all chat sessions
sysagent sessions list

# Search sessions
sysagent sessions list --search "python"

# Show a specific session
sysagent sessions show abc123

# Export session to file
sysagent sessions export abc123 --format markdown -o session.md

# Delete a session
sysagent sessions delete abc123

# View session statistics
sysagent sessions stats
```

### Agent Modes

```bash
# List available modes
sysagent mode list

# Switch to developer mode
sysagent mode set developer

# Switch to sysadmin mode
sysagent mode set sysadmin

# Switch to security mode
sysagent mode set security

# Show current mode
sysagent mode current
```

Available Modes:
- `general` - All-purpose assistant
- `developer` - Git, code, packages
- `sysadmin` - System administration
- `security` - Security auditing
- `productivity` - Apps and workflows
- `automation` - Workflow automation

### Plugin Management

```bash
# List available plugins
sysagent plugins list --all

# Create a new plugin template
sysagent plugins create my_plugin

# Load a plugin
sysagent plugins load my_plugin

# Unload a plugin
sysagent plugins unload my_plugin
```

### Audit Logs

```bash
# View recent audit events
sysagent logs show -n 50

# Filter by event type
sysagent logs show --type tool_execution

# Export logs
sysagent logs export -o audit_log.json --format json

# Clean up old logs
sysagent logs cleanup --days 30
```

## 🏗️ Architecture

```
sysagent/
├── core/           # Core functionality
│   ├── agent.py    # LLM agent implementation
│   ├── permissions.py  # Permission management
│   ├── config.py   # Configuration handling
│   └── logging.py  # Logging and auditing
├── tools/          # System tools
│   ├── file_tool.py
│   ├── system_info_tool.py
│   ├── process_tool.py
│   ├── network_tool.py
│   └── ...
├── cli/            # Command-line interface
│   ├── main.py     # Entry point
│   ├── repl.py     # Interactive REPL
│   └── commands.py # CLI commands
├── plugins/        # Plugin system
│   ├── base.py     # Plugin base classes
│   └── loader.py   # Plugin loader
└── utils/          # Utilities
    ├── security.py # Security utilities
    ├── platform.py # Platform detection
    └── helpers.py  # Helper functions
```

## 🔧 Configuration

SysAgent stores configuration in:
- **macOS**: `~/.sysagent/`
- **Linux**: `~/.sysagent/`
- **Windows**: `%APPDATA%/SysAgent/`

### Environment Variables

```bash
# LLM Configuration
export SYSAGENT_LLM_PROVIDER=openai  # or ollama, local
export SYSAGENT_OPENAI_API_KEY=your_key_here
export SYSAGENT_OLLAMA_BASE_URL=http://localhost:11434

# Security
export SYSAGENT_DRY_RUN=true  # Enable dry-run mode
export SYSAGENT_VERBOSE=true   # Enable verbose logging

# Features
export SYSAGENT_ENABLE_VISION=true   # Enable vision features
export SYSAGENT_ENABLE_VOICE=true    # Enable voice features
```

## 🛡️ Security

### Permission System

SysAgent implements a comprehensive permission system:

1. **Platform Detection**: Automatically detects your OS
2. **Permission Request**: Requests necessary permissions with clear explanations
3. **One-time Setup**: Permissions are granted once and remembered
4. **Granular Control**: Different permission levels for different operations

### Safety Features

- **Dry-run Mode**: Test commands without execution
- **Guardrails**: Block dangerous operations like `rm -rf /`
- **Confirmation Prompts**: Ask before destructive operations
- **Audit Logging**: Track all operations for review

## 🧩 Plugin Development

### Creating Custom Tools

```python
from sysagent.tools.base import BaseTool
from sysagent.types import ToolResult

class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "A custom tool for specific tasks"
    
    def execute(self, **kwargs) -> ToolResult:
        # Your tool logic here
        return ToolResult(
            success=True,
            data={"result": "Custom operation completed"},
            message="Custom tool executed successfully"
        )
```

### Plugin Configuration

```yaml
# ~/.sysagent/plugins/my_plugin.yaml
name: my_plugin
version: 1.0.0
description: My custom plugin
entry_point: my_plugin.tools
permissions:
  - file_system
  - network
dependencies:
  - requests
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/sysagent/sysagent-cli.git
cd sysagent-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
isort src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) for LLM integration
- Uses [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Inspired by modern CLI tools like [Typer](https://typer.tiangolo.com/)

## 📞 Support

- 📖 [Documentation](https://sysagent-cli.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/sysagent/sysagent-cli/issues)
- 💬 [Discussions](https://github.com/sysagent/sysagent-cli/discussions)
- 📧 [Email Support](mailto:support@sysagent.dev)

---

**Made with ❤️ by the SysAgent Team** 