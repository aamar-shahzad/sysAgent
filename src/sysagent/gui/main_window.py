"""
Main GUI Window for SysAgent - Combines Dashboard and Settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

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


class MainWindow:
    """Main application window combining dashboard and settings."""

    def __init__(self):
        self.root = None
        self.current_view = "dashboard"
        self._create_window()
        self._create_menu()
        self._create_content()

    def _create_window(self):
        """Create the main window."""
        if USE_CUSTOMTKINTER:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title("SysAgent - System Control Center")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Set icon if available
        try:
            # self.root.iconbitmap("path/to/icon.ico")
            pass
        except:
            pass
        
        return self.root

    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Dashboard", command=self._show_dashboard)
        file_menu.add_command(label="Settings", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="System Info", command=self._view_system_info)
        view_menu.add_command(label="Processes", command=self._view_processes)
        view_menu.add_command(label="Files", command=self._view_files)
        view_menu.add_command(label="Network", command=self._view_network)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Clean Temp Files", command=self._clean_temp)
        tools_menu.add_command(label="Organize Downloads", command=self._organize_downloads)
        tools_menu.add_command(label="Check Internet", command=self._check_internet)
        tools_menu.add_separator()
        tools_menu.add_command(label="Run CLI Command", command=self._run_cli_command)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_docs)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_content(self):
        """Create the main content area."""
        if USE_CUSTOMTKINTER:
            self.content_frame = ctk.CTkFrame(self.root)
            self.content_frame.pack(fill="both", expand=True)
        else:
            self.content_frame = ttk.Frame(self.root)
            self.content_frame.pack(fill="both", expand=True)
        
        # Show dashboard by default
        self._show_dashboard()

    def _clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_dashboard(self):
        """Show the dashboard view."""
        self._clear_content()
        self.current_view = "dashboard"
        
        from .dashboard import DashboardWindow
        
        # Embed dashboard in the content frame
        if USE_CUSTOMTKINTER:
            # Create sidebar
            sidebar = ctk.CTkFrame(self.content_frame, width=200, corner_radius=0)
            sidebar.pack(side="left", fill="y")
            sidebar.pack_propagate(False)
            
            # Logo
            logo = ctk.CTkLabel(
                sidebar,
                text="🧠 SysAgent",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            logo.pack(pady=30)
            
            # Navigation buttons
            nav_buttons = [
                ("🏠 Dashboard", self._show_dashboard),
                ("💻 System Info", self._view_system_info),
                ("📊 Processes", self._view_processes),
                ("📁 Files", self._view_files),
                ("🌐 Network", self._view_network),
                ("⚙️ Settings", self._show_settings),
            ]
            
            for text, command in nav_buttons:
                btn = ctk.CTkButton(
                    sidebar,
                    text=text,
                    command=command,
                    width=180,
                    height=35,
                    anchor="w"
                )
                btn.pack(pady=3, padx=10)
            
            # Main content
            main_content = ctk.CTkFrame(self.content_frame)
            main_content.pack(side="right", fill="both", expand=True)
            
            # Dashboard content
            self._create_dashboard_content(main_content)
        else:
            ttk.Label(
                self.content_frame,
                text="Dashboard View",
                font=("Helvetica", 18, "bold")
            ).pack(pady=20)

    def _create_dashboard_content(self, parent):
        """Create dashboard content."""
        try:
            import psutil
            PSUTIL_AVAILABLE = True
        except ImportError:
            PSUTIL_AVAILABLE = False
        
        if USE_CUSTOMTKINTER:
            # Title
            title = ctk.CTkLabel(
                parent,
                text="System Dashboard",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20, padx=20, anchor="w")
            
            # Stats grid
            stats_frame = ctk.CTkFrame(parent)
            stats_frame.pack(fill="x", padx=20, pady=10)
            
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                stats = [
                    ("CPU Usage", f"{cpu_percent}%", self._get_color(cpu_percent)),
                    ("Memory", f"{memory.percent}%", self._get_color(memory.percent)),
                    ("Disk", f"{disk.percent}%", self._get_color(disk.percent)),
                    ("Processes", str(len(psutil.pids())), "blue"),
                ]
                
                for i, (label, value, color) in enumerate(stats):
                    box = ctk.CTkFrame(stats_frame)
                    box.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
                    stats_frame.grid_columnconfigure(i, weight=1)
                    
                    ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=12)).pack(pady=(15, 5))
                    ctk.CTkLabel(
                        box,
                        text=value,
                        font=ctk.CTkFont(size=28, weight="bold"),
                        text_color=color
                    ).pack(pady=(5, 15))
            
            # System info
            info_frame = ctk.CTkFrame(parent)
            info_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(
                info_frame,
                text="System Information",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", padx=15, pady=(15, 10))
            
            import platform
            from datetime import datetime
            
            info_text = f"""
