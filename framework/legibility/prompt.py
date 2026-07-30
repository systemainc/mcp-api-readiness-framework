"""
Builds the prompt for the one bounded LLM pass.

The model is given the actual tool descriptions and error response examples
extracted from the OpenAPI spec. Its only job is to identify whether they
contain enough information for an agent to act on them correctly without
guessing. It phrases observations; it does not invent scores or facts.
"""
from __future__ import annotations


def build_legibility_prompt(
    target_name: str,
    operation_samples: list[dict],
    error_samples: list[dict],
) -> str:
    ops_text = "\n".join(
        f"- {op.get('operationId', op.get('path', '?'))}: "
        f"{op.get('description') or op.get('summary') or '[no description]'}"
        for op in operation_samples[:10]
    )
    err_text = "\n".join(
        f"- HTTP {e.get('status', '?')}: {e.get('description') or '[no description]'}"
        for e in error_samples[:5]
    )

    return (
        f"You are reviewing the API tool descriptions for \"{target_name}\" to determine "
        f"whether an AI agent (not a human developer) could use them correctly.\n\n"
        f"Tool descriptions found in the schema:\n{ops_text or '[none found]'}\n\n"
        f"Error response descriptions:\n{err_text or '[none found]'}\n\n"
        f"Assess only what is shown above. Do not invent capabilities, parameters, or "
        f"context not present in the text above. Write exactly 3 sentences:\n"
        f"1. What an agent could correctly do from these descriptions alone.\n"
        f"2. The single most actionable gap that would cause an agent to take a wrong action.\n"
        f"3. One concrete fix (e.g., add a specific sentence to a specific description).\n"
        f"Plain text, no markdown, no preamble, no sign-off."
    )
