"""
Email tool for SysAgent CLI - Send emails.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory


@register_tool
class EmailTool(BaseTool):
    """Tool for sending emails."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="email_tool",
            description="Send emails with attachments",
            category=ToolCategory.NETWORK,
            permissions=["email_access"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "send": self._send_email,
                "compose": self._compose_email,
                "draft": self._save_draft,
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
                message=f"Email operation failed: {str(e)}",
                error=str(e)
            )

    def _get_smtp_config(self) -> dict:
        """Get SMTP configuration from environment."""
        return {
            "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.environ.get("SMTP_PORT", "587")),
            "username": os.environ.get("SMTP_USERNAME", ""),
            "password": os.environ.get("SMTP_PASSWORD", ""),
            "use_tls": os.environ.get("SMTP_TLS", "true").lower() == "true",
        }

    def _send_email(self, **kwargs) -> ToolResult:
        """Send an email."""
        to = kwargs.get("to") or kwargs.get("recipient")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body") or kwargs.get("message") or kwargs.get("content", "")
        from_email = kwargs.get("from") or kwargs.get("sender")
        cc = kwargs.get("cc", [])
        bcc = kwargs.get("bcc", [])
        attachments = kwargs.get("attachments", [])
        html = kwargs.get("html", False)
        
        if not to:
            return ToolResult(
                success=False,
                data={},
                message="Recipient (to) is required"
            )
        
        if not body and not subject:
            return ToolResult(
                success=False,
                data={},
                message="Subject or body is required"
            )
        
        # Get SMTP config
        config = self._get_smtp_config()
        
        if not config["username"] or not config["password"]:
            return ToolResult(
                success=False,
                data={
                    "required_env_vars": ["SMTP_USERNAME", "SMTP_PASSWORD"],
                    "optional_env_vars": ["SMTP_HOST", "SMTP_PORT", "SMTP_TLS"]
                },
                message="SMTP credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables."
            )
        
        if not from_email:
            from_email = config["username"]
        
        try:
            # Create message
            msg = MIMEMultipart("alternative" if html else "mixed")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to if isinstance(to, str) else ", ".join(to)
            
            if cc:
                msg["Cc"] = cc if isinstance(cc, str) else ", ".join(cc)
            
            # Add body
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            # Add attachments
            for attachment_path in attachments:
                if Path(attachment_path).exists():
                    with open(attachment_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={Path(attachment_path).name}"
                    )
                    msg.attach(part)
            
            # Collect all recipients
            recipients = [to] if isinstance(to, str) else list(to)
            if cc:
                recipients.extend([cc] if isinstance(cc, str) else list(cc))
            if bcc:
                recipients.extend([bcc] if isinstance(bcc, str) else list(bcc))
            
            # Send email
            with smtplib.SMTP(config["host"], config["port"]) as server:
                if config["use_tls"]:
                    server.starttls()
                server.login(config["username"], config["password"])
                server.sendmail(from_email, recipients, msg.as_string())
            
            return ToolResult(
                success=True,
                data={
                    "to": to,
                    "subject": subject,
                    "attachments": len(attachments)
                },
                message=f"Email sent to {to}"
            )
        except smtplib.SMTPAuthenticationError:
            return ToolResult(
                success=False,
                data={},
                message="SMTP authentication failed. Check your credentials.",
                error="Authentication error"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to send email: {str(e)}",
                error=str(e)
            )

    def _compose_email(self, **kwargs) -> ToolResult:
        """Open default email client to compose email."""
        to = kwargs.get("to", "")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")
        
        import subprocess
        import urllib.parse
        from ..utils.platform import detect_platform, Platform
        
        platform = detect_platform()
        
        try:
            # Create mailto URL
            mailto = f"mailto:{to}"
            params = []
            if subject:
                params.append(f"subject={urllib.parse.quote(subject)}")
            if body:
                params.append(f"body={urllib.parse.quote(body)}")
            if params:
                mailto += "?" + "&".join(params)
            
            if platform == Platform.MACOS:
                subprocess.Popen(["open", mailto])
            elif platform == Platform.WINDOWS:
                os.startfile(mailto)
            else:
                subprocess.Popen(["xdg-open", mailto])
            
            return ToolResult(
                success=True,
                data={"to": to, "subject": subject},
                message="Opened email client"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to open email client: {str(e)}",
                error=str(e)
            )

    def _save_draft(self, **kwargs) -> ToolResult:
        """Save email as draft file."""
        to = kwargs.get("to", "")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")
        path = kwargs.get("path")
        
        if not path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject = "".join(c if c.isalnum() else "_" for c in subject[:30])
            path = str(Path.home() / ".sysagent" / "drafts" / f"{safe_subject}_{timestamp}.eml")
        
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            # Create EML format
            eml_content = f"""To: {to}
Subject: {subject}
Content-Type: text/plain; charset="utf-8"

{body}
"""
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(eml_content)
            
            return ToolResult(
                success=True,
                data={"path": path},
                message=f"Draft saved to {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to save draft: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Send email: email_tool --action send --to 'user@example.com' --subject 'Hello' --body 'Message'",
            "Compose: email_tool --action compose --to 'user@example.com' --subject 'Hello'",
            "With attachment: email_tool --action send --to 'user@example.com' --subject 'Report' --attachments '[\"file.pdf\"]'",
        ]
