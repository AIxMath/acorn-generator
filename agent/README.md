# Agent Package Structure

This directory contains the modularized components of the Acorn autonomous development agent.

## Module Overview

### `__init__.py`
Package initialization and public API exports.

### `cli.py`
Command-line interface and argument parsing.
- Handles all command-line arguments
- Routes to appropriate execution modes (TODO.md, manual, interactive, analyze-logs)
- Entry point for the application

### `agent.py`
Main agent logic and orchestration.
- `run_agent()`: Main entry point for running the agent in different modes
- `run_single_task()`: Executes a single task with auto-fix retry logic
- Coordinates between LLM, verification, and git operations
- Implements the auto-fix loop (up to 3 attempts)

### `file_ops.py`
File reading, writing, and context management.
- `read_file()`, `write_file()`: Basic file I/O
- `extract_next_task()`: Parse TODO.md for next task
- `update_todo_mark_complete()`: Mark tasks as complete in TODO.md
- `load_acorn_context()`: Load documentation and context files
- `load_existing_files()`: Find and load relevant .ac files for a task
- `apply_implementation()`: Apply LLM-generated changes to files

### `git_ops.py`
Git operations for version control.
- `run_command()`: Execute shell commands
- `git_add_commit_push()`: Add, commit, and optionally push changes

### `verification.py`
Acorn code verification using the Acorn binary.
- `verify_acorn_code()`: Verify all code with `./acorn --lib ./acornlib`
- `verify_acorn_file()`: Verify a specific file

### `llm_interface.py`
LLM integration for code generation.
- `generate_implementation()`: Generate Acorn code using LLM
- Constructs prompts with context, existing files, and error feedback
- Parses LLM responses (handles JSON extraction from markdown blocks)

### `log_utils.py`
Logging and analysis functionality.
- `setup_logging()`: Configure logging for the agent
- `create_log_entry()`: Create structured log entry for a task
- `log_attempt()`: Log each implementation attempt
- `save_agent_log()`: Save complete task log to JSON
- `analyze_logs()`: Analyze historical logs for patterns and statistics
- `show_generated_code()`: Display complete generated code from a specific log file

## Design Principles

1. **Separation of Concerns**: Each module handles a specific aspect of the agent
2. **Testability**: Functions are small and focused, making them easy to test
3. **Maintainability**: Clear module boundaries make the code easier to understand and modify
4. **Reusability**: Components can be imported and used independently

## Usage

The agent can be used in three modes:

```bash
# TODO.md mode (default)
python acorn_agent.py

# Manual task mode
python acorn_agent.py --task "Add multiplication axioms"

# Interactive mode
python acorn_agent.py --interactive

# Analyze logs
python acorn_agent.py --analyze-logs

# View complete generated code from a log file
python agent/log_utils.py logs/task_20231018_160000_example.json

# View specific attempt from a log file
python agent/log_utils.py logs/task_20231018_160000_example.json 2
```

## Error Handling

The agent implements a robust auto-fix mechanism:
1. LLM generates implementation
2. Code is verified with `./acorn`
3. If verification fails, error message is fed back to LLM
4. Process repeats up to 3 times
5. Changes are rolled back between attempts using `git checkout .`

## Logging

All agent activities are logged to JSON files in the `logs/` directory:
- General activity logs: `agent_YYYYMMDD_HHMMSS.log`
- Task-specific logs: `task_YYYYMMDD_HHMMSS_task_name.json`

Logs include:
- Task description and mode
- All LLM attempts with analysis
- **Complete generated code for each file** (full content, not just paths)
- Error messages and verification failures
- Final status and total execution time
- Raw LLM responses (for debugging)
