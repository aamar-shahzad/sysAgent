"""
Main CLI entry point for SysAgent.
"""

import sys
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..core.config import ConfigManager
from ..core.permissions import PermissionManager
from ..core.agent import SysAgent
from ..utils.platform import detect_platform
from .langgraph_commands import langgraph


console = Console()


def print_banner():
    """Print the SysAgent banner."""
    banner = Text()
    banner.append("🧠 ", style="bold blue")
    banner.append("SysAgent CLI", style="bold white")
    banner.append(" v0.1.0", style="dim")
    
    panel = Panel(
        banner,
        border_style="blue",
        padding=(0, 2)
    )
    console.print(panel)


def start_interactive_mode(config_manager, permission_manager, debug=False, auto_grant_permissions=False):
    """Start interactive mode for SysAgent with LangGraph agent."""
    print_banner()
    if debug:
        console.print("[dim]Starting LangGraph interactive mode with DEBUG enabled. Type 'help' for commands, 'exit' to quit[/dim]\n")
    else:
        console.print("[dim]Starting LangGraph interactive mode. Type 'help' for commands, 'exit' to quit[/dim]\n")
    
    # Initialize LangGraph agent with debug flag
    from ..core.langgraph_agent import LangGraphAgent
    agent = LangGraphAgent(config_manager, permission_manager, debug=debug)
    
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    
    # Create prompt session
    history_file = Path.home() / ".sysagent" / "history"
    history_file.parent.mkdir(exist_ok=True)
    
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter([
            'help', 'exit', 'quit', 'tools', 'config', 'permissions',
            'set', 'get', 'grant', 'revoke', 'grant-all',
            'show system info', 'clean up files', 'list processes',
            'what is my CPU usage', 'organize my files', 'check disk space'
        ])
    )
    
    while True:
        try:
            user_input = session.prompt("sysagent > ")
            
            if not user_input.strip():
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("[dim]Goodbye![/dim]")
                break
            
            if user_input.lower() == 'help':
                print_repl_help()
                continue
            
            if user_input.lower() == 'tools':
                print_available_tools()
                continue
            
            if user_input.lower() == 'config':
                print_config_info(config_manager.load_config())
                continue
            
            if user_input.lower() == 'permissions':
                print_permissions_info(permission_manager)
                continue
            
            if user_input.lower() == 'grant-all':
                console.print("[bold]Granting all permissions...[/bold]")
                all_permissions = [
                    "file_access", "system_info", "process_management", "network_access",
                    "system_control", "code_execution", "security_operations", 
                    "automation_operations", "monitoring_operations", "low_level_os"
                ]
                granted_count = 0
                for permission in all_permissions:
                    try:
                        permission_manager.grant_permission(permission)
                        console.print(f"[green]✓[/green] {permission}")
                        granted_count += 1
                    except Exception as e:
                        console.print(f"[red]✗[/red] {permission}: {e}")
                console.print(f"\n[green]✓[/green] Granted {granted_count} permissions")
                continue
            
            # Handle config set/get commands
            if user_input.lower().startswith('set ') and len(user_input.split()) == 3:
                parts = user_input.split(' ', 2)
                if len(parts) >= 3:
                    key, value = parts[1], parts[2]
                    handle_config_set(config_manager.load_config(), permission_manager, key, value)
                    continue
            
            if user_input.lower().startswith('get ') and len(user_input.split()) == 2:
                parts = user_input.split(' ', 1)
                if len(parts) >= 2:
                    key = parts[1]
                    handle_config_get(config_manager.load_config(), key)
                    continue
            
            # Handle permissions grant/revoke commands
            if user_input.lower().startswith('grant ') and len(user_input.split()) == 2:
                parts = user_input.split(' ', 1)
                if len(parts) >= 2:
                    tool = parts[1]
                    handle_permission_grant(permission_manager, tool)
                    continue
            
            if user_input.lower().startswith('revoke ') and len(user_input.split()) == 2:
                parts = user_input.split(' ', 1)
                if len(parts) >= 2:
                    tool = parts[1]
                    handle_permission_revoke(permission_manager, tool)
                    continue
            
            # Process the command with LangGraph agent
            console.print("[dim]Processing your request...[/dim]", end="")
            with console.status("[bold blue]Thinking...", spinner="dots"):
                result = agent.process_command(user_input)
            
            # Check for interrupts (human-in-the-loop)
            if result.get('__interrupt__'):
                interrupt_data = result['__interrupt__']
                if isinstance(interrupt_data, (list, tuple)) and len(interrupt_data) > 0:
                    interrupt = interrupt_data[0]
                    if hasattr(interrupt, 'value') and isinstance(interrupt.value, dict):
                        # Display the permission request
                        console.print(f"\n[yellow]🔒 Permission Request[/yellow]")
                        console.print(f"[bold]{interrupt.value.get('message', 'Permission required')}[/bold]")
                        console.print(f"Tool: {interrupt.value.get('tool', 'Unknown')}")
                        console.print(f"Action: {interrupt.value.get('action', 'Unknown')}")
                        if interrupt.value.get('path'):
                            console.print(f"Path: {interrupt.value.get('path')}")
                        
                        # Get user response
                        prompt = interrupt.value.get('prompt', 'Grant permission? (y/n): ')
                        user_response = session.prompt(f"\n{prompt} ")
                        
                        # Resume the agent with the user's response
                        from langgraph.types import Command
                        resume_result = agent.process_command(Command(resume=user_response))
                        
                        if resume_result['success']:
                            console.print(f"\n[green]✓[/green] {resume_result['message']}")
                        else:
                            console.print(f"\n[red]✗[/red] {resume_result['message']}")
                    else:
                        console.print(f"\n[yellow]⚠️[/yellow] Interrupt received: {interrupt}")
                else:
                    console.print(f"\n[yellow]⚠️[/yellow] Interrupt received: {interrupt_data}")
            # Check for permission request in message (our custom permission handling)
            elif result['success'] and result['message'].startswith('PERMISSION_REQUEST:'):
                try:
                    # Parse the permission request: PERMISSION_REQUEST:permission:tool:message:prompt
                    parts = result['message'].replace('PERMISSION_REQUEST:', '').split(':', 4)
                    if len(parts) >= 5:
                        permission, tool, message, prompt = parts[0], parts[1], parts[2], parts[3]
                        
                        # Check if auto-grant-permissions is enabled
                        if auto_grant_permissions:
                            console.print(f"\n[yellow]🔒 Auto-granting permission for {tool}[/yellow]")
                            console.print(f"[dim]{message}[/dim]")
                            
                            # Automatically grant permission
                            permission_manager.grant_permission(permission)
                            
                            # Retry the original command
                            retry_result = agent.process_command(user_input)
                            if retry_result['success']:
                                console.print(f"\n[green]✓[/green] {retry_result['message']}")
                            else:
                                console.print(f"\n[red]✗[/red] {retry_result['message']}")
                        else:
                            # Display the permission request
                            console.print(f"\n[yellow]🔒 Permission Request[/yellow]")
                            console.print(f"[bold]{message}[/bold]")
                            console.print(f"Tool: {tool}")
                            
                            # Get user response
                            user_response = session.prompt(f"\n{prompt} ")
                            
                            # Handle the permission based on user response
                            if user_response.lower() in ['y', 'yes', 'grant', 'allow']:
                                # Grant permission and retry the operation
                                permission_manager.grant_permission(permission)
                                
                                # Retry the original command
                                retry_result = agent.process_command(user_input)
                                if retry_result['success']:
                                    console.print(f"\n[green]✓[/green] {retry_result['message']}")
                                else:
                                    console.print(f"\n[red]✗[/red] {retry_result['message']}")
                            else:
                                console.print(f"\n[red]✗[/red] Permission denied")
                    else:
                        console.print(f"\n[red]✗[/red] Invalid permission request format")
                except Exception as e:
                    console.print(f"\n[red]✗[/red] Error handling permission request: {str(e)}")
            elif result['success']:
                console.print(f"\n[green]✓[/green] {result['message']}")
                
                # Show tools used if available
                if result.get('data', {}).get('tools_used'):
                    tools_used = result['data']['tools_used']
                    console.print(f"[dim]Tools used: {', '.join(tools_used)}[/dim]")
                
                # Show data if available
                if result.get('data') and config_manager.load_config().verbose:
                    console.print(result['data'])
            else:
                console.print(f"\n[red]✗[/red] {result['message']}")
                if result.get('error'):
                    console.print(f"[red]Error:[/red] {result['error']}")
        
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit[/dim]")
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            if config_manager.load_config().debug:
                import traceback
                console.print(traceback.format_exc())


