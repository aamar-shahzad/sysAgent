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
    # New components
    "FloatingWidget",
    "QuickLauncher",
    "ClipboardHistoryPanel",
    "NotificationCenter",
    "NotificationPanel",
    "ActivityTimeline",
    "TimelinePanel",
    "launch_floating_widget",
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


def FloatingWidget(on_command=None, on_expand=None):
    """Get FloatingWidget class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available.")
    from .floating_widget import FloatingWidget as FW
    return FW(on_command=on_command, on_expand=on_expand)


def QuickLauncher(on_command=None):
    """Get QuickLauncher class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available.")
    from .floating_widget import QuickLauncher as QL
    return QL(on_command=on_command)


def ClipboardHistoryPanel(parent, colors, on_paste=None):
    """Get ClipboardHistoryPanel class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available.")
    from .floating_widget import ClipboardHistoryPanel as CHP
    return CHP(parent, colors, on_paste)


def NotificationCenter():
    """Get NotificationCenter instance."""
    from .notification_center import get_notification_center
    return get_notification_center()


def NotificationPanel(parent, colors, notification_center, on_action=None):
    """Get NotificationPanel class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available.")
    from .notification_center import NotificationPanel as NP
    return NP(parent, colors, notification_center, on_action)


def ActivityTimeline():
    """Get ActivityTimeline instance."""
    from .activity_timeline import get_activity_timeline
    return get_activity_timeline()


def TimelinePanel(parent, colors, timeline, on_entry_click=None):
    """Get TimelinePanel class."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available.")
    from .activity_timeline import TimelinePanel as TP
    return TP(parent, colors, timeline, on_entry_click)


def launch_floating_widget(on_command=None, on_expand=None):
    """Launch the floating widget."""
    if not _check_gui_available():
        raise ImportError("tkinter is not available.")
    from .floating_widget import launch_floating_widget as lfw
    lfw(on_command=on_command, on_expand=on_expand)