Platform: {platform.system()} {platform.release()}
Machine: {platform.machine()}
Processor: {platform.processor() or 'N/A'}
Python: {platform.python_version()}
"""
            if PSUTIL_AVAILABLE:
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.now() - boot_time
                info_text += f"Uptime: {str(uptime).split('.')[0]}"
            
            ctk.CTkLabel(
                info_frame,
                text=info_text,
                font=ctk.CTkFont(size=13),
                justify="left"
            ).pack(anchor="w", padx=15, pady=(0, 15))
            
            # Quick actions
            actions_frame = ctk.CTkFrame(parent)
            actions_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(
                actions_frame,
                text="Quick Actions",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", padx=15, pady=(15, 10))
            
            btn_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(0, 15))
            
            actions = [
                ("🔄 Refresh", self._show_dashboard),
                ("🧹 Clean Temp", self._clean_temp),
                ("📊 Processes", self._view_processes),
                ("🌐 Check Net", self._check_internet),
                ("⚙️ Settings", self._show_settings),
            ]
            
            for text, command in actions:
                btn = ctk.CTkButton(btn_frame, text=text, command=command, width=100)
                btn.pack(side="left", padx=5)

    def _get_color(self, percent: float) -> str:
        """Get color based on percentage."""
        if percent < 50:
            return "green"
        elif percent < 80:
            return "orange"
        return "red"

    def _show_settings(self):
        """Show settings view."""
        self._clear_content()
        self.current_view = "settings"
        
        from .settings import SettingsWindow
        
        # Create embedded settings
        if USE_CUSTOMTKINTER:
            settings_instance = SettingsWindow()
            settings_instance._initialize_managers()
            
            # Create widgets in content frame
            title = ctk.CTkLabel(
                self.content_frame,
                text="🔑 Settings",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            # Create notebook for tabs
            notebook = ctk.CTkTabview(self.content_frame)
            notebook.pack(fill="both", expand=True, padx=20, pady=10)
            
            api_tab = notebook.add("API Keys")
            provider_tab = notebook.add("Model Providers")
            permissions_tab = notebook.add("Permissions")
            
            # Simplified API key section
            self._create_simple_api_section(api_tab, settings_instance)
            self._create_simple_provider_section(provider_tab, settings_instance)
            self._create_simple_permissions_section(permissions_tab, settings_instance)
            
            # Back button
            back_btn = ctk.CTkButton(
                self.content_frame,
                text="← Back to Dashboard",
                command=self._show_dashboard,
                width=150
            )
            back_btn.pack(pady=10)
        else:
            ttk.Label(
                self.content_frame,
                text="Settings",
                font=("Helvetica", 18, "bold")
            ).pack(pady=20)

    def _create_simple_api_section(self, parent, settings_instance):
        """Create simplified API key section."""
        if USE_CUSTOMTKINTER:
            # OpenAI
            frame = ctk.CTkFrame(parent)
            frame.pack(fill="x", pady=10, padx=10)
            
            ctk.CTkLabel(frame, text="OpenAI API Key", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            import os
            openai_key = os.environ.get("OPENAI_API_KEY", "")
            
            entry = ctk.CTkEntry(frame, placeholder_text="sk-...", show="*", width=400)
            entry.pack(fill="x", padx=10, pady=(0, 10))
            if openai_key:
                entry.insert(0, openai_key)
            
            settings_instance.openai_api_key_entry = entry
            
            # Save button
            save_btn = ctk.CTkButton(
                parent,
                text="Save API Keys",
                command=settings_instance._save_api_keys,
                width=200
            )
            save_btn.pack(pady=20)

    def _create_simple_provider_section(self, parent, settings_instance):
        """Create simplified provider section."""
        if USE_CUSTOMTKINTER:
            frame = ctk.CTkFrame(parent)
            frame.pack(fill="x", pady=10, padx=10)
            
            ctk.CTkLabel(frame, text="Model Provider", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            settings_instance.provider_var = tk.StringVar(value="openai")
            
            providers = [("OpenAI", "openai"), ("Ollama", "ollama"), ("Anthropic", "anthropic")]
            
            for text, value in providers:
                rb = ctk.CTkRadioButton(frame, text=text, variable=settings_instance.provider_var, value=value)
                rb.pack(anchor="w", padx=20, pady=2)
            
            ctk.CTkLabel(frame, text="Model Name", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(20, 5))
            
            settings_instance.model_entry = ctk.CTkEntry(frame, placeholder_text="gpt-4", width=300)
            settings_instance.model_entry.pack(fill="x", padx=10, pady=(0, 10))
            settings_instance.model_entry.insert(0, "gpt-4")
            
            save_btn = ctk.CTkButton(
                parent,
                text="Save Provider Settings",
                command=settings_instance._save_provider_settings,
                width=200
            )
            save_btn.pack(pady=20)

    def _create_simple_permissions_section(self, parent, settings_instance):
        """Create simplified permissions section."""
        if USE_CUSTOMTKINTER:
            frame = ctk.CTkFrame(parent)
            frame.pack(fill="both", expand=True, pady=10, padx=10)
            
            ctk.CTkLabel(frame, text="Permissions", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            permissions = [
                ("file_access", "File Access"),
                ("system_info", "System Info"),
                ("process_management", "Process Management"),
                ("network_access", "Network Access"),
                ("system_control", "System Control"),
                ("code_execution", "Code Execution"),
            ]
            
            settings_instance.permission_vars = {}
            
            for perm_key, perm_name in permissions:
                var = tk.BooleanVar(value=settings_instance._get_permission_status(perm_key))
                settings_instance.permission_vars[perm_key] = var
                
                cb = ctk.CTkCheckBox(frame, text=perm_name, variable=var)
                cb.pack(anchor="w", padx=20, pady=2)
            
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkButton(
                btn_frame,
                text="Grant All",
                command=settings_instance._grant_all_permissions,
                width=100
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                btn_frame,
                text="Revoke All",
                command=settings_instance._revoke_all_permissions,
                fg_color="red",
                width=100
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                parent,
                text="Save Permissions",
                command=settings_instance._save_permissions,
                width=200
            ).pack(pady=20)

    def _view_system_info(self):
        """View system information."""
        self._clear_content()
        
        if USE_CUSTOMTKINTER:
            title = ctk.CTkLabel(
                self.content_frame,
                text="System Information",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)
            
            try:
                from ..core.config import ConfigManager
                from ..core.permissions import PermissionManager
                from ..tools.base import ToolExecutor
                from ..tools import SystemInfoTool
                
                config_manager = ConfigManager()
                permission_manager = PermissionManager(config_manager)
                executor = ToolExecutor(permission_manager)
                executor.register_tool(SystemInfoTool())
                
                result = executor.execute_tool("system_info_tool", action="overview")
                
                scroll = ctk.CTkScrollableFrame(self.content_frame)
                scroll.pack(fill="both", expand=True, padx=20, pady=10)
                
                if result.success:
                    self._display_data(scroll, result.data)
                else:
                    ctk.CTkLabel(scroll, text=result.message).pack()
                    
            except Exception as e:
                ctk.CTkLabel(self.content_frame, text=f"Error: {e}").pack()
            
            ctk.CTkButton(
                self.content_frame,
                text="← Back",
                command=self._show_dashboard,
                width=100
            ).pack(pady=10)

    def _display_data(self, parent, data, level=0):
        """Display dictionary data recursively."""
        if isinstance(data, dict):
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
                        self._display_data(frame, value, level + 1)
                else:
                    text = f"{str(key).replace('_', ' ').title()}: {value}"
                    if USE_CUSTOMTKINTER:
                        ctk.CTkLabel(parent, text=text).pack(anchor="w", padx=10 + level*20, pady=2)

    def _view_processes(self):
        """View processes."""
        self._show_process_list()

    def _show_process_list(self):
        """Show process list in a new window."""
        if not PSUTIL_AVAILABLE:
            messagebox.showerror("Error", "psutil is required for process management")
            return
        
        # Create a new window
        if USE_CUSTOMTKINTER:
            proc_window = ctk.CTkToplevel(self.root)
        else:
            proc_window = tk.Toplevel(self.root)
        
        proc_window.title("Process Manager")
        proc_window.geometry("800x600")
        
        # Create treeview for processes
        columns = ("PID", "Name", "CPU %", "Memory %", "Status")
        
        if USE_CUSTOMTKINTER:
            # Frame for treeview
            tree_frame = ctk.CTkFrame(proc_window)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Use ttk.Treeview inside customtkinter
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        else:
            tree_frame = ttk.Frame(proc_window)
            tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100 if col != "Name" else 200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        
        # Populate processes
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = proc.info
                    tree.insert("", "end", values=(
                        info['pid'],
                        info['name'][:30] if info['name'] else "N/A",
                        f"{info['cpu_percent']:.1f}" if info['cpu_percent'] else "0.0",
                        f"{info['memory_percent']:.1f}" if info['memory_percent'] else "0.0",
                        info['status'] if info['status'] else "N/A"
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list processes: {e}")
        
        # Buttons frame
        if USE_CUSTOMTKINTER:
            btn_frame = ctk.CTkFrame(proc_window)
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            refresh_btn = ctk.CTkButton(btn_frame, text="Refresh", command=lambda: self._refresh_processes(tree))
            refresh_btn.pack(side="left", padx=5)
            
            kill_btn = ctk.CTkButton(btn_frame, text="Kill Process", command=lambda: self._kill_selected_process(tree), fg_color="red")
            kill_btn.pack(side="left", padx=5)
        else:
            btn_frame = ttk.Frame(proc_window)
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Button(btn_frame, text="Refresh", command=lambda: self._refresh_processes(tree)).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="Kill Process", command=lambda: self._kill_selected_process(tree)).pack(side="left", padx=5)

    def _refresh_processes(self, tree):
        """Refresh process list."""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Repopulate
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = proc.info
                    tree.insert("", "end", values=(
                        info['pid'],
                        info['name'][:30] if info['name'] else "N/A",
                        f"{info['cpu_percent']:.1f}" if info['cpu_percent'] else "0.0",
                        f"{info['memory_percent']:.1f}" if info['memory_percent'] else "0.0",
                        info['status'] if info['status'] else "N/A"
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh: {e}")

    def _kill_selected_process(self, tree):
        """Kill the selected process."""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a process to kill")
            return
        
        item = tree.item(selected[0])
        pid = int(item['values'][0])
        name = item['values'][1]
        
        if messagebox.askyesno("Confirm", f"Kill process {name} (PID: {pid})?"):
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                messagebox.showinfo("Success", f"Process {name} terminated")
                self._refresh_processes(tree)
            except psutil.NoSuchProcess:
                messagebox.showinfo("Info", "Process no longer exists")
                self._refresh_processes(tree)
            except psutil.AccessDenied:
                messagebox.showerror("Error", "Access denied. Try running with elevated privileges.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to kill process: {e}")

    def _view_files(self):
        """View files."""
        self._show_file_browser()

    def _show_file_browser(self):
        """Show a simple file browser."""
        from pathlib import Path
        
        if USE_CUSTOMTKINTER:
            file_window = ctk.CTkToplevel(self.root)
        else:
            file_window = tk.Toplevel(self.root)
        
        file_window.title("File Browser")
        file_window.geometry("600x500")
        
        current_path = Path.home()
        
        # Path entry
        if USE_CUSTOMTKINTER:
            path_frame = ctk.CTkFrame(file_window)
            path_frame.pack(fill="x", padx=10, pady=10)
            path_entry = ctk.CTkEntry(path_frame, width=400)
            path_entry.pack(side="left", padx=5)
            path_entry.insert(0, str(current_path))
        else:
            path_frame = ttk.Frame(file_window)
            path_frame.pack(fill="x", padx=10, pady=10)
            path_entry = ttk.Entry(path_frame, width=50)
            path_entry.pack(side="left", padx=5)
            path_entry.insert(0, str(current_path))
        
        # File list
        file_list = tk.Listbox(file_window, font=("Courier", 10))
        file_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        def refresh_files():
            path = Path(path_entry.get())
            file_list.delete(0, tk.END)
            
            if path.exists() and path.is_dir():
                file_list.insert(tk.END, "..")
                try:
                    for item in sorted(path.iterdir()):
                        prefix = "[D] " if item.is_dir() else "[F] "
                        file_list.insert(tk.END, prefix + item.name)
                except PermissionError:
                    file_list.insert(tk.END, "(Permission Denied)")
        
        def on_double_click(event):
            selection = file_list.curselection()
            if selection:
                item = file_list.get(selection[0])
                if item == "..":
                    new_path = Path(path_entry.get()).parent
                elif item.startswith("[D] "):
                    new_path = Path(path_entry.get()) / item[4:]
                else:
                    return
                path_entry.delete(0, tk.END)
                path_entry.insert(0, str(new_path))
                refresh_files()
        
        file_list.bind("<Double-Button-1>", on_double_click)
        refresh_files()

    def _view_network(self):
        """View network."""
        self._show_network_info()

    def _show_network_info(self):
        """Show network information."""
        if USE_CUSTOMTKINTER:
            net_window = ctk.CTkToplevel(self.root)
        else:
            net_window = tk.Toplevel(self.root)
        
        net_window.title("Network Information")
        net_window.geometry("600x400")
        
        # Text area for network info
        if USE_CUSTOMTKINTER:
            text_frame = ctk.CTkFrame(net_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            text = tk.Text(text_frame, font=("Courier", 10), wrap="word")
        else:
            text_frame = ttk.Frame(net_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            text = tk.Text(text_frame, font=("Courier", 10), wrap="word")
        
        text.pack(fill="both", expand=True)
        
        # Get network info
        import socket
        info = []
        
        try:
            hostname = socket.gethostname()
            info.append(f"Hostname: {hostname}")
            info.append(f"Local IP: {socket.gethostbyname(hostname)}")
        except:
            info.append("Could not get hostname/IP")
        
        if PSUTIL_AVAILABLE:
            info.append("\nNetwork Interfaces:")
            for iface, addrs in psutil.net_if_addrs().items():
                info.append(f"\n  {iface}:")
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        info.append(f"    IPv4: {addr.address}")
                    elif addr.family == socket.AF_INET6:
                        info.append(f"    IPv6: {addr.address}")
            
            info.append("\nNetwork I/O:")
            net_io = psutil.net_io_counters()
            info.append(f"  Bytes Sent: {net_io.bytes_sent / (1024*1024):.2f} MB")
            info.append(f"  Bytes Received: {net_io.bytes_recv / (1024*1024):.2f} MB")
        
        text.insert("1.0", "\n".join(info))
        text.config(state="disabled")

    def _clean_temp(self):
        """Clean temp files."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..tools.base import ToolExecutor
            from ..tools import FileTool
            
            config_manager = ConfigManager()
            permission_manager = PermissionManager(config_manager)
            executor = ToolExecutor(permission_manager)
            executor.register_tool(FileTool())
            
            result = executor.execute_tool("file_tool", action="cleanup")
            messagebox.showinfo("Cleanup", result.message)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _organize_downloads(self):
        """Organize downloads."""
        from pathlib import Path
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..tools.base import ToolExecutor
            from ..tools import FileTool
            
            config_manager = ConfigManager()
            permission_manager = PermissionManager(config_manager)
            executor = ToolExecutor(permission_manager)
            executor.register_tool(FileTool())
            
            result = executor.execute_tool("file_tool", action="organize", source_dir=str(Path.home() / "Downloads"))
            messagebox.showinfo("Organize", result.message)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _check_internet(self):
        """Check internet connection."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..tools.base import ToolExecutor
            from ..tools import NetworkTool
            
            config_manager = ConfigManager()
            permission_manager = PermissionManager(config_manager)
            executor = ToolExecutor(permission_manager)
            executor.register_tool(NetworkTool())
            
            result = executor.execute_tool("network_tool", action="ping", host="google.com")
            if result.success:
                messagebox.showinfo("Internet", "Internet connection is working!")
            else:
                messagebox.showerror("Internet", "No internet connection")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _run_cli_command(self):
        """Run a CLI command."""
        if USE_CUSTOMTKINTER:
            command = ctk.CTkInputDialog(
                text="Enter command:",
                title="Run CLI Command"
            ).get_input()
            
            if command:
                messagebox.showinfo("CLI", f"Command: {command}\nUse CLI for full functionality.")
        else:
            messagebox.showinfo("CLI", "Use the command line for CLI commands")

    def _show_docs(self):
        """Show documentation."""
        import webbrowser
        webbrowser.open("https://github.com/sysagent/sysagent-cli")

    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About SysAgent",
            "SysAgent v0.1.0\n\n"
            "Secure, intelligent command-line assistant\n"
            "for OS automation and control.\n\n"
            "https://github.com/sysagent/sysagent-cli"
        )

    def _on_exit(self):
        """Handle exit."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.root.destroy()

    def run(self):
        """Run the main window."""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
