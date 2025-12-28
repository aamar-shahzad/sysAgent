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
            "system_info": True,  # Added for system_info_tool
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
        # If user_input is provided and is positive, grant it
        if user_input and user_input.lower() in ['y', 'yes', 'grant', 'allow']:
            self.permissions[permission] = True
            self._save_permissions()
            return True
        
        # If no user_input provided, auto-grant the permission
        # This allows programmatic permission granting
        if user_input is None:
            self.permissions[permission] = True
            self._save_permissions()
            return True
        
        # If user_input was provided but was negative, don't grant
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

    def get_granted_permissions(self) -> List[str]:
        """Get list of granted permissions."""
        return [perm for perm, granted in self.permissions.items() if granted]

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

    def get_required_permissions(self, tool_name: str) -> List["PermissionRequest"]:
        """Get required permissions for a tool as PermissionRequest objects."""
        from ..types import PermissionRequest, PermissionLevel
        
        permission_map = {
            'file_tool': [('file_access', 'Access to file system operations')],
            'system_info_tool': [('system_info', 'Access to system information')],
            'process_tool': [('process_management', 'Access to process management')],
            'network_tool': [('network_access', 'Access to network operations')],
            'system_control_tool': [('system_control', 'Access to system control functions')],
            'security_tool': [('security_operations', 'Access to security operations')],
            'automation_tool': [('automation_operations', 'Access to automation features')],
            'monitoring_tool': [('monitoring_operations', 'Access to monitoring features')],
            'low_level_os_tool': [('low_level_os', 'Access to low-level OS functions')],
            'os_intelligence_tool': [('low_level_os', 'Access to OS intelligence features')],
            'code_generation_tool': [('code_execution', 'Access to code execution')]
        }
        
        permissions = permission_map.get(tool_name, [])
        result = []
        
        for perm_name, description in permissions:
            result.append(PermissionRequest(
                permission=perm_name,
                level=PermissionLevel.READ,
                description=description,
                required=True,
                granted=self.has_permission(perm_name)
            ))
        
        return result

    def check_tool_permissions(self, tool_name: str) -> bool:
        """Check if user has permissions for a specific tool."""
        required_permissions = self.get_required_permissions(tool_name)
        
        for perm_request in required_permissions:
            permission = perm_request.permission if hasattr(perm_request, 'permission') else perm_request
            if not self.has_permission(permission):
                # Try to auto-grant for common tools
                if permission in ['file_access', 'monitoring_operations', 'system_info']:
                    self.grant_permission(permission)
                else:
                    return self.request_permission(permission, f"using {tool_name}")
        
        return True

    def check_system_permissions(self) -> Dict[str, bool]:
        """Check system-level permissions and capabilities."""
        from ..utils.platform import is_admin, can_elevate_privileges, detect_platform
        
        return {
            "is_admin": is_admin(),
            "can_elevate": can_elevate_privileges(),
            "platform": detect_platform().value,
            "file_access": self.has_permission("file_access"),
            "system_info": self.has_permission("system_info"),
            "network_access": self.has_permission("network_access"),
            "process_management": self.has_permission("process_management"),
        }

    def clear_permissions(self) -> None:
        """Clear all permissions (revoke all)."""
        for permission in self.permissions:
            self.permissions[permission] = False
        self._save_permissions() 