from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from qanalisa.ai.provider import AIProviderError


class ClaudeCliProvider:
    """Invoke locally authenticated Claude Code in one-shot print mode."""

    def __init__(self, command: str, model: str | None, timeout_seconds: int) -> None:
        self.command = command
        self.model = model
        self.timeout_seconds = timeout_seconds

    def build_command(self, schema: dict[str, Any]) -> list[str]:
        cmd = [
            self.command,
            "-p",
            "--safe-mode",
            "--tools",
            "",
            "--no-session-persistence",
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
        ]
        if self.model:
            cmd.extend(["--model", self.model])
        return cmd

    def preflight(self) -> list[str]:
        warnings: list[str] = []
        if os.getenv("ANTHROPIC_API_KEY"):
            warnings.append(
                "ANTHROPIC_API_KEY is set; Claude Code may use API billing instead of the subscription."
            )
        return warnings

    def generate(self, prompt: str, schema: dict) -> dict:
        cmd = self.build_command(schema)
        try:
            completed = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise AIProviderError(
                f"Claude Code executable '{self.command}' was not found."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise AIProviderError(
                f"Claude Code exceeded the {self.timeout_seconds}s timeout."
            ) from exc

        if completed.returncode != 0:
            # Do not propagate stderr verbatim because it can include local paths or provider details.
            raise AIProviderError(
                f"Claude Code failed with exit status {completed.returncode}."
            )

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AIProviderError("Claude Code returned malformed JSON output.") from exc

        structured = payload.get("structured_output") if isinstance(payload, dict) else None
        if not isinstance(structured, dict):
            raise AIProviderError("Claude Code response did not contain structured_output.")
        return structured
