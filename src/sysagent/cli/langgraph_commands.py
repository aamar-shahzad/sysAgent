"""
LangGraph CLI commands for SysAgent with human-in-the-loop capabilities.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

from ..core.langgraph_agent import LangGraphAgent
from ..core.config import ConfigManager
from ..core.permissions import PermissionManager

console = Console()


def print_langgraph_banner():
    """Print the LangGraph agent banner."""
    banner = """
╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│  🧠 SysAgent LangGraph CLI v0.1.0 - Advanced React Agent with Human-in-the-Loop                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
"""
    console.print(banner)


def print_langgraph_help():
    """Print help for LangGraph commands."""
    help_text = """
[bold blue]LangGraph Agent Commands:[/bold blue]

[bold]Basic Usage:[/bold]
  sysagent langgraph "your command"     - Run a command with LangGraph agent
  sysagent langgraph repl               - Start interactive LangGraph REPL
  sysagent langgraph chat               - Start conversational mode

[bold]Advanced Features:[/bold]
  sysagent langgraph history            - Show conversation history
  sysagent langgraph clear-history      - Clear conversation history
  sysagent langgraph tools              - List available LangGraph tools
  sysagent langgraph status             - Show agent status and memory

[bold]Human-in-the-Loop:[/bold]
  sysagent langgraph --approval-level   - Set approval level (none/low/medium/high/destructive)
  sysagent langgraph --auto-approve     - Auto-approve all actions
  sysagent langgraph --confirm-all      - Confirm all actions with user

[bold]Examples:[/bold]
  sysagent langgraph "analyze my system and suggest optimizations"
  sysagent langgraph "clean up files and organize my downloads"
  sysagent langgraph "monitor processes and kill any using too much CPU"
