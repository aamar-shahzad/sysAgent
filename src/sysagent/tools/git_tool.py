"""
Git tool for SysAgent CLI - Git repository operations.
"""

import subprocess
import os
from pathlib import Path
from typing import List

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory


@register_tool
class GitTool(BaseTool):
    """Tool for Git version control operations."""
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_tool",
            description="Git operations - clone, commit, push, pull, status",
            category=ToolCategory.FILE,
            permissions=["git_access"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        try:
            actions = {
                "status": self._status,
                "clone": self._clone,
                "pull": self._pull,
                "push": self._push,
                "commit": self._commit,
                "add": self._add,
                "branch": self._branch,
                "checkout": self._checkout,
                "log": self._log,
                "diff": self._diff,
                "init": self._init,
                "stash": self._stash,
                "remote": self._remote,
                "fetch": self._fetch,
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
                message=f"Git operation failed: {str(e)}",
                error=str(e)
            )

    def _run_git(self, args: List[str], cwd: str = None) -> tuple:
        """Run a git command."""
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd()
        )
        return result.returncode, result.stdout, result.stderr

    def _status(self, **kwargs) -> ToolResult:
        """Get repository status."""
        path = kwargs.get("path", ".")
        
        try:
            code, stdout, stderr = self._run_git(["status", "--short"], cwd=path)
            
            if code == 0:
                # Parse status
                changes = []
                for line in stdout.strip().split("\n"):
                    if line:
                        status = line[:2].strip()
                        filename = line[3:]
                        changes.append({"status": status, "file": filename})
                
                # Get branch
                _, branch_out, _ = self._run_git(["branch", "--show-current"], cwd=path)
                branch = branch_out.strip()
                
                return ToolResult(
                    success=True,
                    data={
                        "branch": branch,
                        "changes": changes,
                        "clean": len(changes) == 0
                    },
                    message=f"On branch {branch}, {len(changes)} changes" if changes else f"On branch {branch}, working tree clean"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Not a git repository",
                    error=stderr
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Status failed: {str(e)}",
                error=str(e)
            )

    def _clone(self, **kwargs) -> ToolResult:
        """Clone a repository."""
        url = kwargs.get("url") or kwargs.get("repo")
        path = kwargs.get("path", "")
        
        if not url:
            return ToolResult(
                success=False,
                data={},
                message="No repository URL provided"
            )
        
        try:
            args = ["clone", url]
            if path:
                args.append(path)
            
            code, stdout, stderr = self._run_git(args)
            
            if code == 0:
                return ToolResult(
                    success=True,
                    data={"url": url, "path": path},
                    message=f"Cloned {url}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Clone failed: {stderr}",
                    error=stderr
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Clone failed: {str(e)}",
                error=str(e)
            )

    def _pull(self, **kwargs) -> ToolResult:
        """Pull changes from remote."""
        path = kwargs.get("path", ".")
        remote = kwargs.get("remote", "origin")
        branch = kwargs.get("branch", "")
        
        try:
            args = ["pull", remote]
            if branch:
                args.append(branch)
            
            code, stdout, stderr = self._run_git(args, cwd=path)
            
            return ToolResult(
                success=code == 0,
                data={"output": stdout},
                message="Pulled successfully" if code == 0 else f"Pull failed: {stderr}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Pull failed: {str(e)}",
                error=str(e)
            )

    def _push(self, **kwargs) -> ToolResult:
        """Push changes to remote."""
        path = kwargs.get("path", ".")
        remote = kwargs.get("remote", "origin")
        branch = kwargs.get("branch", "")
        force = kwargs.get("force", False)
        
        try:
            args = ["push", remote]
            if branch:
                args.append(branch)
            if force:
                args.append("--force")
            
            code, stdout, stderr = self._run_git(args, cwd=path)
            
            return ToolResult(
                success=code == 0,
                data={"output": stdout + stderr},
                message="Pushed successfully" if code == 0 else f"Push failed: {stderr}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Push failed: {str(e)}",
                error=str(e)
            )

    def _commit(self, **kwargs) -> ToolResult:
        """Commit changes."""
        message = kwargs.get("message") or kwargs.get("m")
        path = kwargs.get("path", ".")
        all_changes = kwargs.get("all", False)
        
        if not message:
            return ToolResult(
                success=False,
                data={},
                message="Commit message required"
            )
        
        try:
            args = ["commit", "-m", message]
            if all_changes:
                args.insert(1, "-a")
            
            code, stdout, stderr = self._run_git(args, cwd=path)
            
            return ToolResult(
                success=code == 0,
                data={"message": message, "output": stdout},
                message="Committed successfully" if code == 0 else f"Commit failed: {stderr}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Commit failed: {str(e)}",
                error=str(e)
            )

    def _add(self, **kwargs) -> ToolResult:
        """Stage files for commit."""
        files = kwargs.get("files", [])
        path = kwargs.get("path", ".")
        all_files = kwargs.get("all", False)
        
        try:
            if all_files:
                args = ["add", "-A"]
            elif files:
                args = ["add"] + (files if isinstance(files, list) else [files])
            else:
                args = ["add", "."]
            
            code, stdout, stderr = self._run_git(args, cwd=path)
            
            return ToolResult(
                success=code == 0,
                data={"files": files},
                message="Files staged" if code == 0 else f"Add failed: {stderr}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Add failed: {str(e)}",
                error=str(e)
            )

    def _branch(self, **kwargs) -> ToolResult:
        """List or create branches."""
        name = kwargs.get("name")
        path = kwargs.get("path", ".")
        delete = kwargs.get("delete", False)
        
        try:
            if name:
                if delete:
                    args = ["branch", "-d", name]
                else:
                    args = ["branch", name]
            else:
                args = ["branch", "-a"]
            
            code, stdout, stderr = self._run_git(args, cwd=path)
            
            if not name:
                branches = [b.strip() for b in stdout.strip().split("\n") if b.strip()]
                return ToolResult(
                    success=True,
                    data={"branches": branches},
                    message=f"Found {len(branches)} branches"
                )
            
            return ToolResult(
                success=code == 0,
                data={"branch": name},
                message=f"Branch {name} {'deleted' if delete else 'created'}" if code == 0 else stderr
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Branch operation failed: {str(e)}",
                error=str(e)
            )

    def _checkout(self, **kwargs) -> ToolResult:
        """Switch branches or restore files."""
        branch = kwargs.get("branch") or kwargs.get("name")
        create = kwargs.get("create", False)
        path = kwargs.get("path", ".")
        
        if not branch:
            return ToolResult(
                success=False,
                data={},
                message="Branch name required"
            )
        
        try:
            args = ["checkout"]
            if create:
                args.append("-b")
            args.append(branch)
            
            code, stdout, stderr = self._run_git(args, cwd=path)
            
            return ToolResult(
                success=code == 0,
                data={"branch": branch},
                message=f"Switched to {branch}" if code == 0 else stderr
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Checkout failed: {str(e)}",
                error=str(e)
            )

    def _log(self, **kwargs) -> ToolResult:
        """Show commit log."""
        path = kwargs.get("path", ".")
        count = kwargs.get("count", 10)
        
        try:
            code, stdout, stderr = self._run_git(
                ["log", f"-{count}", "--oneline"],
                cwd=path
            )
            
            commits = []
            for line in stdout.strip().split("\n"):
                if line:
                    parts = line.split(" ", 1)
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1] if len(parts) > 1 else ""
                    })
            
            return ToolResult(
                success=True,
                data={"commits": commits},
                message=f"Last {len(commits)} commits"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Log failed: {str(e)}",
                error=str(e)
            )

    def _diff(self, **kwargs) -> ToolResult:
        """Show changes."""
        path = kwargs.get("path", ".")
        staged = kwargs.get("staged", False)
        file = kwargs.get("file")
        
        try:
            args = ["diff"]
            if staged:
                args.append("--staged")
            if file:
                args.append(file)
            
            code, stdout, stderr = self._run_git(args, cwd=path)
            
            return ToolResult(
                success=True,
                data={"diff": stdout[:2000]},
                message=f"Diff: {len(stdout)} characters"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Diff failed: {str(e)}",
                error=str(e)
            )

    def _init(self, **kwargs) -> ToolResult:
        """Initialize a new repository."""
        path = kwargs.get("path", ".")
        
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            code, stdout, stderr = self._run_git(["init"], cwd=path)
            
            return ToolResult(
                success=code == 0,
                data={"path": path},
                message=f"Initialized repository in {path}" if code == 0 else stderr
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Init failed: {str(e)}",
                error=str(e)
            )

    def _stash(self, **kwargs) -> ToolResult:
        """Stash changes."""
        path = kwargs.get("path", ".")
        pop = kwargs.get("pop", False)
        list_stash = kwargs.get("list", False)
        
        try:
            if list_stash:
                args = ["stash", "list"]
            elif pop:
                args = ["stash", "pop"]
            else:
                args = ["stash"]
            
            code, stdout, stderr = self._run_git(args, cwd=path)
            
            return ToolResult(
                success=code == 0,
                data={"output": stdout},
                message="Stash operation completed"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Stash failed: {str(e)}",
                error=str(e)
            )

    def _remote(self, **kwargs) -> ToolResult:
        """Show or manage remotes."""
        path = kwargs.get("path", ".")
        
        try:
            code, stdout, stderr = self._run_git(["remote", "-v"], cwd=path)
            
            remotes = []
            for line in stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        remotes.append({"name": parts[0], "url": parts[1]})
            
            return ToolResult(
                success=True,
                data={"remotes": remotes},
                message=f"Found {len(remotes)} remotes"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Remote failed: {str(e)}",
                error=str(e)
            )

    def _fetch(self, **kwargs) -> ToolResult:
        """Fetch from remote."""
        path = kwargs.get("path", ".")
        remote = kwargs.get("remote", "origin")
        
        try:
            code, stdout, stderr = self._run_git(["fetch", remote], cwd=path)
            
            return ToolResult(
                success=code == 0,
                data={"remote": remote},
                message="Fetched successfully" if code == 0 else stderr
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Fetch failed: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        return [
            "Status: git_tool --action status",
            "Clone: git_tool --action clone --url 'https://github.com/user/repo'",
            "Commit: git_tool --action commit --message 'Fix bug'",
            "Pull: git_tool --action pull",
            "Push: git_tool --action push",
            "Branch: git_tool --action branch",
        ]
