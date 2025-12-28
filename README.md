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

### 🛠️ Comprehensive System Tools (20 Tools)
- **FileTool**: File operations, cleanup, organization
- **SystemInfoTool**: Real-time system metrics and monitoring
- **ProcessTool**: Process management and control
- **NetworkTool**: Network diagnostics and connectivity
- **AppTool**: Application launching and management
- **SchedulerTool**: Task scheduling and cron job management
- **ServiceTool**: System service control (start/stop/restart)
- **SystemControlTool**: System power and control operations
- **ClipboardTool**: Clipboard operations
- **AuthTool**: Secure credential management
- **ScreenshotTool**: Screen capture and analysis
- **VoiceTool**: Voice input/output capabilities
- **SecurityTool**: Security scanning and management
- **MonitoringTool**: System monitoring and alerts
- **AutomationTool**: Workflow automation
- **CodeGenerationTool**: Code generation and execution
- **OSIntelligenceTool**: OS-specific optimizations
- **LowLevelOSTool**: Low-level OS operations
- **DocumentTool**: Create/edit documents, notes, and text files
- **SpreadsheetTool**: Create Excel/CSV files, data entry forms, templates

### 🖥️ GUI Features
- **Chat Interface**: Natural language interaction with SysAgent in a beautiful GUI
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
```

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