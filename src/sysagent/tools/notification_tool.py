"""
Notification tool for SysAgent CLI - System notifications and alerts.
"""

import subprocess
from typing import List
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class NotificationTool(BaseTool):
    """Tool for sending system notifications."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="notification_tool",
            description="Send system notifications and alerts",
            category=ToolCategory.SYSTEM,
            permissions=["notifications"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "send": self._send_notification,
                "notify": self._send_notification,
                "alert": self._send_alert,
                "reminder": self._create_reminder,
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
                message=f"Notification failed: {str(e)}",
                error=str(e)
            )

    def _send_notification(self, **kwargs) -> ToolResult:
        """Send a system notification."""
        title = kwargs.get("title", "SysAgent")
        message = kwargs.get("message", "") or kwargs.get("body", "") or kwargs.get("text", "")
        subtitle = kwargs.get("subtitle", "")
        sound = kwargs.get("sound", True)
        
        if not message:
            return ToolResult(
                success=False,
                data={},
                message="No message provided"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script_parts = [f'display notification "{message}"']
                if title:
                    script_parts.append(f'with title "{title}"')
                if subtitle:
                    script_parts.append(f'subtitle "{subtitle}"')
                if sound:
                    script_parts.append('sound name "default"')
                
                script = " ".join(script_parts)
                subprocess.run(["osascript", "-e", script], capture_output=True)
            
            elif platform == Platform.WINDOWS:
                ps_script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $textNodes = $template.GetElementsByTagName("text")
                $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) | Out-Null
                $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) | Out-Null
                $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("SysAgent").Show($toast)
                '''
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            
            else:  # Linux
                subprocess.run([
                    "notify-send",
                    title,
                    message,
                    "-u", "normal"
                ], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"title": title, "message": message},
                message=f"Notification sent: {title}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to send notification: {str(e)}",
                error=str(e)
            )

    def _send_alert(self, **kwargs) -> ToolResult:
        """Send an alert dialog."""
        title = kwargs.get("title", "Alert")
        message = kwargs.get("message", "") or kwargs.get("text", "")
        
        if not message:
            return ToolResult(
                success=False,
                data={},
                message="No message provided"
            )
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                script = f'''
                display alert "{title}" message "{message}"
                '''
                subprocess.run(["osascript", "-e", script], capture_output=True)
            elif platform == Platform.WINDOWS:
                ps_script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.MessageBox]::Show("{message}", "{title}")
                '''
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            else:
                subprocess.run(["zenity", "--info", "--title", title, "--text", message], capture_output=True)
            
            return ToolResult(
                success=True,
                data={"title": title, "message": message},
                message=f"Alert shown: {title}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to show alert: {str(e)}",
                error=str(e)
            )

    def _create_reminder(self, **kwargs) -> ToolResult:
        """Create a reminder notification."""
        message = kwargs.get("message", "") or kwargs.get("text", "")
        delay = kwargs.get("delay", 60)  # Seconds
        time_str = kwargs.get("time", "")
        
        if not message:
            return ToolResult(
                success=False,
                data={},
                message="No message provided"
            )
        
        # If time string provided, calculate delay
        if time_str:
            try:
                # Parse time like "14:30" or "2:30 PM"
                from datetime import datetime, timedelta
                now = datetime.now()
                
                if ":" in time_str:
                    if "PM" in time_str.upper() or "AM" in time_str.upper():
                        reminder_time = datetime.strptime(time_str, "%I:%M %p").replace(
                            year=now.year, month=now.month, day=now.day
                        )
                    else:
                        reminder_time = datetime.strptime(time_str, "%H:%M").replace(
                            year=now.year, month=now.month, day=now.day
                        )
                    
                    if reminder_time < now:
                        reminder_time += timedelta(days=1)
                    
                    delay = int((reminder_time - now).total_seconds())
            except:
                pass
        
        platform = detect_platform()
        
        try:
            if platform == Platform.MACOS:
                # Use at command or launchd
                script = f'''
                do shell script "sleep {delay} && osascript -e 'display notification \\"{message}\\" with title \\"Reminder\\" sound name \\"default\\"'" &
                '''
                subprocess.Popen([
                    "bash", "-c",
                    f'sleep {delay} && osascript -e \'display notification "{message}" with title "Reminder" sound name "default"\''
                ])
            elif platform == Platform.LINUX:
                subprocess.Popen([
                    "bash", "-c",
                    f'sleep {delay} && notify-send "Reminder" "{message}"'
                ])
            
            reminder_time = datetime.now()
            reminder_time = reminder_time.replace(second=reminder_time.second + delay)
            
            return ToolResult(
                success=True,
                data={"message": message, "delay": delay},
                message=f"Reminder set for {delay} seconds from now"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to create reminder: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Send notification: notification_tool --action send --title 'Hello' --message 'World'",
            "Alert: notification_tool --action alert --message 'Important!'",
            "Reminder: notification_tool --action reminder --message 'Meeting' --delay 300",
        ]