def print_help():
    """Print help information."""
    help_text = """
[bold]Usage:[/bold]
  sysagent [command] [options]
  sysagent                    # Start interactive mode (default)

[bold]Commands:[/bold]
  [blue]run[/blue]          Run a command with natural language
  [blue]repl[/blue]         Start interactive REPL mode
  [blue]tools[/blue]        List available tools
  [blue]config[/blue]       Manage configuration
  [blue]permissions[/blue]  Manage permissions
  [blue]version[/blue]      Show version information

[bold]Examples:[/bold]
  sysagent                    # Start interactive mode
  sysagent run "show me system info"
  sysagent run "clean up temp files"
  sysagent run "what's using the most CPU?"

[bold]Interactive Mode:[/bold]
  Just run 'sysagent' to start asking questions directly!

[bold]For more help:[/bold]
  sysagent --help
  sysagent run --help
    """
    
    console.print(help_text)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.option('--config-dir', help='Configuration directory path')
@click.option('--auto-grant-permissions', is_flag=True, help='Automatically grant all permissions without prompting')
@click.pass_context
def cli(ctx, verbose, debug, config_dir, auto_grant_permissions):
    """SysAgent CLI - Secure, intelligent command-line assistant for OS automation and control."""
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store options in context
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    ctx.obj['config_dir'] = config_dir
    ctx.obj['auto_grant_permissions'] = auto_grant_permissions
    
    # Initialize configuration
    config_manager = ConfigManager(config_dir)
    config = config_manager.load_config()
    
    # Update config with CLI options
    if verbose:
        config.verbose = True
    if debug:
        config.debug = True
    
    ctx.obj['config'] = config
    ctx.obj['config_manager'] = config_manager
    
    # Initialize permission manager
    permission_manager = PermissionManager(config_manager)
    ctx.obj['permission_manager'] = permission_manager


