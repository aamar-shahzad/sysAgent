# 🚀 Installation Guide

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation Options

#### Option 1: Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/sysagent/sysagent-cli.git
cd sysagent-cli

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Or install with all optional features
pip install -e ".[full]"
```

#### Option 2: Install from PyPI (Production)

```bash
# Install basic version
pip install sysagent-cli

# Install with all optional features
pip install sysagent-cli[full]

# Install with development tools
pip install sysagent-cli[dev]
```

#### Option 3: Using pipx (Recommended for CLI tools)

```bash
# Install with pipx for isolated environment
pipx install sysagent-cli

# Or install with all features
pipx install sysagent-cli[full]
```

## Configuration

### First Run

After installation, run SysAgent for the first time:

```bash
# Start interactive mode
sysagent repl

# Or run a direct command
sysagent run "show me system info"
```

### Environment Variables

Set these environment variables to configure SysAgent:

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

### Configuration Files

SysAgent stores configuration in:
- **macOS**: `~/.sysagent/`
- **Linux**: `~/.sysagent/`
- **Windows**: `%APPDATA%/SysAgent/`

## Usage Examples

### Basic Commands

```bash
# System information
sysagent run "show me system info"
sysagent run "what's my CPU usage?"

# File operations
sysagent run "list files in downloads"
sysagent run "clean up temp files"
sysagent run "organize my documents"

# Process management
sysagent run "show running processes"
sysagent run "what's using the most memory?"

# Network diagnostics
sysagent run "check my internet connection"
sysagent run "what's my IP address?"
```

### Interactive Mode

```bash
# Start interactive REPL
sysagent repl

# Then use natural language commands:
# > show me system info
# > clean up temp files
# > what's using the most CPU?
# > exit
```

### Advanced Features

```bash
# Dry-run mode (see what would be done)
sysagent run --dry-run "clean up files"

# Verbose output
sysagent run --verbose "show system info"

# Specific tool usage
sysagent run --tool file_tool --action list --path ~/Downloads
```

## Development Setup

### Install Development Dependencies

```bash
# Install with development tools
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sysagent

# Run specific test file
pytest tests/test_basic.py
```

### Code Formatting

```bash
# Format code
black src/
isort src/

# Check code quality
flake8 src/
mypy src/
```

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - SysAgent requires permissions for system operations
   - Grant permissions when prompted
   - Use `sysagent permissions --show` to check current permissions

2. **LLM Connection Issues**
   - Check your API keys and network connection
   - Verify LLM provider configuration
   - Use rule-based mode if LLM is unavailable

3. **Tool Not Found**
   - Ensure all dependencies are installed
   - Check tool availability for your platform
   - Use `sysagent tools` to list available tools

### Getting Help

```bash
# Show help
sysagent --help

# Show command help
sysagent run --help

# List available tools
sysagent tools

# Show configuration
sysagent config --show

# Show permissions
sysagent permissions --show
```

## Platform-Specific Notes

### macOS

- Requires accessibility permissions for app control
- Uses AppleScript for system automation
- Supports Homebrew package management

### Linux

- May require sudo for certain operations
- Uses systemd for service management
- Supports various package managers (apt, yum, etc.)

### Windows

- Requires UAC elevation for administrative operations
- Uses PowerShell for system automation
- Supports Chocolatey package management

## Next Steps

1. **Explore Tools**: Run `sysagent tools` to see available capabilities
2. **Configure LLM**: Set up OpenAI or Ollama for enhanced intelligence
3. **Grant Permissions**: Allow SysAgent access to system resources
4. **Try Commands**: Start with simple queries and explore advanced features
5. **Customize**: Modify configuration and add custom tools

## Support

- 📖 [Documentation](https://sysagent-cli.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/sysagent/sysagent-cli/issues)
- 💬 [Discussions](https://github.com/sysagent/sysagent-cli/discussions)
- 📧 [Email Support](mailto:support@sysagent.dev) 