# SysAgent CLI Installation Guide

## Overview

SysAgent CLI is a secure, intelligent command-line assistant for OS automation and control. This guide covers all installation methods and setup instructions.

## Prerequisites

- **Python**: 3.8 or higher (3.13 recommended)
- **Platform**: macOS, Linux, or Windows
- **Permissions**: Administrative access may be required for certain features

## Installation Methods

### 1. Development Installation (Recommended for Contributors)

Clone the repository and install in development mode:

```bash
# Clone the repository
git clone https://github.com/your-org/sysagent-cli.git
cd sysagent-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Verify installation
sysagent --help
```

### 2. Local Installation from Source

Build and install from source:

```bash
# Clone and setup
git clone https://github.com/your-org/sysagent-cli.git
cd sysagent-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install build dependencies
pip install build

# Build the package
python -m build

# Install from wheel
pip install dist/sysagent_cli-0.1.0-py3-none-any.whl
```

### 3. PyPI Installation (Future)

Once published to PyPI:

```bash
# Install from PyPI
pip install sysagent-cli

# Or with pipx for isolated installation
pipx install sysagent-cli
```

### 4. Global Installation

For system-wide installation:

```bash
# Install globally (requires admin privileges)
sudo pip install sysagent-cli

# Or use pipx for isolated global installation
pipx install sysagent-cli
```

## Configuration

### Initial Setup

After installation, SysAgent will create its configuration directory automatically:

```bash
# Check configuration
sysagent config --show

# View permissions
sysagent permissions --show

# List available tools
sysagent tools
```

### Environment Variables

Set these environment variables for LLM integration:

```bash
# OpenAI (recommended)
export OPENAI_API_KEY="your-openai-api-key"

# Ollama (local)
export OLLAMA_BASE_URL="http://localhost:11434"

# Configuration directory
export SYSAGENT_CONFIG_DIR="$HOME/.sysagent"
```

### Configuration File

The configuration is stored in `~/.sysagent/config.json`:

```json
{
  "agent": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.1,
    "max_tokens": 2000,
    "api_key": null,
    "base_url": null,
    "timeout": 30
  },
  "security": {
    "dry_run": false,
    "confirm_destructive": true,
    "log_encryption": false,
    "audit_logging": true,
    "guardrails_enabled": true
  },
  "tools": [...],
  "plugins": [],
  "verbose": false,
  "debug": false
}
```

## Usage Examples

### Basic Commands

```bash
# Show help
sysagent --help

# Check version
sysagent version

# List tools
sysagent tools

# Show configuration
sysagent config --show

# Show permissions
sysagent permissions --show
```

### Natural Language Commands

```bash
# Run commands with natural language
sysagent run "show system info"
sysagent run "list files in current directory"
sysagent run "clean up temp files"

# Dry run mode
sysagent run "delete old logs" --dry-run

# With confirmation
sysagent run "restart services" --confirm
```

### Interactive Mode

```bash
# Start interactive REPL
sysagent repl

# In REPL mode:
# help          - Show help
# tools         - List tools
# config        - Show configuration
# permissions   - Show permissions
# exit          - Exit REPL
```

## Platform-Specific Notes

### macOS

- **Permissions**: Uses AppleScript for permission requests
- **Features**: Full support for all features
- **Installation**: Works with all installation methods

### Linux

- **Permissions**: Uses `sudo`/`pkexec`/PolicyKit
- **Features**: Full support for all features
- **Dependencies**: May require additional system packages

### Windows

- **Permissions**: Uses UAC for permission requests
- **Features**: Full support for all features
- **Installation**: Works with all installation methods

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Grant permissions for specific tools
   sysagent permissions --show
   # Follow the prompts to grant permissions
   ```

2. **Configuration Errors**
   ```bash
   # Reset configuration
   sysagent config --reset
   ```

3. **Import Errors**
   ```bash
   # Reinstall in development mode
   pip install -e . --force-reinstall
   ```

4. **LLM Connection Issues**
   ```bash
   # Check API key
   echo $OPENAI_API_KEY
   
   # Test connection
   sysagent run "test connection" --debug
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Run with debug
sysagent --debug run "your command"

# Or set globally
export SYSAGENT_DEBUG=true
```

### Logs

Logs are stored in `~/.sysagent/logs/`:

```bash
# View logs
tail -f ~/.sysagent/logs/sysagent.log

# Clear logs
rm ~/.sysagent/logs/*
```

## Development Setup

### Prerequisites

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install testing tools
pip install pytest pytest-cov

# Install linting tools
pip install black isort mypy
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=sysagent --cov-report=html

# Run specific test
python -m pytest tests/test_basic.py::test_config_manager
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/
```

### Building Documentation

```bash
# Install docs dependencies
pip install sphinx sphinx-rtd-theme

# Build docs
cd docs
make html
```

## Security Considerations

### Permissions

- SysAgent requests permissions only when needed
- Permissions are stored securely
- Users can revoke permissions at any time

### API Keys

- Store API keys in environment variables
- Never commit API keys to version control
- Use keyring for secure storage

### Audit Logging

- All operations are logged
- Logs can be encrypted
- Audit trail is maintained

## Support

### Getting Help

```bash
# Show help
sysagent --help

# Command-specific help
sysagent run --help
sysagent config --help
```

### Reporting Issues

1. Check existing issues on GitHub
2. Enable debug mode and collect logs
3. Create detailed issue report

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

SysAgent CLI is licensed under the MIT License. See LICENSE file for details. 