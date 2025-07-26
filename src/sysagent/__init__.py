"""
SysAgent CLI - Secure, intelligent command-line assistant for OS automation and control.
"""

__version__ = "0.1.0"
__author__ = "SysAgent Team"
__email__ = "team@sysagent.dev"

from .core.agent import SysAgent
from .core.config import Config
from .core.permissions import PermissionManager

__all__ = [
    "SysAgent",
    "Config", 
    "PermissionManager",
    "__version__",
] 