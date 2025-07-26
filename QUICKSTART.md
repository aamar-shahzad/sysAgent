# SysAgent CLI Quick Start Guide

Get up and running with SysAgent CLI in 5 minutes!

## 🚀 Quick Installation

### Option 1: Development Installation (Recommended)

```bash
# Clone and setup
git clone https://github.com/your-org/sysagent-cli.git
cd sysagent-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install
pip install -e .

# Verify installation
sysagent --help
```

### Option 2: From Built Package

```bash
# Download and extract the latest release
# Then install from wheel
pip install sysagent_cli-0.1.0-py3-none-any.whl
```

## 🎯 First Steps

### 1. Check Installation

```bash
sysagent version
```

You should see:
```
SysAgent CLI v0.1.0
Platform: macos
Python: 3.13.5
```

### 2. Explore Available Tools

```bash
sysagent tools
```

This shows all available system tools:
- **file_tool** - File system operations
- **system_info_tool** - System information and metrics
- And more...

### 3. Check Configuration

```bash
sysagent config --show
```

This displays your current configuration settings.

### 4. View Permissions

```bash
sysagent permissions --show
```

This shows what permissions SysAgent has and what it can access.

## 🧠 Basic Usage

### Natural Language Commands

```bash
# Get system information
sysagent run "show system info"

# List files
sysagent run "list files in current directory"

# Check system status
sysagent run "what's using the most CPU?"
```

### Interactive Mode

```bash
# Start interactive session
sysagent repl

# In the REPL, try:
# help          - Show available commands
# tools         - List tools
# "show system info"  - Natural language command
# exit          - Quit
```

### Safe Mode (Dry Run)

```bash
# See what would happen without executing
sysagent run "clean up temp files" --dry-run
```

## 🔧 Configuration

### Set Up LLM Integration

For natural language processing, you'll need an LLM provider:

```bash
# OpenAI (recommended)
export OPENAI_API_KEY="your-api-key-here"

# Or Ollama (local)
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Environment Variables

```bash
# Configuration directory
export SYSAGENT_CONFIG_DIR="$HOME/.sysagent"

# Debug mode
export SYSAGENT_DEBUG=true
```

## 🛡️ Security & Permissions

### Granting Permissions

When you run commands that need system access, SysAgent will ask for permissions:

```bash
sysagent run "list files in downloads"
# SysAgent will prompt for file system permissions
```

### Permission Levels

- **Read**: View files, system info
- **Write**: Create, modify files
- **Execute**: Run commands, install software
- **Admin**: System-level operations

### Revoking Permissions

```bash
# Clear all permissions
sysagent permissions --clear

# Or manage specific permissions
sysagent permissions --show
```

## 📝 Common Commands

### System Information

```bash
# Basic system info
sysagent run "show system info"

# Detailed metrics
sysagent run "what's my CPU usage?"

# Process list
sysagent run "show running processes"
```

### File Operations

```bash
# List files
sysagent run "list files in downloads"

# Find files
sysagent run "find all PDF files"

# Organize files
sysagent run "organize my documents folder"
```

### System Management

```bash
# Check disk space
sysagent run "how much disk space do I have?"

# Clean up
sysagent run "clean up temp files"

# Monitor system
sysagent run "what's using the most memory?"
```

## 🔍 Troubleshooting

### Common Issues

1. **"Permission denied"**
   ```bash
   # Grant permissions when prompted
   # Or check current permissions:
   sysagent permissions --show
   ```

2. **"Command not found"**
   ```bash
   # Reinstall the package
   pip install -e . --force-reinstall
   ```

3. **Configuration errors**
   ```bash
   # Reset to defaults
   sysagent config --reset
   ```

### Debug Mode

```bash
# Run with debug output
sysagent --debug run "your command"

# Or enable globally
export SYSAGENT_DEBUG=true
```

### Getting Help

```bash
# General help
sysagent --help

# Command-specific help
sysagent run --help
sysagent config --help
sysagent permissions --help
```

## 🎯 Next Steps

### Advanced Usage

1. **Set up LLM integration** for natural language processing
2. **Configure permissions** for your use cases
3. **Explore the REPL** for interactive sessions
4. **Check the logs** for detailed operation history

### Development

1. **Read the full documentation** in `README.md`
2. **Check the installation guide** in `INSTALLATION.md`
3. **Explore the source code** in `src/sysagent/`
4. **Run tests** with `python -m pytest tests/`

### Community

- **Report issues** on GitHub
- **Contribute code** via pull requests
- **Join discussions** in the community forum

## 🎉 You're Ready!

You now have a fully functional SysAgent CLI installation. Start exploring with:

```bash
sysagent repl
```

Then try natural language commands like:
- "show me system info"
- "what's using the most CPU?"
- "list files in my home directory"

Happy automating! 🚀 