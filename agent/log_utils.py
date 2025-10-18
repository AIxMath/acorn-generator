#!/usr/bin/env python3
"""
Logging module for the Acorn development agent.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List

DEFAULT_LOG_DIR = "logs"  # Directory for storing agent logs


def setup_logging(log_dir: str = DEFAULT_LOG_DIR) -> logging.Logger:
    """Set up comprehensive logging for the agent."""
    os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger("acorn_agent")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler for detailed logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"agent_{timestamp}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"📝 Logging initialized - Log file: {log_file}")
    return logger


def create_log_entry(task_description: str, mode: str = "auto") -> Dict:
    """Create a structured log entry for tracking agent runs."""
    return {
        "timestamp": datetime.now().isoformat(),
        "task": task_description,
        "mode": mode,
        "attempts": [],
        "final_status": None,
        "files_modified": [],
        "error_messages": [],
        "total_time_seconds": None
    }


def log_attempt(log_entry: Dict, attempt: int, implementation: Dict, error_context: str = None) -> None:
    """Log a single attempt at implementation."""
    attempt_data = {
        "attempt": attempt,
        "analysis": implementation.get('analysis', 'No analysis'),
        "files_count": len(implementation.get('files', [])),
        "files": [f.get('path', 'unknown') for f in implementation.get('files', [])],
        "commit_message": implementation.get('commit_message', 'No commit message'),
        "error_context": error_context,
        "has_raw_response": 'raw_response' in implementation
    }
    log_entry["attempts"].append(attempt_data)


def save_agent_log(log_entry: Dict, log_dir: str = DEFAULT_LOG_DIR) -> str:
    """Save the complete agent log entry to a JSON file."""
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_safe_name = "".join(c for c in log_entry["task"][:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
    task_safe_name = task_safe_name.replace(' ', '_')
    log_filename = f"task_{timestamp}_{task_safe_name}.json"
    log_path = os.path.join(log_dir, log_filename)

    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        return log_path
    except Exception as e:
        logging.error(f"Failed to save agent log: {e}")
        return ""


def analyze_logs(log_dir: str = DEFAULT_LOG_DIR) -> None:
    """Analyze agent logs to identify failure patterns and statistics."""
    if not os.path.exists(log_dir):
        print(f"❌ Log directory not found: {log_dir}")
        return

    print(f"\n📊 Analyzing logs in: {log_dir}")

    # Find all JSON log files
    json_files = [f for f in os.listdir(log_dir) if f.startswith('task_') and f.endswith('.json')]
    if not json_files:
        print("📝 No task logs found.")
        return

    print(f"📁 Found {len(json_files)} task logs")

    # Statistics
    stats = {
        'total_tasks': 0,
        'successful': 0,
        'failed_verification': 0,
        'failed_json_parsing': 0,
        'failed_commit': 0,
        'completed_no_changes': 0,
        'other_failures': 0,
        'total_files_modified': 0,
        'avg_attempts': 0,
        'common_errors': {}
    }

    all_tasks = []

    # Process each log file
    for json_file in json_files:
        log_path = os.path.join(log_dir, json_file)
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
                all_tasks.append(task_data)

                stats['total_tasks'] += 1
                status = task_data.get('final_status', 'unknown')

                # Count by status
                if status == 'completed_successfully':
                    stats['successful'] += 1
                elif status == 'failed_verification':
                    stats['failed_verification'] += 1
                elif status == 'failed_json_parsing':
                    stats['failed_json_parsing'] += 1
                elif status == 'failed_commit':
                    stats['failed_commit'] += 1
                elif status == 'completed_no_changes':
                    stats['completed_no_changes'] += 1
                else:
                    stats['other_failures'] += 1

                # Count files modified
                stats['total_files_modified'] += len(task_data.get('files_modified', []))

                # Count attempts
                stats['avg_attempts'] += len(task_data.get('attempts', []))

                # Collect common errors
                for error in task_data.get('error_messages', []):
                    # Extract first 100 characters to group similar errors
                    error_key = error[:100]
                    stats['common_errors'][error_key] = stats['common_errors'].get(error_key, 0) + 1

        except Exception as e:
            print(f"⚠️ Error reading {json_file}: {e}")

    if stats['total_tasks'] > 0:
        stats['avg_attempts'] = stats['avg_attempts'] / stats['total_tasks']

    # Print statistics
    print(f"\n📈 Task Statistics:")
    print(f"   Total tasks: {stats['total_tasks']}")
    print(f"   ✅ Successful: {stats['successful']} ({stats['successful']/stats['total_tasks']*100:.1f}%)")
    print(f"   ❌ Failed verification: {stats['failed_verification']} ({stats['failed_verification']/stats['total_tasks']*100:.1f}%)")
    print(f"   ❌ Failed JSON parsing: {stats['failed_json_parsing']} ({stats['failed_json_parsing']/stats['total_tasks']*100:.1f}%)")
    print(f"   ❌ Failed commit: {stats['failed_commit']} ({stats['failed_commit']/stats['total_tasks']*100:.1f}%)")
    print(f"   ✅ No changes needed: {stats['completed_no_changes']} ({stats['completed_no_changes']/stats['total_tasks']*100:.1f}%)")
    print(f"   ❌ Other failures: {stats['other_failures']} ({stats['other_failures']/stats['total_tasks']*100:.1f}%)")

    print(f"\n📝 Averages:")
    print(f"   Files modified per task: {stats['total_files_modified']/stats['total_tasks']:.1f}")
    print(f"   Attempts per task: {stats['avg_attempts']:.1f}")

    # Show top common errors
    if stats['common_errors']:
        print(f"\n🔍 Top Common Errors:")
        sorted_errors = sorted(stats['common_errors'].items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (error, count) in enumerate(sorted_errors, 1):
            print(f"   {i}. ({count} occurrences) {error}")

    # Show recent failures
    print(f"\n🕒 Recent Failed Tasks:")
    failed_tasks = [t for t in all_tasks if 'failed' in t.get('final_status', '')]
    failed_tasks.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    for task in failed_tasks[:5]:
        print(f"   📋 {task.get('task', 'Unknown task')[:60]}...")
        print(f"      Status: {task.get('final_status', 'unknown')}")
        if task.get('error_messages'):
            first_error = task['error_messages'][0][:100]
            print(f"      Error: {first_error}...")
        print()