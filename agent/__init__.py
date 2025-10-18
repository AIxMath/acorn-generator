"""
Acorn Development Agent Package.

This package contains modules for autonomous development of the Acorn standard library.
"""

from .agent import run_agent, run_single_task
from .cli import main
from .log_utils import setup_logging, analyze_logs, create_log_entry, save_agent_log
from .git_ops import git_add_commit_push
from .verification import verify_acorn_code, verify_acorn_file
from .file_ops import (
    read_file, write_file, load_acorn_context, extract_next_task,
    update_todo_mark_complete, apply_implementation
)
from .llm_interface import generate_implementation

__all__ = [
    'run_agent',
    'run_single_task',
    'main',
    'setup_logging',
    'analyze_logs',
    'create_log_entry',
    'save_agent_log',
    'git_add_commit_push',
    'verify_acorn_code',
    'verify_acorn_file',
    'read_file',
    'write_file',
    'load_acorn_context',
    'extract_next_task',
    'update_todo_mark_complete',
    'apply_implementation',
    'generate_implementation'
]