@cli.command()
@click.pass_context
def default(ctx):
    """Start interactive mode (default behavior)."""
    config = ctx.obj['config']
    permission_manager = ctx.obj['permission_manager']
    debug = ctx.obj.get('debug', False)
    auto_grant_permissions = ctx.obj.get('auto_grant_permissions', False)
    start_interactive_mode(ctx.obj['config_manager'], ctx.obj['permission_manager'], debug=debug, auto_grant_permissions=auto_grant_permissions)





@cli.command()
@click.argument('command', required=False)
@click.option('--tool', help='Specific tool to use')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.option('--confirm', is_flag=True, help='Ask for confirmation before executing')
@click.pass_context
def run(ctx, command, tool, dry_run, confirm):
    """Run a command with natural language processing."""
    config = ctx.obj['config']
    permission_manager = ctx.obj['permission_manager']
    
    if not command:
        console.print("[red]Error:[/red] No command provided")
        console.print("Usage: sysagent run \"your command here\"")
        return
    
    # Initialize agent
    agent = SysAgent(config, permission_manager)
    
    # Set dry-run mode
    if dry_run:
        config.security.dry_run = True
    
    # Set confirmation mode
    if confirm:
        config.security.confirm_destructive = True
    
    try:
        # Process the command
        result = agent.process_command(command)
        
        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
            if result.data:
                console.print(result.data)
        else:
            console.print(f"[red]✗[/red] {result.message}")
            if result.error:
                console.print(f"[red]Error:[/red] {result.error}")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if config.debug:
            import traceback
            console.print(traceback.format_exc())


@cli.command()
@click.pass_context
def repl(ctx):
    """Start interactive REPL mode."""
    config = ctx.obj['config']
    permission_manager = ctx.obj['permission_manager']
    
    print_banner()
    console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]\n")
    
    # Initialize agent
    agent = SysAgent(config, permission_manager)
    
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    
    # Create prompt session
    history_file = Path.home() / ".sysagent" / "history"
    history_file.parent.mkdir(exist_ok=True)
    
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter([
            'help', 'exit', 'quit', 'tools', 'config', 'permissions',
            'show system info', 'clean up files', 'list processes'
        ])
    )
    
    while True:
        try:
            user_input = session.prompt("sysagent > ")
            
            if not user_input.strip():
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("[dim]Goodbye![/dim]")
                break
            
            if user_input.lower() == 'help':
                print_repl_help()
                continue
            
            if user_input.lower() == 'tools':
                print_available_tools()
                continue
            
            if user_input.lower() == 'config':
                print_config_info(config)
                continue
            
            if user_input.lower() == 'permissions':
                print_permissions_info(permission_manager)
                continue
            
            # Process the command
            result = agent.process_command(user_input)
            
            if result.success:
                console.print(f"[green]✓[/green] {result.message}")
                if result.data and config.verbose:
                    console.print(result.data)
            else:
                console.print(f"[red]✗[/red] {result.message}")
                if result.error:
                    console.print(f"[red]Error:[/red] {result.error}")
        
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit[/dim]")
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            if config.debug:
                import traceback
                console.print(traceback.format_exc())


def print_repl_help():
    """Print LangGraph REPL help information."""
    help_text = """
[bold blue]LangGraph Agent REPL Commands:[/bold blue]

[bold]Advanced AI Agent with React Pattern and Human-in-the-Loop[/bold]

[bold]Basic Commands:[/bold]
  [blue]help[/blue]         Show this help
  [blue]tools[/blue]        List available tools
  [blue]config[/blue]       Show configuration
  [blue]permissions[/blue]  Show permissions
  [blue]exit[/blue]         Exit REPL

[bold]Configuration Commands:[/bold]
  [blue]set <key> <value>[/blue]  Set configuration value
  [blue]get <key>[/blue]           Get configuration value
  Examples: set security.dry_run true
           get agent.provider

[bold]Permission Commands:[/bold]
  [blue]grant <tool>[/blue]        Grant permissions for tool
  [blue]revoke <tool>[/blue]       Revoke permissions for tool
  Examples: grant file_tool
           revoke system_info_tool

[bold]Natural Language Examples:[/bold]
  The LangGraph agent can handle complex multi-step tasks!
  "show me system info and clean up temp files"
  "monitor processes and kill any using too much CPU"
  "analyze disk usage and suggest what to clean up"
  "organize my downloads folder by file type"
  "check network connectivity and diagnose issues"
    """
    console.print(help_text)


def print_available_tools():
    """Print available tools."""
    from ..tools.base import list_available_tools
    
    tools = list_available_tools()
    
    console.print("[bold]Available Tools:[/bold]")
    for tool in tools:
        console.print(f"  [blue]{tool['name']}[/blue] - {tool['description']}")
        console.print(f"    Category: {tool['category']}")
        console.print(f"    Permissions: {', '.join(tool['permissions'])}")
        console.print()


