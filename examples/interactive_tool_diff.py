import logging
import subprocess
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import List

import anthropic
import ell
from pydantic import Field


logger = logging.getLogger(__name__)


def _validate_diff(diff: str) -> subprocess.CompletedProcess:
  logger.info(f"Validating diff: {diff}")
  return subprocess.run(
    ["patch", "-p1", "--dry-run"],
    input=diff.encode("utf-8"),
    capture_output=True,
    check=False
  )


@ell.tool()
def apply_diff(
  diff: str = Field(description="The unified diff to apply."),
) -> str | None:
  """Applies a unified diff to a local workspace using `patch -p1` and returns a natural language result."""
  logger.info(f"Tool call: apply_diff")
  result = _validate_diff(diff)
  # TODO(kwlzn): Can we send a structured output to the LLM with e.g. tool_call_result.exit_code and stdout/stderr for it to natively interpret?
  if result.returncode == 0:
    logger.info("Tool call: apply_diff succeeded")
    return f"Patch applied successfully: {result.stdout.decode()}"
  else:
    logger.warning("Tool call: apply_diff failed")
    # Provide context to the LLM on the failure by proxying the output of `patch -p1`.
    return f"That patch is invalid, can you try again with the correct diff syntax? Here's the output of `patch -p1`:\n{result.stderr.decode()}"


def diff_loop(prompts: str, glob: str, repo: str = ".", max_loops: int = 3):
  repo_path = Path(repo)
  code_file = next(repo_path.glob(glob)).relative_to(repo_path)
  code = f"<file:{code_file}>\n{code_file.read_text()}\n</file:{code_file}>"

  client = anthropic.Anthropic()

  system_prompt = dedent("""\
  You are a helpful, expert-level programmer that generates Python code changes to an existing codebase given a request.
  Your changes will be written to the filesystem using relative paths. You are in the root directory of the repository.
  Test application of the changes by calling the `apply_diff` tool with a valid unified diff (like `diff` or `git diff` would generate).
  This will store the patch, but won't apply it to the local filesystem - so always generate a completely new patch for every request.
  Use chain-of-thought reasoning to generate the code and explain your work in your response.
  """)

  with ell.interactive(
    model="claude-3-5-sonnet-20240620",
    client=client,
    tools=[apply_diff],
    max_tokens=1024,
    temperature=0.3
  ) as session:
    # Set the system prompt without making a request.
    session.set_system_prompt(system_prompt)

    for i, prompt in enumerate(prompts):
      # Send the code context on the first message, but not subsequent ones.
      if i == 0: prompt = f"{code}\n\n{prompt}"
      session.send(prompt)


def main():
  logging.basicConfig(
    format='%(asctime)s %(levelname)-8s] %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
  )

  ell.init(verbose=True, store="./ell_logs")

  diff_loop(
    prompts=[
      "Add a simple argument parsing routine to interactive_tool_diff.py that provides a --help argument.",
      "Now extend the argument parsing so the user can specify a model name that will be printed when the file is invoked. Make it default to gpt4o-mini.",
      "Now modify the diff_loop function in interactive_tool_diff.py to accept a model parameter that is passed via this CLI arg.",
      "Now make the default argument for the model name be: claude-3-5-sonnet-20240620."
    ],
    glob="**/interactive_tool_diff.py",
    max_loops=3
  )


if __name__ == "__main__":
  main()
