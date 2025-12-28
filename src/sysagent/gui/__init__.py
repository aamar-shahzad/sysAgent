"""
GUI module for SysAgent CLI.
Provides graphical interface for settings and OS control.
"""

# Lazy imports to handle missing tkinter gracefully
__all__ = [
    "SettingsWindow",
    "DashboardWindow", 
    "MainWindow",
    "launch_gui",
    "launch_settings",
    "launch_dashboard",
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
