#!/usr/bin/env python3
"""
Git operations module for the Acorn development agent.
"""

import subprocess
from typing import List


def run_command(cmd: List[str], cwd: str = None, check: bool = True):
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    if check and result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
    return result.returncode, result.stdout, result.stderr


def git_add_commit_push(acornlib_path: str, files: List[str], commit_message: str, push: bool = True, confirm_before_push: bool = False) -> bool:
    """Git add, commit, and optionally push changes."""
    try:
        # Add files
        for file in files:
            returncode, _, _ = run_command(["git", "add", file], cwd=acornlib_path, check=False)
            if returncode != 0:
                print(f"Failed to git add {file}")
                return False

        # Commit - pass commit_message as single argument to ensure proper handling
        returncode, stdout, stderr = run_command(
            ["git", "commit", "-m", commit_message],
            cwd=acornlib_path,
            check=False
        )
        if returncode != 0:
            print("Failed to git commit")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return False

        print(f"✅ Committed: {commit_message}")

        # Push if requested
        if push:
            # Ask for confirmation if enabled
            if confirm_before_push:
                print(f"\n📤 Ready to push to remote repository.")
                print(f"   Commit: {commit_message}")
                response = input("   Push to remote? [y/N]: ").strip().lower()
                if response not in ['y', 'yes']:
                    print("⏸️  Skipped push (commit remains local)")
                    return True

            returncode, _, _ = run_command(["git", "push"], cwd=acornlib_path, check=False)
            if returncode != 0:
                print("Failed to git push")
                return False
            print("✅ Pushed to remote repository")

        return True
    except Exception as e:
        print(f"Git operation failed: {e}")
        return False