def print_config_info(config):
    """Print configuration information."""
    console.print("[bold]Configuration:[/bold]")
    console.print(f"  LLM Provider: {config.agent.provider.value}")
    console.print(f"  Model: {config.agent.model}")
    console.print(f"  Verbose: {config.verbose}")
    console.print(f"  Debug: {config.debug}")
    console.print(f"  Dry Run: {config.security.dry_run}")
    console.print(f"  Confirm Destructive: {config.security.confirm_destructive}")
    console.print()


def print_permissions_info(permission_manager):
    """Print permissions information."""
    console.print("[bold]Permissions:[/bold]")
    
    granted_permissions = permission_manager.get_granted_permissions()
    if granted_permissions:
        console.print("  [green]Granted:[/green]")
        for perm in granted_permissions:
            console.print(f"    ✓ {perm}")
    else:
        console.print("  [dim]No permissions granted[/dim]")
    
    # Check system permissions
    system_checks = permission_manager.check_system_permissions()
    console.print("\n  [blue]System Checks:[/blue]")
    for check, status in system_checks.items():
        status_icon = "✓" if status else "✗"
        status_color = "green" if status else "red"
        console.print(f"    {status_icon} {check}")
    
    console.print()


@cli.command()
@click.pass_context
def tools(ctx):
    """List available tools."""
    print_available_tools()


@cli.group()
@click.pass_context
def config(ctx):
    """Manage SysAgent configuration."""
    pass


@config.command()
@click.option('--show', is_flag=True, help='Show current configuration')
@click.option('--reset', is_flag=True, help='Reset to default configuration')
@click.option('--export', type=click.Path(), help='Export configuration to file')
@click.option('--import', 'import_file', type=click.Path(), help='Import configuration from file')
@click.pass_context
def show_config(ctx, show, reset, export, import_file):
    """Show or manage configuration."""
    config_manager = ctx.obj['config_manager']
    config = ctx.obj['config']
    
    if show or not any([reset, export, import_file]):
        print_config_info(config)
    elif reset:
        if click.confirm("Are you sure you want to reset the configuration?"):
            config_manager.reset_config()
            console.print("[green]✓[/green] Configuration reset to defaults")
    elif export:
        try:
            config_manager.export_config(export)
            console.print(f"[green]✓[/green] Configuration exported to {export}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to export configuration: {e}")
    elif import_file:
        try:
            config_manager.import_config(import_file)
            console.print(f"[green]✓[/green] Configuration imported from {import_file}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to import configuration: {e}")


@config.command()
@click.argument('key')
@click.pass_context
def get(ctx, key):
    """Get a configuration value."""
    config = ctx.obj['config']
    
    # Handle nested keys like 'agent.provider' or 'security.dry_run'
    keys = key.split('.')
    value = config
    
    try:
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                console.print(f"[red]✗[/red] Configuration key '{key}' not found")
                return
        
        # Handle enum values
        if hasattr(value, 'value'):
            value = value.value
        
        console.print(f"[green]{key}[/green] = {value}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error getting configuration: {e}")


@config.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def set(ctx, key, value):
    """Set a configuration value."""
    config_manager = ctx.obj['config_manager']
    config = ctx.obj['config']
    
    # Handle nested keys like 'agent.provider' or 'security.dry_run'
    keys = key.split('.')
    
    try:
        # Navigate to the parent object
        parent = config
        for k in keys[:-1]:
            if hasattr(parent, k):
                parent = getattr(parent, k)
            else:
                console.print(f"[red]✗[/red] Configuration key '{key}' not found")
                return
        
        # Set the value
        last_key = keys[-1]
        if hasattr(parent, last_key):
            # Convert value based on the field type
            current_value = getattr(parent, last_key)
            if isinstance(current_value, bool):
                new_value = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(current_value, int):
                new_value = int(value)
            elif isinstance(current_value, float):
                new_value = float(value)
            else:
                new_value = value
            
            setattr(parent, last_key, new_value)
            config_manager.save_config()
            console.print(f"[green]✓[/green] Set {key} = {new_value}")
        else:
            console.print(f"[red]✗[/red] Configuration key '{key}' not found")
    except Exception as e:
        console.print(f"[red]✗[/red] Error setting configuration: {e}")


@cli.group()
@click.pass_context
def permissions(ctx):
    """Manage SysAgent permissions."""
    pass


@permissions.command()
@click.option('--show', is_flag=True, help='Show current permissions')
@click.option('--clear', is_flag=True, help='Clear all permissions')
@click.pass_context
def show_permissions(ctx, show, clear):
    """Show or manage permissions."""
    permission_manager = ctx.obj['permission_manager']
    
    if show or not clear:
        print_permissions_info(permission_manager)
    
    elif clear:
        if click.confirm("Are you sure you want to clear all permissions?"):
            permission_manager.clear_permissions()
            console.print("[green]✓[/green] All permissions cleared")


