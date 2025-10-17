#!/usr/bin/env python3
"""
Autonomous Acorn Standard Library Development Agent

This agent automatically implements tasks from TODO.md, verifies code with ./acorn,
commits changes with meaningful messages, and pushes to the repository.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from typing import List, Dict, Tuple, Optional

# Import the LLM helper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import ask


ACORNLIB_DIR = "acornlib"
CONTEXT_FILE = "context.txt"
MAX_FIX_ATTEMPTS = 3  # Maximum auto-fix attempts


def run_command(cmd: List[str], cwd: str = None, check: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    if check and result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"Error: {result.stderr}", file=sys.stderr)
    return result.returncode, result.stdout, result.stderr


def verify_acorn_file(acornlib_path: str, test_file: str) -> Tuple[bool, str]:
    """Verify a specific Acorn file. Returns (success, output)."""
    print(f"\n🔍 Verifying {test_file} with ./acorn...")
    returncode, stdout, stderr = run_command(
        ["./acorn", test_file],
        cwd=acornlib_path,
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
    """Run ./acorn to verify all code. Returns (success, output)."""
    print("\n🔍 Verifying all code with ./acorn...")
    returncode, stdout, stderr = run_command(["./acorn"], cwd=acornlib_path, check=False)

    output = stdout + stderr
    success = returncode == 0

    if success:
        print("✅ Code verification passed!")
    else:
        print("❌ Code verification failed!")
        print(output)

    return success, output


def git_add_commit_push(acornlib_path: str, files: List[str], commit_message: str, push: bool = True) -> bool:
    """Git add, commit, and optionally push changes."""
    try:
        # Add files
        for file in files:
            returncode, _, _ = run_command(["git", "add", file], cwd=acornlib_path)
            if returncode != 0:
                print(f"Failed to git add {file}")
                return False

        # Commit
        returncode, _, _ = run_command(
            ["git", "commit", "-m", commit_message],
            cwd=acornlib_path
        )
        if returncode != 0:
            print("Failed to git commit")
            return False

        print(f"✅ Committed: {commit_message}")

        # Push if requested
        if push:
            returncode, _, _ = run_command(["git", "push"], cwd=acornlib_path)
            if returncode != 0:
                print("Failed to git push")
                return False
            print("✅ Pushed to remote repository")

        return True
    except Exception as e:
        print(f"Git operation failed: {e}")
        return False


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
            acorn_docs = f.read(20000)
            context_parts.append("\n=== Acorn Documentation (Truncated) ===")
            context_parts.append(acorn_docs)

    return "\n".join(context_parts)


def generate_implementation(task: Dict[str, str], context: str, model: str, error_context: str = None) -> Dict[str, any]:
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

    prompt = f"""You are an expert Acorn theorem prover developer. You are working on the Acorn standard library.

TASK: {task['description']}

{error_instruction}

CONTEXT:
{context}

Your job is to implement this task by:
1. Analyzing what needs to be done
2. Determining which files need to be modified
3. Writing the necessary Acorn code following the syntax and style in the codebase
4. Ensuring the code will verify with ./acorn

IMPORTANT RULES:
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
            "content": "full file content",
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


def test_in_external_file(acornlib_path: str, code: str, test_filename: str = "test_code.ac") -> Tuple[bool, str]:
    """Test code in external file before merging into stdlib."""
    test_path = os.path.join(os.path.dirname(acornlib_path), test_filename)

    print(f"\n📝 Writing test code to {test_filename}...")
    write_file(test_path, code)

    # Verify with relative path
    success, output = verify_acorn_file(acornlib_path, f"../{test_filename}")

    return success, output


def apply_implementation(acornlib_path: str, implementation: Dict[str, any]) -> List[str]:
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


