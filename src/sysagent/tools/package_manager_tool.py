"""
Package Manager tool for SysAgent CLI - Software installation and management.
"""

import subprocess
from typing import List

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class PackageManagerTool(BaseTool):
    """Tool for managing software packages."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="package_manager_tool",
            description="Install, update, and manage software packages",
            category=ToolCategory.SYSTEM,
            permissions=["package_management", "sudo"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "install": self._install,
                "uninstall": self._uninstall,
                "remove": self._uninstall,
                "update": self._update,
                "upgrade": self._upgrade,
                "search": self._search,
                "list": self._list_installed,
                "info": self._package_info,
                "which_manager": self._detect_manager,
            }
            
            if action in actions:
                return actions[action](**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={"available_actions": list(actions.keys())},
                    message=f"Unknown action: {action}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Package operation failed: {str(e)}",
                error=str(e)
            )

    def _detect_package_manager(self) -> tuple:
        """Detect the available package manager."""
        platform = detect_platform()
        
        if platform == Platform.MACOS:
            # Check for brew
            result = subprocess.run(["which", "brew"], capture_output=True)
            if result.returncode == 0:
                return ("brew", "brew")
            return ("none", None)
        
        elif platform == Platform.WINDOWS:
            # Check for winget, choco, scoop
            for mgr in ["winget", "choco", "scoop"]:
                result = subprocess.run(["where", mgr], capture_output=True)
                if result.returncode == 0:
                    return (mgr, mgr)
            return ("none", None)
        
        else:  # Linux
            managers = [
                ("apt", "apt"),
                ("apt-get", "apt-get"),
                ("dnf", "dnf"),
                ("yum", "yum"),
                ("pacman", "pacman"),
                ("zypper", "zypper"),
                ("snap", "snap"),
                ("flatpak", "flatpak"),
            ]
            for name, cmd in managers:
                result = subprocess.run(["which", cmd], capture_output=True)
                if result.returncode == 0:
                    return (name, cmd)
            return ("none", None)

    def _detect_manager(self, **kwargs) -> ToolResult:
        """Detect available package manager."""
        name, cmd = self._detect_package_manager()
        
        return ToolResult(
            success=True,
            data={"manager": name, "command": cmd},
            message=f"Package manager: {name}"
        )

    def _install(self, **kwargs) -> ToolResult:
        """Install a package."""
        package = kwargs.get("package") or kwargs.get("name")
        
        if not package:
            return ToolResult(
                success=False,
                data={},
                message="No package name provided"
            )
        
        manager, cmd = self._detect_package_manager()
        
        if not cmd:
            return ToolResult(
                success=False,
                data={},
                message="No package manager found"
            )
        
        try:
            if manager == "brew":
                result = subprocess.run(
                    ["brew", "install", package],
                    capture_output=True, text=True
                )
            elif manager == "apt":
                result = subprocess.run(
                    ["sudo", "apt", "install", "-y", package],
                    capture_output=True, text=True
                )
            elif manager == "dnf":
                result = subprocess.run(
                    ["sudo", "dnf", "install", "-y", package],
                    capture_output=True, text=True
                )
            elif manager == "pacman":
                result = subprocess.run(
                    ["sudo", "pacman", "-S", "--noconfirm", package],
                    capture_output=True, text=True
                )
            elif manager == "winget":
                result = subprocess.run(
                    ["winget", "install", package],
                    capture_output=True, text=True
                )
            elif manager == "choco":
                result = subprocess.run(
                    ["choco", "install", package, "-y"],
                    capture_output=True, text=True
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unsupported package manager: {manager}"
                )
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"package": package, "manager": manager},
                    message=f"Installed {package}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={"stderr": result.stderr},
                    message=f"Failed to install {package}",
                    error=result.stderr
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Installation failed: {str(e)}",
                error=str(e)
            )

    def _uninstall(self, **kwargs) -> ToolResult:
        """Uninstall a package."""
        package = kwargs.get("package") or kwargs.get("name")
        
        if not package:
            return ToolResult(
                success=False,
                data={},
                message="No package name provided"
            )
        
        manager, cmd = self._detect_package_manager()
        
        try:
            if manager == "brew":
                result = subprocess.run(
                    ["brew", "uninstall", package],
                    capture_output=True, text=True
                )
            elif manager == "apt":
                result = subprocess.run(
                    ["sudo", "apt", "remove", "-y", package],
                    capture_output=True, text=True
                )
            elif manager == "winget":
                result = subprocess.run(
                    ["winget", "uninstall", package],
                    capture_output=True, text=True
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unsupported manager: {manager}"
                )
            
            return ToolResult(
                success=result.returncode == 0,
                data={"package": package},
                message=f"Uninstalled {package}" if result.returncode == 0 else f"Failed to uninstall"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Uninstall failed: {str(e)}",
                error=str(e)
            )

    def _update(self, **kwargs) -> ToolResult:
        """Update package lists."""
        manager, cmd = self._detect_package_manager()
        
        try:
            if manager == "brew":
                result = subprocess.run(["brew", "update"], capture_output=True, text=True)
            elif manager == "apt":
                result = subprocess.run(["sudo", "apt", "update"], capture_output=True, text=True)
            elif manager == "dnf":
                result = subprocess.run(["sudo", "dnf", "check-update"], capture_output=True, text=True)
            elif manager == "winget":
                result = subprocess.run(["winget", "source", "update"], capture_output=True, text=True)
            else:
                return ToolResult(success=False, data={}, message="Update not supported")
            
            return ToolResult(
                success=True,
                data={"manager": manager},
                message=f"Package lists updated"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Update failed: {str(e)}",
                error=str(e)
            )

    def _upgrade(self, **kwargs) -> ToolResult:
        """Upgrade all packages."""
        package = kwargs.get("package")
        manager, cmd = self._detect_package_manager()
        
        try:
            if manager == "brew":
                if package:
                    result = subprocess.run(["brew", "upgrade", package], capture_output=True, text=True)
                else:
                    result = subprocess.run(["brew", "upgrade"], capture_output=True, text=True)
            elif manager == "apt":
                result = subprocess.run(["sudo", "apt", "upgrade", "-y"], capture_output=True, text=True)
            elif manager == "winget":
                if package:
                    result = subprocess.run(["winget", "upgrade", package], capture_output=True, text=True)
                else:
                    result = subprocess.run(["winget", "upgrade", "--all"], capture_output=True, text=True)
            else:
                return ToolResult(success=False, data={}, message="Upgrade not supported")
            
            return ToolResult(
                success=True,
                data={"manager": manager, "package": package},
                message=f"Upgraded {package or 'all packages'}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Upgrade failed: {str(e)}",
                error=str(e)
            )

    def _search(self, **kwargs) -> ToolResult:
        """Search for packages."""
        query = kwargs.get("query") or kwargs.get("package") or kwargs.get("name")
        
        if not query:
            return ToolResult(
                success=False,
                data={},
                message="No search query provided"
            )
        
        manager, cmd = self._detect_package_manager()
        packages = []
        
        try:
            if manager == "brew":
                result = subprocess.run(
                    ["brew", "search", query],
                    capture_output=True, text=True
                )
                packages = result.stdout.strip().split("\n")[:20]
            elif manager == "apt":
                result = subprocess.run(
                    ["apt", "search", query],
                    capture_output=True, text=True
                )
                for line in result.stdout.split("\n")[:20]:
                    if "/" in line:
                        packages.append(line.split("/")[0])
            elif manager == "winget":
                result = subprocess.run(
                    ["winget", "search", query],
                    capture_output=True, text=True
                )
                packages = result.stdout.strip().split("\n")[2:12]
            
            return ToolResult(
                success=True,
                data={"packages": packages, "query": query},
                message=f"Found {len(packages)} packages"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Search failed: {str(e)}",
                error=str(e)
            )

    def _list_installed(self, **kwargs) -> ToolResult:
        """List installed packages."""
        manager, cmd = self._detect_package_manager()
        packages = []
        
        try:
            if manager == "brew":
                result = subprocess.run(["brew", "list"], capture_output=True, text=True)
                packages = result.stdout.strip().split("\n")[:50]
            elif manager == "apt":
                result = subprocess.run(
                    ["dpkg", "--get-selections"],
                    capture_output=True, text=True
                )
                for line in result.stdout.split("\n")[:50]:
                    if "\tinstall" in line:
                        packages.append(line.split("\t")[0])
            elif manager == "winget":
                result = subprocess.run(["winget", "list"], capture_output=True, text=True)
                packages = result.stdout.strip().split("\n")[2:52]
            
            return ToolResult(
                success=True,
                data={"packages": packages, "count": len(packages)},
                message=f"Listed {len(packages)} packages"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"List failed: {str(e)}",
                error=str(e)
            )

    def _package_info(self, **kwargs) -> ToolResult:
        """Get information about a package."""
        package = kwargs.get("package") or kwargs.get("name")
        
        if not package:
            return ToolResult(
                success=False,
                data={},
                message="No package name provided"
            )
        
        manager, cmd = self._detect_package_manager()
        
        try:
            if manager == "brew":
                result = subprocess.run(
                    ["brew", "info", package],
                    capture_output=True, text=True
                )
            elif manager == "apt":
                result = subprocess.run(
                    ["apt", "show", package],
                    capture_output=True, text=True
                )
            elif manager == "winget":
                result = subprocess.run(
                    ["winget", "show", package],
                    capture_output=True, text=True
                )
            else:
                return ToolResult(success=False, data={}, message="Info not supported")
            
            return ToolResult(
                success=True,
                data={"info": result.stdout[:1000]},
                message=f"Info for {package}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Info failed: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Install: package_manager_tool --action install --package 'vim'",
            "Uninstall: package_manager_tool --action uninstall --package 'vim'",
            "Search: package_manager_tool --action search --query 'python'",
            "Update: package_manager_tool --action update",
            "Upgrade: package_manager_tool --action upgrade",
        ]