@permissions.command()
@click.argument('tool')
@click.pass_context
def grant(ctx, tool):
    """Grant permissions for a specific tool."""
    permission_manager = ctx.obj['permission_manager']
    
    try:
        # Get required permissions for the tool
        required_permissions = permission_manager.get_required_permissions(tool)
        
        if not required_permissions:
            console.print(f"[red]✗[/red] Tool '{tool}' not found or has no permissions")
            return
        
        console.print(f"[bold]Granting permissions for tool: {tool}[/bold]")
        
        for perm_request in required_permissions:
            if not perm_request.granted:
                console.print(f"\nRequesting permission: {perm_request.permission}")
                console.print(f"Description: {perm_request.description}")
                console.print(f"Level: {perm_request.level.value}")
                
                granted = permission_manager.request_permission(
                    perm_request.permission,
                    perm_request.level,
                    perm_request.description
                )
                
                if granted:
                    console.print(f"[green]✓[/green] Permission '{perm_request.permission}' granted")
                else:
                    console.print(f"[red]✗[/red] Permission '{perm_request.permission}' denied")
            else:
                console.print(f"[dim]Permission '{perm_request.permission}' already granted[/dim]")
        
        console.print(f"\n[green]✓[/green] Permissions updated for tool: {tool}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error granting permissions: {e}")


@permissions.command()
@click.argument('tool')
@click.pass_context
def revoke(ctx, tool):
    """Revoke permissions for a specific tool."""
    permission_manager = ctx.obj['permission_manager']
    
    try:
        # Get required permissions for the tool
        required_permissions = permission_manager.get_required_permissions(tool)
        
        if not required_permissions:
            console.print(f"[red]✗[/red] Tool '{tool}' not found or has no permissions")
            return
        
        console.print(f"[bold]Revoking permissions for tool: {tool}[/bold]")
        
        revoked_count = 0
        for perm_request in required_permissions:
            if perm_request.granted:
                permission_manager.revoke_permission(perm_request.permission)
                console.print(f"[green]✓[/green] Permission '{perm_request.permission}' revoked")
                revoked_count += 1
            else:
                console.print(f"[dim]Permission '{perm_request.permission}' not granted[/dim]")
        
        if revoked_count > 0:
            console.print(f"\n[green]✓[/green] Revoked {revoked_count} permissions for tool: {tool}")
        else:
            console.print(f"\n[dim]No permissions were revoked for tool: {tool}[/dim]")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error revoking permissions: {e}")


@permissions.command()
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def grant_all(ctx, confirm):
    """Grant all permissions for all tools."""
    permission_manager = ctx.obj['permission_manager']
    
    try:
        # Define all available permissions
        all_permissions = [
            "file_access",
            "system_info", 
            "process_management",
            "network_access",
            "system_control",
            "code_execution",
            "security_operations",
            "automation_operations",
            "monitoring_operations",
            "low_level_os"
        ]
        
        console.print(f"[bold]Granting all permissions for SysAgent[/bold]")
        console.print(f"This will grant permissions for: {', '.join(all_permissions)}")
        
        if not confirm:
            if not click.confirm("Are you sure you want to grant all permissions?"):
                console.print("[dim]Permission granting cancelled[/dim]")
                return
        
        granted_count = 0
        for permission in all_permissions:
            try:
                permission_manager.grant_permission(permission)
                console.print(f"[green]✓[/green] Permission '{permission}' granted")
                granted_count += 1
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to grant '{permission}': {e}")
        
        console.print(f"\n[green]✓[/green] Successfully granted {granted_count} permissions")
        console.print("[bold]All tools are now available for use![/bold]")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error granting all permissions: {e}")


@cli.command()
def version():
    """Show version information."""
    from .. import __version__
    
    console.print(f"[bold]SysAgent CLI[/bold] v{__version__}")
    console.print(f"Platform: {detect_platform().value}")
    console.print(f"Python: {sys.version}")


@cli.command()
@click.pass_context
def gui(ctx):
    """Launch the graphical user interface."""
    console.print("[blue]Launching SysAgent GUI...[/blue]")
    try:
        from ..gui import launch_gui
        launch_gui()
    except ImportError as e:
        console.print(f"[red]Error:[/red] GUI dependencies not installed. Install with: pip install sysagent-cli[gui]")
        console.print(f"[dim]Details: {e}[/dim]")
    except Exception as e:
        console.print(f"[red]Error launching GUI:[/red] {e}")


@cli.command()
@click.pass_context
def settings(ctx):
    """Open the settings GUI."""
    console.print("[blue]Opening SysAgent Settings...[/blue]")
    try:
        from ..gui import launch_settings
        launch_settings()
    except ImportError as e:
        console.print(f"[red]Error:[/red] GUI dependencies not installed. Install with: pip install sysagent-cli[gui]")
        console.print(f"[dim]Details: {e}[/dim]")
    except Exception as e:
        console.print(f"[red]Error opening settings:[/red] {e}")


