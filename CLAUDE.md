# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python utility for dumping documentation folders into a single text file, designed to work with the Acorn Prover documentation. The tool recursively collects all files from a directory and formats them into a single stream for processing by LLMs.

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

## Project Context

This tool is designed to work alongside the Acorn Prover documentation repository (https://github.com/acornprover/acornprover.org). The typical workflow involves:
1. Cloning both repositories
2. Using `dump_folder.py` to aggregate the documentation into `context.txt`
3. Using `acorn_agent.py` to generate new Acorn standard library code based on the context

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