def run_agent(
    acornlib_path: str,
    context_file: str,
    model: str,
    max_iterations: int = 10,
    auto_push: bool = True
) -> None:
    """Run the autonomous development agent."""

    print("🤖 Acorn Autonomous Development Agent Starting...")
    print(f"📂 Working directory: {acornlib_path}")
    print(f"🔄 Max iterations: {max_iterations}")
    print(f"📤 Auto-push: {auto_push}")

    todo_path = os.path.join(acornlib_path, "TODO.md")

    for iteration in range(max_iterations):
        print(f"\n{'='*60}")
        print(f"🔄 Iteration {iteration + 1}/{max_iterations}")
        print(f"{'='*60}")

        # Extract next task
        task = extract_next_task(todo_path)
        if not task:
            print("✅ No more tasks found in TODO.md!")
            print("🎉 All tasks completed!")
            break

        print(f"\n📋 Next task: {task['description']}")

        # Load context
        print("\n📚 Loading context...")
        context = load_acorn_context(acornlib_path, context_file)

        # Try to implement with auto-fix
        error_context = None
        for attempt in range(MAX_FIX_ATTEMPTS):
            if attempt > 0:
                print(f"\n🔧 Auto-fix attempt {attempt}/{MAX_FIX_ATTEMPTS - 1}...")

            # Generate implementation
            print("\n🧠 Generating implementation with LLM...")
            implementation = generate_implementation(task, context, model, error_context)

            print(f"\n📊 Analysis: {implementation.get('analysis', 'No analysis')}")

            if 'raw_response' in implementation:
                print(f"\n⚠️  LLM returned non-JSON response:")
                print(implementation['raw_response'][:500])
                if attempt < MAX_FIX_ATTEMPTS - 1:
                    error_context = "LLM response was not valid JSON. Please respond with valid JSON format."
                    continue
                else:
                    print("\n❌ Stopping due to parsing error after max attempts")
                    break

            # Test in external file first
            if implementation.get('files'):
                test_code_parts = []
                for file_spec in implementation['files']:
                    if 'content' in file_spec:
                        test_code_parts.append(f"// {file_spec['path']}")
                        test_code_parts.append(file_spec['content'])
                        test_code_parts.append("")

                test_code = "\n".join(test_code_parts)
                test_success, test_output = test_in_external_file(acornlib_path, test_code)

                if not test_success:
                    if attempt < MAX_FIX_ATTEMPTS - 1:
                        error_context = f"Code verification failed with error:\n{test_output}\n\nPlease fix the errors."
                        continue
                    else:
                        print(f"\n❌ Auto-fix failed after {MAX_FIX_ATTEMPTS} attempts")
                        print("Manual intervention needed.")
                        break

                print("\n✅ External file test passed!")

            # Apply implementation to actual files
            modified_files = apply_implementation(acornlib_path, implementation)

            if not modified_files:
                print("\n⚠️  No files were modified. Stopping.")
                break

            # Verify with ./acorn
            success, output = verify_acorn_code(acornlib_path)

            if not success:
                if attempt < MAX_FIX_ATTEMPTS - 1:
                    print(f"\n🔄 Verification failed, rolling back for retry...")
                    run_command(["git", "checkout", "."], cwd=acornlib_path)
                    error_context = f"Code verification failed with error:\n{output}\n\nPlease fix the errors."
                    continue
                else:
                    print("\n❌ Verification failed. Rolling back changes...")
                    run_command(["git", "checkout", "."], cwd=acornlib_path)
                    print("🔄 Rolled back changes")
                    print(f"\nStopping agent after {MAX_FIX_ATTEMPTS} failed attempts. Manual intervention needed.")
                    break

            # Success! Commit and push
            commit_msg = implementation.get('commit_message', f"feat: {task['description'][:50]}")
            if git_add_commit_push(acornlib_path, modified_files, commit_msg, push=auto_push):
                # Mark task as complete
                update_todo_mark_complete(todo_path, task['description'])
                print(f"\n✅ Task completed successfully!")
            else:
                print("\n❌ Failed to commit/push. Stopping.")
                break

            # Break out of retry loop on success
            break

    print(f"\n{'='*60}")
    print("🏁 Agent finished")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Acorn Standard Library Development Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This agent:
1. Reads TODO.md to find next task
2. Uses LLM to generate implementation
3. Tests code in external file first
4. Auto-fixes errors (up to 3 attempts)
5. Verifies with ./acorn
6. Commits and pushes changes
7. Updates TODO.md
8. Repeats until all tasks are done

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
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    # Validate paths
    if not os.path.exists(args.acornlib_path):
        print(f"Error: acornlib path not found: {args.acornlib_path}")
        sys.exit(1)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        todo_path = os.path.join(args.acornlib_path, "TODO.md")
        task = extract_next_task(todo_path)
        if task:
            print(f"\nNext task would be: {task['description']}")
        else:
            print("\nNo tasks found in TODO.md")
        return

    # Run the agent
    run_agent(
        acornlib_path=args.acornlib_path,
        context_file=args.context,
        model=args.model,
        max_iterations=args.max_iterations,
        auto_push=not args.no_push
    )


if __name__ == '__main__':
    main()
