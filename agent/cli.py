#!/usr/bin/env python3
"""
Command line interface for the Acorn development agent.
"""

import argparse
import os
import sys
from typing import List

from agent.agent import run_agent
from agent.log_utils import analyze_logs, DEFAULT_LOG_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Acorn Standard Library Development Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This agent:
1. Reads TODO.md to find next task (or accepts manual/interactive input)
2. Uses LLM to generate implementation
3. Applies changes directly to stdlib files
4. Verifies with ./acorn --lib ./acornlib (runs from base directory)
5. Auto-fixes errors (up to 3 attempts with error feedback)
6. Commits and pushes changes
7. Updates TODO.md (if in TODO.md mode)
8. Logs all actions and failures to JSON files
9. Repeats until all tasks are done (TODO.md mode)

Logging:
- All agent runs are logged to JSON files in the 'logs' directory
- Each task creates a detailed log with attempts, errors, and outcomes
- Logs include LLM responses, verification errors, and file modifications
- Use logs to analyze why code generation fails and identify patterns

Environment variables required:
  OPENAI_API_KEY - API key for LLM
  OPENAI_BASE_URL - Base URL for LLM API
"""
    )

    parser.add_argument(
        '--acornlib-path',
        default='acornlib',
        help='Path to acornlib repository (default: acornlib)'
    )

    parser.add_argument(
        '--context',
        default='context.txt',
        help='Path to Acorn documentation context file (default: context.txt)'
    )

    parser.add_argument(
        '--model',
        default='deepseek-v3-250324',
        help='LLM model to use (default: deepseek-v3-250324)'
    )

    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum number of tasks to complete (default: 10)'
    )

    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Do not push to remote (only commit locally)'
    )

    parser.add_argument(
        '--confirm-push',
        action='store_true',
        help='Ask for confirmation before each push to remote'
    )

    parser.add_argument(
        '--task',
        type=str,
        help='Single task to execute (manual mode, does not use TODO.md)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode - enter tasks manually'
    )

    parser.add_argument(
        '--analyze-logs',
        action='store_true',
        help='Analyze agent logs to identify failure patterns'
    )

    parser.add_argument(
        '--log-dir',
        default='logs',
        help='Directory to save agent logs (default: logs)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    # Handle log analysis
    if args.analyze_logs:
        analyze_logs(args.log_dir)
        return

    # Validate paths
    if not os.path.exists(args.acornlib_path):
        print(f"Error: acornlib path not found: {args.acornlib_path}")
        sys.exit(1)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        todo_path = os.path.join(args.acornlib_path, "TODO.md")
        from agent.file_ops import extract_next_task
        task = extract_next_task(todo_path)
        if task:
            print(f"\nNext task would be: {task['description']}")
        else:
            print("\nNo tasks found in TODO.md")
        return

    # Note: log_dir is passed through to functions as needed

    # Run the agent
    run_agent(
        acornlib_path=args.acornlib_path,
        context_file=args.context,
        model=args.model,
        max_iterations=args.max_iterations,
        auto_push=not args.no_push,
        confirm_before_push=args.confirm_push,
        manual_task=args.task,
        interactive=args.interactive
    )


if __name__ == '__main__':
    main()