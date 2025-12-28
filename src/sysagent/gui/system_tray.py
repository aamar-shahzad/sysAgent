"""
System Tray for SysAgent - Background mode with tray icon and global hotkeys.
Run SysAgent in the background with quick access.
"""

import os
import sys
import threading
from typing import Optional, Callable
from pathlib import Path

# Platform detection
PLATFORM = sys.platform

# Check for tray dependencies
TRAY_AVAILABLE = False
try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    pystray = None
    Image = None


class SystemTray:
    """
    System tray integration for SysAgent.
    
    Features:
    - Tray icon with menu
    - Global hotkeys (platform-dependent)
    - Quick actions from tray
    - Show/hide main window
    """
    
    def __init__(self, 
                 on_show: Optional[Callable] = None,
                 on_quit: Optional[Callable] = None,
                 on_quick_action: Optional[Callable[[str], None]] = None):
        self.on_show = on_show
        self.on_quit = on_quit
        self.on_quick_action = on_quick_action
        self.tray_icon = None
        self.running = False
    
    def _get_icon(self):
        """Get the tray icon image."""
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple icon
            size = 64
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw a brain-like shape (circle with some details)
            draw.ellipse([4, 4, size-4, size-4], fill=(59, 130, 246, 255))
            draw.ellipse([20, 18, 28, 26], fill=(255, 255, 255, 255))
            draw.ellipse([36, 18, 44, 26], fill=(255, 255, 255, 255))
            draw.arc([18, 32, 46, 48], 0, 180, fill=(255, 255, 255, 255), width=3)
            
            return img
        except ImportError:
            return None
    
    def start(self):
        """Start the system tray."""
        try:
            import pystray
            from PIL import Image
        except ImportError:
            print("System tray requires 'pystray' and 'Pillow'. Install with: pip install pystray Pillow")
            return False
        
        icon_image = self._get_icon()
        if not icon_image:
            print("Could not create tray icon")
            return False
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Show SysAgent", self._on_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quick Actions", pystray.Menu(
                pystray.MenuItem("System Status", lambda: self._quick_action("Show system status")),
                pystray.MenuItem("Health Check", lambda: self._quick_action("Run health check")),
                pystray.MenuItem("List Processes", lambda: self._quick_action("Show running processes")),
                pystray.MenuItem("Disk Usage", lambda: self._quick_action("Check disk space")),
            )),
            pystray.MenuItem("Tools", pystray.Menu(
                pystray.MenuItem("Terminal", lambda: self._quick_action("Open terminal")),
                pystray.MenuItem("Browser", lambda: self._quick_action("Open browser")),
                pystray.MenuItem("File Manager", lambda: self._quick_action("Open file manager")),
            )),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self._on_settings),
            pystray.MenuItem("About", self._on_about),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )
        
        self.tray_icon = pystray.Icon(
            "SysAgent",
            icon_image,
            "SysAgent - AI System Assistant",
            menu
        )
        
        self.running = True
        
        # Run in background thread
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()
        
        # Start global hotkey listener
        self._start_hotkey_listener()
        
        return True
    
    def stop(self):
        """Stop the system tray."""
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
    
    def _on_show(self):
        """Handle show action."""
        if self.on_show:
            self.on_show()
    
    def _on_quit(self):
        """Handle quit action."""
        self.stop()
        if self.on_quit:
            self.on_quit()
    
    def _on_settings(self):
        """Handle settings action."""
        self._quick_action("Open settings")
    
    def _on_about(self):
        """Handle about action."""
        try:
            if PLATFORM == "darwin":
                os.system('osascript -e \'display dialog "SysAgent v1.0.0\nAI-Powered System Assistant\n\nhttps://github.com/sysagent" buttons {"OK"} default button "OK" with title "About SysAgent"\'')
            elif PLATFORM == "win32":
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, "SysAgent v1.0.0\nAI-Powered System Assistant", "About SysAgent", 0)
            else:
                os.system('notify-send "SysAgent" "v1.0.0 - AI-Powered System Assistant"')
        except Exception:
            pass
    
    def _quick_action(self, action: str):
        """Execute a quick action."""
        if self.on_quick_action:
            self.on_quick_action(action)
    
    def _start_hotkey_listener(self):
        """Start listening for global hotkeys."""
        try:
            if PLATFORM == "darwin":
                self._start_macos_hotkeys()
            elif PLATFORM == "win32":
                self._start_windows_hotkeys()
            else:
                self._start_linux_hotkeys()
        except Exception as e:
            print(f"Could not start global hotkeys: {e}")
    
    def _start_macos_hotkeys(self):
        """Start macOS global hotkey listener."""
        try:
            from pynput import keyboard
            
            COMBO = {keyboard.Key.cmd, keyboard.Key.shift}
            current = set()
            
            def on_press(key):
                if key in COMBO:
                    current.add(key)
                elif hasattr(key, 'char') and key.char == 's' and current == COMBO:
                    self._on_show()
            
            def on_release(key):
                if key in COMBO:
                    current.discard(key)
            
            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
        except ImportError:
            pass  # pynput not available
    
    def _start_windows_hotkeys(self):
        """Start Windows global hotkey listener."""
        try:
            import ctypes
            from ctypes import wintypes
            import threading
            
            user32 = ctypes.windll.user32
            
            # Ctrl+Shift+S
            MOD_CONTROL = 0x0002
            MOD_SHIFT = 0x0004
            VK_S = 0x53
            
            def hotkey_thread():
                user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_SHIFT, VK_S)
                
                msg = wintypes.MSG()
                while self.running:
                    if user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                        if msg.message == 0x0312:  # WM_HOTKEY
                            self._on_show()
            
            thread = threading.Thread(target=hotkey_thread, daemon=True)
            thread.start()
        except Exception:
            pass
    
    def _start_linux_hotkeys(self):
        """Start Linux global hotkey listener."""
        try:
            from pynput import keyboard
            
            COMBO = {keyboard.Key.ctrl, keyboard.Key.shift}
            current = set()
            
            def on_press(key):
                if key in COMBO:
                    current.add(key)
                elif hasattr(key, 'char') and key.char == 's' and current == COMBO:
                    self._on_show()
            
            def on_release(key):
                if key in COMBO:
                    current.discard(key)
            
            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
        except ImportError:
            pass
    
    def update_icon(self, status: str = "normal"):
        """Update tray icon based on status."""
        if not self.tray_icon:
            return
        
        try:
            from PIL import Image, ImageDraw
            
            size = 64
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Different colors for different states
            colors = {
                "normal": (59, 130, 246, 255),   # Blue
                "working": (245, 158, 11, 255),  # Orange
                "error": (239, 68, 68, 255),     # Red
                "success": (16, 185, 129, 255),  # Green
            }
            color = colors.get(status, colors["normal"])
            
            draw.ellipse([4, 4, size-4, size-4], fill=color)
            draw.ellipse([20, 18, 28, 26], fill=(255, 255, 255, 255))
            draw.ellipse([36, 18, 44, 26], fill=(255, 255, 255, 255))
            draw.arc([18, 32, 46, 48], 0, 180, fill=(255, 255, 255, 255), width=3)
            
            self.tray_icon.icon = img
        except Exception:
            pass
    
    def show_notification(self, title: str, message: str):
        """Show a system notification."""
        if self.tray_icon:
            try:
                self.tray_icon.notify(message, title)
            except Exception:
                # Fallback to system notifications
                self._system_notify(title, message)
        else:
            self._system_notify(title, message)
    
    def _system_notify(self, title: str, message: str):
        """Show system notification using platform tools."""
        try:
            if PLATFORM == "darwin":
                os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
            elif PLATFORM == "win32":
                # Use Windows toast notification
                pass
            else:
                os.system(f'notify-send "{title}" "{message}"')
        except Exception:
            pass


