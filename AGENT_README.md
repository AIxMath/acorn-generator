# Acorn Standard Library Extension Agent

An AI-powered agent for extending the Acorn mathematical proof language standard library.

## Overview

This agent helps generate high-quality Acorn code including theorems, definitions, structures, and typeclasses. It uses the Acorn documentation as context to understand syntax and library patterns, then generates code that fits naturally into the standard library.

## Setup

### Prerequisites

1. Python 3.7 or higher
2. An OpenAI-compatible API endpoint (e.g., OpenAI, DeepSeek, or local LLM)
3. The Acorn documentation context file

### Environment Variables

Set these environment variables before running the agent:

```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_BASE_URL="https://api.your-provider.com/v1/chat/completions"
```

### Generate Context File

First, generate the Acorn documentation context:

```bash
cd /tmp
git clone https://github.com/acornprover/acornprover.org.git
git clone https://github.com/Zecyel/acorn-generator.git
cd acorn-generator
python dump_folder.py --path ../acornprover.org/docs/ -o context.txt
```

## Usage

### Interactive Mode

Run the agent in interactive REPL mode:

```bash
python acorn_agent.py --interactive
```

Then enter requests like:
- "Define a Vector3D structure with dot product and cross product"
- "Prove the Pythagorean theorem"
- "Define the Fibonacci sequence"
- "Create a Graph structure with basic graph theory operations"

### Command-Line Mode

Generate code from a single request:

```bash
python acorn_agent.py --request "Define a Matrix structure with addition and multiplication"
```

Save output to a file:

```bash
python acorn_agent.py --request "Prove the Pythagorean theorem" -o pythagorean.ac
```

### Advanced Options

Use a different model:

```bash
python acorn_agent.py --request "Define Fermat's Little Theorem" --model gpt-4
```

Disable example usage in output:

```bash
python acorn_agent.py --request "Define prime numbers" --no-examples
```

Specify a custom context file:

```bash
python acorn_agent.py --request "Define quaternions" --context custom_context.txt
```

## What the Agent Generates

The agent produces complete, compilable Acorn code including:

1. **Proper imports**: `from nat import Nat`, etc.
2. **Structure definitions**: For mathematical objects
3. **Attributes**: Methods and constants for types
4. **Theorems**: With proofs in `by` blocks
5. **Definitions**: Pure functions and predicates
6. **Comments**: Clear explanations of mathematical concepts
7. **Example usage**: Demonstrating how to use the new code

## Example Output

Request: `"Define a Vector2D structure with dot product"`

```acorn
from real import Real
numerals Real

// A 2-dimensional vector with real-valued components
structure Vector2D {
    x: Real
    y: Real
}

attributes Vector2D {
    // The zero vector
    let zero = Vector2D.new(0, 0)

    // Dot product (inner product)
    define dot(self, other: Vector2D) -> Real {
        self.x * other.x + self.y * other.y
    }
}

theorem dot_product_commutative(u: Vector2D, v: Vector2D) {
    u.dot(v) = v.dot(u)
} by {
    u.dot(v) = u.x * v.x + u.y * v.y
    v.dot(u) = v.x * u.x + v.y * u.y
}
```

## Best Practices

### For Better Results

1. **Be specific**: "Define a binary search tree with insertion and search" is better than "Define a tree"
2. **State the domain**: Mention if you want natural numbers, integers, reals, etc.
3. **Request proofs**: Ask for theorems proving key properties
4. **Iterate**: Generate code, review it, then refine with follow-up requests

### Common Request Patterns

- Structure definitions: "Define a [Name] structure with [properties/operations]"
- Theorems: "Prove [theorem name/statement]"
- Operations: "Add [operation] to [existing type]"
- Sequences: "Define the [sequence name] sequence"
- Algebraic structures: "Define [structure] as a typeclass"

## Integration with Acorn

The generated `.ac` files can be:

1. Tested in VS Code with the Acorn Prover extension
2. Refined based on Acorn's feedback
3. Contributed to the Acorn standard library repository

## Troubleshooting

### "Context file not found"

Run `dump_folder.py` to generate `context.txt`:

```bash
python dump_folder.py --path ../acornprover.org/docs/ -o context.txt
```

### "Environment variable not set"

Ensure both `OPENAI_API_KEY` and `OPENAI_BASE_URL` are exported:

```bash
echo $OPENAI_API_KEY
echo $OPENAI_BASE_URL
```

### Generated code doesn't compile

The agent generates code based on patterns from the documentation, but may not always be perfect. Common issues:
- Missing imports: Add required `from module import Type` statements
- Proof gaps: Expand the `by` block with more detailed steps
- Type mismatches: Verify types align with standard library definitions

## Contributing

To contribute to the Acorn standard library:

1. Generate code with the agent
2. Test it with the Acorn Prover VS Code extension
3. Refine based on feedback
4. Submit a pull request to [acornlib](https://github.com/acornprover/acornlib)

## License

This tool is part of the acorn-generator project. See the main repository for license details.
