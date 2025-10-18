#!/usr/bin/env python3
"""
File operations module for reading, writing, and context management.
"""

import os
import re
from typing import Any, Dict, List, Optional


def read_file(path: str) -> str:
    """Read file contents."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path: str, content: str) -> None:
    """Write file contents."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def extract_next_task(todo_path: str) -> Optional[Dict[str, str]]:
    """Extract the next uncompleted task from TODO.md."""
    content = read_file(todo_path)

    # Look for the NEXT STEP marker
    next_step_pattern = r'\*\*NEXT STEP\*\*:\s*(.+?)(?:\n|$)'
    match = re.search(next_step_pattern, content)

    if match:
        return {
            'description': match.group(1).strip(),
            'type': 'next_step',
            'context': content
        }

    # Look for unchecked items
    unchecked_pattern = r'- \[ \]\s*(.+?)(?:\n|$)'
    matches = re.findall(unchecked_pattern, content)

    if matches:
        return {
            'description': matches[0].strip(),
            'type': 'unchecked',
            'context': content
        }

    return None


def update_todo_mark_complete(todo_path: str, task_description: str) -> None:
    """Mark a task as complete in TODO.md."""
    content = read_file(todo_path)

    # Replace [ ] with [x] for this task
    # Handle both regular items and NEXT STEP items
    patterns = [
        (rf'(- \[ \]\s*\*\*NEXT STEP\*\*:\s*{re.escape(task_description)})', r'- [x] ~~NEXT STEP~~: ' + task_description),
        (rf'(- \[ \]\s*{re.escape(task_description)})', r'- [x] ' + task_description)
    ]

    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            break

    write_file(todo_path, content)
    print(f"✅ Marked task as complete in TODO.md")


def load_acorn_context(acornlib_path: str, context_file: str) -> str:
    """Load Acorn library context."""
    # Read key files for context
    context_parts = []

    # Read CLAUDE.md for guidelines
    claude_md_path = os.path.join(acornlib_path, "CLAUDE.md")
    if os.path.exists(claude_md_path):
        context_parts.append("=== CLAUDE.md (Development Guidelines) ===")
        context_parts.append(read_file(claude_md_path))

    # Read TODO.md
    todo_path = os.path.join(acornlib_path, "TODO.md")
    if os.path.exists(todo_path):
        context_parts.append("\n=== TODO.md (Current Tasks) ===")
        context_parts.append(read_file(todo_path))

    # Read context file if available
    if os.path.exists(context_file):
        with open(context_file, 'r') as f:
            # Read first 20000 chars to avoid token limits
            # acorn_docs = f.read(20000)
            # context_parts.append("\n=== Acorn Documentation (Truncated) ===")
            acorn_docs = f.read()
            context_parts.append("\n=== Acorn Documentation ===")
            context_parts.append(acorn_docs)

    return "\n".join(context_parts)


def load_existing_files(acornlib_path: str, task_description: str) -> Dict[str, str]:
    """Load existing files that might be relevant to the task."""
    existing_files = {}

    # Common patterns to search for based on task description
    keywords = task_description.lower().split()

    # Search for .ac files in the acornlib directory
    for root, dirs, files in os.walk(acornlib_path):
        for file in files:
            if file.endswith('.ac'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, acornlib_path)

                # Check if filename matches any keyword in the task
                if any(keyword in file.lower() for keyword in keywords):
                    try:
                        content = read_file(file_path)
                        existing_files[relative_path] = content
                    except Exception as e:
                        print(f"Warning: Could not read {relative_path}: {e}")

    return existing_files


def apply_implementation(acornlib_path: str, implementation: Dict[str, Any]) -> List[str]:
    """Apply the implementation to files. Returns list of modified file paths."""
    modified_files = []

    for file_spec in implementation.get('files', []):
        file_path = os.path.join(acornlib_path, file_spec['path'])
        action = file_spec.get('action', 'modify')

        print(f"\n📝 {action.capitalize()}ing {file_spec['path']}...")
        print(f"   Reason: {file_spec.get('explanation', 'No explanation provided')}")

        if action == 'create':
            # Create new file
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            write_file(file_path, file_spec['content'])
            modified_files.append(file_spec['path'])
        elif action == 'modify':
            # For modify, we expect 'content'
            if 'content' in file_spec:
                write_file(file_path, file_spec['content'])
                modified_files.append(file_spec['path'])
            else:
                print(f"   ⚠️  Modify action without content - skipping")

    return modified_files