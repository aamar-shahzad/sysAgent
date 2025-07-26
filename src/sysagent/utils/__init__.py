"""
Utility functions for SysAgent CLI.
"""

from .platform import (
    detect_platform,
    get_platform_info,
    get_home_directory,
    get_temp_directory,
    get_desktop_directory,
    get_downloads_directory,
    get_documents_directory,
    is_admin,
    can_elevate_privileges,
    get_system_paths,
    get_environment_variables,
)

__all__ = [
    "detect_platform",
    "get_platform_info",
    "get_home_directory",
    "get_temp_directory", 
    "get_desktop_directory",
    "get_downloads_directory",
    "get_documents_directory",
    "is_admin",
    "can_elevate_privileges",
    "get_system_paths",
    "get_environment_variables",
] 