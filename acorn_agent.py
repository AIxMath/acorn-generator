#!/usr/bin/env python3
"""
Acorn Standard Library Extension Agent

This agent helps extend the Acorn standard library by generating new theorems,
definitions, structures, and typeclasses based on user requests.
"""

import argparse
import os
import sys
from typing import Optional
from llm import ask


SYSTEM_PROMPT = """You are an expert in the Acorn mathematical proof language. Your task is to help extend the Acorn standard library by generating high-quality, well-documented code.

Key Acorn syntax rules:
1. Import statements: `from module import Type` (e.g., `from nat import Nat`)
2. Numerals: Use `numerals Type` to enable number literals
3. Theorems: `theorem name(args) { statement }` with optional `by { proof }`
4. Definitions: `define name(args) -> ReturnType { body }`
5. Structures: `structure Name { field1: Type1, field2: Type2 }`
6. Attributes: `attributes TypeName { ... }` to add methods and constants
7. Typeclasses: `class ClassName[T] { ... }` for abstract algebraic structures
8. Inductive types: `inductive TypeName { constructors }`

Guidelines:
- Always include clear comments explaining the mathematical concept
- Use descriptive names following snake_case convention
- Include proofs when non-trivial (in `by` blocks)
- Follow existing library patterns and conventions
- For structures and classes, include relevant theorems demonstrating properties
- When defining operators, use the reserved names (add, mul, sub, etc.)

Generate complete, compilable Acorn code that fits naturally into the standard library."""


def load_context(context_path: str = "context.txt") -> str:
    """Load the Acorn documentation context."""
    if not os.path.exists(context_path):
        print(f"Warning: Context file '{context_path}' not found.", file=sys.stderr)
        print("Consider running: python dump_folder.py --path ../acornprover.org/docs/ -o context.txt", file=sys.stderr)
        return ""

    try:
        with open(context_path, 'r', encoding='utf-8') as f:
            # Read first 30000 characters to avoid overwhelming the LLM
            content = f.read(30000)
            if len(content) == 30000:
                content += "\n\n[Context truncated for length...]"
            return content
    except Exception as e:
        print(f"Error loading context: {e}", file=sys.stderr)
        return ""


def generate_library_extension(
    request: str,
    context: str,
    model: str = "deepseek-v3-250324",
    include_examples: bool = True
) -> str:
    """
    Generate Acorn standard library extensions based on user request.

    Args:
        request: The user's request for what to add to the library
        context: The Acorn documentation context
        model: The LLM model to use
        include_examples: Whether to include example usage in the output

    Returns:
        Generated Acorn code
    """

    # Build the prompt with context
    prompt_parts = [SYSTEM_PROMPT]

    if context:
        prompt_parts.append("\n\nHere is relevant context from the Acorn documentation:")
        prompt_parts.append(context[:15000])  # Limit context to avoid token limits

    prompt_parts.append("\n\nUser request:")
    prompt_parts.append(request)

    if include_examples:
        prompt_parts.append("\n\nPlease generate:")
        prompt_parts.append("1. The main implementation (theorems, definitions, structures)")
        prompt_parts.append("2. Example usage showing how to use the new additions")
        prompt_parts.append("3. Comments explaining the mathematical concepts")

    prompt_parts.append("\n\nGenerate only valid Acorn code. Do not include explanatory text outside of Acorn comments.")

    full_prompt = "\n".join(prompt_parts)

    try:
        response = ask(full_prompt, model=model)
        return response
    except Exception as e:
        print(f"Error generating code: {e}", file=sys.stderr)
        return f"// Error: {e}"


def interactive_mode(context: str, model: str):
    """Run the agent in interactive mode."""
    print("Acorn Standard Library Extension Agent")
    print("=" * 60)
    print("Enter your requests to generate Acorn library code.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            request = input("Request: ").strip()

            if not request:
                continue

            if request.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            print("\nGenerating Acorn code...\n")
            result = generate_library_extension(request, context, model)
            print(result)
            print("\n" + "=" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            break


def main():
    parser = argparse.ArgumentParser(
        description="Agent for extending the Acorn standard library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python acorn_agent.py --interactive

  # Generate from a request
  python acorn_agent.py --request "Define a Vector3D structure with dot product and cross product"

  # Save output to a file
  python acorn_agent.py --request "Prove the Pythagorean theorem" -o pythagorean.ac

  # Use a different model
  python acorn_agent.py --request "Define fibonacci sequence" --model gpt-4
"""
    )

    parser.add_argument(
        '--request', '-r',
        type=str,
        help='What to add to the Acorn standard library'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path (default: stdout)'
    )

    parser.add_argument(
        '--context', '-c',
        type=str,
        default='context.txt',
        help='Path to the context file (default: context.txt)'
    )

    parser.add_argument(
        '--model', '-m',
        type=str,
        default='deepseek-v3-250324',
        help='LLM model to use (default: deepseek-v3-250324)'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )

    parser.add_argument(
        '--no-examples',
        action='store_true',
        help='Do not include usage examples in output'
    )

    args = parser.parse_args()

    # Load context
    context = load_context(args.context)

    if args.interactive:
        interactive_mode(context, args.model)
    elif args.request:
        result = generate_library_extension(
            args.request,
            context,
            args.model,
            include_examples=not args.no_examples
        )

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Output written to {args.output}")
        else:
            print(result)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
