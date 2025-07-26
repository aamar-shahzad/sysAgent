"""
Permission management for SysAgent CLI.
"""

import os
import platform
import subprocess
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from .config import ConfigManager


class PermissionManager:
    """Manages permissions for SysAgent operations."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.permissions_file = config.config_dir / "permissions.json"
        self.permissions = self._load_permissions()

    def _load_permissions(self) -> Dict[str, Any]:
        """Load permissions from file."""
        if self.permissions_file.exists():
            try:
                with open(self.permissions_file, "r") as f:
                    return json.load(f)
            except Exception:
                return self._get_default_permissions()
        return self._get_default_permissions()

    def _save_permissions(self):
        """Save permissions to file."""
        try:
            self.permissions_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.permissions_file, "w") as f:
                json.dump(self.permissions, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save permissions: {e}")

    def _get_default_permissions(self) -> Dict[str, Any]:
        """Get default permissions."""
        return {
            "system_admin": False,
            "file_access": True,
            "process_management": False,
            "network_access": True,
            "system_control": False,
            "security_operations": False,
            "automation_operations": False,
            "monitoring_operations": True,
            "low_level_os": False,
            "code_execution": False
        }

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return self.permissions.get(permission, False)

    def grant_permission(self, permission: str, user_input: str = None) -> bool:
        """Grant a permission with optional user confirmation."""
        if user_input and user_input.lower() in ['y', 'yes', 'grant', 'allow']:
            self.permissions[permission] = True
            self._save_permissions()
            return True
        
        # Auto-grant for safe operations
        safe_permissions = ['file_access', 'monitoring_operations']
        if permission in safe_permissions:
            self.permissions[permission] = True
            self._save_permissions()
            return True
        
        return False

    def revoke_permission(self, permission: str) -> bool:
        """Revoke a permission."""
        self.permissions[permission] = False
        self._save_permissions()
        return True

    def request_permission(self, permission: str, operation: str = None) -> bool:
        """Request permission for an operation."""
        if self.has_permission(permission):
            return True
        
        # Auto-grant for basic operations
        if permission in ['file_access', 'monitoring_operations']:
            self.grant_permission(permission)
            return True
        
        # For more sensitive operations, ask user
        operation_desc = operation or permission
        print(f"\n🔐 Permission required for: {operation_desc}")
        print("This operation requires elevated permissions.")
        
        # Try to get permission automatically for common operations
        if permission in ['process_management', 'system_info', 'low_level_os']:
            print("Attempting to grant permission automatically...")
            self.grant_permission(permission)
            return True
        
        user_input = input("Grant permission? (y/n): ").strip().lower()
        if user_input in ['y', 'yes', 'grant', 'allow']:
            self.grant_permission(permission)
            return True
        
        return False

    def get_permission_status(self) -> Dict[str, bool]:
        """Get current permission status."""
        return self.permissions.copy()

    def list_permissions(self) -> List[str]:
        """List all available permissions."""
        return list(self.permissions.keys())

    def reset_permissions(self):
        """Reset all permissions to defaults."""
        self.permissions = self._get_default_permissions()
        self._save_permissions()

    def update_permission(self, permission: str, value: bool) -> bool:
        """Update a specific permission."""
        if permission in self.permissions:
            self.permissions[permission] = value
            self._save_permissions()
            return True
        return False

    def get_required_permissions(self, tool_name: str) -> List[str]:
        """Get required permissions for a tool."""
        permission_map = {
            'file_tool': ['file_access'],
            'system_info_tool': ['system_info'],
            'process_tool': ['process_management'],
            'network_tool': ['network_access'],
            'system_control_tool': ['system_control'],
            'security_tool': ['security_operations'],
            'automation_tool': ['automation_operations'],
            'monitoring_tool': ['monitoring_operations'],
            'low_level_os_tool': ['low_level_os'],
            'code_generation_tool': ['code_execution']
        }
        return permission_map.get(tool_name, [])

    def check_tool_permissions(self, tool_name: str) -> bool:
        """Check if user has permissions for a specific tool."""
        required_permissions = self.get_required_permissions(tool_name)
        
        for permission in required_permissions:
            if not self.has_permission(permission):
                # Try to auto-grant for common tools
                if permission in ['file_access', 'monitoring_operations', 'system_info']:
                    self.grant_permission(permission)
                else:
                    return self.request_permission(permission, f"using {tool_name}")
        
        return True 