from __future__ import annotations

import os

from .base import LegibilityProvider


class AnthropicProvider(LegibilityProvider):
    def __init__(self, options: dict):
        self._model = options.get("model", "claude-sonnet-5")
        self._max_tokens = options.get("max_tokens", 300)
        api_key_env = options.get("api_key_env", "ANTHROPIC_API_KEY")
        self._api_key = os.environ.get(api_key_env, "")

    def assess(self, prompt: str) -> str:
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package required for legibility assessment: pip install anthropic"
            ) from e
        if not self._api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set; cannot run legibility assessment"
            )
        client = anthropic.Anthropic(api_key=self._api_key)
        msg = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
