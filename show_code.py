#!/usr/bin/env python3
"""
Utility to display generated code from agent log files.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.log_utils import show_generated_code


def main():
    if len(sys.argv) < 2:
        print("Usage: python show_code.py <log_file_path> [attempt_number]")
        print("Example: python show_code.py logs/task_20231018_160000_example.json")
        print("Example: python show_code.py logs/task_20231018_160000_example.json 2")
        sys.exit(1)

    log_file = sys.argv[1]
    attempt_num = int(sys.argv[2]) if len(sys.argv) > 2 else None

    show_generated_code(log_file, attempt_num)


if __name__ == '__main__':
    main()