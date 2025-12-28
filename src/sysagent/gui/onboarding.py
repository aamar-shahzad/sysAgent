"""
Onboarding Wizard for SysAgent - First-time user setup experience.
Professional guided setup for new users.
"""

import os
from typing import Optional, Callable
from pathlib import Path

# Handle missing tkinter gracefully
try:
    import tkinter as tk
    from tkinter import messagebox
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False
    tk = None
    messagebox = None

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None


class OnboardingWizard:
    """
    First-time user onboarding wizard.
    
    Steps:
    1. Welcome
    2. API Key Setup
    3. Permission Configuration
    4. Choose Agent Mode
    5. Quick Tour
    6. Ready to Go
    """
    
    STEPS = [
        "welcome",
        "api_key",
        "permissions",
        "mode",
        "tour",
        "complete"
    ]
    
    def __init__(self, on_complete: Optional[Callable] = None):
        self.on_complete = on_complete
        self.current_step = 0
        self.data = {
            "api_key": "",
            "permissions": [],
            "mode": "general"
        }
        self.window = None
        self.content_frame = None
    
    def should_show(self) -> bool:
        """Check if onboarding should be shown."""
        config_dir = Path.home() / ".sysagent"
        onboarding_file = config_dir / ".onboarding_complete"
        
        if onboarding_file.exists():
            return False
        
        # Check if API key is set
        if os.environ.get("OPENAI_API_KEY"):
            return False
        
        env_file = config_dir / ".env"
        if env_file.exists():
            try:
                content = env_file.read_text()
                if "OPENAI_API_KEY=" in content and len(content.split("OPENAI_API_KEY=")[1].strip()) > 10:
                    return False
            except:
                pass
        
        return True
    
    def mark_complete(self):
        """Mark onboarding as complete."""
        config_dir = Path.home() / ".sysagent"
        config_dir.mkdir(parents=True, exist_ok=True)
        onboarding_file = config_dir / ".onboarding_complete"
        onboarding_file.touch()
    
    def show(self):
        """Show the onboarding wizard."""
        if not CTK_AVAILABLE:
            # Fallback to simple prompt
            self._simple_onboarding()
            return
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.window = ctk.CTkToplevel() if hasattr(ctk, 'CTkToplevel') else ctk.CTk()
        self.window.title("Welcome to SysAgent")
        self.window.geometry("700x550")
        self.window.resizable(False, False)
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 700) // 2
        y = (self.window.winfo_screenheight() - 550) // 2
        self.window.geometry(f"700x550+{x}+{y}")
        
        # Main container
        main = ctk.CTkFrame(self.window, fg_color="#0f172a")
        main.pack(fill="both", expand=True)
        
        # Header with logo
        header = ctk.CTkFrame(main, fg_color="transparent", height=80)
        header.pack(fill="x", padx=40, pady=(30, 0))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="🧠 SysAgent",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="white"
        ).pack(side="left")
        
        # Progress indicator
        self.progress_frame = ctk.CTkFrame(main, fg_color="transparent", height=40)
        self.progress_frame.pack(fill="x", padx=40, pady=(20, 0))
        self._update_progress()
        
        # Content area
        self.content_frame = ctk.CTkFrame(main, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Navigation
        nav = ctk.CTkFrame(main, fg_color="transparent", height=60)
        nav.pack(fill="x", padx=40, pady=(0, 30))
        nav.pack_propagate(False)
        
        self.back_btn = ctk.CTkButton(
            nav,
            text="← Back",
            width=100,
            fg_color="transparent",
            hover_color="#1e293b",
            command=self._prev_step
        )
        self.back_btn.pack(side="left")
        
        self.next_btn = ctk.CTkButton(
            nav,
            text="Continue →",
            width=140,
            font=ctk.CTkFont(weight="bold"),
            command=self._next_step
        )
        self.next_btn.pack(side="right")
        
        self.skip_btn = ctk.CTkButton(
            nav,
            text="Skip Setup",
            width=100,
            fg_color="transparent",
            hover_color="#1e293b",
            text_color="#64748b",
            command=self._skip
        )
        self.skip_btn.pack(side="right", padx=10)
        
        # Show first step
        self._show_step()
        
        self.window.mainloop()
    
    def _update_progress(self):
        """Update progress indicator."""
        for widget in self.progress_frame.winfo_children():
            widget.destroy()
        
        for i, step in enumerate(self.STEPS):
            color = "#3b82f6" if i <= self.current_step else "#334155"
            
            dot = ctk.CTkFrame(
                self.progress_frame,
                width=12,
                height=12,
                corner_radius=6,
                fg_color=color
            )
            dot.pack(side="left", padx=4)
            
            if i < len(self.STEPS) - 1:
                line = ctk.CTkFrame(
                    self.progress_frame,
                    width=40,
                    height=2,
                    fg_color=color if i < self.current_step else "#334155"
                )
                line.pack(side="left")
    
    def _clear_content(self):
        """Clear content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _show_step(self):
        """Show the current step."""
        self._clear_content()
        self._update_progress()
        
        step = self.STEPS[self.current_step]
        
        # Update navigation buttons
        self.back_btn.configure(state="normal" if self.current_step > 0 else "disabled")
        
        if step == "complete":
            self.next_btn.configure(text="Get Started")
            self.skip_btn.pack_forget()
        else:
            self.next_btn.configure(text="Continue →")
        
        # Show step content
        method = getattr(self, f"_step_{step}", None)
        if method:
            method()
    
    def _step_welcome(self):
        """Welcome step."""
        ctk.CTkLabel(
            self.content_frame,
            text="Welcome to SysAgent! 🎉",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            self.content_frame,
            text="Your intelligent system assistant",
            font=ctk.CTkFont(size=16),
            text_color="#94a3b8"
        ).pack(pady=(0, 30))
        
        features = [
            ("🤖", "Natural Language Control", "Control your system with plain English"),
            ("🔧", "33+ Powerful Tools", "File management, system monitoring, automation"),
            ("⚡", "Workflow Automation", "Create and run multi-step workflows"),
            ("🔒", "Secure by Design", "Permission-based access control"),
        ]
        
        for icon, title, desc in features:
            row = ctk.CTkFrame(self.content_frame, fg_color="#1e293b", corner_radius=10)
            row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=24), width=50).pack(side="left", padx=15, pady=15)
            
            text_frame = ctk.CTkFrame(row, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True, pady=15)
            
            ctk.CTkLabel(
                text_frame,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                text_frame,
                text=desc,
                font=ctk.CTkFont(size=12),
                text_color="#94a3b8",
                anchor="w"
            ).pack(anchor="w")
    
    def _step_api_key(self):
        """API key setup step."""
        ctk.CTkLabel(
            self.content_frame,
            text="Connect Your AI",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            self.content_frame,
            text="SysAgent uses OpenAI's GPT models for intelligent responses",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        ).pack(pady=(0, 30))
        
        # API key input
        form = ctk.CTkFrame(self.content_frame, fg_color="#1e293b", corner_radius=10)
        form.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            form,
            text="OpenAI API Key",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.api_key_entry = ctk.CTkEntry(
            form,
            placeholder_text="sk-...",
            width=400,
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.api_key_entry.pack(padx=20, pady=(0, 10))
        
        if self.data.get("api_key"):
            self.api_key_entry.insert(0, self.data["api_key"])
        
        ctk.CTkLabel(
            form,
            text="Get your API key from: platform.openai.com/api-keys",
            font=ctk.CTkFont(size=11),
            text_color="#64748b"
        ).pack(anchor="w", padx=20, pady=(0, 20))
        
        # Info
        info = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        info.pack(fill="x", pady=20)
        
        ctk.CTkLabel(
            info,
            text="💡 Your API key is stored locally and never shared",
            font=ctk.CTkFont(size=12),
            text_color="#64748b"
        ).pack(anchor="w")
    
    def _step_permissions(self):
        """Permissions setup step."""
        ctk.CTkLabel(
            self.content_frame,
            text="Configure Permissions",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            self.content_frame,
            text="Choose what SysAgent can access on your system",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        ).pack(pady=(0, 20))
        
        permissions = [
            ("file_access", "📁 File Access", "Read and write files", True),
            ("system_info", "📊 System Info", "Access CPU, memory, disk info", True),
            ("process_management", "⚙️ Process Control", "List and manage processes", True),
            ("network_access", "🌐 Network", "Network diagnostics", False),
            ("app_control", "📱 App Control", "Launch and control apps", False),
            ("system_control", "🔧 System Control", "System settings and services", False),
        ]
        
        self.permission_vars = {}
        
        for perm_id, icon_name, desc, default in permissions:
            row = ctk.CTkFrame(self.content_frame, fg_color="#1e293b", corner_radius=8)
            row.pack(fill="x", pady=3)
            
            var = tk.BooleanVar(value=default)
            self.permission_vars[perm_id] = var
            
            cb = ctk.CTkCheckBox(
                row,
                text="",
                variable=var,
                width=24
            )
            cb.pack(side="left", padx=15, pady=12)
            
            ctk.CTkLabel(
                row,
                text=icon_name,
                font=ctk.CTkFont(size=13, weight="bold"),
                width=150,
                anchor="w"
            ).pack(side="left", pady=12)
            
            ctk.CTkLabel(
                row,
                text=desc,
                font=ctk.CTkFont(size=12),
                text_color="#94a3b8"
            ).pack(side="left", pady=12)
        
        # Quick options
        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text="Enable All",
            width=100,
            height=30,
            fg_color="#1e293b",
            command=lambda: self._set_all_permissions(True)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Minimal",
            width=100,
            height=30,
            fg_color="#1e293b",
            command=lambda: self._set_all_permissions(False)
        ).pack(side="left", padx=5)
    
    def _set_all_permissions(self, value: bool):
        """Set all permissions."""
        for var in self.permission_vars.values():
            var.set(value)
    
    def _step_mode(self):
        """Agent mode selection step."""
        ctk.CTkLabel(
            self.content_frame,
            text="Choose Your Mode",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            self.content_frame,
            text="Select a specialized mode or use General for all tasks",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        ).pack(pady=(0, 20))
        
        modes = [
            ("general", "🧠", "General", "All-purpose assistant", "#3b82f6"),
            ("developer", "👨‍💻", "Developer", "Git, code, packages", "#10b981"),
            ("sysadmin", "🔧", "SysAdmin", "System management", "#f59e0b"),
            ("security", "🔒", "Security", "Auditing & scanning", "#ef4444"),
            ("productivity", "⚡", "Productivity", "Apps & workflows", "#8b5cf6"),
        ]
        
        self.mode_var = tk.StringVar(value=self.data.get("mode", "general"))
        
        grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        grid.pack(fill="x")
        
        for i, (mode_id, icon, name, desc, color) in enumerate(modes):
            card = ctk.CTkFrame(
                grid,
                fg_color="#1e293b",
                corner_radius=10,
                border_width=2,
                border_color=color if self.mode_var.get() == mode_id else "#334155"
            )
            card.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="nsew")
            
            # Make clickable
            card.bind("<Button-1>", lambda e, m=mode_id: self._select_mode(m))
            
            ctk.CTkLabel(
                card,
                text=icon,
                font=ctk.CTkFont(size=28)
            ).pack(pady=(15, 5))
            
            ctk.CTkLabel(
                card,
                text=name,
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack()
            
            ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color="#94a3b8"
            ).pack(pady=(2, 15))
        
        for i in range(3):
            grid.grid_columnconfigure(i, weight=1)
    
    def _select_mode(self, mode: str):
        """Select a mode."""
        self.mode_var.set(mode)
        self.data["mode"] = mode
        self._step_mode()  # Refresh to update selection
    
    def _step_tour(self):
        """Quick tour step."""
        ctk.CTkLabel(
            self.content_frame,
            text="Quick Tips",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            self.content_frame,
            text="Get the most out of SysAgent",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        ).pack(pady=(0, 20))
        
        tips = [
            ("⌨️", "Command Palette", "Press Ctrl+K (Cmd+K) for quick commands"),
            ("💬", "Natural Language", "Just type what you want in plain English"),
            ("⚡", "Quick Actions", "Use the buttons below the chat for common tasks"),
            ("🔄", "Workflows", "Create reusable multi-step automations"),
            ("📊", "Insights", "Ask for 'health check' to diagnose your system"),
        ]
        
        for icon, title, desc in tips:
            row = ctk.CTkFrame(self.content_frame, fg_color="#1e293b", corner_radius=8)
            row.pack(fill="x", pady=4)
            
            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=20), width=50).pack(side="left", padx=15, pady=12)
            
            text = ctk.CTkFrame(row, fg_color="transparent")
            text.pack(side="left", fill="x", expand=True, pady=12)
            
            ctk.CTkLabel(text, text=title, font=ctk.CTkFont(weight="bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(text, text=desc, font=ctk.CTkFont(size=12), text_color="#94a3b8", anchor="w").pack(anchor="w")
    
    def _step_complete(self):
        """Complete step."""
        ctk.CTkLabel(
            self.content_frame,
            text="You're All Set! 🎉",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        ).pack(pady=(40, 10))
        
        ctk.CTkLabel(
            self.content_frame,
            text="SysAgent is ready to help you",
            font=ctk.CTkFont(size=16),
            text_color="#94a3b8"
        ).pack(pady=(0, 40))
        
        # Summary
        summary = ctk.CTkFrame(self.content_frame, fg_color="#1e293b", corner_radius=10)
        summary.pack(fill="x", pady=10)
        
        mode_name = self.data.get("mode", "general").title()
        perm_count = len([v for v in self.permission_vars.values() if v.get()]) if hasattr(self, 'permission_vars') else 0
        
        ctk.CTkLabel(
            summary,
            text=f"Mode: {mode_name} | Permissions: {perm_count} enabled",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8"
        ).pack(pady=15)
        
        ctk.CTkLabel(
            self.content_frame,
            text="Try asking: 'Show my system status'",
            font=ctk.CTkFont(size=14),
            text_color="#64748b"
        ).pack(pady=20)
    
    def _next_step(self):
        """Go to next step."""
        # Save current step data
        step = self.STEPS[self.current_step]
        
        if step == "api_key":
            api_key = self.api_key_entry.get().strip()
            if api_key:
                self.data["api_key"] = api_key
                self._save_api_key(api_key)
        
        elif step == "permissions":
            self.data["permissions"] = [
                k for k, v in self.permission_vars.items() if v.get()
            ]
            self._save_permissions()
        
        elif step == "mode":
            self.data["mode"] = self.mode_var.get()
        
        elif step == "complete":
            self._finish()
            return
        
        # Move to next step
        if self.current_step < len(self.STEPS) - 1:
            self.current_step += 1
            self._show_step()
    
    def _prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._show_step()
    
    def _skip(self):
        """Skip onboarding."""
        if messagebox.askyesno("Skip Setup", "Skip the setup wizard? You can configure settings later."):
            self.mark_complete()
            self._close()
    
    def _finish(self):
        """Finish onboarding."""
        self.mark_complete()
        self._close()
        
        if self.on_complete:
            self.on_complete(self.data)
    
    def _close(self):
        """Close the wizard."""
        if self.window:
            self.window.destroy()
    
    def _save_api_key(self, key: str):
        """Save API key."""
        config_dir = Path.home() / ".sysagent"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        env_file = config_dir / ".env"
        with open(env_file, 'w') as f:
            f.write(f"OPENAI_API_KEY={key}\n")
    
    def _save_permissions(self):
        """Save permissions."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            
            config = ConfigManager()
            perms = PermissionManager(config)
            
            for perm in self.data.get("permissions", []):
                perms.grant_permission(perm)
        except Exception as e:
            print(f"Warning: Could not save permissions: {e}")
    
    def _simple_onboarding(self):
        """Simple CLI onboarding fallback."""
        print("\n🧠 Welcome to SysAgent!")
        print("=" * 40)
        print("\nTo get started, you need an OpenAI API key.")
        print("Get one from: https://platform.openai.com/api-keys\n")
        
        api_key = input("Enter your API key (or press Enter to skip): ").strip()
        
        if api_key:
            self._save_api_key(api_key)
            print("✓ API key saved!")
        
        self.mark_complete()
        print("\n✨ Setup complete! Run 'sysagent' to start.\n")


def show_onboarding(on_complete: Callable = None) -> bool:
    """Show onboarding if needed. Returns True if shown."""
    wizard = OnboardingWizard(on_complete)
    
    if wizard.should_show():
        wizard.show()
        return True
    
    return False
