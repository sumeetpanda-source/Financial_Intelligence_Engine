"""Secure OpenAI connectivity check for the Phase 1 demo."""

from __future__ import annotations

import argparse
import getpass
import os

from config import get_settings


def main():
    parser = argparse.ArgumentParser(description="Verify OpenAI access without printing or storing the API key.")
    parser.add_argument("--model", help="Optional model override.")
    args = parser.parse_args()

    settings = get_settings()
    api_key = settings.openai_api_key or getpass.getpass("OpenAI API key: ").strip()
    model = args.model or settings.genai_model

    if not api_key:
        raise SystemExit("No OpenAI API key was provided.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=(
            "Reply with exactly: Financial Intelligence Engine OpenAI check passed."
        ),
        max_output_tokens=40,
    )
    print(f"OpenAI API check passed with model: {model}")
    print(response.output_text.strip())


if __name__ == "__main__":
    main()
