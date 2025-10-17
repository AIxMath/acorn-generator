# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python toolkit for AI-assisted development of the Acorn mathematical proof language standard library. It includes:

1. **Documentation Dumper** (`dump_folder.py`) - Aggregates Acorn documentation into a context file
2. **Library Extension Agent** (`acorn_agent.py`) - Generates new Acorn theorems and structures on demand
3. **Autonomous Development Agent** (`acorn_dev_agent.py`) - Automatically implements tasks from TODO.md with verification and git integration

The tools work together to accelerate Acorn standard library development using LLM assistance.

## Common Commands

### Running the documentation dumper
```bash
python dump_folder.py --path <directory_to_scan> -o <output_file>
# Example from README:
python dump_folder.py --path ../acornprover.org/docs/ -o context.txt
```

- Use `-o -` or omit `-o` to write to stdout
- The output file format is: `<path>:\ncontent\n\n` for each file

### Running the Acorn library extension agent
```bash
# Interactive mode
python acorn_agent.py --interactive

# Generate from a request
python acorn_agent.py --request "Define a Vector3D structure with dot product"

# Save output to a file
python acorn_agent.py --request "Prove the Pythagorean theorem" -o pythagorean.ac

# Use a different model
python acorn_agent.py --request "Define fibonacci sequence" --model gpt-4
```

### Running the autonomous development agent
```bash
# Dry run (see what would be done)
python acorn_dev_agent.py --dry-run

# Run with default settings (processes tasks from acornlib/TODO.md)
python acorn_dev_agent.py

# Run without pushing (commit locally only)
python acorn_dev_agent.py --no-push

# Limit iterations
python acorn_dev_agent.py --max-iterations 3

# Custom paths
python acorn_dev_agent.py --acornlib-path ./acornlib --context ./context.txt
```

The autonomous agent will:
1. Read next task from `acornlib/TODO.md`
2. Generate implementation using LLM
3. **Apply changes directly to stdlib files**
4. **Verify with `./acorn --lib ./acornlib`** (runs from base directory)
5. **Auto-fix errors** (up to 3 attempts with error feedback to LLM)
6. Git add, commit, and push changes
7. Update TODO.md marking task complete
8. Repeat until max iterations or no tasks remain

Required environment variables:
- `OPENAI_API_KEY`: API key for the LLM service
- `OPENAI_BASE_URL`: Base URL for the OpenAI-compatible API endpoint

### Running with the LLM helper
The `llm.py` module provides an `ask()` function for querying LLMs:
- Requires `OPENAI_API_KEY` and `OPENAI_BASE_URL` environment variables
- Default model: `deepseek-v3-250324`

## Code Architecture

### dump_folder.py
The main utility script with three key functions:
- `collect_file_paths(root_directory)`: Recursively walks a directory tree, returns sorted list of all file paths
- `ensure_parent_dir_exists(file_path)`: Creates parent directories if needed for output file
- `main()`: CLI entry point that handles argument parsing, file collection, and output formatting
  - Automatically excludes the output file if it's inside the scanned directory
  - Supports both stdout and file output
  - Uses UTF-8 encoding with error replacement for robust file reading

### llm.py
Simple LLM API wrapper:
- `ask(prompt, model)`: Sends a single-turn prompt to an OpenAI-compatible API endpoint
- Expects environment variables for authentication

### acorn_agent.py
AI agent for extending the Acorn standard library:
- `load_context(context_path)`: Loads the Acorn documentation context from `context.txt`
- `generate_library_extension(request, context, model, include_examples)`: Generates Acorn code based on user request
- `interactive_mode(context, model)`: Runs the agent in interactive REPL mode
- `main()`: CLI entry point with argument parsing

The agent uses the documentation context to understand Acorn syntax and library patterns, then generates high-quality extensions including:
- Theorems with proofs
- Structure and inductive type definitions
- Attributes (methods and constants)
- Typeclasses for algebraic structures
- Example usage and comments

### acorn_dev_agent.py
Autonomous development agent for the Acorn standard library with auto-fix:
- `extract_next_task(todo_path)`: Parses TODO.md to find next uncompleted task
- `update_todo_mark_complete(todo_path, task_description)`: Marks tasks as [x] when done
- `load_acorn_context(acornlib_path, context_file)`: Loads CLAUDE.md, TODO.md, and documentation context
- `generate_implementation(task, context, model, error_context)`: Uses LLM to generate code (with error feedback)
- `verify_acorn_file(acornlib_path, test_file)`: Verifies specific file with `./acorn --lib ./acornlib`
- `verify_acorn_code(acornlib_path)`: Runs `./acorn --lib ./acornlib` to verify all code
- `apply_implementation(acornlib_path, implementation)`: Applies file changes from LLM response
- `git_add_commit_push(acornlib_path, files, commit_message, push)`: Commits and pushes changes
- `run_agent(...)`: Main loop with retry logic (up to 3 auto-fix attempts per task)

**Auto-fix feature**: When verification fails, the agent feeds error messages back to the LLM for automatic correction, retrying up to 3 times before giving up. Changes are rolled back between retry attempts using `git checkout .`.

**Note**: The Acorn binary is located in the base directory (not inside acornlib). The agent runs `./acorn --lib ./acornlib` from the base directory to verify code.

## Project Context

This toolkit is designed to work alongside:
- **Acorn Prover documentation** (https://github.com/acornprover/acornprover.org)
- **Acorn standard library** (https://github.com/AIxMath/acornlib.git)

### Typical Workflow

1. **Initial Setup**:
   ```bash
   # Clone documentation
   git clone https://github.com/acornprover/acornprover.org.git

   # Clone or use existing acornlib
   # (acornlib should be in the project directory)

   # Generate context
   python dump_folder.py --path ../acornprover.org/docs/ -o context.txt
   ```

2. **Manual Development** (interactive):
   ```bash
   python acorn_agent.py --interactive
   # Enter requests to generate code
   # Review and manually add to acornlib
   ```

3. **Autonomous Development** (from TODO.md):
   ```bash
   python acorn_dev_agent.py
   # Agent reads tasks from acornlib/TODO.md
   # Implements, verifies, commits, and pushes automatically
   ```

4. **Verification**:
   ```bash
   cd acornlib
   ./acorn  # Verify all code compiles
   ```

5. **Create Pull Request**:
   ```bash
   # After reviewing commits, create PR on GitHub
   gh pr create --title "feat: implement X" --body "..."
   ```

## Acorn Language Overview

Acorn is a mathematical proof language with:
- **Imports**: `from module import Type` (modules: nat, int, real, etc.)
- **Numerals**: `numerals Type` enables numeric literals
- **Theorems**: `theorem name(args) { statement } by { proof }`
- **Definitions**: `define name(args) -> ReturnType { body }`
- **Structures**: `structure Name { fields }`
- **Inductive types**: `inductive Name { constructors }`
- **Attributes**: `attributes Type { methods and constants }`
- **Typeclasses**: `class Name[T] { abstract properties }`

The standard library includes: Nat, Int, Real, Complex, Rat, List, Set, FiniteSet, Group, Ring, Field, and various algebraic structures.
