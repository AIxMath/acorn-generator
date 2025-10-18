#!/usr/bin/env python3
"""
LLM interface module for generating Acorn code implementations.
"""

import os
import re
import sys
from typing import Dict, Any

# Import the LLM helper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from llm import ask
except ImportError:
    # If llm module is not in parent directory, try current directory
    from llm import ask

from agent.file_ops import load_existing_files


def generate_implementation(task: Dict[str, str], context: str, model: str, acornlib_path: str, error_context: str = None) -> Dict[str, Any]:
    """Generate implementation for a task using LLM."""

    error_instruction = ""
    if error_context:
        error_instruction = f"""
PREVIOUS ATTEMPT FAILED WITH ERROR:
{error_context}

Please fix the error above. Common issues:
- Type names must be capitalized (Nat, not nat)
- Variable names must be lowercase
- Missing imports or numerals statements
- Syntax errors in proofs or definitions
"""

    # Load existing files that might be relevant
    existing_files = load_existing_files(acornlib_path, task['description'])
    existing_files_section = ""

    if existing_files:
        existing_files_section = "\n=== EXISTING FILES (to be modified carefully) ===\n"
        for file_path, content in existing_files.items():
            existing_files_section += f"\nFile: {file_path}\n```acorn\n{content}\n```\n"

    prompt = f"""You are an expert Acorn theorem prover developer. You are working on the Acorn standard library.

TASK: {task['description']}

{error_instruction}

CONTEXT:
{context}
{existing_files_section}

Your job is to implement this task by:
1. Analyzing what needs to be done
2. Determining which files need to be modified
3. Writing the necessary Acorn code following the syntax and style in the codebase
4. Ensuring the code will verify with ./acorn

CRITICAL RULES FOR MODIFYING EXISTING FILES:
- **DO NOT rewrite entire files** - only add new content at the end
- **PRESERVE all existing code** - copy it exactly as-is
- **Add new definitions/theorems AFTER existing code**
- When modifying a file, include ALL existing content first, then append your additions
- Make minimal, surgical changes - do not restructure or refactor existing code
- If a file already exists, your "content" field must contain: [existing code] + [your new additions]
- **You can modify MULTIPLE files** - include all necessary files in the "files" array
- **If NO changes are needed**, return empty "files" array with explanation in "analysis"

GENERAL RULES:
- Follow the Acorn syntax exactly as shown in the existing code
- Use /// for doc comments, not //
- Variable names must be lowercase
- Type names must be capitalized (Nat, Real, etc.)
- Numeric literals must have a type (Nat.0, Real.0, etc.) unless numerals statement exists
- Write proofs step-by-step, filling in all intermediate steps
- Follow the style guide in CLAUDE.md

OUTPUT FORMAT:
Provide your response as a JSON object with:
{{
    "analysis": "Brief analysis of what needs to be done",
    "files": [
        {{
            "path": "relative/path/to/file.ac",
            "action": "create" or "modify",
            "content": "full file content (for modify: existing code + new additions)",
            "explanation": "why this change is needed"
        }}
    ],
    "commit_message": "concise commit message following conventional commits style",
    "verification_notes": "what to check when running ./acorn"
}}

Generate the implementation now:"""

    response = ask(prompt, model=model)

    # Try to extract JSON from response
    # LLMs sometimes wrap JSON in markdown code blocks
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        response = json_match.group(1)

    # Try to parse as JSON
    import json
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # If not valid JSON, return structured error
        return {
            "analysis": "Failed to parse LLM response as JSON",
            "files": [],
            "commit_message": "Failed implementation attempt",
            "verification_notes": "Manual review needed",
            "raw_response": response
        }