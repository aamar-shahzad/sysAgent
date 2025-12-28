"""
Settings GUI for SysAgent - API Key Management and Configuration.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import customtkinter as ctk
    USE_CUSTOMTKINTER = True
except ImportError:
    USE_CUSTOMTKINTER = False


class SettingsWindow:
    """Settings window for API key management and configuration."""

    def __init__(self):
        self.root = None
        self.config_manager = None
        self.permission_manager = None
        self._initialize_managers()

    def _initialize_managers(self):
        """Initialize config and permission managers."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            self.config_manager = ConfigManager()
            self.permission_manager = PermissionManager(self.config_manager)
        except Exception as e:
            print(f"Warning: Could not initialize managers: {e}")

    def _create_window(self):
        """Create the main settings window."""
        if USE_CUSTOMTKINTER:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title("SysAgent Settings - API Configuration")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)
        
        # Center window
        self._center_window()
        
        return self.root

    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self):
        """Create all widgets for the settings window."""
        # Main container
        if USE_CUSTOMTKINTER:
            main_frame = ctk.CTkFrame(self.root)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        else:
            main_frame = ttk.Frame(self.root, padding="20")
            main_frame.pack(fill="both", expand=True)

        # Title
        self._create_title(main_frame)
        
        # Create notebook for tabs
        self._create_notebook(main_frame)

    def _create_title(self, parent):
        """Create title section."""
        if USE_CUSTOMTKINTER:
            title_label = ctk.CTkLabel(
                parent, 
                text="🔑 SysAgent Settings",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=(0, 20))
            
            subtitle = ctk.CTkLabel(
                parent,
                text="Configure your API keys and model providers",
                font=ctk.CTkFont(size=12)
            )
            subtitle.pack(pady=(0, 20))
        else:
            title_label = ttk.Label(
                parent, 
                text="🔑 SysAgent Settings",
                font=("Helvetica", 18, "bold")
            )
            title_label.pack(pady=(0, 10))
            
            subtitle = ttk.Label(
                parent,
                text="Configure your API keys and model providers",
                font=("Helvetica", 10)
            )
            subtitle.pack(pady=(0, 20))

    def _create_notebook(self, parent):
        """Create tabbed notebook for different settings sections."""
        if USE_CUSTOMTKINTER:
            self.notebook = ctk.CTkTabview(parent)
            self.notebook.pack(fill="both", expand=True)
            
            # Add tabs
            api_tab = self.notebook.add("API Keys")
            provider_tab = self.notebook.add("Model Providers")
            permissions_tab = self.notebook.add("Permissions")
            advanced_tab = self.notebook.add("Advanced")
            
            self._create_api_tab(api_tab)
            self._create_provider_tab(provider_tab)
            self._create_permissions_tab(permissions_tab)
            self._create_advanced_tab(advanced_tab)
        else:
            self.notebook = ttk.Notebook(parent)
            self.notebook.pack(fill="both", expand=True)
            
            # Create frames for each tab
            api_frame = ttk.Frame(self.notebook, padding="10")
            provider_frame = ttk.Frame(self.notebook, padding="10")
            permissions_frame = ttk.Frame(self.notebook, padding="10")
            advanced_frame = ttk.Frame(self.notebook, padding="10")
            
            self.notebook.add(api_frame, text="API Keys")
            self.notebook.add(provider_frame, text="Model Providers")
            self.notebook.add(permissions_frame, text="Permissions")
            self.notebook.add(advanced_frame, text="Advanced")
            
            self._create_api_tab(api_frame)
            self._create_provider_tab(provider_frame)
            self._create_permissions_tab(permissions_frame)
            self._create_advanced_tab(advanced_frame)

    def _create_api_tab(self, parent):
        """Create API keys configuration tab."""
        # OpenAI API Key
        self._create_api_section(
            parent,
            "OpenAI API Key",
            "Enter your OpenAI API key for GPT models",
            "openai_api_key",
            "https://platform.openai.com/api-keys"
        )
        
        # Anthropic API Key
        self._create_api_section(
            parent,
            "Anthropic API Key", 
            "Enter your Anthropic API key for Claude models",
            "anthropic_api_key",
            "https://console.anthropic.com/account/keys"
        )
        
        # Google AI API Key
        self._create_api_section(
            parent,
            "Google AI API Key",
            "Enter your Google AI API key for Gemini models",
            "google_api_key",
            "https://aistudio.google.com/app/apikey"
        )
        
        # AWS Bedrock
        self._create_api_section(
            parent,
            "AWS Access Key",
            "Enter your AWS Access Key for Bedrock",
            "aws_access_key",
            "https://aws.amazon.com/bedrock/"
        )
        
        # Save button
        self._create_save_button(parent, self._save_api_keys)

    def _create_api_section(self, parent, title: str, description: str, 
                           key_name: str, help_url: str):
        """Create an API key input section."""
        if USE_CUSTOMTKINTER:
            frame = ctk.CTkFrame(parent)
            frame.pack(fill="x", pady=10, padx=5)
            
            # Title row
            title_frame = ctk.CTkFrame(frame, fg_color="transparent")
            title_frame.pack(fill="x", padx=10, pady=(10, 5))
            
            label = ctk.CTkLabel(title_frame, text=title, font=ctk.CTkFont(weight="bold"))
            label.pack(side="left")
            
            help_btn = ctk.CTkButton(
                title_frame, 
                text="Get Key",
                width=80,
                command=lambda: self._open_url(help_url)
            )
            help_btn.pack(side="right")
            
            # Description
            desc_label = ctk.CTkLabel(frame, text=description, font=ctk.CTkFont(size=11))
            desc_label.pack(anchor="w", padx=10)
            
            # Entry
            entry = ctk.CTkEntry(frame, placeholder_text="Enter API key...", show="*", width=400)
            entry.pack(fill="x", padx=10, pady=(5, 10))
            
            # Load existing value
            self._load_api_key(entry, key_name)
            
            # Store reference
            setattr(self, f"{key_name}_entry", entry)
        else:
            frame = ttk.LabelFrame(parent, text=title, padding="10")
            frame.pack(fill="x", pady=10, padx=5)
            
            desc_label = ttk.Label(frame, text=description)
            desc_label.pack(anchor="w")
            
            entry_frame = ttk.Frame(frame)
            entry_frame.pack(fill="x", pady=5)
            
            entry = ttk.Entry(entry_frame, show="*", width=50)
            entry.pack(side="left", fill="x", expand=True)
            
            help_btn = ttk.Button(
                entry_frame, 
                text="Get Key",
                command=lambda: self._open_url(help_url)
            )
            help_btn.pack(side="right", padx=(5, 0))
            
            # Load existing value
            self._load_api_key(entry, key_name)
            
            # Store reference
            setattr(self, f"{key_name}_entry", entry)

    def _create_provider_tab(self, parent):
        """Create model provider configuration tab."""
        if USE_CUSTOMTKINTER:
            # Provider selection
            provider_frame = ctk.CTkFrame(parent)
            provider_frame.pack(fill="x", pady=10, padx=5)
            
            label = ctk.CTkLabel(
                provider_frame, 
                text="Default Model Provider",
                font=ctk.CTkFont(weight="bold")
            )
            label.pack(anchor="w", padx=10, pady=(10, 5))
            
            self.provider_var = tk.StringVar(value="openai")
            
            providers = [
                ("OpenAI (GPT-4, GPT-3.5)", "openai"),
                ("Anthropic (Claude)", "anthropic"),
                ("Google AI (Gemini)", "google"),
                ("Ollama (Local)", "ollama"),
                ("AWS Bedrock", "bedrock")
            ]
            
            for text, value in providers:
                rb = ctk.CTkRadioButton(
                    provider_frame,
                    text=text,
                    variable=self.provider_var,
                    value=value
                )
                rb.pack(anchor="w", padx=20, pady=2)
            
            # Model selection
            model_frame = ctk.CTkFrame(parent)
            model_frame.pack(fill="x", pady=10, padx=5)
            
            model_label = ctk.CTkLabel(
                model_frame,
                text="Model Name",
                font=ctk.CTkFont(weight="bold")
            )
            model_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            self.model_entry = ctk.CTkEntry(
                model_frame,
                placeholder_text="e.g., gpt-4, claude-3-opus, gemini-pro",
                width=400
            )
            self.model_entry.pack(fill="x", padx=10, pady=(5, 10))
            
            # Ollama settings
            ollama_frame = ctk.CTkFrame(parent)
            ollama_frame.pack(fill="x", pady=10, padx=5)
            
            ollama_label = ctk.CTkLabel(
                ollama_frame,
                text="Ollama Base URL (for local models)",
                font=ctk.CTkFont(weight="bold")
            )
            ollama_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            self.ollama_url_entry = ctk.CTkEntry(
                ollama_frame,
                placeholder_text="http://localhost:11434",
                width=400
            )
            self.ollama_url_entry.pack(fill="x", padx=10, pady=(5, 10))
            self.ollama_url_entry.insert(0, "http://localhost:11434")
            
        else:
            # Provider selection
            provider_frame = ttk.LabelFrame(parent, text="Default Model Provider", padding="10")
            provider_frame.pack(fill="x", pady=10, padx=5)
            
            self.provider_var = tk.StringVar(value="openai")
            
            providers = [
                ("OpenAI (GPT-4, GPT-3.5)", "openai"),
                ("Anthropic (Claude)", "anthropic"),
                ("Google AI (Gemini)", "google"),
                ("Ollama (Local)", "ollama"),
                ("AWS Bedrock", "bedrock")
            ]
            
            for text, value in providers:
                rb = ttk.Radiobutton(
                    provider_frame,
                    text=text,
                    variable=self.provider_var,
                    value=value
                )
                rb.pack(anchor="w", pady=2)
            
            # Model selection
            model_frame = ttk.LabelFrame(parent, text="Model Name", padding="10")
            model_frame.pack(fill="x", pady=10, padx=5)
            
            self.model_entry = ttk.Entry(model_frame, width=50)
            self.model_entry.pack(fill="x")
            self.model_entry.insert(0, "gpt-4")
            
            # Ollama settings
            ollama_frame = ttk.LabelFrame(parent, text="Ollama Base URL", padding="10")
            ollama_frame.pack(fill="x", pady=10, padx=5)
            
            self.ollama_url_entry = ttk.Entry(ollama_frame, width=50)
            self.ollama_url_entry.pack(fill="x")
            self.ollama_url_entry.insert(0, "http://localhost:11434")
        
        # Load current settings
        self._load_provider_settings()
        
        # Save button
        self._create_save_button(parent, self._save_provider_settings)

    def _create_permissions_tab(self, parent):
        """Create permissions configuration tab."""
        permissions = [
            ("file_access", "File System Access", "Allow reading and writing files"),
            ("system_info", "System Information", "Allow accessing system info"),
            ("process_management", "Process Management", "Allow managing processes"),
            ("network_access", "Network Access", "Allow network operations"),
            ("system_control", "System Control", "Allow system control operations"),
            ("code_execution", "Code Execution", "Allow executing generated code"),
            ("security_operations", "Security Operations", "Allow security scans"),
            ("automation_operations", "Automation", "Allow automation tasks"),
            ("monitoring_operations", "Monitoring", "Allow system monitoring"),
            ("low_level_os", "Low-Level OS Access", "Allow low-level OS operations"),
        ]
        
        self.permission_vars = {}
        
        if USE_CUSTOMTKINTER:
            # Scrollable frame for permissions
            scroll_frame = ctk.CTkScrollableFrame(parent, height=300)
            scroll_frame.pack(fill="both", expand=True, pady=10)
            
            for perm_key, perm_name, perm_desc in permissions:
                frame = ctk.CTkFrame(scroll_frame)
                frame.pack(fill="x", pady=5, padx=5)
                
                var = tk.BooleanVar(value=self._get_permission_status(perm_key))
                self.permission_vars[perm_key] = var
                
                cb = ctk.CTkCheckBox(
                    frame,
                    text=perm_name,
                    variable=var,
                    font=ctk.CTkFont(weight="bold")
                )
                cb.pack(anchor="w", padx=10, pady=(5, 0))
                
                desc = ctk.CTkLabel(frame, text=perm_desc, font=ctk.CTkFont(size=11))
                desc.pack(anchor="w", padx=30, pady=(0, 5))
            
            # Buttons
            btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
            btn_frame.pack(fill="x", pady=10)
            
            grant_all_btn = ctk.CTkButton(
                btn_frame,
                text="Grant All",
                command=self._grant_all_permissions
            )
            grant_all_btn.pack(side="left", padx=5)
            
            revoke_all_btn = ctk.CTkButton(
                btn_frame,
                text="Revoke All",
                fg_color="red",
                command=self._revoke_all_permissions
            )
            revoke_all_btn.pack(side="left", padx=5)
            
        else:
            # Scrollable frame
            canvas = tk.Canvas(parent)
            scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            scroll_frame = ttk.Frame(canvas)
            
            scroll_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            for perm_key, perm_name, perm_desc in permissions:
                frame = ttk.LabelFrame(scroll_frame, text=perm_name, padding="5")
                frame.pack(fill="x", pady=5, padx=5)
                
                var = tk.BooleanVar(value=self._get_permission_status(perm_key))
                self.permission_vars[perm_key] = var
                
                cb = ttk.Checkbutton(frame, text="Enabled", variable=var)
                cb.pack(anchor="w")
                
                desc = ttk.Label(frame, text=perm_desc)
                desc.pack(anchor="w")
        
        # Save button
        self._create_save_button(parent, self._save_permissions)

    def _create_advanced_tab(self, parent):
        """Create advanced settings tab."""
        if USE_CUSTOMTKINTER:
            # Security settings
            security_frame = ctk.CTkFrame(parent)
            security_frame.pack(fill="x", pady=10, padx=5)
            
            security_label = ctk.CTkLabel(
                security_frame,
                text="Security Settings",
                font=ctk.CTkFont(weight="bold")
            )
            security_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            self.dry_run_var = tk.BooleanVar(value=False)
            dry_run_cb = ctk.CTkCheckBox(
                security_frame,
                text="Dry Run Mode (preview actions without executing)",
                variable=self.dry_run_var
            )
            dry_run_cb.pack(anchor="w", padx=20, pady=2)
            
            self.confirm_destructive_var = tk.BooleanVar(value=True)
            confirm_cb = ctk.CTkCheckBox(
                security_frame,
                text="Confirm destructive actions",
                variable=self.confirm_destructive_var
            )
            confirm_cb.pack(anchor="w", padx=20, pady=2)
            
            self.audit_logging_var = tk.BooleanVar(value=True)
            audit_cb = ctk.CTkCheckBox(
                security_frame,
                text="Enable audit logging",
                variable=self.audit_logging_var
            )
            audit_cb.pack(anchor="w", padx=20, pady=(2, 10))
            
            # Debug settings
            debug_frame = ctk.CTkFrame(parent)
            debug_frame.pack(fill="x", pady=10, padx=5)
            
            debug_label = ctk.CTkLabel(
                debug_frame,
                text="Debug Settings",
                font=ctk.CTkFont(weight="bold")
            )
            debug_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            self.verbose_var = tk.BooleanVar(value=False)
            verbose_cb = ctk.CTkCheckBox(
                debug_frame,
                text="Verbose output",
                variable=self.verbose_var
            )
            verbose_cb.pack(anchor="w", padx=20, pady=2)
            
            self.debug_var = tk.BooleanVar(value=False)
            debug_cb = ctk.CTkCheckBox(
                debug_frame,
                text="Debug mode",
                variable=self.debug_var
            )
            debug_cb.pack(anchor="w", padx=20, pady=(2, 10))
            
            # Export/Import
            export_frame = ctk.CTkFrame(parent)
            export_frame.pack(fill="x", pady=10, padx=5)
            
            export_label = ctk.CTkLabel(
                export_frame,
                text="Configuration",
                font=ctk.CTkFont(weight="bold")
            )
            export_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            btn_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=(5, 10))
            
            export_btn = ctk.CTkButton(
                btn_frame,
                text="Export Config",
                command=self._export_config
            )
            export_btn.pack(side="left", padx=5)
            
            import_btn = ctk.CTkButton(
                btn_frame,
                text="Import Config",
                command=self._import_config
            )
            import_btn.pack(side="left", padx=5)
            
            reset_btn = ctk.CTkButton(
                btn_frame,
                text="Reset to Defaults",
                fg_color="red",
                command=self._reset_config
            )
            reset_btn.pack(side="left", padx=5)
            
        else:
            # Security settings
            security_frame = ttk.LabelFrame(parent, text="Security Settings", padding="10")
            security_frame.pack(fill="x", pady=10, padx=5)
            
            self.dry_run_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                security_frame,
                text="Dry Run Mode",
                variable=self.dry_run_var
            ).pack(anchor="w")
            
            self.confirm_destructive_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                security_frame,
                text="Confirm destructive actions",
                variable=self.confirm_destructive_var
            ).pack(anchor="w")
            
            self.audit_logging_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                security_frame,
                text="Enable audit logging",
                variable=self.audit_logging_var
            ).pack(anchor="w")
            
            # Debug settings
            debug_frame = ttk.LabelFrame(parent, text="Debug Settings", padding="10")
            debug_frame.pack(fill="x", pady=10, padx=5)
            
            self.verbose_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(debug_frame, text="Verbose output", variable=self.verbose_var).pack(anchor="w")
            
            self.debug_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(debug_frame, text="Debug mode", variable=self.debug_var).pack(anchor="w")
        
        # Load current settings
        self._load_advanced_settings()
        
        # Save button
        self._create_save_button(parent, self._save_advanced_settings)

    def _create_save_button(self, parent, command):
        """Create a save button."""
        if USE_CUSTOMTKINTER:
            btn = ctk.CTkButton(
                parent,
                text="Save Settings",
                command=command,
                width=200
            )
            btn.pack(pady=20)
        else:
            btn = ttk.Button(parent, text="Save Settings", command=command)
            btn.pack(pady=20)

    def _open_url(self, url: str):
        """Open a URL in the default browser."""
        import webbrowser
        webbrowser.open(url)

    def _load_api_key(self, entry, key_name: str):
        """Load an API key from secure storage or environment."""
        env_map = {
            "openai_api_key": "OPENAI_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "google_api_key": "GOOGLE_API_KEY",
            "aws_access_key": "AWS_ACCESS_KEY_ID"
        }
        
        env_var = env_map.get(key_name)
        if env_var:
            # Try to get from config manager's secure storage
            value = None
            if self.config_manager:
                value = self.config_manager.get_api_key(env_var)
            
            # Fallback to environment
            if not value:
                value = os.environ.get(env_var, "")
            
            if value:
                entry.insert(0, value)

    def _load_provider_settings(self):
        """Load provider settings from config."""
        if self.config_manager:
            try:
                config = self.config_manager.get_config()
                self.provider_var.set(config.agent.provider.value)
                if hasattr(self, 'model_entry'):
                    self.model_entry.delete(0, tk.END)
                    self.model_entry.insert(0, config.agent.model)
                if hasattr(self, 'ollama_url_entry') and config.agent.base_url:
                    self.ollama_url_entry.delete(0, tk.END)
                    self.ollama_url_entry.insert(0, config.agent.base_url)
            except Exception:
                pass

    def _load_advanced_settings(self):
        """Load advanced settings from config."""
        if self.config_manager:
            try:
                config = self.config_manager.get_config()
                self.dry_run_var.set(config.security.dry_run)
                self.confirm_destructive_var.set(config.security.confirm_destructive)
                self.audit_logging_var.set(config.security.audit_logging)
                self.verbose_var.set(config.verbose)
                self.debug_var.set(config.debug)
            except Exception:
                pass

    def _get_permission_status(self, permission: str) -> bool:
        """Get the current status of a permission."""
        if self.permission_manager:
            return self.permission_manager.has_permission(permission)
        return False

    def _save_api_keys(self):
        """Save API keys to secure storage."""
        try:
            if self.config_manager:
                saved_count = 0
                
                key_entries = [
                    ("openai_api_key_entry", "OPENAI_API_KEY"),
                    ("anthropic_api_key_entry", "ANTHROPIC_API_KEY"),
                    ("google_api_key_entry", "GOOGLE_API_KEY"),
                    ("aws_access_key_entry", "AWS_ACCESS_KEY_ID"),
                ]
                
                for entry_name, env_name in key_entries:
                    if hasattr(self, entry_name):
                        entry = getattr(self, entry_name)
                        key_value = entry.get().strip()
                        if key_value:
                            if self.config_manager.save_api_key(env_name, key_value):
                                saved_count += 1
                
                if saved_count > 0:
                    messagebox.showinfo("Success", f"Saved {saved_count} API key(s) securely!\n\nKeys are stored in:\n• System keyring (if available)\n• {self.config_manager.env_file}")
                else:
                    messagebox.showinfo("Info", "No API keys to save. Enter your keys first.")
            else:
                messagebox.showerror("Error", "Could not save API keys - config manager not initialized")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API keys: {e}")

    def _save_provider_settings(self):
        """Save provider settings to config."""
        try:
            if self.config_manager:
                config = self.config_manager.get_config()
                
                # Update provider
                from ..types import LLMProvider
                provider_str = self.provider_var.get()
                try:
                    config.agent.provider = LLMProvider(provider_str)
                except ValueError:
                    config.agent.provider = LLMProvider.OPENAI
                
                # Update model
                if hasattr(self, 'model_entry'):
                    model = self.model_entry.get()
                    if model:
                        config.agent.model = model
                
                # Update Ollama URL
                if hasattr(self, 'ollama_url_entry'):
                    url = self.ollama_url_entry.get()
                    if url:
                        config.agent.base_url = url
                
                self.config_manager.save_config()
                messagebox.showinfo("Success", "Provider settings saved successfully!")
            else:
                messagebox.showerror("Error", "Could not save settings - config manager not initialized")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save provider settings: {e}")

    def _save_permissions(self):
        """Save permissions."""
        try:
            if self.permission_manager:
                for perm_key, var in self.permission_vars.items():
                    if var.get():
                        self.permission_manager.grant_permission(perm_key)
                    else:
                        self.permission_manager.revoke_permission(perm_key)
                
                messagebox.showinfo("Success", "Permissions saved successfully!")
            else:
                messagebox.showerror("Error", "Could not save permissions - permission manager not initialized")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save permissions: {e}")

    def _grant_all_permissions(self):
        """Grant all permissions."""
        for var in self.permission_vars.values():
            var.set(True)

    def _revoke_all_permissions(self):
        """Revoke all permissions."""
        for var in self.permission_vars.values():
            var.set(False)

    def _save_advanced_settings(self):
        """Save advanced settings."""
        try:
            if self.config_manager:
                config = self.config_manager.get_config()
                
                config.security.dry_run = self.dry_run_var.get()
                config.security.confirm_destructive = self.confirm_destructive_var.get()
                config.security.audit_logging = self.audit_logging_var.get()
                config.verbose = self.verbose_var.get()
                config.debug = self.debug_var.get()
                
                self.config_manager.save_config()
                messagebox.showinfo("Success", "Advanced settings saved successfully!")
            else:
                messagebox.showerror("Error", "Could not save settings - config manager not initialized")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save advanced settings: {e}")

    def _export_config(self):
        """Export configuration to a file."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if file_path and self.config_manager:
                self.config_manager.export_config(file_path)
                messagebox.showinfo("Success", f"Configuration exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export configuration: {e}")

    def _import_config(self):
        """Import configuration from a file."""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if file_path and self.config_manager:
                self.config_manager.import_config(file_path)
                messagebox.showinfo("Success", "Configuration imported successfully!")
                self._load_provider_settings()
                self._load_advanced_settings()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import configuration: {e}")

    def _reset_config(self):
        """Reset configuration to defaults."""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to defaults?"):
            try:
                if self.config_manager:
                    self.config_manager.reset_config()
                    messagebox.showinfo("Success", "Configuration reset to defaults!")
                    self._load_provider_settings()
                    self._load_advanced_settings()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset configuration: {e}")

    def run(self):
        """Run the settings window."""
        self._create_window()
        self._create_widgets()
        self.root.mainloop()


if __name__ == "__main__":
    app = SettingsWindow()
    app.run()