class TrayApplication:
    """
    Complete tray-based application.
    
    Runs SysAgent in the background with:
    - System tray icon
    - Global hotkeys
    - Popup chat window
    """
    
    def __init__(self):
        self.tray = None
        self.main_window = None
        self.running = False
    
    def start(self):
        """Start the tray application."""
        self.tray = SystemTray(
            on_show=self._show_window,
            on_quit=self._quit,
            on_quick_action=self._handle_quick_action
        )
        
        if self.tray.start():
            self.running = True
            print("🧠 SysAgent running in system tray")
            print("   Press Ctrl+Shift+S (Cmd+Shift+S on Mac) to show")
            print("   Right-click tray icon for menu")
            
            # Keep running
            try:
                while self.running:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                self._quit()
    
    def _show_window(self):
        """Show the main window."""
        try:
            # Import and create window
            from .main_window import MainWindow
            
            if not self.main_window:
                import threading
                def run_window():
                    self.main_window = MainWindow()
                    self.main_window.run()
                    self.main_window = None
                
                thread = threading.Thread(target=run_window, daemon=True)
                thread.start()
            else:
                # Focus existing window
                try:
                    self.main_window.window.deiconify()
                    self.main_window.window.focus_force()
                except Exception:
                    pass
        except Exception as e:
            print(f"Could not show window: {e}")
    
    def _quit(self):
        """Quit the application."""
        self.running = False
        if self.tray:
            self.tray.stop()
        if self.main_window:
            try:
                self.main_window.window.destroy()
            except Exception:
                pass
        sys.exit(0)
    
    def _handle_quick_action(self, action: str):
        """Handle quick action from tray."""
        # Show window and send action
        self._show_window()
        
        # Wait for window to be ready, then send action
        import time
        time.sleep(0.5)
        
        if self.main_window and hasattr(self.main_window, 'chat_interface'):
            try:
                self.main_window.chat_interface._send_message_direct(action)
            except Exception:
                pass


def run_tray_mode():
    """Run SysAgent in tray mode (CLI entry point)."""
    app = TrayApplication()
    app.start()


if __name__ == "__main__":
    run_tray_mode()
