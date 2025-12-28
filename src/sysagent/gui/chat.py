"""
Chat Interface for SysAgent GUI.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
from typing import Optional, Callable
from datetime import datetime

try:
    import customtkinter as ctk
    USE_CUSTOMTKINTER = True
except ImportError:
    USE_CUSTOMTKINTER = False


class ChatMessage:
    """Represents a chat message."""
    
    def __init__(self, content: str, is_user: bool, timestamp: Optional[datetime] = None):
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()


class ChatInterface:
    """Chat interface widget for interacting with SysAgent."""
    
    def __init__(self, parent, on_send: Optional[Callable[[str], None]] = None):
        """Initialize chat interface.
        
        Args:
            parent: Parent widget
            on_send: Callback function when user sends a message
        """
        self.parent = parent
        self.on_send = on_send
        self.messages = []
        self.message_queue = queue.Queue()
        self.is_processing = False
        
        self._create_widgets()
        self._start_message_processor()
    
    def _create_widgets(self):
        """Create chat interface widgets."""
        # Main container
        if USE_CUSTOMTKINTER:
            self.frame = ctk.CTkFrame(self.parent)
        else:
            self.frame = ttk.Frame(self.parent)
        
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Chat header
        self._create_header()
        
        # Messages area
        self._create_messages_area()
        
        # Input area
        self._create_input_area()
        
        # Quick actions
        self._create_quick_actions()
    
    def _create_header(self):
        """Create chat header."""
        if USE_CUSTOMTKINTER:
            header = ctk.CTkFrame(self.frame)
            header.pack(fill="x", padx=5, pady=5)
            
            title = ctk.CTkLabel(
                header,
                text="🧠 SysAgent Chat",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title.pack(side="left", padx=10)
            
            # Status indicator
            self.status_label = ctk.CTkLabel(
                header,
                text="● Ready",
                font=ctk.CTkFont(size=12),
                text_color="green"
            )
            self.status_label.pack(side="right", padx=10)
            
            # Clear button
            clear_btn = ctk.CTkButton(
                header,
                text="Clear",
                width=60,
                command=self.clear_chat
            )
            clear_btn.pack(side="right", padx=5)
        else:
            header = ttk.Frame(self.frame)
            header.pack(fill="x", padx=5, pady=5)
            
            title = ttk.Label(header, text="🧠 SysAgent Chat", font=("", 14, "bold"))
            title.pack(side="left", padx=10)
            
            self.status_label = ttk.Label(header, text="● Ready", foreground="green")
            self.status_label.pack(side="right", padx=10)
            
            ttk.Button(header, text="Clear", command=self.clear_chat).pack(side="right", padx=5)
    
    def _create_messages_area(self):
        """Create scrollable messages area."""
        # Container for messages with scrollbar
        if USE_CUSTOMTKINTER:
            self.messages_frame = ctk.CTkScrollableFrame(
                self.frame,
                label_text="",
                corner_radius=10
            )
            self.messages_frame.pack(fill="both", expand=True, padx=5, pady=5)
        else:
            # Create canvas with scrollbar for messages
            container = ttk.Frame(self.frame)
            container.pack(fill="both", expand=True, padx=5, pady=5)
            
            canvas = tk.Canvas(container, bg="white")
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
        self._add_system_message(
            "Welcome to SysAgent! I'm your intelligent system assistant.\n\n"
            "You can ask me to:\n"
            "• Show system information\n"
            "• Manage files and processes\n"
            "• Monitor system performance\n"
            "• And much more!\n\n"
            "Type a message below to get started."
        )
    
    def _create_input_area(self):
        """Create message input area."""
        if USE_CUSTOMTKINTER:
            input_frame = ctk.CTkFrame(self.frame)
            input_frame.pack(fill="x", padx=5, pady=5)
            
            # Text input
            self.input_text = ctk.CTkTextbox(
                input_frame,
                height=60,
                corner_radius=10
            )
            self.input_text.pack(side="left", fill="x", expand=True, padx=(5, 10))
            
            # Bind Enter key
            self.input_text.bind("<Return>", self._on_enter)
            self.input_text.bind("<Shift-Return>", lambda e: None)  # Allow shift+enter for newline
            
            # Send button
            self.send_btn = ctk.CTkButton(
                input_frame,
                text="Send",
                width=80,
                height=50,
                command=self._send_message
            )
            self.send_btn.pack(side="right", padx=5)
        else:
            input_frame = ttk.Frame(self.frame)
            input_frame.pack(fill="x", padx=5, pady=5)
            
            # Text input
            self.input_text = tk.Text(input_frame, height=3, wrap="word")
            self.input_text.pack(side="left", fill="x", expand=True, padx=(5, 10))
            
            self.input_text.bind("<Return>", self._on_enter)
            self.input_text.bind("<Shift-Return>", lambda e: None)
            
            # Send button
            self.send_btn = ttk.Button(input_frame, text="Send", command=self._send_message)
            self.send_btn.pack(side="right", padx=5)
    
    def _create_quick_actions(self):
        """Create quick action buttons."""
        if USE_CUSTOMTKINTER:
            actions_frame = ctk.CTkFrame(self.frame)
            actions_frame.pack(fill="x", padx=5, pady=5)
            
            label = ctk.CTkLabel(actions_frame, text="Quick Actions:", font=ctk.CTkFont(size=12))
            label.pack(side="left", padx=5)
            
            quick_commands = [
                ("System Info", "Show me system information"),
                ("CPU Usage", "What's my CPU usage?"),
                ("Memory", "Show memory usage"),
                ("Disk Space", "Check disk space"),
                ("Processes", "List top processes by CPU"),
                ("Network", "Show network status"),
            ]
            
            for text, command in quick_commands:
                btn = ctk.CTkButton(
                    actions_frame,
                    text=text,
                    width=80,
                    height=28,
                    font=ctk.CTkFont(size=11),
                    command=lambda c=command: self._quick_send(c)
                )
                btn.pack(side="left", padx=3)
        else:
            actions_frame = ttk.Frame(self.frame)
            actions_frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(actions_frame, text="Quick Actions:").pack(side="left", padx=5)
            
            quick_commands = [
                ("System Info", "Show me system information"),
                ("CPU Usage", "What's my CPU usage?"),
                ("Memory", "Show memory usage"),
                ("Disk Space", "Check disk space"),
            ]
            
            for text, command in quick_commands:
                ttk.Button(
                    actions_frame,
                    text=text,
                    command=lambda c=command: self._quick_send(c)
                ).pack(side="left", padx=3)
    
    def _on_enter(self, event):
        """Handle Enter key press."""
        if not event.state & 0x1:  # Shift not pressed
            self._send_message()
            return "break"  # Prevent default newline
        return None
    
    def _quick_send(self, message: str):
        """Send a quick action message."""
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", message)
        self._send_message()
    
    def _send_message(self):
        """Send the current message."""
        if USE_CUSTOMTKINTER:
            message = self.input_text.get("1.0", "end").strip()
        else:
            message = self.input_text.get("1.0", "end").strip()
        
        if not message or self.is_processing:
            return
        
        # Clear input
        self.input_text.delete("1.0", "end")
        
        # Add user message to chat
        self._add_user_message(message)
        
        # Set processing state
        self._set_processing(True)
        
        # Call the send callback if provided
        if self.on_send:
            # Run in background thread
            thread = threading.Thread(target=self._process_message, args=(message,))
            thread.daemon = True
            thread.start()
        else:
            # No callback - just echo
            self._add_assistant_message("No agent connected. Message received: " + message)
            self._set_processing(False)
    
    def _process_message(self, message: str):
        """Process message in background thread."""
        try:
            # Call the callback
            if self.on_send:
                self.on_send(message)
        except Exception as e:
            self.add_message(f"Error: {str(e)}", is_user=False)
        finally:
            # Reset processing state (done in main thread)
            self.parent.after(0, lambda: self._set_processing(False))
    
    def _set_processing(self, processing: bool):
        """Set processing state."""
        self.is_processing = processing
        
        if USE_CUSTOMTKINTER:
            if processing:
                self.status_label.configure(text="● Processing...", text_color="orange")
                self.send_btn.configure(state="disabled")
            else:
                self.status_label.configure(text="● Ready", text_color="green")
                self.send_btn.configure(state="normal")
        else:
            if processing:
                self.status_label.configure(text="● Processing...", foreground="orange")
                self.send_btn.configure(state="disabled")
            else:
                self.status_label.configure(text="● Ready", foreground="green")
                self.send_btn.configure(state="normal")
    
    def _add_user_message(self, content: str):
        """Add a user message to the chat."""
        self._add_message_bubble(content, is_user=True)
    
    def _add_assistant_message(self, content: str):
        """Add an assistant message to the chat."""
        self._add_message_bubble(content, is_user=False)
    
    def _add_system_message(self, content: str):
        """Add a system message to the chat."""
        if USE_CUSTOMTKINTER:
            msg_frame = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
            msg_frame.pack(fill="x", padx=10, pady=5)
            
            msg_label = ctk.CTkLabel(
                msg_frame,
                text=content,
                font=ctk.CTkFont(size=12),
                text_color="gray",
                wraplength=500,
                justify="left"
            )
            msg_label.pack(anchor="center")
        else:
            msg_frame = ttk.Frame(self.messages_frame)
            msg_frame.pack(fill="x", padx=10, pady=5)
            
            msg_label = ttk.Label(
                msg_frame,
                text=content,
                foreground="gray",
                wraplength=500,
                justify="left"
            )
            msg_label.pack(anchor="center")
    
    def _add_message_bubble(self, content: str, is_user: bool):
        """Add a message bubble to the chat."""
        # Check if messages_frame still exists
        try:
            if not self.messages_frame or not self.messages_frame.winfo_exists():
                return
        except Exception:
            return
        
        timestamp = datetime.now().strftime("%H:%M")
        
        if USE_CUSTOMTKINTER:
            # Message container
            container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
            container.pack(fill="x", padx=10, pady=5)
            
            # Configure alignment
            if is_user:
                anchor = "e"
                bg_color = "#1f538d"  # Blue for user
                text_color = "white"
            else:
                anchor = "w"
                bg_color = "#2b2b2b"  # Dark gray for assistant
                text_color = "white"
            
            # Message bubble
            bubble = ctk.CTkFrame(container, fg_color=bg_color, corner_radius=15)
            bubble.pack(anchor=anchor, padx=5)
            
            # Sender label
            sender = "You" if is_user else "🧠 SysAgent"
            sender_label = ctk.CTkLabel(
                bubble,
                text=sender,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=text_color
            )
            sender_label.pack(anchor="w", padx=10, pady=(8, 2))
            
            # Message content
            msg_label = ctk.CTkLabel(
                bubble,
                text=content,
                font=ctk.CTkFont(size=12),
                text_color=text_color,
                wraplength=400,
                justify="left"
            )
            msg_label.pack(anchor="w", padx=10, pady=2)
            
            # Timestamp
            time_label = ctk.CTkLabel(
                bubble,
                text=timestamp,
                font=ctk.CTkFont(size=9),
                text_color="gray"
            )
            time_label.pack(anchor="e", padx=10, pady=(2, 8))
        else:
            # Message container
            container = ttk.Frame(self.messages_frame)
            container.pack(fill="x", padx=10, pady=5)
            
            # Configure alignment
            if is_user:
                anchor = "e"
                bg = "#e3f2fd"  # Light blue for user
            else:
                anchor = "w"
                bg = "#f5f5f5"  # Light gray for assistant
            
            # Message frame (simulated bubble)
            bubble = tk.Frame(container, bg=bg, padx=10, pady=8)
            bubble.pack(anchor=anchor)
            
            # Sender
            sender = "You" if is_user else "🧠 SysAgent"
            tk.Label(bubble, text=sender, font=("", 9, "bold"), bg=bg).pack(anchor="w")
            
            # Content
            tk.Label(
                bubble,
                text=content,
                wraplength=400,
                justify="left",
                bg=bg
            ).pack(anchor="w", pady=2)
            
            # Timestamp
            tk.Label(bubble, text=timestamp, font=("", 8), fg="gray", bg=bg).pack(anchor="e")
        
        # Scroll to bottom
        self._scroll_to_bottom()
    
    def _scroll_to_bottom(self):
        """Scroll messages to bottom."""
        try:
            if USE_CUSTOMTKINTER:
                if hasattr(self.messages_frame, '_parent_canvas') and self.messages_frame._parent_canvas.winfo_exists():
                    self.messages_frame._parent_canvas.yview_moveto(1.0)
            else:
                if hasattr(self, '_canvas') and self._canvas.winfo_exists():
                    self._canvas.yview_moveto(1.0)
        except Exception:
            pass  # Widget may have been destroyed
    
    def add_message(self, content: str, is_user: bool = False):
        """Add a message to the chat (thread-safe)."""
        self.message_queue.put((content, is_user))
    
    def _start_message_processor(self):
        """Start background message processor."""
        def process_queue():
            try:
                while True:
                    content, is_user = self.message_queue.get_nowait()
                    if is_user:
                        self._add_user_message(content)
                    else:
                        self._add_assistant_message(content)
            except queue.Empty:
                pass
            finally:
                self.parent.after(100, process_queue)
        
        self.parent.after(100, process_queue)
    
    def clear_chat(self):
        """Clear all messages from chat."""
        try:
            # Check if the frame still exists
            if self.messages_frame and self.messages_frame.winfo_exists():
                for widget in self.messages_frame.winfo_children():
                    widget.destroy()
                
                self._add_system_message("Chat cleared. How can I help you?")
        except Exception:
            # Frame was destroyed, nothing to clear
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
        self.root.geometry("700x800")
        self.root.minsize(500, 600)
        
        return self.root
    
    def _on_message(self, message: str):
        """Handle incoming user message."""
        if self.agent:
            try:
                result = self.agent.process_command(message)
                
                if result.get('success'):
                    response = result.get('message', 'Command executed successfully.')
                    
                    # Add tool info if available
                    if result.get('data', {}).get('tools_used'):
                        tools = result['data']['tools_used']
                        response += f"\n\n[Tools used: {', '.join(tools)}]"
                else:
                    response = f"Error: {result.get('message', 'Unknown error')}"
                    if result.get('error'):
                        response += f"\n{result['error']}"
                
                self.chat.add_message(response, is_user=False)
                
            except Exception as e:
                self.chat.add_message(f"Error processing command: {str(e)}", is_user=False)
        else:
            self.chat.add_message(
                "Agent not available. Please check your configuration and API keys.",
                is_user=False
            )
    
    def run(self):
        """Run the chat window."""
        self._create_window()
        
        # Create chat interface
        self.chat = ChatInterface(self.root, on_send=self._on_message)
        
        self.root.mainloop()


def launch_chat():
    """Launch the chat window."""
    window = ChatWindow()
    window.run()


if __name__ == "__main__":
    launch_chat()