@cli.command()
@click.pass_context
def dashboard(ctx):
    """Open the system dashboard GUI."""
    console.print("[blue]Opening SysAgent Dashboard...[/blue]")
    try:
        from ..gui import launch_dashboard
        launch_dashboard()
    except ImportError as e:
        console.print(f"[red]Error:[/red] GUI dependencies not installed. Install with: pip install sysagent-cli[gui]")
        console.print(f"[dim]Details: {e}[/dim]")
    except Exception as e:
        console.print(f"[red]Error opening dashboard:[/red] {e}")


@cli.command()
@click.pass_context
def chat(ctx):
    """Open the chat GUI for interacting with SysAgent."""
    console.print("[blue]Opening SysAgent Chat...[/blue]")
    try:
        from ..gui import launch_chat
        launch_chat()
    except ImportError as e:
        console.print(f"[red]Error:[/red] GUI dependencies not installed. Install with: pip install sysagent-cli[gui]")
        console.print(f"[dim]Details: {e}[/dim]")
    except Exception as e:
        console.print(f"[red]Error opening chat:[/red] {e}")


# Plugin management commands
@cli.group()
@click.pass_context
def plugins(ctx):
    """Manage SysAgent plugins."""
    pass


@plugins.command(name="list")
@click.option('--all', 'show_all', is_flag=True, help='Show all discovered plugins (not just loaded)')
@click.pass_context
def list_plugins(ctx, show_all):
    """List installed plugins."""
    from ..core.plugins import PluginManager
    
    plugin_manager = PluginManager()
    
    if show_all:
        discovered = plugin_manager.discover_plugins()
        console.print("[bold]Discovered Plugins:[/bold]")
        if discovered:
            for plugin in discovered:
                status = "[green]loaded[/green]" if plugin.get('loaded') else "[dim]not loaded[/dim]"
                console.print(f"  • {plugin.get('name', 'Unknown')} - {status}")
                if plugin.get('description'):
                    console.print(f"    {plugin['description']}")
                if plugin.get('error'):
                    console.print(f"    [red]Error: {plugin['error']}[/red]")
        else:
            console.print("  [dim]No plugins found[/dim]")
    else:
        loaded = plugin_manager.list_plugins()
        console.print("[bold]Loaded Plugins:[/bold]")
        if loaded:
            for plugin in loaded:
                enabled = "[green]enabled[/green]" if plugin.enabled else "[yellow]disabled[/yellow]"
                console.print(f"  • {plugin.name} v{plugin.version} - {enabled}")
                console.print(f"    {plugin.description}")
                console.print(f"    Tools: {', '.join(plugin.tools) if plugin.tools else 'none'}")
        else:
            console.print("  [dim]No plugins loaded[/dim]")


@plugins.command()
@click.argument('name')
@click.pass_context
def load(ctx, name):
    """Load a plugin."""
    from ..core.plugins import PluginManager
    
    plugin_manager = PluginManager()
    
    console.print(f"[blue]Loading plugin: {name}...[/blue]")
    result = plugin_manager.load_plugin(name)
    
    if result:
        console.print(f"[green]✓[/green] Plugin '{result.name}' loaded successfully")
        console.print(f"  Version: {result.version}")
        console.print(f"  Tools: {', '.join(result.tools) if result.tools else 'none'}")
    else:
        console.print(f"[red]✗[/red] Failed to load plugin '{name}'")


@plugins.command()
@click.argument('name')
@click.pass_context
def unload(ctx, name):
    """Unload a plugin."""
    from ..core.plugins import PluginManager
    
    plugin_manager = PluginManager()
    
    if plugin_manager.unload_plugin(name):
        console.print(f"[green]✓[/green] Plugin '{name}' unloaded")
    else:
        console.print(f"[red]✗[/red] Plugin '{name}' not found or not loaded")


@plugins.command()
@click.argument('name')
@click.option('--output', '-o', help='Output directory for plugin')
@click.pass_context
def create(ctx, name, output):
    """Create a new plugin template."""
    from ..core.plugins import create_plugin_template
    
    console.print(f"[blue]Creating plugin template: {name}...[/blue]")
    
    try:
        plugin_path = create_plugin_template(name, output)
        console.print(f"[green]✓[/green] Plugin template created at: {plugin_path}")
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  1. Edit {plugin_path}/example_tool.py")
        console.print(f"  2. Update {plugin_path}/plugin.json with metadata")
        console.print(f"  3. Load with: sysagent plugins load {name}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create plugin: {e}")


# Audit log commands
@cli.group()
@click.pass_context
def logs(ctx):
    """View and manage audit logs."""
    pass


@logs.command(name="show")
@click.option('--limit', '-n', default=20, help='Number of events to show')
@click.option('--type', 'event_type', help='Filter by event type')
@click.option('--since', help='Show events since date (YYYY-MM-DD)')
@click.option('--until', help='Show events until date (YYYY-MM-DD)')
@click.pass_context
def show_logs(ctx, limit, event_type, since, until):
    """Show recent audit events."""
    from ..core.logging import get_audit_logger
    
    logger = get_audit_logger()
    
    event_types = [event_type] if event_type else None
    events = logger.get_events(
        start_date=since,
        end_date=until,
        event_types=event_types,
        limit=limit
    )
    
    console.print(f"[bold]Audit Log ({len(events)} events):[/bold]\n")
    
    for event in events:
        # Format timestamp
        time_str = event.timestamp.split('T')[1].split('.')[0] if 'T' in event.timestamp else event.timestamp
        
        # Color based on success
        status = "[green]✓[/green]" if event.success else "[red]✗[/red]"
        
        console.print(f"{status} [{time_str}] {event.event_type}: {event.action}")
        if event.error:
            console.print(f"    [red]Error: {event.error}[/red]")


