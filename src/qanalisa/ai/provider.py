from __future__ import annotations

from typing import Protocol


class AIProviderError(RuntimeError):
    """Raised when an AI provider cannot produce valid structured output."""


class AIProvider(Protocol):
    def generate(self, prompt: str, schema: dict) -> dict:
        """Generate structured output that conforms to the provided schema."""

    def preflight(self) -> list[str]:
        """Return non-fatal warnings discovered before analysis."""
