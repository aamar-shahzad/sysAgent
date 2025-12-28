"""
Dashboard GUI for SysAgent - OS Control and Monitoring.
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    import customtkinter as ctk
    USE_CUSTOMTKINTER = True
except ImportError:
    USE_CUSTOMTKINTER = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class DashboardWindow:
    """Dashboard window for OS control and monitoring."""

    def __init__(self):
        self.root = None
        self.config_manager = None
        self.permission_manager = None
        self.tool_executor = None
        self.update_thread = None
        self.running = False
        self.content_frames = {}  # Initialize empty dict
        self.sidebar = None
        self.content = None
        self._initialize_managers()

    def _initialize_managers(self):
        """Initialize config, permission managers, and tools."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..tools.base import ToolExecutor
            
            self.config_manager = ConfigManager()
            self.permission_manager = PermissionManager(self.config_manager)
            self.tool_executor = ToolExecutor(self.permission_manager)
            
            # Register tools
            from ..tools import (
                FileTool, SystemInfoTool, ProcessTool, NetworkTool,
                SystemControlTool, MonitoringTool
            )
            
            self.tool_executor.register_tool(FileTool())
            self.tool_executor.register_tool(SystemInfoTool())
            self.tool_executor.register_tool(ProcessTool())
            self.tool_executor.register_tool(NetworkTool())
            self.tool_executor.register_tool(SystemControlTool())
            self.tool_executor.register_tool(MonitoringTool())
            
        except Exception as e:
            print(f"Warning: Could not initialize managers: {e}")

    def _create_window(self):
        """Create the main dashboard window."""
        if USE_CUSTOMTKINTER:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title("SysAgent Dashboard - OS Control")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Protocol for closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        return self.root

    def _on_closing(self):
        """Handle window closing."""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1)
        self.root.destroy()

    def _create_widgets(self):
        """Create all widgets for the dashboard."""
        # Main container with sidebar and content
        if USE_CUSTOMTKINTER:
            # Sidebar
            self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
            self.sidebar.pack(side="left", fill="y")
            self.sidebar.pack_propagate(False)
            
            # Content area
            self.content = ctk.CTkFrame(self.root)
            self.content.pack(side="right", fill="both", expand=True)
        else:
            # Sidebar
            self.sidebar = ttk.Frame(self.root, width=200)
            self.sidebar.pack(side="left", fill="y")
            self.sidebar.pack_propagate(False)
            
            # Content area
            self.content = ttk.Frame(self.root)
            self.content.pack(side="right", fill="both", expand=True)
        
        self._create_sidebar()
        self._create_content_area()

    def _create_sidebar(self):
        """Create the sidebar with navigation."""
        if USE_CUSTOMTKINTER:
            # Logo/Title
            logo = ctk.CTkLabel(
                self.sidebar,
                text="🧠 SysAgent",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            logo.pack(pady=30)
            
            # Navigation buttons
            nav_buttons = [
                ("🏠 Dashboard", self._show_dashboard),
                ("💻 System Info", self._show_system_info),
                ("📊 Processes", self._show_processes),
                ("📁 Files", self._show_files),
                ("🌐 Network", self._show_network),
                ("⚙️ Services", self._show_services),
                ("🔋 Power", self._show_power),
                ("📈 Monitoring", self._show_monitoring),
                ("🛡️ Security", self._show_security),
                ("⚡ Quick Actions", self._show_quick_actions),
            ]
            
            for text, command in nav_buttons:
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=text,
                    command=command,
                    width=180,
                    height=35,
                    anchor="w"
                )
                btn.pack(pady=3, padx=10)
            
            # Settings button at bottom
            settings_btn = ctk.CTkButton(
                self.sidebar,
                text="⚙️ Settings",
                command=self._open_settings,
                width=180,
                fg_color="gray"
            )
            settings_btn.pack(side="bottom", pady=20, padx=10)
            
        else:
            # Logo/Title
            logo = ttk.Label(
                self.sidebar,
                text="🧠 SysAgent",
                font=("Helvetica", 16, "bold")
            )
            logo.pack(pady=20)
            
            # Navigation buttons
            nav_buttons = [
                ("Dashboard", self._show_dashboard),
                ("System Info", self._show_system_info),
                ("Processes", self._show_processes),
                ("Files", self._show_files),
                ("Network", self._show_network),
                ("Services", self._show_services),
                ("Power", self._show_power),
                ("Monitoring", self._show_monitoring),
                ("Security", self._show_security),
                ("Quick Actions", self._show_quick_actions),
            ]
            
            for text, command in nav_buttons:
                btn = ttk.Button(self.sidebar, text=text, command=command, width=20)
                btn.pack(pady=3, padx=10)
            
            # Settings button at bottom
            settings_btn = ttk.Button(
                self.sidebar,
                text="Settings",
                command=self._open_settings
            )
            settings_btn.pack(side="bottom", pady=20, padx=10)

    def _create_content_area(self):
        """Create the main content area."""
        self.content_frames = {}
        
        # Create frames for each section
        sections = [
            "dashboard", "system_info", "processes", "files",
            "network", "services", "power", "monitoring", "security", "quick_actions"
        ]
        
        for section in sections:
            if USE_CUSTOMTKINTER:
                frame = ctk.CTkFrame(self.content)
            else:
                frame = ttk.Frame(self.content)
            self.content_frames[section] = frame
        
        # Show dashboard by default
        self._show_dashboard()

    def _clear_content(self):
        """Clear the current content frame."""
        if not self.content_frames:
            return
        for frame in self.content_frames.values():
            frame.pack_forget()

    def _show_dashboard(self):
        """Show the main dashboard."""
        self._clear_content()
        frame = self.content_frames["dashboard"]
        
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            # Title
            title = ctk.CTkLabel(
                frame,
                text="System Dashboard",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            # Stats grid
            stats_frame = ctk.CTkFrame(frame)
            stats_frame.pack(fill="x", padx=20, pady=10)
            
            # CPU, Memory, Disk stats
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                stats = [
                    ("CPU Usage", f"{cpu_percent}%", self._get_color_for_percent(cpu_percent)),
                    ("Memory Usage", f"{memory.percent}%", self._get_color_for_percent(memory.percent)),
                    ("Disk Usage", f"{disk.percent}%", self._get_color_for_percent(disk.percent)),
                    ("Processes", str(len(psutil.pids())), "blue"),
                ]
            else:
                stats = [
                    ("CPU Usage", "N/A", "gray"),
                    ("Memory Usage", "N/A", "gray"),
                    ("Disk Usage", "N/A", "gray"),
                    ("Processes", "N/A", "gray"),
                ]
            
            for i, (label, value, color) in enumerate(stats):
                stat_box = ctk.CTkFrame(stats_frame)
                stat_box.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
                stats_frame.grid_columnconfigure(i, weight=1)
                
                stat_label = ctk.CTkLabel(stat_box, text=label, font=ctk.CTkFont(size=12))
                stat_label.pack(pady=(10, 5))
                
                stat_value = ctk.CTkLabel(
                    stat_box,
                    text=value,
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=color
                )
                stat_value.pack(pady=(5, 10))
            
            # System info section
            info_frame = ctk.CTkFrame(frame)
            info_frame.pack(fill="x", padx=20, pady=10)
            
            info_label = ctk.CTkLabel(
                info_frame,
                text="System Information",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            info_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            import platform
            info_text = f"""
Platform: {platform.system()} {platform.release()}
Machine: {platform.machine()}
Processor: {platform.processor()}
Python: {platform.python_version()}
"""
            if PSUTIL_AVAILABLE:
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.now() - boot_time
                info_text += f"Uptime: {str(uptime).split('.')[0]}"
            
            info_content = ctk.CTkLabel(
                info_frame,
                text=info_text,
                font=ctk.CTkFont(size=12),
                justify="left"
            )
            info_content.pack(anchor="w", padx=10, pady=(5, 10))
            
            # Recent activity (placeholder)
            activity_frame = ctk.CTkFrame(frame)
            activity_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            activity_label = ctk.CTkLabel(
                activity_frame,
                text="Quick Actions",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            activity_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            # Quick action buttons
            btn_frame = ctk.CTkFrame(activity_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            quick_actions = [
                ("🔄 Refresh", self._refresh_dashboard),
                ("🧹 Clean Temp", self._clean_temp_files),
                ("📊 Top Processes", self._show_top_processes),
                ("🌐 Check Internet", self._check_internet),
            ]
            
            for text, command in quick_actions:
                btn = ctk.CTkButton(btn_frame, text=text, command=command, width=120)
                btn.pack(side="left", padx=5)
            
        else:
            # Fallback to ttk
            title = ttk.Label(frame, text="System Dashboard", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
            
            # Stats
            stats_frame = ttk.Frame(frame)
            stats_frame.pack(fill="x", padx=20, pady=10)
            
            if PSUTIL_AVAILABLE:
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                ttk.Label(stats_frame, text=f"CPU: {cpu}%").pack(side="left", padx=20)
                ttk.Label(stats_frame, text=f"Memory: {memory.percent}%").pack(side="left", padx=20)
                ttk.Label(stats_frame, text=f"Disk: {disk.percent}%").pack(side="left", padx=20)
        
        frame.pack(fill="both", expand=True)
        
        # Start auto-refresh
        self._start_auto_refresh()

    def _get_color_for_percent(self, percent: float) -> str:
        """Get color based on percentage value."""
        if percent < 50:
            return "green"
        elif percent < 80:
            return "orange"
        else:
            return "red"

    def _show_system_info(self):
        """Show detailed system information."""
        self._clear_content()
        frame = self.content_frames["system_info"]
        
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                frame,
                text="System Information",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            # Scrollable frame for system info
            scroll_frame = ctk.CTkScrollableFrame(frame)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Get system info using tool
            if self.tool_executor:
                result = self.tool_executor.execute_tool("system_info_tool", action="overview")
                if result.success and result.data:
                    self._display_dict_data(scroll_frame, result.data)
                else:
                    ctk.CTkLabel(scroll_frame, text=result.message).pack()
            else:
                ctk.CTkLabel(scroll_frame, text="Tools not available").pack()
        else:
            title = ttk.Label(frame, text="System Information", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
        
        frame.pack(fill="both", expand=True)

    def _show_processes(self):
        """Show process management interface."""
        self._clear_content()
        frame = self.content_frames["processes"]
        
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            # Title and controls
            header = ctk.CTkFrame(frame, fg_color="transparent")
            header.pack(fill="x", padx=20, pady=10)
            
            title = ctk.CTkLabel(
                header,
                text="Process Manager",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(side="left")
            
            refresh_btn = ctk.CTkButton(
                header,
                text="🔄 Refresh",
                command=lambda: self._refresh_processes(tree),
                width=100
            )
            refresh_btn.pack(side="right", padx=5)
            
            kill_btn = ctk.CTkButton(
                header,
                text="⛔ Kill Selected",
                command=lambda: self._kill_selected_process(tree),
                fg_color="red",
                width=120
            )
            kill_btn.pack(side="right", padx=5)
            
            # Search
            search_frame = ctk.CTkFrame(frame, fg_color="transparent")
            search_frame.pack(fill="x", padx=20, pady=5)
            
            search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search processes...", width=300)
            search_entry.pack(side="left")
            
            # Process list (using treeview)
            tree_frame = ctk.CTkFrame(frame)
            tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Create treeview (ttk widget)
            columns = ("PID", "Name", "CPU %", "Memory %", "Status")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
            
            for col in columns:
                tree.heading(col, text=col, command=lambda c=col: self._sort_processes(tree, c))
                tree.column(col, width=100)
            
            tree.column("Name", width=200)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Populate processes
            self._refresh_processes(tree)
            
        else:
            title = ttk.Label(frame, text="Process Manager", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
            
            columns = ("PID", "Name", "CPU %", "Memory %", "Status")
            tree = ttk.Treeview(frame, columns=columns, show="headings")
            
            for col in columns:
                tree.heading(col, text=col)
            
            tree.pack(fill="both", expand=True, padx=20, pady=10)
            self._refresh_processes(tree)
        
        frame.pack(fill="both", expand=True)

    def _refresh_processes(self, tree):
        """Refresh the process list."""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        if PSUTIL_AVAILABLE:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = proc.info
                    processes.append((
                        info['pid'],
                        info['name'],
                        f"{info['cpu_percent']:.1f}",
                        f"{info['memory_percent']:.1f}",
                        info['status']
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: float(x[2]), reverse=True)
            
            for proc in processes[:100]:  # Limit to 100 processes
                tree.insert("", "end", values=proc)

    def _kill_selected_process(self, tree):
        """Kill the selected process."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a process to kill")
            return
        
        item = tree.item(selection[0])
        pid = item['values'][0]
        name = item['values'][1]
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to kill process {name} (PID: {pid})?"):
            try:
                if PSUTIL_AVAILABLE:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    messagebox.showinfo("Success", f"Process {name} terminated")
                    self._refresh_processes(tree)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to kill process: {e}")

    def _sort_processes(self, tree, column):
        """Sort processes by column."""
        items = [(tree.set(item, column), item) for item in tree.get_children("")]
        
        try:
            items.sort(key=lambda x: float(x[0]), reverse=True)
        except ValueError:
            items.sort(key=lambda x: x[0])
        
        for index, (_, item) in enumerate(items):
            tree.move(item, "", index)

    def _show_files(self):
        """Show file browser interface."""
        self._clear_content()
        frame = self.content_frames["files"]
        
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                frame,
                text="File Browser",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            # Path bar
            path_frame = ctk.CTkFrame(frame, fg_color="transparent")
            path_frame.pack(fill="x", padx=20, pady=5)
            
            self.current_path = tk.StringVar(value=str(Path.home()))
            path_entry = ctk.CTkEntry(path_frame, textvariable=self.current_path, width=500)
            path_entry.pack(side="left", fill="x", expand=True)
            
            go_btn = ctk.CTkButton(
                path_frame,
                text="Go",
                command=lambda: self._browse_directory(tree, self.current_path.get()),
                width=60
            )
            go_btn.pack(side="left", padx=5)
            
            home_btn = ctk.CTkButton(
                path_frame,
                text="🏠",
                command=lambda: self._browse_directory(tree, str(Path.home())),
                width=40
            )
            home_btn.pack(side="left", padx=5)
            
            # File list
            tree_frame = ctk.CTkFrame(frame)
            tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            columns = ("Name", "Size", "Type", "Modified")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
            
            tree.heading("Name", text="Name")
            tree.heading("Size", text="Size")
            tree.heading("Type", text="Type")
            tree.heading("Modified", text="Modified")
            
            tree.column("Name", width=300)
            tree.column("Size", width=100)
            tree.column("Type", width=100)
            tree.column("Modified", width=150)
            
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Double-click to navigate
            tree.bind("<Double-1>", lambda e: self._on_file_double_click(tree))
            
            # Populate
            self._browse_directory(tree, self.current_path.get())
            
            # Action buttons
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=20, pady=10)
            
            actions = [
                ("🧹 Clean Temp Files", self._clean_temp_files),
                ("📁 Organize Downloads", self._organize_downloads),
                ("🔍 Find Large Files", self._find_large_files),
            ]
            
            for text, command in actions:
                btn = ctk.CTkButton(btn_frame, text=text, command=command, width=150)
                btn.pack(side="left", padx=5)
        else:
            title = ttk.Label(frame, text="File Browser", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
        
        frame.pack(fill="both", expand=True)

    def _browse_directory(self, tree, path: str):
        """Browse a directory and display its contents."""
        from pathlib import Path
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return
            
            self.current_path.set(str(dir_path))
            
            # Add parent directory
            if dir_path.parent != dir_path:
                tree.insert("", "end", values=("..", "", "Directory", ""))
            
            # List directory contents
            items = []
            for item in dir_path.iterdir():
                try:
                    stat = item.stat()
                    size = self._format_size(stat.st_size) if item.is_file() else ""
                    item_type = "Directory" if item.is_dir() else item.suffix or "File"
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    items.append((item.name, size, item_type, modified, item.is_dir()))
                except (PermissionError, OSError):
                    continue
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (not x[4], x[0].lower()))
            
            for name, size, item_type, modified, is_dir in items:
                tree.insert("", "end", values=(name, size, item_type, modified))
                
        except PermissionError:
            messagebox.showerror("Error", "Permission denied")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to browse directory: {e}")

    def _on_file_double_click(self, tree):
        """Handle double-click on file/directory."""
        from pathlib import Path
        
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        name = item['values'][0]
        
        current = Path(self.current_path.get())
        
        if name == "..":
            new_path = current.parent
        else:
            new_path = current / name
        
        if new_path.is_dir():
            self._browse_directory(tree, str(new_path))

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def _show_network(self):
        """Show network information interface."""
        self._clear_content()
        frame = self.content_frames["network"]
        
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                frame,
                text="Network Information",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            # Network stats
            if PSUTIL_AVAILABLE:
                net_io = psutil.net_io_counters()
                
                stats_frame = ctk.CTkFrame(frame)
                stats_frame.pack(fill="x", padx=20, pady=10)
                
                stats = [
                    ("Bytes Sent", self._format_size(net_io.bytes_sent)),
                    ("Bytes Received", self._format_size(net_io.bytes_recv)),
                    ("Packets Sent", str(net_io.packets_sent)),
                    ("Packets Received", str(net_io.packets_recv)),
                ]
                
                for i, (label, value) in enumerate(stats):
                    stat_box = ctk.CTkFrame(stats_frame)
                    stat_box.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
                    stats_frame.grid_columnconfigure(i, weight=1)
                    
                    ctk.CTkLabel(stat_box, text=label).pack(pady=(10, 5))
                    ctk.CTkLabel(stat_box, text=value, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(5, 10))
            
            # Network interfaces
            interfaces_frame = ctk.CTkFrame(frame)
            interfaces_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            ctk.CTkLabel(
                interfaces_frame,
                text="Network Interfaces",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", padx=10, pady=(10, 5))
            
            if PSUTIL_AVAILABLE:
                scroll_frame = ctk.CTkScrollableFrame(interfaces_frame)
                scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                for interface, addrs in psutil.net_if_addrs().items():
                    iface_frame = ctk.CTkFrame(scroll_frame)
                    iface_frame.pack(fill="x", pady=5)
                    
                    ctk.CTkLabel(
                        iface_frame,
                        text=interface,
                        font=ctk.CTkFont(weight="bold")
                    ).pack(anchor="w", padx=10, pady=5)
                    
                    for addr in addrs:
                        addr_text = f"  {addr.family.name}: {addr.address}"
                        ctk.CTkLabel(iface_frame, text=addr_text).pack(anchor="w", padx=20)
            
            # Action buttons
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=20, pady=10)
            
            actions = [
                ("🌐 Check Internet", self._check_internet),
                ("📡 Ping Test", self._ping_test),
                ("🔍 Port Scan", self._port_scan),
            ]
            
            for text, command in actions:
                btn = ctk.CTkButton(btn_frame, text=text, command=command, width=120)
                btn.pack(side="left", padx=5)
        else:
            title = ttk.Label(frame, text="Network Information", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
        
        frame.pack(fill="both", expand=True)

    def _show_services(self):
        """Show services management interface."""
        self._clear_content()
        frame = self.content_frames["services"]
        
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                frame,
                text="System Services",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            ctk.CTkLabel(
                frame,
                text="Service management requires elevated privileges.\nUse CLI commands for service control.",
                font=ctk.CTkFont(size=12)
            ).pack(pady=20)
        else:
            title = ttk.Label(frame, text="System Services", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
        
        frame.pack(fill="both", expand=True)

    def _show_power(self):
        """Show power management interface."""
        self._clear_content()
        frame = self.content_frames["power"]
        
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                frame,
                text="Power Management",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            # Battery info
            if PSUTIL_AVAILABLE:
                battery = psutil.sensors_battery()
                if battery:
                    battery_frame = ctk.CTkFrame(frame)
                    battery_frame.pack(fill="x", padx=20, pady=10)
                    
                    ctk.CTkLabel(
                        battery_frame,
                        text=f"🔋 Battery: {battery.percent}%",
                        font=ctk.CTkFont(size=20, weight="bold")
                    ).pack(pady=10)
                    
                    status = "Charging" if battery.power_plugged else "Discharging"
                    ctk.CTkLabel(battery_frame, text=f"Status: {status}").pack()
                    
                    if battery.secsleft > 0:
                        time_left = battery.secsleft // 3600
                        mins_left = (battery.secsleft % 3600) // 60
                        ctk.CTkLabel(battery_frame, text=f"Time remaining: {time_left}h {mins_left}m").pack()
                else:
                    ctk.CTkLabel(frame, text="No battery detected (desktop system)").pack(pady=20)
            
            # Power actions (disabled for safety)
            ctk.CTkLabel(
                frame,
                text="Power actions are disabled in GUI for safety.\nUse CLI commands for power management.",
                font=ctk.CTkFont(size=12)
            ).pack(pady=20)
        else:
            title = ttk.Label(frame, text="Power Management", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
        
        frame.pack(fill="both", expand=True)

    def _show_monitoring(self):
        """Show monitoring interface."""
        self._clear_content()
        frame = self.content_frames["monitoring"]
        
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                frame,
                text="System Monitoring",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            # Real-time stats
            self.monitoring_labels = {}
            
            stats_frame = ctk.CTkFrame(frame)
            stats_frame.pack(fill="x", padx=20, pady=10)
            
            metrics = ["CPU", "Memory", "Disk I/O", "Network I/O"]
            
            for i, metric in enumerate(metrics):
                box = ctk.CTkFrame(stats_frame)
                box.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
                stats_frame.grid_columnconfigure(i, weight=1)
                
                ctk.CTkLabel(box, text=metric).pack(pady=(10, 5))
                label = ctk.CTkLabel(box, text="0%", font=ctk.CTkFont(size=24, weight="bold"))
                label.pack(pady=(5, 10))
                self.monitoring_labels[metric] = label
            
            # Start monitoring updates
            self._start_monitoring_updates()
        else:
            title = ttk.Label(frame, text="System Monitoring", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
        
        frame.pack(fill="both", expand=True)

    def _show_security(self):
        """Show security interface."""
        self._clear_content()
        frame = self.content_frames["security"]
        
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                frame,
                text="Security",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            # Security actions
            actions = [
                ("🔍 Run Security Scan", self._run_security_scan),
                ("🔐 Check Permissions", self._check_permissions),
                ("📋 View Audit Log", self._view_audit_log),
            ]
            
            for text, command in actions:
                btn = ctk.CTkButton(frame, text=text, command=command, width=200)
                btn.pack(pady=5)
        else:
            title = ttk.Label(frame, text="Security", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
        
        frame.pack(fill="both", expand=True)

    def _show_quick_actions(self):
        """Show quick actions interface."""
        self._clear_content()
        frame = self.content_frames["quick_actions"]
        
        for widget in frame.winfo_children():
            widget.destroy()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                frame,
                text="Quick Actions",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            actions = [
                ("🧹 Clean Temporary Files", self._clean_temp_files),
                ("📁 Organize Downloads", self._organize_downloads),
                ("🔍 Find Large Files", self._find_large_files),
                ("📊 Show Top Processes", self._show_top_processes),
                ("🌐 Check Internet Connection", self._check_internet),
                ("💾 Show Disk Usage", self._show_disk_usage),
                ("🔄 Refresh System Info", self._refresh_dashboard),
            ]
            
            for text, command in actions:
                btn = ctk.CTkButton(frame, text=text, command=command, width=300)
                btn.pack(pady=5)
        else:
            title = ttk.Label(frame, text="Quick Actions", font=("Helvetica", 18, "bold"))
            title.pack(pady=20)
        
        frame.pack(fill="both", expand=True)

    def _display_dict_data(self, parent, data: Dict, level: int = 0):
        """Display dictionary data in a readable format."""
        for key, value in data.items():
            if isinstance(value, dict):
                if USE_CUSTOMTKINTER:
                    frame = ctk.CTkFrame(parent)
                    frame.pack(fill="x", pady=5, padx=level*20)
                    ctk.CTkLabel(
                        frame,
                        text=str(key).replace("_", " ").title(),
                        font=ctk.CTkFont(weight="bold")
                    ).pack(anchor="w", padx=10, pady=5)
                    self._display_dict_data(frame, value, level + 1)
                else:
                    ttk.Label(parent, text=f"{key}:", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=level*20)
                    self._display_dict_data(parent, value, level + 1)
            else:
                text = f"{str(key).replace('_', ' ').title()}: {value}"
                if USE_CUSTOMTKINTER:
                    ctk.CTkLabel(parent, text=text).pack(anchor="w", padx=10 + level*20, pady=2)
                else:
                    ttk.Label(parent, text=text).pack(anchor="w", padx=level*20)

    # Quick action methods
    def _refresh_dashboard(self):
        """Refresh the dashboard."""
        self._show_dashboard()

    def _clean_temp_files(self):
        """Clean temporary files."""
        if self.tool_executor:
            result = self.tool_executor.execute_tool("file_tool", action="cleanup")
            if result.success:
                messagebox.showinfo("Success", f"Cleanup complete!\n{result.message}")
            else:
                messagebox.showerror("Error", result.message)

    def _organize_downloads(self):
        """Organize downloads folder."""
        from pathlib import Path
        downloads = Path.home() / "Downloads"
        
        if self.tool_executor:
            result = self.tool_executor.execute_tool("file_tool", action="organize", source_dir=str(downloads))
            if result.success:
                messagebox.showinfo("Success", f"Organization complete!\n{result.message}")
            else:
                messagebox.showerror("Error", result.message)

    def _find_large_files(self):
        """Find large files."""
        if self.tool_executor:
            result = self.tool_executor.execute_tool("file_tool", action="search", path=str(Path.home()))
            if result.success:
                messagebox.showinfo("Large Files", f"Found {result.data.get('count', 0)} files")
            else:
                messagebox.showerror("Error", result.message)

    def _show_top_processes(self):
        """Show top processes."""
        self._show_processes()

    def _check_internet(self):
        """Check internet connectivity."""
        if self.tool_executor:
            result = self.tool_executor.execute_tool("network_tool", action="ping", host="google.com")
            if result.success:
                messagebox.showinfo("Internet Check", "Internet connection is working!")
            else:
                messagebox.showerror("Internet Check", "No internet connection detected")

    def _show_disk_usage(self):
        """Show disk usage."""
        if PSUTIL_AVAILABLE:
            partitions = psutil.disk_partitions()
            info = []
            for part in partitions:
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    info.append(f"{part.mountpoint}: {usage.percent}% used ({self._format_size(usage.used)} / {self._format_size(usage.total)})")
                except:
                    continue
            messagebox.showinfo("Disk Usage", "\n".join(info))

    def _ping_test(self):
        """Run ping test."""
        host = tk.simpledialog.askstring("Ping Test", "Enter host to ping:")
        if host and self.tool_executor:
            result = self.tool_executor.execute_tool("network_tool", action="ping", host=host)
            messagebox.showinfo("Ping Result", result.message)

    def _port_scan(self):
        """Run port scan."""
        messagebox.showinfo("Port Scan", "Use CLI for port scanning: sysagent run 'scan ports on localhost'")

    def _run_security_scan(self):
        """Run security scan."""
        messagebox.showinfo("Security Scan", "Use CLI for security scanning: sysagent run 'run security scan'")

    def _check_permissions(self):
        """Check current permissions."""
        if self.permission_manager:
            perms = self.permission_manager.get_granted_permissions()
            messagebox.showinfo("Permissions", f"Granted permissions:\n" + "\n".join(perms))

    def _view_audit_log(self):
        """View audit log."""
        messagebox.showinfo("Audit Log", "Audit log viewing not yet implemented")

    def _start_auto_refresh(self):
        """Start auto-refresh for dashboard."""
        self.running = True
        
        def refresh_loop():
            while self.running:
                time.sleep(5)
                if self.running:
                    try:
                        self.root.after(0, self._update_dashboard_stats)
                    except:
                        break
        
        self.update_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.update_thread.start()

    def _update_dashboard_stats(self):
        """Update dashboard statistics."""
        # This would update the dashboard with new stats
        pass

    def _start_monitoring_updates(self):
        """Start monitoring updates."""
        def update_loop():
            while self.running:
                try:
                    if PSUTIL_AVAILABLE and hasattr(self, 'monitoring_labels'):
                        cpu = psutil.cpu_percent()
                        memory = psutil.virtual_memory().percent
                        
                        self.root.after(0, lambda: self.monitoring_labels.get("CPU", tk.Label()).configure(text=f"{cpu}%"))
                        self.root.after(0, lambda: self.monitoring_labels.get("Memory", tk.Label()).configure(text=f"{memory}%"))
                except:
                    pass
                time.sleep(2)
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()

    def _open_settings(self):
        """Open settings window."""
        from .settings import SettingsWindow
        settings = SettingsWindow()
        settings.run()

    def run(self):
        """Run the dashboard window."""
        self._create_window()
        self._create_widgets()
        self.running = True
        self.root.mainloop()


# Import Path at module level
from pathlib import Path


if __name__ == "__main__":
    app = DashboardWindow()
    app.run()