@logs.command()
@click.option('--format', 'fmt', type=click.Choice(['json', 'csv']), default='json', help='Export format')
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--limit', '-n', default=1000, help='Maximum events to export')
@click.pass_context
def export(ctx, fmt, output, limit):
    """Export audit logs to a file."""
    from ..core.logging import get_audit_logger
    
    logger = get_audit_logger()
    
    try:
        path = logger.export_events(output, format=fmt, limit=limit)
        console.print(f"[green]✓[/green] Exported audit logs to: {path}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to export logs: {e}")


@logs.command()
@click.option('--days', default=30, help='Keep logs from last N days')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def cleanup(ctx, days, confirm):
    """Clean up old audit logs."""
    from ..core.logging import get_audit_logger
    
    if not confirm:
        if not click.confirm(f"Delete audit logs older than {days} days?"):
            console.print("[dim]Cleanup cancelled[/dim]")
            return
    
    logger = get_audit_logger()
    logger.clear_old_logs(days)
    console.print(f"[green]✓[/green] Cleaned up logs older than {days} days")


@logs.command()
@click.pass_context
def session(ctx):
    """Show events from the current session."""
    from ..core.logging import get_audit_logger
    
    logger = get_audit_logger()
    
    console.print(f"[bold]Session ID: {logger.session_id}[/bold]\n")
    
    events = logger.get_session_events()
    
    if events:
        for event in events:
            if event.session_id == logger.session_id:
                time_str = event.timestamp.split('T')[1].split('.')[0] if 'T' in event.timestamp else event.timestamp
                status = "[green]✓[/green]" if event.success else "[red]✗[/red]"
                console.print(f"{status} [{time_str}] {event.event_type}: {event.action}")
    else:
        console.print("[dim]No events in current session[/dim]")


# Add langgraph command group to main CLI
cli.add_command(langgraph)

@cli.command()
@click.argument('command', required=False)
@click.option('--approval-level', 
              type=click.Choice(['none', 'low', 'medium', 'high', 'destructive']),
              default='medium',
              help='Set human approval level')
@click.option('--auto-approve', is_flag=True, help='Auto-approve all actions')
@click.option('--confirm-all', is_flag=True, help='Confirm all actions with user')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def langgraph_cmd(ctx, command, approval_level, auto_approve, confirm_all, debug):
    """LangGraph agent with React pattern and human-in-the-loop capabilities."""
    from .langgraph_commands import LangGraphAgent
    
    # Initialize config and permissions
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if debug:
        config.debug = True
    
    permission_manager = PermissionManager(config_manager)
    
    try:
        # Initialize LangGraph agent
        agent = LangGraphAgent(config, permission_manager)
        
        if command:
            console.print(f"[blue]Processing command with LangGraph agent...[/blue]")
            result = agent.process_command(command)
            
            if result['success']:
                console.print(f"[green]✓[/green] {result['message']}")
                
                # Show tools used
                if result.get('data', {}).get('tools_used'):
                    tools_used = result['data']['tools_used']
                    console.print(f"[dim]Tools used: {', '.join(tools_used)}[/dim]")
                
                # Show data if available
                if result.get('data') and config.verbose:
                    console.print(result['data'])
            else:
                console.print(f"[red]✗[/red] {result['message']}")
                if result.get('error'):
                    console.print(f"[red]Error:[/red] {result['error']}")
        else:
            # Start interactive mode
            from .langgraph_commands import print_langgraph_banner, print_langgraph_help
            print_langgraph_banner()
            console.print("[dim]Starting LangGraph interactive mode. Type 'help' for commands, 'exit' to quit[/dim]\n")
            
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
            
            # Create prompt session
            history_file = Path.home() / ".sysagent" / "langgraph_history"
            history_file.parent.mkdir(exist_ok=True)
            
            session = PromptSession(
                history=FileHistory(str(history_file)),
                auto_suggest=AutoSuggestFromHistory()
            )
            
            while True:
                try:
                    user_input = session.prompt("langgraph > ")
                    
                    if not user_input.strip():
                        continue
                    
                    if user_input.lower() in ['exit', 'quit']:
                        console.print("[dim]Goodbye![/dim]")
                        break
                    
                    if user_input.lower() == 'help':
                        print_langgraph_help()
                        continue
                    
                    # Process the command
                    console.print(f"[blue]Processing with LangGraph agent...[/blue]")
                    result = agent.process_command(user_input)
                    
                    if result['success']:
                        console.print(f"[green]✓[/green] {result['message']}")
                        
                        # Show tools used
                        if result.get('data', {}).get('tools_used'):
                            tools_used = result['data']['tools_used']
                            console.print(f"[dim]Tools used: {', '.join(tools_used)}[/dim]")
                        
                        # Show data if available
                        if result.get('data') and config.verbose:
                            console.print(result['data'])
                    else:
                        console.print(f"[red]✗[/red] {result['message']}")
                        if result.get('error'):
                            console.print(f"[red]Error:[/red] {result['error']}")
                
                except KeyboardInterrupt:
                    console.print("\n[dim]Use 'exit' to quit[/dim]")
                except EOFError:
                    console.print("\n[dim]Goodbye![/dim]")
                    break
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
                    if config.debug:
                        import traceback
                        console.print(traceback.format_exc())
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if config.debug:
            import traceback
            console.print(traceback.format_exc())


