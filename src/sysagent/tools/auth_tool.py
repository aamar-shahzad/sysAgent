"""
Authentication and credential management tool for SysAgent CLI.
"""

import os
import json
import base64
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class AuthTool(BaseTool):
    """Tool for secure credential management."""
    
    def __init__(self):
        """Initialize auth tool."""
        super().__init__()
        self._credentials_file = Path.home() / ".sysagent" / "credentials.enc"
        self._credentials_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="auth_tool",
            description="Secure credential storage, retrieval, and management",
            category=ToolCategory.SECURITY,
            permissions=["credentials", "keychain"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Execute auth action."""
        try:
            if action == "store":
                return self._store_credential(**kwargs)
            elif action == "get":
                return self._get_credential(**kwargs)
            elif action == "delete":
                return self._delete_credential(**kwargs)
            elif action == "list":
                return self._list_credentials(**kwargs)
            elif action == "verify":
                return self._verify_credential(**kwargs)
            elif action == "export":
                return self._export_credentials(**kwargs)
            elif action == "import":
                return self._import_credentials(**kwargs)
            elif action == "rotate":
                return self._rotate_credential(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown action: {action}",
                    error=f"Unsupported action: {action}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Auth operation failed: {str(e)}",
                error=str(e)
            )

    def _get_encryption_key(self) -> bytes:
        """Get or create encryption key for credentials."""
        key_file = Path.home() / ".sysagent" / ".key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate a key from machine-specific data
            import uuid
            machine_id = str(uuid.getnode())
            key = hashlib.sha256(machine_id.encode()).digest()
            
            # Save the key
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            
            return key

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data using cryptography library or fallback."""
        try:
            from cryptography.fernet import Fernet
            
            key = base64.urlsafe_b64encode(self._get_encryption_key())
            fernet = Fernet(key)
            encrypted = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
            
        except ImportError:
            # Simple XOR fallback (not as secure but functional)
            key = self._get_encryption_key()
            data_bytes = data.encode()
            encrypted = bytes([data_bytes[i] ^ key[i % len(key)] for i in range(len(data_bytes))])
            return base64.b64encode(encrypted).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data."""
        try:
            from cryptography.fernet import Fernet
            
            key = base64.urlsafe_b64encode(self._get_encryption_key())
            fernet = Fernet(key)
            decrypted = fernet.decrypt(base64.b64decode(encrypted_data))
            return decrypted.decode()
            
        except ImportError:
            # Simple XOR fallback
            key = self._get_encryption_key()
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted = bytes([encrypted_bytes[i] ^ key[i % len(key)] for i in range(len(encrypted_bytes))])
            return decrypted.decode()

    def _load_credentials(self) -> Dict[str, Any]:
        """Load credentials from file."""
        if not self._credentials_file.exists():
            return {}
        
        try:
            with open(self._credentials_file, 'r') as f:
                encrypted = f.read()
            
            if not encrypted:
                return {}
            
            decrypted = self._decrypt_data(encrypted)
            return json.loads(decrypted)
            
        except Exception:
            return {}

    def _save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save credentials to file."""
        try:
            data = json.dumps(credentials)
            encrypted = self._encrypt_data(data)
            
            with open(self._credentials_file, 'w') as f:
                f.write(encrypted)
            
            os.chmod(self._credentials_file, 0o600)
            return True
            
        except Exception:
            return False

    def _store_credential(self, **kwargs) -> ToolResult:
        """Store a credential securely."""
        service = kwargs.get("service") or kwargs.get("name")
        username = kwargs.get("username") or kwargs.get("user")
        password = kwargs.get("password") or kwargs.get("secret")
        extra = kwargs.get("extra", {})
        
        if not service:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing service"
            )
        
        if not password:
            return ToolResult(
                success=False,
                data={},
                message="No password/secret provided",
                error="Missing password"
            )
        
        try:
            # Try to use system keychain first
            current_platform = detect_platform()
            use_keychain = False
            
            try:
                import keyring
                keyring.set_password(service, username or "default", password)
                use_keychain = True
            except ImportError:
                pass
            except Exception:
                pass
            
            # Also store in our encrypted file for backup/fallback
            credentials = self._load_credentials()
            credentials[service] = {
                "username": username,
                "password": password,
                "extra": extra,
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "in_keychain": use_keychain
            }
            
            if self._save_credentials(credentials):
                return ToolResult(
                    success=True,
                    data={
                        "service": service,
                        "username": username,
                        "in_keychain": use_keychain
                    },
                    message=f"Stored credential for {service}" + 
                            (" (also in system keychain)" if use_keychain else "")
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Failed to save credential",
                    error="Save failed"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to store credential: {str(e)}",
                error=str(e)
            )

    def _get_credential(self, **kwargs) -> ToolResult:
        """Retrieve a credential."""
        service = kwargs.get("service") or kwargs.get("name")
        username = kwargs.get("username")
        
        if not service:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing service"
            )
        
        try:
            password = None
            source = "file"
            
            # Try system keychain first
            try:
                import keyring
                password = keyring.get_password(service, username or "default")
                if password:
                    source = "keychain"
            except ImportError:
                pass
            except Exception:
                pass
            
            # Fallback to our file
            if not password:
                credentials = self._load_credentials()
                if service in credentials:
                    cred = credentials[service]
                    password = cred.get("password")
                    username = username or cred.get("username")
            
            if password:
                return ToolResult(
                    success=True,
                    data={
                        "service": service,
                        "username": username,
                        "password": password,
                        "source": source
                    },
                    message=f"Retrieved credential for {service}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"No credential found for {service}",
                    error="Not found"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to get credential: {str(e)}",
                error=str(e)
            )

    def _delete_credential(self, **kwargs) -> ToolResult:
        """Delete a credential."""
        service = kwargs.get("service") or kwargs.get("name")
        username = kwargs.get("username")
        
        if not service:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing service"
            )
        
        try:
            deleted_keychain = False
            deleted_file = False
            
            # Try to delete from system keychain
            try:
                import keyring
                keyring.delete_password(service, username or "default")
                deleted_keychain = True
            except ImportError:
                pass
            except Exception:
                pass
            
            # Delete from our file
            credentials = self._load_credentials()
            if service in credentials:
                del credentials[service]
                self._save_credentials(credentials)
                deleted_file = True
            
            if deleted_keychain or deleted_file:
                return ToolResult(
                    success=True,
                    data={"service": service, "deleted_keychain": deleted_keychain, "deleted_file": deleted_file},
                    message=f"Deleted credential for {service}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"No credential found for {service}",
                    error="Not found"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to delete credential: {str(e)}",
                error=str(e)
            )

    def _list_credentials(self, **kwargs) -> ToolResult:
        """List all stored credentials (names only, not secrets)."""
        try:
            credentials = self._load_credentials()
            
            cred_list = []
            for service, cred in credentials.items():
                cred_list.append({
                    "service": service,
                    "username": cred.get("username"),
                    "created": cred.get("created"),
                    "modified": cred.get("modified"),
                    "in_keychain": cred.get("in_keychain", False)
                })
            
            return ToolResult(
                success=True,
                data={"credentials": cred_list, "count": len(cred_list)},
                message=f"Found {len(cred_list)} stored credentials"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list credentials: {str(e)}",
                error=str(e)
            )

    def _verify_credential(self, **kwargs) -> ToolResult:
        """Verify a credential exists and is valid."""
        service = kwargs.get("service") or kwargs.get("name")
        
        if not service:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing service"
            )
        
        try:
            credentials = self._load_credentials()
            
            if service in credentials:
                cred = credentials[service]
                has_password = bool(cred.get("password"))
                
                return ToolResult(
                    success=True,
                    data={
                        "service": service,
                        "exists": True,
                        "has_password": has_password,
                        "username": cred.get("username"),
                        "created": cred.get("created")
                    },
                    message=f"Credential for {service} exists" + (" and is valid" if has_password else " but has no password")
                )
            else:
                return ToolResult(
                    success=True,
                    data={"service": service, "exists": False},
                    message=f"No credential found for {service}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to verify credential: {str(e)}",
                error=str(e)
            )

    def _export_credentials(self, **kwargs) -> ToolResult:
        """Export credentials to an encrypted backup file."""
        output_file = kwargs.get("output") or kwargs.get("path")
        password = kwargs.get("password")
        
        if not output_file:
            return ToolResult(
                success=False,
                data={},
                message="No output file specified",
                error="Missing output"
            )
        
        if not password:
            return ToolResult(
                success=False,
                data={},
                message="Password required for export encryption",
                error="Missing password"
            )
        
        try:
            credentials = self._load_credentials()
            
            # Create a password-derived key
            key = hashlib.sha256(password.encode()).digest()
            data = json.dumps(credentials)
            
            # Simple encryption with provided password
            data_bytes = data.encode()
            encrypted = bytes([data_bytes[i] ^ key[i % len(key)] for i in range(len(data_bytes))])
            
            with open(output_file, 'wb') as f:
                f.write(base64.b64encode(encrypted))
            
            return ToolResult(
                success=True,
                data={"path": output_file, "count": len(credentials)},
                message=f"Exported {len(credentials)} credentials to {output_file}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Export failed: {str(e)}",
                error=str(e)
            )

    def _import_credentials(self, **kwargs) -> ToolResult:
        """Import credentials from an encrypted backup file."""
        input_file = kwargs.get("input") or kwargs.get("path")
        password = kwargs.get("password")
        merge = kwargs.get("merge", True)
        
        if not input_file:
            return ToolResult(
                success=False,
                data={},
                message="No input file specified",
                error="Missing input"
            )
        
        if not password:
            return ToolResult(
                success=False,
                data={},
                message="Password required for decryption",
                error="Missing password"
            )
        
        if not os.path.exists(input_file):
            return ToolResult(
                success=False,
                data={},
                message=f"File not found: {input_file}",
                error="File not found"
            )
        
        try:
            with open(input_file, 'rb') as f:
                encrypted = base64.b64decode(f.read())
            
            # Decrypt with provided password
            key = hashlib.sha256(password.encode()).digest()
            decrypted = bytes([encrypted[i] ^ key[i % len(key)] for i in range(len(encrypted))])
            
            imported_creds = json.loads(decrypted.decode())
            
            if merge:
                existing = self._load_credentials()
                existing.update(imported_creds)
                self._save_credentials(existing)
            else:
                self._save_credentials(imported_creds)
            
            return ToolResult(
                success=True,
                data={"count": len(imported_creds)},
                message=f"Imported {len(imported_creds)} credentials"
            )
            
        except json.JSONDecodeError:
            return ToolResult(
                success=False,
                data={},
                message="Invalid password or corrupted file",
                error="Decryption failed"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Import failed: {str(e)}",
                error=str(e)
            )

    def _rotate_credential(self, **kwargs) -> ToolResult:
        """Rotate (update) a credential with a new password."""
        service = kwargs.get("service") or kwargs.get("name")
        new_password = kwargs.get("new_password") or kwargs.get("password")
        
        if not service:
            return ToolResult(
                success=False,
                data={},
                message="No service name provided",
                error="Missing service"
            )
        
        if not new_password:
            return ToolResult(
                success=False,
                data={},
                message="No new password provided",
                error="Missing password"
            )
        
        try:
            credentials = self._load_credentials()
            
            if service not in credentials:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"No credential found for {service}",
                    error="Not found"
                )
            
            old_cred = credentials[service]
            old_cred["password"] = new_password
            old_cred["modified"] = datetime.now().isoformat()
            
            # Update keychain if it was there
            if old_cred.get("in_keychain"):
                try:
                    import keyring
                    keyring.set_password(service, old_cred.get("username") or "default", new_password)
                except Exception:
                    pass
            
            self._save_credentials(credentials)
            
            return ToolResult(
                success=True,
                data={"service": service, "rotated": True},
                message=f"Rotated credential for {service}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Rotation failed: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        """Get usage examples for this tool."""
        return [
            "Store credential: auth_tool --action store --service 'github' --username 'user' --password 'token'",
            "Get credential: auth_tool --action get --service 'github'",
            "List credentials: auth_tool --action list",
            "Delete credential: auth_tool --action delete --service 'github'",
            "Verify credential: auth_tool --action verify --service 'github'",
            "Export credentials: auth_tool --action export --output backup.enc --password 'backuppass'",
            "Rotate credential: auth_tool --action rotate --service 'github' --new_password 'newtoken'",
        ]
