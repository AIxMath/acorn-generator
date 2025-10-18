#!/usr/bin/env python3
"""
Verification module for Acorn code checking.
"""

import os
from agent.git_ops import run_command
from typing import Tuple


def verify_acorn_file(acornlib_path: str, test_file: str) -> Tuple[bool, str]:
    """Verify a specific Acorn file. Returns (success, output)."""
    # Get parent directory (where acorn binary is located)
    parent_dir = os.path.dirname(os.path.abspath(acornlib_path))

    print(f"\n🔍 Verifying {test_file} with ./acorn --lib ./acornlib...")
    returncode, stdout, stderr = run_command(
        ["./acorn", "--lib", "./acornlib", test_file],
        cwd=parent_dir,
        check=False
    )

    output = stdout + stderr
    success = returncode == 0

    if success:
        print("✅ Code verification passed!")
    else:
        print("❌ Code verification failed!")
        print(output)

    return success, output


def verify_acorn_code(acornlib_path: str) -> Tuple[bool, str]:
    """Run ./acorn --lib ./acornlib to verify all code. Returns (success, output)."""
    # Get parent directory (where acorn binary is located)
    parent_dir = os.path.dirname(os.path.abspath(acornlib_path))

    print("\n🔍 Verifying all code with ./acorn --lib ./acornlib...")
    returncode, stdout, stderr = run_command(
        ["./acorn", "--lib", "./acornlib"],
        cwd=parent_dir,
        check=False
    )

    output = stdout + stderr
    success = returncode == 0

    if success:
        print("✅ Code verification passed!")
    else:
        print("❌ Code verification failed!")
        print(output)

    return success, output