def main():
    """Main entry point."""
    try:
        # Check if no arguments provided, start interactive mode
        if len(sys.argv) == 1:
            # Initialize configuration
            config_manager = ConfigManager()
            config = config_manager.load_config()
            
            # Initialize permission manager
            permission_manager = PermissionManager(config_manager)
            
            # Start interactive mode
            start_interactive_mode(config_manager, permission_manager)
        else:
            cli()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted by user[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


# Helper functions for interactive mode
def handle_config_set(config, permission_manager, key, value):
    """Handle config set command in interactive mode."""
    try:
        # Handle nested keys like 'agent.provider' or 'security.dry_run'
        keys = key.split('.')
        
        # Navigate to the parent object
        parent = config
        for k in keys[:-1]:
            if hasattr(parent, k):
                parent = getattr(parent, k)
            else:
                console.print(f"[red]✗[/red] Configuration key '{key}' not found")
                return
        
        # Set the value
        last_key = keys[-1]
        if hasattr(parent, last_key):
            # Convert value based on the field type
            current_value = getattr(parent, last_key)
            if isinstance(current_value, bool):
                new_value = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(current_value, int):
                new_value = int(value)
            elif isinstance(current_value, float):
                new_value = float(value)
            else:
                new_value = value
            
            setattr(parent, last_key, new_value)
            
            # Save the configuration
            from ..core.config import ConfigManager
            config_manager = ConfigManager()
            config_manager._config = config
            config_manager.save_config()
            
            console.print(f"[green]✓[/green] Set {key} = {new_value}")
        else:
            console.print(f"[red]✗[/red] Configuration key '{key}' not found")
    except Exception as e:
        console.print(f"[red]✗[/red] Error setting configuration: {e}")


def handle_config_get(config, key):
    """Handle config get command in interactive mode."""
    try:
        # Handle nested keys like 'agent.provider' or 'security.dry_run'
        keys = key.split('.')
        value = config
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                console.print(f"[red]✗[/red] Configuration key '{key}' not found")
                return
        
        # Handle enum values
        if hasattr(value, 'value'):
            value = value.value
        
        console.print(f"[green]{key}[/green] = {value}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error getting configuration: {e}")


def handle_permission_grant(permission_manager, tool):
    """Handle permission grant command in interactive mode."""
    try:
        # Get required permissions for the tool
        required_permissions = permission_manager.get_required_permissions(tool)
        
        if not required_permissions:
            console.print(f"[red]✗[/red] Tool '{tool}' not found or has no permissions")
            return
        
        console.print(f"[bold]Granting permissions for tool: {tool}[/bold]")
        
        for perm_request in required_permissions:
            if not perm_request.granted:
                console.print(f"\nRequesting permission: {perm_request.permission}")
                console.print(f"Description: {perm_request.description}")
                console.print(f"Level: {perm_request.level.value}")
                
                granted = permission_manager.request_permission(
                    perm_request.permission,
                    perm_request.level,
                    perm_request.description
                )
                
                if granted:
                    console.print(f"[green]✓[/green] Permission '{perm_request.permission}' granted")
                else:
                    console.print(f"[red]✗[/red] Permission '{perm_request.permission}' denied")
            else:
                console.print(f"[dim]Permission '{perm_request.permission}' already granted[/dim]")
        
        console.print(f"\n[green]✓[/green] Permissions updated for tool: {tool}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error granting permissions: {e}")


def handle_permission_revoke(permission_manager, tool):
    """Handle permission revoke command in interactive mode."""
    try:
        # Get required permissions for the tool
        required_permissions = permission_manager.get_required_permissions(tool)
        
        if not required_permissions:
            console.print(f"[red]✗[/red] Tool '{tool}' not found or has no permissions")
            return
        
        console.print(f"[bold]Revoking permissions for tool: {tool}[/bold]")
        
        revoked_count = 0
        for perm_request in required_permissions:
            if perm_request.granted:
                permission_manager.revoke_permission(perm_request.permission)
                console.print(f"[green]✓[/green] Permission '{perm_request.permission}' revoked")
                revoked_count += 1
            else:
                console.print(f"[dim]Permission '{perm_request.permission}' not granted[/dim]")
        
        if revoked_count > 0:
            console.print(f"\n[green]✓[/green] Revoked {revoked_count} permissions for tool: {tool}")
        else:
            console.print(f"\n[dim]No permissions were revoked for tool: {tool}[/dim]")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error revoking permissions: {e}")


if __name__ == "__main__":
    main() 