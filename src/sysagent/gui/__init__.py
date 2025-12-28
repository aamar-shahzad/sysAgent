"""
GUI module for SysAgent CLI.
Provides graphical interface for settings, OS control, and chat.
"""

# Lazy imports to handle missing tkinter gracefully
__all__ = [
    "SettingsWindow",
    "DashboardWindow", 
    "MainWindow",
    "ChatWindow",
    "ChatInterface",
    "launch_gui",
    "launch_settings",
    "launch_dashboard",
    "launch_chat",
    "launch_activity_dashboard",
    "OnboardingWizard",
    "show_onboarding",
    "SystemTray",
    "run_tray_mode",
]


def _check_gui_available():
    """Check if GUI is available (tkinter installed)."""
    try:
        import tkinter
        return True
    except ImportError:
        return False


def SettingsWindow():
    """Get SettingsWindow class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .settings import SettingsWindow as SW
    return SW()


def DashboardWindow():
    """Get DashboardWindow class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .dashboard import DashboardWindow as DW
    return DW()


def MainWindow():
    """Get MainWindow class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .main_window import MainWindow as MW
    return MW()


def ChatWindow():
    """Get ChatWindow class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .chat import ChatWindow as CW
    return CW()


def ChatInterface(parent, on_send=None):
    """Get ChatInterface class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .chat import ChatInterface as CI
    return CI(parent, on_send)


def launch_gui():
    """Launch the main GUI application."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .main_window import MainWindow
    app = MainWindow()
    app.run()


def launch_settings():
    """Launch the settings GUI only."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .settings import SettingsWindow
    app = SettingsWindow()
    app.run()


def launch_dashboard():
    """Launch the dashboard GUI only."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .dashboard import DashboardWindow
    app = DashboardWindow()
    app.run()


def launch_chat():
    """Launch the chat GUI only."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .chat import ChatWindow
    app = ChatWindow()
    app.run()


def launch_activity_dashboard():
    """Launch the activity dashboard."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available. Install with: apt-get install python3-tk (Linux) or ensure Python was installed with Tcl/Tk support.")
    from .activity_dashboard import show_activity_dashboard
    show_activity_dashboard()


def OnboardingWizard(on_complete=None):
    """Get OnboardingWizard class."""
    from .onboarding import OnboardingWizard as OW
    return OW(on_complete)


def show_onboarding(on_complete=None):
    """Show onboarding if needed."""
    from .onboarding import show_onboarding as so
    return so(on_complete)


def SystemTray(on_show=None, on_quit=None, on_quick_action=None):
    """Get SystemTray class."""
    from .system_tray import SystemTray as ST
    return ST(on_show, on_quit, on_quick_action)


def run_tray_mode():
    """Run SysAgent in tray mode."""
    from .system_tray import run_tray_mode as rtm
    rtm()
