"""
Provider-agnostic GenAI interface.

Local mode gives deterministic reports for offline development. Cloud mode can
use OpenAI first, while leaving room for Gemini, Claude, or local LLM adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from config import AppSettings, get_settings


class GenAIProvider(ABC):
    """Abstract text generation provider."""

    @abstractmethod
    def generate_report(self, prompt: str) -> str:
        """Generate a report from a grounded prompt."""


class LocalGenAIProvider(GenAIProvider):
    """Offline deterministic fallback used before API keys are configured."""

    def generate_report(self, prompt: str) -> str:
        return prompt


class OpenAIGenAIProvider(GenAIProvider):
    """OpenAI Responses API provider."""

    def __init__(self, settings: AppSettings):
        self.settings = settings

    def generate_report(self, prompt: str) -> str:
        if not self.settings.openai_api_key:
            return prompt

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.settings.openai_api_key)
            response = client.responses.create(
                model=self.settings.genai_model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are a financial intelligence report writer. "
                            "Use only the provided agent outputs and evidence. "
                            "Separate facts from model predictions. Include a disclaimer."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.output_text
        except Exception as exc:
            return f"{prompt}\n\nGenAI provider warning: OpenAI generation failed locally: {exc}"


def build_genai_provider(settings: Optional[AppSettings] = None) -> GenAIProvider:
    settings = settings or get_settings()
    provider = settings.genai_provider.lower()
    if provider == "openai":
        return OpenAIGenAIProvider(settings)
    return LocalGenAIProvider()
