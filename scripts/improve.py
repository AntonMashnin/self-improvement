"""
LLM self-improvement agent.
Reads Python files in algorithms/ and asks Claude to improve them.
Runs as part of the GitHub Actions self-improve workflow.
"""
import os
import sys
from pathlib import Path

import anthropic

ALGORITHMS_DIR = Path(__file__).parent.parent / "algorithms"
MODEL = "claude-opus-4-5"


def improve_file(client: anthropic.Anthropic, file_path: Path) -> str:
    code = file_path.read_text()

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are improving a Python algorithms library. "
                    "Return ONLY the improved Python code, no explanations, no markdown fences.\n\n"
                    "Improve this file by:\n"
                    "- Improving or adding docstrings and type hints\n"
                    "- Fixing bugs if any\n"
                    "- Improving efficiency where possible\n"
                    "- Adding edge case handling\n"
                    "- Keeping all existing public functions intact\n\n"
                    f"File: {file_path.name}\n\n{code}"
                ),
            }
        ],
    )

    improved = response.content[0].text.strip()
    # Strip markdown fences if the model wrapped the code
    if improved.startswith("```python"):
        improved = improved[9:]
    if improved.startswith("```"):
        improved = improved[3:]
    if improved.endswith("```"):
        improved = improved[:-3]
    return improved.strip()


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    python_files = [
        f for f in ALGORITHMS_DIR.glob("*.py") if f.name != "__init__.py"
    ]

    if not python_files:
        print("No Python files found to improve.")
        return

    for file_path in python_files:
        print(f"Improving {file_path.name}...")
        try:
            improved = improve_file(client, file_path)
            file_path.write_text(improved + "\n")
            print(f"  Done.")
        except Exception as e:
            print(f"  Failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
