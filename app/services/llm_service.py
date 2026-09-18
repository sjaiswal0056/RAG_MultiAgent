from __future__ import annotations

from typing import Protocol


class StructuredLLM(Protocol):
    def generate(self, prompt: str, schema: type) -> object: ...


class DisabledLLM:
    """Explicit offline provider used by the deterministic reference implementation."""

    def generate(self, prompt: str, schema: type) -> object:
        raise RuntimeError("No LLM is required by the deterministic workflow; configure a provider extension explicitly")
