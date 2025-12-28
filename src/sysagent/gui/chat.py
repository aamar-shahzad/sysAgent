"""
Chat Interface for SysAgent GUI - Improved Version.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
from typing import Optional, Callable, List
from datetime import datetime

try:
    import customtkinter as ctk
    USE_CUSTOMTKINTER = True
except ImportError:
    USE_CUSTOMTKINTER = False


class ChatMessage:
    """Represents a chat message."""
    
    def __init__(self, content: str, is_user: bool, timestamp: Optional[datetime] = None, 
                 message_type: str = "text"):
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()
        self.message_type = message_type  # text, code, error, success, info


class ChatInterface:
    """Improved chat interface widget for interacting with SysAgent."""
    
    def __init__(self, parent, on_send: Optional[Callable[[str], None]] = None):
        """Initialize chat interface."""
        self.parent = parent
        self.on_send = on_send
        self.messages: List[ChatMessage] = []
        self.message_queue = queue.Queue()
        self.is_processing = False
        self.command_history: List[str] = []
        self.history_index = -1
        
        self._create_widgets()
        self._start_message_processor()
        self._bind_shortcuts()
    
    def _create_widgets(self):
        """Create chat interface widgets."""
        if USE_CUSTOMTKINTER:
            self.frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        else:
            self.frame = ttk.Frame(self.parent)
        
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self._create_header()
        self._create_messages_area()
        self._create_input_area()
        self._create_quick_actions()
    
    def _create_header(self):
        """Create chat header with status and controls."""
        if USE_CUSTOMTKINTER:
            header = ctk.CTkFrame(self.frame, fg_color=("gray90", "gray17"), corner_radius=10)
            header.pack(fill="x", padx=5, pady=(5, 10))
            
            # Left side - Title and status
            left_frame = ctk.CTkFrame(header, fg_color="transparent")
            left_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
            
            title = ctk.CTkLabel(
                left_frame,
                text="🧠 SysAgent Assistant",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title.pack(side="left")
            
            self.status_label = ctk.CTkLabel(
                left_frame,
                text="● Ready",
                font=ctk.CTkFont(size=12),
                text_color="#00d26a"
            )
            self.status_label.pack(side="left", padx=15)
            
            # Right side - Controls
            right_frame = ctk.CTkFrame(header, fg_color="transparent")
            right_frame.pack(side="right", padx=10, pady=8)
            
            # Export button
            export_btn = ctk.CTkButton(
                right_frame,
                text="📤",
                width=35,
                height=35,
                corner_radius=8,
                command=self._export_chat,
                fg_color="transparent",
                hover_color=("gray80", "gray30")
            )
            export_btn.pack(side="left", padx=2)
            
            # Clear button
            clear_btn = ctk.CTkButton(
                right_frame,
                text="🗑️",
                width=35,
                height=35,
                corner_radius=8,
                command=self.clear_chat,
                fg_color="transparent",
                hover_color=("gray80", "gray30")
            )
            clear_btn.pack(side="left", padx=2)
        else:
            header = ttk.Frame(self.frame)
            header.pack(fill="x", padx=5, pady=5)
            
            title = ttk.Label(header, text="🧠 SysAgent Assistant", font=("", 14, "bold"))
            title.pack(side="left", padx=10)
            
            self.status_label = ttk.Label(header, text="● Ready", foreground="green")
            self.status_label.pack(side="left", padx=10)
            
            ttk.Button(header, text="Clear", command=self.clear_chat).pack(side="right", padx=5)
    
    def _create_messages_area(self):
        """Create scrollable messages area with improved styling."""
        if USE_CUSTOMTKINTER:
            # Container with border
            container = ctk.CTkFrame(self.frame, fg_color=("gray95", "gray10"), corner_radius=10)
            container.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.messages_frame = ctk.CTkScrollableFrame(
                container,
                fg_color="transparent",
                corner_radius=0
            )
            self.messages_frame.pack(fill="both", expand=True, padx=2, pady=2)
        else:
            container = ttk.Frame(self.frame)
            container.pack(fill="both", expand=True, padx=5, pady=5)
            
            canvas = tk.Canvas(container, bg="white", highlightthickness=0)
            scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
            
            self.messages_frame = ttk.Frame(canvas)
            
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            
            canvas_frame = canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")
            
            def configure_scroll(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.itemconfig(canvas_frame, width=event.width)
            
            self.messages_frame.bind("<Configure>", configure_scroll)
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))
            
            self._canvas = canvas
        
        # Add welcome message
        self._add_welcome_message()
    
    def _add_welcome_message(self):
        """Add a styled welcome message."""
        welcome_text = """Welcome to SysAgent! 🎉