"""
    console.print(Panel(help_text, title="🧠 LangGraph Agent Help", border_style="blue"))


def print_approval_levels():
    """Print available approval levels."""
    levels = Table(title="Human Approval Levels")
    levels.add_column("Level", style="cyan")
    levels.add_column("Description", style="white")
    levels.add_column("Actions", style="yellow")
    
    levels.add_row("none", "No approval needed", "Read-only operations")
    levels.add_row("low_risk", "Low risk approval", "File listing, system info")
    levels.add_row("medium_risk", "Medium risk approval", "File operations, process info")
    levels.add_row("high_risk", "High risk approval", "Process management, network ops")
    levels.add_row("destructive", "Destructive approval", "File deletion, system shutdown")
    
    console.print(levels)


def get_approval_level(level_str: str) -> str:
    """Convert approval level string to enum value."""
    level_map = {
        "none": "NONE",
        "low": "LOW_RISK", 
        "medium": "MEDIUM_RISK",
        "high": "HIGH_RISK",
        "destructive": "DESTRUCTIVE"
    }
    return level_map.get(level_str.lower(), "MEDIUM_RISK")


def handle_human_approval(actions: list, approval_level: str) -> bool:
    """Handle human approval for actions."""
    if approval_level == "NONE":
        return True

    console.print(f"\n[bold yellow]⚠️ Human Approval Required ({approval_level})[/bold yellow]")

    # Display actions
    table = Table(title="Pending Actions")
    table.add_column("ID", style="magenta")
    table.add_column("Tool", style="cyan")
    table.add_column("Action", style="white")
    table.add_column("Parameters", style="yellow")

    for i, action in enumerate(actions):
        tool_name = action.get("name", "unknown")
        tool_args = action.get("args", {})
        table.add_row(str(i + 1), tool_name, str(tool_args.get("action", "")), str(tool_args))

    console.print(table)

    # Ask for approval
    if approval_level in ["HIGH_RISK", "DESTRUCTIVE"]:
        console.print("[bold red]⚠️ WARNING: These are high-risk actions![/bold red]")

    approved_actions = []
    for i, action in enumerate(actions):
        prompt = f"Approve action {i + 1}? (y/n/all)"
        response = Prompt.ask(prompt, choices=["y", "n", "all"], default="n").lower()

        if response == "y":
            approved_actions.append(action)
        elif response == "all":
            approved_actions.extend(actions[i:])
            break
        elif response == "n":
            console.print(f"[dim]Skipping action {i + 1}[/dim]")

    if not approved_actions:
        console.print("[red]No actions approved. Aborting.[/red]")
        return False

    # Modify the original list to only include approved actions
    actions[:] = approved_actions
    return True


@click.group()
@click.option('--approval-level', 
              type=click.Choice(['none', 'low', 'medium', 'high', 'destructive']),
              default='medium',
              help='Set human approval level')
@click.option('--auto-approve', is_flag=True, help='Auto-approve all actions')
@click.option('--confirm-all', is_flag=True, help='Confirm all actions with user')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def langgraph(ctx, approval_level, auto_approve, confirm_all, debug):
    """LangGraph agent with React pattern and human-in-the-loop capabilities."""
    # Initialize config and permissions
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if debug:
        config.debug = True
    
    permission_manager = PermissionManager(config_manager)
    
    # Store in context
    ctx.obj = {
        'config': config,
        'permission_manager': permission_manager,
        'approval_level': get_approval_level(approval_level),
        'auto_approve': auto_approve,
        'confirm_all': confirm_all
    }


@langgraph.command()
@click.argument('command', required=False)
@click.option('--async', 'use_async', is_flag=True, help='Use async processing')
@click.pass_context
def run(ctx, command, use_async):
    """Run a command with LangGraph agent."""
    if not command:
        console.print("[red]Error:[/red] No command provided")
        console.print("Usage: sysagent langgraph run \"your command here\"")
        return
    
    config = ctx.obj['config']
    config_manager = ctx.obj.get('config_manager', ConfigManager())
    permission_manager = ctx.obj['permission_manager']
    
    try:
        # Initialize LangGraph agent
        agent = LangGraphAgent(config_manager, permission_manager)
        
        console.print(f"[blue]Processing command with LangGraph agent...[/blue]")
        
        if use_async:
            # Async processing
            result = asyncio.run(agent.process_command_async(command))
        else:
            # Sync processing
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
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if config.debug:
            import traceback
            console.print(traceback.format_exc())


@langgraph.command()
@click.pass_context
def repl(ctx):
    """Start interactive LangGraph REPL."""
    print_langgraph_banner()
    console.print("[dim]Starting LangGraph interactive mode. Type 'help' for commands, 'exit' to quit[/dim]\n")
    
    config = ctx.obj['config']
    permission_manager = ctx.obj['permission_manager']
    approval_level = ctx.obj['approval_level']
    auto_approve = ctx.obj['auto_approve']
    
    # Initialize LangGraph agent
    agent = LangGraphAgent(config, permission_manager)
    
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    
    # Create prompt session
    history_file = Path.home() / ".sysagent" / "langgraph_history"
    history_file.parent.mkdir(exist_ok=True)
    
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter([
            'help', 'exit', 'quit', 'history', 'clear-history', 'tools', 'status',
            'show system info', 'analyze performance', 'clean up files',
            'monitor processes', 'check network', 'organize downloads'
        ])
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
            
            if user_input.lower() == 'history':
                history = agent.get_conversation_history()
                if history:
                    console.print(f"[dim]Conversation history: {len(history)} messages[/dim]")
                else:
                    console.print("[dim]No conversation history[/dim]")
                continue
            
            if user_input.lower() == 'clear-history':
                agent.clear_conversation_history()
                console.print("[green]✓[/green] Conversation history cleared")
                continue
            
            if user_input.lower() == 'tools':
                console.print("[dim]Available LangGraph tools: file_operations, system_info, process_management, network_diagnostics[/dim]")
                continue
            
            if user_input.lower() == 'status':
                console.print(f"[dim]Session ID: {agent.session_id}[/dim]")
                console.print(f"[dim]Approval Level: {approval_level}[/dim]")
                console.print(f"[dim]Auto-approve: {auto_approve}[/dim]")
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


@langgraph.command()
@click.pass_context
def chat(ctx):
    """Start conversational mode with memory."""
    print_langgraph_banner()
    console.print("[dim]Starting conversational mode with memory. Type 'help' for commands, 'exit' to quit[/dim]\n")
    
    config = ctx.obj['config']
    permission_manager = ctx.obj['permission_manager']
    
    # Initialize LangGraph agent
    agent = LangGraphAgent(config, permission_manager)
    
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    
    # Create prompt session
    history_file = Path.home() / ".sysagent" / "langgraph_chat_history"
    history_file.parent.mkdir(exist_ok=True)
    
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory()
    )
    
    console.print("[green]Chat started! The agent will remember our conversation.[/green]\n")
    
    while True:
        try:
            user_input = session.prompt("chat > ")
            
            if not user_input.strip():
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("[dim]Goodbye![/dim]")
                break
            
            if user_input.lower() == 'help':
                console.print("[dim]Just chat naturally! The agent will remember our conversation and can help with system tasks.[/dim]")
                continue
            
            # Process the command
            result = agent.process_command(user_input)
            
            if result['success']:
                console.print(f"[green]Agent:[/green] {result['message']}")
            else:
                console.print(f"[red]Error:[/red] {result['message']}")
        
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit[/dim]")
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")


@langgraph.command()
@click.pass_context
def history(ctx):
    """Show conversation history."""
    config = ctx.obj['config']
    permission_manager = ctx.obj['permission_manager']
    
    agent = LangGraphAgent(config, permission_manager)
    history = agent.get_conversation_history()
    
    if history:
        console.print(f"[dim]Conversation history ({len(history)} messages):[/dim]")
        for i, msg in enumerate(history[-10:], 1):  # Show last 10 messages
            if hasattr(msg, 'content'):
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                console.print(f"[dim]{i}. {content}[/dim]")
    else:
        console.print("[dim]No conversation history[/dim]")


@langgraph.command()
@click.pass_context
def clear_history(ctx):
    """Clear conversation history."""
    config = ctx.obj['config']
    permission_manager = ctx.obj['permission_manager']
    
    agent = LangGraphAgent(config, permission_manager)
    agent.clear_conversation_history()
    
    console.print("[green]✓[/green] Conversation history cleared")


@langgraph.command()
@click.pass_context
def tools(ctx):
    """List available LangGraph tools."""
    tools_info = [
        {"name": "file_operations", "description": "Perform file system operations", "actions": "list, read, write, move, delete, cleanup, organize"},
        {"name": "system_info", "description": "Get system information and metrics", "actions": "overview, cpu, memory, disk, network, processes"},
        {"name": "process_management", "description": "Manage system processes", "actions": "list, kill, monitor, restart"},
        {"name": "network_diagnostics", "description": "Perform network diagnostics", "actions": "ping, traceroute, connectivity, dns"}
    ]
    
    table = Table(title="LangGraph Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Actions", style="yellow")
    
    for tool in tools_info:
        table.add_row(tool["name"], tool["description"], tool["actions"])
    
    console.print(table)


@langgraph.command()
@click.pass_context
def status(ctx):
    """Show agent status and memory."""
    config = ctx.obj['config']
    permission_manager = ctx.obj['permission_manager']
    
    agent = LangGraphAgent(config, permission_manager)
    history = agent.get_conversation_history()
    
    console.print(f"[dim]Session ID: {agent.session_id}[/dim]")
    console.print(f"[dim]Messages in memory: {len(history)}[/dim]")
    console.print(f"[dim]LLM Provider: {config.agent.provider.value}[/dim]")
    console.print(f"[dim]Model: {config.agent.model}[/dim]")
    console.print(f"[dim]Debug Mode: {config.debug}[/dim]")


@langgraph.command()
@click.pass_context
def approval_levels(ctx):
    """Show available approval levels."""
    print_approval_levels() 