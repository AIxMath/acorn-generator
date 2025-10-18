#!/usr/bin/env python3
"""
Autonomous Acorn Standard Library Development Agent

This agent automatically implements tasks from TODO.md, verifies code with ./acorn,
commits changes with meaningful messages, and pushes to the repository.
"""

import sys
import os

# Add the current directory to the Python path to ensure agent package is found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.cli import main

if __name__ == '__main__':
    main()