I'm your intelligent system assistant. I can help you with:

📊 System monitoring and diagnostics
📁 File management and organization  
⚙️ Process control and management
🌐 Network diagnostics
🔧 System maintenance tasks
💻 Running shell commands

Try asking me something like:
• "Show my system info"
• "What's using the most CPU?"
• "Clean up temp files"
• "List running processes"

Type your message below or use a quick action to get started!"""
        
        self._add_system_message(welcome_text)
    
    def _create_input_area(self):
        """Create message input area with improved design."""
        if USE_CUSTOMTKINTER:
            input_container = ctk.CTkFrame(self.frame, fg_color=("gray90", "gray17"), corner_radius=10)
            input_container.pack(fill="x", padx=5, pady=5)
            
            # Inner frame for padding
            inner_frame = ctk.CTkFrame(input_container, fg_color="transparent")
            inner_frame.pack(fill="x", padx=10, pady=10)
            
            # Text input with placeholder
            self.input_text = ctk.CTkTextbox(
                inner_frame,
                height=70,
                corner_radius=10,
                fg_color=("white", "gray20"),
                border_width=1,
                border_color=("gray70", "gray40")
            )
            self.input_text.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            # Placeholder text
            self.input_text.insert("1.0", "Type your message here... (Enter to send, Shift+Enter for new line)")
            self.input_text.configure(text_color="gray50")
            self._placeholder_active = True
            
            self.input_text.bind("<FocusIn>", self._on_focus_in)
            self.input_text.bind("<FocusOut>", self._on_focus_out)
            self.input_text.bind("<Return>", self._on_enter)
            self.input_text.bind("<Shift-Return>", lambda e: None)
            self.input_text.bind("<Up>", self._on_history_up)
            self.input_text.bind("<Down>", self._on_history_down)
            
            # Button frame
            btn_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
            btn_frame.pack(side="right")
            
            # Send button
            self.send_btn = ctk.CTkButton(
                btn_frame,
                text="Send ➤",
                width=90,
                height=40,
                corner_radius=10,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=self._send_message
            )
            self.send_btn.pack(pady=(0, 5))
            
            # Voice button (placeholder)
            voice_btn = ctk.CTkButton(
                btn_frame,
                text="🎤",
                width=40,
                height=25,
                corner_radius=8,
                fg_color="transparent",
                hover_color=("gray80", "gray30"),
                command=self._voice_input
            )
            voice_btn.pack()
        else:
            input_frame = ttk.Frame(self.frame)
            input_frame.pack(fill="x", padx=5, pady=5)
            
            self.input_text = tk.Text(input_frame, height=3, wrap="word")
            self.input_text.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            self.input_text.bind("<Return>", self._on_enter)
            self.input_text.bind("<Shift-Return>", lambda e: None)
            
            self.send_btn = ttk.Button(input_frame, text="Send", command=self._send_message)
            self.send_btn.pack(side="right")
            
            self._placeholder_active = False
    
    def _create_quick_actions(self):
        """Create quick action buttons with categories."""
        if USE_CUSTOMTKINTER:
            actions_container = ctk.CTkFrame(self.frame, fg_color="transparent")
            actions_container.pack(fill="x", padx=5, pady=(0, 5))
            
            # Scrollable frame for actions
            actions_scroll = ctk.CTkScrollableFrame(
                actions_container,
                orientation="horizontal",
                height=45,
                fg_color="transparent"
            )
            actions_scroll.pack(fill="x")
            
            quick_commands = [
                ("💻 System Info", "Show me detailed system information"),
                ("📊 CPU Usage", "What's my current CPU usage?"),
                ("🧠 Memory", "Show memory usage details"),
                ("💾 Disk Space", "Check disk space usage"),
                ("📈 Top Processes", "Show top 10 processes by CPU"),
                ("🌐 Network", "Show network status and connections"),
                ("🧹 Clean Temp", "Clean up temporary files"),
                ("📁 Downloads", "List files in Downloads folder"),
                ("🔄 Uptime", "How long has the system been running?"),
                ("🔋 Battery", "Show battery status"),
            ]
            
            for text, command in quick_commands:
                btn = ctk.CTkButton(
                    actions_scroll,
                    text=text,
                    height=32,
                    corner_radius=16,
                    font=ctk.CTkFont(size=12),
                    fg_color=("gray80", "gray25"),
                    hover_color=("gray70", "gray35"),
                    text_color=("gray20", "gray90"),
                    command=lambda c=command: self._quick_send(c)
                )
                btn.pack(side="left", padx=3)
        else:
            actions_frame = ttk.Frame(self.frame)
            actions_frame.pack(fill="x", padx=5, pady=5)
            
            quick_commands = [
                ("System Info", "Show me system information"),
                ("CPU", "What's my CPU usage?"),
                ("Memory", "Show memory usage"),
                ("Disk", "Check disk space"),
            ]
            
            for text, command in quick_commands:
                ttk.Button(
                    actions_frame,
                    text=text,
                    command=lambda c=command: self._quick_send(c)
                ).pack(side="left", padx=3)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        try:
            self.parent.bind("<Control-l>", lambda e: self.clear_chat())
            self.parent.bind("<Control-e>", lambda e: self._export_chat())
        except Exception:
            pass
    
    def _on_focus_in(self, event):
        """Handle focus in - remove placeholder."""
        if self._placeholder_active:
            self.input_text.delete("1.0", "end")
            if USE_CUSTOMTKINTER:
                self.input_text.configure(text_color=("gray10", "gray90"))
            self._placeholder_active = False
    
    def _on_focus_out(self, event):
        """Handle focus out - add placeholder if empty."""
        content = self.input_text.get("1.0", "end").strip()
        if not content:
            self._placeholder_active = True
            self.input_text.insert("1.0", "Type your message here... (Enter to send, Shift+Enter for new line)")
            if USE_CUSTOMTKINTER:
                self.input_text.configure(text_color="gray50")
    
    def _on_history_up(self, event):
        """Navigate command history up."""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", self.command_history[-(self.history_index + 1)])
        return "break"
    
    def _on_history_down(self, event):
        """Navigate command history down."""
        if self.history_index > 0:
            self.history_index -= 1
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", self.command_history[-(self.history_index + 1)])
        elif self.history_index == 0:
            self.history_index = -1
            self.input_text.delete("1.0", "end")
        return "break"
    
    def _on_enter(self, event):
        """Handle Enter key press."""
        if not event.state & 0x1:  # Shift not pressed
            self._send_message()
            return "break"
        return None
    
    def _quick_send(self, message: str):
        """Send a quick action message."""
        if self._placeholder_active:
            self.input_text.delete("1.0", "end")
            self._placeholder_active = False
            if USE_CUSTOMTKINTER:
                self.input_text.configure(text_color=("gray10", "gray90"))
        
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", message)
        self._send_message()
    
    def _send_message(self):
        """Send the current message."""
        message = self.input_text.get("1.0", "end").strip()
        
        # Ignore placeholder text
        if self._placeholder_active or not message or message.startswith("Type your message"):
            return
        
        if self.is_processing:
            return
        
        # Clear input
        self.input_text.delete("1.0", "end")
        
        # Add to history
        if message and (not self.command_history or self.command_history[-1] != message):
            self.command_history.append(message)
        self.history_index = -1
        
        # Add user message
        self._add_user_message(message)
        
        # Set processing state
        self._set_processing(True)
        
        # Process in background
        if self.on_send:
            thread = threading.Thread(target=self._process_message, args=(message,))
            thread.daemon = True
            thread.start()
        else:
            self._add_assistant_message("No agent connected. Please configure your API keys in Settings.")
            self._set_processing(False)
    
    def _process_message(self, message: str):
        """Process message in background thread."""
        try:
            if self.on_send:
                self.on_send(message)
        except Exception as e:
            self.add_message(f"Error: {str(e)}", is_user=False, message_type="error")
        finally:
            try:
                self.parent.after(0, lambda: self._set_processing(False))
            except Exception:
                pass
    
    def _set_processing(self, processing: bool):
        """Set processing state with animation."""
        self.is_processing = processing
        
        try:
            if USE_CUSTOMTKINTER:
                if processing:
                    self.status_label.configure(text="● Processing...", text_color="#ffa500")
                    self.send_btn.configure(state="disabled", text="...")
                else:
                    self.status_label.configure(text="● Ready", text_color="#00d26a")
                    self.send_btn.configure(state="normal", text="Send ➤")
            else:
                if processing:
                    self.status_label.configure(text="● Processing...", foreground="orange")
                    self.send_btn.configure(state="disabled")
                else:
                    self.status_label.configure(text="● Ready", foreground="green")
                    self.send_btn.configure(state="normal")
        except Exception:
            pass
    
    def _add_user_message(self, content: str):
        """Add a user message."""
        self._add_message_bubble(content, is_user=True)
    
    def _add_assistant_message(self, content: str, message_type: str = "text"):
        """Add an assistant message."""
        self._add_message_bubble(content, is_user=False, message_type=message_type)
    
    def _add_system_message(self, content: str):
        """Add a system message with special styling."""
        try:
            if not self.messages_frame or not self.messages_frame.winfo_exists():
                return
        except Exception:
            return
        
        if USE_CUSTOMTKINTER:
            msg_frame = ctk.CTkFrame(
                self.messages_frame,
                fg_color=("gray85", "gray20"),
                corner_radius=10
            )
            msg_frame.pack(fill="x", padx=20, pady=10)
            
            msg_label = ctk.CTkLabel(
                msg_frame,
                text=content,
                font=ctk.CTkFont(size=13),
                text_color=("gray30", "gray70"),
                wraplength=500,
                justify="left"
            )
            msg_label.pack(padx=15, pady=15)
        else:
            msg_frame = ttk.Frame(self.messages_frame)
            msg_frame.pack(fill="x", padx=20, pady=10)
            
            msg_label = ttk.Label(
                msg_frame,
                text=content,
                foreground="gray",
                wraplength=500,
                justify="left"
            )
            msg_label.pack(padx=15, pady=10)
    
    def _add_message_bubble(self, content: str, is_user: bool, message_type: str = "text"):
        """Add a message bubble with improved styling."""
        try:
            if not self.messages_frame or not self.messages_frame.winfo_exists():
                return
        except Exception:
            return
        
        timestamp = datetime.now().strftime("%H:%M")
        
        if USE_CUSTOMTKINTER:
            # Container for alignment
            container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
            container.pack(fill="x", padx=10, pady=5)
            
            # Bubble styling based on sender and type
            if is_user:
                anchor = "e"
                bg_color = "#1a73e8"  # Google blue
                text_color = "white"
                max_width = 450
            else:
                anchor = "w"
                if message_type == "error":
                    bg_color = "#d32f2f"
                    text_color = "white"
                elif message_type == "success":
                    bg_color = "#388e3c"
                    text_color = "white"
                elif message_type == "code":
                    bg_color = "#263238"
                    text_color = "#80cbc4"
                else:
                    bg_color = ("gray80", "gray25")
                    text_color = ("gray10", "gray90")
                max_width = 500
            
            # Message bubble
            bubble = ctk.CTkFrame(container, fg_color=bg_color, corner_radius=18)
            bubble.pack(anchor=anchor, padx=5)
            
            # Avatar and sender
            header_frame = ctk.CTkFrame(bubble, fg_color="transparent")
            header_frame.pack(fill="x", padx=12, pady=(10, 2))
            
            avatar = "👤" if is_user else "🧠"
            sender = "You" if is_user else "SysAgent"
            
            avatar_label = ctk.CTkLabel(
                header_frame,
                text=f"{avatar} {sender}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=text_color if isinstance(text_color, str) else None
            )
            avatar_label.pack(side="left")
            
            time_label = ctk.CTkLabel(
                header_frame,
                text=timestamp,
                font=ctk.CTkFont(size=10),
                text_color="gray60" if is_user else "gray50"
            )
            time_label.pack(side="right")
            
            # Message content
            msg_label = ctk.CTkLabel(
                bubble,
                text=content,
                font=ctk.CTkFont(size=13, family="Consolas" if message_type == "code" else None),
                text_color=text_color if isinstance(text_color, str) else None,
                wraplength=max_width,
                justify="left"
            )
            msg_label.pack(anchor="w", padx=12, pady=(2, 10))
            
            # Action buttons frame
            actions_frame = ctk.CTkFrame(bubble, fg_color="transparent")
            actions_frame.pack(fill="x", padx=10, pady=(0, 8))
            
            # Copy button
            copy_btn = ctk.CTkButton(
                actions_frame,
                text="📋 Copy",
                width=55,
                height=22,
                corner_radius=5,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color=("gray70", "gray40"),
                command=lambda c=content: self._copy_to_clipboard(c)
            )
            copy_btn.pack(side="left", padx=2)
            
            # Save to file button
            save_btn = ctk.CTkButton(
                actions_frame,
                text="💾 Save",
                width=55,
                height=22,
                corner_radius=5,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color=("gray70", "gray40"),
                command=lambda c=content: self._save_message_to_file(c)
            )
            save_btn.pack(side="left", padx=2)
            
            # More actions for assistant messages
            if not is_user:
                # Retry button
                retry_btn = ctk.CTkButton(
                    actions_frame,
                    text="🔄 Retry",
                    width=55,
                    height=22,
                    corner_radius=5,
                    font=ctk.CTkFont(size=10),
                    fg_color="transparent",
                    hover_color=("gray70", "gray40"),
                    command=lambda: self._retry_last_message()
                )
                retry_btn.pack(side="left", padx=2)
                
                # Open in app button (for code/data)
                if message_type in ["code", "text"] or "```" in content:
                    open_btn = ctk.CTkButton(
                        actions_frame,
                        text="📝 Open",
                        width=55,
                        height=22,
                        corner_radius=5,
                        font=ctk.CTkFont(size=10),
                        fg_color="transparent",
                        hover_color=("gray70", "gray40"),
                        command=lambda c=content: self._open_in_editor(c)
                    )
                    open_btn.pack(side="left", padx=2)
            
            # Bind right-click context menu
            self._bind_context_menu(bubble, content, is_user)
            self._bind_context_menu(msg_label, content, is_user)
            
            # Legacy copy button removed - replaced with action buttons above
            if False:  # Disabled
                copy_btn = ctk.CTkButton(
                    bubble,
                    text="📋 Copy",
                    width=60,
                    height=22,
                    corner_radius=5,
                    font=ctk.CTkFont(size=10),
                    fg_color="transparent",
                    hover_color=("gray70", "gray40"),
                    command=lambda c=content: self._copy_to_clipboard(c)
                )
                copy_btn.pack(anchor="e", padx=10, pady=(0, 8))
        else:
            container = ttk.Frame(self.messages_frame)
            container.pack(fill="x", padx=10, pady=5)
            
            if is_user:
                anchor = "e"
                bg = "#e3f2fd"
            else:
                bg = "#f5f5f5" if message_type == "text" else "#ffebee"
            
            bubble = tk.Frame(container, bg=bg, padx=12, pady=8)
            bubble.pack(anchor=anchor if is_user else "w")
            
            sender = "You" if is_user else "🧠 SysAgent"
            tk.Label(bubble, text=sender, font=("", 9, "bold"), bg=bg).pack(anchor="w")
            tk.Label(bubble, text=content, wraplength=400, justify="left", bg=bg).pack(anchor="w", pady=2)
            tk.Label(bubble, text=timestamp, font=("", 8), fg="gray", bg=bg).pack(anchor="e")
        
        self._scroll_to_bottom()
    
    def _scroll_to_bottom(self):
        """Scroll to bottom of messages."""
        try:
            if USE_CUSTOMTKINTER:
                if hasattr(self.messages_frame, '_parent_canvas'):
                    self.messages_frame._parent_canvas.yview_moveto(1.0)
            else:
                if hasattr(self, '_canvas'):
                    self._canvas.yview_moveto(1.0)
        except Exception:
            pass
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
            # Show brief feedback
            if USE_CUSTOMTKINTER:
                self.status_label.configure(text="● Copied!", text_color="#00d26a")
                self.parent.after(1500, lambda: self.status_label.configure(text="● Ready", text_color="#00d26a"))
        except Exception:
            pass

    def _save_message_to_file(self, content: str):
        """Save a message to a file."""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown", "*.md"),
                ("Python", "*.py"),
                ("JSON", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(content)
                
                if USE_CUSTOMTKINTER:
                    self.status_label.configure(text="● Saved!", text_color="#00d26a")
                    self.parent.after(1500, lambda: self.status_label.configure(text="● Ready", text_color="#00d26a"))
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Save Error", f"Failed to save: {e}")

    def _retry_last_message(self):
        """Retry the last user message."""
        if self.command_history:
            last_message = self.command_history[-1]
            self._quick_send(last_message)

    def _open_in_editor(self, content: str):
        """Open content in default text editor."""
        import tempfile
        import subprocess
        import os
        
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            # Open in default editor
            from ..utils.platform import detect_platform, Platform
            platform = detect_platform()
            
            if platform == Platform.MACOS:
                subprocess.Popen(["open", temp_path])
            elif platform == Platform.WINDOWS:
                os.startfile(temp_path)
            else:  # Linux
                # Try common editors
                for editor in ["xdg-open", "gedit", "kate", "nano", "vim"]:
                    try:
                        subprocess.Popen([editor, temp_path])
                        break
                    except FileNotFoundError:
                        continue
            
            if USE_CUSTOMTKINTER:
                self.status_label.configure(text="● Opened!", text_color="#00d26a")
                self.parent.after(1500, lambda: self.status_label.configure(text="● Ready", text_color="#00d26a"))
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to open editor: {e}")

    def _bind_context_menu(self, widget, content: str, is_user: bool):
        """Bind right-click context menu to a widget."""
        menu = tk.Menu(widget, tearoff=0)
        
        menu.add_command(label="📋 Copy", command=lambda: self._copy_to_clipboard(content))
        menu.add_command(label="💾 Save to File", command=lambda: self._save_message_to_file(content))
        menu.add_command(label="📝 Open in Editor", command=lambda: self._open_in_editor(content))
        menu.add_separator()
        
        if not is_user:
            menu.add_command(label="🔄 Retry Last", command=self._retry_last_message)
            menu.add_separator()
        
        menu.add_command(label="📤 Export Chat", command=self._export_chat)
        menu.add_command(label="🗑️ Clear Chat", command=self.clear_chat)
        
        def show_menu(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        
        widget.bind("<Button-3>", show_menu)  # Right-click
        if USE_CUSTOMTKINTER:
            widget.bind("<Button-2>", show_menu)  # Middle-click on Mac
    
    def _export_chat(self):
        """Export chat history."""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Markdown", "*.md"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write("SysAgent Chat Export\n")
                    f.write("=" * 50 + "\n\n")
                    for msg in self.messages:
                        sender = "You" if msg.is_user else "SysAgent"
                        timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] {sender}:\n{msg.content}\n\n")
                
                if USE_CUSTOMTKINTER:
                    self.status_label.configure(text="● Exported!", text_color="#00d26a")
                    self.parent.after(2000, lambda: self.status_label.configure(text="● Ready", text_color="#00d26a"))
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Export Error", f"Failed to export: {e}")
    
    def _voice_input(self):
        """Handle voice input (placeholder)."""
        from tkinter import messagebox
        messagebox.showinfo("Voice Input", "Voice input requires the voice module.\nInstall with: pip install sysagent-cli[voice]")
    
    def add_message(self, content: str, is_user: bool = False, message_type: str = "text"):
        """Add a message (thread-safe)."""
        self.messages.append(ChatMessage(content, is_user, message_type=message_type))
        self.message_queue.put((content, is_user, message_type))
    
    def _start_message_processor(self):
        """Start background message processor."""
        def process_queue():
            try:
                while True:
                    item = self.message_queue.get_nowait()
                    if len(item) == 3:
                        content, is_user, msg_type = item
                    else:
                        content, is_user = item
                        msg_type = "text"
                    
                    if is_user:
                        self._add_user_message(content)
                    else:
                        self._add_assistant_message(content, msg_type)
            except queue.Empty:
                pass
            except Exception:
                pass
            finally:
                try:
                    self.parent.after(100, process_queue)
                except Exception:
                    pass
        
        try:
            self.parent.after(100, process_queue)
        except Exception:
            pass
    
    def clear_chat(self):
        """Clear all messages."""
        try:
            if self.messages_frame and self.messages_frame.winfo_exists():
                for widget in self.messages_frame.winfo_children():
                    widget.destroy()
                
                self.messages.clear()
                self._add_system_message("Chat cleared. How can I help you?")
        except Exception:
            pass
    
    def get_frame(self):
        """Get the main frame widget."""
        return self.frame


class ChatWindow:
    """Standalone chat window."""
    
    def __init__(self):
        self.root = None
        self.agent = None
        self.chat = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the LangGraph agent."""
        try:
            from ..core.config import ConfigManager
            from ..core.permissions import PermissionManager
            from ..core.langgraph_agent import LangGraphAgent
            
            config_manager = ConfigManager()
            permission_manager = PermissionManager(config_manager)
            self.agent = LangGraphAgent(config_manager, permission_manager)
        except Exception as e:
            print(f"Warning: Could not initialize agent: {e}")
            self.agent = None
    
    def _create_window(self):
        """Create the chat window."""
        if USE_CUSTOMTKINTER:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title("SysAgent Chat")
        self.root.geometry("800x900")
        self.root.minsize(600, 700)
        
        return self.root
    
    def _on_message(self, message: str):
        """Handle incoming user message."""
        if self.agent:
            try:
                result = self.agent.process_command(message)
                
                if result.get('success'):
                    response = result.get('message', 'Command executed successfully.')
                    
                    if result.get('data', {}).get('tools_used'):
                        tools = result['data']['tools_used']
                        response += f"\n\n📦 Tools used: {', '.join(tools)}"
                    
                    self.chat.add_message(response, is_user=False)
                else:
                    error_msg = f"❌ {result.get('message', 'Unknown error')}"
                    if result.get('error'):
                        error_msg += f"\n{result['error']}"
                    self.chat.add_message(error_msg, is_user=False, message_type="error")
                
            except Exception as e:
                self.chat.add_message(f"❌ Error: {str(e)}", is_user=False, message_type="error")
        else:
            self.chat.add_message(
                "⚠️ Agent not available. Please check your API keys in Settings.",
                is_user=False,
                message_type="error"
            )
    
    def run(self):
        """Run the chat window."""
        self._create_window()
        self.chat = ChatInterface(self.root, on_send=self._on_message)
        self.root.mainloop()


def launch_chat():
    """Launch the chat window."""
    window = ChatWindow()
    window.run()


if __name__ == "__main__":
    launch_chat()
